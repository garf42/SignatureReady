#!/usr/bin/env python3
"""Negative checks on the build's own gate.

scripts/check.py is the mechanism that enforces every structural property of this
build. It has the same problem as any other guard: a guard nobody has watched fail
is not known to work. This file installs a defect against each guard and asserts
the gate goes red, which is the operating loop's step 7 applied to the gate itself.

It also pins the clause-addressability repair recorded in the ledger. Before that
repair `(clause: X)` appeared zero times across all twenty node files, so
check_ledger's clause_ids set was always empty and every `rediscovered` value —
every spelling of it — failed validation. The rediscovery rate is the only
instrument this build has for telling whether packet assembly is working, and it
could not be used at all.

Runs with pytest, or standalone:  python3 tests/build/test_gate.py
Exits non-zero on failure. Exits non-zero when it cannot run — an absent build
directory never reads as a passing zero.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build"
CHECK = ROOT / "scripts" / "check.py"
LEDGER = ROOT / "scripts" / "ledger.py"

CLAUSE_ID = re.compile(r"\(clause:\s*(\S+?)\)")
CLAUSE_LINE = re.compile(r"^\s*-\s*\[(?:BINDING|ADVISORY)\]")


def _run_check(build_dir, phase=0):
    """Return (exit_code, stdout) for the gate over build_dir."""
    p = subprocess.run(
        [sys.executable, str(CHECK), str(build_dir), "--phase", str(phase)],
        capture_output=True, text=True,
    )
    return p.returncode, p.stdout + p.stderr


def _sandbox():
    """A throwaway copy of build/ so a defect never touches the real contracts."""
    tmp = Path(tempfile.mkdtemp(prefix="gate-negcheck-"))
    dst = tmp / "build"
    shutil.copytree(BUILD, dst)
    return tmp, dst


def _clauses_section(text):
    m = re.search(r"^##\s+clauses\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def _node_files():
    return sorted((BUILD / "nodes").glob("*.md"))


# --- the repair this file pins -----------------------------------------------

def test_every_clause_carries_an_id():
    """A clause with no id cannot be named by a ledger entry, so its rediscovery
    is unrecordable and the packet-assembly signal loses that clause silently."""
    missing = []
    for f in _node_files():
        for line in _clauses_section(f.read_text()).splitlines():
            if CLAUSE_LINE.match(line) and not CLAUSE_ID.search(line):
                missing.append(f"{f.stem}: {line.strip()[:70]}")
    assert not missing, "clause lines with no (clause: id):\n  " + "\n  ".join(missing)


def test_clause_ids_are_unique_across_the_build():
    """Two clauses sharing an id make `rediscovered` ambiguous, which is worse than
    absent: it resolves, and it resolves to the wrong reasoning."""
    seen = {}
    dupes = []
    for f in _node_files():
        for cid in CLAUSE_ID.findall(f.read_text()):
            if cid in seen:
                dupes.append(f"{cid} in both {seen[cid]} and {f.stem}")
            seen[cid] = f.stem
    assert not dupes, "duplicate clause ids:\n  " + "\n  ".join(dupes)
    assert seen, "no clause ids found anywhere — the repair has been reverted"


def test_rediscovered_validates_against_a_real_clause_id():
    """The kill test for the repair. Before it, this assertion was unsatisfiable by
    construction: no value of --rediscovered could pass, because nothing carried an id."""
    tmp, build = _sandbox()
    try:
        cid = CLAUSE_ID.findall((build / "nodes" / "n.verifier.md").read_text())[0]
        led = build / "ledger.jsonl"
        subprocess.run(
            [sys.executable, str(LEDGER), str(led), "--node", "n.verifier",
             "--clause", "pinned by tests/build/test_gate.py", "--rediscovered", cid],
            capture_output=True, text=True, check=True,
        )
        _, out = _run_check(build)
        assert "is not a known clause id" not in out, (
            f"a real clause id ({cid}) was rejected by the gate:\n{out}"
        )
        # and the rediscovery-rate instrument now actually reports
        assert "rediscovery rate" in out, f"rediscovery rate never surfaced:\n{out}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_rediscovered_still_rejects_an_unknown_clause_id():
    """The repair must not turn the check into a rubber stamp. A typo'd id still fails."""
    tmp, build = _sandbox()
    try:
        led = build / "ledger.jsonl"
        subprocess.run(
            [sys.executable, str(LEDGER), str(led), "--node", "n.verifier",
             "--clause", "x", "--rediscovered", "n.verifier/c99-does-not-exist"],
            capture_output=True, text=True, check=True,
        )
        _, out = _run_check(build)
        assert "is not a known clause id" in out, (
            "an unknown clause id was accepted — the check has gone vacuous:\n" + out
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- negative checks against the gate's other guards -------------------------

def test_baseline_is_red_only_on_unprobed_prefabs():
    """The documented Phase -1 starting position. If anything else fails, the
    defect installed by a later test cannot be attributed to that test."""
    code, out = _run_check(BUILD)
    fails = [l for l in out.splitlines() if l.startswith("FAIL")]
    non_prefab = [l for l in fails if "probed is false" not in l]
    assert not non_prefab, "gate fails for reasons other than unprobed prefabs:\n" + "\n".join(non_prefab)
    assert code == 1 and fails, "gate is green while prefabs are still unprobed"


def test_cap_violation_is_caught():
    tmp, build = _sandbox()
    try:
        c = build / "constitution.md"
        c.write_text(c.read_text() + "\n" * 80)
        _, out = _run_check(build)
        assert "cap is" in out, "constitution cap did not fire:\n" + out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_regressed_seam_blocks():
    tmp, build = _sandbox()
    try:
        p = build / "seams.jsonl"
        rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
        rows[0]["status"] = "regressed"
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        _, out = _run_check(build)
        assert "REGRESSED" in out, "a regressed seam did not block:\n" + out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_demon_killed_with_pending_negative_check_is_caught():
    """A demon marked killed whose negative check never ran is the exact shape of
    a guard nobody has watched fail."""
    tmp, build = _sandbox()
    try:
        p = build / "nodes" / "n.verifier.md"
        p.write_text(p.read_text().replace("status: live", "status: killed", 1))
        _, out = _run_check(build)
        assert "marked killed but negative_check is pending" in out, out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_binding_clause_without_a_kill_test_is_caught():
    tmp, build = _sandbox()
    try:
        p = build / "nodes" / "n.verifier.md"
        text = p.read_text()
        sec = _clauses_section(text)
        line = next(l for l in sec.splitlines() if l.strip().startswith("- [BINDING]"))
        stripped = re.sub(r"\(kill_test:[^)]*\)", "", line)
        p.write_text(text.replace(line, stripped, 1))
        _, out = _run_check(build)
        assert "names no kill_test" in out, "a BINDING clause with no kill test passed:\n" + out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_corrupt_jsonl_line_is_reported_not_skipped():
    """Concurrent appends corrupt lines mid-write. A silently skipped line is a
    seam that vanishes from the register while every node suite stays green."""
    tmp, build = _sandbox()
    try:
        p = build / "seams.jsonl"
        p.write_text(p.read_text() + '{"seam": "n.a->n.b", "tier": "sta\n')
        _, out = _run_check(build)
        assert "is not valid JSON" in out, "a corrupt register line was skipped silently:\n" + out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gate_exits_nonzero_when_it_cannot_run():
    """An absent build directory must never read as a passing zero."""
    tmp = Path(tempfile.mkdtemp(prefix="gate-absent-"))
    try:
        code, out = _run_check(tmp / "no-such-build")
        assert code != 0, "the gate exited zero over a build directory that does not exist"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if not CHECK.exists() or not BUILD.is_dir():
        print(f"cannot run: missing {CHECK} or {BUILD}", file=sys.stderr)
        return 2
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"pass  {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}\n      {e}")
        except Exception as e:  # a test that cannot run is a failure, not a skip
            failed += 1
            print(f"ERROR {name}\n      {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
