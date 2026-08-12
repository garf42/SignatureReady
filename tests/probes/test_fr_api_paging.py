"""Phase -1 prefab probe: federalregister.gov, the Part 1b amendment lineage.

prefab:     federalregister.gov
used_by:    n.authority_ledger
probe_dims: the amendment lineage of 7 CFR Part 1b plus the final-rule preamble
gaps:       G002 -- re-check cadence for authority currency
            G006 -- rate limit and page size at this build's volume
            G036 -- conditions[cfr][part] cannot name "1b"

WHAT THIS PROBE ESTABLISHES, by running code against the real API:

  1. G036 CONFIRMED, and it goes deeper than the gap says. `conditions[cfr][part]=1b` is
     HTTP 400 -- "CFR part must be an integer or a range". But the restriction is not just
     in the query parser: the USDA NEPA rule's OWN `cfr_references` records
     {"title": 7, "part": "1"}. The API cannot represent Part 1b anywhere, in queries or in
     document metadata, so a CFR-filtered lineage is not merely awkward, it is unavailable.

  2. A CITATION ERROR IN THE CONSTITUTION. It names "91 FR 17092 (2026-04-03)" as the
     authority version. The rule published that day is document 2026-06537, cited
     **91 FR 17062**, spanning pages 17062-17122. A Federal Register citation names the
     START page; 17092 is an interior page of that rule. Under tie-break rule 1 -- a
     citation the primary source does not support is wrong regardless of what it costs to
     fix -- the constitution is wrong and this probe is the primary source.
     The second citation, 91 FR 40353 (2026-07-02), is CORRECT: document 2026-13372.

  3. PAGING IS OFFSET-BASED, and the register's note that it is "cursor-based via
     search_after_cursor, not offset, so a paged retrieval is not resumable from a page
     number" is wrong. `?page=N` works. The truth is worse than either reading:

       THE PAGE PARAMETER IS SILENTLY IGNORED PAST ITS CEILING AND THE RESULT SET WRAPS.
       At 20 per page over 902 hits: page 46 returns the last 2, pages 47-50 return 0, and
       page 51 returns PAGE ONE'S ROWS. A loop that walks a fixed number of pages re-ingests
       the head of the corpus as though it were the tail, with no error and no empty page to
       stop on. n.authority_ledger keys on (authority_id, effective_date) and would silently
       double-count.

  4. per_page HAS AN UNDOCUMENTED CEILING AND DEGRADES SILENTLY. 1000 and 2000 are honoured;
     5000 returns 20 -- the default -- with HTTP 200. Asking for more than the ceiling does
     not error, it quietly gives you almost nothing.

  5. The preamble IS retrievable as text, but `raw_text_url` serves HTML-wrapped <pre>, not
     plain text, so "retrievable as text" needs a strip step the register did not budget.

  6. No rate-limit headers are exposed, so G006's rate-limit half cannot be answered by
     observation of headers and is bounded here by measurement instead.

NETWORK: fetches over HTTPS from www.federalregister.gov. Unreachable host RAISES; a probe
that skips into green would launder G006 and G036 back into "assumed".

RUN:
    python3 tests/probes/test_fr_api_paging.py
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------- pinned facts

API = "https://www.federalregister.gov/api/v1"
UA = {"User-Agent": "SignatureReady-probe/1 (phase -1; contact via repo)"}

TERM = '"7 CFR Part 1b"'

# The USDA NEPA rule and its amendment, discovered by agency+type+date search, not guessed.
RULE_DOC = "2026-06537"
RULE_CITATION = "91 FR 17062"
RULE_START, RULE_END = 17062, 17122
RULE_DATE = "2026-04-03"

AMENDMENT_DOC = "2026-13372"
AMENDMENT_CITATION = "91 FR 40353"
AMENDMENT_DATE = "2026-07-02"

# What build/constitution.md says today. Asserted as WRONG so the fix is forced.
CONSTITUTION_CLAIMS = "91 FR 17092"

PER_PAGE = 20
PAGE_CEILING = 50           # observed: page > 50 is ignored and the response wraps to page 1


def get(url, timeout=120):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(), dict(r.headers)


def api(path, **params):
    parts = []
    for k, v in params.items():
        if isinstance(v, (list, tuple)):
            for item in v:
                parts.append("%s=%s" % (k, urllib.parse.quote(str(item))))
        else:
            parts.append("%s=%s" % (k, urllib.parse.quote(str(v))))
    return "%s%s?%s" % (API, path, "&".join(parts))


def docs(**params):
    status, body, _ = get(api("/documents.json", **params))
    assert status == 200, "expected 200, got %s" % status
    return json.loads(body)


# ---------------------------------------------------------------- 1. G036

def test_g036_the_cfr_filter_cannot_name_part_1b():
    try:
        get(api("/documents.json", **{"conditions[cfr][title]": 7,
                                      "conditions[cfr][part]": "1b", "per_page": 5}))
    except urllib.error.HTTPError as e:
        assert e.code == 400, "expected 400 for part=1b, got %s" % e.code
        msg = e.read().decode("utf-8", "replace")
        assert "integer" in msg, "the 400 no longer explains why: %s" % msg[:200]
    else:
        raise AssertionError(
            "conditions[cfr][part]=1b now succeeds -- G036 may be resolved and the lineage "
            "could come from a CFR filter after all. Re-derive before relying on it.")

    # part=1 is a DIFFERENT part, not a loose match for 1b
    d = docs(**{"conditions[cfr][title]": 7, "conditions[cfr][part]": "1", "per_page": 1})
    assert d["count"] > 0, "part=1 returned nothing; the control for this test is gone"
    print("      part=1b -> HTTP 400; part=1 -> %d documents, a different part" % d["count"])


def test_g036_extends_to_document_metadata_not_just_the_query():
    """The sharper half: the rule's own cfr_references cannot say 1b either."""
    status, body, _ = get("%s/documents/%s.json" % (API, RULE_DOC))
    assert status == 200
    d = json.loads(body)
    refs = d.get("cfr_references") or []
    assert refs, "the NEPA rule no longer carries cfr_references"
    parts = {str(r.get("part")) for r in refs}
    assert "1b" not in parts, (
        "cfr_references now names 1b (%r) -- the API has gained subpart-letter precision "
        "and G036 should be revisited" % parts)
    assert "1" in parts, "expected part '1' as the coarse stand-in, got %r" % parts
    print("      the rule's own cfr_references records part=%s, never '1b'" % sorted(parts))


# ---------------------------------------------------------------- 2. the citation error

def test_the_constitution_names_an_interior_page_not_the_citation():
    """Tie-break rule 1. This probe is the primary source; the constitution is wrong."""
    status, body, _ = get("%s/documents/%s.json" % (API, RULE_DOC))
    assert status == 200
    d = json.loads(body)

    assert d["citation"] == RULE_CITATION, (
        "the rule's citation is now %r, pinned %r" % (d["citation"], RULE_CITATION))
    assert d["publication_date"] == RULE_DATE
    assert (d["start_page"], d["end_page"]) == (RULE_START, RULE_END), (
        "page span moved to %s-%s" % (d["start_page"], d["end_page"]))

    claimed_page = int(CONSTITUTION_CLAIMS.split()[-1])
    assert claimed_page != RULE_START, (
        "the constitution now agrees with the API; delete this test and the gap with it")
    assert RULE_START < claimed_page <= RULE_END, (
        "%d is not even an interior page of %s (%d-%d) -- the constitution's claim is wrong "
        "in a different way than recorded"
        % (claimed_page, RULE_CITATION, RULE_START, RULE_END))
    print("      constitution says %r; the rule is %r spanning pages %d-%d, so %d is an "
          "INTERIOR page" % (CONSTITUTION_CLAIMS, RULE_CITATION, RULE_START, RULE_END,
                             claimed_page))


def test_the_amendment_citation_is_correct():
    status, body, _ = get("%s/documents/%s.json" % (API, AMENDMENT_DOC))
    assert status == 200
    d = json.loads(body)
    assert d["citation"] == AMENDMENT_CITATION, (
        "amendment citation is %r, pinned %r" % (d["citation"], AMENDMENT_CITATION))
    assert d["publication_date"] == AMENDMENT_DATE
    assert "Environmental Policy Act" in d["title"], (
        "document %s is no longer the NEPA amendment: %r" % (AMENDMENT_DOC, d["title"]))
    print("      %s = %s on %s, %r -- the constitution is RIGHT about this one"
          % (AMENDMENT_DOC, AMENDMENT_CITATION, AMENDMENT_DATE, d["title"]))


# ---------------------------------------------------------------- 3. paging

def test_paging_is_offset_based_contra_the_register():
    first = docs(**{"conditions[term]": TERM, "per_page": PER_PAGE, "page": 1,
                    "fields[]": ["document_number"]})
    second = docs(**{"conditions[term]": TERM, "per_page": PER_PAGE, "page": 2,
                     "fields[]": ["document_number"]})
    assert second["results"], "page=2 returned nothing; offset paging may be gone"
    a = {r["document_number"] for r in first["results"]}
    b = {r["document_number"] for r in second["results"]}
    assert not (a & b), "pages 1 and 2 overlap on %r" % sorted(a & b)[:4]
    print("      ?page=N works and pages 1 and 2 are disjoint -- paging is OFFSET-based")


def test_the_page_parameter_is_silently_ignored_past_its_ceiling_and_wraps():
    """The headline defect. n.authority_ledger would double-count and nothing would error."""
    head = docs(**{"conditions[term]": TERM, "per_page": PER_PAGE, "page": 1,
                   "fields[]": ["document_number"]})
    count = head["count"]
    last_page = (count + PER_PAGE - 1) // PER_PAGE
    head_ids = [r["document_number"] for r in head["results"]]

    tail = docs(**{"conditions[term]": TERM, "per_page": PER_PAGE, "page": last_page,
                   "fields[]": ["document_number"]})
    assert tail["results"], "the computed last page %d is empty" % last_page

    just_past = docs(**{"conditions[term]": TERM, "per_page": PER_PAGE, "page": last_page + 1,
                        "fields[]": ["document_number"]})
    assert not just_past["results"], (
        "page %d past the end now returns rows; the wrap boundary moved" % (last_page + 1))

    beyond = docs(**{"conditions[term]": TERM, "per_page": PER_PAGE, "page": PAGE_CEILING + 1,
                     "fields[]": ["document_number"]})
    wrapped = [r["document_number"] for r in beyond["results"]]
    assert wrapped == head_ids, (
        "page %d no longer returns page 1's rows. Either the ceiling moved or the wrap was "
        "fixed -- re-derive before removing the guard this finding demands.\n"
        "  page 1:  %r\n  page %d: %r" % (PAGE_CEILING + 1, head_ids[:3],
                                          PAGE_CEILING + 1, wrapped[:3]))
    print("      count=%d, last page=%d. page %d -> 0 rows, but page %d -> PAGE ONE'S ROWS. "
          "A fixed-N page loop silently re-ingests the head."
          % (count, last_page, last_page + 1, PAGE_CEILING + 1))


def test_per_page_degrades_silently_past_its_ceiling():
    seen = {}
    for pp in (1000, 2000, 5000):
        d = docs(**{"conditions[term]": "nepa", "per_page": pp,
                    "fields[]": ["document_number"]})
        seen[pp] = len(d["results"])
    assert seen[1000] == 1000, "per_page=1000 returned %d" % seen[1000]
    assert seen[5000] < 100, (
        "per_page=5000 returned %d; the silent-degradation finding may be fixed" % seen[5000])
    print("      per_page 1000 -> %d, 2000 -> %d, 5000 -> %d (HTTP 200 throughout): asking "
          "past the ceiling silently yields the default page size"
          % (seen[1000], seen[2000], seen[5000]))


# ---------------------------------------------------------------- 4. preamble + rate limit

def test_the_preamble_is_retrievable_but_is_html_wrapped_not_plain_text():
    status, body, _ = get("%s/documents/%s.json" % (API, RULE_DOC))
    d = json.loads(body)
    url = d.get("raw_text_url")
    assert url, "the rule no longer exposes raw_text_url"
    status, raw, headers = get(url, timeout=180)
    assert status == 200
    assert len(raw) > 50000, "preamble is only %d bytes" % len(raw)
    head = raw[:200].decode("utf-8", "replace")
    assert head.lstrip().lower().startswith("<html"), (
        "raw_text_url is now actually plain text; the strip step this finding demands may "
        "be unnecessary. Head: %r" % head[:120])
    assert "<pre>" in raw[:600].decode("utf-8", "replace"), (
        "the <pre> wrapper is gone; re-derive the extraction step")
    print("      raw_text_url: %d bytes, served as HTML-wrapped <pre> despite the name"
          % len(raw))


def test_g006_no_rate_limit_headers_are_exposed():
    """Bounds the answerable part of G006: the API does not tell you your budget, so a
    retriever cannot back off on a header and must be paced by policy instead."""
    elapsed = []
    for _ in range(6):
        t0 = time.time()
        status, _, headers = get(api("/documents.json", **{
            "conditions[term]": "nepa", "per_page": 1, "fields[]": ["document_number"]}))
        elapsed.append(time.time() - t0)
        assert status == 200
        rate = [k for k in headers if "ratelimit" in k.lower().replace("-", "")]
        assert not rate, (
            "rate-limit headers now exist (%r) -- G006 is answerable by observation and a "
            "retriever should read them" % rate)
    print("      6 sequential requests, no rate-limit headers, %.2fs slowest -- pacing must "
          "be policy, not feedback" % max(elapsed))


# ---------------------------------------------------------------- runner

def main():
    print("Phase -1 probe: federalregister.gov / 7 CFR Part 1b lineage\n")
    checks = [
        test_g036_the_cfr_filter_cannot_name_part_1b,
        test_g036_extends_to_document_metadata_not_just_the_query,
        test_the_constitution_names_an_interior_page_not_the_citation,
        test_the_amendment_citation_is_correct,
        test_paging_is_offset_based_contra_the_register,
        test_the_page_parameter_is_silently_ignored_past_its_ceiling_and_wraps,
        test_per_page_degrades_silently_past_its_ceiling,
        test_the_preamble_is_retrievable_but_is_html_wrapped_not_plain_text,
        test_g006_no_rate_limit_headers_are_exposed,
    ]
    failures = 0
    for fn in checks:
        try:
            fn()
            print("  PASS %s" % fn.__name__)
        except AssertionError as exc:
            failures += 1
            print("  FAIL %s\n       %s" % (fn.__name__, exc))

    if failures:
        print("\n%d check(s) FAILED" % failures)
        return 1
    print("\nAll checks passed.")
    print("G036: CONFIRMED and widened -- the API cannot name Part 1b in queries OR metadata.")
    print("G006: page size ceiling and wrap measured; no rate-limit headers exist.")
    print("CONSTITUTION: '91 FR 17092' is an interior page. The citation is 91 FR 17062.")
    print("VERDICT: fail -- the probe ran and the prefab does not behave as expected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
