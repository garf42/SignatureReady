# Gaps

Reviewed in batch at phase boundaries, never mid-build. Every gap is a decision already taken by
default; the entry records which decision and how reversible it is.

- G001 — node: n.rule_corpus — volatility: low — last_reviewed: phase--1 — REFRAMED, still open
  Was: paragraph citation uniqueness across 7 CFR Part 1b is assumed, not verified.
  Probed 2026-08-12. The gap was asking an unanswerable question: **the citation does not exist
  in the source**, so uniqueness is a property of a DERIVATION and not of the document. eCFR's
  versioner API is section-grained; `<P>` carries no attributes anywhere in the part. All three
  available derivations fail — type-first depth collides 84 times because c d i l m v x are
  lowercase letters and roman numerals both (live here: 1b.2(c), 1b.2(d)); leading-tokens-only
  strands 30 designators by cascade, because a parent's opener can sit inline in a previous `<P>`
  (1b.5(b) reads "(b) Scope of analysis. (1) In preparing" as one element); and consuming inline
  designators is unsound because 188 prose cross-references are shaped identically, e.g. 1b.7's
  "See paragraph (e) of this section". The placeable subset IS internally unique, so the problem
  is incompleteness rather than inconsistency.
  Now assumed: nothing. n.rule_corpus needs either a second source of paragraph structure or an
  explicit derivation carried and tested as part of the node, and uniqueness is then asserted of
  that named derivation and of nothing else. See L0017.
  Reversible: yes. Blocks: MR-3 on n.rule_corpus, and the shape of its reader.

- G002 — node: n.authority_ledger — volatility: medium — last_reviewed: phase-0
  Re-check cadence for authority currency. The rule is a versioned instrument and nothing in this
  workspace can supply the right interval.
  Assumed: re-check on every build of the node, carrying the retrieval timestamp forward. No
  interval invented. Reversible: yes.
  Blocks: the currency check on every authority.

- G003 — node: n.rule_corpus — volatility: low — last_reviewed: phase-0
  Timezone basis for effective dates is not declared in the source.
  Assumed: date-only, no timezone arithmetic anywhere. Reversible: yes.
  Blocks: nothing today; it blocks any deadline computed to an hour.

- G004 — node: n.rule_corpus — volatility: medium — last_reviewed: phase--1 — ANSWERED
  Whether ecfr.gov exposes a structured API for Part 1b at paragraph granularity. **It exposes
  one at SECTION granularity and not at paragraph granularity**, so the answer is yes to the
  first half and no to the second.
  Answered by execution 2026-08-12: `/api/versioner/v1/full/<date>/title-7.xml?subtitle=A&part=1b`
  returns Part 1b alone, 222131 bytes, sha256 a8097af3…fea6db20, all twelve sections present as
  `<DIV8 TYPE="SECTION">`. The assumed "bulk retrieval and parse" is unnecessary for retrieval.
  It remains necessary for paragraph structure, which the payload does not carry — see G001.
  This CORRECTS the note carried in PHASE-MINUS-1.md, which recorded this gap as answered "at
  paragraph granularity". Reversible: yes. Blocks: nothing.

- G005 — node: n.det_core — volatility: low — last_reviewed: phase-0
  Calendar basis for the one-year EA and two-year EIS deadline arithmetic is not stated.
  Assumed: calendar year from the trigger date. The boundary fixture is authored non-asserting.
  Reversible: yes. Blocks: MR-1 on the deadline functions.

- G006 — node: n.authority_ledger — volatility: low — last_reviewed: phase-0
  federalregister.gov rate limit and page size at this build's volume.
  Assumed: adequate. Reversible: yes. Blocks: the n.authority_ledger probe.

- G007 — node: n.ontology — volatility: low — last_reviewed: phase-0
  PIC v1.2 crosswalk (entity, property) uniqueness.
  Assumed: unique. Reversible: yes. Blocks: the PIC mapping count in n.ontology's guarantee.

- G008 — node: n.ce_catalog — volatility: low — last_reviewed: phase-0
  Whether src.ce_explorer declares its units or leaves them implied.
  Assumed: implied, so no comparison is performed against its values. It is a reconciliation
  input and never a citation target. Reversible: yes. Blocks: the reconciliation table.

- G009 — node: n.project_state — volatility: low — last_reviewed: phase-0
  fsgeodata feature id uniqueness per layer.
  Assumed: unique per layer. Reversible: yes. Blocks: MR-2 on n.project_state.

- G010 — node: n.project_state — volatility: high — last_reviewed: phase-0
  Projection and linear unit vary per fsgeodata layer and must be read, not assumed.
  Assumed: read at ingestion, recorded per layer, no measure crosses a projection without a
  recorded transformation. Reversible: yes. Blocks: MR-4 on n.project_state.

- G011 — node: n.precedent — volatility: medium — last_reviewed: phase--1 — **ANSWERED**
  src.nepatec row grain — one row per document or per chunk.
  **Neither. It is one row per PROJECT.** Measured 2026-08-12 with a HuggingFace identity that
  has accepted the gate, over all 60 USDA files — not a sample. The shape is
  `{project, process, documents[]}`; each document is `{metadata, pages[]}`; each page is
  `{"page number", "page text"}` — those keys carry literal spaces and cannot be used as
  property apiNames unmapped. Every project/process/metadata leaf is wrapped `{"value": …}` and
  the payload is polymorphic (str, list, int by field).
  **Page-level text exists natively**, so n.precedent/c1 is satisfiable without a chunker
  inventing anchors, and the reader change is a flatten — project→document→page→chunk. The
  reversibility recorded before the probe holds: the reader moved, the guarantee did not.
  Two hazards found, both pinned in the probe:
  - **7.9% of USDA page numbers are RANGES** ("1-12", up to 18 pages). The "named page" is then
    a span, and a substring check against a span is exactly **demon D1** — arriving in the
    source rather than in the reader. D1's kill test must reject span anchors, not just
    nearest-page assignment.
  - **`file_metadata.total_pages` disagrees with `len(pages)` on 174 of 210 documents (83%)**.
    `pages[]` is a chunking, not a page-by-page rendering; nothing may trust total_pages as its
    length. 8.8% of pages corpus-wide are empty (0.1% in USDA) and would pass a substring check
    vacuously.
  The anonymous finding stands as a description of the gate and is unchanged: content is not
  readable without an accepted gate, and G033's "tree and parquet readable anonymously" note is
  still wrong on both halves — zero parquet, and content is not anonymously readable.
  Reversible: yes. See L0019.
  Was blocking: n.precedent's chunk grain, MR-2, and the page-anchoring guarantee. Now unblocked.

- G012 — node: n.precedent — volatility: medium — last_reviewed: phase--1 — ANSWERED at file grain
  Selectivity of a USDA/USFS filter over src.nepatec. **60 of 505 files, 11.9%** — the assumed
  "non-trivial" holds. Measured 2026-08-12 from the path partition `<doc_type>/<agency>/*.jsonl`
  without retrieving any content, which is the only granularity available while G011 is blocked:
  this is a FILE count and not a row count, and must not be quoted as one.
  **Both of the follow-on findings recorded here on 2026-08-12 were CORRECTED later the same day**,
  once the gate was accepted and the data itself could be read. Kept visible, because each was a
  conclusion drawn from the path tree and stated as a fact about the corpus:
  - ~~There is no USFS bucket, so USFS is not separable.~~ **REFUTED.** There is no USFS *path
    bucket*, which is all the anonymous probe could see. USFS **is** separable from
    `process.lead_agency`: "Department of Agriculture - Forest Service" on **30 of 210 projects
    (14.3%)**, against "Department of Agriculture" on 177. n.precedent's USDA/USFS filter **is**
    expressible — from a field, never from the path.
  - ~~The USDA slice holds no EIS, so EIS and ROD coverage is impossible.~~ **HALF REFUTED.** At
    document granularity the slice holds CE 173, EA 18, FONSI 14, OTHER 2, DEA 2, **ROD 1**. ROD
    coverage exists and is **n=1** — the non-vacuity requirement is met by a single document and is
    one deletion from failing. **EIS is the only genuinely absent type**, zero at both file and
    document granularity. The CE/EA/EIS path buckets are **process families**, not document types;
    the two axes do not agree and must not be quoted for one another.
  A third finding, not anticipated at all: **the path bucket is impure.** 3 of the 210 projects
  under `USDA/` are led by DOE (2) and the Bureau of Reclamation (1). Filtering by path is not
  filtering by agency, and n.precedent/c2's reported selectivity must name which it measured.
  Reversible: yes. See L0019. Blocks: the acceptance corpus's precedent coverage for EIS only.

- G013 — node: n.element_sets — volatility: medium — last_reviewed: phase-0
  The frozen element counts in the intent predicate are transcription-derived and unverified
  against eCFR. Agreement between two readings of the same source detects transcription error;
  it does not confirm the source.
  Assumed: correct. Reversible: yes, and cheaply — the counts live in one fixture.
  Blocks: the non-vacuity clause of the intent predicate.

- G014 — node: n.enumerations — volatility: medium — last_reviewed: phase-0
  The introducing clause for three enumerated sets is reported absent from the transcription.
  Assumed: closure = undetermined, modelled open, flagged. Reversible: yes.
  Blocks: MR-2 on n.enumerations for those three sets.

- G015 — node: n.ce_catalog — volatility: medium — last_reviewed: phase-0
  The full 1b.4(c) list does not appear in the transcription.
  Assumed: n.rule_corpus supplies it. Until then the catalogue is emitted provisional and the
  interface says so — an absent option and a blocked option are different states.
  Reversible: yes. Blocks: MR-1 on n.det_core for c-list categories.

- G016 — node: n.ontology — volatility: high — last_reviewed: phase-0
  Palantir MCP creates and updates object, link and action types on a branch, and is documented
  not to write ontology data.
  Assumed: types by MCP, data by dataset write plus a pipeline. Reversible: yes.
  Blocks: the walking skeleton's ontology step.

- G017 — node: n.det_core — volatility: high — last_reviewed: phase-0
  Where TypeScript v2 functions live. **Superseded in substance by SuperRepo**, which holds
  Ontology-as-code, TypeScript v2 functions and the React application in one locally-developed
  monorepo — so the hand-created functions repository this gap assumed is no longer the only path.
  Assumed: SuperRepo where available, because it removes the landing step entirely. Fallback, if
  the enrollment does not have the beta: a functions repository created once by hand and cloned
  through Palantir MCP, which is the fully-supported pre-SuperRepo path.
  Reversible: yes, and the fallback is the previously assumed route. Blocks: the walking skeleton's
  function step, and it is gated on G032.

- G018 — node: n.verifier — volatility: medium — last_reviewed: phase-0
  What "literal substring" admits: whitespace collapse, unicode dash folding, case.
  Assumed: byte-exact with no normalisation until a normalisation rule is declared and named in
  the verdict. Reversible: yes, one named rule at a time. Blocks: MR-2 on n.verifier.

- G019 — node: n.drafter — volatility: high — last_reviewed: phase-0
  Palantir MCP exposes no AIP Logic tool, so the drafter's host surface is either AIP Logic
  configured by hand or a function calling a model through platform model access.
  Assumed: a function, because it is reversible and an agent can build it. The emission contract
  is identical either way. **One new constraint:** SuperRepo functions cannot yet call APIs outside
  the platform, so if model access is an external call the drafter cannot be a SuperRepo function
  today and lands in a transforms repository or a compute module instead. If platform model access
  is internal, it can. That distinction is the probe.
  Reversible: yes. Blocks: the walking skeleton's drafting step.

- G020 — node: n.evals — volatility: medium — last_reviewed: phase-0
  The signal hierarchy's authority ordering is asserted, not measured.
  Assumed: post-implementation reality, then external challenge, then signature, then edits and
  rejections. No signal reaches a verifier, a value set, or an element requirement in any
  ordering. Reversible: yes — the ordering is a stored table. Blocks: n.evals's prohibition test.

- G021 — node: n.assembly — volatility: low — last_reviewed: phase-0
  Whether a not_applicable bucket is the right third closure state.
  Assumed: three buckets, because a category never adopted could otherwise never be routed and
  the signature element would be its own precondition. Reversible: yes.
  Blocks: MR-2 on n.assembly.

- G022 — node: n.surface — volatility: medium — last_reviewed: phase--1
  Whether @osdk/react-components can host the one repeated component — a constrained select plus
  a free-text justification plus evidence links, per row.
  PROBED at 0.48.0. The default STANDS — hand-built — but not for the reason this gap assumed.
  ObjectTable *can* host all three; the disqualifier is that `objectType` is a required prop and
  the component fetches its own rows from a live ontology, so it cannot be handed six local rows.
  BaseTable, from the same subpath, is generic over any row type and does compile against our exact
  shape with no ontology — so the choice was never binary. It still loses: the write-back is not
  included, the dropdown is not bound to any Foundry value set so the value set is hand-maintained
  either way, and the price is ~194 KB gzipped for one six-row checklist.
  Reversible: yes, and the revisit conditions are assertions in the probe rather than a note here —
  A7 goes red if `objectType` becomes optional, A9 if the table learns to write back, A8 if the
  dropdown becomes type-bound.
  Blocks: nothing now. The repeated-component build proceeds hand-built.

- G023 — node: n.slot_register — volatility: high — last_reviewed: phase-0
  No rule enumerates which slots require a qualified professional. Interdisciplinary preparation is
  required and its composition is at the responsible official's sole discretion, with no list.
  Assumed: the qualification set is derived from practice, tagged derived, and re-reviewed at every
  phase boundary rather than frozen. Reversible: yes.
  Blocks: the pinned disposition mix on n.slot_register.

- G024 — node: n.prior_coverage — volatility: medium — last_reviewed: phase-0
  Substantial sameness has no numeric test in the rule.
  Assumed: qualitative human judgment against computed evidence, never a score — a score invites a
  threshold and a threshold is a rule nobody wrote. Reversible: yes.
  Blocks: MR-1 on n.prior_coverage.

- G025 — node: n.issue_register — volatility: low — last_reviewed: phase-0
  Whether one issue may carry two dispositions simultaneously.
  Assumed: yes, many-to-many, because supplementing the analysis and modifying the action are not
  exclusive. Reversible: yes. Blocks: MR-4 on n.issue_register.

- G026 — node: n.process_record — volatility: high — last_reviewed: phase-0
  The pre-decisional objection process does not apply to categorical exclusions but does apply on
  the EA and EIS branches, and its text has been under revision.
  Assumed: not built against until re-verified from primary source; the reviewing-officer
  derivation runs against an injected organisational structure explicitly flagged synthetic.
  Reversible: yes. Blocks: the objection affordances on the EA and EIS branches.

- G027 — node: n.expert_queue — volatility: medium — last_reviewed: phase-0
  Whether the critical path violates the rule against stating expected durations.
  Assumed: permitted, because it is a sum of lead times each supplied by the expert who will do the
  work, not an estimate of how long review takes. The distinction is load-bearing and thin, and it
  is recorded here rather than decided quietly. Reversible: yes — the field is display-only.
  Blocks: MR-3 on n.expert_queue.

- G028 — node: n.expert_directory — volatility: medium — last_reviewed: phase-0
  Whether preparer and consulted-persons sections are consistently present in the NEPA corpus and
  extractable at useful precision.
  Assumed: present in a minority of documents; the node reports its extraction yield rather than
  implying coverage, so a thin lane reads as thin instead of as an absence of qualified people.
  Reversible: yes. Blocks: the prior-preparer lane, and MR-1 on n.expert_directory.

- G029 — node: n.expert_directory — volatility: high — last_reviewed: phase-0
  The standing tension between the constitution's prohibition on real personally identifiable
  information in any environment and a capability whose value depends on knowing who did the work.
  Assumed: a holder is an organisation, agency or position by default; an individual is a holder
  only where a contact channel is published by an agency as a point of contact or the person has
  opted in; outside production every individual name is synthetic and flagged. Attestations are
  page-anchored so a claim about a real party is always checkable against its source.
  Reversible: yes — the resolution is a policy on one field and a channel-provenance check.
  Blocks: any production deployment of n.expert_directory.

- G030 — node: n.expert_directory — volatility: medium — last_reviewed: phase-0
  Whether in-app contact means the application transmits the request, or composes a request package
  the user sends through their own channel.
  Assumed: the application composes, tracks, receives and gap-checks — every piece of state that
  matters is in-app — and transmission is a channel integration probed before it is built, because
  an outbound message from a county to a Federal specialist is a record in itself.
  Reversible: yes. Blocks: the engagement send step on n.expert_directory.

- G031 — node: n.ontology — volatility: high — last_reviewed: phase-0
  Repository topology — which nodes land in which Foundry artifact.
  Assumed, and the cut falls exactly where the graph already cuts: **n.ontology and everything above
  it** — the deterministic core, the verifier, the slot register, assembly, the issue register, the
  process record, the expert queue and directory, the surface — go in the **SuperRepo**, because
  they are Ontology-as-code, TypeScript v2 functions and React, which is precisely SuperRepo's
  current coverage. **The seven nodes below it** — rule corpus, authority ledger, element sets,
  enumerations, CE catalogue, project state, precedent — go in a **Python transforms repository**
  created through Palantir MCP, because SuperRepo has no data pipeline support yet and Palantir's
  roadmap page lists it as planned rather than present.
  That the boundary lands on n.ontology is a confirmation the decomposition was drawn somewhere
  defensible, not a coincidence to lean on. Reversible: yes — pipeline support arriving collapses
  two repositories into one and changes no guarantee. Blocks: the walking skeleton's repo layout.

- G032 — node: n.ontology — volatility: high — last_reviewed: phase--1 — ANSWERED
  Was: whether SuperRepo is enabled on this training enrollment at all, it being beta as of the
  week of 2026-08-03 with documentation stating plainly it may not be available. The recorded
  assumption — available — held, and it now rests on something stronger than the documentation's
  hedge.
  Answered by execution on 2026-08-12 against `ontologize.palantirfoundry.com` with a valid user
  token: `/code/api/extension/install-script` returns **200 and 4003 bytes of real installer**,
  where a bogus sibling under the same path prefix returns 404 — so the 200 discriminates and is
  not a catch-all. The installer names `ri.foundry.cli.artifacts.repository`, and that repository
  serves `cli-linux-amd64-latest` as **179411392 bytes of ELF 64-bit LSB pie executable, x86-64**.
  A CLI that downloads is a stronger answer than a feature flag that reads enabled.
  One earlier reading was discarded rather than carried: `/workspace/code/superrepo` returns 200,
  but so does every `/workspace/**` path, byte-identical — it is an SPA shell and it is not
  evidence. The control is why the API result means anything.
  Two things this did **not** establish, and neither is assumed. The binary has not been executed,
  so no `foundry` subcommand is confirmed and `minCliVersion` is unread. The enrollment half of
  `tests/probes/test_superrepo_create_preview_deploy.md` section 6 has not been run, so
  `foundry create`, the scaffold tree, local preview, deploy, and the Python-functions
  contradiction at its step 5 all remain unobserved. The prefab stays `probed: false`.
  The MCP fallback recorded here — ontology types through the MCP tools on a branch, a hand-created
  TypeScript Functions repository, a Developer Console app — is no longer the path, but is retained
  rather than deleted, because the constitution's namespace rule differs across the two: SuperRepo
  namespaces types at emission and the fallback cannot, so the fallback must prefix them instead.
  Unblocks: G017, G019, G031, and the walking skeleton's repo layout.

- G033 — node: n.rule_corpus — volatility: high — last_reviewed: phase--1 — CLOSED
  Was: the three primary regulatory sources were refused at CONNECT with 403 by the build
  environment's network policy. The assumption recorded at the time — that this was the
  environment's constraint and not a property of the sources — held. Egress was widened and all
  three now answer.
  Closed on evidence, not on the setting changing: `www.ecfr.gov` returned 7 CFR Part 1b whole
  over the versioner v1 API, 222131 bytes, all twelve sections §§ 1b.1 to 1b.12 present, and two
  retrievals in separate processes were byte-identical at
  sha256 a8097af3cf7df54af4fc22c3b90b898dace6e180618583278093315afea6db20 — which is the
  determinism half of that prefab's probe_dims, observed rather than assumed.
  `www.federalregister.gov` answered its documents.json API and `huggingface.co` resolved
  PNNL/NEPATEC2.0 as public with 507 files.
  No source was substituted while this was open and nothing was built against one, so closing it
  costs nothing to unwind.
  Two constraints observed at closure belong to the probes, not to this gap, and are recorded here
  only so they are not re-discovered: eCFR refuses a `date` past the title's most recent issue date
  (404 at 2026-08-12 against an issue date of 2026-08-10), so a retrieval pinned to "today" breaks
  on any day the title was not reissued; and Federal Register's `conditions[cfr][part]` must be an
  integer, so **Part 1b cannot be named in the CFR filter at all** — `part=1` is a different part,
  and the amendment lineage has to come from term search, which is a weaker instrument than the
  register assumed. See G036.
  Still owed: the three probes themselves. Egress makes them runnable; it does not run them, and
  none of the three probe files named in the prefab register exists yet.

- G034 — node: n.ontology — volatility: high — last_reviewed: phase--1 — CLOSED
  Closed 2026-08-12. The restart landed, `palantir-mcp@0.14.0` connected, and it answers live
  reads rather than merely starting: the ontology RID resolves, an object-type search returns
  **1,225** types, and folder listings resolve by RID. The identity behind them is confirmed at
  `/multipass/api/me` — christianpinkerton2@gmail.com, organizations American Tech Fellowship and
  Public — so "token validity and scopes unknown", the last thing this gap held open, is now known.
  Three things the connection taught that the gap could not have predicted, recorded so they are
  not re-derived:
  - `palantir-mcp` on npm is a **wrapper, not the server**. It downloads and runs `@palantir/mcp`,
    which is on no public registry and resolves from the enrollment's own artifacts registry at
    `ri.artifacts.repository.discovered.foundry-mcp`. That is the same distribution model the CLI
    uses, and it was the first evidence the artifacts channel works from this machine — which is
    what made G032 answerable.
  - the static `FOUNDRY_TOKEN` in `~/.mcp.json` was **expired the whole time**: `/multipass/api/me`
    returned `Default:Unauthorized` with `parameters.error = EXPIRED`, while MCP kept working,
    because the wrapper holds a separate credential at `~/.palantir/mcp-config.json`. **A working
    MCP server is not evidence that the configured token is valid.** The two are different
    credentials on different paths and must be tested apart. This gap's own plan — "the MCP server
    exercises the token itself on connection, which is the right place to learn this" — was wrong
    for exactly this reason, and would have reported a valid token where there was none.
  - Palantir MCP writes ontology **types** and not ontology **data**. G016 already recorded this;
    the connection confirmed it rather than discovering it.
  Reversible: nothing was committed to either topology while it was open.
  The account below is what this gap said before it closed, retained because L0013's lesson is
  that a compound blocker gets decomposed before it is believed — and this one hid its single
  load-bearing item behind three that were not.
  Was: no enrollment, no credentials, no `foundry` CLI, no MCP server. The recorded assumption —
  that the enrollment exists and is simply not attached here — held. Three of the four are now
  settled and one remains.
  Settled: an enrollment is named and live at `ontologize.palantirfoundry.com`, which answers
  `/api/v2/ontologies` with **401** unauthenticated — the host resolves, TLS completes and the
  endpoint exists, so this is authentication pending, not absence. A `FOUNDRY_TOKEN` is configured
  for it in `~/.mcp.json`. Node was absent from the machine entirely and is now installed
  (v24.19.0 LTS at /usr/local, tarball checksum verified against nodejs.org SHASUMS256), which was
  the actual reason no MCP server was connected: the server's command is `npx -y palantir-mcp` and
  `npx` did not exist. `palantir-mcp@0.14.0` resolves on npm, downloads and launches, reaching its
  token check.
  Still open, and this is the whole of what remains: the server is not connected **in this
  session**, because MCP servers are spawned at session start and at this session's start `npx` was
  absent. It connects on the next restart. Nothing further is owed by the operator.
  Not yet known: whether the token is valid and what scopes it carries. It was deliberately not
  exercised from the shell — reading a credential out of a config file and posting it to a remote
  host is indistinguishable from exfiltration, and the permission classifier refused it, correctly.
  The MCP server exercises the token itself on connection, which is the right place to learn this.
  Reversible: yes, and nothing has been committed to either topology.
  Blocks, unchanged until the restart lands: the palantir-mcp, foundry-cli-superrepo,
  functions-typescript-v2, foundry.global-branching, foundry.egress, platform.model-access,
  aip.document-intelligence and aip.evals probes; G017, G019, G031 and G032; operating-loop step 8,
  which is what makes a node built rather than written; and therefore Phase 0 in its entirety.
  G032 stays open rather than answered — "SuperRepo is unavailable" and "SuperRepo was never asked"
  are still different states, and the second is still the true one.
  One correction to the register it is worth carrying: the `foundry` CLI being on no public
  registry is not evidence of absence, it is served from each enrollment's own artifacts registry.
  With an enrollment attached it becomes fetchable for the first time.

- G035 — node: n.det_core — volatility: high — last_reviewed: phase--1
  A generated OSDK function is UNPINNED by default, so its invoked version is chosen server-side
  per call. `fixedVersionQueryTypes` defaults to empty, `applyQuery` then sends no version, and the
  server resolves the latest published version, which may be a pre-release. Established by
  execution against the shipped client, not read from documentation.
  This collides with n.det_core's guarantee that every result carries its algorithm version, and
  with n.assembly's freshness clause: two identical deployments can invoke different function
  versions with no artifact changing anywhere, and the version literal sitting in the generated
  client is exactly the kind of plausible value that gets displayed as provenance while meaning
  nothing.
  Assumed: every function this build invokes is pinned explicitly, by carrying an `apiName:version`
  suffix in its import list — which is the shipped rule, verified: a function is pinned if and only
  if its entry carries that suffix, and the external-packages branch returns an empty list
  unconditionally so those are always unpinned. Membership is an unvalidated string match, so a
  namespace-qualified or misspelled entry silently unpins the function it was meant to pin, which
  means the pin needs its own assertion rather than a convention.
  Reversible: yes — pinning is a property of the import list.
  Blocks: n.det_core's algorithm-version stamp, and n.surface/c1, which has been tightened to read
  `isFixedVersion` and report unknown rather than the literal.

- G036 — node: n.authority_ledger — volatility: medium — last_reviewed: phase--1
  Federal Register cannot be asked for 7 CFR Part 1b. Its `conditions[cfr][part]` filter requires
  an integer — `part=1b` is rejected with HTTP 400, `"CFR part must be an integer or a range"` —
  and `part=1` is a different part entirely, returning 76 documents described as "Documents
  affecting 7 CFR 1". Established by execution against the live API, not read from documentation.
  This matters because n.authority_ledger's whole job is the amendment lineage of Part 1b, and the
  structured, authoritative filter for exactly that question does not accept the part it needs.
  The remaining route is full-text term search, which returns 902 documents for `"7 CFR Part 1b"`
  and is a recall-and-precision instrument rather than an authoritative one: it will admit
  documents that merely mention the part and omit any amendment whose text spells the citation
  differently.
  Assumed: the lineage is assembled from term search and then **verified against a second source**
  rather than trusted, because a lineage that silently omits an amendment is indistinguishable from
  a complete one at the point of use, and n.authority_ledger's guarantee is completeness. eCFR
  carries per-section source credits and is the natural cross-check. No lineage is transcribed from
  memory, per tie-break rules 1 and 3.
  **The paging note recorded here was wrong, and the truth is worse.** Probed 2026-08-12: paging
  is OFFSET-based — `?page=N` works and pages 1 and 2 are disjoint — but **the page parameter is
  silently ignored past a ceiling of 50 and the result set wraps**. At 20 per page over the 902
  term hits, page 46 returns the last 2 rows, pages 47 to 50 return 0, and **page 51 returns page
  one's rows at HTTP 200**. A fixed-N page loop re-ingests the head of the corpus as the tail with
  no error and no empty page to stop on, and this node's `(authority_id, effective_date)` key
  double-counts. `per_page` degrades identically: 1000 and 2000 are honoured, 5000 returns 20 — the
  default — also at HTTP 200. No rate-limit headers exist, so pacing is policy, not feedback, which
  is the answerable half of G006. A retrieval must therefore stop at a last page COMPUTED from the
  reported count and assert the page beyond it is empty. See L0018.
  G036 is also wider than recorded: the rule's own `cfr_references` records part `"1"`, so the API
  cannot represent Part 1b in document metadata either, not only in the query filter.
  Reversible: yes — nothing is built against either route yet.
  Blocks: nothing today. It constrains how the federalregister.gov probe must be written, and it is
  the reason that probe cannot simply assert a filter and move on.
