# node: n.authority_ledger

## assume
[BINDING] origin: specified
- in: n.rule_corpus — one row per (authority, citation) with effective date and retrieval timestamp
- in: src.federalregister — one row per FR document, unique FR document number

## guarantee
[BINDING] origin: specified
- out: one row per (authority_id, version); key `(authority_id, effective_date)`, unique
- every paragraph in n.rule_corpus resolves to exactly one authority version; the count of
  unresolved paragraphs is emitted and is zero or the node fails
- every version carries the three disclosure flags of 1b.9(e)(8)(vi) — not final within the
  preparing agency, subject of an adequacy referral, subject of a non-final judicial action —
  each as an explicit tri-state `true | false | unknown`, never a defaulted boolean
- a flag reading `unknown` is emitted as `unknown` downstream and never rendered as `false`

## oracle
type: derivable
risk: semantic
fixture: `fixtures/authority_ledger/91fr17092_amended_by_91fr40353.json` — the known amendment
lineage of Part 1b, hand-constructed

## metamorphic relations
[BINDING] origin: specified
- MR-1 (translation): shift every effective date by one year ⇒ version ordering and lineage
  edges are identical; no hardcoded date boundary changes the result
- MR-2 (orphan isolation): add an FR document referencing an authority not in the corpus ⇒ only
  the unmatched bucket grows; no existing version's flags change

## demons
- D1: default every disclosure flag to `false` when no FR document says otherwise. All three
  flags are then present and typed, the guarantee reads satisfied, and a document relying on a
  vacated analysis prints "not subject to a non-final judicial action" as a positive statement.
  kill_test: `tests/authority_ledger/test_absent_evidence_yields_unknown_not_false`
  negative_check: pending — install by replacing the tri-state with `bool(match)`
  status: live

## clauses
- [BINDING] origin: specified — absence of evidence is `unknown`; only an affirmative source sets a flag `false` (kill_test: `tests/authority_ledger/test_absent_evidence_yields_unknown_not_false`) (clause: n.authority_ledger/c1)
## open gaps
- G002 — re-check cadence for authority currency. Assumed: on every build of this node, with the
  retrieval timestamp carried forward. No interval is invented.
- G006 — federalregister.gov rate limit and page size at this volume.
