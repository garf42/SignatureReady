# node: n.precedent

## assume
[BINDING] origin: specified
- in: src.nepatec — NEPA document corpus with CEQ-standard metadata; row grain unverified

## guarantee
[BINDING] origin: specified
- out: one row per (document_id, page, chunk_ordinal); key unique
- every chunk carries `document_id`, `page`, `char_start`, `char_end` and an embedding; a chunk
  whose page anchor cannot be established is not emitted and is counted in a reported shortfall
- every chunk's text is a literal substring of its named page's text
- the corpus is filtered to USDA/USFS and the filter's selectivity — rows in, rows out — is
  emitted, not assumed
- retrieval returns chunks with their page anchors intact; a result with no resolvable page is
  never returned

## oracle
type: relational
risk: semantic,reproducibility
MRs below. No ground truth for retrieval relevance; the anchoring and substring properties are
the checkable part and the only part downstream depends on.

## metamorphic relations
[BINDING] origin: specified
- MR-1 (permutation): reorder input documents ⇒ identical chunk set and identical page anchors
- MR-2 (split-recombine): index half the corpus, then the other half, union ⇒ equals the
  whole-corpus index by chunk key
- MR-3 (re-execution): embed the same chunk twice in separate processes ⇒ identical vector.
  A drifting embedding silently reorders retrieval and no output looks wrong

## demons
- D1: chunk on a fixed character window with no page anchor, then assign the nearest page. Every
  chunk has a page, every substring check passes against the concatenated document, and every
  citation the drafter emits points at a page that does not contain the quoted text.
  kill_test: `tests/precedent/test_chunk_is_substring_of_its_named_page`
  negative_check: pending — install nearest-page assignment and confirm the test goes red on a
  chunk straddling a page break
  status: live

## clauses
- [BINDING] origin: specified — the substring check is against the named page, not the document; page anchoring is what makes a citation checkable (kill_test: `tests/precedent/test_chunk_is_substring_of_its_named_page`) (clause: n.precedent/c1)
- [ADVISORY] origin: derived — this node ingests a filtered slice, never the whole corpus; the filter's selectivity is a reported number so a silently empty filter is visible (clause: n.precedent/c2)
## open gaps
- G011 — src.nepatec row grain unverified. Assumed one row per document with a page-level text
  field. Reversible: yes — a per-chunk source changes the reader, not the guarantee.
- G012 — USDA/USFS filter selectivity unmeasured. Assumed non-trivial.
  Blocks: the acceptance corpus's precedent coverage.
