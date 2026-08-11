# node: n.assembly

## assume
[BINDING] origin: specified
- in: n.element_sets — required elements with stable opaque ids and frozen counts per document type
- in: n.ontology — canonical path index and per-path `changed_at`
- in: n.det_core — computed values carrying their inputs' paths, algorithm version, invalidation trigger
- in: n.verifier — verdicts per (claim_id, verified_at)
- in: n.drafter — claims per (slot_id, invocation) with declared grounding kind
- in: n.slot_register — slots with frozen dispositions and the pinned mix per document type
- in: n.prior_coverage — record-supplied fills, or an explicit "none found" carrying its query
- in: n.process_record — notices, comment responses, certifying statements, errata, reevaluations
- in: n.expert_queue — per expert slot, an open assignment or a received artifact, with privilege marking

## guarantee
[BINDING] origin: specified
- out: one `EmissionManifest` per emitted document; key `(document_id, emitted_at)`, unique.
  **This node produces the artifact the intent predicate is evaluated against**, and the predicate
  is checkable from the manifest alone
- element closure holds on every manifest: required = satisfied ⊎ pending ⊎ not_applicable,
  disjoint and exhaustive; a `not_applicable` entry names the rule that makes it so
- every satisfied entry names the canonical path it resolved and the input affordance that wrote
  it; an entry whose provenance is stored rather than derived is emitted in its own bucket and
  disclosed, never folded into satisfied
- **every slot is accounted for under the disposition the register froze for it**: a `drafted` slot
  by a claim id, a `record_supplied` slot by a record item or an explicit "none found" with its
  query, an `expert_required` slot by a received artifact or an open assignment naming the
  qualification and the earliest close date. An empty slot id fails emission, and a slot accounted
  for under a disposition other than its own fails emission
- the manifest carries the **disposition mix actually used** and it equals the register's pinned
  mix, so work cannot migrate between dispositions during assembly
- an `expert_required` slot with an open assignment renders as **pending with its routing stated** —
  the qualification, the artifact awaited, the lead time — never as a blank and never as a draft
- privileged material is marked and is never incorporated by reference unredacted
- every model-drafted claim is **re-verified at emission**; a verdict stamped before `emitted_at`
  is not accepted. A source-grounded claim may reuse a verdict, a state-grounded claim may not
- every computed value carries `recomputed_at` ≥ the latest `changed_at` over its inputs' paths;
  re-derivation is bound to **events** — display, incorporation, export — and to no interval
- **issuance is an act distinct from export.** Issuance is refused while any other required
  element is unsatisfied, and an issuance already made is withdrawn when an element it rested on
  ceases to be satisfied. The element recording date issued and the signature block is excluded
  from its own precondition; a `not_applicable` element is not blocking
- ordinary export is refused while a required element is unsatisfied. A distinct publication mode
  exists for the case where the rule compels publication on the day a deadline elapses; it requires
  an explicit human act and records every element unsatisfied at that moment as a durable list.
  Without the list it is an override; with it, it is a record
- no gate outcome is set by this node

## oracle
type: derivable
risk: semantic
fixture: `fixtures/assembly/manifest_expected.json` — for the overlapping-units fixture project,
the expected manifest, authored before the assembler exists

## metamorphic relations
[BINDING] origin: specified
- MR-1 (translation): change one input value ⇒ `recomputed_at` advances for exactly the values
  whose paths name it, the affected claims re-verify, and no other manifest field changes
- MR-2 (orphan isolation): mark one required element `not_applicable` ⇒ it leaves satisfied and
  pending, appears in the third bucket, and closure still holds with the same total
- MR-3 (idempotence): emit twice with no state change between ⇒ identical manifest apart from
  `emitted_at`
- MR-4 (re-execution): assemble in separate processes ⇒ byte-identical document body

## demons
- D1: emit no documents. Every clause of the intent predicate quantifies over emitted documents,
  so all five hold, the suite is green, and the cheapest conforming build produces nothing.
  kill_test: `tests/assembly/test_acceptance_corpus_non_vacuity`
  negative_check: pending — install a no-op assembler and confirm the non-vacuity assert goes red
  status: live
- D2: reuse the draft-time verdict at emission. Every claim carries a pass, the manifest is
  complete, and a state-grounded sentence asserting an acreage that changed after drafting sits in
  a signed document still carrying a passed verification.
  kill_test: `tests/assembly/test_state_claim_reverified_at_emission`
  negative_check: pending — install verdict reuse and confirm MR-1 goes red
  status: live
- D4: count an `expert_required` slot as satisfied because a coverage-gap report exists for it.
  Closure holds, the mix appears unchanged, and the document ships with a section describing what
  is missing from a study nobody has done.
  kill_test: `tests/assembly/test_expert_slot_satisfied_only_by_artifact`
  negative_check: pending — accept a gap report as a fill and confirm the assert goes red
  status: live
- D3: refuse export whenever anything is unsatisfied, including the date-and-signature element.
  Every refusal is correct-looking, and routing for signature is unreachable by construction —
  the document can never be completed because completing it requires signing it.
  kill_test: `tests/assembly/test_signature_element_excluded_from_its_own_precondition`
  negative_check: pending — remove the carve-out and confirm routing becomes unreachable
  status: live

## clauses
- [BINDING] origin: specified — a document that cannot be produced because the categorical exclusion is unavailable is the product working; a document that cannot be produced because an element has no reachable affordance is not. The manifest distinguishes them by naming the finding and the resource that caused the refusal (kill_test: `tests/assembly/test_correct_refusal_names_its_cause`) (clause: n.assembly/c1)
- [BINDING] origin: derived — a stale value renders identically to a fresh one, so the reader cannot tell, and the reader who cannot tell is the official signing the document (kill_test: `tests/assembly/test_state_claim_reverified_at_emission`) (clause: n.assembly/c2)
- [ADVISORY] origin: derived — one rule covers the stale claim and the stale cached verdict, because two rules for one hazard is how the hazard survives: each is obeyed in its own layer and the gap between them is where the failure lives (clause: n.assembly/c3)
## open gaps
- G021 — whether a `not_applicable` bucket is the right third state, or whether the rule admits
  only satisfied and unsatisfied. Assumed: three buckets, because a category never adopted could
  otherwise never be routed. Reversible: yes.
  Blocks: MR-2.
