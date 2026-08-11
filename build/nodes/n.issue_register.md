# node: n.issue_register

## assume
[BINDING] origin: specified
- in: n.ontology — proposed action, design criteria, alternatives, canonical paths, change events
- in: n.enumerations — issue dispositions, comment-response actions, named no-action rationales,
  reasonable-alternative prongs, design-criterion types and origins, mitigation types

## guarantee
[BINDING] origin: specified
- out: `issue` one row per issue; `proposed_action_modification` one row per change;
  `issue_disposition` one row per (issue, disposition); keys unique
- an issue is a **cause-effect relation**: a named cause in the proposed action and a named effect
  on a resource in the affected environment. An issue with either side unnamed is not emitted and
  is reported — "concerns about noise" is not an issue, it is a topic
- **three dispositions, never a boolean**: modify the proposed action, develop an action
  alternative, or supplement, improve or modify the analysis. An issue may carry more than one
- **the derived transition**: a design criterion created in response to an issue causes that issue
  to leave detailed analysis, recorded as an event naming both ids. This is what keeps an EA inside
  its page limit, and it is a rule in the definition, not a convention
- the modification log carries, per change to the proposed action, the change, the issue it
  resolved, and its origin. **Without this log the required narrative for why no additional
  alternatives were developed is unproducible by anyone**, model or human
- alternative elimination carries the three prongs — technically and economically feasible, meets
  the purpose and need, meets applicant goals where applicable — separately, never as a summary
- design criterion and mitigation stay distinct objects: one is part of the proposed action, the
  other is documented in a finding or decision document and requires a stated statutory or
  regulatory authority plus a monitoring and enforcement program where enforceable

## oracle
type: derivable
risk: semantic
fixture: `fixtures/issue_register/three_issues.json` — one resolved by a design criterion, one by
an action alternative, one carried into detailed analysis, with the expected transition events

## metamorphic relations
[BINDING] origin: specified
- MR-1 (translation): add a design criterion in response to issue X ⇒ X leaves detailed analysis,
  appears in the no-additional-alternatives narrative, and no other issue moves
- MR-2 (orphan isolation): add an issue with no named effect ⇒ rejected and reported; no existing
  issue changes
- MR-3 (idempotence): record the same modification twice ⇒ one log entry and one transition
- MR-4 (permutation): reorder issues ⇒ identical dispositions and identical transition events

## demons
- D1: model disposition as a boolean, analyzed or not analyzed. Every issue has a state, the
  narrative generates fluently, and the rationale for why no additional alternatives were developed
  cites nothing — which is the sentence a challenger reads first.
  kill_test: `tests/issue_register/test_three_dispositions_not_two`
  negative_check: pending — collapse to a boolean and confirm the narrative-evidence assert goes red
  status: live
- D2: permit a design criterion with no `inResponseTo` link. The transition never fires, every issue
  stays in detailed analysis, the EA grows past 75 pages, and no test notices because every row is
  well-formed.
  kill_test: `tests/issue_register/test_design_criterion_requires_its_issue`
  negative_check: pending — drop the link requirement and confirm MR-1 goes red
  status: live

## clauses
- [BINDING] origin: specified — an issue is a cause-effect relation with both sides named to a canonical path (kill_test: `tests/issue_register/test_both_sides_named`) (clause: n.issue_register/c1)
- [BINDING] origin: specified — design criterion and mitigation are different objects with different creators, timing, host documents and citation duties; conflating them puts a design criterion in a finding without authority, or a mitigation in the proposed action where it escapes the monitoring requirement (kill_test: `tests/issue_register/test_criterion_and_mitigation_are_distinct_types`) (clause: n.issue_register/c2)
- [ADVISORY] origin: derived — the modification log looks like bookkeeping and is the sole input to a required narrative; it is written as the modification happens or it is not written (clause: n.issue_register/c3)
## open gaps
- G025 — whether one issue may carry two dispositions simultaneously. Assumed: yes, many-to-many,
  because supplementing the analysis and modifying the action are not exclusive. Reversible: yes.
  Blocks: MR-4.
