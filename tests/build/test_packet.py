#!/usr/bin/env python3
"""Pin the packet-assembly rule, which is what makes this build's context flat.

The build's claim is that context per task is O(node degree), not O(build size).
That claim is not a property of the plan's prose; it is a property of what gets
handed to an agent. These tests assert it against the assembler itself.

The load-bearing one is test_adding_a_non_neighbour_node_changes_no_packet. If a
node can be added to the build and a packet grows, the claim is false and the
structure has silently become an ordinary plan that accumulates.

Runs with pytest, or standalone:  python3 tests/build/test_packet.py
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
PACKET = ROOT / "scripts" / "packet.py"

CLAUSE_ID = re.compile(r"\(clause:\s*(\S+?)\)")


def _packet(build_dir, node, expect_ok=True):
    p = subprocess.run(
        [sys.executable, str(PACKET), str(build_dir), node],
        capture_output=True, text=True,
    )
    if expect_ok:
        assert p.returncode == 0, f"packet.py failed for {node}:\n{p.stderr}"
    return p.stdout, p.returncode


def _sandbox():
    tmp = Path(tempfile.mkdtemp(prefix="packet-"))
    dst = tmp / "build"
    shutil.copytree(BUILD, dst)
    return tmp, dst


def _nodes():
    return sorted(f.stem for f in (BUILD / "nodes").glob("*.md"))


def _seams():
    return [json.loads(l) for l in (BUILD / "seams.jsonl").read_text().splitlines() if l.strip()]


def _neighbours(node):
    out = set()
    for s in _seams():
        a, _, b = s["seam"].partition("->")
        if b == node and not a.startswith("src."):
            out.add(a)
        elif a == node:
            out.add(b)
    return out


# --- the rule: neighbour clauses never travel --------------------------------

def test_no_neighbour_clause_appears_in_any_packet():
    """Clause bleed across nodes is how a capped plan quietly becomes an uncapped
    one. Clause ids are unique build-wide, so this is exact rather than a prose match."""
    leaks = []
    for node in _nodes():
        text, _ = _packet(BUILD, node)
        found = set(CLAUSE_ID.findall(text))
        foreign = {c for c in found if not c.startswith(node + "/")}
        if foreign:
            leaks.append(f"{node}'s packet carries {sorted(foreign)}")
    assert not leaks, "neighbour clauses travelled:\n  " + "\n  ".join(leaks)


def test_target_own_clauses_do_travel():
    """The converse. A packet that drops the target's own clauses is not capped,
    it is broken — the agent would re-derive reasoning already written down."""
    for node in _nodes():
        own = set(CLAUSE_ID.findall((BUILD / "nodes" / f"{node}.md").read_text()))
        if not own:
            continue
        text, _ = _packet(BUILD, node)
        missing = own - set(CLAUSE_ID.findall(text))
        assert not missing, f"{node}'s packet is missing its own clauses: {sorted(missing)}"


def test_no_neighbour_reasoning_section_travels():
    """Only assume and guarantee cross a node boundary. Exactly one of each
    reasoning section may appear in a packet: the target's own.

    Matched at any heading depth. A neighbour's sections are emitted one level
    deeper than the target's, so a depth-specific match would miss the leak — and
    demons, oracles and metamorphic relations carry no ids, so this is the only
    check standing between them and a packet."""
    for name in ("clauses", "demons", "oracle", "metamorphic relations"):
        for node in _nodes():
            text, _ = _packet(BUILD, node)
            n = len(re.findall(rf"^#{{2,6}}\s+{re.escape(name)}\s*$", text, re.M))
            assert n <= 1, f"{node}'s packet carries {n} '{name}' sections; only the target's may travel"


# --- the claim: O(node degree), not O(build size) ----------------------------

def test_adding_a_non_neighbour_node_changes_no_packet():
    """The decisive test. Add a twenty-first node with its own seam, wired to a
    node that is not a neighbour of the target. If the target's packet moves by a
    single byte, context is a function of build size and the claim is false."""
    target = "n.verifier"
    nbrs = _neighbours(target)
    donor = next(n for n in _nodes() if n != target and n not in nbrs)

    tmp, build = _sandbox()
    try:
        before, _ = _packet(build, target)

        (build / "nodes" / "n.synthetic_probe.md").write_text(
            "# node: n.synthetic_probe\n\n"
            "## assume\n[BINDING] origin: specified\n"
            f"- in: {donor} — a synthetic edge that must not reach {target}\n\n"
            "## guarantee\n[BINDING] origin: specified\n- out: nothing real\n\n"
            "## oracle\ntype: none\nrisk: none\nGap: synthetic fixture for tests/build/test_packet.py\n\n"
            "## clauses\n- [ADVISORY] origin: derived — synthetic (clause: n.synthetic_probe/c1)\n"
        )
        seams = build / "seams.jsonl"
        seams.write_text(seams.read_text() + json.dumps({
            "seam": f"{donor}->n.synthetic_probe", "crosses": ["synthetic"], "hazard": "",
            "tier": "static", "driver": "", "status": "pending", "first_seen": "test",
        }) + "\n")

        after, _ = _packet(build, target)
        assert before == after, (
            f"adding n.synthetic_probe (wired to {donor}, not a neighbour of {target}) "
            f"changed {target}'s packet by {abs(len(after) - len(before))} chars. "
            "Context is O(build size), not O(node degree)."
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_packet_size_tracks_degree_not_build_size():
    """Weaker but broader: across all twenty nodes, the highest-degree node's packet
    must be larger than the lowest-degree node's, and no packet may approach the
    whole build. A packet that is most of the build has stopped being a packet."""
    rows = json.loads(subprocess.run(
        [sys.executable, str(PACKET), str(BUILD), "--stats-all", "--json"],
        capture_output=True, text=True, check=True).stdout)
    whole = sum(len(p.read_text().splitlines())
                for p in BUILD.rglob("*") if p.is_file() and p.suffix in (".md", ".jsonl"))
    hi = max(rows, key=lambda r: r["degree"])
    lo = min(rows, key=lambda r: r["degree"])
    assert hi["lines"] > lo["lines"], (
        f"{hi['node']} (degree {hi['degree']}) packet is not larger than "
        f"{lo['node']} (degree {lo['degree']}) — size is not tracking degree"
    )
    worst = max(r["lines"] / whole for r in rows)
    assert worst < 0.60, f"largest packet is {worst:.0%} of the whole build; that is not a packet"


# --- the packet contains exactly its own registers ---------------------------

def test_packet_carries_every_seam_naming_the_node_and_no_others():
    for node in _nodes():
        text, _ = _packet(BUILD, node)
        expected = {s["seam"] for s in _seams() if node in s["seam"].split("->")}
        present = set(re.findall(r'"seam":\s*"([^"]+)"', text))
        assert present == expected, (
            f"{node}: seam set mismatch\n  missing: {sorted(expected - present)}"
            f"\n  extra:   {sorted(present - expected)}"
        )


def test_packet_carries_every_prefab_used_by_the_node_and_no_others():
    prefabs = [json.loads(l) for l in (BUILD / "prefabs.jsonl").read_text().splitlines() if l.strip()]
    for node in _nodes():
        text, _ = _packet(BUILD, node)
        expected = {p["prefab"] for p in prefabs if node in p.get("used_by", [])}
        present = set(re.findall(r'"prefab":\s*"([^"]+)"', text))
        assert present == expected, (
            f"{node}: prefab set mismatch\n  missing: {sorted(expected - present)}"
            f"\n  extra:   {sorted(present - expected)}"
        )


def test_packet_warns_off_a_node_whose_prefabs_are_unprobed():
    """Do not build a node whose prefabs are unprobed. The packet has to say so;
    an agent that only gets the contract cannot know."""
    text, _ = _packet(BUILD, "n.surface")
    assert "Do not build this node." in text, "packet did not warn about unprobed prefabs"


# --- can-i-build --------------------------------------------------------------

def test_regressed_inbound_seam_refuses_the_packet():
    """A newly declared seam does not block on first appearance. A seam that passed
    and then regressed does."""
    tmp, build = _sandbox()
    try:
        p = build / "seams.jsonl"
        rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
        target = None
        for r in rows:
            a, _, b = r["seam"].partition("->")
            if not a.startswith("src."):
                r["status"] = "regressed"
                target = b
                break
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

        text, code = _packet(build, target, expect_ok=False)
        assert code == 1, f"packet.py exited {code} for a node with a regressed inbound seam"
        assert "REGRESSED" in text and "Refused" in text, text[:800]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_pending_seam_does_not_block():
    """Every seam is pending at phase -1. If pending blocked, no node could ever open."""
    for node in _nodes():
        _, code = _packet(BUILD, node)
        assert code == 0, f"{node} refused while all seams are merely pending"


def main():
    if not PACKET.exists() or not BUILD.is_dir():
        print(f"cannot run: missing {PACKET} or {BUILD}", file=sys.stderr)
        return 2
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"pass  {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}\n      {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {name}\n      {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
