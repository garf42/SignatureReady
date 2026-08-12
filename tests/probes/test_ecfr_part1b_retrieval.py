"""Phase -1 prefab probe: ecfr.gov, 7 CFR Part 1b retrieval.

prefab:     ecfr.gov
used_by:    n.rule_corpus
probe_dims: all of 7 CFR Part 1b, SS 1b.1 to 1b.12, retrieved twice in separate processes
gaps:       G001 -- paragraph citation uniqueness, assumed not verified
            G004 -- whether a structured API exists. Assumed: bulk download and parse
            G033 -- CLOSED; the date constraint observed at closure is asserted here

WHAT THIS PROBE ESTABLISHES, by running code against the real artifact:

  1. A structured API exists -- versioner v1 -- and returns all twelve sections.
     G004's assumption of "bulk download and parse" is wrong in the retrieval half.

  2. It is structured at SECTION granularity and NOT at paragraph granularity.
     This CORRECTS the note carried in PHASE-MINUS-1.md, which recorded G004 as answered
     "at paragraph granularity". It is not. <DIV8 TYPE="SECTION"> is machine-readable;
     the paragraph designators (a), (g)(2)(iv) are INLINE TEXT inside <P> with no
     attributes anywhere in the part. n.rule_corpus keys on (authority_id, citation) at
     paragraph grain, so that key must be DERIVED by a stateful walk, and this probe
     measures what the walk is up against rather than asserting it is easy.

  3. MR-1 (re-execution): two retrievals of the same effective version, in genuinely
     separate OS processes, are byte-identical.

  4. The G033 date constraint: a `date` past the title's most recent issue date is a 404,
     not an empty document and not a silent fallback to the latest issue.

  5. THREE PARSING HAZARDS, each demonstrated against the real bytes rather than argued:

     (a) One <P> is NOT one paragraph. In 1b.5, `(b) Scope of analysis. (1) In preparing`
         is a SINGLE <P> carrying two designators. A reader that emits one row per <P>
         silently merges 1b.5(b) with 1b.5(b)(1), and the merged row still satisfies every
         "every row carries..." guarantee n.rule_corpus states.

     (b) A length-capped citation regex silently drops the DEEPEST entries. 1b.4 -- the
         categorical-exclusion catalogue, the section n.ce_catalog reads -- carries
         designators up to (xxxix). A regex of (\\w{1,4}) matches (xvii) and misses
         (xviii), so the CE list truncates with no error anywhere.

     (c) SEVEN single characters -- c d i l m v x -- are simultaneously a lowercase
         paragraph letter and a roman numeral. This is LIVE in Part 1b, not latent:
         1b.2(c) and 1b.2(d) are top-level letters, and a walk that assigns depth from a
         token's type nests them under 1b.2(b)(2) and produces 84 colliding citations.

  6. THE RESULT: G001 is NOT ANSWERABLE from this source. Uniqueness is a property of a
     derivation, not of the document, and all three available derivations fail -- type-first
     collides, leading-tokens-only strands 30 designators by cascade, and consuming inline
     designators swallows prose cross-references like "See paragraph (e) of this section".
     The prefab therefore does not behave as the register expected: verdict FAIL.

NETWORK: this probe fetches over HTTPS from www.ecfr.gov. If the host is unreachable it
RAISES -- it never skips into a green run, because a silent pass here would launder G004
and G001 back into "assumed".

RUN:
    python3 tests/probes/test_ecfr_part1b_retrieval.py
"""

import collections
import hashlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

# ---------------------------------------------------------------- pinned facts

HOST = "https://www.ecfr.gov"
TITLE = 7
PART = "1b"
SUBTITLE = "A"

# Observed 2026-08-12. latest_issue_date is a MOVING target: it advances whenever the title
# is reissued. The probe reads it from the API rather than pinning it, and pins only the
# bytes that a fixed issue date must produce.
PINNED_ISSUE_DATE = "2026-08-10"
EXPECTED_SHA256 = "a8097af3cf7df54af4fc22c3b90b898dace6e180618583278093315afea6db20"
EXPECTED_BYTES = 222131

EXPECTED_SECTIONS = ["1b.%d" % n for n in range(1, 13)]  # 1b.1 .. 1b.12
EXPECTED_P_COUNT = 939

# A date the title cannot have been reissued on, used to assert the G033 constraint.
FUTURE_DATE = "2099-01-01"

UA = {"User-Agent": "SignatureReady-probe/1 (phase -1; contact via repo)"}

# Deliberately GREEDY: matches (a), (12), (xxxix). The 1..4 cap that hazard (b) is about is
# introduced only inside the demonstration below, never used for real parsing.
DESIGNATOR = re.compile(r"\(([0-9a-zA-Z]+)\)")
LEADING_GREEDY = re.compile(r"^\s*\(([0-9a-zA-Z]+)\)")
LEADING_CAPPED = re.compile(r"^\s*\(([0-9a-zA-Z]{1,4})\)")
ROMAN_ONLY = re.compile(r"^[ivxlcdm]+$")


# ---------------------------------------------------------------- retrieval

def full_xml_url(date):
    return "%s/api/versioner/v1/full/%s/title-%d.xml?subtitle=%s&part=%s" % (
        HOST, date, TITLE, SUBTITLE, PART)


def fetch(url, timeout=120):
    """Fetch or raise. Never returns a sentinel -- a probe that degrades to a skip on a
    network error reports green for a question it did not ask."""
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


_CACHE = {}


def part_1b_bytes(date=PINNED_ISSUE_DATE):
    if date not in _CACHE:
        status, body = fetch(full_xml_url(date))
        assert status == 200, "expected 200 for %s, got %s" % (date, status)
        _CACHE[date] = body
    return _CACHE[date]


def latest_issue_date():
    import json
    status, body = fetch("%s/api/versioner/v1/titles.json" % HOST)
    assert status == 200
    titles = json.loads(body)["titles"]
    t = [x for x in titles if x["number"] == TITLE][0]
    return t["latest_issue_date"], t["latest_amended_on"]


def sections(xml):
    """(section_number, body) for every <DIV8 TYPE="SECTION">, in document order."""
    return re.findall(r'<DIV8[^>]*N="([^"]+)"[^>]*TYPE="SECTION"[^>]*>(.*?)</DIV8>', xml, re.S)


def paragraphs(body):
    """Raw inner text of each <P>, tags stripped, in document order."""
    return [re.sub(r"<[^>]+>", "", p).strip() for p in re.findall(r"<P>(.*?)</P>", body, re.S)]


# ---------------------------------------------------------------- 1. a structured API exists

def test_a_structured_api_exists_and_returns_the_whole_part():
    """G004: assumed 'bulk download and parse'. A versioner API exists and returns Part 1b
    alone, so the bulk half of that assumption is unnecessary."""
    body = part_1b_bytes()
    assert len(body) == EXPECTED_BYTES, (
        "Part 1b at %s is %d bytes, pinned at %d. The part was reissued or the API changed; "
        "re-pin deliberately rather than widening this assert."
        % (PINNED_ISSUE_DATE, len(body), EXPECTED_BYTES))
    got = hashlib.sha256(body).hexdigest()
    assert got == EXPECTED_SHA256, "sha256 %s != pinned %s" % (got, EXPECTED_SHA256)

    xml = body.decode("utf-8")
    found = [n for n, _ in sections(xml)]
    assert found == EXPECTED_SECTIONS, (
        "expected SS 1b.1 to 1b.12 in order, got %r" % (found,))


def test_the_api_is_section_grained_not_paragraph_grained():
    """The correction. Paragraph citations are inline text, not markup. If <P> ever gains an
    attribute carrying a citation, this assert fails and the finding is revisited -- which is
    the point of asserting a negative."""
    xml = part_1b_bytes().decode("utf-8")

    attributed = re.findall(r"<P\s+[^>]*>", xml)
    assert not attributed, (
        "<P> now carries attributes (%d of them, e.g. %r) -- paragraph-level metadata may "
        "exist after all, and the derived-citation walk should be reconsidered."
        % (len(attributed), attributed[:2]))

    # The only machine-readable citation in the document is section-level.
    meta = re.findall(r"citation&quot;:&quot;([^&]+)&quot;", xml)
    assert meta, "hierarchy_metadata citations disappeared from the payload"
    deepest = max(meta, key=len)
    assert not re.search(r"\([0-9a-z]+\)", deepest), (
        "a hierarchy_metadata citation now names a paragraph (%r) -- the API may have gained "
        "paragraph granularity" % deepest)

    tags = collections.Counter(re.findall(r"<([A-Z][A-Z0-9]*)[\s>]", xml))
    assert tags["P"] == EXPECTED_P_COUNT, (
        "<P> count is %d, pinned at %d" % (tags["P"], EXPECTED_P_COUNT))


# ---------------------------------------------------------------- 2. MR-1, separate processes

def test_mr1_two_retrievals_in_separate_processes_are_byte_identical():
    """n.rule_corpus MR-1. Two fetches inside one process share a connection pool, a DNS
    cache and any library-level memoisation, so they are not the relation the node states.
    This spawns a real second interpreter."""
    local = hashlib.sha256(part_1b_bytes()).hexdigest()

    out = subprocess.run(
        [sys.executable, __file__, "--emit-sha"],
        capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, (
        "child process failed (rc=%s)\nstdout: %s\nstderr: %s"
        % (out.returncode, out.stdout[-800:], out.stderr[-800:]))
    child = out.stdout.strip().splitlines()[-1]

    assert child == local == EXPECTED_SHA256, (
        "MR-1 violated: parent %s, child %s, pinned %s" % (local, child, EXPECTED_SHA256))


# ---------------------------------------------------------------- 3. the G033 date constraint

def test_a_date_past_the_latest_issue_is_a_404_not_a_silent_fallback():
    """G033 recorded this at closure. It matters because the failure mode of a retrieval
    pinned to 'today' is a hard 404 on any day the title was not reissued -- loud, which is
    the good case. The bad case this rules out is a silent fallback to the latest issue,
    which would stamp today's date on older text."""
    try:
        status, body = fetch(full_xml_url(FUTURE_DATE))
    except urllib.error.HTTPError as e:
        assert e.code == 404, "expected 404 for a future date, got %s" % e.code
        msg = e.read().decode("utf-8", "replace")
        assert "most recent issue date" in msg, (
            "the 404 no longer names the most recent issue date; a retriever cannot "
            "self-correct from this error any more. Body: %s" % msg[:300])
        return
    raise AssertionError(
        "a date of %s returned %s with %d bytes instead of 404 -- the API may now silently "
        "fall back to the latest issue, which would stamp a requested date onto text that "
        "is not from it" % (FUTURE_DATE, status, len(body)))


def test_the_pinned_issue_date_is_not_in_the_future_of_the_live_title():
    """Keeps the pin honest: if eCFR ever rolls back, the pinned date becomes unfetchable and
    every other test here fails confusingly. Fail clearly instead."""
    latest, amended = latest_issue_date()
    assert PINNED_ISSUE_DATE <= latest, (
        "pinned issue date %s is past the live latest_issue_date %s" % (PINNED_ISSUE_DATE, latest))
    if PINNED_ISSUE_DATE != latest:
        print("      note: title 7 has advanced to %s (amended %s); this probe still pins %s"
              % (latest, amended, PINNED_ISSUE_DATE))


# ---------------------------------------------------------------- 4. hazard (a)

def test_hazard_one_P_element_can_carry_two_designators():
    """A reader emitting one row per <P> merges a parent paragraph with its first child."""
    xml = part_1b_bytes().decode("utf-8")
    by_sec = dict(sections(xml))

    multi = []
    for sec, body in sections(xml):
        for text in paragraphs(body):
            m = LEADING_GREEDY.match(text)
            if not m:
                continue
            rest = text[m.end():]
            # a second designator appearing at a sentence boundary inside the same <P>
            if re.search(r"(?:^|\.\s|\s)\((?:[0-9]+|[ivxlcdm]+|[a-z])\)\s+[A-Z]", rest):
                multi.append((sec, text[:90]))

    assert multi, (
        "no <P> carries a second designator any more. The hazard may be gone -- verify "
        "against 1b.5(b) before deleting this test.")

    secs = sorted({s for s, _ in multi})
    assert "1b.5" in secs, (
        "1b.5 was the witness for this hazard and no longer shows it; witnesses now: %r" % secs)

    # the specific witness, asserted so a reshuffle is visible rather than silently tolerated
    b_paras = [t for t in paragraphs(by_sec["1b.5"]) if t.startswith("(b)")]
    assert b_paras, "1b.5(b) not found"
    assert re.match(r"^\(b\)\s*Scope of analysis\.\s*\(1\)", b_paras[0]), (
        "1b.5(b)'s text no longer opens with an inline (1); got %r" % b_paras[0][:120])

    print("      %d <P> elements carry a second designator, across sections %s"
          % (len(multi), ", ".join(secs)))


# ---------------------------------------------------------------- 5. hazard (b)

def test_hazard_a_length_capped_citation_regex_truncates_the_CE_catalogue():
    """1b.4 is the categorical-exclusion catalogue. This is the demon installed and watched
    to go red: the capped regex is the defect, and the assert below is what catches it."""
    xml = part_1b_bytes().decode("utf-8")
    body = dict(sections(xml))["1b.4"]
    texts = paragraphs(body)

    greedy = [m.group(1) for m in (LEADING_GREEDY.match(t) for t in texts) if m]
    capped = [m.group(1) for m in (LEADING_CAPPED.match(t) for t in texts) if m]

    dropped = len(greedy) - len(capped)
    assert dropped > 0, (
        "the capped regex no longer drops anything in 1b.4 -- either the section shrank or "
        "the deepest designators went away. Re-derive before relaxing this.")

    long_ones = sorted({d for d in greedy if len(d) > 4})
    assert long_ones, "1b.4 no longer carries designators longer than four characters"
    assert "xviii" in long_ones, (
        "(xviii) was the first casualty of the cap and is gone; longest now: %r" % long_ones)

    print("      1b.4: %d designators greedily, %d with a 4-char cap -- %d CE entries "
          "silently dropped, e.g. %s"
          % (len(greedy), len(capped), dropped, ", ".join("(%s)" % d for d in long_ones[:6])))


# ---------------------------------------------------------------- 6. hazard (c)

def test_hazard_seven_single_letters_are_also_roman_numerals_and_it_fires_here():
    """The collision is not just (i). Every one of c d i l m v x is simultaneously a valid
    lowercase paragraph letter and a valid roman numeral, so a walk that decides depth from
    a token's TYPE cannot place them. In Part 1b this is live, not latent: 1b.2(c) and
    1b.2(d) are top-level letters that a roman-first reader nests under 1b.2(b)(2)."""
    xml = part_1b_bytes().decode("utf-8")

    ambiguous_tokens = set()
    for sec, body in sections(xml):
        for text in paragraphs(body):
            m = LEADING_GREEDY.match(text)
            if m and len(m.group(1)) == 1 and ROMAN_ONLY.match(m.group(1)):
                ambiguous_tokens.add(m.group(1))

    assert ambiguous_tokens, (
        "no single-character token in Part 1b is roman-ambiguous any more -- verify against "
        "1b.2(c) before deleting this test")
    assert {"c", "d"} <= ambiguous_tokens, (
        "1b.2(c) and 1b.2(d) were the witnesses for this hazard; ambiguous tokens now: %r"
        % sorted(ambiguous_tokens))

    # The demon, installed and watched to go red: type-first depth assignment.
    type_first_keys = []
    for sec, body in sections(xml):
        stack = []
        for text in paragraphs(body):
            m = LEADING_GREEDY.match(text)
            if not m:
                continue
            tok = m.group(1)
            depth = 1 if tok.isdigit() else 2 if ROMAN_ONLY.match(tok) else 3 if tok.isupper() else 0
            stack = stack[:depth] + [tok]
            type_first_keys.append("%s%s" % (sec, "".join("(%s)" % t for t in stack)))

    collisions = [k for k, n in collections.Counter(type_first_keys).items() if n > 1]
    assert collisions, (
        "the type-first walk no longer collides. Either the part changed or the demon is no "
        "longer installed; a green here means this test has stopped testing anything.")

    print("      ambiguous single-char tokens present: %s"
          % ", ".join("(%s)" % t for t in sorted(ambiguous_tokens)))
    print("      type-first depth assignment produces %d colliding citations, e.g. %s"
          % (len(collisions), ", ".join(sorted(collisions)[:4])))


# ---------------------------------------------------------------- 7. G001

ROMAN_VALUE = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
OPENS = {"1": "digit", "a": "letter", "i": "roman", "A": "upper"}


def roman_to_int(s):
    total, prev = 0, 0
    for ch in reversed(s):
        v = ROMAN_VALUE.get(ch)
        if v is None:
            return None
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


def is_successor(kind, prev, tok):
    """Is `tok` the next label after `prev` within a level of the given kind?"""
    if kind == "digit":
        return tok.isdigit() and prev.isdigit() and int(tok) == int(prev) + 1
    if kind == "upper":
        return len(tok) == len(prev) == 1 and tok.isupper() and ord(tok) == ord(prev) + 1
    if kind == "letter":
        return len(tok) == len(prev) == 1 and tok.islower() and ord(tok) == ord(prev) + 1
    if kind == "roman":
        a, b = roman_to_int(prev), roman_to_int(tok)
        return a is not None and b is not None and b == a + 1
    return False


def walk_citations(sec, texts):
    """Derive a paragraph citation for each designated <P>, using SEQUENCE rather than token
    type. A token continues the innermost level it is the successor of; failing that it opens
    a new level, and only 1/a/i/A may open one. This is the walk n.rule_corpus needs, and the
    reason its (authority_id, citation) key is derived rather than read."""
    stack = []          # list of [kind, token]
    keys, anomalies = [], []
    for text in texts:
        m = LEADING_GREEDY.match(text)
        if not m:
            continue
        tok = m.group(1)
        matched = None
        for idx in range(len(stack) - 1, -1, -1):
            if is_successor(stack[idx][0], stack[idx][1], tok):
                matched = idx
                break
        if matched is not None:
            stack = stack[:matched] + [[stack[matched][0], tok]]
        else:
            kind = OPENS.get(tok)
            if kind is None:
                anomalies.append((sec, tok, text[:70]))
                continue
            stack = stack + [[kind, tok]]
        keys.append("%s%s" % (sec, "".join("(%s)" % t for _, t in stack)))
    return keys, anomalies


CROSSREF = re.compile(
    r"(?:paragraph|paragraphs|section|sections|subpart|part|U\.S\.C\.|CFR)\s*"
    r"[^.;]{0,40}?\(([0-9a-zA-Z]+)\)")


def test_g001_is_not_verifiable_against_this_source_and_stays_open():
    """THE RESULT OF THIS PROBE, and it is a fail in the register's sense: the prefab does
    not behave as the register expected.

    G001 assumed (authority, citation) uniqueness. Uniqueness of WHAT is the problem -- the
    citation is not in the source, so it has to be derived, and none of the three available
    derivations is both complete and unambiguous:

      type-first depth   -> collides, because c d i l m v x are letters and numerals both
      leading tokens only -> incomplete, because a parent's opener can sit inline in a
                             previous <P> and the miss then CASCADES down its whole level
      consume inline too  -> unsound, because prose cross-references are shaped exactly like
                             designators: 1b.7 says "See paragraph (e) of this section"

    So G001 is not "unverified pending effort". It is not answerable from this source alone,
    and n.rule_corpus's key needs either a different source of paragraph structure or an
    explicit, tested derivation carried as part of the node. Each leg is measured below so
    the conclusion rests on counts rather than on this docstring."""
    xml = part_1b_bytes().decode("utf-8")

    # leg 1 -- type-first collides
    type_first = []
    for sec, body in sections(xml):
        stack = []
        for text in paragraphs(body):
            m = LEADING_GREEDY.match(text)
            if not m:
                continue
            tok = m.group(1)
            depth = 1 if tok.isdigit() else 2 if ROMAN_ONLY.match(tok) else 3 if tok.isupper() else 0
            stack = stack[:depth] + [tok]
            type_first.append("%s%s" % (sec, "".join("(%s)" % t for t in stack)))
    collisions = {k for k, n in collections.Counter(type_first).items() if n > 1}

    # leg 2 -- leading-token-only is incomplete
    keys, anomalies = [], []
    for sec, body in sections(xml):
        k, a = walk_citations(sec, paragraphs(body))
        keys += k
        anomalies += a

    # leg 3 -- inline consumption would swallow cross-references
    crossrefs = []
    for sec, body in sections(xml):
        for text in paragraphs(body):
            for tok in CROSSREF.findall(text):
                crossrefs.append((sec, tok, text[:60]))

    assert collisions, "the type-first walk no longer collides; re-derive leg 1"
    assert anomalies, "the leading-token walk no longer strands designators; re-derive leg 2"
    assert crossrefs, "no prose cross-references found; re-derive leg 3"

    # What IS true, and worth carrying: the placeable subset is internally consistent.
    dupes = [k for k, n in collections.Counter(keys).items() if n > 1]
    assert not dupes, (
        "the placeable subset is not even internally unique (%d duplicates, e.g. %r) -- "
        "the derivation is worse than this probe reports" % (len(dupes), dupes[:6]))

    placed, stranded = len(keys), len(anomalies)
    print("      leg 1  type-first depth:      %d colliding citations" % len(collisions))
    print("      leg 2  leading tokens only:   %d placed, %d stranded (%.1f%% lost)"
          % (placed, stranded, 100.0 * stranded / (placed + stranded)))
    print("      leg 3  inline consumption:    %d prose cross-references shaped like "
          "designators, e.g. %r" % (len(crossrefs), crossrefs[0][2]))
    print("      the placeable subset IS unique, so the derivation is incomplete rather "
          "than inconsistent")
    print("      G001: NOT ANSWERABLE from ecfr.gov alone. Stays open, reason now precise.")


# ---------------------------------------------------------------- runner

def main():
    if "--emit-sha" in sys.argv:
        print(hashlib.sha256(part_1b_bytes()).hexdigest())
        return 0

    print("Phase -1 probe: ecfr.gov / 7 CFR Part 1b")
    print("  %s\n" % full_xml_url(PINNED_ISSUE_DATE))

    checks = [
        test_a_structured_api_exists_and_returns_the_whole_part,
        test_the_api_is_section_grained_not_paragraph_grained,
        test_mr1_two_retrievals_in_separate_processes_are_byte_identical,
        test_a_date_past_the_latest_issue_is_a_404_not_a_silent_fallback,
        test_the_pinned_issue_date_is_not_in_the_future_of_the_live_title,
        test_hazard_one_P_element_can_carry_two_designators,
        test_hazard_a_length_capped_citation_regex_truncates_the_CE_catalogue,
        test_hazard_seven_single_letters_are_also_roman_numerals_and_it_fires_here,
        test_g001_is_not_verifiable_against_this_source_and_stays_open,
    ]
    failures = 0
    for fn in checks:
        try:
            fn()
            print("  PASS %s" % fn.__name__)
        except AssertionError as exc:
            failures += 1
            print("  FAIL %s\n       %s" % (fn.__name__, exc))

    xml = part_1b_bytes().decode("utf-8")
    print("\n  bytes=%d  sha256=%s" % (len(part_1b_bytes()), EXPECTED_SHA256))
    print("  sections=%d  <P>=%d" % (len(sections(xml)), EXPECTED_P_COUNT))

    if failures:
        print("\n%d check(s) FAILED" % failures)
        return 1
    print("\nAll checks passed.")
    print("G004: ANSWERED -- a structured API exists, at SECTION granularity only,")
    print("      which is weaker than the note carried in PHASE-MINUS-1.md.")
    print("G001: NOT ANSWERABLE from ecfr.gov alone -- stays open with a precise reason.")
    print("VERDICT: fail -- the probe ran and the prefab does not behave as expected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
