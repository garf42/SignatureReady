# Gaps

Reviewed in batch at phase boundaries, never mid-build. Every gap is a decision already taken by
default; the entry records which decision and how reversible it is.

- G001 — node: n.rule_corpus — volatility: low — last_reviewed: phase-0
  Paragraph citation uniqueness across 7 CFR Part 1b is assumed, not verified.
  Assumed: unique. Reversible: yes (a composite key change is local to one node).
  Blocks: MR-3 on n.rule_corpus.

- G002 — node: n.authority_ledger — volatility: medium — last_reviewed: phase-0
  Re-check cadence for authority currency. The rule is a versioned instrument and nothing in this
  workspace can supply the right interval.
  Assumed: re-check on every build of the node, carrying the retrieval timestamp forward. No
  interval invented. Reversible: yes.
  Blocks: the currency check on every authority.

- G003 — node: n.rule_corpus — volatility: low — last_reviewed: phase-0
  Timezone basis for effective dates is not declared in the source.
  Assumed: date-only, no timezone arithmetic anywhere. Reversible: yes.
  Blocks: nothing today; it blocks any deadline computed to an hour.

- G004 — node: n.rule_corpus — volatility: medium — last_reviewed: phase-0
  Whether ecfr.gov exposes a structured API for Part 1b at paragraph granularity.
  Assumed: bulk retrieval and parse. Reversible: yes (the guarantee is grain, not method).
  Blocks: the n.rule_corpus probe.

- G005 — node: n.det_core — volatility: low — last_reviewed: phase-0
  Calendar basis for the one-year EA and two-year EIS deadline arithmetic is not stated.
  Assumed: calendar year from the trigger date. The boundary fixture is authored non-asserting.
  Reversible: yes. Blocks: MR-1 on the deadline functions.

- G006 — node: n.authority_ledger — volatility: low — last_reviewed: phase-0
  federalregister.gov rate limit and page size at this build's volume.
  Assumed: adequate. Reversible: yes. Blocks: the n.authority_ledger probe.

- G007 — node: n.ontology — volatility: low — last_reviewed: phase-0
  PIC v1.2 crosswalk (entity, property) uniqueness.
  Assumed: unique. Reversible: yes. Blocks: the PIC mapping count in n.ontology's guarantee.

- G008 — node: n.ce_catalog — volatility: low — last_reviewed: phase-0
  Whether src.ce_explorer declares its units or leaves them implied.
  Assumed: implied, so no comparison is performed against its values. It is a reconciliation
  input and never a citation target. Reversible: yes. Blocks: the reconciliation table.

- G009 — node: n.project_state — volatility: low — last_reviewed: phase-0
  fsgeodata feature id uniqueness per layer.
  Assumed: unique per layer. Reversible: yes. Blocks: MR-2 on n.project_state.

- G010 — node: n.project_state — volatility: high — last_reviewed: phase-0
  Projection and linear unit vary per fsgeodata layer and must be read, not assumed.
  Assumed: read at ingestion, recorded per layer, no measure crosses a projection without a
  recorded transformation. Reversible: yes. Blocks: MR-4 on n.project_state.

- G011 — node: n.precedent — volatility: medium — last_reviewed: phase-0
  src.nepatec row grain — one row per document or per chunk.
  Assumed: one row per document with a page-level text field. Reversible: yes (the reader
  changes, the guarantee does not). Blocks: the n.precedent probe.

- G012 — node: n.precedent — volatility: medium — last_reviewed: phase-0
  Selectivity of a USDA/USFS filter over src.nepatec is unmeasured.
  Assumed: non-trivial. A silently empty filter is the failure this measures against.
  Reversible: yes. Blocks: the acceptance corpus's precedent coverage.

- G013 — node: n.element_sets — volatility: medium — last_reviewed: phase-0
  The frozen element counts in the intent predicate are transcription-derived and unverified
  against eCFR. Agreement between two readings of the same source detects transcription error;
  it does not confirm the source.
  Assumed: correct. Reversible: yes, and cheaply — the counts live in one fixture.
  Blocks: the non-vacuity clause of the intent predicate.

- G014 — node: n.enumerations — volatility: medium — last_reviewed: phase-0
  The introducing clause for three enumerated sets is reported absent from the transcription.
  Assumed: closure = undetermined, modelled open, flagged. Reversible: yes.
  Blocks: MR-2 on n.enumerations for those three sets.

- G015 — node: n.ce_catalog — volatility: medium — last_reviewed: phase-0
  The full 1b.4(c) list does not appear in the transcription.
  Assumed: n.rule_corpus supplies it. Until then the catalogue is emitted provisional and the
  interface says so — an absent option and a blocked option are different states.
  Reversible: yes. Blocks: MR-1 on n.det_core for c-list categories.

- G016 — node: n.ontology — volatility: high — last_reviewed: phase-0
  Palantir MCP creates and updates object, link and action types on a branch, and is documented
  not to write ontology data.
  Assumed: types by MCP, data by dataset write plus a pipeline. Reversible: yes.
  Blocks: the walking skeleton's ontology step.

- G017 — node: n.det_core — volatility: high — last_reviewed: phase-0
  Where TypeScript v2 functions live. **Superseded in substance by SuperRepo**, which holds
  Ontology-as-code, TypeScript v2 functions and the React application in one locally-developed
  monorepo — so the hand-created functions repository this gap assumed is no longer the only path.
  Assumed: SuperRepo where available, because it removes the landing step entirely. Fallback, if
  the enrollment does not have the beta: a functions repository created once by hand and cloned
  through Palantir MCP, which is the fully-supported pre-SuperRepo path.
  Reversible: yes, and the fallback is the previously assumed route. Blocks: the walking skeleton's
  function step, and it is gated on G032.

- G018 — node: n.verifier — volatility: medium — last_reviewed: phase-0
  What "literal substring" admits: whitespace collapse, unicode dash folding, case.
  Assumed: byte-exact with no normalisation until a normalisation rule is declared and named in
  the verdict. Reversible: yes, one named rule at a time. Blocks: MR-2 on n.verifier.

- G019 — node: n.drafter — volatility: high — last_reviewed: phase-0
  Palantir MCP exposes no AIP Logic tool, so the drafter's host surface is either AIP Logic
  configured by hand or a function calling a model through platform model access.
  Assumed: a function, because it is reversible and an agent can build it. The emission contract
  is identical either way. **One new constraint:** SuperRepo functions cannot yet call APIs outside
  the platform, so if model access is an external call the drafter cannot be a SuperRepo function
  today and lands in a transforms repository or a compute module instead. If platform model access
  is internal, it can. That distinction is the probe.
  Reversible: yes. Blocks: the walking skeleton's drafting step.

- G020 — node: n.evals — volatility: medium — last_reviewed: phase-0
  The signal hierarchy's authority ordering is asserted, not measured.
  Assumed: post-implementation reality, then external challenge, then signature, then edits and
  rejections. No signal reaches a verifier, a value set, or an element requirement in any
  ordering. Reversible: yes — the ordering is a stored table. Blocks: n.evals's prohibition test.

- G021 — node: n.assembly — volatility: low — last_reviewed: phase-0
  Whether a not_applicable bucket is the right third closure state.
  Assumed: three buckets, because a category never adopted could otherwise never be routed and
  the signature element would be its own precondition. Reversible: yes.
  Blocks: MR-2 on n.assembly.

- G022 — node: n.surface — volatility: medium — last_reviewed: phase-0
  Whether @osdk/react-components can host the one repeated component — a constrained select plus
  a free-text justification plus evidence links, per row.
  Assumed: hand-built. Reversible: yes, swapping in a prebuilt table is local.
  Blocks: the repeated-component build.

- G023 — node: n.slot_register — volatility: high — last_reviewed: phase-0
  No rule enumerates which slots require a qualified professional. Interdisciplinary preparation is
  required and its composition is at the responsible official's sole discretion, with no list.
  Assumed: the qualification set is derived from practice, tagged derived, and re-reviewed at every
  phase boundary rather than frozen. Reversible: yes.
  Blocks: the pinned disposition mix on n.slot_register.

- G024 — node: n.prior_coverage — volatility: medium — last_reviewed: phase-0
  Substantial sameness has no numeric test in the rule.
  Assumed: qualitative human judgment against computed evidence, never a score — a score invites a
  threshold and a threshold is a rule nobody wrote. Reversible: yes.
  Blocks: MR-1 on n.prior_coverage.

- G025 — node: n.issue_register — volatility: low — last_reviewed: phase-0
  Whether one issue may carry two dispositions simultaneously.
  Assumed: yes, many-to-many, because supplementing the analysis and modifying the action are not
  exclusive. Reversible: yes. Blocks: MR-4 on n.issue_register.

- G026 — node: n.process_record — volatility: high — last_reviewed: phase-0
  The pre-decisional objection process does not apply to categorical exclusions but does apply on
  the EA and EIS branches, and its text has been under revision.
  Assumed: not built against until re-verified from primary source; the reviewing-officer
  derivation runs against an injected organisational structure explicitly flagged synthetic.
  Reversible: yes. Blocks: the objection affordances on the EA and EIS branches.

- G027 — node: n.expert_queue — volatility: medium — last_reviewed: phase-0
  Whether the critical path violates the rule against stating expected durations.
  Assumed: permitted, because it is a sum of lead times each supplied by the expert who will do the
  work, not an estimate of how long review takes. The distinction is load-bearing and thin, and it
  is recorded here rather than decided quietly. Reversible: yes — the field is display-only.
  Blocks: MR-3 on n.expert_queue.

- G028 — node: n.expert_directory — volatility: medium — last_reviewed: phase-0
  Whether preparer and consulted-persons sections are consistently present in the NEPA corpus and
  extractable at useful precision.
  Assumed: present in a minority of documents; the node reports its extraction yield rather than
  implying coverage, so a thin lane reads as thin instead of as an absence of qualified people.
  Reversible: yes. Blocks: the prior-preparer lane, and MR-1 on n.expert_directory.

- G029 — node: n.expert_directory — volatility: high — last_reviewed: phase-0
  The standing tension between the constitution's prohibition on real personally identifiable
  information in any environment and a capability whose value depends on knowing who did the work.
  Assumed: a holder is an organisation, agency or position by default; an individual is a holder
  only where a contact channel is published by an agency as a point of contact or the person has
  opted in; outside production every individual name is synthetic and flagged. Attestations are
  page-anchored so a claim about a real party is always checkable against its source.
  Reversible: yes — the resolution is a policy on one field and a channel-provenance check.
  Blocks: any production deployment of n.expert_directory.

- G030 — node: n.expert_directory — volatility: medium — last_reviewed: phase-0
  Whether in-app contact means the application transmits the request, or composes a request package
  the user sends through their own channel.
  Assumed: the application composes, tracks, receives and gap-checks — every piece of state that
  matters is in-app — and transmission is a channel integration probed before it is built, because
  an outbound message from a county to a Federal specialist is a record in itself.
  Reversible: yes. Blocks: the engagement send step on n.expert_directory.

- G031 — node: n.ontology — volatility: high — last_reviewed: phase-0
  Repository topology — which nodes land in which Foundry artifact.
  Assumed, and the cut falls exactly where the graph already cuts: **n.ontology and everything above
  it** — the deterministic core, the verifier, the slot register, assembly, the issue register, the
  process record, the expert queue and directory, the surface — go in the **SuperRepo**, because
  they are Ontology-as-code, TypeScript v2 functions and React, which is precisely SuperRepo's
  current coverage. **The seven nodes below it** — rule corpus, authority ledger, element sets,
  enumerations, CE catalogue, project state, precedent — go in a **Python transforms repository**
  created through Palantir MCP, because SuperRepo has no data pipeline support yet and Palantir's
  roadmap page lists it as planned rather than present.
  That the boundary lands on n.ontology is a confirmation the decomposition was drawn somewhere
  defensible, not a coincidence to lean on. Reversible: yes — pipeline support arriving collapses
  two repositories into one and changes no guarantee. Blocks: the walking skeleton's repo layout.

- G032 — node: n.ontology — volatility: high — last_reviewed: phase-0
  Whether SuperRepo is enabled on this training enrollment at all. It is beta as of the week of
  2026-08-03 and the documentation states plainly it may not be available.
  Assumed: available. **Probe this before any other probe** — it is the only gap whose answer
  changes the topology of the whole build rather than the method inside one node.
  Fallback, fully supported and fully MCP-driven: ontology types through the MCP ontology tools on
  a branch, a hand-created TypeScript Functions repository cloned locally, and the React
  application connected to a Developer Console app through `connect_to_dev_console_app`.
  Reversible: yes, but not cheaply once code exists — which is why it is probed first.
  Blocks: G017, G019, G031, and the walking skeleton.
