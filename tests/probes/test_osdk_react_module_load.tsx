/**
 * PHASE -1 PREFAB PROBE — @osdk/react  (used_by: n.surface)
 * ============================================================================
 * probe_dims: one screen using useOsdkObjects, one using useOsdkFunction,
 *             one using useOsdkAction.
 *
 * WHAT THIS FILE PINS
 * -------------------
 * The prefab register carried this claim in from a parallel build:
 *
 *   "the data hooks call useSyncExternalStore with no getServerSnapshot, so
 *    renderToString throws for any data-bound screen. Pin the limitation with
 *    an asserting test so it goes red the day the library ships the capability."
 *
 * Probed here against @osdk/react 2.56.0 (npm `latest` on 2026-08-11), under
 * react 19.2.8 AND react 18.3.1, on node v22.22.2. Verdict: CONFIRMED for the
 * data hooks, REFUTED for useOsdkAction.
 *
 *   - useOsdkObjects  -> renderToString THROWS "Missing getServerSnapshot, ..."
 *   - useOsdkFunction -> renderToString THROWS "Missing getServerSnapshot, ..."
 *   - useOsdkAction   -> renderToString SUCCEEDS. It never calls
 *                        useSyncExternalStore at all; it is built from
 *                        useState/useRef/useCallback/useEffect/useMemo.
 *
 * So the register's "any data-bound screen" is right, but "any screen using
 * these three hooks" would be wrong. An action-only screen server-renders fine.
 * Assertion A9 below pins that, so the day useOsdkAction acquires an external
 * store this file also goes red.
 *
 * These assertions are written to FAIL when the limitation LIFTS. A red run is
 * therefore not necessarily bad news: read the failure line. If A6b/A7/A8 fail,
 * @osdk/react has shipped getServerSnapshot and n.surface's SSR posture should
 * be revisited. If A4 fails, the hooks were renamed.
 *
 * HOW TO RUN
 * ----------
 *   1. Install the deps somewhere (NEVER inside this repo):
 *        mkdir -p /tmp/osdk-probe && cd /tmp/osdk-probe && npm init -y
 *        npm install @osdk/react @osdk/client react react-dom tsx
 *   2. Point the probe at that install and run it:
 *        OSDK_PROBE_DEPS=/tmp/osdk-probe \
 *          npx --prefix /tmp/osdk-probe tsx \
 *          /home/user/SignatureReady/tests/probes/test_osdk_react_module_load.tsx
 *
 *   If deps are ever installed at the repo root, OSDK_PROBE_DEPS can be omitted
 *   and node's normal upward resolution from this file will find them.
 *
 *   Run it TWICE in two separate processes and diff the RESULT-DIGEST line:
 *        for i in 1 2; do <cmd> > run$i.txt; done; diff run1.txt run2.txt
 *
 * EXIT CODES
 * ----------
 *   0  every assertion held: the limitation is still present, exactly as pinned
 *   1  an assertion failed: the library changed. READ THE FAILURE LINE.
 *   2  PENDING/BLOCKED: the probe could not run (deps missing, etc). Never a pass.
 *
 * NOTES FOR WHOEVER RUNS THIS NEXT
 * --------------------------------
 *   - No Foundry enrollment is needed. The OsdkProvider is fed a client built
 *     against an unreachable host with a dummy token. Nothing is dialled:
 *     renderToString is synchronous and useSyncExternalStore never calls
 *     `subscribe` on the server, so no request is ever made. The credential
 *     string below is not a credential.
 *   - createObservableClient leaves open handles; without the explicit
 *     process.exit() at the bottom this probe hangs after printing. That is not
 *     a failure, it is why the exit is explicit.
 *   - Deliberately no JSX and no top-level await, despite the .tsx extension the
 *     register names. JSX would bind either a lexical `React` or a bare
 *     "react/jsx-runtime" import at transform time, and this probe resolves
 *     React dynamically so it can run against a dep tree outside the repo.
 *     Top-level await fails under tsx while this repo has no root package.json
 *     declaring "type": "module". React.createElement inside an async main()
 *     keeps both honest.
 */

import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve as pathResolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const PROBED_AT_VERSION = "2.56.0";
const SSR_ERROR = /Missing getServerSnapshot/;

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = pathResolve(HERE, "..", "..");

type Check = { id: string; ok: boolean; label: string; detail: string };
const checks: Check[] = [];
const notes: string[] = [];

function assert(id: string, ok: boolean, label: string, detail: string): void {
  checks.push({ id, ok, label, detail });
}
function note(text: string): void {
  notes.push(text);
}
function blocked(reason: string): never {
  console.error("");
  console.error("=".repeat(78));
  console.error("PROBE STATUS: PENDING / BLOCKED — this is NOT a pass.");
  console.error("=".repeat(78));
  console.error(reason);
  console.error("");
  console.error("This probe must be re-run the moment the blocker above lifts.");
  process.exit(2);
}

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
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) walkJs(p, out);
    else if (p.endsWith(".js")) out.push(p);
  }
  return out;
}

/**
 * Balance-parse the argument list of each `useSyncExternalStore(` call.
 * A third positional argument IS getServerSnapshot, whatever it is named at
 * the call site — so count arguments, do not grep for the identifier. At 2.56.0
 * the identifier "getServerSnapshot" appears nowhere in the shipped build even
 * though aip/useChat.js does pass a third argument.
 */
function callSites(src: string): Array<{ line: number; argc: number; text: string }> {
  const sites: Array<{ line: number; argc: number; text: string }> = [];
  const needle = "useSyncExternalStore(";
  let i = 0;
  while ((i = src.indexOf(needle, i)) !== -1) {
    let depth = 0;
    let j = i + needle.length - 1;
    const args: string[] = [];
    let cur = "";
    for (; j < src.length; j++) {
      const c = src[j];
      if (c === "(" || c === "[" || c === "{") {
        depth++;
        if (depth === 1) continue;
      }
      if (c === ")" || c === "]" || c === "}") {
        depth--;
        if (depth === 0) {
          args.push(cur.trim());
          break;
        }
      }
      if (c === "," && depth === 1) {
        args.push(cur.trim());
        cur = "";
        continue;
      }
      cur += c;
    }
    sites.push({
      line: src.slice(0, i).split("\n").length,
      argc: args.filter((a) => a !== "").length,
      text: src.slice(src.lastIndexOf("\n", i) + 1, j + 1).trim(),
    });
    i = j + 1;
  }
  return sites;
}

/**
 * The modules that back the data hooks n.surface binds to. Named explicitly
 * rather than pattern-matched: a derived set would silently shrink if a file
 * were renamed, and the assertion would then pass by finding nothing.
 */
const DATA_HOOK_MODULES = [
  "new/useOsdkObjects.js",
  "new/useOsdkObject.js",
  "new/useOsdkFunction.js",
  "new/useOsdkFunctions.js",
  "new/useObjectSet.js",
  "new/useOsdkAggregation.js",
  "new/useLinks.js",
  "utils/usePlatformQuery.js",
];

const REQUIRED_HOOKS = ["useOsdkObjects", "useOsdkFunction", "useOsdkAction"] as const;

// Bound inside main(), read by the screen components below.
let osdkReact: any;
let h: any;
let objectType: any;
let queryDef: any;
let actionDef: any;

/** One screen bound to a list of objects — n.surface's screening list shape. */
function ObjectsScreen() {
  const { data, isLoading } = osdkReact.useOsdkObjects(objectType, { pageSize: 6 });
  return h("div", null, isLoading ? "loading" : String(data));
}

/** One screen bound to a function verdict — n.surface's blocking summary shape. */
function FunctionScreen() {
  const { data, isLoading } = osdkReact.useOsdkFunction(queryDef, { params: {} });
  return h("div", null, isLoading ? "loading" : String(data));
}

/** One screen recording a determination — n.surface's explicit human act. */
function ActionScreen() {
  const { applyAction, isPending } = osdkReact.useOsdkAction(actionDef);
  return h("button", { onClick: () => applyAction({}) }, isPending ? "..." : "Record determination");
}

/** Pure presentation, data supplied as values. n.surface requires this to render. */
function PureScreen({ rows }: { rows: Array<{ id: string; status: string }> }) {
  return h("ul", null, rows.map((r) => h("li", { key: r.id }, `${r.id}: ${r.status}`)));
}

async function main(): Promise<void> {
  // -------------------------------------------------------------------------
  // 0. Locate a dependency tree, or refuse and say exactly what is missing.
  // -------------------------------------------------------------------------
  const osdkReactRoot = findPkgRoot("@osdk/react");
  if (!osdkReactRoot) {
    blocked(
      "@osdk/react is not installed anywhere this probe can see.\n" +
        `Searched upward from: OSDK_PROBE_DEPS, ${REPO_ROOT}, ${HERE}, ${process.cwd()}\n` +
        "Fix: install the deps OUTSIDE this repo and set OSDK_PROBE_DEPS — see the header of this file.",
    );
  }

  const osdkClientRoot = findPkgRoot("@osdk/client");
  if (!osdkClientRoot) {
    blocked(
      "@osdk/client is not installed. It is a peer dependency of @osdk/react and is\n" +
        "required to build a real OsdkProvider, without which the useOsdkObjects\n" +
        "dimension of this probe cannot be exercised at all — useOsdkObjects calls\n" +
        "observableClient.canonicalizeOptions() synchronously and throws the\n" +
        "'No OsdkProvider found' error long before it reaches useSyncExternalStore.\n" +
        "Refusing to report a partial run as a pass.",
    );
  }

  // Anchor CJS resolution at the dependency tree, not at this file.
  const depsAnchor = join(dirname(dirname(osdkReactRoot)), "__probe_anchor__.cjs");
  const requireFromDeps = createRequire(pathToFileURL(depsAnchor));

  const osdkReactPkg = JSON.parse(readFileSync(join(osdkReactRoot, "package.json"), "utf8"));
  const INSTALLED_VERSION: string = osdkReactPkg.version;

  // -------------------------------------------------------------------------
  // A1..A3  n.surface: "the module loads outside the bundler ... A clean
  //         bundler build is not evidence." So load it under plain node.
  // -------------------------------------------------------------------------

  // Follow the package's OWN declared export map rather than guessing a path.
  const esmEntryRel: string | undefined = osdkReactPkg?.exports?.["."]?.import?.default;
  if (!esmEntryRel) {
    blocked(
      "@osdk/react package.json has no exports['.'].import.default; the probe cannot\n" +
        "name the ESM entry without inventing one.",
    );
  }
  const esmEntryAbs = join(osdkReactRoot, esmEntryRel);

  let esmLoadDetail = "";
  try {
    osdkReact = await import(pathToFileURL(esmEntryAbs).href);
    esmLoadDetail = `imported ${esmEntryRel} under plain node, no bundler`;
  } catch (e: any) {
    esmLoadDetail = `${e?.constructor?.name}: ${e?.message}`;
  }
  assert("A1", !!osdkReact, "ESM build loads outside the bundler", esmLoadDetail);
  if (!osdkReact) {
    blocked("The ESM entry would not load; every downstream assertion would be vacuous.\n" + esmLoadDetail);
  }

  let cjsExportCount = -1;
  let cjsLoadDetail = "";
  try {
    cjsExportCount = Object.keys(requireFromDeps("@osdk/react")).length;
    cjsLoadDetail = `require("@osdk/react") -> ${cjsExportCount} exports`;
  } catch (e: any) {
    cjsLoadDetail = `${e?.constructor?.name}: ${e?.message}`;
  }
  assert("A2", cjsExportCount > 0, "CJS build loads outside the bundler", cjsLoadDetail);

  // Observation, not an assertion: the package does not export "./package.json".
  // The "./*" subpath pattern rewrites it to ./build/browser/public/package.json.js,
  // so require.resolve("@osdk/react/package.json") throws MODULE_NOT_FOUND. Tooling
  // that reads a dependency's package.json by specifier will trip on this.
  try {
    requireFromDeps.resolve("@osdk/react/package.json");
    note('PACKAGING: "@osdk/react/package.json" IS resolvable (it was not at 2.56.0).');
  } catch {
    note(
      'PACKAGING: "@osdk/react/package.json" is NOT resolvable — the "./*" export ' +
        "pattern swallows it. Read the file by path, not by specifier.",
    );
  }

  const react = requireFromDeps("react");
  const { renderToString } = requireFromDeps("react-dom/server");
  h = react.createElement;

  // @osdk/client MUST be loaded through the same module system as @osdk/react,
  // i.e. ESM. Loading it via require() while @osdk/react came in as ESM creates
  // two distinct copies of the client package, and createObservableClient then
  // fails deep inside with "Cannot read properties of undefined (reading
  // 'fetch')" — a dual-package hazard that masquerades as an SSR failure and
  // would make A7/A8 pass for entirely the wrong reason.
  const osdkClientPkg = JSON.parse(readFileSync(join(osdkClientRoot, "package.json"), "utf8"));
  const clientEsmRel: string | undefined = osdkClientPkg?.exports?.["."]?.import?.default;
  if (!clientEsmRel) {
    blocked("@osdk/client package.json has no exports['.'].import.default; cannot name its ESM entry.");
  }
  const { createClient } = await import(pathToFileURL(join(osdkClientRoot, clientEsmRel)).href);

  // -------------------------------------------------------------------------
  // A4..A5  The hooks the register names exist under exactly those names.
  // -------------------------------------------------------------------------
  const missingHooks = REQUIRED_HOOKS.filter((k) => typeof osdkReact[k] !== "function");
  assert(
    "A4",
    missingHooks.length === 0,
    "useOsdkObjects / useOsdkFunction / useOsdkAction are exported under those names",
    missingHooks.length === 0
      ? `all three present; ${Object.keys(osdkReact).length} total exports`
      : `MISSING or renamed: ${missingHooks.join(", ")}. Full export list: ${Object.keys(osdkReact).sort().join(", ")}`,
  );
  if (missingHooks.length > 0) {
    blocked(
      "The named hooks are gone. The SSR assertions below would test nothing.\n" +
        "Re-derive this probe against the new names before trusting any verdict.",
    );
  }

  assert(
    "A5",
    typeof osdkReact.OsdkProvider === "function",
    "OsdkProvider is exported",
    `typeof OsdkProvider === ${typeof osdkReact.OsdkProvider}`,
  );

  // -------------------------------------------------------------------------
  // A6  STATIC EVIDENCE — argument count at every useSyncExternalStore call
  //     site in the shipped ESM build.
  // -------------------------------------------------------------------------
  const esmRoot = join(osdkReactRoot, "build", "esm");
  const arityRows: string[] = [];
  const dataHookModulesSeen = new Set<string>();
  let dataHookSitesFound = 0;
  let dataHookSitesWithServerSnapshot = 0;

  for (const file of walkJs(esmRoot)) {
    const rel = file.slice(esmRoot.length + 1).split("\\").join("/");
    for (const site of callSites(readFileSync(file, "utf8"))) {
      arityRows.push(`${rel}:${site.line} argc=${site.argc} | ${site.text}`);
      if (DATA_HOOK_MODULES.includes(rel)) {
        dataHookModulesSeen.add(rel);
        dataHookSitesFound++;
        if (site.argc >= 3) dataHookSitesWithServerSnapshot++;
      }
    }
  }
  arityRows.sort();

  const unseen = DATA_HOOK_MODULES.filter((m) => !dataHookModulesSeen.has(m));
  assert(
    "A6a",
    unseen.length === 0,
    "every named data-hook module still contains a useSyncExternalStore call site",
    unseen.length === 0
      ? `${dataHookSitesFound} call sites across all ${DATA_HOOK_MODULES.length} named modules`
      : `no call site found in: ${unseen.join(", ")} — the module layout moved; A6b may be vacuous`,
  );

  assert(
    "A6b",
    dataHookSitesFound > 0 && dataHookSitesWithServerSnapshot === 0,
    "NO data-hook call site passes a third argument (getServerSnapshot)",
    dataHookSitesWithServerSnapshot === 0
      ? `${dataHookSitesFound}/${dataHookSitesFound} data-hook call sites pass exactly 2 args`
      : `${dataHookSitesWithServerSnapshot} call site(s) now pass a server snapshot — THE LIMITATION HAS LIFTED`,
  );

  // Observation: the omission is a choice, not an oversight. The same codebase
  // passes a third argument in aip/useChat.js. Recorded, not asserted — useChat
  // is outside n.surface's surface area and may change freely.
  const chatSite = arityRows.find((r) => r.startsWith("aip/useChat.js"));
  note(
    chatSite
      ? `PRIOR ART IN-PACKAGE: ${chatSite}  <- 3 args. The library knows how; the data hooks do not do it.`
      : "PRIOR ART: aip/useChat.js call site not found in this version.",
  );

  // -------------------------------------------------------------------------
  // A7..A11  BEHAVIOURAL EVIDENCE — actually run renderToString.
  // -------------------------------------------------------------------------

  // Not a credential. An unreachable host and a dummy token string. Nothing is
  // dialled during renderToString; see the header note.
  const offlineClient = createClient(
    "https://probe.invalid",
    "ri.ontology.main.ontology.00000000-0000-0000-0000-000000000000",
    async () => "probe-token-not-a-real-credential",
  );

  objectType = { type: "object", apiName: "ProbeObject" };
  queryDef = { type: "query", apiName: "probeQuery", version: "0.0.0" };
  actionDef = { type: "action", apiName: "probeAction" };

  type RenderOutcome = { threw: boolean; message: string };
  const renderOutcome = (el: any): RenderOutcome => {
    try {
      return { threw: false, message: renderToString(el) };
    } catch (e: any) {
      return { threw: true, message: String(e?.message ?? e) };
    }
  };
  const withProvider = (Comp: any) =>
    h(osdkReact.OsdkProvider, { client: offlineClient }, h(Comp));

  const battery = () => ({
    objects: renderOutcome(withProvider(ObjectsScreen)),
    fn: renderOutcome(withProvider(FunctionScreen)),
    action: renderOutcome(withProvider(ActionScreen)),
    pure: renderOutcome(h(PureScreen, { rows: [{ id: "1b.11(a)(46)(i)", status: "unsatisfied" }] })),
  });

  const pass1 = battery();
  const pass2 = battery();

  assert(
    "A7",
    pass1.objects.threw && SSR_ERROR.test(pass1.objects.message),
    "useOsdkObjects screen: renderToString THROWS for want of getServerSnapshot",
    pass1.objects.threw ? pass1.objects.message : `DID NOT THROW — rendered: ${pass1.objects.message}`,
  );

  assert(
    "A8",
    pass1.fn.threw && SSR_ERROR.test(pass1.fn.message),
    "useOsdkFunction screen: renderToString THROWS for want of getServerSnapshot",
    pass1.fn.threw ? pass1.fn.message : `DID NOT THROW — rendered: ${pass1.fn.message}`,
  );

  // The refutation, pinned. The register said "any data-bound screen"; an
  // action-only screen is not data-bound and server-renders today. If this ever
  // starts throwing, useOsdkAction has grown an external store.
  assert(
    "A9",
    !pass1.action.threw,
    "useOsdkAction screen: renderToString SUCCEEDS (it uses no external store)",
    pass1.action.threw
      ? `NOW THROWS — useOsdkAction changed: ${pass1.action.message}`
      : `rendered: ${pass1.action.message}`,
  );

  // n.surface: "the pure presentation renders with its data supplied as values."
  assert(
    "A10",
    !pass1.pure.threw && pass1.pure.message.includes("1b.11(a)(46)(i): unsatisfied"),
    "pure presentation renders server-side with its data supplied as values",
    pass1.pure.threw ? `THREW: ${pass1.pure.message}` : `rendered: ${pass1.pure.message}`,
  );

  // MR-2 flavour: same inputs, same outcomes, within one process.
  const idempotent = JSON.stringify(pass1) === JSON.stringify(pass2);
  assert(
    "A11",
    idempotent,
    "two identical render passes produce identical outcomes (in-process)",
    idempotent ? "pass 1 === pass 2" : `pass1=${JSON.stringify(pass1)} pass2=${JSON.stringify(pass2)}`,
  );

  // -------------------------------------------------------------------------
  // Report
  // -------------------------------------------------------------------------
  const failed = checks.filter((c) => !c.ok);

  console.log("=".repeat(78));
  console.log("PREFAB PROBE — @osdk/react   (node: n.surface)");
  console.log("=".repeat(78));
  console.log(`@osdk/react installed : ${INSTALLED_VERSION}   (probe authored against ${PROBED_AT_VERSION})`);
  console.log(`react                 : ${react.version}`);
  console.log(`react-dom             : ${requireFromDeps("react-dom/package.json").version}`);
  console.log(`node                  : ${process.version}`);
  console.log(`package root          : ${osdkReactRoot}`);
  if (INSTALLED_VERSION !== PROBED_AT_VERSION) {
    console.log(`NOTE: version drift from the authored baseline (${PROBED_AT_VERSION} -> ${INSTALLED_VERSION}).`);
    console.log("      Drift alone is not a failure. The assertions below decide.");
  }
  console.log("");

  console.log("-- useSyncExternalStore call sites in the shipped ESM build --------------");
  for (const row of arityRows) console.log("   " + row);
  console.log("");

  console.log("-- observations ---------------------------------------------------------");
  for (const n of notes) console.log("   " + n);
  console.log("");

  console.log("-- assertions -----------------------------------------------------------");
  for (const c of checks) {
    console.log(`   [${c.ok ? "PASS" : "FAIL"}] ${c.id}  ${c.label}`);
    console.log(`          ${c.detail}`);
  }
  console.log("");

  // A stable digest of the load-bearing outcomes. Run this probe twice in two
  // separate processes and diff this line: identical digests mean the result is
  // reproducible, not an artefact of one process's state.
  const digest = createHash("sha256")
    .update(
      JSON.stringify({
        version: INSTALLED_VERSION,
        exports: Object.keys(osdkReact).sort(),
        arity: arityRows,
        outcomes: pass1,
      }),
    )
    .digest("hex");
  console.log(`RESULT-DIGEST ${digest}`);
  console.log("");

  if (failed.length > 0) {
    console.log("=".repeat(78));
    console.log(`PROBE RED — ${failed.length} assertion(s) failed:`);
    for (const c of failed) console.log(`   ${c.id}  ${c.label}\n        ${c.detail}`);
    console.log("");
    console.log("If A6b/A7/A8 are among them, @osdk/react has SHIPPED getServerSnapshot.");
    console.log("That is good news, not a regression. Re-open n.surface's SSR posture and");
    console.log("update build/prefabs.jsonl through the orchestrator.");
    console.log("=".repeat(78));
    process.exit(1);
  }

  console.log("=".repeat(78));
  console.log("PROBE GREEN — the limitation is still present, exactly as pinned.");
  console.log("Data-bound screens (useOsdkObjects, useOsdkFunction) cannot be server-");
  console.log("rendered. An action-only screen (useOsdkAction) can. Pure presentation");
  console.log("with data supplied as values can.");
  console.log("=".repeat(78));

  // createObservableClient leaves open handles; without this the process hangs.
  process.exit(0);
}

main().catch((e: any) => {
  console.error("");
  console.error("=".repeat(78));
  console.error("PROBE STATUS: PENDING / BLOCKED — the probe itself threw. NOT a pass.");
  console.error("=".repeat(78));
  console.error(e?.stack ?? String(e));
  process.exit(2);
});
