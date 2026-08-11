#!/usr/bin/env python3
"""Validate a buildplan build directory.

Enforces the properties that must hold structurally rather than by discipline:
the constitution cap, non-vacuity on the intent predicate, force and origin
labels, oracle and risk assignment, edge closure, seam coverage, prefab probes,
gap expiry, and demon kill tests.

Usage:  python check.py build/ [--phase N]
Exit 0 = clean, exit 1 = violations found.
"""

import json
import re
import sys
from pathlib import Path

FORCE = re.compile(r"\[(BINDING|ADVISORY)\]")
ORIGIN = re.compile(r"origin:\s*(specified|derived)")
CAP = re.compile(r"<!--\s*cap:\s*(\d+)\s*-->")
ORACLE = re.compile(r"^type:\s*(derivable|relational|differential|none)\s*$", re.M)
RISK = re.compile(r"^risk:\s*([\w,\s]+?)\s*$", re.M)
IN_EDGE = re.compile(r"^\s*-\s*in:\s*([\w.]+)", re.M)
KILL = re.compile(r"kill_test:\s*(\S+)")
GAP_ID = re.compile(r"^\s*-\s*(G\d+)\b")
VOLATILITY = re.compile(r"volatility:\s*(low|medium|high)")
LAST_REVIEWED = re.compile(r"last_reviewed:\s*(\S+)")

DEFAULT_CAP = 200
RISK_AXES = {"semantic", "reproducibility", "none"}
VOL_WINDOW = {"low": 99, "medium": 2, "high": 1}  # phases before a gap goes stale


def section(text, name):
    m = re.search(rf"^##\s+{re.escape(name)}\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def clause_lines(body):
    out = []
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("<!--") or s.startswith("#"):
            continue
        if s.startswith("-") or s.startswith("["):
            out.append(s)
    return out


def load_jsonl(path, errors):
    rows = []
    if not path.exists():
        return rows
    for i, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}:{i} is not valid JSON ({e.msg}) — "
                          "concurrent appends corrupt lines; use scripts/ledger.py")
    return rows


# --- constitution ------------------------------------------------------------

def check_constitution(path, errors, warnings):
    if not path.exists():
        errors.append("constitution.md missing")
        return set(), ""
    text = path.read_text()

    m = CAP.search(text)
    cap = int(m.group(1)) if m else DEFAULT_CAP
    if not m:
        warnings.append(f"constitution.md has no '<!-- cap: N -->' marker; assuming {DEFAULT_CAP}")
    n = len(text.splitlines())
    if n > cap:
        errors.append(
            f"constitution.md is {n} lines, cap is {cap}. Do not raise the cap — remove a "
            "line, or fix the tie-break order so the new rule is unnecessary."
        )

    for name in ("Intent predicate", "Source contracts", "Tie-break order", "Escalation rule"):
        if not section(text, name).strip():
            errors.append(f"constitution.md missing required section: {name}")

    intent = section(text, "Intent predicate")
    if intent.strip():
        if not FORCE.search(intent):
            errors.append("constitution.md intent predicate has no force label")
        if "non-vacuity" not in intent:
            errors.append(
                "intent predicate has no non-vacuity assertion. A predicate quantifying over "
                "rows is satisfied by an empty table, so the cheapest green build produces "
                "nothing. Write the assertion now, not eighteen nodes later."
            )

    order = [l for l in section(text, "Tie-break order").splitlines() if re.match(r"^\s*\d+\.", l)]
    if 0 < len(order) < 2:
        warnings.append("tie-break order has fewer than 2 rules; it will rarely discriminate")

    sources = set(re.findall(r"^###\s+(src\.[\w.]+)", text, re.M))
    return sources, text


# --- nodes -------------------------------------------------------------------

def check_node(path, errors, warnings):
    text = path.read_text()
    nid = path.stem

    for name in ("assume", "guarantee", "oracle"):
        if not section(text, name).strip():
            errors.append(f"{nid}: missing required section '{name}'")

    oracle = section(text, "oracle")
    if not ORACLE.search(oracle):
        errors.append(f"{nid}: oracle needs 'type: derivable|relational|differential|none'")
    elif "type: none" in oracle and "G" not in oracle and "gap" not in text.lower():
        warnings.append(f"{nid}: oracle type is 'none' but no gap is referenced")

    rm = RISK.search(oracle)
    if not rm:
        errors.append(f"{nid}: oracle section needs a 'risk:' axis line")
    else:
        axes = {a.strip() for a in rm.group(1).split(",") if a.strip()}
        bad = axes - RISK_AXES
        if bad:
            errors.append(
                f"{nid}: risk axis {sorted(bad)} not in the closed enum {sorted(RISK_AXES)}. "
                "A new axis is admitted only when a ledger entry proves one was missing."
            )

    for sec in ("assume", "guarantee", "clauses"):
        body = section(text, sec)
        inherited = any(FORCE.search(l) and not l.strip().startswith("-")
                        for l in body.splitlines())
        for line in clause_lines(body):
            if not inherited and not FORCE.search(line):
                errors.append(f"{nid}/{sec}: clause has no [BINDING]/[ADVISORY] label -> {line[:60]}")

    for line in clause_lines(section(text, "clauses")):
        if not ORIGIN.search(line):
            errors.append(f"{nid}/clauses: clause has no 'origin:' tag -> {line[:60]}")
        if "[BINDING]" in line and not KILL.search(line):
            errors.append(
                f"{nid}/clauses: BINDING clause names no kill_test -> {line[:60]} "
                "(a clause without a kill test is a comment)"
            )

    demons = section(text, "demons")
    for block in re.findall(r"-\s*(D\d+):(.*?)(?=\n\s*-\s*D\d+:|\Z)", demons, re.S):
        did, body = block
        if "kill_test:" not in body:
            errors.append(f"{nid}/{did}: demon has no kill_test")
        if "negative_check:" not in body:
            errors.append(f"{nid}/{did}: demon has no negative_check")
        elif "pending" in body and "status: killed" in body:
            errors.append(
                f"{nid}/{did}: marked killed but negative_check is pending. "
                "A guard you have not seen fail is not known to work."
            )

    return nid, set(IN_EDGE.findall(section(text, "assume")))


# --- registers ---------------------------------------------------------------

def check_seams(rows, edges, errors, warnings):
    have = {r.get("seam") for r in rows}
    for nid, ins in edges.items():
        for up in ins:
            if up.startswith("src."):
                continue
            key = f"{up}->{nid}"
            if key not in have:
                errors.append(f"seam '{key}' is implied by {nid}'s assume but has no register entry")

    for r in rows:
        s = r.get("seam", "?")
        if r.get("tier") not in ("static", "replay"):
            errors.append(f"seam {s}: tier must be 'static' or 'replay'")
        if r.get("hazard") and r.get("tier") != "replay":
            errors.append(f"seam {s}: has a hazard but tier is not 'replay'")
        if r.get("status") not in ("pending", "driven", "regressed"):
            errors.append(f"seam {s}: status must be pending|driven|regressed")
        if r.get("status") == "driven" and not r.get("driver"):
            errors.append(f"seam {s}: marked driven with no driver test")
        if r.get("status") == "regressed":
            errors.append(f"seam {s}: REGRESSED — blocks can-i-build on {s.split('->')[-1]}")


def check_prefabs(rows, declared, errors, warnings):
    for r in rows:
        p = r.get("prefab", "?")
        if not r.get("probed"):
            errors.append(
                f"prefab {p}: probed is false. Libraries misbehave at your dimensions, "
                "not their tutorial's — probe at real sizes and run it twice."
            )
        if not r.get("probe_dims"):
            warnings.append(f"prefab {p}: no probe_dims recorded; a probe at default sizes proves little")
        for n in r.get("used_by", []):
            if n not in declared:
                errors.append(f"prefab {p}: used_by names '{n}', which has no node file")


def check_gaps(path, phase, declared, errors, warnings):
    if not path.exists():
        warnings.append("gaps.md missing — agents have nowhere to escalate")
        return set()
    ids = set()
    for block in re.split(r"\n(?=\s*-\s*G\d+)", path.read_text()):
        m = GAP_ID.search(block)
        if not m:
            continue
        gid = m.group(1)
        ids.add(gid)
        vm = VOLATILITY.search(block)
        if not vm:
            errors.append(f"{gid}: no volatility (low|medium|high). Without expiry a gap register "
                          "only grows — the amendment problem in a new file.")
            continue
        lm = LAST_REVIEWED.search(block)
        if not lm:
            errors.append(f"{gid}: no last_reviewed")
        elif phase is not None:
            last = re.sub(r"\D", "", lm.group(1))
            if last.isdigit() and phase - int(last) > VOL_WINDOW[vm.group(1)]:
                errors.append(
                    f"{gid}: volatility {vm.group(1)}, last reviewed phase {last}, now phase "
                    f"{phase} — stale. Every gap is a decision taken by default."
                )
        if "Blocks:" not in block:
            warnings.append(f"{gid}: names no blocking node; it will never surface for review")
    return ids


def check_ledger(rows, clause_ids, errors, warnings):
    seen = set()
    for r in rows:
        lid = r.get("id", "?")
        if lid in seen:
            errors.append(f"ledger {lid}: duplicate id — interleaved append; use scripts/ledger.py")
        seen.add(lid)
        if not r.get("clause"):
            errors.append(f"ledger {lid}: no clause. An entry with no clause is a fix that recurs.")
        red = r.get("rediscovered")
        if red and red not in clause_ids:
            errors.append(f"ledger {lid}: rediscovered names '{red}', which is not a known clause id")
    redis = sum(1 for r in rows if r.get("rediscovered"))
    if rows and redis:
        warnings.append(
            f"rediscovery rate {redis}/{len(rows)} — each is a packet-assembly failure "
            "(clause absent from the packet, or present and unattended)"
        )


# --- driver ------------------------------------------------------------------

def main(argv):
    root = Path(argv[1] if len(argv) > 1 else "build")
    phase = None
    if "--phase" in argv:
        try:
            phase = int(argv[argv.index("--phase") + 1])
        except (IndexError, ValueError):
            pass

    errors, warnings = [], []
    sources, _ = check_constitution(root / "constitution.md", errors, warnings)

    nodes_dir = root / "nodes"
    if not nodes_dir.is_dir():
        errors.append("nodes/ directory missing")
        return report(errors, warnings)

    declared, edges, clause_ids = set(), {}, set()
    for f in sorted(nodes_dir.glob("*.md")):
        nid, ins = check_node(f, errors, warnings)
        declared.add(nid)
        edges[nid] = ins
        clause_ids |= set(re.findall(r"\(clause:\s*(\S+?)\)", f.read_text()))

    for nid, ins in edges.items():
        for up in ins:
            if up.startswith("src."):
                if up not in sources:
                    errors.append(f"{nid}: assumes {up}, which has no source contract")
            elif up not in declared:
                errors.append(f"{nid}: assumes upstream '{up}', which has no node file")

    check_seams(load_jsonl(root / "seams.jsonl", errors), edges, errors, warnings)
    check_prefabs(load_jsonl(root / "prefabs.jsonl", errors), declared, errors, warnings)
    check_gaps(root / "gaps.md", phase, declared, errors, warnings)
    check_ledger(load_jsonl(root / "ledger.jsonl", errors), clause_ids, errors, warnings)

    if not (root / "seams.jsonl").exists():
        errors.append("seams.jsonl missing — every integration defect lives on an edge")
    if not (root / "ledger.jsonl").exists():
        warnings.append("ledger.jsonl missing — resolved surprises have nowhere to land")

    return report(errors, warnings)


def report(errors, warnings):
    for w in warnings:
        print(f"warn  {w}")
    for e in errors:
        print(f"FAIL  {e}")
    if errors:
        print(f"\n{len(errors)} violation(s).")
        return 1
    print(f"\nclean ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
