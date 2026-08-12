# Phase −1 prefab probe: `foundry-cli-superrepo`

    prefab:   foundry-cli-superrepo
    used_by:  n.ontology, n.det_core, n.verifier, n.slot_register, n.assembly,
              n.issue_register, n.expert_queue, n.process_record, n.surface,
              n.expert_directory   (ten nodes -- effectively the whole upper graph)
    probe:    tests/probes/test_superrepo_create_preview_deploy.md   (this file)
    runner:   tests/probes/superrepo_offline_half.sh                 (the runnable half)
    probed:   PARTIAL -- see VERDICT

    probed on:  2026-08-11
    probed at:  Node v22.22.2, npm 10.9.7, Linux 6.18.5, no Foundry enrollment,
                egress via an agent proxy (registry.npmjs.org and pypi.org reachable)

## VERDICT: **blocked**, but only in half, and the blocked half is now short

The register's central claim is **confirmed**: `foundry create` / `foundry deploy` and the
whole SuperRepo path **cannot be started from an environment like this one**, because
Palantir's SuperRepo CLI is **not distributed on any reachable public registry**. It is not
"beta and maybe off for this enrollment" — it is not obtainable at all without an enrollment
to download it from. That is a stronger constraint than the register recorded, and it is a
constraint on *who can run Phase −1*, not just on what Phase −1 finds.

The register's implicit assumption that the *whole* prefab is enrollment-gated is
**refuted**. Four things the ten dependent nodes need are runnable offline, today, and were
run:

| probe dimension | offline? | established here |
| --- | --- | --- |
| one SuperRepo via `foundry create` | **no** | CLI unobtainable |
| one object type declared in Ontology-as-code | **yes** | compiled, deterministic |
| one object type imported from the UI | **partly** | import path exercised with a hand-built stub |
| one TypeScript v2 function | **no** | needs `foundry start typescript-functions` |
| one React screen calling it | **partly** | scaffolded offline; cannot `npm install` |
| embedded Ontology preview run locally | **partly** | the OAC→OSDK chain ran; the preview *server* did not |
| one `foundry deploy` to the training enrollment | **no** | definitively blocked |

Run `bash tests/probes/superrepo_offline_half.sh` to reproduce every "yes" and "partly"
above. It exits **2 = PENDING ENROLLMENT** on success and **1** if the offline findings have
regressed. It can never exit 0; this probe is not complete and the file will not pretend it is.

---

## 1. Is the Foundry CLI on npm or pypi? No.

Searched `registry.npmjs.org` for `foundry`, `palantir`, `osdk`, `foundry cli`, `superrepo`,
`superrepo foundry`, `ontology as code palantir`, `foundry.yml`, and `scope:osdk`; then
requested these exact names. Every one is **404**:

    @palantir/foundry-cli   @palantir/cli        @palantir/foundry     @osdk/foundry-cli
    @osdk/superrepo-cli     @osdk/superrepo      @osdk/create-superrepo @palantir/superrepo
    @osdk/superrepo.cli     @osdk/ontology-as-code @osdk/oac           @foundry/cli

No installed Palantir package declares a `bin` named `foundry`. `@osdk/cli` declares `osdk`,
`@osdk/create-app` declares `create-osdk-app`, `@osdk/maker` declares `maker`. (An earlier
revision of this file claimed the first two were "the entire Palantir-published bin surface";
that was wrong — `maker` is a third, and this probe's own runner invokes it.)

**Guessing package names was the wrong method, and it missed the answer.** Palantir publishes
its *own* `foundry`-CLI integration harness on public npm as **`@osdk/integration-testing`**
(0.1.0), together with `@osdk/seed-helpers` and `@osdk/vite-plugin-status-reporter`. That
package carries the generated conjure model of the CLI and the CLI's installer. Section 2a
below is read off it. Steps 9 and 10 of the runner assert against it.

**Two decoys to name explicitly, so nobody re-finds them and thinks the probe is done:**

- **pypi `foundry-cli` 0.29.1** — *installs, and is not the thing.* Authored by Anjor Kanekar
  and Zay Cruz (`github.com/zaycruz/foundry-cli`), not Palantir. It installs a binary named
  **`pltr`**, not `foundry`. Its command surface is REST-API operations against a live stack
  (`dataset`, `ontology`, `sql`, `orchestration`, `third-party-apps`, …). There is no
  `create`, no `deploy` of a repo, no local preview, no SuperRepo concept. Useful for talking
  to a stack; irrelevant to this prefab.
- **pypi `foundry-dev-tools` 2.1.25** — "run your Palantir Foundry Repository transforms code
  on your local machine". Real and Foundry-adjacent, but it is the *transforms* local-dev
  story, not the SuperRepo story. Not probed further.

### Where the real CLI actually lives — RUN, not inferred

An earlier revision of this file inferred the CLI's distribution mechanism from
`palantir-mcp@0.14.0` and from the `.npmrc` that `create-osdk-app` emits, and stated it as
the enrollment's **artifacts npm registry** (`//<stack>/artifacts/api/:_authToken=${FOUNDRY_TOKEN}`).
**That inference was wrong.** The `.npmrc` mechanism is how the *generated OSDK package* is
installed; it is not how the CLI is obtained.

The real mechanism is in `@osdk/integration-testing/build/esm/scripts/download.js`:

    GET https://<stack>/code/api/extension/install-script      (POSIX)
    GET https://<stack>/code/api/extension/install-bat         (Windows)
      header: authorization: Bearer <token>
    -> piped to `bash -s --` with FOUNDRY_URL and TOKEN injected into its env

The stack serves a shell installer; the harness runs it. Host resolution is
`FOUNDRY_EXTERNAL_HOST`, else `FOUNDRY_HOSTNAME`, else a git remote pointing at Foundry.
The version floor the harness enforces is `MIN_FOUNDRY_CLI_VERSION = "0.224.0"`, probed by
`which foundry && foundry --version` parsed against `/cli (\d+\.\d+\.\d+…)/`.

**This was executed, not read.** Runner step 10 runs `npm install @osdk/integration-testing`
with scripts enabled; the postinstall calls `installFoundryCli()` and dies at:

    i Foundry CLI not found locally, attempting to install...
    Error: Invariant failed: Cannot resolve the Foundry host. Please set
    FOUNDRY_EXTERNAL_HOST or FOUNDRY_HOSTNAME, or configure a git remote pointing at Foundry.

**The `foundry` CLI is downloaded from the enrollment, not from the internet** — and that is
now established by running Palantir's own installer to the point where it stops, rather than
by 404-ing guessed package names. Phase −1 for this prefab cannot be delegated to an
unenrolled machine or agent. That is the topology-relevant finding, and it survives.

### 2a. `foundry.yml`'s SCHEMA — no longer unknown, and no enrollment needed

`@osdk/integration-testing` ships `build/types/generated/cli/__components.d.ts`, the generated
conjure model of the CLI's own API. It gives the schema this file previously listed as the one
thing blocking G031. Asserted by runner step 9.

    FoundryConfig                       # "Project-level configuration loaded from foundry.yml"
      minCliVersion: string                             REQUIRED
      products: ProductConfig[]                         REQUIRED
      functionsTypescriptRuntimeVersion?: string
      platformApiProxy?: { ontologyFoundryFallback: Route[]; passthrough: Route[] }
                                        # Route = { path: string; methods: string[] }

    ProductConfig
      apiNamespace: string                              REQUIRED
      components: Component[]                           REQUIRED
      osdkOutput: string                                REQUIRED
      imports?: ImportConfig[]          # ImportConfig = { ontology?: string }
      bundle?: BundleConfig             # marketplace: name, description, installMode
                                        #   InstallMode = PRODUCTION | BOOTSTRAP | SINGLETON
      includeInBundle?: boolean
      contentSecurityPolicyAdditions?: Record<string, string[]>

    Component = { path: string; type: ServiceName }

    ServiceName = ONTOLOGY | TYPESCRIPT_FUNCTIONS | PYTHON_FUNCTIONS | APP
                | STATUS_SERVER | PLATFORM_API_PROXY

Two load-bearing notes carried verbatim from the model's own docstrings:

- *"Single-product `foundry.yml` files (with top-level `components`) are normalized into this
  shape at load time with one product."* — so the minimal form has no `products:` key at all.
- *"ONTOLOGY, TYPESCRIPT_FUNCTIONS, PYTHON_FUNCTIONS, and APP are user-owned component types
  declared in `foundry.yml`. STATUS_SERVER and PLATFORM_API_PROXY are internal Foundry-managed
  services started implicitly by the CLI and must not be declared in `foundry.yml`."*

The smallest `foundry.yml` that the shipped SuperRepo tests actually write is one line:

    minCliVersion: "0.0.0"

### 2b. Service command lines and bodies — partly known offline too

- **Ontology preview server:**
  `foundry start ontology --skip-build --metadata <fullMetadataPath> --discovery-path <root>/.palantir`
  The `--metadata` file is **the same full-metadata JSON section 3c already produces offline.**
- **Status server:** `POST /status` with `ServiceStatus { service, status, level, timestamp, message? }`;
  `GET /status` returns the snapshot. `ServiceLifecycle = PREPARING | READY | FAILED | STARTING | STOPPED`,
  `StatusLevel = INFO | WARN | ERROR`.
- **Ontology seeding:** `PUT /seed` with
  `OntologySeed { objects: Record<objectTypeApiName, ObjectSeed[]>; links: SeedLinkEntry[] }`.
  200 empty on success; 400 malformed body; 503 while starting; 500 seeding failure.
- Still unknown: the **typescript-functions and python-functions runtime** request/response
  bodies beyond the endpoint paths `smartClient` posts to.

## 2. What the SuperRepo actually looks like — derived from shipped code, not docs

`@osdk/vite-plugin-superrepo@0.10.0` is public, and it is the client half of the
`foundry-cli` contract. Its compiled source names the CLI, its root marker, and its services.
This is **read off working code and then exercised**, not inferred from a docs page.

    <superrepo root>/
      foundry.yml                  <- THE root marker. findSuperrepoRoot() walks up
                                      until it finds this file; no other signal is used.
                                      Its SCHEMA is in section 2a (no enrollment needed).
      .palantir/
        .ontology-discovery.json            <- written by `foundry start ontology`
        .typescript-functions-discovery.json
        .python-functions-discovery.json
        .platform-api-proxy-discovery.json
        .status-server-discovery.json       <- named in the 0.6.0 changelog
      <the vite app>/
        src/client.ts              <- load-bearing EXACT path. The plugin's transform
                                      hook fires on `id.endsWith("/src/client.ts")` and
                                      rewrites its `@osdk/client` import in dev only.

**Two schemas, not one — an earlier revision of this file conflated them.** What the vite
plugin *reads* is `{ pid, url, caCertPath? }`, and step 8 proves that reader is satisfied by
exactly those keys. What the CLI *writes* is strictly larger — `ComponentDiscovery` in the
CLI's own generated model (section 2a) is:

    { pid: number, processStartTimeSecs: number, url: string, caCertPath?: string }

`processStartTimeSecs` is **required** on the writer side and is absent from the reader's
checks; treat `{pid, url}` as the minimum a *consumer* may assume, never as the file format.
Liveness is `process.kill(pid, 0)` — which is PID-reuse-unsafe on its own, and
`processStartTimeSecs` is presumably why the writer records a start time.
The four reader states are `ok` / `stale` (pid dead) / `malformed` (bad JSON or missing
fields) / `missing`. **All four were produced and asserted** by
`superrepo_offline_half.sh` step 8 against a hand-built skeleton; step 9 asserts the writer
schema separately.

The dev-server proxy table, verbatim from `PROXY_ROUTES`:

| dev-server prefix | service | path rewritten |
| --- | --- | --- |
| `/ontology-metadata` | `ontology` | no |
| `/object-set-service` | `ontology` | no |
| `/local-functions` | `typescript-functions` | yes |
| `/local-python-functions` | `python-functions` | yes |
| `/api` | `platform-api-proxy` | no |

In dev, `smartClient` intercepts `executeFunction` and posts to
`/local-functions/functions-typescript-runtime/api/functions/runtime/execute` (and the Python
equivalent) with `Authorization: Bearer fake-local-dev-token`. Production builds are untouched:
real `createClient`, real foundry URL, no wrap. **Nothing about the local dev loop is a
security boundary** — worth knowing before n.surface or n.det_core lean on it.

### Two SURPRISES that contradict the register

1. **`python-functions` is a first-class service in the shipped dev-server contract.** The
   register states, on Palantir's roadmap authority, that Python functions are "NOT yet
   supported" in SuperRepo. `PROXY_ROUTES` carries `/local-python-functions →
   python-functions`, `smartClient` carries a full `PY_RUNTIME` with snake_case parameter
   coercion and a serializing queue ("the runtime can only handle one at a time"), and the
   0.7.0 changelog names "python-functions waiting on ontology discovery" as a real race it
   fixed.

   An earlier revision of this file called this undiscriminable offline. It is **partly
   discriminable, and was discriminated**: the CLI's *own* generated model (section 2a) lists
   `PYTHON_FUNCTIONS` in `ServiceName` and states in its docstring that it is a **user-owned
   component type declared in `foundry.yml`**, alongside `ONTOLOGY` and `TYPESCRIPT_FUNCTIONS`.
   That is the CLI's contract, not a client built speculatively against it. What remains
   genuinely unknown is narrower and should be stated as such: **whether a given enrollment
   has it enabled, and whether a Python function actually executes.** That is Gate (c).
   It bears directly on n.drafter, which the register says is bound by exactly this.
2. **The register's "MAY NOT BE AVAILABLE ON THIS ENROLLMENT" understates the problem.** The
   availability question cannot even be *asked* from here, because the CLI is not obtainable.
   Availability-first is still the right order — it is just a question for an enrolled machine.

## 3. What ran offline

All of this is reproduced by `superrepo_offline_half.sh`. Exact versions exercised:

    @osdk/cli@0.81.0            @osdk/create-app@2.56.0     @osdk/maker@0.54.0
    @osdk/vite-plugin-oac@0.55.0 @osdk/vite-plugin-superrepo@0.10.0
    @osdk/generator-converters.ontologyir@2.55.0  @osdk/faux@0.41.0
    @osdk/api@2.56.0            @osdk/client.unstable@2.56.0

**a. `create-osdk-app` scaffolds with no network beyond npm, and no enrollment.** Templates are
bundled inside the package. The scaffold is **an OSDK app, NOT a SuperRepo**: no `foundry.yml`,
no `.ontology/`, no functions directory. It emits `foundry.config.json`, `vite.config.ts`,
`src/client.ts`, `.npmrc`, `.env.development/.production`, and a React app under `src/`.

Non-interactive invocation is fiddly and undocumented; every prompt must be pre-answered or
the CLI opens a TTY and crashes with `ERR_TTY_INIT_FAILED`. Three traps, all discovered by
reading `build/esm/index.js` after failing:

- `--clientId` must match `/^[0-9a-f]+$/`. A word like `FAKECLIENTID` is rejected.
- `--sdkVersion` takes `1.x` or `2.x` — a template key, **not** a semver. `2.5.7` is rejected.
- `--corsProxy` is a tri-state; omitting it prompts. Pass `--corsProxy` or `--no-corsProxy`.

**b. Ontology-as-code compiles offline and is byte-deterministic.** `@osdk/maker` reads
`.ontology/ontology.mjs` and emits the IR. Run in **two separate processes**, the output is
**byte-identical** (sha256 equal) with **no `--randomnessKey`** supplied. Note the CLI does
expose `--randomnessKey` ("value used to assure uniqueness of entities", must be a UUID), so
some path *can* be nondeterministic — but not this one, at these dimensions.

`defineObject` (declared) and `importOntologyEntity` (imported) land in **separate top-level
blocks**: `ontology.objectTypes` vs `importedOntology.objectTypes`. That is the register's
"code definitions are the source of truth; types created in the UI can be imported into code",
visible in the artifact.

*Caveat, stated rather than papered over:* the imported object here is a **hand-built stub**,
not a real export from a UI-created type. `importOntologyEntity` performs **no normalization** —
it writes straight into `importedTypes`. So the stub must already be in the flattened internal
shape (`properties` as an **array** carrying `apiName`), which is what `defineObject` produces.
Passing the ergonomic record shape crashes downstream in `convertObject` with
`(objectType.properties ?? []).map is not a function`. **Whether a real UI import produces that
shape is Gate (f).**

**c. The full OAC → OSDK chain runs offline, deterministically.** Three stages, per
`@osdk/vite-plugin-oac`'s own pipeline:

    .ontology/ontology.mjs --maker--> IR --converter--> full metadata --osdk cli--> .osdk/src/*

Stage 3 is `osdk unstable typescript generate --ontologyPath <local file> --outDir <dir>
--version dev`. In `--ontologyPath` mode it takes **no `--foundryUrl`, no token, no network**.
It produced `.osdk/src/ontology/objects/NepaDocument.ts` with the declared properties and
`primaryKeyApiName: 'documentId'`. Re-run in separate processes, the generated tree is
**identical** (`diff -r` clean). **This is the single biggest de-risk: n.ontology can develop
and regenerate its object types with no enrollment at all.**

**d. A real version seam, found by running it.** `@osdk/vite-plugin-oac@0.55.0` does:

```js
const blockData = JSON.parse(irContent).blockData;
OntologyIrToFullMetadataConverter.getFullMetadataFromIr(blockData);
```

but `@osdk/maker@0.54.0` emits top-level keys `[ontology, importedOntology, valueTypes,
importedValueTypes]` — **there is no `blockData`**. Fed `ir.blockData` the converter throws
`Cannot read properties of undefined (reading 'interfaceTypes')`; fed `ir.ontology` it
succeeds. At the current public latest-vs-latest pairing the OAC vite plugin **breaks at
Stage 2**. Two more sharp edges in the same file: it shells out to **`pnpm exec`** (hardcoded —
an npm-only SuperRepo breaks), and it invokes maker on **`ontology.mts`**, while maker's own
default is `ontology.ts` and this probe used `ontology.mjs`. A real SuperRepo may pin
versions that agree; **this pairing does not**, and G032's fallback path walks straight into it.

**e. The scaffold cannot be installed without the enrollment.** `create-osdk-app` writes
`"@<scope>/sdk": "latest"` into `package.json` and pins that scope to the enrollment's
artifacts registry in `.npmrc`. `npm install` therefore cannot resolve. The CLI does expose
`--skipOsdk` (2.x only), which is the lever if an unenrolled machine needs to typecheck the
React screen against a locally generated SDK instead — **untested here, Gate (g)**.

## 4. Precisely what needs an enrollment, and what does not

**Does NOT need an enrollment** (all reproduced above):
`create-osdk-app` scaffolding · `@osdk/maker` Ontology-as-code compilation · IR → full metadata
· `osdk unstable typescript generate --ontologyPath` · the `findSuperrepoRoot` / discovery-file
contract · reading the entire dev-server proxy and `smartClient` routing contract.

**DOES need an enrollment** — the whole blocked list, and it is five items, not "all of it":

- **(a) `foundry create`** — obtaining the CLI at all, and the SuperRepo scaffold it emits.
  **NOT the schema of `foundry.yml`** — that is section 2a and needs no enrollment. What is
  still open is only what `foundry create` *fills in*: the apiNamespace it picks, the default
  component layout, the `minCliVersion` it stamps.
- **(b) `foundry start <service>`** — the four service runtimes actually *running*. The
  ontology command line, the status service and the seeding endpoint are in section 2b.
  Still unknown: the typescript-functions and python-functions runtime request/response
  bodies beyond the endpoint paths `smartClient` posts to.
- **(c) the embedded Ontology preview** — the preview *server* executing, as opposed to the
  codegen chain, which ran, and whose output is exactly the `--metadata` file the server
  takes. **And the narrowed Python question from §2** (enabled on the enrollment? does a
  Python function execute?).
- **(d) a TypeScript v2 function end to end** — authoring, discovery via the `preview/specs`
  endpoint, execution through `smartClient`, and a React screen calling it with a real SDK
  installed from the enrollment registry.
- **(e) `foundry deploy`** — and, before any of it, **whether SuperRepo is enabled on this
  enrollment at all**. Availability first, exactly as the register says.

Smaller open questions, worth carrying but not blockers: **(f)** the real shape of a UI-imported
object type (§3b caveat); **(g)** whether `--skipOsdk` + a locally generated SDK lets an
unenrolled machine typecheck the React screen.

## 5. What this means for the graph

- **This does not change a node guarantee.** It changes *who can do Phase −1* and *what the
  fallback costs*. No node's assume/guarantee needs to move on this result.
- **G031 (repo split).** The SuperRepo shape is now known offline to the level of: root marker
  filename **and its full schema** (§2a), `.palantir/` discovery directory, the six service
  names and which two are CLI-internal, both discovery-file schemas (reader and writer), the
  proxy table, and the load-bearing `src/client.ts` path. **G031 has no remaining structural
  unknown blocking design** — only the values `foundry create` chooses.
- **G032 (pre-SuperRepo fallback).** The documented `@osdk/create-app` path works offline and
  is a genuine fallback, but three costs are now measured rather than assumed: the OSDK
  dependency is enrollment-gated at install time (§3e), the OAC vite plugin is **broken**
  against the current public maker (§3d), and non-interactive scaffolding has three
  undocumented flag traps (§3a).
- **n.drafter.** Left where it was. The Python-functions contradiction (§2, surprise 1) is
  real and unresolved; resolving it from the roadmap page alone would be supplying a value
  the source does not state.

## 6. RUNBOOK — the exact steps, and who can run them

### Offline half — run anywhere, no enrollment. **Completed 2026-08-11.**

```bash
bash tests/probes/superrepo_offline_half.sh          # exits 2 = PENDING (expected)
WORKDIR=/some/scratch bash tests/probes/superrepo_offline_half.sh
```

Exit **2** = offline half reproduces, enrollment half still pending. Exit **1** = an offline
finding regressed and this file is stale. Exit **0** is unreachable by construction.

### Enrollment half — **STEP 0 AND STEP 1 ARE NOW RUN. 2026-08-12.**

Step 0 is discharged: SuperRepo is available on this enrollment (G032). Step 1 is discharged
as far as an unauthenticated CLI can go — **the binary executes**, and §1's central claim that
it cannot be obtained from a public registry stands: it was fetched from the enrollment's own
`ri.foundry.cli.artifacts.repository`, not from npm.

```
~/.local/bin/foundry --version   ->  cli 0.223.0
```

**The installed CLI is BELOW the floor §1 records.** `MIN_FOUNDRY_CLI_VERSION` in
`@osdk/integration-testing` is `0.224.0`; this binary is `0.223.0`. Palantir's own harness would
refuse it. `foundry update self` exists and downloads from the stack's Artifacts repository, so
the fix is one authenticated command — but it is authenticated, so it is not yet run.

#### The real top-level command surface — executed, not inferred

    create  update  build  install  deploy  login  logout  start  generate-osdk
    config  import  register  run-with-auth  help

**Four commands §2a's model did not predict**, and they change what this prefab is:

- **`foundry deploy` does not deploy a SuperRepo. It deploys a MARKETPLACE BUNDLE.** Its flags
  are `--zip-path` (default `build/store.zip`), `--env-file-path` (default `env.yml`),
  `--store-rid` (a `ri.marketplace..marketplace.…` store) and **`--folder-rid`** (the Compass
  folder to install into). Subcommands `configure` and `poll`. So the deploy model is
  build-a-bundle → upload-to-a-store → install-into-a-folder, which is materially different from
  the "deploy the repo" §6 step 6 assumed. **`--folder-rid` is the containment lever** — it is
  where `SignatureReady_v2`'s RID has to go, and it is a flag, not a prompt.
- **`foundry build`** — `website`, `function-ts`, `ontology`. Marketplace integration blocks.
- **`foundry validate`** — validates a bundle *without deploying*, and carries `--dry-run`
  ("validate that a dry run build (no bundle produced) is valid"). This is a safe rehearsal that
  needs no write, and it should be run before any `deploy` on a shared enrollment.
- **`foundry register`** — registers a signing key with a Marketplace store, and its help names
  **`signingKeys` as a `foundry.yml` key**. §2a's schema, read off the conjure model, does not
  contain `signingKeys`. The schema in §2a is therefore **incomplete, not wrong** — it is the
  model `@osdk/integration-testing` ships, and the CLI reads more than that model describes.

Three more corrections to this file:

- **`foundry create` is template-driven, not "scaffold a SuperRepo".** Its help: "Create a new
  project from a template", interactive by default, templates sourced from `[[templates.sources]]`
  in the CLI config *and* from templates published by the stack you are logged in to. Three repo
  layouts (`template/`, `templates/<variant>/`, or the repo root). `--template` and `--variant`
  are required in non-interactive mode. §6 step 2's bare `foundry create sigready-superrepo` will
  not run unattended.
- **`foundry start` has six subcommands, and `python-functions` is one of them**: `display`,
  `ontology`, `platform-api-proxy`, `python-functions`, `status-server`, `typescript-functions`.
  This is a *third* independent contradiction of the register's "Python functions NOT yet
  supported", now from the shipped CLI's own help rather than from a client library or a generated
  model. Gate (c) narrows again: what is unknown is only whether *this enrollment* has it enabled
  and whether a Python function *executes*.
- **`foundry install pnpm`** — "Install pnpm dependencies with Foundry authentication". pnpm is
  the CLI's native package manager, which corroborates §3d's finding that `vite-plugin-oac`
  hardcodes `pnpm exec`. An npm-only SuperRepo is swimming against the tool.

`foundry run-with-auth '<cmd>'` injects `FOUNDRY_HOSTNAME` and `FOUNDRY_TOKEN` into a shell.
Worth naming plainly: it is the sanctioned way to hand credentials to a build step, and it is
also the shortest path to leaking them into a log. Do not wrap anything that prints its env.

#### Authentication — where step 1 stops

`~/.config/foundry-cli/config.toml` is created on first run (`[templates] sources = []`,
`[auth]` empty). **There is no stored credential**, and:

```
foundry login refresh
  ❌  Cannot refresh a token non-interactively: `foundry login refresh` requires human
      interaction to open the authorisation page within a browser.
```

`foundry login` itself reads `FOUNDRY_TOKEN` from the environment for non-interactive use and
takes `--foundry-url` (env `FOUNDRY_EXTERNAL_HOST`). **`login refresh` takes neither** — it is
browser-only by construction. So the enrollment half from step 2 onward is blocked on a human
opening a browser, not on anything this file can discover. That is the correct place for it to
stop, and it is a one-command unblock.

### Enrollment half, step 2 onward — **NOT RUN. Blocked on interactive authentication.**

Run these on an enrolled machine, in order, and record the real output — including failures,
which are the point. Stop at the first step that fails and record where.

```bash
# 0. AVAILABILITY FIRST. Everything below is moot if this is off.
#    In the Foundry UI, confirm SuperRepo / Ontology-as-code is enabled for this enrollment.
#    Record: enabled or not, the stack URL, and the date. If not enabled, STOP -- that
#    answer alone resolves the prefab and the fallback in G032 becomes the path.

# 1. Obtain the CLI. It is NOT on public npm (section 1). The stack serves a shell
#    installer; Palantir's own harness fetches and runs it. Easiest path:
export FOUNDRY_HOSTNAME=<stack hostname>       # or FOUNDRY_EXTERNAL_HOST
export FOUNDRY_TOKEN=<token from Developer Console>
npm install @osdk/integration-testing          # its postinstall installs the CLI
#    or by hand, which is exactly what that postinstall does:
#    curl -H "authorization: Bearer $FOUNDRY_TOKEN" \
#      https://$FOUNDRY_HOSTNAME/code/api/extension/install-script \
#      | FOUNDRY_URL=https://$FOUNDRY_HOSTNAME TOKEN=$FOUNDRY_TOKEN bash -s --
foundry --version                   # must be >= 0.224.0 (MIN_FOUNDRY_CLI_VERSION)
foundry --help                      # record the real top-level command surface

# 2. Scaffold. Record the ACTUAL directory tree, and DIFF foundry.yml against the
#    schema in section 2a -- the schema is known; the values it fills in are not.
foundry create sigready-superrepo
cd sigready-superrepo && find . -type f -not -path './node_modules/*' | sort
cat foundry.yml                     # expect: minCliVersion + components or products

# 3. Declare one object type in Ontology-as-code; import one created in the UI.
#    Compare the imported type's real shape against the hand-built stub in
#    superrepo_offline_half.sh step 5 -- this closes gate (f).

# 4. One TypeScript v2 function. One React screen calling it.

# 5. Local preview. Then check whether Python functions actually run -- gate (c),
#    the contradiction in section 2. Run `foundry start` and list what came up:
foundry start
ls -la .palantir/                   # which .<service>-discovery.json files appear?
#    If .python-functions-discovery.json appears AND a Python function executes,
#    the register's "Python functions NOT yet supported" is refuted. Record either way.

# 6. Deploy.
foundry deploy

# 7. Re-run the offline half inside the real SuperRepo and see whether the version
#    seam in section 3d exists there too, or whether `foundry create` pins versions
#    that agree:
grep -rE '"@osdk/(maker|vite-plugin-oac|cli)"' package.json */package.json
```

Then: replace this section's verdict, append a ledger entry naming the clause it moves, and
flip `probed` on `foundry-cli-superrepo` in `build/prefabs.jsonl` — via the orchestrator, not
by hand.

## 7. Ground rules honored

- **Rule 3 (never supply a value the source does not state).** `foundry.yml`'s schema, the
  service request/response bodies, and whether the enrollment has SuperRepo enabled are left
  as named unknowns. The Python contradiction is recorded as a contradiction, not resolved.
- **Rule 4 (refuse and name what is missing).** The blocked half is a five-item list with an
  owner and a runbook, not "all of it".
- **Rule 7 (explicit over inferred).** Every structural claim in §2 is read off compiled code
  in `@osdk/vite-plugin-superrepo@0.10.0` and then *executed* in step 8 of the runner. Where
  something is inferred rather than run — the hand-built import stub, `foundry.yml`'s contents —
  it is labeled inline.
- **Documentation is not a probe.** Nothing here rests on a docs page. Every "yes" in the
  verdict table is backed by a command in `superrepo_offline_half.sh` that a later session
  can re-run.
- **Twice, in separate processes.** Both determinism claims (maker IR; the full OAC→OSDK
  chain) were run as two independent `node` invocations and compared by hash and by `diff -r`.

## 8. Adversarial re-probe, 2026-08-11 — what changed and why

This file was re-run and attacked. The runner reproduced from a clean `WORKDIR` (exit 2) and
every version it names is the version actually installed. The central verdict **survives**.
Four claims did not, and the following were changed:

1. **Step 6 of the runner asserted nothing.** It printed `ok` down *both* branches and exited
   0, so the version-seam finding (§3d) — a headline result — had no kill test and would have
   stayed green if Palantir fixed the seam. Replaced with a two-sided assertion that pins the
   producer (`maker` emits no `.blockData`) *and* the consumer (`vite-plugin-oac` still reads
   `.blockData`, still hardcodes `pnpm exec`, still targets `ontology.mts`). Mutation-tested:
   rewriting the consumer to read `.ontology` now turns the step red.
2. **The proxy table was a comment.** Step 8 only checked the *set of service names*; the
   `prefix` and `rewrite` columns the table prints were never read. Now the whole table is
   compared element-by-element.
3. **The CLI's distribution mechanism was inferred and stated as fact** (artifacts npm
   registry + `FOUNDRY_TOKEN`). Refuted — it is `<stack>/code/api/extension/install-script`.
   Corrected in §1, and the gate is now *executed* by runner step 10 rather than argued.
4. **Three things were listed as enrollment-blocked that were reachable from here**: the
   `foundry.yml` schema, the service command lines and status/seed endpoints, and the
   writer-side discovery schema. All three are in `@osdk/integration-testing` on **public
   npm**. Added as §2a/§2b and asserted by runner step 9. The method failure worth naming:
   the original probe guessed twelve package names and 404'd them, instead of finding the
   package Palantir actually publishes.

Versions pinned by the runner are now asserted against what npm installed, so a silent
resolution drift fails the probe instead of quietly re-scoping every assertion below it.
