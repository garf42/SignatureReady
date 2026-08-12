# node: n.precedent

## assume
[BINDING] origin: specified
- in: src.nepatec — NEPA document corpus with CEQ-standard metadata; row grain **measured** —
  one row per project, `{project, process, documents[]}`, each document `{metadata, pages[]}`,
  each page `{"page number", "page text"}`. The reader flattens project→document→page — G011

## guarantee
[BINDING] origin: specified
- out: one row per (document_id, page, chunk_ordinal); key unique
- every chunk carries `document_id`, `page`, `char_start`, `char_end` and an embedding; a chunk
  whose page anchor cannot be established is not emitted and is counted in a reported shortfall
- every chunk's text is a literal substring of its named page's text
- the corpus is filtered to USDA/USFS **on `process.lead_agency`, corpus-wide — never on the
  path partition**, which has no USFS bucket at all and whose USDA bucket is impure. The
  filter's selectivity — rows in, rows out — is emitted, not assumed, and **names the field it
  filtered on**, because path-selectivity and agency-selectivity are different numbers and were
  being quoted for one another — G012
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
  status: live — and **the source already instantiates it.** 7.9% of USDA `page number` values
  are ranges ("1-12", up to 18 pages), so the named page is a span and a substring check against
  it passes for text on any page in the span. This is D1 arriving from the corpus rather than
  from a chunker, and the kill test must reject span-valued anchors, not only nearest-page
  assignment. 3 USDA pages (0.1%; 8.8% corpus-wide) carry empty text and would pass vacuously.

## clauses
- [BINDING] origin: specified — the substring check is against the named page, not the document; page anchoring is what makes a citation checkable (kill_test: `tests/precedent/test_chunk_is_substring_of_its_named_page`) (clause: n.precedent/c1)
- [ADVISORY] origin: derived — this node ingests a filtered slice, never the whole corpus; the filter's selectivity is a reported number so a silently empty filter is visible (clause: n.precedent/c2)
## open gaps
- G011 — **ANSWERED 2026-08-12.** Grain is one row per *project*, not per document or per chunk;
  page-level text is native, so c1 is satisfiable. The reader changed, the guarantee did not.
- G012 — **ANSWERED 2026-08-12.** 11.9% of files are USDA. USFS *is* separable, from
  `process.lead_agency` (30 of 210 projects), never from the path — and the path bucket is impure,
  carrying 3 non-USDA-led projects. c2 must report which of the two filters it measured.
  Residual: **resolved by moving the filter to lead_agency.** Six Forest-Service-led EIS-process
  projects exist outside the USDA path bucket, carrying 16 FEIS + 4 DEIS + 1 ROD across 354
  documents / 16,922 pages. All five non-vacuity types are then coverable. ROD stands at n=2.
- G037 — `document_type` is blank on most documents and cannot carry non-vacuity alone.
