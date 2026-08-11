# node: n.expert_queue

## assume
[BINDING] origin: specified
- in: n.slot_register — slots with disposition, qualification, artifact_type, lead_time_days
- in: n.ontology — positions, disciplines, cooperating-agency designations, privilege markings,
  canonical paths
- in: n.expert_directory — attested qualification holders, provenance-bearing channels, request packages

## guarantee
[BINDING] origin: specified
- out: one row per (slot_id, assignment); key unique. **Every `expert_required` slot has exactly one
  open assignment or one received artifact** — never zero, never both
- every assignment names the **qualification** required, the artifact type accepted, the lead time,
  and the earliest date that slot can close given that lead time
- **routing is to a position or a discipline, never to a named individual.** A record saying a
  person is responsible outlives that person's employment and misstates who holds the duty
- AI on an `expert_required` slot is restricted to **coverage-gap checking against the received
  artifact**: it names what the element requires that the artifact does not address, and drafts
  nothing. A gap report is not a draft and is never promoted to one
- an item within the withholding provisions — threatened or endangered species locations, cultural
  or heritage sites, third-party proprietary information, personally identifiable information —
  carries a privilege marking, and unredacted privileged material is never incorporated by reference
- cooperating-agency assignments carry roles, issue assignment, schedule and staff commitments; for
  a non-Federal agency a confidentiality commitment is required and a waiver of the right to
  judicial review may not be
- where more than one responsible official must sign, the signature blocks live in the one document
  and each states **what that official is approving**, given the actions proposed and that
  official's statutory authority
- an assignment may name a selected holder or none; **routing to a qualification with no holder
  selected is a valid state**, not an incomplete one, and the interface says which
- where a holder is selected, the assignment carries the generated request package, and the
  preparer disclosure statement is a precondition of accepting the returned artifact
- on artifact receipt the coverage-gap result and the elapsed-against-quoted lead time are written
  back as an attested engagement outcome — **the only ranking evidence the directory is permitted**
- per document type the node emits the **critical path**: the longest outstanding lead time among
  open assignments, and the earliest date the document could become signature-ready

## oracle
type: derivable
risk: semantic
fixture: `fixtures/expert_queue/assignments.json` — four expert slots across three qualifications
with differing lead times, one artifact received, one privilege-marked

## metamorphic relations
[BINDING] origin: specified
- MR-1 (translation): shift an assignment's start date ⇒ its earliest-close date shifts identically
  and the critical path recomputes with it
- MR-2 (orphan isolation): receive one artifact ⇒ exactly that assignment closes; no other
  assignment, lead time, or privilege marking changes
- MR-3 (scaling): double every lead time ⇒ the critical path doubles and every per-slot
  earliest-close doubles
- MR-4 (idempotence): upload the same artifact twice ⇒ one received artifact and one closure

## demons
- D1: let the drafter fill an `expert_required` slot and mark the artifact pending. The document
  assembles, the slot is full, the manifest reads complete, and a cultural resources section was
  written by a model that has never seen the site.
  kill_test: `tests/expert_queue/test_expert_slot_accepts_only_an_artifact`
  negative_check: pending — route a drafted claim into an expert slot and confirm the assert goes red
  status: live
- D2: promote the coverage-gap report into the slot when no artifact arrives before the deadline.
  Every slot is filled, nothing is empty, and the content is a list of what is missing presented as
  what is present.
  kill_test: `tests/expert_queue/test_gap_report_is_not_slot_content`
  negative_check: pending — install the promotion and confirm the content-type assert goes red
  status: live
- D3: route to a named individual because the position lookup is empty. Everything works, the
  workflow completes, and the record misstates who holds the duty.
  kill_test: `tests/expert_queue/test_routing_target_is_a_position`
  negative_check: pending — install a person id and confirm the target-type assert goes red
  status: live

## clauses
- [BINDING] origin: specified — an expert-required slot accepts only an uploaded artifact; AI is restricted to coverage-gap checking and its output is never slot content (kill_test: `tests/expert_queue/test_expert_slot_accepts_only_an_artifact`)
- [BINDING] origin: specified — routing targets a position or discipline, never a person (kill_test: `tests/expert_queue/test_routing_target_is_a_position`)
- [ADVISORY] origin: derived — this node is what makes the product honest for the environmental assessment and impact statement branches: the tail of work a model cannot do is not hidden, it is named, routed, and dated

## open gaps
- G027 — whether the critical path violates the rule against stating expected durations.
  Assumed: permitted, because it is a sum of lead times each supplied by the expert who will do the
  work, not an estimate of how long review takes. The distinction is load-bearing and thin.
  Reversible: yes — the field is display-only. Blocks: MR-3.
