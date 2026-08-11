# node: n.enumerations

## assume
[BINDING] origin: specified
- in: n.rule_corpus — one row per (authority, citation) with verbatim text

## guarantee
[BINDING] origin: specified
- out: one row per enumerated set; key `set_id`, unique; 34 sets for Part 1b
- every row carries `citation`, `members[]`, `member_count`, `introducing_clause_verbatim`, and
  `closure ∈ {open, closed}`
- `closure` is derived **only** from `introducing_clause_verbatim`; a set whose introducing clause
  was not located carries `closure = undetermined` and is emitted as such, never defaulted
- an `open` set carries an `extension_mechanism` naming what a recorded addition must supply:
  the added member, its interdisciplinary or professional basis, and a date
- `member_count` per (citation) matches the independently transcribed count, by multiplicity

## oracle
type: derivable
risk: semantic
fixture: `fixtures/enumerations/thirty_four_sets.json` — the 34 (citation, member count) pairs
transcribed independently of the extractor

## metamorphic relations
[BINDING] origin: specified
- MR-1 (orphan isolation): append an unrelated paragraph ⇒ set count stays 34; no member moves
- MR-2 (equivalent rewrite): an introducing clause containing "may include, but are not limited
  to" ⇒ `closure = open`; the same clause with that phrase removed ⇒ `closed`. The classification
  is a function of the clause text and of nothing else
- MR-3 (permutation): reorder members in the source ⇒ identical member set, and member order is
  preserved as `ordinal` without affecting `set_id` or membership

## demons
- D1: default `closure` to `closed` when no introducing clause is found. 34 sets appear, every
  count matches, and the extraordinary-circumstance resource list at 1b.3(f)(1) becomes a fixed
  enum of eight — which the rule expressly forbids, and which no count can detect.
  kill_test: `tests/enumerations/test_missing_clause_yields_undetermined`
  negative_check: pending — install `closure = "closed" if not clause else classify(clause)`
  status: live

## clauses
- [BINDING] origin: specified — closure is a function of the introducing clause alone; no set is classified from its members (kill_test: `tests/enumerations/test_missing_clause_yields_undetermined`) (clause: n.enumerations/c1)
## open gaps
- G014 — the introducing clause for three sets is reported absent from the transcription
  (1b.7(f)(2)(vi), 1b.9(c), 1b.7(f)(2)). Assumed `undetermined` until n.rule_corpus supplies them.
  Reversible: yes — reclassification touches one column.
