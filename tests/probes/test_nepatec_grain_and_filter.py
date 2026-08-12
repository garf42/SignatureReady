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

  4. G011 IS NOT ANSWERABLE HERE, and this is a NEW BLOCKER rather than work owed. The
     dataset is `gated: "auto"`, and the gate blocks every file in the repository --
     including `.gitattributes`. Only README.md and the metadata/tree APIs are public.
     `datasets-server` answers 401 for splits, first-rows and size. Row grain, page-level
     text and the substring property n.precedent/c1 depends on cannot be measured without
     an authenticated HuggingFace identity that has accepted the gate.

  5. A CORRECTION TO G033's CLOSURE NOTE, which recorded that "tree and parquet readable
     anonymously despite gated: auto". Both halves are wrong. THERE ARE NO PARQUET FILES --
     the corpus is 505 JSONL files and zero parquet -- and file content is not anonymously
     readable. What is readable is the tree, which is metadata, not data. Reachability was
     mistaken for retrievability.

NETWORK: fetches over HTTPS from huggingface.co. Unreachable host RAISES. The 401s below are
ASSERTED, not tolerated -- if the gate is lifted this probe fails and G011 becomes answerable,
which is the outcome worth being told about.

RUN:
    python3 tests/probes/test_nepatec_grain_and_filter.py
"""

import collections
import json
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


def test_there_is_no_usfs_bucket_so_the_contract_filter_is_coarser_than_stated():
    agencies = sorted({a for _, a in grid()})
    assert "USFS" not in agencies and "FS" not in agencies, (
        "a USFS bucket now exists (%r) -- n.precedent's USDA/USFS filter can be expressed "
        "after all" % agencies)
    print("      agency buckets are exactly %s; USFS is not separable from USDA"
          % ", ".join(agencies))


def test_the_usda_slice_carries_no_eis_at_all():
    g = grid()
    assert g.get(("EIS", "USDA"), 0) == 0, (
        "USDA now has %d EIS files -- precedent coverage for the EIS and ROD paths may be "
        "available from this corpus" % g[("EIS", "USDA")])
    assert g.get(("EIS", "EPA"), 0) > 100, (
        "EPA's EIS bulk is gone; the contrast this finding rests on has changed")
    print("      USDA: %d CE, %d EA, 0 EIS. EPA holds %d EIS. The five document types the "
          "constitution requires cannot all be covered from the USDA slice."
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


def test_g011_row_grain_is_unanswerable_and_datasets_server_confirms_it():
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


# ---------------------------------------------------------------- runner

def main():
    print("Phase -1 probe: PNNL/NEPATEC2.0 / the USDA slice\n")
    checks = [
        test_the_corpus_is_partitioned_by_doc_type_and_agency_in_the_path,
        test_there_are_no_parquet_files_correcting_the_g033_closure_note,
        test_g012_selectivity_is_measurable_and_non_trivial,
        test_there_is_no_usfs_bucket_so_the_contract_filter_is_coarser_than_stated,
        test_the_usda_slice_carries_no_eis_at_all,
        test_the_gate_blocks_every_file_including_gitattributes,
        test_readme_and_the_tree_apis_are_public_so_the_gate_is_on_content_only,
        test_g011_row_grain_is_unanswerable_and_datasets_server_confirms_it,
    ]
    failures = 0
    for fn in checks:
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
    print("G012: ANSWERED at file granularity -- 60/505 = 11.9% USDA, and there is no USFS.")
    print("G011: BLOCKED on HuggingFace authentication, not on effort. New blocker.")
    print("VERDICT: fail -- the probe ran and the prefab does not behave as expected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
