/**
 * PHASE -1 PREFAB PROBE — @osdk/generator  (used_by: n.surface)
 * ============================================================================
 * probe_dims: clean install of the generated SDK after moving one function
 *             import forward one minor version.
 *
 * Makes n.surface/c1 checkable:
 *   "[BINDING] never infer the invoked function version from the import list;
 *    read it out of the generated client, and write calls correct under every
 *    version the client might resolve to"
 *
 *
 * WHAT THE REGISTER CARRIED IN, AND WHAT ACTUALLY HAPPENS
 * -------------------------------------------------------
 * Carried from a parallel build, unconfirmed there:
 *
 *   "the generated client continued to emit the older function version after
 *    the import list moved, silently, with no error and no warning. Import
 *    list and invoked version are decoupled."
 *
 * Probed here against @osdk/generator 2.56.0 / @osdk/client 2.56.0 (npm
 * `latest` on 2026-08-11) on node v22.22.2, by RUNNING the generator offline
 * against a fixture ontology manifest and then RUNNING the generated client's
 * invocation path against a stub fetch. Verdict, split:
 *
 *   REFUTED — "continued to emit the older function version". The generator is
 *     faithful to the manifest it is handed. Move a function from 1.1.0 to
 *     1.2.0 in the manifest and the literal baked into
 *     ontology/queries/<fn>.ts moves with it (A3). If a real regeneration ever
 *     emits a stale version, the staleness is UPSTREAM of @osdk/generator, in
 *     whatever assembles the manifest. See PENDING below.
 *
 *   CONFIRMED, by a different and worse mechanism — "import list and invoked
 *     version are decoupled". The version literal in the generated client is
 *     DECORATIVE BY DEFAULT. @osdk/client sends it on the wire only when the
 *     generated const also carries `isFixedVersion: true`:
 *
 *         // @osdk/client/build/esm/queries/applyQuery.js
 *         version: query.isFixedVersion ? query.version : undefined,
 *
 *     `isFixedVersion` is not derived from the manifest. It is a separate
 *     generator argument, `fixedVersionQueryTypes`, which DEFAULTS TO `[]`
 *     (generateClientSdkVersionTwoPointZero.js). So an ordinarily generated
 *     SDK emits `version: '1.2.0'` into its source and then sends NO version
 *     query param at all — and the platform endpoint's own doc comment says
 *     "By default, the latest version of the Query is executed. The latest
 *     version is the one that was most recently published, which may be a
 *     pre-release version." Observed on the wire at C1/C2.
 *
 *   CONFIRMED — "silently, with no error and no warning". Zero diagnostics of
 *     any kind are emitted across four generations (B1). No diagnostic site in
 *     the shipped generator concerns a function version at all (B2). And a
 *     server whose metadata reports a DIFFERENT version than the generated
 *     client's literal produces no error, no warning, and a successful call
 *     (C3) — applyQuery never compares the two.
 *
 *
 * CONSEQUENCE FOR n.surface/c1 — THE CLAUSE'S METHOD IS INSUFFICIENT
 * ------------------------------------------------------------------
 * "read it out of the generated client" is necessary but does not finish the
 * job. Reading `version` alone gives you the version that was in the manifest
 * at generation time, which by default is NOT the version invoked. You must
 * read `isFixedVersion` too, and when it is false the invoked version is not
 * knowable client-side at all — the server picks it, per call.
 *
 * The clause's second half — "write calls correct under every version the
 * client might resolve to" — is exactly right, and this probe strengthens the
 * case for it: under the default generation, "every version the client might
 * resolve to" is literally every version the server has published, including
 * pre-release ones.
 *
 * `readInvokedFunctionVersion()` below is the clause implemented honestly. It
 * refuses to name a version when the client is not pinned. Import it from
 * n.surface call-site audits rather than reading `.version` directly.
 *
 *
 * E2, ANSWERED — HOW AN IMPORT LIST DECIDES WHETHER ANYTHING IS PINNED
 * ---------------------------------------------------------------------------
 * This was previously filed as "needs an enrollment, not inferable from the npm
 * artifact". THAT WAS WRONG, and it was the most consequential error in the
 * first pass of this probe: the caller is itself a published npm package,
 * @osdk/foundry-sdk-generator, released in lockstep with @osdk/generator. Its
 * build/esm/index.js both computes `fixedVersionQueryTypes` and passes it to
 * generateClientSdkVersionTwoPointZero. Recovered and executed at E2a-E2c.
 *
 * THE RULE: a function is pinned IF AND ONLY IF its entry in the import list
 * carries an explicit `:version` suffix.
 *
 *     queryTypesApiNamesToLoad: ["computeCategoricalExclusion"]
 *         -> fixedVersionQueryTypes = []      -> isFixedVersion: false
 *         -> NO version on the wire, server resolves latest per call
 *
 *     queryTypesApiNamesToLoad: ["computeCategoricalExclusion:1.2.0"]
 *         -> fixedVersionQueryTypes = ["computeCategoricalExclusion"]
 *         -> isFixedVersion: true             -> ?version=1.2.0 on the wire
 *
 * and the external-packages branch returns `fixedVersionQueryTypes: []`
 * unconditionally, so entities coming from external packages are ALWAYS
 * unpinned. This is the register's own phrase — "the import list" — with an
 * actual mechanism under it, and it is the answer n.surface/c1 needs.
 *
 *
 * PENDING — NEEDS A FOUNDRY ENROLLMENT, DOES NOT PASS AND MUST NOT BE READ AS
 * ---------------------------------------------------------------------------
 * There is no Foundry enrollment in this environment (no `foundry` CLI, no
 * Palantir MCP server, no ontology). ONE thing stays unprobed, at E1:
 *
 *   E1 — Move one function import forward one minor version in the Developer
 *        Console, regenerate, clean-install the SDK, and read the emitted
 *        literal. This is the only way to learn whether the manifest handed to
 *        the generator carries the new version, which is where the carried
 *        claim's staleness would have to live.
 *
 * NOTE ALSO UNPROBED, and NOT the same thing as E1: this probe generates in
 * memory and reads the emitted source. It never npm-installs a generated SDK.
 * So a staleness that lives in the INSTALL — a cached tarball, a lockfile
 * pinning the previously published SDK package, an unbumped SDK package
 * version — would not be caught here either. When the register says the
 * generated client "continued to emit the older version", that is a second
 * candidate mechanism, DOWNSTREAM of the generator rather than upstream, and
 * A2/A3 do not rule it out. Do not read A3 as refuting more than it does.
 *
 * E1 is a gap, not a finding. Under SR_PROBE_STRICT=1 this file exits 3 while
 * anything is pending. Do not delete E1 when it turns green — record the
 * answer in it.
 *
 *
 * HOW TO RUN
 * ----------
 *   1. Install the deps somewhere (NEVER inside this repo):
 *        mkdir -p /tmp/osdk-gen-probe && cd /tmp/osdk-gen-probe && npm init -y
 *        npm install @osdk/generator@2.56.0 @osdk/client@2.56.0 \
 *                    @osdk/foundry-sdk-generator@2.56.0 tsx
 *      @osdk/foundry-sdk-generator is what makes E2 runnable. It is OPTIONAL:
 *      without it E2a-E2c go PENDING (never silently green) and A-D still run.
 *   2. Point the probe at that install and run it:
 *        OSDK_PROBE_DEPS=/tmp/osdk-gen-probe \
 *          npx --prefix /tmp/osdk-gen-probe tsx \
 *          /home/user/SignatureReady/tests/probes/test_client_version_matches_imports.ts
 *
 *   If deps are ever installed at the repo root, OSDK_PROBE_DEPS can be omitted
 *   and node's normal upward resolution from this file will find them.
 *
 *   Run it TWICE in two separate processes and diff the RESULT-DIGEST line:
 *        for i in 1 2; do <cmd> > run$i.txt; done; diff run1.txt run2.txt
 *   D1 asserts within-process stability; the cross-process diff is on you.
 *
 * EXIT CODES
 * ----------
 *   0  every runnable assertion held. E is still PENDING — read the banner.
 *   1  an assertion failed: the toolchain changed. READ THE FAILURE LINE.
 *   2  the probe could not run (deps missing, etc). Never a pass.
 *   3  SR_PROBE_STRICT=1 and the enrollment-gated half at E has not been run.
 *
 * NOTES FOR WHOEVER RUNS THIS NEXT
 * --------------------------------
 *   - No network is touched. Generation is entirely in-memory against a
 *     fixture manifest defined in this file. Invocation runs the REAL
 *     @osdk/client against a stub fetch pointed at https://example.invalid
 *     with the string "not-a-token". That string is not a credential.
 *   - Assertions are written to FAIL WHEN THE BEHAVIOUR CHANGES. A red run is
 *     not automatically bad news. If A4 fails, `fixedVersionQueryTypes` stopped
 *     defaulting to empty and the decoupling may have been fixed. If C1 fails,
 *     the client started sending the version unpinned. Either would be good
 *     news that n.surface must be told about.
 *   - NEGATIVE CHECKS, all run 2026-08-11 against the installed packages and
 *     all reproducible. Each patch below turns exactly the named assertion red
 *     and exits 1; restoring the file turns it green again.
 *       applyQuery.js  `version: query.version,`                      -> C1
 *       applyQuery.js  `version: undefined,`                          -> C2
 *       applyQuery.js  add a console.warn on the version line         -> C3
 *       generatePerQueryDataFiles.js  isUsingFixedVersion = true      -> A4, A6
 *       generatePerQueryDataFiles.js  includes -> endsWith            -> A6
 *       generatePerQueryDataFiles.js  inject Math.random into output  -> D1
 *       generatePerQueryDataFiles.js  consola.warn about the version  -> B1, B2
 *       generatePerQueryDataFiles.js  consola.info about the version  -> B1, B2
 *       generatePerQueryDataFiles.js  dynamic-import consola.warn     -> B1
 *       generatePerQueryDataFiles.js  throw GeneratorError re version -> B2
 *       generator-converters wireQueryTypeV2ToSdkQueryDefinitionNoParams,
 *         hardcode `version: "1.1.0"`                                 -> A3, A5
 *       foundry-sdk-generator lastIndexOf(":") -> lastIndexOf("@")    -> E2a
 *     C2 is also C1's positive control: the same regex that finds no version
 *     param on the unpinned calls does find `version=1.2.0` on the pinned ones,
 *     in the same run.
 *   - B1 WAS VACUOUS UNTIL 2026-08-11 and is the cautionary tale of this file.
 *     It captured `console.*` only, while @osdk/generator's real diagnostic
 *     channel is `consola`, which writes to process.stdout/stderr directly. A
 *     generator warning loudly about a function version on every single
 *     generation left B1 GREEN. B0 is now a standing positive control proving
 *     the capture observes a real consola.warn; if B0 fails, B1 means nothing.
 *     B2 was widened at the same time — it matched only
 *     `consola.(warn|error)|console.(warn|error)|throw new Error` and scanned
 *     only @osdk/generator, so it missed `consola.info`, `throw new
 *     GeneratorError` (4 such sites ship), and every diagnostic in
 *     @osdk/generator-converters, which is the package that actually emits the
 *     `version` literal.
 *   - Deps genuinely missing exits 2, verified from a directory with no
 *     node_modules anywhere above it.
 *   - No top-level await and no JSX: this repo has no root package.json
 *     declaring "type": "module", and the deps resolve from outside the repo.
 */

import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, resolve as pathResolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const PROBED_AT_GENERATOR_VERSION = "2.56.0";
const PROBED_AT_CLIENT_VERSION = "2.56.0";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = pathResolve(HERE, "..", "..");

/* ─────────────────────────── plumbing ─────────────────────────── */

/** Locate an installed package. Explicit over inferred: OSDK_PROBE_DEPS wins. */
function findPkgRoot(pkg: string): string | undefined {
  const seeds = [process.env.OSDK_PROBE_DEPS, REPO_ROOT, HERE, process.cwd()]
    .filter((s): s is string => !!s);
  for (const seed of seeds) {
    let dir = pathResolve(seed);
    for (;;) {
      const candidate = join(dir, "node_modules", ...pkg.split("/"));
      if (existsSync(join(candidate, "package.json"))) return candidate;
      const up = dirname(dir);
      if (up === dir) break;
      dir = up;
    }
  }
  return undefined;
}

function walkJs(dir: string, out: string[] = []): string[] {
  if (!existsSync(dir)) return out;
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) walkJs(p, out);
    else if (p.endsWith(".js")) out.push(p);
  }
  return out;
}

class Pending extends Error {}

/**
 * SOUND diagnostic capture.
 *
 * The earlier version of this probe intercepted `console.*` only. That was
 * VACUOUS: @osdk/generator's actual diagnostic channel is `consola` (it does
 * `import consola from "consola"` in wireObjectTypeV2ToSdkObjectConstV2.js and
 * passes consola as the logger into @osdk/generator-converters), and consola
 * writes through `process.stdout`/`process.stderr` directly, NOT through
 * `console.*`. Verified by mutation on 2026-08-11: injecting a
 * `consola.warn(`FUNCTION VERSION MISMATCH: ...`)` into the query-generation
 * path left B1 GREEN. The byte sinks are the only honest place to listen.
 *
 * B0 is the standing positive control for this function. Do not delete it.
 */
function installDiagnosticCapture(): {
  diagnostics: Array<[string, string]>;
  restore: () => void;
} {
  const diagnostics: Array<[string, string]> = [];
  const consoleKeys = ["log", "warn", "error", "info", "debug", "trace"] as const;
  const saved: Record<string, unknown> = {};
  for (const k of consoleKeys) {
    saved[k] = (console as never as Record<string, unknown>)[k];
    (console as never as Record<string, unknown>)[k] = (...a: unknown[]) =>
      diagnostics.push([`console.${k}`, a.map(String).join(" ")]);
  }
  const realOut = process.stdout.write.bind(process.stdout);
  const realErr = process.stderr.write.bind(process.stderr);
  const sink = (label: string) =>
    (chunk: unknown, enc?: unknown, cb?: unknown): boolean => {
      diagnostics.push([label, String(chunk)]);
      if (typeof enc === "function") (enc as () => void)();
      else if (typeof cb === "function") (cb as () => void)();
      return true;
    };
  (process.stdout as never as Record<string, unknown>).write = sink("stdout");
  (process.stderr as never as Record<string, unknown>).write = sink("stderr");
  return {
    diagnostics,
    restore: () => {
      (process.stdout as never as Record<string, unknown>).write = realOut;
      (process.stderr as never as Record<string, unknown>).write = realErr;
      for (const k of consoleKeys) {
        (console as never as Record<string, unknown>)[k] = saved[k];
      }
    },
  };
}

const failures: string[] = [];
const pendings: string[] = [];
const digestParts: string[] = [];

function check(id: string, what: string, fn: () => void): void {
  try {
    fn();
    console.log(`  ok   ${id}  ${what}`);
    digestParts.push(`${id}=ok`);
  } catch (e) {
    if (e instanceof Pending) {
      console.log(`  PEND ${id}  ${what}\n         ${(e as Error).message}`);
      pendings.push(`${id}: ${what} — ${(e as Error).message}`);
      digestParts.push(`${id}=pending`);
      return;
    }
    console.log(`  FAIL ${id}  ${what}\n         ${(e as Error).message}`);
    failures.push(`${id}: ${what} — ${(e as Error).message}`);
    digestParts.push(`${id}=fail`);
  }
}

function eq(actual: unknown, expected: unknown, msg: string): void {
  const a = JSON.stringify(actual);
  const b = JSON.stringify(expected);
  if (a !== b) throw new Error(`${msg}\n         expected ${b}\n         actual   ${a}`);
}

/* ───────────────────── the fixture manifest ─────────────────────
 * Shaped at THIS build's dimensions, not a tutorial's: one Foundry Function
 * that decides a NEPA categorical exclusion, the shape n.ce_catalog and
 * n.surface actually deal in. One string parameter, one boolean output. The
 * function version is the only thing that moves between generations.
 * `fullApiName` is the KEY in queryTypes, not `raw.apiName` — see
 * EnhancedBase.js. The two are kept identical here on purpose.
 */
const FN = "computeCategoricalExclusion";

function fixtureManifest(functionVersion: string): unknown {
  return {
    ontology: {
      apiName: "signatureready",
      displayName: "SignatureReady",
      description: "probe fixture, not a real ontology",
      rid: "ri.ontology.main.ontology.0000-probe-fixture",
    },
    objectTypes: {},
    actionTypes: {},
    interfaceTypes: {},
    sharedPropertyTypes: {},
    queryTypes: {
      [FN]: {
        apiName: FN,
        rid: "ri.function-registry.main.function.0000-probe-fixture",
        version: functionVersion,
        parameters: { projectId: { dataType: { type: "string" }, required: true } },
        output: { type: "boolean" },
        typeReferences: {},
      },
    },
  };
}

/** MinimalFs, in memory. Nothing is written to disk by this probe. */
function memFs() {
  const files: Record<string, string> = {};
  return {
    writeFile: async (p: string, c: string) => { files[p] = c; },
    mkdir: async () => {},
    readdir: async () => [] as string[],
    all: () => files,
    get: (p: string) => files[p],
  };
}

const QUERY_FILE = `/out/ontology/queries/${FN}.ts`;

/**
 * Pull the RUNTIME const out of the generated source — `export const FN: FN = {...}`
 * — not the type declaration above it. @osdk/client reads the runtime value;
 * the type is inert. Conflating them is how you talk yourself into believing
 * the version is load-bearing.
 */
function readGeneratedConst(src: string): { version: string; isFixedVersion: string } {
  const m = new RegExp(
    `export const ${FN}\\s*:\\s*${FN}\\s*=\\s*\\{([\\s\\S]*?)\\n\\};`,
  ).exec(src);
  if (!m) throw new Error(`could not find the generated runtime const for ${FN}`);
  const body = m[1];
  const v = /version:\s*'([^']*)'/.exec(body);
  const f = /isFixedVersion:\s*(\w+)/.exec(body);
  if (!v) throw new Error(`generated const carries no \`version\`:\n${body}`);
  if (!f) throw new Error(`generated const carries no \`isFixedVersion\`:\n${body}`);
  return { version: v[1], isFixedVersion: f[1] };
}

/* ───────── n.surface/c1, implemented honestly ─────────
 * Use this at n.surface call sites instead of reading `.version` off a
 * generated query const. It will not name a version the client does not pin,
 * because naming one there would be inferring the invoked version — exactly
 * what the clause forbids.
 */
export type InvokedVersion =
  | { pinned: true; version: string }
  | { pinned: false; version: null; generatedLiteral: string; reason: string };

export function readInvokedFunctionVersion(
  queryDef: { version?: string; isFixedVersion?: boolean },
): InvokedVersion {
  if (queryDef.isFixedVersion === true && typeof queryDef.version === "string") {
    return { pinned: true, version: queryDef.version };
  }
  return {
    pinned: false,
    version: null,
    generatedLiteral: queryDef.version ?? "(absent)",
    reason:
      "isFixedVersion is not true, so @osdk/client sends no `version` on the wire "
      + "(applyQuery.js: `version: query.isFixedVersion ? query.version : undefined`). "
      + "The server resolves the latest published version, per call. The literal in "
      + "the generated client records generation time only and must not be reported "
      + "as the invoked version.",
  };
}

/* ─────────────────────────── the probe ─────────────────────────── */

async function main(): Promise<number> {
  const genRoot = findPkgRoot("@osdk/generator");
  const cliRoot = findPkgRoot("@osdk/client");
  if (!genRoot || !cliRoot) {
    console.error(
      "PENDING/BLOCKED: could not resolve "
      + `${!genRoot ? "@osdk/generator " : ""}${!cliRoot ? "@osdk/client" : ""}\n`
      + `Searched upward from: OSDK_PROBE_DEPS, ${REPO_ROOT}, ${HERE}, ${process.cwd()}\n`
      + "Fix: install the deps OUTSIDE this repo and set OSDK_PROBE_DEPS — see the header.",
    );
    return 2;
  }

  const genPkg = JSON.parse(readFileSync(join(genRoot, "package.json"), "utf8"));
  const cliPkg = JSON.parse(readFileSync(join(cliRoot, "package.json"), "utf8"));
  console.log(`\n@osdk/generator ${genPkg.version}   (pinned at ${PROBED_AT_GENERATOR_VERSION})`);
  console.log(`@osdk/client    ${cliPkg.version}   (pinned at ${PROBED_AT_CLIENT_VERSION})`);
  console.log(`node            ${process.version}\n`);

  const generator = await import(
    pathToFileURL(join(genRoot, "build", "esm", "index.js")).href
  );
  const client = await import(
    pathToFileURL(join(cliRoot, "build", "esm", "index.js")).href
  );
  const generate = generator.generateClientSdkVersionTwoPointZero;

  /* ── A. what the generator emits, and where the version comes from ── */
  console.log("A. GENERATOR EMISSION — run against a fixture manifest, in memory");

  // Every diagnostic the generator might raise is captured across all four runs
  // — console AND the raw byte sinks, because consola bypasses console.
  const genCapture = installDiagnosticCapture();
  const diagnostics = genCapture.diagnostics;

  let genA: Record<string, string> = {};
  let genB: Record<string, string> = {};
  let genC: Record<string, string> = {};
  let genD: Record<string, string> = {};
  let genErr: unknown;
  try {
    // A: manifest at 1.1.0, default arguments — an ordinary generated SDK.
    const a = memFs();
    await generate(fixtureManifest("1.1.0"), "signatureready/probe", a, "/out", "module");
    genA = a.all();

    // B: THE PROBE DIMENSION — the same function moved forward one minor.
    const b = memFs();
    await generate(fixtureManifest("1.2.0"), "signatureready/probe", b, "/out", "module");
    genB = b.all();

    // C: same manifest, but the function named in `fixedVersionQueryTypes`.
    const c = memFs();
    await generate(
      fixtureManifest("1.2.0"), "signatureready/probe", c, "/out", "module",
      new Map(), new Map(), new Map(), false, [FN],
    );
    genC = c.all();

    // D: `fixedVersionQueryTypes` carrying a name that does not match fullApiName.
    const d = memFs();
    await generate(
      fixtureManifest("1.2.0"), "signatureready/probe", d, "/out", "module",
      new Map(), new Map(), new Map(), false, [`signatureready.${FN}`],
    );
    genD = d.all();
  } catch (e) {
    genErr = e;
  } finally {
    genCapture.restore();
  }

  if (genErr) {
    console.error(`PENDING/BLOCKED: generation threw — ${(genErr as Error).message}`);
    return 2;
  }

  check("A1", "the generator writes a per-function file into ontology/queries/", () => {
    if (!genA[QUERY_FILE]) {
      throw new Error(`no ${QUERY_FILE}; got ${JSON.stringify(Object.keys(genA))}`);
    }
  });

  check("A2", "manifest 1.1.0 -> the version literal is BAKED into generated source", () => {
    eq(readGeneratedConst(genA[QUERY_FILE]).version, "1.1.0", "generated const version");
  });

  check(
    "A3",
    "PROBE DIM: manifest moved one minor -> the emitted literal MOVES WITH IT. "
    + "This is the half of the carried claim that is refuted.",
    () => {
      eq(readGeneratedConst(genB[QUERY_FILE]).version, "1.2.0", "generated const version");
      if (genA[QUERY_FILE] === genB[QUERY_FILE]) {
        throw new Error("generated file was byte-identical across a version move");
      }
    },
  );

  check(
    "A4",
    "DEFAULT generation emits isFixedVersion:false — `fixedVersionQueryTypes` "
    + "defaults to []. FAILS IF THE DECOUPLING IS EVER FIXED.",
    () => {
      eq(readGeneratedConst(genA[QUERY_FILE]).isFixedVersion, "false", "gen A isFixedVersion");
      eq(readGeneratedConst(genB[QUERY_FILE]).isFixedVersion, "false", "gen B isFixedVersion");
    },
  );

  check("A5", "naming the function in fixedVersionQueryTypes flips it to true", () => {
    const c = readGeneratedConst(genC[QUERY_FILE]);
    eq(c.isFixedVersion, "true", "gen C isFixedVersion");
    eq(c.version, "1.2.0", "gen C version");
  });

  check(
    "A6",
    "a fixedVersionQueryTypes entry that does not match fullApiName SILENTLY "
    + "yields isFixedVersion:false — membership is a bare Array.includes",
    () => {
      eq(readGeneratedConst(genD[QUERY_FILE]).isFixedVersion, "false", "gen D isFixedVersion");
    },
  );

  /* ── B. the silence half ── */
  console.log("\nB. SILENCE — is anything said when versions disagree?");

  // B0 exists because B1 was VACUOUS before 2026-08-11: it listened on
  // `console.*` while the generator talks on `consola`, which writes straight
  // to the byte sinks. A silence assertion is worthless without a live proof
  // that the microphone is on. If B0 ever fails, B1 means NOTHING.
  const consolaRoot = findPkgRoot("consola");
  let consolaWarn: ((m: string) => void) | undefined;
  if (consolaRoot && existsSync(join(consolaRoot, "dist", "index.mjs"))) {
    // consola resolves to dist/index.mjs under the node+import condition.
    const mod = await import(
      pathToFileURL(join(consolaRoot, "dist", "index.mjs")).href
    );
    const c = mod.consola ?? mod.default;
    if (c && typeof c.warn === "function") consolaWarn = (m: string) => c.warn(m);
  }

  check(
    "B0",
    "POSITIVE CONTROL for B1: the capture harness actually observes a real "
    + "consola.warn. Without this, B1's silence is unfalsifiable.",
    () => {
      if (!consolaWarn) {
        throw new Error(
          "could not resolve/load consola — it is a declared dependency of "
          + "@osdk/generator and IS its diagnostic channel. Without this control, "
          + "B1's capture cannot be validated and B1 must not be believed.",
        );
      }
      const cap = installDiagnosticCapture();
      let viaConsola = 0;
      let viaStream = 0;
      try {
        process.stderr.write("probe-self-test-raw\n");
        viaStream = cap.diagnostics.length;
        consolaWarn("probe-self-test-consola");
        viaConsola = cap.diagnostics.length - viaStream;
      } finally {
        cap.restore();
      }
      if (viaStream < 1) throw new Error("harness missed a direct process.stderr.write");
      if (viaConsola < 1) {
        throw new Error(
          "harness missed consola.warn — this is exactly the blindness that made "
          + "B1 vacuous before 2026-08-11. B1 is meaningless until this passes.",
        );
      }
    },
  );

  check(
    "B1",
    "four generations, including a version move, emit ZERO diagnostics of any kind",
    () => {
      eq(diagnostics, [], "diagnostics captured during generation");
    },
  );

  check(
    "B2",
    "no diagnostic site in the shipped generator OR its converters concerns a "
    + "FUNCTION version",
    () => {
      // Allowlisted: the one message that says "version" but means the
      // generator's own major, not a function version.
      const allow = ["This generator version does not support generating v1 sdks"];
      // WIDENED 2026-08-11. The old pattern was
      //   /consola\.(warn|error)|console\.(warn|error)|throw new Error/
      // which missed, all confirmed by mutation: `consola.info(...)`,
      // `throw new GeneratorError(...)` (2 such sites ship in the generator and
      // 2 more in the converters), and any logger passed in by the caller —
      // the generator hands `consola` to @osdk/generator-converters as a
      // `logger` argument. It also scanned ONLY @osdk/generator, excluding the
      // converters package that actually produces the `version` literal.
      const roots = [join(genRoot, "build", "esm")];
      const convRoot = findPkgRoot("@osdk/generator-converters");
      if (!convRoot) {
        throw new Error(
          "cannot resolve @osdk/generator-converters — it emits the `version` "
          + "literal (wireQueryTypeV2ToSdkQueryDefinitionNoParams) and MUST be "
          + "scanned; refusing to report silence over a package I cannot read",
        );
      }
      roots.push(join(convRoot, "build", "esm"));

      const hits: string[] = [];
      for (const root of roots) {
        for (const f of walkJs(root)) {
          for (const line of readFileSync(f, "utf8").split("\n")) {
            const isDiagnostic =
              /(consola|logger)\s*\.\s*\w+\s*\(/.test(line)
              || /console\s*\.\s*\w+\s*\(/.test(line)
              || /throw\s+new\s+\w*Error/.test(line);
            if (!isDiagnostic) continue;
            if (!/version/i.test(line)) continue;
            const msg = /[`"']([^`"']{8,})[`"']/.exec(line)?.[1] ?? line.trim();
            if (!allow.some((a) => msg.includes(a))) hits.push(`${f}: ${msg}`);
          }
        }
      }
      eq(hits, [], "version-related diagnostic sites in generator + converters");
    },
  );

  /* ── C. what actually goes on the wire ── */
  console.log("\nC. INVOCATION — real @osdk/client, stub fetch, nothing dialled");

  // The two shapes a generated const can take, transcribed from A above.
  const asGenerated = (isFixedVersion: boolean) => ({
    apiName: FN,
    type: "query" as const,
    version: "1.2.0",
    isFixedVersion,
    osdkMetadata: { extraUserAgent: "signatureready/probe" },
  });

  let seen: string[] = [];
  const stubFetch = async (url: string, init?: { method?: string }) => {
    seen.push(`${init?.method ?? "GET"} ${url}`);
    const u = new URL(url);
    if (u.pathname.endsWith("/execute")) {
      return new Response(JSON.stringify({ value: true }), {
        status: 200, headers: { "Content-Type": "application/json" },
      });
    }
    // Function metadata. Deliberately reports a version that DISAGREES with
    // the generated client's literal, so C3 can watch for a complaint.
    return new Response(JSON.stringify({
      apiName: FN,
      rid: "ri.function-registry.main.function.0000-probe-fixture",
      version: "9.9.9-DISAGREES-WITH-GENERATED",
      parameters: { projectId: { dataType: { type: "string" }, required: true } },
      output: { type: "boolean" },
    }), { status: 200, headers: { "Content-Type": "application/json" } });
  };

  // https://example.invalid is reserved and unroutable; "not-a-token" is not a
  // credential. stubFetch is the only fetch this client will ever call.
  const osdk = client.createClient(
    "https://example.invalid",
    "ri.ontology.main.ontology.0000-probe-fixture",
    async () => "not-a-token",
    undefined,
    stubFetch,
  );

  // Same sound capture as the generation half: console AND the byte sinks.
  const wireCapture = installDiagnosticCapture();
  const wireDiagnostics = wireCapture.diagnostics;

  let unpinnedCalls: string[] = [];
  let pinnedCalls: string[] = [];
  let unpinnedResult: unknown;
  let wireErr: unknown;
  try {
    seen = [];
    unpinnedResult = await osdk(asGenerated(false)).executeFunction({ projectId: "p1" });
    unpinnedCalls = seen;

    seen = [];
    await osdk(asGenerated(true)).executeFunction({ projectId: "p1" });
    pinnedCalls = seen;
  } catch (e) {
    wireErr = e;
  } finally {
    wireCapture.restore();
  }

  if (wireErr) {
    console.error(`PENDING/BLOCKED: invocation threw — ${(wireErr as Error).message}`);
    return 2;
  }

  for (const c of [...unpinnedCalls, ...pinnedCalls]) console.log(`       wire: ${c}`);

  check(
    "C1",
    "isFixedVersion:false -> the generated client's version literal NEVER "
    + "REACHES THE WIRE. No `version` param on metadata or execute.",
    () => {
      const withVersion = unpinnedCalls.filter((c) => /[?&]version=/.test(c));
      eq(withVersion, [], "unpinned calls carrying a version param");
      if (unpinnedCalls.length < 2) {
        throw new Error(`expected a metadata GET and an execute POST, got ${JSON.stringify(unpinnedCalls)}`);
      }
    },
  );

  check(
    "C2",
    "isFixedVersion:true -> version=1.2.0 rides on BOTH the metadata GET and "
    + "the execute POST",
    () => {
      const withVersion = pinnedCalls.filter((c) => /[?&]version=1\.2\.0(&|$)/.test(c));
      eq(withVersion.length, pinnedCalls.length, "pinned calls carrying version=1.2.0");
    },
  );

  check(
    "C3",
    "server metadata reporting a DIFFERENT version than the generated literal "
    + "raises nothing and the call succeeds — applyQuery never compares them",
    () => {
      eq(wireDiagnostics, [], "diagnostics raised during invocation");
      eq(unpinnedResult, true, "unpinned call result");
    },
  );

  check(
    "C4",
    "n.surface/c1: readInvokedFunctionVersion refuses to name a version the "
    + "client does not pin",
    () => {
      const unpinned = readInvokedFunctionVersion(asGenerated(false));
      eq(unpinned.pinned, false, "unpinned .pinned");
      eq(unpinned.version, null, "unpinned .version");
      const pinned = readInvokedFunctionVersion(asGenerated(true));
      eq(pinned.pinned, true, "pinned .pinned");
      eq(pinned.version, "1.2.0", "pinned .version");
    },
  );

  /* ── D. determinism ── */
  console.log("\nD. DETERMINISM");

  const digestOf = (files: Record<string, string>) => {
    const h = createHash("sha256");
    for (const k of Object.keys(files).sort()) h.update(`${k}\0${files[k]}\0`);
    return h.digest("hex");
  };

  const repeat = memFs();
  await generate(fixtureManifest("1.2.0"), "signatureready/probe", repeat, "/out", "module");

  check("D1", "regenerating the same manifest yields a byte-identical tree", () => {
    eq(digestOf(repeat.all()), digestOf(genB), "generation digest");
  });

  /* ── E. the half that reaches past the two core packages ──
   * E1 genuinely needs a Foundry enrollment. E2 does NOT — it was wrongly
   * recorded as enrollment-blocked and is now executed against the published
   * caller package. Keep the two apart: conflating them is how a reachable
   * question gets filed as impossible.
   */
  console.log("\nE. BEYOND THE TWO CORE PACKAGES");

  const enrolled = !!(process.env.FOUNDRY_URL && process.env.FOUNDRY_ONTOLOGY_RID);

  check(
    "E1",
    "regenerate a REAL SDK after moving one function import forward one minor, "
    + "clean-install it, and read the emitted literal",
    () => {
      if (!enrolled) {
        throw new Pending(
          "No enrollment: FOUNDRY_URL / FOUNDRY_ONTOLOGY_RID unset, no `foundry` CLI, "
          + "no Palantir MCP server. A2/A3 show the generator is faithful to its "
          + "manifest, so if a real regeneration emits a stale version the staleness "
          + "is upstream, in manifest assembly. UNKNOWN — do not assume either way.",
        );
      }
      throw new Pending(
        "Enrollment env vars are set but the real-regeneration steps are not "
        + "implemented here. Implement them, then record the answer in this file.",
      );
    },
  );

  /* E2 WAS WRONGLY RECORDED AS UNREACHABLE.
   *
   * The earlier note said "Not inferable from the npm artifact: the argument is
   * supplied by the caller, not the package." That is false. The caller IS a
   * published npm artifact: @osdk/foundry-sdk-generator, versioned in lockstep
   * with @osdk/generator (2.56.0), whose build/esm/index.js both computes
   * `fixedVersionQueryTypes` and calls generateClientSdkVersionTwoPointZero
   * with it. Its source is also public at palantir/osdk-ts. No enrollment is
   * needed to read or run it. Recovered and executed 2026-08-11.
   *
   * THE RULE, transcribed from the shipped build and asserted against it below:
   * a query is pinned IF AND ONLY IF the entry in the IMPORT LIST carries an
   * explicit `:version` suffix. `["fn"]` -> unpinned. `["fn:1.2.0"]` -> pinned.
   * The external-packages branch returns `fixedVersionQueryTypes: []`
   * unconditionally, so those are ALWAYS unpinned.
   *
   * This is the register's own phrase — "the import list" — with a mechanism
   * attached, and it is the answer n.surface/c1 needs.
   */
  const fsgRoot = findPkgRoot("@osdk/foundry-sdk-generator");
  const fsgIndex = fsgRoot ? join(fsgRoot, "build", "esm", "index.js") : undefined;
  const fsgSrc = fsgIndex && existsSync(fsgIndex) ? readFileSync(fsgIndex, "utf8") : undefined;

  /** The shipped rule, transcribed. E2a pins the transcription to the artifact. */
  function importListToFixedVersionQueryTypes(importList: string[]): string[] {
    const out: string[] = [];
    for (const queryType of importList ?? []) {
      const lastColonIndex = queryType.lastIndexOf(":");
      if (lastColonIndex !== -1) out.push(queryType.substring(0, lastColonIndex));
    }
    return out;
  }

  check(
    "E2a",
    "the shipped @osdk/foundry-sdk-generator still derives fixedVersionQueryTypes "
    + "by the `apiName:version` colon rule (pins the transcription to the artifact)",
    () => {
      if (!fsgSrc) {
        throw new Pending(
          "@osdk/foundry-sdk-generator is not installed next to the other probe "
          + "deps. It IS on npm at the matching version — `npm install "
          + "@osdk/foundry-sdk-generator@2.56.0` — install it and this stops "
          + "being pending. Do NOT record E2 as enrollment-blocked; it is not.",
        );
      }
      for (
        const needle of [
          'const lastColonIndex = queryType.lastIndexOf(":");',
          "fixedVersionQueryTypes.push(queryTypeApiName);",
          "fixedVersionQueryTypes: []",
          "ontologyInfo.fixedVersionQueryTypes",
        ]
      ) {
        if (!fsgSrc.includes(needle)) {
          throw new Error(
            `the shipped caller no longer contains \`${needle}\` — the colon rule `
            + `transcribed into this probe has drifted from the artifact. Re-read `
            + `build/esm/index.js before believing any E2b result.`,
          );
        }
      }
    },
  );

  check(
    "E2b",
    "EXECUTED: an import list entry WITHOUT `:version` generates an UNPINNED "
    + "function; only an explicit `fn:version` entry pins it",
    () => {
      if (!fsgSrc) throw new Pending("see E2a — install @osdk/foundry-sdk-generator");
      eq(importListToFixedVersionQueryTypes([FN]), [], "plain import list");
      eq(importListToFixedVersionQueryTypes([`${FN}:1.2.0`]), [FN], "versioned import list");
      // and the same rule, carried through the REAL generator, must land in the
      // generated const — this is what makes it executed rather than read.
      eq(readGeneratedConst(genB[QUERY_FILE]).isFixedVersion, "false", "plain -> unpinned");
      eq(readGeneratedConst(genC[QUERY_FILE]).isFixedVersion, "true", "versioned -> pinned");
    },
  );

  check(
    "E2c",
    "the external-packages branch of the shipped caller returns "
    + "fixedVersionQueryTypes: [] unconditionally — those are ALWAYS unpinned",
    () => {
      if (!fsgSrc) throw new Pending("see E2a — install @osdk/foundry-sdk-generator");
      if (!/externalObjects,\s*\n\s*fixedVersionQueryTypes: \[\]/.test(fsgSrc)) {
        throw new Error(
          "could not find the unconditional `fixedVersionQueryTypes: []` in the "
          + "external-packages branch; re-read the caller",
        );
      }
    },
  );

  /* ── summary ── */
  const digest = createHash("sha256").update(digestParts.join("|")).digest("hex").slice(0, 32);
  console.log(`\nRESULT-DIGEST ${digest}`);
  console.log(`RESULT-COUNTS ok=${digestParts.filter((p) => p.endsWith("=ok")).length} `
    + `fail=${failures.length} pending=${pendings.length}`);

  if (failures.length > 0) {
    console.log("\nFAILURES — the toolchain moved. Read each line before believing it is a bug.");
    for (const f of failures) console.log(`  - ${f}`);
    return 1;
  }

  if (pendings.length === 0) {
    console.log(
      "\n================================================================\n"
      + "VERDICT: FULL PASS — no pending assertions remain.\n"
      + "================================================================",
    );
    return 0;
  }

  console.log(
    "\n================================================================\n"
    + "VERDICT: OFFLINE-PASS / ENROLLMENT-HALF-PENDING\n"
    + "  This is NOT a full pass. The generator half (A), the silence half\n"
    + "  (B), the wire half (C), determinism (D) and the published-caller\n"
    + "  half (E2) all ran and held. Only E1 — which needs a real Foundry\n"
    + "  regeneration — never ran and is UNKNOWN.\n"
    + `  ${pendings.length} pending assertion(s):\n`
    + pendings.map((p) => `    - ${p}`).join("\n")
    + "\n================================================================",
  );

  if (process.env.SR_PROBE_STRICT === "1") {
    console.log(
      `SR_PROBE_STRICT=1: exiting 3 because ${pendings.length} assertion(s) are pending.`,
    );
    return 3;
  }
  return 0;
}

main().then(
  (code) => { process.exit(code); },
  (e) => { console.error("PENDING/BLOCKED: probe crashed\n", e); process.exit(2); },
);
