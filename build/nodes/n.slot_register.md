# node: n.slot_register

## assume
[BINDING] origin: specified
- in: n.element_sets — required elements per document type, stable opaque ids, spans_citations
- in: n.enumerations — constrained value sets, members, closure classification
- in: n.rule_corpus — verbatim text, for the citation and any qualification the rule itself names

## guarantee
[BINDING] origin: specified
- out: one row per slot; key `slot_id`, opaque and stable; a slot is the smallest unit that can be
  separately drafted, separately supplied from the record, or separately routed to one expert
- every slot carries `document_type`, the `element_id` it contributes to, its `citation`, a
  `selection_set_id` or null, and a `disposition ∈ {drafted, record_supplied, expert_required}`
- **the disposition is frozen here and is never chosen at invocation time.** A drafter may not
  decide a slot is too hard; an expert queue may not decide a slot is easy
- a `drafted` slot carries the `grounding_kind` its content requires — a descriptive sentence about
  this project cannot be source-grounded, because every source predates the project
- a `record_supplied` slot names the query over the proposal record or prior coverage that supplies it
- an `expert_required` slot names the `qualification`, the `artifact_type` accepted, and the
  `lead_time_days`; AI on that slot is restricted to coverage-gap checking against the artifact
- the union of slots per `document_type` covers every required element of that type; an element
  with no slot is reported by `element_id` and the count is zero or the node fails
- the disposition mix per `document_type` is emitted as counts and is **pinned**; the node fails
  when the mix changes at all, so a re-pin is a visible act in the same commit

## oracle
type: derivable
risk: semantic
fixture: `fixtures/slot_register/expected_slots.json` — the full slot map for all five document
types with dispositions, authored from the rule text before the register exists

## metamorphic relations
[BINDING] origin: specified
- MR-1 (orphan isolation): add a required element ⇒ exactly one uncovered-element report appears
  and no existing slot's id or disposition changes
- MR-2 (permutation): reorder the input elements ⇒ identical `slot_id` set and identical dispositions
- MR-3 (equivalent rewrite): change one slot's disposition in the register ⇒ the drafter's coverage
  obligation and the expert queue's assignment count move in opposite directions and their total is
  invariant. **The count cannot leak** — work moved between dispositions is visible as a mix change
- MR-4 (split-recombine): register FANEC and EA separately, union ⇒ equals registering both together

## demons
- D1: mark every hard slot `expert_required`. Slot disposition holds — no `drafted` slot is empty,
  because there are almost none — the manifest is complete, and the app is a routing form. The
  county officer who is not a NEPA expert receives a list of people to call.
  kill_test: `tests/slot_register/test_disposition_mix_is_pinned`
  negative_check: pending — reclassify three drafted slots as expert_required and confirm the pin
  goes red before anything else does
  status: live
- D2: emit one slot per required element. Coverage holds, every element has a slot, and EIS element
  5 with its seven impacts sub-elements becomes a single slot nobody can route to seven disciplines.
  kill_test: `tests/slot_register/test_slot_granularity_below_element`
  negative_check: pending — collapse to one slot per element and confirm the sub-element assert
  goes red on 1b.7(h)(5)
  status: live

## clauses
- [BINDING] origin: specified — disposition is a property of the slot, frozen in the register, never a runtime choice by the node that consumes it (kill_test: `tests/slot_register/test_disposition_is_not_invocation_scoped`)
- [BINDING] origin: specified — the disposition mix per document type is pinned; a change fails until re-pinned in the same commit with the diff recorded (kill_test: `tests/slot_register/test_disposition_mix_is_pinned`)
- [ADVISORY] origin: derived — `expert_required` is a routing instruction, not an exemption. Every one names who, which artifact, and how long, or it is a shrug with a schema

## open gaps
- G023 — no rule enumerates which slots require a qualified professional. 1b.9(g) requires
  interdisciplinary preparation at the responsible official's sole discretion and names no list.
  Assumed: the qualification set is derived from practice, tagged `origin: derived`, and reviewed
  at every phase boundary rather than frozen. Reversible: yes.
  Blocks: the pinned disposition mix.
