# Constitution — SignatureReady (parallel build)
<!-- cap: 200 -->

## Intent predicate
[BINDING] origin: specified
For every environmental document the system emits, the emission writes an `EmissionManifest`,
and all five clauses hold against that manifest alone:
1. **Element closure** — `required(document_type)` = `satisfied` ⊎ `pending` ⊎ `not_applicable`,
   pairwise disjoint and jointly exhaustive; every `satisfied` entry names the canonical path it
   resolved and the input affordance that wrote it; every `pending` entry names its citation.
2. **Slot disposition** — every slot in the slot register carries a disposition frozen in that
   register: `drafted`, `record_supplied`, or `expert_required`. Every `drafted` slot carries a
   model-drafted claim. Every `record_supplied` slot names the proposal-record item or
   prior-coverage candidate supplying it, or carries an emitted "none found" with the query that
   found nothing. Every `expert_required` slot names the qualification, the lead time, and either
   an open assignment or a received artifact. No slot id is empty, and no disposition is chosen
   at invocation time.
3. **Claim grounding** — every model-drafted claim declares `grounding_kind` ∈ {source, state},
   and carries a verifier verdict of `pass` stamped at or after `emitted_at`. No other verdict
   value may appear in an emitted document.
4. **Determination provenance** — each of the five determinations at 7 CFR 1b.11(a)(46) present in
   the document resolves to a recorded human act carrying an actor principal distinct from any
   service principal, a timestamp, and a hash of the computed evidence displayed at that moment.
5. **Freshness** — for every computed value in the document, `recomputed_at` ≥ the latest
   `changed_at` over the inputs its canonical paths name.
- non-vacuity: **the in-scope document_type set is all five** — FANEC, EA, FONSI, EIS, ROD — and
  the acceptance corpus contains ≥1 emitted document of each. Per document type: ≥1 `satisfied`
  and ≥1 `pending` element; ≥1 slot of every disposition the register declares for that type, and
  the disposition mix equals its pinned expectation; ≥1 claim of each `grounding_kind`. Across the
  corpus: ≥1 recorded determination; ≥1 received expert artifact and ≥1 open assignment; ≥1 holder
  selected from the directory carrying an attestation, and ≥1 engagement outcome written back; ≥1
  document emitted after an input change that invalidated a displayed value. `|required(t)|` is
  non-zero and equals the frozen count for t — FANEC 6 (1b.3(g)(2)), EA 7 (1b.5(c)),
  FONSI 5 (1b.6(b)), EIS 8 (1b.7(h)), ROD 8 (1b.8(b)). Frozen counts are transcription-derived
  and unverified against eCFR — G013.

## Source contracts

### src.ecfr_1b
- grain: one row per numbered paragraph of 7 CFR Part 1b, §§ 1b.1–1b.12, verbatim text
- keys: paragraph citation, e.g. `1b.3(g)(2)(iv)`; uniqueness assumed, unverified — G001
- cardinality: many-to-many to required elements — one paragraph may carry several elements and
  one element may span several paragraphs
- cadence: versioned instrument; 91 FR 17092 (2026-04-03) as amended by 91 FR 40353 (2026-07-02);
  re-check cadence undecided — G002
- late/null: none. Supersession is a new version, never an edit to an existing row
- units/tz: none. Effective dates are US federal dates; timezone not declared — G003
- unknowns: G001, G002, G003, G004. **ecfr.gov only** — Cornell/LII serves superseded Part 1b text

### src.uscode
- grain: one row per statutory subsection of 42 U.S.C. 4336–4336e, 16 U.S.C. 2113a, 16 U.S.C. 1604(i)
- keys: citation; unique
- cardinality: one-to-one to the deadline and authority values that cite it
- cadence: snapshot with a "text in effect on" date
- late/null: none
- units/tz: deadlines expressed in years; calendar basis for the +1yr / +2yr arithmetic not declared — G005
- unknowns: G005

### src.federalregister
- grain: one row per Federal Register document
- keys: FR document number; unique
- cardinality: many FR documents per authority version; one preamble per final rule
- cadence: documented public API; daily publication
- late/null: none
- units/tz: publication dates, US Eastern
- unknowns: rate limit and page size behaviour at this build's volume — G006

### src.pic_standard
- grain: one row per entity/property pair in the PIC v1.2 crosswalk CSV
- keys: (entity, property); uniqueness unverified — G007
- cardinality: many PIC properties to one Foundry object type; some PIC entities have no counterpart
- cadence: versioned GitHub repository, pinned by commit
- late/null: none
- units/tz: none
- unknowns: G007

### src.ce_explorer
- grain: one row per federal categorical exclusion, JSON
- keys: (agency, category identifier); uniqueness unverified — G008
- cardinality: many-to-one against a 1b.4 category; may disagree with rule text
- cadence: snapshot download
- late/null: none
- units/tz: acreage and mileage units as published; declaration unverified — G008
- unknowns: G008. **Non-authoritative by its own documentation** — reconciliation input only,
  never a citation target

### src.fsgeodata
- grain: one geographic feature per row, per layer
- keys: layer-assigned feature id; uniqueness unverified — G009
- cardinality: one treatment unit overlaps 0..n designated areas; treatment-to-unit is many-to-many
- cadence: periodic republication; some layers carry under-review notices and have been withdrawn
- late/null: layer availability may change between retrievals; retrieval date recorded per layer
- units/tz: projection and linear unit vary per layer and must be read, never assumed — G010
- unknowns: G009, G010

### src.nepatec
- grain: unverified — one row per document, or per chunk — G011
- keys: CEQ-standard metadata identifier
- cardinality: ~120,000 documents across ~60,000 projects, 60+ agencies
- cadence: static release
- late/null: none
- units/tz: none
- unknowns: G011; selectivity of a USDA/USFS filter unmeasured — G012

### src.synthetic
- grain: one row per generated project, treatment unit, activity group, or screen
- keys: generator-assigned; unique by construction
- cardinality: set by seed; must include ≥1 unit carrying two overlapping treatments and
  ≥1 project whose extraordinary-circumstance screen is entirely clear
- cadence: on demand; seeded and reproducible
- late/null: none
- units/tz: acres and statute miles, declared
- unknowns: none. Every row carries `synthetic = true` and is visually distinguishable

## Tie-break order
[BINDING] origin: specified
Walk in order. First rule that discriminates wins. No ties.
1. Regulatory accuracy wins — a citation, element set, cap, deadline or enumerated member the
   primary source does not support is wrong regardless of what it costs to fix
2. The intent predicate wins over everything below it
3. Never supply a regulatory value the source does not state — a missing value opens a gap
4. Refuse and name what is missing, over asserting — a blocked state that says why beats a
   silent one, and beats a plausible one
5. Prefer the reversible option
6. Never silently change grain, and never collapse a many-to-many
7. Explicit over inferred — a declared kind, a named path, a parsed strictness beats a derived one
8. Reuse an existing contract over minting a new one; then fewest moving parts

## Escalation rule
[BINDING] origin: specified
If the tie-break order does not resolve a decision, do not ask the human.
Take the most reversible option, append a gap, and continue.
7 CFR 1b.11(a)(46) reserves five determinations inside the **deployed product**. It reserves
nothing about what gets built. No regulation governs a build decision, so no build decision
escalates on regulatory grounds.

## Operating loop
[BINDING] origin: specified
1. Receive packet — constitution + own node + neighbour interfaces + own seams, prefabs, gaps
2. Predict the concrete fixture output and commit it — flagged nodes only
3. Implement in a context that cannot read the prediction
4. Diff prediction against output
5. Surprise → walk the tie-break order → unresolved becomes a gap plus the reversible branch
6. Write back as a tightened clause; a clause with no kill test is a comment
7. Negative-check: install the demon, watch the kill test go red, record the evidence
8. Land the output as a Foundry resource on the phase branch and read it back by RID, then drive
   outbound seams. The node is not done until both have run — a node with no resource is not built
9. Report only the surprise upward
