# node: n.ce_catalog

## assume
[BINDING] origin: specified
- in: n.rule_corpus — one row per (authority, citation) with verbatim text
- in: src.ce_explorer — one row per federal categorical exclusion; non-authoritative

## guarantee
[BINDING] origin: specified
- out: one row per category at 1b.4(c) and 1b.4(d); key `category_code`, unique; the full lists,
  uncurated
- every row carries `documentation_required` (c-list false, d-list true) and
  `constraints[]`, each constraint a typed record of `{measure, value, unit, strictness, source_span}`
- `strictness ∈ {lte, lt}` is parsed from the verbatim phrasing and stored; it is never inferred
  from the value, the measure, or a sibling constraint
- a constraint whose clock start the rule does not define is emitted with `clock_start = undefined`
  and a flag, never with an assumed start
- a category the rule flags in its own text carries `status_flag` with the flag's verbatim span
- a conditional exemption is a predicate row, not a note: 47d's NFS road repair and maintenance
  exemption is a `constraint_exemption` with its own `source_span`
- divergences against src.ce_explorer are emitted as a reconciliation table; neither source is
  silently preferred, and the rule text is the only citation target

## oracle
type: derivable
risk: semantic
fixture: `fixtures/ce_catalog/nine_capped_categories.json` — 47d, 35d, 36d, 37d, 34d, 45d, 46d,
32d, 28d with every cap, unit and strictness transcribed independently

## metamorphic relations
[BINDING] origin: specified
- MR-1 (equivalent rewrite): replace `≤` phrasing with `<` in a source span ⇒ stored `strictness`
  changes and the boundary verdict computed downstream flips. Same value, different verdict
- MR-2 (permutation): reorder categories in the source ⇒ identical constraint set per category
- MR-3 (scaling): express a cap in a different unit in the source span ⇒ `unit` changes and
  `value` changes; no downstream comparison is performed across mismatched units

## demons
- D1: store caps as prose strings. Every guarantee about presence holds, every category is
  catalogued, and every comparison downstream becomes a parse at call time — which succeeds until
  a cap reads "2,800" with a comma or "0.5 mi" with a space.
  kill_test: `tests/ce_catalog/test_constraints_are_typed_numerics_with_units`
  negative_check: pending — install by storing the raw cap phrase
  status: live
- D2: normalise every strictness to `lte`. All nine capped categories look right, every boundary
  fixture below and above passes, and exactly one case is wrong per category — the boundary,
  which is the case a challenger tests.
  kill_test: `tests/ce_catalog/test_strictness_round_trips_from_span`
  negative_check: pending — install a constant `lte` and confirm the 28d `< 20 ac` case goes red
  status: live

## clauses
- [BINDING] origin: specified — comparison strictness is parsed and stored, never inferred (kill_test: `tests/ce_catalog/test_strictness_round_trips_from_span`) (clause: n.ce_catalog/c1)
- [ADVISORY] origin: derived — 30d carries a status flag in the rule text itself; model it as present-with-a-flag. Silently including or excluding it are both defects (kill_test: `tests/ce_catalog/test_flagged_category_is_present_and_flagged`) (clause: n.ce_catalog/c2)
## open gaps
- G015 — the full 1b.4(c) list does not appear in the transcription. Assumed: n.rule_corpus
  supplies it. Until then the catalogue is emitted `provisional` and the interface says so —
  an absent option and a blocked option are different states.
  Blocks: MR-1 on n.det_core for c-list categories.
- G008 — src.ce_explorer unit declaration unverified.
