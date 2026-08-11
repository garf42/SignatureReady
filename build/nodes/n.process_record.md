# node: n.process_record

## assume
[BINDING] origin: specified
- in: n.issue_register — issues with dispositions and their cause-effect pairs
- in: n.enumerations — notice contents and subtypes, scoping responsibilities, comment-response
  actions, named no-action rationales, reevaluation paths, errata fields, emergency tiers
- in: n.ontology — canonical paths, deadline triggers, authority versions, proposal-record items

## guarantee
[BINDING] origin: specified
- out: `notice`, `comment`, `comment_group`, `comment_response`, `certifying_statement`,
  `errata_sheet`, `reevaluation_determination`; keys unique
- a notice of intent carries all ten required contents, and its **preliminary list of substantive
  issues with expected impacts resolves to issue-register rows**, never to free text. That register
  must therefore exist at notice publication, long before the document it announces
- notice subtypes are distinct: announcing preparation, pausing, resuming, withdrawing — and in
  limited situations announcing an environmental assessment. A notice with no subtype is not emitted
- comment responses document **the action the responsible official took**, not a reply. Multiple
  comments on the same substantive issue may be grouped and paraphrased as one; where action was
  taken, the response cites where in the document or the proposal record it is accounted for
- "no action needed" carries one of the four named rationales and never free text
- **certifying statements are fully generated — fixed text plus computed values, and no model is
  reachable from that path.** The responsible official is certifying, and a fluent paraphrase of a
  certification is a false statement in the one place that cannot carry one
- the errata sheet's eight fields are derived from state; a field with no state behind it is not
  emitted, and the sheet is not assembled partially
- deadlines compute from the earliest of the three triggers. **Readiness-to-start is an explicit
  dated human decision, never inferred** — it is the largest scheduling lever in the domain
- the publication mode used where the rule compels publication on the day a deadline elapses records
  every element unsatisfied at that moment as a durable list. That list is what the certification
  attests to and the input to supplementation. Without it the mode is an override; with it, a record

## oracle
type: derivable
risk: semantic
fixture: `fixtures/process_record/noi_and_errata.json` — one notice with all ten contents resolved
to issue rows, one errata sheet with all eight fields, one comment set grouped three ways

## metamorphic relations
[BINDING] origin: specified
- MR-1 (translation): shift a deadline trigger by one year ⇒ the deadline shifts identically; no
  hardcoded period and no fiscal-boundary behaviour
- MR-2 (orphan isolation): add a comment raising a new substantive issue ⇒ one new group appears and
  no existing group's action changes
- MR-3 (idempotence): file the same comment twice ⇒ one comment row after dedupe and unchanged
  group membership
- MR-4 (re-execution): generate the same certifying statement twice in separate processes ⇒
  byte-identical text

## demons
- D1: generate a certifying statement with a model. It reads perfectly, it is a sworn statement by
  the responsible official, and one clause is subtly not what the rule says — which is exactly the
  failure no reader is positioned to catch.
  kill_test: `tests/process_record/test_no_model_reachable_from_certifying_path`
  negative_check: pending — route the statement through the drafter and confirm the reachability
  assert goes red
  status: live
- D2: emit the notice's substantive-issue list as free text. All ten contents are present, the
  notice publishes, and the register the eventual document must be consistent with never existed —
  so consistency can never be checked, in either direction.
  kill_test: `tests/process_record/test_noi_issues_resolve_to_register_rows`
  negative_check: pending — install a text field and confirm the resolution assert goes red
  status: live

## clauses
- [BINDING] origin: specified — no model is reachable from the certifying-statement or errata path; both are fixed text plus computed values (kill_test: `tests/process_record/test_no_model_reachable_from_certifying_path`)
- [BINDING] origin: specified — readiness-to-start is a dated human decision surfaced explicitly, never derived from the state of the work (kill_test: `tests/process_record/test_readiness_is_a_recorded_act`)
- [ADVISORY] origin: derived — never state an expected duration; observed durations for the same branch span eight months to nearly three years. Elapsed and remaining against statutory deadlines only

## open gaps
- G026 — the pre-decisional objection process does not apply to categorical exclusions but does
  apply on the EA and EIS branches, and its text has been under revision.
  Assumed: not built against until re-verified from primary source; the reviewing-officer
  derivation runs against an injected organisational structure explicitly flagged synthetic.
  Reversible: yes. Blocks: the objection affordances on the EA and EIS branches.
