# node: n.project_state

## assume
[BINDING] origin: specified
- in: src.fsgeodata — one geographic feature per row per layer, projection and linear unit per layer
- in: src.synthetic — one row per generated project, unit, activity group, screen; `synthetic = true`

## guarantee
[BINDING] origin: specified
- out: `treatment_unit` one row per unit; `activity_group` one row per group;
  `treatment_unit_activity` one row per (unit, activity) pair — a **many-to-many** relation whose
  pair key is unique and whose cardinality is asserted, not assumed
- for every (project, category), **both** readings of the covered portion are emitted with their
  divergence: `geometric_union_acres` and `treatment_sum_acres`, each with its unit
- neither reading is marked preferred; the elected basis is a separate recorded human input and
  is never defaulted by this node
- every linear and areal measure carries its unit and the projection it was computed in; no
  measure crosses a projection boundary without a recorded transformation
- the prohibition inputs a category's conditions require — even-aged regeneration, vegetation type
  conversion — are aggregated onto the proposed action by `anyOf` over its activity groups, and are
  properties, never constants supplied at a call site

## oracle
type: derivable
risk: semantic
fixture: `fixtures/project_state/overlapping_units.json` — four units, two activity groups, one
unit carrying two overlapping treatments so the two readings provably diverge

## metamorphic relations
[BINDING] origin: specified
- MR-1 (idempotence): duplicate a (unit, activity) row ⇒ `geometric_union_acres` unchanged and
  `treatment_sum_acres` unchanged after pair-key dedupe. A change in either is a fanout defect
- MR-2 (orphan isolation): add an activity whose unit id is absent ⇒ only the unmatched bucket
  moves; no unit's acreage changes
- MR-3 (split-recombine): split the unit set in half, compute each, union ⇒ equals the whole-set
  result for `treatment_sum_acres`, and **must not** for `geometric_union_acres` where the halves
  overlap. The asymmetry is the test — a pipeline where both agree has collapsed the relation
- MR-4 (scaling): multiply every treatment acreage by k ⇒ `treatment_sum_acres` scales by k;
  `geometric_union_acres` does not, unless geometry scaled too

## demons
- D1: emit a one-to-one treatment-to-unit relation. Every acreage is a plausible number, every
  cap test runs, the fixture data happens not to overlap, and summed treatment acreage is reported
  as project acreage — which invalidates every categorical exclusion computed from it.
  kill_test: `tests/project_state/test_two_readings_diverge_on_overlap`
  negative_check: pending — install a one-to-one join and confirm the divergence collapses to zero
  status: live
- D2: emit only the reading that produces the smaller number. Both fields are populated, the
  divergence is reported, and the category always fits.
  kill_test: `tests/project_state/test_neither_reading_is_marked_preferred`
  negative_check: pending — install a `preferred` field set to the minimum
  status: live

## clauses
- [BINDING] origin: specified — the covered portion has two readings and no default; election is a recorded human input (kill_test: `tests/project_state/test_neither_reading_is_marked_preferred`) (clause: n.project_state/c1)
- [BINDING] origin: derived — every prohibition input is an ontology property; a named constant standing in for an absent property is a defect that produces a correct answer today (kill_test: `tests/project_state/test_no_constant_stands_in_for_a_property`) (clause: n.project_state/c2)
## open gaps
- G009 — fsgeodata feature id uniqueness unverified. Assumed unique per layer.
- G010 — projection and linear unit per layer must be read, not assumed. Assumed: read at
  ingestion and recorded per layer. Blocks: MR-4.
