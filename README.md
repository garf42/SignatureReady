# SignatureReady

A NEPA assembly-to-signature workflow for county-side environmental documents, built as a
contract graph so that **context per task is O(node degree), not O(build size)**.

The plan is in [`build/`](build/). Read [`build/README.md`](build/README.md) first — it is the
plan's own account of itself. This file is about working in the repository.

```
build/            the plan: constitution, 20 node contracts, seams, prefabs, gaps, ledger
scripts/          the machinery that makes the plan enforceable rather than aspirational
tests/build/      negative checks on that machinery
tests/probes/     one file per prefab probe, at the paths build/prefabs.jsonl already names
```

## Working on a node

Agents never read `build/`. Assemble a packet instead:

```bash
python3 scripts/packet.py build/ n.verifier
```

That emits the whole context for one task: the constitution in full, the target contract in
full, neighbour contracts as **assume + guarantee only**, and exactly the seams, prefabs and
gaps naming that node. It runs the `can-i-build` gate first and refuses if an inbound seam has
regressed. Neighbour clauses never travel — clause bleed across nodes is how a capped plan
quietly becomes an uncapped one, and it is the failure the structure exists to prevent.

The claim is measured, not asserted:

```bash
python3 scripts/packet.py build/ --stats-all
```

Degree 15 gives a 779-line packet; degree 1 gives 306. Adding a node that is not a neighbour
leaves a packet byte-identical, which is pinned by
`tests/build/test_packet.py::test_adding_a_non_neighbour_node_changes_no_packet`.

## The gate

```bash
python3 scripts/check.py build/ --phase 0
```

**It is red on purpose.** Every violation it reports today is `probed is false`, and that list
is Phase −1's work order rather than a defect in the plan. Nothing else fails: the cap holds,
edge closure holds in both directions, every node has an oracle and a risk axis, every BINDING
clause names a kill test, every demon carries a pending negative check, and the graph is a DAG.

Because it stays red until Phase −1 completes, CI does not gate on its exit code. CI gates on
the assertion that the only thing wrong is unprobed prefabs:

```bash
python3 tests/build/test_gate.py      # structural invariants + negative checks on the gate
python3 tests/build/test_packet.py    # packet assembly stays capped
```

Both must be green. They go red the moment a structural property breaks, and stay green while
Phase −1 is merely incomplete.

## Recording a finding

Never edit `build/ledger.jsonl` or `build/seams.jsonl` by hand — parallel appends interleave
mid-line and corrupt them.

```bash
python3 scripts/ledger.py build/ledger.jsonl --node n.verifier \
  --surprise "..." --resolution "..." \
  --clause "..." --kill-test tests/verifier/test_x \
  [--rediscovered n.assembly/c3]
```

An entry with no clause is refused, because a fix with no clause behind it is a fix that
recurs. `--rediscovered` names a clause id — every clause in every node file carries one, as
`(clause: <node>/c<n>)` — and the resulting rediscovery rate is the only instrument this build
has for telling whether packet assembly is working.

Query it per node; it is never read whole:

```bash
python3 scripts/ledger.py build/ledger.jsonl --query n.verifier
```

## Order of work

Phase −1 is probes. **Do not build a node whose prefabs are unprobed** — `packet.py` says so in
the packet. See [`PHASE-MINUS-1.md`](PHASE-MINUS-1.md) for what has been probed, what is
blocked, and why.

Phase 0 is the walking skeleton: one row end to end through all twenty nodes, once per document
type. It is allowed to be embarrassing. It is not allowed to skip a node, and it is a liveness
check on the graph rather than an acceptance signal.

Then, per node, the nine-step operating loop in the constitution.
