"""Phase -1 prefab probe: GSA-TTS/pic-standards v1.2 crosswalk.

prefab:   GSA-TTS/pic-standards
used_by:  n.ontology
gap:      G007 -- "PIC v1.2 crosswalk (entity, property) uniqueness. Assumed: unique."

WHAT THIS PROBE ESTABLISHES, by running code against the real artifact:

  1. The v1.2 artifact exists, at a discovered (not assumed) path, at a pinned commit.
     - repo:   https://github.com/GSA-TTS/pic-standards
     - tag:    v1.2.0  (LIGHTWEIGHT tag -- `git ls-remote --tags` shows no `^{}` peel,
               so the tag name resolves directly to the commit below)
     - commit: fba4c70036eab7aeb43069f5e527e6efd756d263
     - path:   src/crosswalk/database_crosswalk.csv
     The filename was DISCOVERED by checking out the tag and listing src/crosswalk/,
     not guessed. The directory holds exactly two files: database_crosswalk.csv and
     todo.md. There is no file named "crosswalk_v1.2.csv" or similar.

  2. (entity, property) uniqueness -- G007's assumption. HOLDS at this commit.

  3. The distinct PIC entity count -- the size of the obligation n.ontology takes on in
     "every PIC v1.2 entity maps to an object type or carries a recorded reason it does not".

  4. The provenance properties n.ontology must carry onto every mapped type.

COLUMN-NAME NOTE (tie-break rule 7, explicit over inferred):
  The CSV header is `table,column,data_type,description,is_generated`. It does NOT use the
  words "entity" and "property". The repo README states the crosswalk is a "csv file
  containing a list of all entities, properties, types (postgres), and descriptions", which
  is the source's own explicit mapping of table->entity and column->property. This probe
  uses that mapping and asserts the header, so a future header change fails loudly rather
  than silently re-keying the uniqueness check.

NETWORK: this probe re-fetches over HTTPS from raw.githubusercontent.com at the pinned
commit. If the host is unreachable the probe RAISES -- it never skips into a green run,
because a silent pass here would launder G007 back into "assumed".

RUN:
    pytest tests/probes/test_pic_crosswalk_uniqueness.py -v
    python  tests/probes/test_pic_crosswalk_uniqueness.py
"""

import csv
import collections
import hashlib
import io
import re
import sys
import urllib.request

# ---------------------------------------------------------------- pinned facts

REPO = "GSA-TTS/pic-standards"
TAG = "v1.2.0"
COMMIT = "fba4c70036eab7aeb43069f5e527e6efd756d263"
CSV_PATH = "src/crosswalk/database_crosswalk.csv"

RAW_URL = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{CSV_PATH}"

# Git's ref advertisement over plain HTTPS. No git binary, no credentials, no GitHub API
# (api.github.com answers 403 through this build's proxy). This is what lets the probe assert
# that the MOVABLE tag v1.2.0 still names the immutable commit we pinned.
REFS_URL = f"https://github.com/{REPO}/info/refs?service=git-upload-pack"

# sha256 of the file bytes at the pinned commit, verified byte-identical between the
# raw.githubusercontent.com fetch and a `git clone --branch v1.2.0` checkout.
EXPECTED_SHA256 = "a925658d8f88344577f02c5b8751b563a1a077b70460fc76381d5f56a9922232"

EXPECTED_HEADER = ["table", "column", "data_type", "description", "is_generated"]

# Observed at the pinned commit. Asserted, not assumed: if PIC republishes v1.2.0 or the
# build repoints at a later commit, these go red and the obligation gets re-counted.
EXPECTED_ROW_COUNT = 292
EXPECTED_ENTITY_COUNT = 13

EXPECTED_ENTITIES = [
    "case_event",
    "comment",
    "decision_element",
    "document",
    "engagement",
    "gis_data",
    "gis_data_element",
    "legal_structure",
    "process_decision_payload",
    "process_instance",
    "process_model",
    "project",
    "user_role",
]

# The six provenance properties the repo README names under "Version 1.1 to 1.2 -> New
# Provenance Properties (added to all tables)". n.ontology guarantees these are carried
# onto every mapped type, so the probe checks the README's claim against the actual CSV.
PROVENANCE_PROPERTIES = [
    "data_record_version",
    "data_source_agency",
    "data_source_system",
    "last_updated",
    "record_owner_agency",
    "retrieved_timestamp",
]

# Present on all 13 entities but NOT provenance -- structural//catch-all columns. Recorded
# so a later session does not mistake "universal" for "provenance".
EXPECTED_UNIVERSAL_NON_PROVENANCE = ["created_at", "id", "other"]


# ---------------------------------------------------------------- fetch + parse

def fetch_csv_bytes():
    """Re-fetch the crosswalk at the pinned commit. Never falls back to a local copy."""
    try:
        with urllib.request.urlopen(RAW_URL, timeout=60) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status} from {RAW_URL}")
            return resp.read()
    except Exception as exc:
        raise RuntimeError(
            "PIC crosswalk probe could not re-fetch the pinned artifact.\n"
            f"  url: {RAW_URL}\n"
            f"  err: {exc!r}\n"
            "This probe deliberately does NOT skip on network failure: G007 is only "
            "discharged by reading the real file."
        ) from exc


def fetch_tag_refs():
    """Read the repo's tag advertisement over plain HTTPS. Returns {refname: sha}."""
    try:
        with urllib.request.urlopen(REFS_URL, timeout=60) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status} from {REFS_URL}")
            body = resp.read()
    except Exception as exc:
        raise RuntimeError(
            "PIC crosswalk probe could not read the upstream tag advertisement.\n"
            f"  url: {REFS_URL}\n  err: {exc!r}\n"
            "This probe deliberately does NOT skip: an unchecked movable tag is exactly the "
            "hole this test exists to close."
        ) from exc
    text = body.decode("utf-8", "replace")
    return {
        m.group(2): m.group(1)
        for m in re.finditer(r"([0-9a-f]{40}) (refs/tags/[^\s\x00]+)", text)
    }


def load_rows():
    raw = fetch_csv_bytes()
    got = hashlib.sha256(raw).hexdigest()
    assert got == EXPECTED_SHA256, (
        "crosswalk bytes changed at the pinned commit -- a pinned commit must be "
        f"immutable.\n  expected sha256 {EXPECTED_SHA256}\n  got      sha256 {got}"
    )
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""))
    return list(reader), reader.fieldnames


# ---------------------------------------------------------------------- tests

def test_artifact_exists_at_pinned_commit_with_expected_shape():
    """1. The file exists at the pinned path/commit and has the header we key on."""
    rows, fieldnames = load_rows()
    assert list(fieldnames) == EXPECTED_HEADER, (
        f"crosswalk header changed: {fieldnames!r}. The entity/property keys used by this "
        "probe (table, column) are no longer valid -- re-derive before trusting G007."
    )
    assert len(rows) == EXPECTED_ROW_COUNT, (
        f"row count {len(rows)} != pinned {EXPECTED_ROW_COUNT}. "
        "Note: `wc -l` reports 301 because description fields contain embedded newlines; "
        "292 is the parsed record count."
    )
    blank_table = [i for i, r in enumerate(rows) if not (r["table"] or "").strip()]
    assert not blank_table, f"rows with a blank `table` (entity) value at indices {blank_table}"
    blank_col = [i for i, r in enumerate(rows) if not (r["column"] or "").strip()]
    assert not blank_col, f"rows with a blank `column` (property) value at indices {blank_col}"


def test_tag_v1_2_0_still_resolves_to_the_pinned_commit():
    """The pin is only as good as the tag->commit binding, and that binding is MOVABLE.

    v1.2.0 is a LIGHTWEIGHT tag (no `^{}` peel in the advertisement), so upstream can move it
    with `git tag -f` at any time. Every other check in this file keys off COMMIT, which is
    immutable -- meaning if GSA-TTS retagged v1.2.0 onto different bytes, this probe would stay
    green forever while "the v1.2 crosswalk" silently meant something else. The register's
    probe_dims are "the v1.2 crosswalk CSV at a pinned commit"; without this test only the
    "pinned commit" half is asserted and the "v1.2" half is taken on faith.
    """
    refs = fetch_tag_refs()
    got = refs.get(f"refs/tags/{TAG}")
    assert got == COMMIT, (
        f"upstream tag {TAG} no longer resolves to the pinned commit.\n"
        f"  expected {COMMIT}\n  got      {got}\n"
        "Everything else in this probe still passes because it keys off the immutable commit. "
        "Re-derive the obligation against the new v1.2 before trusting G007."
    )
    assert f"refs/tags/{TAG}^{{}}" not in refs, (
        f"{TAG} is now an ANNOTATED tag; it was lightweight when pinned. The tag object was "
        "replaced, so confirm the commit it peels to before trusting the pin."
    )


def test_entity_property_pairs_are_unique():
    """2. G007. (entity, property) == (table, column) is unique. Zero duplicates."""
    rows, _ = load_rows()
    counts = collections.Counter((r["table"], r["column"]) for r in rows)
    dups = {k: v for k, v in counts.items() if v > 1}

    detail = ""
    if dups:
        lines = []
        for (t, c), n in sorted(dups.items()):
            lines.append(f"  ({t}, {c}) x{n}")
            for r in rows:
                if (r["table"], r["column"]) == (t, c):
                    lines.append(f"      {r!r}")
        detail = "\n" + "\n".join(lines)

    assert not dups, (
        f"G007 REFUTED: {len(dups)} duplicated (entity, property) pair(s), "
        f"{sum(v - 1 for v in dups.values())} excess row(s).{detail}"
    )
    assert len(counts) == len(rows) == EXPECTED_ROW_COUNT


def test_distinct_entity_count_is_the_size_of_the_ontology_obligation():
    """3. n.ontology owes an object type OR a recorded reason for each of these."""
    rows, _ = load_rows()
    entities = sorted({r["table"] for r in rows})
    assert entities == EXPECTED_ENTITIES, (
        f"PIC v1.2 entity set changed.\n  expected {EXPECTED_ENTITIES}\n  got      {entities}"
    )
    assert len(entities) == EXPECTED_ENTITY_COUNT


def test_provenance_properties_are_present_on_every_entity():
    """4. n.ontology carries these onto every mapped type; confirm PIC defines them so."""
    rows, _ = load_rows()
    entities = {r["table"] for r in rows}
    missing = {}
    for prop in PROVENANCE_PROPERTIES:
        have = {r["table"] for r in rows if r["column"] == prop}
        if have != entities:
            missing[prop] = sorted(entities - have)
    assert not missing, (
        "README claims the v1.2 provenance properties were 'added to all tables', but the "
        f"crosswalk disagrees: {missing}"
    )


def test_universal_columns_are_exactly_provenance_plus_three_structural():
    """Guard: 'present on every entity' is a strictly larger set than 'provenance'."""
    rows, _ = load_rows()
    entities = {r["table"] for r in rows}
    by_col = collections.defaultdict(set)
    for r in rows:
        by_col[r["column"]].add(r["table"])
    universal = sorted(c for c, ts in by_col.items() if ts == entities)
    expected = sorted(PROVENANCE_PROPERTIES + EXPECTED_UNIVERSAL_NON_PROVENANCE)
    assert universal == expected, (
        f"universal-column set changed.\n  expected {expected}\n  got      {universal}\n"
        "Do not infer provenance from universality -- id/created_at/other are also universal."
    )


def test_pic_entity_counterpart_count_is_not_yet_computable():
    """The register's second question, answered honestly rather than plausibly.

    The register asks: "how many PIC entities have no counterpart in this build's shape."
    That subtraction needs BOTH operands. The PIC operand is established above: 13 entities.
    The build operand does not exist at Phase -1.

    n.ontology's guarantee names its output as "Foundry object types, link types and action
    types" but nowhere enumerates them, and no object-type inventory exists anywhere under
    build/ or in the repo. Per tie-break rule 3 (never supply a value the source does not
    state) and rule 4 (refuse and name what is missing, over asserting), this probe does NOT
    guess a mapping from PIC entity names to build concepts. Prose in the node contracts
    contains the English words "document", "project", "comment" and "engagement", but those
    are prose, not declared types, and matching on them would be an inferred counterpart --
    exactly what tie-break rule 7 forbids.

    UNBLOCKS WHEN: n.ontology emits its object-type inventory. At that point replace this
    skip with a set difference against EXPECTED_ENTITIES and assert that every unmapped PIC
    entity carries a recorded reason, which is the literal text of n.ontology's guarantee.
    """
    try:
        import pytest
    except ImportError:
        print(
            "PENDING: PIC-entity-to-object-type counterpart count is not computable at "
            "this build. Missing operand: this build's object-type inventory."
        )
        return
    pytest.skip(
        "Not computable at Phase -1. The PIC operand is known (13 entities, asserted "
        "above); the build operand -- an enumerated object-type inventory for n.ontology "
        "-- does not exist yet in this repo. Refusing to infer counterparts from prose."
    )


# ------------------------------------------------------------------- __main__

def main():
    print(f"PIC crosswalk probe -- {REPO} @ {TAG} ({COMMIT[:12]})")
    print(f"  path {CSV_PATH}")
    print(f"  url  {RAW_URL}")

    checks = [
        test_artifact_exists_at_pinned_commit_with_expected_shape,
        test_tag_v1_2_0_still_resolves_to_the_pinned_commit,
        test_entity_property_pairs_are_unique,
        test_distinct_entity_count_is_the_size_of_the_ontology_obligation,
        test_provenance_properties_are_present_on_every_entity,
        test_universal_columns_are_exactly_provenance_plus_three_structural,
    ]
    failures = 0
    for fn in checks:
        try:
            fn()
            print(f"  PASS {fn.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL {fn.__name__}\n{exc}")

    rows, _ = load_rows()
    entities = sorted({r["table"] for r in rows})
    print(f"\n  rows={len(rows)}  distinct (entity, property) pairs="
          f"{len({(r['table'], r['column']) for r in rows})}  duplicates=0")
    print(f"  distinct PIC v1.2 entities = {len(entities)}")
    for e in entities:
        print(f"    {e:<26} properties={sum(1 for r in rows if r['table'] == e)}")
    print(f"  provenance properties = {len(PROVENANCE_PROPERTIES)}: "
          f"{', '.join(PROVENANCE_PROPERTIES)}")

    print("\n  PENDING (not a pass): counterpart count needs this build's object-type "
          "inventory, which does not exist at Phase -1. See "
          "test_pic_entity_counterpart_count_is_not_yet_computable.")

    if failures:
        print(f"\n{failures} check(s) FAILED")
        return 1
    print("\nAll executable checks passed. G007: (entity, property) is UNIQUE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
