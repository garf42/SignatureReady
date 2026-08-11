# node: n.ontology

## assume
[BINDING] origin: specified
- in: n.element_sets — one row per required element with a stable opaque `element_id`
- in: n.enumerations — one row per enumerated set with members and a closure classification
- in: n.ce_catalog — one row per category with typed constraints carrying unit and strictness
- in: n.project_state — units, activity groups, a many-to-many relation, both covered-portion readings
- in: n.authority_ledger — one row per authority version with three tri-state disclosure flags
- in: src.pic_standard — one row per PIC v1.2 entity/property pair in the crosswalk

## guarantee
[BINDING] origin: specified
- out: Foundry object types, link types and action types, plus a `canonical_path_index` emitted as
  data: one row per addressable value, key `canonical_path`, unique
- **every value a claim may assert has exactly one canonical path, and no path resolves to two
  values**; both directions are asserted by a count that must be zero
- no canonical path contains an array index or a positional lookup; required elements, screens,
  constraints and claims are addressable entities with stable identity
- a value that exists only as a computed intermediate has no path; where a claim must assert a
  computed value, the computation's result is stored and addressed
- the two covered-portion readings have **distinct paths**; no path resolves to "the covered
  portion" without naming which reading
- every enumerated set from n.enumerations is a constrained value set; an `open` set carries the
  attested extension mechanism; a set with `closure = undetermined` is modelled open and flagged
- every PIC v1.2 entity maps to an object type or carries a recorded reason it does not; PIC
  provenance properties are carried onto every mapped type
- design criteria and mitigation are distinct types with distinct host documents and distinct
  citation duties; an issue carries three dispositions, never a boolean
- every object type carries an append-only change record: a correction is a new event, and
  `changed_at` is queryable per canonical path

## oracle
type: derivable
risk: semantic
fixture: `fixtures/ontology/path_index_expected.json` — the expected canonical path set for the
overlapping-units fixture, authored before the ontology exists

## metamorphic relations
[BINDING] origin: specified
- MR-1 (orphan isolation): insert a required element between two existing ones ⇒ **every
  previously issued canonical path still resolves to the same value.** This is the positional-array
  killer and it is the single most load-bearing relation in the build
- MR-2 (equivalent rewrite): rename a display label ⇒ no canonical path changes
- MR-3 (idempotence): re-run the ontology emission ⇒ byte-identical path index
- MR-4 (permutation): reorder the input element rows ⇒ identical path index

## demons
- D1: address a required element as `document.elements[i]` where `i` is the index at which a
  parallel id array matches. Every path resolves today, the uniqueness count reads zero, and the
  first insertion re-points every state-grounded claim in the corpus at a different element —
  with no error, because the path still resolves.
  kill_test: `tests/ontology/test_path_survives_element_insertion`
  negative_check: pending — install parallel arrays aligned by index and confirm MR-1 goes red
  status: live
- D2: emit one path per property name rather than per value. Uniqueness holds trivially — one
  path per name — and `treats N acres` resolves against whichever reading answers first.
  kill_test: `tests/ontology/test_two_readings_have_two_paths`
  negative_check: pending — install a name-keyed index and confirm both readings collide
  status: live
- D3: satisfy an element by writing the literal string `SATISFIED` into a map named `derivedState`.
  Element closure holds, the manifest reads satisfied, and nothing was derived from anything.
  kill_test: `tests/ontology/test_satisfaction_resolves_a_path`
  negative_check: pending — install a stored constant and confirm the resolution assert goes red
  status: live

## clauses
- [BINDING] origin: specified — resolution is against a named path, never a search for a matching value; a verifier that accepts any path whose value happens to match would pass a sentence true of one reading and false of the other (kill_test: `tests/ontology/test_two_readings_have_two_paths`)
- [BINDING] origin: specified — addressability is a property of shape and cannot be retrofitted; a path index emitted after the types exist is a description, not a constraint (kill_test: `tests/ontology/test_path_index_is_emitted_with_the_types`)
- [ADVISORY] origin: derived — the knowledge-capture types hold no regulatory content and satisfy no element set; they go in here because they are the one cluster that cannot be added later without touching everything above

## open gaps
- G007 — PIC crosswalk (entity, property) uniqueness unverified. Assumed unique.
- G016 — Palantir MCP creates and updates object, link and action types **on a branch** but
  cannot write ontology data. Assumed: types by MCP, data by
  `create_and_write_to_foundry_dataset` plus a pipeline. Reversible: yes.
  Blocks: the walking skeleton's ontology step.
