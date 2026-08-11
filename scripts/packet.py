#!/usr/bin/env python3
"""Assemble the per-task context packet for one node.

The build's central claim is that context per task is O(node degree), not
O(build size). That claim rests entirely on one rule, stated in build/README.md
and previously enforced only by discipline:

    constitution.md                full
    nodes/<target>.md              full
    nodes/<neighbour>.md           assume + guarantee sections ONLY
    seams.jsonl                    entries naming <target>
    prefabs.jsonl                  entries whose used_by includes <target>
    gaps.md                        entries naming <target>

    Neighbour clauses never travel.

Clause bleed across nodes is how a capped plan quietly becomes an uncapped one.
An agent that reads build/ wholesale has silently converted this into a plan
whose per-task context grows with the build, which is the failure the structure
exists to prevent. This script is the affordance that makes the rule structural:
run it, hand the output to the agent, and the agent never opens build/ at all.

It also runs the `can-i-build` gate before emitting. A newly declared seam is
driven and recorded but does not block on first appearance; only a seam that
passed and then regressed blocks.

Usage:
    python3 scripts/packet.py build/ n.verifier            # packet to stdout
    python3 scripts/packet.py build/ n.verifier --stats    # size accounting only
    python3 scripts/packet.py build/ --stats-all           # degree-vs-size table
    python3 scripts/packet.py build/ n.verifier --out packet.md

Exit 0 = packet emitted. Exit 1 = refused, with the reason. Exit 2 = cannot run.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Sections of a NEIGHBOUR's contract that are permitted to travel. Everything
# else — clauses, demons, metamorphic relations, oracle, open gaps — is that
# node's own reasoning and stays in that node's packet.
NEIGHBOUR_SECTIONS = ("assume", "guarantee")

SECTION = r"^##\s+{name}\s*$(.*?)(?=^##\s|\Z)"


def die(msg, code=2):
    print(f"packet: {msg}", file=sys.stderr)
    sys.exit(code)


def load_jsonl(path):
    if not path.exists():
        return []
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            die(f"{path.name}:{i} is not valid JSON ({e.msg}) — use scripts/ledger.py to append")
    return rows


def section(text, name):
    m = re.search(SECTION.format(name=re.escape(name)), text, re.M | re.S)
    return m.group(1).strip("\n") if m else ""


def neighbours(seams, target):
    """Upstream and downstream, kept apart. A node must satisfy its downstream
    neighbours' assumptions as surely as it consumes its upstream guarantees, so
    both directions are in the packet — but the direction is labelled, because
    reading a downstream assume as an available input is its own defect."""
    up, down = [], []
    for s in seams:
        a, _, b = s.get("seam", "").partition("->")
        if b == target and a and not a.startswith("src."):
            up.append(a)
        elif a == target and b:
            down.append(b)
    return sorted(set(up)), sorted(set(down))


def gap_blocks(gaps_text, target):
    """Gap entries naming this node. Split on the entry boundary, not on lines —
    a gap is a multi-line block and half a gap is worse than none."""
    out = []
    for block in re.split(r"\n(?=\s*-\s*G\d+)", gaps_text):
        if re.search(r"^\s*-\s*G\d+", block) and target in block:
            out.append(block.rstrip())
    return out


def can_i_build(seams, target):
    """Returns (ok, notes). Only a regressed inbound seam blocks."""
    notes, blocked = [], False
    for s in seams:
        a, _, b = s.get("seam", "").partition("->")
        if b != target:
            continue
        st = s.get("status", "?")
        if st == "regressed":
            blocked = True
            notes.append(f"BLOCKED  {s['seam']} has REGRESSED — drive {s.get('driver') or '(no driver)'} before opening this node")
        elif st == "pending":
            notes.append(f"pending  {s['seam']} not yet driven ({s.get('tier')}) — does not block on first appearance")
        else:
            notes.append(f"ok       {s['seam']} {st}")
    return (not blocked), notes


def assemble(root, target, phase=None):
    cons = root / "constitution.md"
    node_f = root / "nodes" / f"{target}.md"
    if not cons.exists():
        die("constitution.md missing")
    if not node_f.exists():
        die(f"no node file for '{target}' (looked in {root / 'nodes'})")

    seams = load_jsonl(root / "seams.jsonl")
    prefabs = load_jsonl(root / "prefabs.jsonl")
    gaps_text = (root / "gaps.md").read_text(encoding="utf-8") if (root / "gaps.md").exists() else ""

    ok, notes = can_i_build(seams, target)
    up, down = neighbours(seams, target)
    my_seams = [s for s in seams if target in s.get("seam", "").split("->")]
    my_prefabs = [p for p in prefabs if target in p.get("used_by", [])]
    my_gaps = gap_blocks(gaps_text, target)

    parts = []
    parts.append(f"# Packet — {target}" + (f" — phase {phase}" if phase is not None else ""))
    parts.append(
        "\nAssembled by scripts/packet.py. This is the whole context for this task.\n"
        "Do not open build/. Neighbour contracts appear as assume + guarantee only; their\n"
        "clauses, demons, metamorphic relations and oracles are deliberately absent, because\n"
        "clause bleed across nodes is how a capped plan quietly becomes an uncapped one."
    )

    parts.append("\n## can-i-build\n")
    parts.append("\n".join(f"- {n}" for n in notes) if notes else "- no inbound seams")
    if not ok:
        parts.append("\n**Refused.** A seam that passed and then regressed blocks this node.")

    parts.append("\n---\n\n" + cons.read_text(encoding="utf-8").rstrip())
    parts.append("\n---\n\n# Target contract — read in full\n\n" + node_f.read_text(encoding="utf-8").rstrip())

    if up or down:
        parts.append("\n---\n\n# Neighbour interfaces — assume and guarantee only")
    for label, group in (("upstream — you consume these guarantees", up),
                         ("downstream — you must satisfy these assumptions", down)):
        if not group:
            continue
        parts.append(f"\n## {label}")
        for n in group:
            f = root / "nodes" / f"{n}.md"
            if not f.exists():
                parts.append(f"\n### {n}\n(no node file)")
                continue
            t = f.read_text(encoding="utf-8")
            parts.append(f"\n### {n}")
            for s in NEIGHBOUR_SECTIONS:
                body = section(t, s)
                if body:
                    parts.append(f"\n#### {s}\n{body}")

    parts.append("\n---\n\n# Seams naming this node")
    parts.append("\n".join(json.dumps(s, ensure_ascii=False) for s in my_seams) or "(none)")

    parts.append("\n---\n\n# Prefabs used by this node")
    if my_prefabs:
        for p in my_prefabs:
            parts.append(json.dumps(p, ensure_ascii=False))
        unprobed = [p["prefab"] for p in my_prefabs if not p.get("probed")]
        if unprobed:
            parts.append(
                "\n**Do not build this node.** Unprobed prefabs: " + ", ".join(unprobed) +
                "\nA library that misbehaves at this build's dimensions costs a node, and one that\n"
                "misbehaves silently costs the nodes above it too."
            )
    else:
        parts.append("(none)")

    parts.append("\n---\n\n# Gaps naming this node")
    parts.append("\n\n".join(my_gaps) or "(none)")

    parts.append(
        "\n---\n\n# Operating loop — this task\n"
        "1. Receive packet (this document)\n"
        "2. Predict the concrete fixture output and commit it — flagged nodes only\n"
        "3. Implement in a context that cannot read the prediction\n"
        "4. Diff prediction against output\n"
        "5. Surprise -> walk the tie-break order -> unresolved becomes a gap plus the reversible branch\n"
        "6. Write back as a tightened clause; a clause with no kill test is a comment\n"
        "7. Negative-check: install the demon, watch the kill test go red, record the evidence\n"
        "8. Land the output as a Foundry resource on the phase branch and read it back by RID,\n"
        "   then drive outbound seams. A node with no resource is not built\n"
        "9. Report only the surprise upward\n\n"
        "Append findings with scripts/ledger.py. Never edit build/ledger.jsonl by hand.\n"
    )

    return "\n".join(parts), ok, dict(
        upstream=len(up), downstream=len(down), seams=len(my_seams),
        prefabs=len(my_prefabs), gaps=len(my_gaps),
    )


def stats_row(root, target):
    text, ok, c = assemble(root, target)
    degree = c["upstream"] + c["downstream"]
    return dict(node=target, degree=degree, lines=len(text.splitlines()),
                chars=len(text), buildable=ok, **c)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="the build/ directory")
    ap.add_argument("node", nargs="?", help="target node id, e.g. n.verifier")
    ap.add_argument("--phase")
    ap.add_argument("--out")
    ap.add_argument("--stats", action="store_true", help="print size accounting instead of the packet")
    ap.add_argument("--stats-all", action="store_true", help="degree-vs-size table over every node")
    ap.add_argument("--json", action="store_true", help="machine-readable stats")
    a = ap.parse_args(argv)

    root = Path(a.root)
    if not root.is_dir():
        die(f"{root} is not a directory")

    if a.stats_all:
        rows = [stats_row(root, f.stem) for f in sorted((root / "nodes").glob("*.md"))]
        if a.json:
            print(json.dumps(rows, indent=2))
            return 0
        whole = sum(len(p.read_text().splitlines()) for p in root.rglob("*") if p.is_file() and p.suffix in (".md", ".jsonl"))
        print(f"{'node':<24}{'degree':>7}{'lines':>8}{'chars':>9}   vs whole build")
        for r in sorted(rows, key=lambda r: -r["degree"]):
            print(f"{r['node']:<24}{r['degree']:>7}{r['lines']:>8}{r['chars']:>9}   {r['lines']/whole:>6.1%}")
        ls = [r["lines"] for r in rows]
        print(f"\nwhole build: {whole} lines")
        print(f"packet min {min(ls)} / median {sorted(ls)[len(ls)//2]} / max {max(ls)} lines")
        print(f"largest packet is {max(ls)/whole:.1%} of the build; a packet never grows when a "
              f"node is added unless that node becomes a neighbour")
        return 0

    if not a.node:
        ap.error("a node id is required unless --stats-all is given")

    text, ok, c = assemble(root, a.node, a.phase)

    if a.stats:
        if a.json:
            print(json.dumps(stats_row(root, a.node), indent=2))
        else:
            print(f"{a.node}: degree {c['upstream'] + c['downstream']} "
                  f"(up {c['upstream']}, down {c['downstream']}), "
                  f"{c['seams']} seams, {c['prefabs']} prefabs, {c['gaps']} gaps, "
                  f"{len(text.splitlines())} lines, buildable={ok}")
        return 0 if ok else 1

    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"packet: wrote {a.out} ({len(text.splitlines())} lines)", file=sys.stderr)
    else:
        print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
