# node: n.drafter

## assume
[BINDING] origin: specified
- in: n.ontology — canonical path index; values addressable by named path
- in: n.precedent — page-anchored chunks; every chunk a substring of its named page
- in: n.enumerations — constrained value sets with closure classification
- in: n.slot_register — slots with a frozen disposition and, where drafted, a required grounding_kind
- in: n.prior_coverage — ranked candidates with their three prongs unresolved
- in: n.issue_register — issues, dispositions, and the modification log

## guarantee
[BINDING] origin: specified
- **drafts only slots whose register disposition is `drafted`.** A slot marked `record_supplied` or
  `expert_required` is refused at the entry point, not skipped inside — an inferred boundary is not
  a boundary
- the `grounding_kind` a claim declares is the one the **slot** requires; a mismatch is refused
- out: one claim per (slot_id, invocation); every claim carries `grounding_kind`, and either
  `{source_id, verbatim_span}` or `{canonical_path, asserted_value}[]`, never both and never neither
- **one claim per constrained selection.** A claim asserting more than one selection is not
  emitted; verification cost grows superlinearly in claims per sentence and a multi-claim
  paragraph is how a partially-false statement passes
- a slot with insufficient evidence emits a refusal carrying what was missing, never a sentence
- every invocation writes an interaction record **whatever the disposition** — a rejected claim is
  the only evidence a drafter is drifting, and discarding it destroys the signal
- no claim proposes, sets, or implies any of the five determinations at 7 CFR 1b.11(a)(46)
- one drafter per justification type; a general drafter is not emitted

## oracle
type: relational
risk: semantic,reproducibility
MRs below. There is no oracle for whether a justification sentence is good; the bindings, the
declaration, the single-claim property and the refusal behaviour are the checkable part, and they
are what the intent predicate rests on.

## metamorphic relations
[BINDING] origin: specified
- MR-1 (permutation): reorder the evidence items supplied ⇒ identical binding set, compared as a
  set. Prose may differ; the bindings may not
- MR-2 (orphan isolation): remove the only evidence item supporting a selection ⇒ a refusal, never
  a claim. A drafter that still produces a sentence is inventing one
- MR-3 (translation): change the ontology value at a path the claim asserts, re-run ⇒ either
  `asserted_value` moves with it, or the claim fails verification. Never asserts the stale value
  and passes
- MR-4 (re-execution): two runs in separate processes at fixed sampling ⇒ identical
  `grounding_kind` and identical `canonical_path` set

## demons
- D1: emit nothing for every slot, on the reading that evidence is always insufficient. Refusal
  rate 100%, every guarantee holds, every claim that exists is grounded, and the product's reason
  for existing — a document close to signature-ready without a NEPA expert typing it — is gone,
  invisibly, because the predicate's grounding clause is satisfied by having no claims.
  kill_test: `tests/drafter/test_every_drafted_slot_is_filled`
  negative_check: pending — install a constant refusal and confirm the coverage assert goes red
  status: live
- D4: draft a slot the register marks `expert_required`, on the reading that a draft is better than
  a blank. The manifest fills, the expert queue empties, and the disposition mix silently moves
  without anyone re-pinning it.
  kill_test: `tests/drafter/test_refuses_non_drafted_dispositions`
  negative_check: pending — remove the entry-point check and confirm the mix pin goes red
  status: live
- D2: declare every claim source-grounded and quote a source sentence adjacent to the point.
  Every substring check passes, every claim renders, and no sentence says anything about this
  project — because the sources predate it.
  kill_test: `tests/drafter/test_descriptive_slots_are_state_grounded`
  negative_check: pending — install a quote-only drafter and confirm the slot-kind assert goes red
  status: live
- D3: emit a plausible acreage in `asserted_value` without resolving the path. Binding-resolution
  rate stays high because the paths are well-formed; only the value is invented.
  kill_test: `tests/drafter/test_value_match_reported_separately_from_resolution`
  negative_check: pending — install a value perturbation and confirm value-match falls while
  resolution does not
  status: live

## clauses
- [BINDING] origin: specified — every regulatory slot requiring a justification has a required grounding kind declared **in the slot**, not chosen per invocation; a descriptive sentence about this project cannot be source-grounded because the sources predate the project (kill_test: `tests/drafter/test_descriptive_slots_are_state_grounded`)
- [BINDING] origin: specified — the disposition boundary is enforced at this node's entry point, so a drafted claim can never occupy a record-supplied or expert-required slot (kill_test: `tests/drafter/test_refuses_non_drafted_dispositions`)
- [BINDING] origin: specified — the highest-value output of the search drafter is sometimes "you do not need to build this"; a prior-coverage search that never returns that answer is not searching (kill_test: `tests/drafter/test_prior_coverage_can_return_no_new_analysis`)

## open gaps
- G019 — Palantir MCP exposes no AIP Logic tool, so the drafter's host surface is either AIP Logic
  configured by hand or a function calling a model through the platform's model access.
  Assumed: a function, because it is the reversible option and the one an agent can build.
  Reversible: yes — the emission contract is the same either way. Blocks: the walking skeleton's
  drafting step.
- G020 — signals from human edits and rejections adjust how content is written and never what
  counts as sufficient. Assumed: no signal path reaches a verifier, a value set, or an element
  requirement. Blocks: n.evals.
