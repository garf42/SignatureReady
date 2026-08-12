# SignatureReady — contract-graph build

A parallel build of the same product, structured so **context per task is O(node degree), not
O(build size)**. There are no phase handoff prompts and no session summaries. A fresh session
needs a node id and a phase.

```
build/
├── constitution.md      capped at 200 lines, read by every agent, every task (currently 170)
├── nodes/*.md           20 nodes; only that node's agent reads its file
├── seams.jsonl          53 edges; 27 replay, 26 static
├── prefabs.jsonl        16 external dependencies, each with its probe
├── gaps.md              36 open decisions, each with a volatility expiry
└── ledger.jsonl         append-only, queried by node id, never read whole
```

## Start here — the gate is red on purpose

```bash
python3 scripts/check.py build/ --phase 0
```

Returns **11 violations, all of them `probed is false`.** That list is what remains of Phase −1's
work order, not a defect in the plan. Nothing else fails: the cap holds, edge closure holds, every
node has an oracle and a risk axis, every BINDING clause names a kill test, every demon carries a
pending negative check.

**5 of the 16 prefabs are probed** — every one that this environment can reach. Each ran real code
against a real published artifact at this build's dimensions, twice, and each was then attacked by
an independent verifier. Four of the five changed a method and none changed a guarantee, which is
what the order of work says should happen. Read the verdicts in `prefabs.jsonl`, not here.

**11 are not probed, and none for want of trying.** Ten are blocked on one of two environment facts
— G033, the network policy that refuses the three primary sources, and G034, the absent Foundry
enrollment. The eleventh, `foundry-cli-superrepo`, ran its whole offline half and is blocked only on
the enrollment; that half established the SuperRepo shape and proved the Ontology-as-code toolchain
runs with no enrollment at all, so `n.ontology` is no longer waiting on it.

The advice to **probe `foundry-cli-superrepo` first** stands and has been followed as far as it can
be. The finding that matters for planning: the CLI is not on npm or PyPI in any form. It is served
from each enrollment's own artifacts registry, so this probe cannot be delegated to an unenrolled
machine or agent at all — which is a stronger constraint than "may not be available on this
enrollment", and a constraint on *who* can run Phase −1 rather than on what it costs.

**Do not build a node whose prefabs are unprobed** — a library that misbehaves at this build's
dimensions costs a node, and one that misbehaves silently costs the nodes above it too.
`scripts/packet.py` says so in the packet, so an agent does not have to remember.

## Packet assembly — the rule that keeps context flat

Agents never read `build/`. Per task, assemble:

```
constitution.md                full
nodes/<target>.md              full
nodes/<neighbour>.md           assume + guarantee sections ONLY
seams.jsonl                    entries naming <target>
prefabs.jsonl                  entries whose used_by includes <target>
gaps.md                        entries naming <target>
```

Neighbour **clauses never travel.** Clause bleed across nodes is how a capped plan quietly
becomes an uncapped one, and it is the failure this structure exists to prevent.

## Order of work

**Phase −1 — probes.** Run the sixteen. Record results in `prefabs.jsonl`. Several will change
a node's method and none should change a node's guarantee; if a probe result changes a
guarantee, that is a finding worth a ledger entry.

**Phase 0 — walking skeleton.** Drive one row end to end through all twenty nodes, however
crude. The skeleton is allowed to be embarrassing. It is not allowed to skip a node.
**Scope it explicitly: this is a liveness check on the graph, never an acceptance signal.** It
says nothing about whether any node is correct. Its only job is to make "half the graph was never
driven" structurally impossible.

Drive it once per document type, not once. A skeleton that only runs the categorical-exclusion
branch leaves four of five branches undriven, which is the exact failure the skeleton exists to
make impossible.

**Then, per node, the nine-step loop in the constitution.** Stabilise determinism before any
negative check — on a flaky test command a demon can appear killed by chance, and every kill test
downstream is then evidence of nothing.

**`can-i-build` gate.** Before opening a node, query the seam register: are its inbound seams
verified? A newly declared seam is driven and recorded but does not block on first appearance.
Only a seam that passed and then **regressed** blocks.

**Phase boundaries — audit subagent.** Contract-set consistency, undriven seams, never-red
assertions, vacuity, prose drift, unprobed prefabs, pending negative checks. Its context blowout
is disposable: it reads every contract, dies, and only a structured verdict list propagates.
Structured fields during the build; prose only at the end.

## Scope — all five document types, all the way to signature

Every pathway ends signature-ready. `n.slot_register` decomposes each required element into slots
and freezes each slot's disposition: **drafted** by a model against a declared grounding kind,
**record_supplied** from prior coverage or the proposal record, or **expert_required** and routed
to a qualification with an artifact type and a lead time.

That register is the honesty mechanism. Its disposition mix per document type is **pinned**, so
work cannot migrate from drafted to expert-required to make a build easier, and cannot migrate the
other way to make a demo look better. Either direction fails the pin before it reaches the manifest.

The user who is not a NEPA expert sees, per document type, before starting: what the system will
draft, what it can pull from the record, and which disciplines they must route to — with the
artifact awaited and the earliest date that section can close. An expert slot accepts an uploaded
artifact only; AI on it is restricted to coverage-gap checking, and a gap report is never promoted
into slot content.

`n.expert_directory` closes the loop in-app: search by qualification, get four lanes in cost order —
the lead agency's own specialists, a cooperating-agency designation, prior preparers attested from
the corpus, then the county's own roster — each holder shown beside the page-anchored evidence that
they prepared what they are claimed to have prepared. The app composes the request package carrying
the element citations the artifact must address, tracks the engagement, receives the artifact, and
writes the coverage-gap result back as the roster's only ranking evidence.

**Two rules make that safe rather than a scraped contact database.** A holder is an organisation,
agency or position by default; an individual only where a channel is published by an agency or the
person opted in. And track record is attested facts — what was prepared, when, whether it closed the
gap — never an aggregate score, because a score invites a threshold and a threshold is a
qualification rule nobody wrote.

## Landing in Foundry — there is no import step

Verified against Palantir's documentation, August 2026 — confirm against your enrollment.

**The framing to drop first.** "Build it, then import it" is the expensive path and it is avoidable.
Both routes below produce Foundry resources as the build proceeds, so nothing is ever imported —
the artifacts were Foundry artifacts from the first commit.

### Primary route — SuperRepo (beta, released the week of 2026-08-03)

A **SuperRepo** is a single monorepo holding **Ontology-as-code** — object types, links, interfaces
and actions declared in TypeScript — together with **TypeScript v2 functions** and the **React
application**, developed locally through the **Foundry CLI** with an embedded Ontology preview that
reproduces Ontology behaviour on your machine. Code definitions are the source of truth and
materialise as real entities on deployment. Types created in the UI import into code and vice versa,
so nothing is siloed by where it was created. The repo compiles natively into a **Marketplace
product**: a self-contained, reproducible, cryptographically signed bundle installable on one or
more enrollments.

That is the entire "import" problem, dissolved. `foundry create` locally, `foundry deploy` when ready.

**What SuperRepo does not cover yet**, from Palantir's own roadmap page — Python functions, **data
pipeline support**, Automate, an agent SDK, and **external source support for SuperRepo functions**.
The last one binds `n.drafter` directly.

### The repo split, and where it falls (G031)

| Repo | Nodes | Why |
| --- | --- | --- |
| **SuperRepo** | `n.ontology` and everything above it — det core, verifier, slot register, assembly, issue register, process record, expert queue, expert directory, surface | Ontology-as-code + TS v2 functions + React is exactly SuperRepo's current coverage |
| **Python transforms repo**, created by MCP | the seven ingestion and extraction nodes — rule corpus, authority ledger, element sets, enumerations, CE catalogue, project state, precedent | SuperRepo has no pipeline support yet; Palantir lists it as planned |

The boundary falls on `n.ontology`, which is where the contract graph already cuts. That is a
confirmation the decomposition was drawn somewhere defensible — not a coincidence to lean on. When
pipeline support lands, two repos collapse into one and **no guarantee changes**.

### Fallback route — Palantir MCP only (G032)

SuperRepo is beta and may not be enabled on the training enrollment. **Probe that before anything
else**; it is the one answer that changes the shape of the build rather than the method inside a
node. The fallback is fully supported and fully agent-drivable: ontology object, link and action
types created **on a branch** through the MCP ontology tools; a TypeScript Functions repository
created once by hand and cloned locally; the React application connected through
`connect_to_dev_console_app`, which attaches a non-Foundry Git repository to a Developer Console
application; SDK regeneration through `generate_new_ontology_sdk_version` and `install_sdk_package`.

Either way, the pipeline nodes go through `create_python_transforms_code_repository`,
`create_and_write_to_foundry_dataset`, `build_datasets` and `get_or_create_network_egress_policy`,
with `get_build_status` and `get_job_status` giving an agent readback on its own CI — which in the
parallel build required a human to relay the result.

### The demon this closes

Build everything locally with beautiful local fidelity and land nothing until the end. Every node
green, every kill test red-then-green, every seam driven — and the first Foundry resource appears in
week eleven, when the shape of the platform starts disagreeing with the shape of the code and there
is no time left to find out which is wrong. That is inert foresight aimed at the platform instead of
the data.

**The kill is in the operating loop, step 8:** land the output as a Foundry resource on the phase
branch and read it back by RID, *then* drive outbound seams. A node with no resource is not built.
Read-back has a real runtime — `view_foundry_object_type`, `get_foundry_dataset_schema`,
`get_build_status`, `get_resource_graph` — so this is a check rather than an intention.

## What was searched and not built

PNNL's PermitAI programme already supplies the NEPA corpus and the models trained on it
(`NEPATEC 2.0`, `PermitTEC`), and those are consumed here as sources `src.nepatec` and the
litigation join, not rebuilt. No Foundry Marketplace product covers county-side NEPA assembly.
The gap this build fills is the assembly-to-signature workflow, not the corpus.
