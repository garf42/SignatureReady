# node: n.surface

## assume
[BINDING] origin: specified
- in: n.assembly — one `EmissionManifest` per emitted document, with closure, slots, verdicts, freshness
- in: n.det_core — computed values carrying their inputs' paths, algorithm version, invalidation trigger
- in: n.ontology — canonical path index; every data-bearing element resolves to exactly one path
- in: n.slot_register — slots with frozen dispositions, qualifications and lead times
- in: n.expert_queue — per expert slot, an assignment or a received artifact, and the critical path
- in: n.expert_directory — attested holders by qualification, in four lanes, with their evidence

## guarantee
[BINDING] origin: specified
- out: an OSDK React application; per screen, a `BindingReport` emitted as data — one row per
  data-bearing element with the canonical path it resolves, its source and its invalidation trigger
- **every required element across every in-scope document type has a reachable input affordance,
  named.** The set difference between required elements and available affordances is emitted and
  is empty, or the shortfall is listed by element id with the reason and the node that closes it.
  An affordance that accepts input and writes nowhere is not an affordance
- the blocking summary renders, beside each unsatisfied citation, **the affordance that would
  satisfy it** — and where the slot's disposition is `expert_required`, the qualification to route
  to, the artifact awaited and the earliest close date instead. "Element (iii) is unsatisfied" tells
  a county officer they are blocked; naming the affordance or the discipline tells them what to do
- **all five document types are reachable in the interface**, and each shows its own slot
  disposition mix: how much is drafted, how much comes from the record, how much needs an expert.
  A user who is not a NEPA expert can see, before starting, what they can finish and what they
  cannot
- an expert-required slot presents the routing, a **search for holders by qualification** returning
  the four lanes in cost order with each holder's attestation visible beside it, the request package
  for review before it is sent, the artifact upload, and — once the artifact is received — the
  coverage-gap report against the element's requirements. The gap report is never presented as
  content and is never editable into content
- a holder is never displayed without its attestation, and no suitability score is displayed at all;
  the user sees what a holder has demonstrably prepared, not a number ranking them
- required elements are shown as unsatisfied citations, never as a completion percentage
- every displayed computed value names its source and its invalidation trigger; a displayed value
  with neither is a defect, and the node ends with an audit of every call site against that rule
- each of the five determinations at 7 CFR 1b.11(a)(46) is recorded by an explicit human act
  carrying an actor principal distinct from any service principal; the screen presents computed
  evidence and a recommendation and sets no outcome
- routing is to a **position**, never to a person; no state reachable by the system is `signed`
- one repeated component covers the screening list, issue disposition, comment responses,
  screening tables, alternative elimination and effects exclusion: item, constrained select,
  one-line justification, evidence links
- the module loads outside the bundler and the pure presentation renders with its data supplied as
  values. A clean bundler build is not evidence — bundlers check syntax, not module load
- no expected duration is stated anywhere; elapsed and remaining time against statutory deadlines only

## oracle
type: derivable
risk: semantic
fixture: `fixtures/surface/affordance_coverage.json` — the expected required-element-to-affordance
map per document type, authored before any screen exists

## metamorphic relations
[BINDING] origin: specified
- MR-1 (orphan isolation): record one determination ⇒ the blocking summary loses exactly that
  citation and gains nothing
- MR-2 (idempotence): load the same screen twice ⇒ identical displayed computed values and
  identical invalidation triggers
- MR-3 (translation): change an ontology value a screen displays ⇒ the displayed value moves on
  next display. A screen that does not move is reading a cache that stopped tracking
- MR-4 (equivalent rewrite): reach a required element through a different navigation path ⇒ the
  same affordance, writing the same canonical path

## demons
- D1: build an affordance for every required element that renders a control and discards its
  input. The producibility difference is empty, every element has a named affordance, and nothing
  the county officer types is stored.
  kill_test: `tests/surface/test_affordance_writes_its_path`
  negative_check: pending — install a control with no action binding and confirm the write-back
  assert goes red
  status: live
- D2: read the function verdict from a hook cache without declaring the state it depends on. Every
  test passes, the build is clean, and a recorded finding changes the ontology while the screen
  goes on displaying the verdict computed before it.
  kill_test: `tests/surface/test_displayed_value_moves_on_state_change`
  negative_check: pending — drop the dependency declaration and confirm MR-3 goes red
  status: live
- D3: record a determination with the drafting service principal as actor. Provenance clause 4
  holds — there is an actor, a timestamp and an evidence hash — and no human decided anything.
  kill_test: `tests/surface/test_actor_principal_is_not_a_service_principal`
  negative_check: pending — install the service principal as actor
  status: live

## clauses
- [BINDING] origin: specified — never infer the invoked function version from the import list; read `version` **and `isFixedVersion`** out of the generated client, and where `isFixedVersion` is false report the invoked version as **unknown** rather than reporting the literal, because the client then sends no version and the server resolves the latest published — possibly pre-release — per call; write calls correct under every version the client might resolve to (kill_test: `tests/surface/test_import_version_matches_client_version`) (clause: n.surface/c1)
- [BINDING] origin: derived — where a query documents an optional parameter and the React binding cannot express its absence, the cast carries a comment naming the mismatch; a bare cast hides an API mismatch, which is the defect and not the fix (kill_test: `tests/surface/test_optional_param_omitted_not_sentinelled`) (clause: n.surface/c2)
- [ADVISORY] origin: derived — six regulatory processes, one component. Building six bespoke screens is the failure mode, and it looks like progress while it happens (clause: n.surface/c3)
## open gaps
- G022 — `@osdk/react-components` ships `ObjectTable` and other prebuilt components. Unprobed at
  this build's shape. Assumed: hand-built list component. Reversible: yes — swapping in a prebuilt
  table is local. Blocks: the repeated-component build.
