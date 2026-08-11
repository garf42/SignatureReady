#!/usr/bin/env python3
"""Make the plan's account of itself self-checking.

build/README.md states counts — nodes, seams, the replay/static split, prefabs,
gaps, the constitution's line count, and how many probes Phase -1 owes. Those
numbers are read by every agent deciding what work remains, and nothing was
keeping them honest.

They had already drifted. The README said "Run the fourteen" while the register
held sixteen prefabs, two paragraphs after saying "16 violations" itself. An
agent that runs fourteen leaves two prefabs unprobed, and an unprobed prefab is
exactly what blocks a node from being opened. Prose drift is on the phase-boundary
audit's duty list for this reason; this file moves it off that list and into CI.

Runs with pytest, or standalone:  python3 tests/build/test_plan_prose.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build"

WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20,
}


def readme():
    return (BUILD / "README.md").read_text(encoding="utf-8")


def jsonl(name):
    return [json.loads(l) for l in (BUILD / name).read_text().splitlines() if l.strip()]


def find(pattern, text=None, word=False):
    """Pull one number out of the README, failing loudly if the sentence it lives
    in has been rewritten. A silently-absent claim is how this check goes vacuous."""
    t = text if text is not None else readme()
    m = re.search(pattern, t, re.M | re.I)
    assert m, f"README no longer contains the claim matched by {pattern!r} — update this test with it"
    raw = m.group(1)
    return WORDS[raw.lower()] if word else int(raw)


def test_node_count_matches():
    actual = len(list((BUILD / "nodes").glob("*.md")))
    assert find(r"nodes/\*\.md\s+(\d+) nodes") == actual


def test_seam_count_and_tier_split_match():
    seams = jsonl("seams.jsonl")
    total = find(r"seams\.jsonl\s+(\d+) edges")
    replay = find(r"seams\.jsonl\s+\d+ edges; (\d+) replay")
    static = find(r"seams\.jsonl\s+\d+ edges; \d+ replay, (\d+) static")
    assert total == len(seams), f"README says {total} edges, register has {len(seams)}"
    assert replay == sum(1 for s in seams if s["tier"] == "replay")
    assert static == sum(1 for s in seams if s["tier"] == "static")
    assert replay + static == total, "the tier split does not add up to the edge count"


def test_prefab_count_matches():
    assert find(r"prefabs\.jsonl\s+(\d+) external dependencies") == len(jsonl("prefabs.jsonl"))


def test_gap_count_matches():
    stated = find(r"gaps\.md\s+(\d+) open decisions")
    actual = len(re.findall(r"^\s*-\s*G\d+\b", (BUILD / "gaps.md").read_text(), re.M))
    assert stated == actual, f"README says {stated} gaps, gaps.md has {actual}"


def test_constitution_line_count_matches():
    stated = find(r"constitution\.md.*?\(currently (\d+)\)")
    actual = len((BUILD / "constitution.md").read_text().splitlines())
    assert stated == actual, f"README says the constitution is {stated} lines, it is {actual}"


def test_probe_count_owed_by_phase_minus_1_matches_the_register():
    """The drift that prompted this file. "Run the fourteen" against a register of
    sixteen leaves two prefabs unprobed, and an unprobed prefab blocks its node."""
    stated = find(r"Phase\s*−?-?1\s*—\s*probes\.\*\*\s*Run the (\w+)\.", word=True)
    assert stated == len(jsonl("prefabs.jsonl")), (
        f"README tells Phase -1 to run {stated} probes; the register holds "
        f"{len(jsonl('prefabs.jsonl'))}. Every unprobed prefab blocks a node."
    )


def test_stated_violation_count_matches_the_gate():
    """The README opens by telling the reader what the gate returns. If that number
    is stale the reader cannot tell a fresh violation from the documented baseline."""
    import subprocess
    stated = find(r"Returns \*\*(\d+) violations")
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check.py"), str(BUILD), "--phase", "0"],
        capture_output=True, text=True).stdout
    actual = len([l for l in out.splitlines() if l.startswith("FAIL")])
    assert stated == actual, (
        f"README says the gate returns {stated} violations; it returns {actual}. "
        "Re-state it as probes land, so the baseline stays legible."
    )


def test_evidence_split_matches_the_register():
    """The README's original two-way split — "Six ... Ten" — matched no reading of
    the register. There are three kinds of prior evidence here, not two: evidence
    carried from the parallel build, evidence carried from Palantir's documentation,
    and none. Documentation is the weaker kind and is why those two are still probes,
    so folding them into either bucket loses the distinction that matters.
    """
    prefabs = jsonl("prefabs.jsonl")
    parallel = [p for p in prefabs if "carried evidence from a parallel build" in p["result"]]
    none = [p for p in prefabs if "no prior evidence" in p["result"]]
    documented = [p for p in prefabs if p not in parallel and p not in none]

    stated_parallel = find(r"(\w+) of the sixteen carry evidence from the parallel build", word=True)
    stated_documented = find(r"(\w+) more — `[^`]+` and `[^`]+` — carry evidence from Palantir", word=True)
    stated_none = find(r"(\w+) have no prior evidence at all", word=True)

    assert stated_parallel == len(parallel), (
        f"README says {stated_parallel} carry parallel-build evidence; register shows {len(parallel)}")
    assert stated_documented == len(documented), (
        f"README says {stated_documented} carry documentation evidence; register shows {len(documented)}")
    assert stated_none == len(none), (
        f"README says {stated_none} have no prior evidence; register shows {len(none)}")
    assert stated_parallel + stated_documented + stated_none == len(prefabs), (
        "the three-way evidence split does not add up to the prefab count")


def main():
    if not BUILD.is_dir():
        print(f"cannot run: missing {BUILD}", file=sys.stderr)
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
