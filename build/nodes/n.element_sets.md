# node: n.element_sets

## assume
[BINDING] origin: specified
- in: n.rule_corpus — one row per (authority, citation); many-to-many to elements: one paragraph
  may carry several required elements and one element may span several paragraphs

## guarantee
[BINDING] origin: specified
- out: one row per required element; key `element_id`, a stable opaque identifier that is
  **not** an ordinal and **not** an array index
- every row carries `document_type`, `citation`, `ordinal`, `verbatim_span`, and
  `spans_citations[]` — the full set of paragraphs the element rests on
- `verbatim_span` is a literal substring of the concatenation of `spans_citations[]` texts, by a
  deterministic check; a row failing that check is not emitted and is reported by id
- `|required(t)|` equals the frozen count for each in-scope t; a shortfall names which ordinal is
  missing rather than reporting a total
- reordering, inserting or removing an element never changes any other element's `element_id`

## oracle
type: derivable
risk: semantic
fixture: `fixtures/element_sets/frozen_counts.json` — FANEC 6, EA 7, FONSI 5, EIS 8, ROD 8, each
with its citation, transcribed independently of the extractor

## metamorphic relations
[BINDING] origin: specified
- MR-1 (permutation): reorder input paragraphs ⇒ identical element set including every
  `element_id` and every `ordinal`
- MR-2 (orphan isolation): remove one paragraph an element cites ⇒ that element alone is absent
  and reported by id; every other element is byte-identical
- MR-3 (idempotence): supply a duplicate paragraph row ⇒ element set unchanged, no element
  duplicated, no `ordinal` shifted

## demons
- D1: derive `element_id` from `(document_type, ordinal)`. Every guarantee reads satisfied today.
  The first time an element is inserted, every downstream canonical path silently re-points to a
  different element, and every state-grounded claim resting on one is now about something else.
  kill_test: `tests/element_sets/test_id_survives_insertion`
  negative_check: pending — install by setting `element_id = f"{doc}-{ordinal}"` and confirm the
  test goes red when a new element is inserted at ordinal 3
  status: live
- D2: emit one element per paragraph. Counts come out plausible, the substring check passes on
  every row, and element (ii)'s adopted-category conditional is silently merged into its parent.
  kill_test: `tests/element_sets/test_multi_paragraph_element_is_one_row`
  negative_check: pending — install a one-row-per-paragraph mapper
  status: live

## clauses
- [BINDING] origin: specified — an element's identity is opaque and stable; ordinal is a display property, never an address (kill_test: `tests/element_sets/test_id_survives_insertion`) (clause: n.element_sets/c1)
- [ADVISORY] origin: derived — the register's seven-requirement reading of the FANEC's six elements is a requirements artifact; the rule has six elements and this node emits six (kill_test: `tests/element_sets/test_frozen_counts`) (clause: n.element_sets/c2)
## open gaps
- G013 — frozen element counts are transcription-derived and unverified against eCFR.
  Assumed correct. Closed by MR-1 on n.rule_corpus round-tripping the five citations.
