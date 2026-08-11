# node: n.rule_corpus

## assume
[BINDING] origin: specified
- in: src.ecfr_1b — one row per numbered paragraph, citation key, verbatim text, effective date
- in: src.uscode — one row per statutory subsection, citation key, text-in-effect date

## guarantee
[BINDING] origin: specified
- out: one row per (authority, paragraph citation); key `(authority_id, citation)`, unique
- every row carries `verbatim_text`, `effective_date`, `retrieved_timestamp`, `source_url`
- `verbatim_text` is the retrieved bytes with no normalisation applied; any normalisation is a
  separate derived column naming the rule that produced it
- no row originates from any source other than ecfr.gov or the named U.S. Code endpoint, asserted
  by `source_url` prefix on every row
- a paragraph that fails retrieval is emitted as a row with `retrieval_status = failed` and null
  text, never omitted — the corpus states its own holes

## oracle
type: derivable
risk: semantic,reproducibility
fixture: `fixtures/rule_corpus/hand_verified_paragraphs.json` — 12 paragraphs transcribed
independently from eCFR, covering 1b.3(g)(2), 1b.5(c), 1b.6(b), 1b.7(h), 1b.8(b), 1b.3(f)(1)

## metamorphic relations
[BINDING] origin: specified
- MR-1 (re-execution): two retrievals of the same effective version, in separate processes ⇒
  byte-identical `verbatim_text` for every citation
- MR-2 (permutation): parsing the source in a different paragraph order ⇒ identical citation key
  set and identical text per key
- MR-3 (orphan isolation): retrieving one additional section ⇒ only that section's rows appear;
  no existing row's text or citation changes

## demons
- D1: return the LII copy of Part 1b. Every guarantee holds — rows, keys, dates, timestamps —
  and the text is superseded. The build is then correct against lapsed law, silently.
  kill_test: `tests/rule_corpus/test_source_url_prefix_and_known_span`
  negative_check: pending — install by pointing the retriever at law.cornell.edu and confirm the
  test goes red on the § 1b.2 "Under Secretary of NRE" / "USDA Senior Agency Official" divergence
  status: live
- D2: emit zero rows on a retrieval failure. Every "for every row" guarantee holds vacuously and
  every downstream count is zero, which reads as "nothing required" rather than "nothing read".
  kill_test: `tests/rule_corpus/test_failed_retrieval_emits_a_row`
  negative_check: pending — install by returning an empty list on HTTP error
  status: live

## clauses
- [ADVISORY] origin: derived — Cornell/LII is excluded at the retriever, not at review time; a URL allowlist is cheaper than a reading (kill_test: `tests/rule_corpus/test_source_url_prefix_and_known_span`)
- [BINDING] origin: specified — normalisation never overwrites `verbatim_text`; the source-grounded verifier compares against the unnormalised column or its substring guarantee is about a string nobody stored (kill_test: `tests/rule_corpus/test_verbatim_column_is_untransformed`)

## open gaps
- G001 — paragraph citation uniqueness assumed, not verified. Assumed unique; a collision would
  silently merge two paragraphs.
- G004 — whether ecfr.gov exposes a structured API for Part 1b. Assumed: bulk download and parse.
