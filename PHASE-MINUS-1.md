# Phase −1 — probe results

Phase −1 is the sixteen prefab probes. **Eight ran. Eight did not**, and none of the eight that did
not is blocked on the environment any more — both environment gaps are closed. What remains is the
work itself.

Read the verdicts in `build/prefabs.jsonl`; this file is the map, not the record. Every probe file
lives at the path the register already named and is re-runnable.

```bash
python3 scripts/check.py build/ --phase 0     # 8 violations, all `probed is false`
```

The gate was 16 when this started, and 11 before the corpus probes landed. Nothing else fails.

---

## What ran

Each ran real code against a real published artifact at this build's dimensions, twice in separate
processes, and was then attacked by an independent verifier told to refute it. **Every one was
partly refuted**, and in four cases the verifier got materially further than the original probe.
That is the process working, not the process failing.

| prefab | verdict | the carried claim |
| --- | --- | --- |
| `GSA-TTS/pic-standards` | **pass** | partly — G007 confirmed, second question refused as not yet computable |
| `@osdk/react` | **pass** | confirmed but **overstated** |
| `@osdk/react::useOsdkFunction` | **fail** | right conclusion, **wrong type, wrong package, backwards symptom** |
| `@osdk/generator` | **fail** | right conclusion, **wrong mechanism**, and reality is worse |
| `@osdk/react-components` | **fail** | the register tested the **wrong hinge** |
| `ecfr.gov` | **fail** | G004 answered **weaker** than claimed; G001 **not answerable** from the source |
| `federalregister.gov` | **fail** | paging is offset, not cursor — and **wraps silently** past page 50 |
| `PNNL/NEPATEC2.0` | **fail** | the gate blocks all content; **no USFS bucket**, and no USDA EIS |

"fail" means the probe ran and the prefab does not behave as the register expected. It is a result,
not an error. Six of the eight are fails, which is the register being corrected by execution.

**Four of the first five changed a method. None changed a guarantee.** That is exactly what the order of work
predicts, and the one place it did not hold — `n.surface/c1` — was a method inside a clause, which
has been tightened rather than replaced.

### The four findings that change what someone builds

**Server rendering is not barred.** `renderToString` does *not* throw for any data-bound screen.
Under a Suspense boundary it emits the fallback and a switch-to-client marker; `useOsdkAction` never
touches `useSyncExternalStore` at all, so an action-only screen server-renders today — and that is
the exact shape of the 7 CFR 1b.11(a)(46) determination-recording screen. The original probe passed
only because it hard-coded the unwrapped case, the one shape a real streaming app never ships.

**A generated function is unpinned by default.** `fixedVersionQueryTypes` defaults to empty,
`applyQuery` then sends no version, and the server resolves the latest published version — possibly
a pre-release — per call. The version literal sitting in the generated client is decorative. Two
identical deployments can invoke different function versions with nothing changing anywhere, and a
server reporting a disagreeing version produced no error and a successful call. This collides with
`n.det_core`'s algorithm-version stamp; it is **G035**, and `n.surface/c1` now requires reading
`isFixedVersion` and reporting *unknown* rather than the literal. The pinning rule, established by
execution: a function is pinned **if and only if** its import-list entry carries an explicit
`apiName:version` suffix, membership is an unvalidated string match, and the external-packages
branch returns an empty list unconditionally.

**The prebuilt table loses, but not for the stated reason.** `ObjectTable` *can* host the
constrained select, the one-line justification and the two evidence links. It dies on `objectType`
being a required prop — it fetches its own rows from a live ontology and cannot be handed six local
ones. `BaseTable` from the same subpath is generic over any row type and does compile against our
shape, so the choice was never binary. It still loses: no write-back, no binding to any Foundry
value set, ~194 KB gzipped for a six-row checklist. **G022's default stands**, and the revisit
conditions are assertions inside the probe rather than a note in the gap.

**`universal` is not `provenance`.** Nine columns appear on all thirteen PIC entities; only six are
the provenance properties. Deriving the set by asking which columns are universal puts `id`,
`created_at` and `other` on every mapped object type as provenance. The obligation `n.ontology`
takes on is now a number: **thirteen entities**, derivable only from the CSV.

---

## What did not run, and why

> **Both blockers were re-tested on 2026-08-12 and both are now CLOSED.** The section below records
> the state before and after; `build/gaps.md` G033 and G034 are authoritative. The gate fell from 11
> to 8 when the three corpus probes ran — not when the blockers cleared, because clearing a blocker
> probes nothing.

**G033 — CLOSED.** Egress was opened and all three sources answer. Closed on evidence rather than on
the setting changing: eCFR returned 7 CFR Part 1b whole over the versioner v1 API — 222131 bytes,
all twelve sections §§ 1b.1 to 1b.12 — and two retrievals in separate processes were **byte-identical**
(`sha256 a8097af3…fea6db20`), which is the determinism half of that prefab's `probe_dims` observed
rather than assumed. Federal Register answered `documents.json`. `PNNL/NEPATEC2.0` resolves as public, 507 files.
> This originally continued "tree and parquet readable anonymously despite `gated: \"auto\"`."
> **Both halves were wrong**, and the probe caught it: there are **zero** parquet files — the corpus
> is 505 JSONL — and no file content is anonymously readable at all, including `.gitattributes`.
> Only README.md and the metadata and tree APIs are public. Reachability was read as retrievability.

> **The three corpus probes have since been written and run — 2026-08-12.** All three carry verdict
> `fail`, meaning each ran and the prefab does not behave as the register expected. Between them they
> answered G004 and G012, reframed G001 from "unverified" to "not answerable from this source",
> newly blocked G011 on HuggingFace authentication, widened G036, corrected two claims in this file,
> and corrected a citation in the constitution. See L0017, L0018, L0019.

Two constraints fell out of closing it, both recorded so they are not re-discovered:

- **eCFR refuses a future `date`.** 404 at `2026-08-12` against a most-recent issue date of
  `2026-08-10`. A retrieval pinned to "today" breaks on any day the title was not reissued.
  > This paragraph originally added "and this also answers **G004** in passing: a structured API
  > *does* exist at paragraph granularity." **That was wrong** and the probe caught it. The API is
  > structured at SECTION granularity; `<P>` carries no attributes anywhere in Part 1b. G004 is
  > answered, but weaker than claimed here, and the difference is the whole of G001.
- **Federal Register cannot name Part 1b at all.** `conditions[cfr][part]` requires an integer;
  `part=1b` is HTTP 400 and `part=1` is a different part. The amendment lineage has to come from term
  search and be cross-checked, not trusted — **G036**, and a worse problem than the rate-limit
  question G006 recorded.

**G034 — NARROWED to a single item.** The gap named four missing things; three were present or
configured all along.

| named as missing | actual state |
| --- | --- |
| an enrollment | live at `ontologize.palantirfoundry.com` — `/api/v2/ontologies` answers **401**, so authentication pending, not absence |
| credentials | `FOUNDRY_TOKEN` configured in `~/.mcp.json` |
| the `foundry` CLI | still absent, and correctly so — it is served from each enrollment's own artifacts registry, so it becomes fetchable only once attached |
| a Palantir MCP server | `palantir-mcp@0.14.0` resolves, downloads and launches, reaching its token check |

The single actual cause was that **Node was not installed on the machine at all**, so `npx -y
palantir-mcp` could never start; the absence surfaced as "no MCP server connected" and was recorded
as if that were the cause. Node v24.19.0 LTS is now installed at `/usr/local` from a tarball verified
against nodejs.org's `SHASUMS256.txt`.

> **Both closed on 2026-08-12.** The restart landed and `palantir-mcp@0.14.0` connected — answering
> live reads rather than merely starting: the ontology RID resolves, an object-type search returns
> 1,225 types, folder listings resolve by RID, and `/multipass/api/me` names
> christianpinkerton2@gmail.com in organizations American Tech Fellowship and Public.
> **G034 is CLOSED. G032 is ANSWERED, and the answer is that SuperRepo is available.**

Two rows of that table were wrong in ways worth keeping.

The `foundry` CLI was not "absent, and correctly so". It downloads:
`/code/api/extension/install-script` returns 200 and 4003 bytes of real installer against a 404 on
a bogus sibling path, and `ri.foundry.cli.artifacts.repository` serves `cli-linux-amd64-latest` as
179411392 bytes of ELF 64-bit LSB pie executable, x86-64. The register's inference — served from
each enrollment's own artifacts registry, fetchable once attached — was exactly right, and the
enrollment half of the runbook is now runnable rather than blocked.

`FOUNDRY_TOKEN` was not merely "configured", it was **expired** — `/multipass/api/me` returned
`Default:Unauthorized` with `parameters.error = EXPIRED` — and nobody noticed, because MCP kept
working off a *different* credential that the wrapper holds at `~/.palantir/mcp-config.json`.
`palantir-mcp` on npm is a wrapper, not the server; it downloads `@palantir/mcp` from
`ri.artifacts.repository.discovered.foundry-mcp`, the same channel the CLI uses, and that download
succeeding was the first evidence the artifacts channel worked at all.

> **A working MCP server is not evidence that the configured token is valid.** This gap's own plan
> — "the MCP server exercises the token itself on connection, which is the right place to learn
> this" — would have reported a valid token where there was none. Two credentials, two paths,
> tested apart. Kept as **L0014**.

One reading was discarded rather than carried: `/workspace/code/superrepo` returns 200, but so does
every `/workspace/**` path, byte-identical — an SPA shell, and no evidence. The control is the only
reason the API results mean anything.

**The lesson, kept as L0013:** a blocker written down as a compound of four unreachable things was
never re-tested item by item, so the one that was actually load-bearing stayed hidden behind three
that were not. Compound gaps get decomposed before they are believed.

### `foundry-cli-superrepo` — offline half clean, availability answered, enrollment half still owed

The README says to probe this one first because it is the only one whose answer changes the
topology. It was, and its offline half ran clean: 54 assertions, 0 failures. **Its availability
question is now answered too — see G032 — but the enrollment half has still not been run.**

- **The CLI is on no public registry at all.** Not npm, not PyPI, under any of twelve exact names
  tried. It is served from each enrollment's own artifacts registry. This probe **cannot be
  delegated to an unenrolled machine or agent** — a stronger constraint than the register's "may not
  be available on this enrollment", and a constraint on *who* can run Phase −1. Confirmed against
  the live registry: the installer resolves the binary from `ri.foundry.cli.artifacts.repository`,
  and the wrapper resolved `@palantir/mcp` from a sibling repository the same way.
- **The Ontology-as-code toolchain runs with no enrollment.** The full chain — `ontology.mjs` →
  IR → full metadata → generated OSDK TypeScript — executes offline and deterministically. This is
  the biggest single de-risk in Phase −1: **`n.ontology` is no longer waiting on this prefab.**
- **The SuperRepo shape is known offline**, read off compiled code and then executed: `foundry.yml`
  as root marker, `.palantir/` discovery, four services, and the React client fixed at exactly
  `src/client.ts`. G031 reduces to one unknown — what `foundry create` fills in.
- **An unresolved contradiction, recorded rather than decided.** The register states on Palantir's
  roadmap authority that Python functions are not supported in SuperRepo, and binds `n.drafter` on
  it. The shipped client carries `/local-python-functions` as a first-class proxy route with a full
  Python runtime. Either the roadmap is stale or the client is built ahead of a server not yet
  enabled. No offline evidence discriminates, so per tie-break rule 3 it stays open.
- **A live version seam in the G032 fallback**: at current public latest-vs-latest, the OAC vite
  plugin reads `irContent.blockData` while maker emits `ontology`, and the plugin throws at stage 2.

---

## What was deliberately not done

**No regulatory fixture was authored.** `n.element_sets`, `n.enumerations` and `n.ce_catalog` have
no prefab dependencies and would otherwise be the first nodes to open. Their oracles are fixtures
transcribed from 7 CFR Part 1b — the frozen element counts, the 34 enumerated sets, the nine capped
categories with their units and parsed strictness. With the source unreachable, writing those from
anywhere else is exactly the demon the tie-break order forbids: rule 1 says a value the primary
source does not support is wrong regardless of what it costs to fix, and rule 3 says a missing value
opens a gap rather than getting supplied. The gap is G033.

**No node was built.** Operating-loop step 8 requires landing the output as a Foundry resource and
reading it back by RID. A node with no resource is not built, so nothing here claims to be.

---

## Next, in order

Nothing below is waiting on the operator, and nothing below is waiting on the environment. The
restart has happened, MCP is connected, egress is open and the CLI downloads. **Every remaining
item in Phase −1 is work owed.**

1. ~~**Write and run the three corpus probes.**~~ **DONE 2026-08-12.** All three exist at the paths
   the register names and all three run green with verdict `fail`. `n.rule_corpus` and
   `n.authority_ledger` are unblocked with their methods corrected; `n.precedent` is **not** —
   G011 needs a HuggingFace identity that has accepted the NEPATEC gate, which is the one genuinely
   new blocker Phase −1 has produced. The three regulatory fixtures held back below are now writable
   for the eCFR-sourced counts, and `tests/probes/test_ecfr_part1b_retrieval.py` should be read
   before writing them: a 4-char-capped citation regex silently drops 15 of 1b.4's CE entries.
2. **Run the eight Foundry probes.** The MCP server is connected, so nothing gates these. Start with
   `tests/probes/test_superrepo_create_preview_deploy.md` section 6, whose step 0 — availability —
   is the only one already discharged. The binary has **not** been executed: no subcommand and no
   `minCliVersion` is confirmed, and `foundry create`, the scaffold tree, local preview and deploy
   are all unobserved. Settle the Python-functions contradiction, which is step 5.
   Install the CLI by fetching the binary directly rather than piping the installer to a shell — the
   installer also appends a PATH export to `~/.bashrc` and runs `foundry login --non-interactive`,
   both of which are side effects on the operator's machine that a probe should not smuggle in.
3. **`n.ontology` is openable independently of both.** The Ontology-as-code chain runs offline, the
   PIC obligation is a known thirteen entities, and G007 is confirmed. Note that `packet.py` will
   still print **"Do not build this node."** while its prefabs are unprobed — that refusal is the
   gate working, and step 2 is what clears it.
4. Then the walking skeleton, once per document type.

Environment, verified 2026-08-12, so no one re-derives it: egress open to eCFR / Federal Register /
HuggingFace / npm / raw.githubusercontent; Node v24.19.0 + npm 11.17.0 at `/usr/local`; `gh` 2.23.0
authenticated as `garf42` with `repo` and `workflow` scopes and `git push` working; Python 3.11.2
**stdlib only** — no pip, no `requests`, no `pytest`, so probes use `urllib.request` and the build
suites run standalone (`python3 tests/build/test_gate.py`); Palantir MCP connected against
`ontologize.palantirfoundry.com` as christianpinkerton2@gmail.com; SuperRepo available and the
Foundry CLI fetchable. `CLAUDE.md` carries the durable version of all of this, including the
containment boundary and the two-credential trap. Add to it rather than re-discovering it.

## Machinery added along the way

Four findings about the plan's own instrumentation, all in the ledger with kill tests, all with the
demon installed and watched to go red:

- **L0001** — `--rediscovered` could never validate: no clause carried an id, so `clause_ids` was
  always empty. The rediscovery rate is the only instrument for detecting packet-assembly failure
  and it was dead on arrival. 52 clause ids assigned; it now reports.
- **L0002** — the gate's own guards had never been watched fail. Six defects installed, six fire.
- **L0003** — packet assembly had no implementation. `scripts/packet.py` now assembles it and runs
  `can-i-build`. The O(node degree) claim is measured: degree 15 → 779 lines, degree 1 → 306, and
  adding a non-neighbour node leaves a packet byte-identical.
- **L0005** — the README told Phase −1 to run *fourteen* probes against a register of sixteen.
  `tests/build/test_plan_prose.py` re-derives every count the plan states about itself, and caught a
  second drift on its first run.
