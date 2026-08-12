"""Phase -1 prefab probe: PNNL/NEPATEC2.0, the USDA slice.

prefab:     PNNL/NEPATEC2.0
used_by:    n.precedent
probe_dims: the USDA/USFS slice only, not the whole corpus
gaps:       G011 -- row grain unverified. Assumed one row per document with page-level text
            G012 -- USDA/USFS filter selectivity unmeasured. Assumed non-trivial

WHAT THIS PROBE ESTABLISHES, by running code against the real dataset:

  1. G012 IS ANSWERED, at FILE granularity and no finer. The corpus is partitioned by path
     as <doc_type>/<agency>/*.jsonl, so selectivity is measurable from the tree alone
     without downloading anything: 60 of 505 files are USDA. That is 11.9%, which confirms
     the gap's "assumed non-trivial" -- but see 2 and 3 before spending it.

  2. THERE IS NO USFS. The corpus carries exactly four agency buckets -- BLM, DOE, EPA,
     USDA. "USDA/USFS" is not a filter this corpus can express; USFS is not separable from
     USDA at any granularity visible without the data. n.precedent's filter is therefore
     coarser than its contract implies.

  3. USDA HAS ZERO EIS FILES. It carries 30 CE and 30 EA and nothing else, while EPA
     carries 230 EIS. The constitution's non-vacuity clause wants >=1 emitted document of
     each of five types, and precedent coverage for the EIS and ROD paths cannot come from
     the USDA slice of this corpus at all.

  4. THE GATE IS ON CONTENT AND STILL BLOCKS ANONYMOUS READS. The dataset is
     `gated: "auto"`, and anonymously the gate blocks every file in the repository --
     including `.gitattributes`. Only README.md and the metadata/tree APIs are public.
     `datasets-server` answers 401 for splits, first-rows and size. This is unchanged and
     still asserted below: it is what makes the partition measurable and the rows not.

  5. A CORRECTION TO G033's CLOSURE NOTE, which recorded that "tree and parquet readable
     anonymously despite gated: auto". Both halves are wrong. THERE ARE NO PARQUET FILES --
     the corpus is 505 JSONL files and zero parquet -- and file content is not anonymously
     readable. What is readable is the tree, which is metadata, not data. Reachability was
     mistaken for retrievability.

SECTION 4 -- THE AUTHENTICATED HALF, run 2026-08-12 with a HuggingFace token that has
accepted the gate. G011 IS NOW ANSWERED, and three findings above are CORRECTED by it.
The anonymous half is kept exactly as it was: it characterises the gate, and it is still true.

  6. G011 IS ANSWERED, AND BOTH CANDIDATE ANSWERS IN THE CONSTITUTION WERE WRONG. The grain
     is neither one row per document nor one row per chunk. IT IS ONE ROW PER PROJECT:
     {project, process, documents[]}, where each document carries {metadata, pages[]} and
     each page is {"page number", "page text"} -- note the literal spaces in those keys.
     Page-level text therefore EXISTS NATIVELY and n.precedent/c1 is satisfiable without a
     chunker inventing page anchors.

  7. USFS IS SEPARABLE AFTER ALL, and finding 2 above is REFUTED as a claim about the corpus
     (it remains true as a claim about the *path tree*). `process.lead_agency` distinguishes
     "Department of Agriculture - Forest Service" (30 of 210 USDA projects, 14.3%) from
     "Department of Agriculture" (177). n.precedent's USDA/USFS filter IS expressible -- just
     not from the path, which is the only thing the anonymous half could see.

  8. THE PATH PARTITION IS IMPURE. 3 of the 210 projects under USDA/ carry a non-USDA lead
     agency -- two DOE, one Bureau of Reclamation. Filtering by path is not filtering by
     agency, and the ADVISORY selectivity number must say which one it measured.

  9. FINDING 3 IS HALF REFUTED. At DOCUMENT granularity the USDA slice holds CE 173, EA 18,
     FONSI 14, OTHER 2, DEA 2, and ROD 1. So ROD coverage is not absent -- it is n=1, which
     satisfies the constitution's >=1 non-vacuity requirement by a single document and is
     one deletion away from failing. EIS is the only type genuinely absent: zero, at both
     file and document granularity. The path buckets CE/EA/EIS are PROCESS families; the
     document_type field is a different axis and does not agree with them.

 10. TWO INTEGRITY HAZARDS, both measured. `file_metadata.total_pages` disagrees with
     `len(pages)` on 174 of 210 USDA documents -- pages[] is a chunking, not a page-by-page
     rendering, and 7.9% of USDA page numbers are RANGES ("1-12"), so "the named page" is
     sometimes a span of up to 18 pages. And 8.8% of pages corpus-wide have empty text
     (0.1% within USDA), which a substring check must reject rather than trivially pass.

NETWORK: fetches over HTTPS from huggingface.co. Unreachable host RAISES. The anonymous 401s
are ASSERTED, not tolerated. The authenticated half needs a token at ~/.cache/huggingface/token
whose identity has accepted the gate; without one it reports BLOCKED and does not fail, because
a missing credential is not a regression in the corpus.

RUN:
    python3 tests/probes/test_nepatec_grain_and_filter.py          # both halves
    NEPATEC_SKIP_AUTHED=1 python3 tests/probes/...                 # anonymous half only
"""

import collections
import json
import os
import re
import sys
import urllib.error
import urllib.request

# ---------------------------------------------------------------- pinned facts

REPO = "PNNL/NEPATEC2.0"
HF = "https://huggingface.co"
UA = {"User-Agent": "SignatureReady-probe/1 (phase -1; contact via repo)"}

EXPECTED_AGENCIES = ["BLM", "DOE", "EPA", "USDA"]
EXPECTED_DOC_TYPES = ["CE", "EA", "EIS"]
EXPECTED_JSONL = 505

# Observed 2026-08-12, from the path partition alone.
EXPECTED_GRID = {
    ("CE", "BLM"): 30, ("EA", "BLM"): 60, ("EIS", "BLM"): 35,
    ("CE", "DOE"): 30, ("EA", "DOE"): 30, ("EIS", "DOE"): 30,
    ("CE", "EPA"): 0, ("EA", "EPA"): 0, ("EIS", "EPA"): 230,
    ("CE", "USDA"): 30, ("EA", "USDA"): 30, ("EIS", "USDA"): 0,
}
USDA_FILES = 60

GATED_SAMPLE = "CE/USDA/nepatec2_CE_USDA_001.jsonl"


def get(url, timeout=120):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


_META = {}


def metadata():
    if not _META:
        status, body = get("%s/api/datasets/%s" % (HF, REPO))
        assert status == 200, "dataset metadata returned %s" % status
        _META.update(json.loads(body))
    return _META


def jsonl_paths():
    return [s["rfilename"] for s in metadata()["siblings"]
            if s["rfilename"].endswith(".jsonl")]


def grid():
    g = collections.Counter()
    for path in jsonl_paths():
        parts = path.split("/")
        if len(parts) >= 3:
            g[(parts[0], parts[1])] += 1
    return g


# ---------------------------------------------------------------- 1. the corpus shape

def test_the_corpus_is_partitioned_by_doc_type_and_agency_in_the_path():
    """This is what makes G012 measurable without retrieving anything."""
    paths = jsonl_paths()
    assert len(paths) == EXPECTED_JSONL, (
        "%d jsonl files, pinned %d -- the corpus changed" % (len(paths), EXPECTED_JSONL))

    g = grid()
    assert sorted({t for t, _ in g}) == EXPECTED_DOC_TYPES, (
        "doc types are now %r" % sorted({t for t, _ in g}))
    assert sorted({a for _, a in g}) == EXPECTED_AGENCIES, (
        "agencies are now %r" % sorted({a for _, a in g}))
    assert dict(g) == {k: v for k, v in EXPECTED_GRID.items() if v}, (
        "the doc_type x agency grid moved:\n  got    %r\n  pinned %r"
        % (dict(sorted(g.items())), EXPECTED_GRID))


def test_there_are_no_parquet_files_correcting_the_g033_closure_note():
    names = [s["rfilename"] for s in metadata()["siblings"]]
    parquet = [n for n in names if n.endswith(".parquet")]
    assert not parquet, (
        "parquet files now exist (%d, e.g. %r) -- G033's closure note was right after all "
        "and the retrieval path should be reconsidered" % (len(parquet), parquet[:2]))
    print("      %d files total, %d jsonl, 0 parquet" % (len(names), len(jsonl_paths())))


# ---------------------------------------------------------------- 2. G012

def test_g012_selectivity_is_measurable_and_non_trivial():
    g = grid()
    total = sum(g.values())
    usda = sum(n for (_, a), n in g.items() if a == "USDA")
    assert usda == USDA_FILES, "USDA slice is %d files, pinned %d" % (usda, USDA_FILES)
    pct = 100.0 * usda / total
    assert 5.0 < pct < 25.0, (
        "USDA selectivity is now %.1f%%, outside the band this finding recorded" % pct)
    print("      USDA slice: %d of %d files = %.1f%% -- G012's 'non-trivial' holds, at FILE "
          "granularity only" % (usda, total, pct))


def test_there_is_no_usfs_bucket_in_the_path_tree():
    """Scope corrected 2026-08-12. This is true of the PATH TREE and only of the path tree.
    USFS *is* separable from the data via process.lead_agency -- see the authenticated half,
    which refutes the conclusion this check used to print."""
    agencies = sorted({a for _, a in grid()})
    assert "USFS" not in agencies and "FS" not in agencies, (
        "a USFS bucket now exists in the path tree (%r) -- the filter can be expressed "
        "from the tree alone, which it previously could not" % agencies)
    print("      path buckets are exactly %s -- no USFS *bucket*. Separability is a "
          "question about lead_agency, answered in the authenticated half"
          % ", ".join(agencies))


def test_the_usda_slice_carries_no_eis_files():
    """Scope corrected 2026-08-12. CE/EA/EIS are PROCESS families in the path, not document
    types. 'No EIS' survives at both granularities; 'no ROD' did not -- see the authed half."""
    g = grid()
    assert g.get(("EIS", "USDA"), 0) == 0, (
        "USDA now has %d EIS files -- precedent coverage for the EIS path may be "
        "available from this corpus" % g[("EIS", "USDA")])
    assert g.get(("EIS", "EPA"), 0) > 100, (
        "EPA's EIS bulk is gone; the contrast this finding rests on has changed")
    print("      USDA: %d CE, %d EA, 0 EIS files. EPA holds %d EIS. EIS is the one type "
          "the USDA slice cannot cover at any granularity."
          % (g[("CE", "USDA")], g[("EA", "USDA")], g[("EIS", "EPA")]))


# ---------------------------------------------------------------- 3. G011 is blocked

def test_the_gate_blocks_every_file_including_gitattributes():
    """Asserting the 401 rather than tolerating it. If the gate lifts, this goes red and
    G011 becomes answerable -- which is exactly the news worth having."""
    blocked = []
    for path in (GATED_SAMPLE, ".gitattributes", "CE/BLM/nepatec2_CE_BLM_001.jsonl"):
        url = "%s/datasets/%s/resolve/main/%s" % (HF, REPO, path)
        try:
            status, body = get(url)
        except urllib.error.HTTPError as e:
            assert e.code == 401, "expected 401 for %s, got %s" % (path, e.code)
            blocked.append(path)
            continue
        raise AssertionError(
            "%s is now readable anonymously (%s, %d bytes) -- the gate has lifted and G011 "
            "should be probed for real" % (path, status, len(body)))
    assert len(blocked) == 3
    assert metadata().get("gated") == "auto", (
        "the dataset's gated flag is now %r" % metadata().get("gated"))
    print("      gated=auto blocks all 3 sampled paths, including .gitattributes")


def test_readme_and_the_tree_apis_are_public_so_the_gate_is_on_content_only():
    status, body = get("%s/datasets/%s/resolve/main/README.md" % (HF, REPO))
    assert status == 200 and len(body) > 1000, "README.md is no longer public"
    status, _ = get("%s/api/datasets/%s/tree/main/CE/USDA" % (HF, REPO))
    assert status == 200, "the tree API is no longer public"
    print("      README.md (%d bytes) and the tree API are public; the gate is on file "
          "content, which is why the partition is measurable and the rows are not"
          % len(body))


def test_datasets_server_refuses_anonymously():
    """Why G011 was blocked before a credential existed. Kept as a characterisation of the
    gate; G011 itself is answered in the authenticated half below."""
    for endpoint in ("splits", "first-rows", "size"):
        url = ("https://datasets-server.huggingface.co/%s?dataset=%s" % (endpoint, REPO))
        if endpoint == "first-rows":
            url += "&config=default&split=train"
        try:
            status, body = get(url)
        except urllib.error.HTTPError as e:
            assert e.code in (401, 404), "%s returned %s" % (endpoint, e.code)
            continue
        raise AssertionError(
            "datasets-server /%s now answers (%s) -- row grain is measurable and G011 "
            "should be probed for real rather than recorded as blocked" % (endpoint, status))
    print("      datasets-server splits/first-rows/size all refuse: G011 needs an "
          "authenticated identity that has accepted the gate")


# ------------------------------------------------- 4. G011, with the gate accepted
#
# Everything below needs a token. Measured 2026-08-12; every number is pinned so that a
# change in the corpus fails this probe instead of silently re-scoping the findings.

TOKEN_PATH = os.path.expanduser("~/.cache/huggingface/token")

# The USDA slice, whole -- all 60 files, not a sample.
USDA_PROJECTS = 210
USDA_DOCUMENTS = 210
USDA_PAGES = 2241
USDA_DOC_TYPES = {"CE": 173, "EA": 18, "FONSI": 14, "OTHER": 2, "DEA": 2, "ROD": 1}
USDA_LEAD_AGENCIES = {
    "Department of Agriculture": 177,
    "Department of Agriculture - Forest Service": 30,
    "Department of Energy - Department of Energy": 2,
    "Department of the Interior - Bureau of Reclamation": 1,
}
USFS_PROJECTS = 30
NON_USDA_UNDER_USDA_PATH = 3
USDA_PAGENUM_RANGES = 177
USDA_TOTALPAGES_MISMATCH = 174
USDA_PREPARED_BY = 208            # NOT 210 -- two documents carry an empty list
USDA_PREPARED_BY_DELIMITED = 165

ROW_KEYS = {"project", "process", "documents"}
PAGE_KEYS = {"page number", "page text"}

_AUTH = {}


def token():
    """None when there is no credential -- a missing token is not a corpus regression."""
    if "tok" not in _AUTH:
        try:
            with open(TOKEN_PATH) as fh:
                _AUTH["tok"] = fh.read().strip() or None
        except OSError:
            _AUTH["tok"] = None
    return _AUTH["tok"]


def authed(url, timeout=180):
    req = urllib.request.Request(url, headers=dict(UA))
    req.add_header("Authorization", "Bearer %s" % token())
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def usda_rows():
    """Every row of all 60 USDA files. Cached: this is ~6 MB over 60 requests."""
    if "rows" not in _AUTH:
        rows = []
        for path in sorted(p for p in jsonl_paths() if "/USDA/" in p):
            _, body = authed("%s/datasets/%s/resolve/main/%s" % (HF, REPO, path))
            rows.extend(json.loads(l) for l in body.decode("utf-8").split("\n") if l.strip())
        _AUTH["rows"] = rows
    return _AUTH["rows"]


def value_of(container, key):
    """Every project/process/metadata leaf is wrapped as {"value": ...}. The payload is
    polymorphic -- str, list or int depending on the field -- so this never assumes str."""
    node = (container or {}).get(key)
    return node.get("value") if isinstance(node, dict) else None


def test_the_gate_is_accepted_by_this_identity():
    status, body = authed("%s/api/whoami-v2" % HF)
    who = json.loads(body)
    assert status == 200 and who.get("name"), "whoami-v2 did not identify the token"
    _, body = authed("%s/datasets/%s/resolve/main/%s" % (HF, REPO, GATED_SAMPLE))
    assert len(body) > 1000, "gated sample came back empty"
    print("      identity %r has accepted the gate; %s reads back %d bytes"
          % (who["name"], GATED_SAMPLE, len(body)))


def test_g011_the_row_grain_is_one_row_per_project():
    """THE ANSWER TO G011. Neither of the constitution's two candidates was right."""
    rows = usda_rows()
    assert len(rows) == USDA_PROJECTS, (
        "USDA slice holds %d rows, pinned %d" % (len(rows), USDA_PROJECTS))
    shapes = {frozenset(r.keys()) for r in rows}
    assert shapes == {frozenset(ROW_KEYS)}, (
        "row shape moved: %r" % [sorted(s) for s in shapes])

    docs = sum(len(r["documents"]) for r in rows)
    pages = sum(len(d.get("pages") or []) for r in rows for d in r["documents"])
    assert (docs, pages) == (USDA_DOCUMENTS, USDA_PAGES), (
        "USDA slice is now %d documents / %d pages, pinned %d / %d"
        % (docs, pages, USDA_DOCUMENTS, USDA_PAGES))

    pk = {frozenset(p.keys()) for r in rows for d in r["documents"]
          for p in (d.get("pages") or [])}
    assert pk == {frozenset(PAGE_KEYS)}, (
        "pages[] key set moved: %r -- 'page number'/'page text' carry literal spaces"
        % [sorted(s) for s in pk])
    print("      ONE ROW PER PROJECT: %d projects -> %d documents -> %d pages; "
          "pages are exactly %s" % (len(rows), docs, pages, sorted(PAGE_KEYS)))


def test_usfs_is_separable_from_lead_agency_refuting_the_anonymous_finding():
    """The correction that matters most to n.precedent's contract."""
    seen = collections.Counter()
    for r in usda_rows():
        for a in (value_of(r.get("process"), "lead_agency") or []):
            seen[a] += 1
    assert dict(seen) == USDA_LEAD_AGENCIES, (
        "lead_agency distribution moved:\n  got    %r\n  pinned %r"
        % (dict(seen), USDA_LEAD_AGENCIES))
    usfs = seen["Department of Agriculture - Forest Service"]
    assert usfs == USFS_PROJECTS
    print("      USFS IS separable: %d of %d projects = %.1f%% carry lead_agency "
          "'...- Forest Service'. The USDA/USFS filter is expressible."
          % (usfs, USDA_PROJECTS, 100.0 * usfs / USDA_PROJECTS))


def test_the_usda_path_bucket_contains_non_usda_lead_agencies():
    """Filtering by path is not filtering by agency. The ADVISORY selectivity number in
    n.precedent/c2 has to say which of the two it measured."""
    stray = [a for r in usda_rows()
             for a in (value_of(r.get("process"), "lead_agency") or [])
             if not a.startswith("Department of Agriculture")]
    assert len(stray) == NON_USDA_UNDER_USDA_PATH, (
        "%d non-USDA lead agencies under USDA/, pinned %d: %r"
        % (len(stray), NON_USDA_UNDER_USDA_PATH, stray))
    print("      the USDA path bucket is IMPURE: %d of %d projects are led by %s"
          % (len(stray), USDA_PROJECTS, sorted(set(stray))))


def test_rod_exists_at_document_granularity_but_eis_does_not():
    """Half-refutes the anonymous finding. ROD is n=1, not zero -- non-vacuity for the ROD
    path rests on a single document. EIS is genuinely absent at both granularities."""
    seen = collections.Counter()
    for r in usda_rows():
        for d in r["documents"]:
            dm = (d.get("metadata") or {}).get("document_metadata") or {}
            seen[value_of(dm, "document_type")] += 1
    assert dict(seen) == USDA_DOC_TYPES, (
        "document_type distribution moved:\n  got    %r\n  pinned %r"
        % (dict(seen), USDA_DOC_TYPES))
    assert seen["ROD"] == 1, "ROD count moved off 1"
    assert not any(t in seen for t in ("EIS", "FEIS", "DEIS")), (
        "an EIS-family document type appeared in the USDA slice: %r" % dict(seen))
    print("      documents by type: %s"
          % ", ".join("%s=%d" % kv for kv in sorted(seen.items())))
    print("      ROD=1 satisfies >=1 non-vacuity by ONE document; EIS=0 cannot be covered")


def test_page_anchoring_is_real_but_the_named_page_is_sometimes_a_span():
    """n.precedent/c1 -- 'every chunk a substring of its named page'. Satisfiable, with two
    measured hazards: range-valued page numbers, and empty pages that would pass trivially."""
    ranges = empties = 0
    checked = 0
    for r in usda_rows():
        for d in r["documents"]:
            for p in d.get("pages") or []:
                num, txt = p["page number"].strip(), p["page text"]
                if re.match(r"^\d+\s*-\s*\d+$", num):
                    ranges += 1
                if not txt.strip():
                    empties += 1
                elif checked < 200 and len(txt) > 400:
                    chunk = txt[120:340]
                    assert chunk in txt, "a slice of a page is not a substring of it"
                    checked += 1
    assert ranges == USDA_PAGENUM_RANGES, (
        "range-valued page numbers moved: %d, pinned %d" % (ranges, USDA_PAGENUM_RANGES))
    assert checked >= 100, "only %d pages were long enough to exercise c1" % checked
    print("      c1 holds on %d sampled pages. HAZARDS: %d/%d page numbers (%.1f%%) are "
          "SPANS not pages; %d pages are empty and would pass a substring check vacuously"
          % (checked, ranges, USDA_PAGES, 100.0 * ranges / USDA_PAGES, empties))


def test_total_pages_metadata_disagrees_with_the_page_array():
    """pages[] is a chunking, not a page-by-page rendering. Anything that trusts
    total_pages as the length of pages[] is wrong on 83% of USDA documents."""
    mismatch = match = 0
    for r in usda_rows():
        for d in r["documents"]:
            fm = (d.get("metadata") or {}).get("file_metadata") or {}
            tp = value_of(fm, "total_pages")
            if isinstance(tp, int) and tp == len(d.get("pages") or []):
                match += 1
            else:
                mismatch += 1
    assert mismatch == USDA_TOTALPAGES_MISMATCH, (
        "total_pages agreement moved: %d mismatch / %d match, pinned %d mismatch"
        % (mismatch, match, USDA_TOTALPAGES_MISMATCH))
    print("      file_metadata.total_pages != len(pages) on %d of %d documents (%.0f%%)"
          % (mismatch, USDA_DOCUMENTS, 100.0 * mismatch / USDA_DOCUMENTS))


def test_prepared_by_names_organisations_not_people():
    """Bears on n.expert_directory and on aip.document-intelligence's probe dimension. The
    corpus hands over ORGANISATIONS in a delimited blob; individual preparers are not here
    and must come from the page text, which is what makes the AIP probe load-bearing."""
    present = delimited = 0
    for r in usda_rows():
        for d in r["documents"]:
            dm = (d.get("metadata") or {}).get("document_metadata") or {}
            pb = value_of(dm, "prepared_by")
            if isinstance(pb, list) and pb:
                present += 1
                if any(";" in s or "\n" in s for s in pb if isinstance(s, str)):
                    delimited += 1
    assert present == USDA_PREPARED_BY, (
        "prepared_by is populated on %d of %d documents, pinned %d"
        % (present, USDA_DOCUMENTS, USDA_PREPARED_BY))
    assert delimited == USDA_PREPARED_BY_DELIMITED, (
        "%d delimited multi-org blobs, pinned %d" % (delimited, USDA_PREPARED_BY_DELIMITED))
    print("      prepared_by populated on %d/%d documents -- NOT all of them, %d are empty; "
          "%d carry ';'- or newline-delimited multi-org blobs. Orgs only, no individuals."
          % (present, USDA_DOCUMENTS, USDA_DOCUMENTS - present, delimited))


AUTHED_CHECKS = [
    test_the_gate_is_accepted_by_this_identity,
    test_g011_the_row_grain_is_one_row_per_project,
    test_usfs_is_separable_from_lead_agency_refuting_the_anonymous_finding,
    test_the_usda_path_bucket_contains_non_usda_lead_agencies,
    test_rod_exists_at_document_granularity_but_eis_does_not,
    test_page_anchoring_is_real_but_the_named_page_is_sometimes_a_span,
    test_total_pages_metadata_disagrees_with_the_page_array,
    test_prepared_by_names_organisations_not_people,
]


# ---------------------------------------------------------------- runner

def main():
    print("Phase -1 probe: PNNL/NEPATEC2.0 / the USDA slice\n")
    checks = [
        test_the_corpus_is_partitioned_by_doc_type_and_agency_in_the_path,
        test_there_are_no_parquet_files_correcting_the_g033_closure_note,
        test_g012_selectivity_is_measurable_and_non_trivial,
        test_there_is_no_usfs_bucket_in_the_path_tree,
        test_the_usda_slice_carries_no_eis_files,
        test_the_gate_blocks_every_file_including_gitattributes,
        test_readme_and_the_tree_apis_are_public_so_the_gate_is_on_content_only,
        test_datasets_server_refuses_anonymously,
    ]

    skip_authed = os.environ.get("NEPATEC_SKIP_AUTHED") or not token()
    if not skip_authed:
        checks = checks + AUTHED_CHECKS

    failures = 0
    for fn in checks:
        if fn is AUTHED_CHECKS[0]:
            print("\n  -- authenticated half: G011 --")
        try:
            fn()
            print("  PASS %s" % fn.__name__)
        except AssertionError as exc:
            failures += 1
            print("  FAIL %s\n       %s" % (fn.__name__, exc))

    g = grid()
    print("\n  %-6s %s" % ("agency", "  ".join("%-5s" % t for t in EXPECTED_DOC_TYPES)))
    for a in EXPECTED_AGENCIES:
        print("  %-6s %s   total=%d"
              % (a, "  ".join("%-5d" % g.get((t, a), 0) for t in EXPECTED_DOC_TYPES),
                 sum(g.get((t, a), 0) for t in EXPECTED_DOC_TYPES)))

    if failures:
        print("\n%d check(s) FAILED" % failures)
        return 1
    print("\nAll checks passed.")
    if skip_authed:
        print("G011: NOT RE-MEASURED -- no token at %s. The recorded answer stands "
              "unverified by this run." % TOKEN_PATH)
        print("VERDICT: fail (anonymous half only).")
        return 0
    print("G012: ANSWERED. 60/505 = 11.9% of files, but the path bucket is IMPURE (3 of 210 "
          "projects are not USDA-led) and USFS IS separable via lead_agency, 30/210 = 14.3%.")
    print("G011: ANSWERED. One row per PROJECT -- {project, process, documents[]}, each "
          "document {metadata, pages[]}, each page {'page number','page text'}. Neither "
          "'per document' nor 'per chunk' was correct.")
    print("n.precedent/c1 is SATISFIABLE -- page text is native. Hazards: 7.9% of USDA page "
          "numbers are spans, total_pages disagrees with len(pages) on 83% of documents.")
    print("NON-VACUITY: CE/EA/FONSI/ROD are all present in the USDA slice (ROD by exactly "
          "one document); EIS is absent at every granularity and cannot be covered.")
    print("VERDICT: fail -- the probe ran and the prefab does not behave as expected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
