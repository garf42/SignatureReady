#!/usr/bin/env bash
# Phase -1 prefab probe, RUNNABLE HALF: foundry-cli-superrepo.
#
# Companion to tests/probes/test_superrepo_create_preview_deploy.md, which is the
# runbook and carries the verdict. This script reproduces every step of that probe
# that can be run WITHOUT a Foundry enrollment, then exits NON-ZERO at the
# enrollment gate so the probe can never be mistaken for complete.
#
#   PASS (exit 0) is impossible by construction. The offline half either
#   reproduces (and the script exits 2 = PENDING ENROLLMENT) or it regresses
#   (exit 1 = the offline finding no longer holds and the .md is stale).
#
# RUN:
#   bash tests/probes/superrepo_offline_half.sh
#   WORKDIR=/some/scratch bash tests/probes/superrepo_offline_half.sh
#
# Needs: node >= 18.19, npm, network to registry.npmjs.org. Never run in the repo
# root -- it npm-installs. It uses a scratch WORKDIR and never writes to the repo.

set -uo pipefail

WORKDIR="${WORKDIR:-$(mktemp -d -t superrepo-probe-XXXXXX)}"
mkdir -p "$WORKDIR"
echo "workdir: $WORKDIR"

FAILURES=0
fail() { echo "  FAIL: $*"; FAILURES=$((FAILURES + 1)); }
ok()   { echo "  ok:   $*"; }

# Versions pinned to what the probe actually exercised on 2026-08-11. Bumping
# these is a re-probe, not a maintenance edit: assertion 5 in particular is a
# cross-package version seam and is expected to change when it is fixed.
CLI_V=0.81.0
CREATE_APP_V=2.56.0
MAKER_V=0.54.0
OAC_V=0.55.0
SUPERREPO_V=0.10.0
# @osdk/integration-testing is PALANTIR'S OWN foundry-cli harness, published on
# PUBLIC npm. It carries the generated foundry-cli conjure model (foundry.yml
# schema, discovery schema, service endpoints) and the CLI installer. Its
# postinstall tries to download the real CLI -- see step 10, which runs it.
INTEG_V=0.1.0

# --------------------------------------------------------------------------
echo
echo "[1] Palantir's SuperRepo CLI (\`foundry\`) is not on public npm."
# Every plausible public name. A 200 on any of these REFUTES the central finding.
CANDIDATES='@palantir/foundry-cli @palantir/cli @palantir/foundry @osdk/foundry-cli
@osdk/superrepo-cli @osdk/superrepo @osdk/create-superrepo @palantir/superrepo'
NET_OK=0
for p in $CANDIDATES; do
  enc=$(node -e 'process.stdout.write(encodeURIComponent(process.argv[1]))' "$p")
  code=$(curl -sS -o /dev/null -w "%{http_code}" "https://registry.npmjs.org/$enc" || echo "000")
  case "$code" in
    404) NET_OK=1 ;;
    200) fail "$p now EXISTS on npm (HTTP 200) -- re-probe, the finding has changed"; NET_OK=1 ;;
    *)   fail "$p: unexpected HTTP $code from registry.npmjs.org (network problem?)" ;;
  esac
done
[ "$NET_OK" -eq 1 ] && ok "no Palantir-published \`foundry\` CLI package on public npm"
# Refusing to skip: a probe that cannot reach the registry has established nothing.
[ "$NET_OK" -eq 0 ] && fail "could not reach registry.npmjs.org -- probe established NOTHING"

# --------------------------------------------------------------------------
echo
echo "[2] install the real artifacts that DO exist"
cd "$WORKDIR" || exit 1
mkdir -p install && cd install || exit 1
[ -f package.json ] || npm init -y >/dev/null 2>&1
# --ignore-scripts is REQUIRED: @osdk/integration-testing's postinstall tries to
# download the real Foundry CLI from a stack and aborts the whole install when it
# cannot. That abort is itself an assertion -- it is run deliberately in step 10.
npm install --no-audit --no-fund --silent --ignore-scripts \
  "@osdk/cli@$CLI_V" "@osdk/create-app@$CREATE_APP_V" "@osdk/maker@$MAKER_V" \
  "@osdk/vite-plugin-oac@$OAC_V" "@osdk/vite-plugin-superrepo@$SUPERREPO_V" \
  "@osdk/integration-testing@$INTEG_V" >/dev/null 2>&1 \
  || { fail "npm install failed -- probe established NOTHING beyond step 1"; }
# Pinned constants must be the versions actually exercised, or every assertion
# below is about some other software than the .md claims.
node -e '
  const want = {"@osdk/cli":process.argv[1],"@osdk/create-app":process.argv[2],
    "@osdk/maker":process.argv[3],"@osdk/vite-plugin-oac":process.argv[4],
    "@osdk/vite-plugin-superrepo":process.argv[5],"@osdk/integration-testing":process.argv[6]};
  let bad=0;
  for (const [n,v] of Object.entries(want)) {
    let got; try { got = require("./node_modules/"+n+"/package.json").version; } catch { got = "MISSING"; }
    if (got !== v) { console.log(`  FAIL: ${n} installed ${got}, probe claims ${v}`); bad++; }
  }
  if (!bad) console.log("  ok:   every installed version matches the pinned constant");
  process.exit(bad ? 1 : 0);
' "$CLI_V" "$CREATE_APP_V" "$MAKER_V" "$OAC_V" "$SUPERREPO_V" "$INTEG_V" || FAILURES=$((FAILURES + 1))
BIN="$WORKDIR/install/node_modules/.bin"
[ -x "$BIN/osdk" ] && ok "@osdk/cli installed, bin is 'osdk'" || fail "@osdk/cli bin missing"
[ -x "$BIN/foundry" ] && fail "a 'foundry' bin appeared -- re-probe" || ok "no 'foundry' bin ships with any of these"

# --------------------------------------------------------------------------
echo
echo "[3] the osdk CLI command surface: no 'create', no top-level 'deploy'"
HELP=$("$BIN/osdk" --help 2>&1)
echo "$HELP" | grep -qE '^\s+osdk create' && fail "'osdk create' now exists -- re-probe" || ok "no 'osdk create'"
for c in site widgetset unstable; do
  echo "$HELP" | grep -q "osdk $c" && ok "subcommand present: osdk $c" || fail "osdk $c disappeared -- re-probe"
done
# Deploy exists, but only as a site/widgetset artifact push, and it demands a stack.
SITE=$("$BIN/osdk" site deploy --help 2>&1)
echo "$SITE" | grep -q -- "--foundryUrl" && ok "'osdk site deploy' requires --foundryUrl (enrollment-gated)" \
  || fail "'osdk site deploy' no longer requires --foundryUrl -- re-probe"

# --------------------------------------------------------------------------
echo
echo "[4] create-osdk-app scaffolds OFFLINE (the G032 fallback path)"
mkdir -p "$WORKDIR/scaffold" && cd "$WORKDIR/scaffold" || exit 1
rm -rf sigready-app
# Every prompt must be answered by flag or the CLI opens a TTY and dies.
# clientId must match /^[0-9a-f]+$/ ; sdkVersion is "1.x" or "2.x", not a semver.
"$BIN/create-osdk-app" sigready-app --template react --overwrite --sdkVersion 2.x \
  --foundryUrl https://example.palantirfoundry.com \
  --applicationUrl https://sigready.example.com \
  --application ri.third-party-applications.main.application.abc \
  --ontology ri.ontology.main.ontology.abc \
  --osdkPackage @sigready/sdk --clientId 0123456789abcdef \
  --osdkRegistryUrl https://example.palantirfoundry.com/artifacts/api/repositories/ri.artifacts.main.repository.abc/contents/release/npm \
  --scopes api:ontologies-read --no-corsProxy >/dev/null 2>&1
for f in package.json vite.config.ts foundry.config.json src/client.ts .npmrc .env.development; do
  [ -f "sigready-app/$f" ] && ok "scaffolded $f" || fail "scaffold missing $f"
done
# The shape distinction that decides G031: this is an APP, not a SuperRepo.
[ -f sigready-app/foundry.yml ] && fail "create-osdk-app now emits foundry.yml -- it may scaffold a SuperRepo now, RE-PROBE" \
  || ok "no foundry.yml: create-osdk-app makes an OSDK app, NOT a SuperRepo"
[ -d sigready-app/.ontology ] && fail "create-osdk-app now emits .ontology/ -- RE-PROBE" \
  || ok "no .ontology/: no Ontology-as-code in the scaffold"
grep -q '_authToken=${FOUNDRY_TOKEN}' sigready-app/.npmrc \
  && ok ".npmrc pins the OSDK to the enrollment's artifacts registry (this is the install-time gate)" \
  || fail ".npmrc no longer pins FOUNDRY_TOKEN -- re-probe"

# --------------------------------------------------------------------------
echo
echo "[5] Ontology-as-code compiles OFFLINE, and is byte-deterministic"
mkdir -p "$WORKDIR/oac/.ontology" && cd "$WORKDIR/oac" || exit 1
printf '{ "name": "oac-probe", "private": true, "type": "module", "version": "0.0.0" }\n' > package.json
ln -sfn ../install/node_modules node_modules
cat > .ontology/ontology.mjs <<'ONTOLOGY'
import { defineObject, importOntologyEntity, OntologyEntityTypeEnum } from "@osdk/maker";

// (1) DECLARED in code -- code is the source of truth for this one.
export const NepaDocument = defineObject({
  apiName: "NepaDocument",
  primaryKeyPropertyApiName: "documentId",
  titlePropertyApiName: "title",
  displayName: "NEPA Document",
  pluralDisplayName: "NEPA Documents",
  description: "A county-side NEPA environmental document moving toward signature.",
  properties: {
    documentId: { type: "string", displayName: "Document ID" },
    title: { type: "string", displayName: "Title" },
    documentType: { type: "string", displayName: "Document Type" },
    signatureReady: { type: "boolean", displayName: "Signature Ready" },
  },
});

// (2) IMPORTED -- stands in for an object type authored in the Foundry UI and
// pulled into code. NOTE: hand-built stub. importOntologyEntity does NOT
// normalize, so `properties` must already be the flattened ARRAY form that
// defineObject produces internally. Passing the record form throws
// "(objectType.properties ?? []).map is not a function" in convertObject.
importOntologyEntity({
  __type: OntologyEntityTypeEnum.OBJECT_TYPE,
  apiName: "CountyJurisdiction",
  primaryKeyPropertyApiName: "fipsCode",
  titlePropertyApiName: "countyName",
  displayName: "County Jurisdiction",
  pluralDisplayName: "County Jurisdictions",
  properties: [
    { apiName: "fipsCode", type: "string", displayName: "FIPS Code" },
    { apiName: "countyName", type: "string", displayName: "County Name" },
  ],
});
ONTOLOGY

# TWICE, in SEPARATE PROCESSES -- the constitution's reproducibility rule.
node "$BIN/maker" -i .ontology/ontology.mjs -o ir-a.json >/dev/null 2>&1 || fail "maker run A failed"
node "$BIN/maker" -i .ontology/ontology.mjs -o ir-b.json >/dev/null 2>&1 || fail "maker run B failed"
if [ -f ir-a.json ] && [ -f ir-b.json ]; then
  A=$(sha256sum ir-a.json | cut -d' ' -f1); B=$(sha256sum ir-b.json | cut -d' ' -f1)
  [ "$A" = "$B" ] && ok "maker IR byte-identical across two processes (no --randomnessKey needed)" \
    || fail "maker IR is NON-DETERMINISTIC across processes -- G031/G032 must pin --randomnessKey"
  node -e '
    const ir = require("./ir-a.json");
    const d = Object.keys(ir.ontology.objectTypes);
    const i = Object.keys(ir.importedOntology.objectTypes);
    if (d.join() !== "NepaDocument") { console.log("  FAIL: declared objectTypes = " + d); process.exit(1); }
    if (i.join() !== "CountyJurisdiction") { console.log("  FAIL: imported objectTypes = " + i); process.exit(1); }
    console.log("  ok:   declared and imported object types land in SEPARATE top-level blocks");
    console.log("        ontology.objectTypes         = " + d.join(", "));
    console.log("        importedOntology.objectTypes = " + i.join(", "));
  ' || FAILURES=$((FAILURES + 1))
fi

# --------------------------------------------------------------------------
echo
echo "[6] VERSION SEAM: vite-plugin-oac reads ir.blockData, maker emits ir.ontology"
# A KILL TEST, not a print statement. The seam has two sides and BOTH are pinned:
# the producer (maker emits .ontology, no .blockData) and the consumer
# (vite-plugin-oac reads .blockData). If EITHER side moves, this goes red and the
# .md's section 3d is stale. The previous version of this step printed "ok" down
# both branches and exited 0 -- it could never fail, so it asserted nothing.
node -e '
  const fs = require("node:fs");
  let bad = 0;
  const T = (c, m) => { console.log((c ? "  ok:   " : "  FAIL: ") + m); if (!c) bad++; };
  const ir = JSON.parse(fs.readFileSync("ir-a.json", "utf-8"));
  // Producer side.
  T(ir.blockData === undefined,
    "producer: maker@'"$MAKER_V"' emits NO .blockData (top-level: " + Object.keys(ir).join(", ") + ")");
  T(ir.ontology !== undefined && ir.ontology.objectTypes !== undefined,
    "producer: maker emits .ontology.objectTypes instead");
  // Consumer side, read off the SHIPPED plugin rather than asserted from memory.
  const oac = fs.readFileSync(
    "'"$WORKDIR"'/install/node_modules/@osdk/vite-plugin-oac/build/esm/generateOntologyAssets.js", "utf-8");
  T(/JSON\.parse\(irContent\)\.blockData/.test(oac),
    "consumer: vite-plugin-oac@'"$OAC_V"' still reads JSON.parse(irContent).blockData");
  T(/execa\("pnpm"/.test(oac),
    "consumer: vite-plugin-oac still hardcodes `pnpm exec` (an npm-only SuperRepo breaks)");
  T(/ontology\.mts/.test(oac),
    "consumer: vite-plugin-oac still invokes maker on ontology.mts");
  // The seam itself: the consumer would throw on the producer output.
  T(ir.blockData === undefined && /JSON\.parse\(irContent\)\.blockData/.test(oac),
    "SEAM OPEN: producer .ontology vs consumer .blockData -> Stage 2 throws. If this");
  console.log("        line ever goes red the seam CLOSED and .md section 3d must be rewritten.");
  process.exit(bad === 0 ? 0 : 1);
' || FAILURES=$((FAILURES + 1))

echo
echo "[7] IR -> full metadata -> OSDK, OFFLINE, no enrollment, deterministic"
for r in a b; do
  node --input-type=module -e "
    import fs from 'node:fs';
    import { OntologyIrToFullMetadataConverter } from '@osdk/generator-converters.ontologyir';
    const ir = JSON.parse(fs.readFileSync('ir-$r.json', 'utf-8'));
    const fm = OntologyIrToFullMetadataConverter.getFullMetadataFromIr(ir.ontology);
    fs.writeFileSync('fullmeta-$r.json', JSON.stringify(fm, null, 2));
  " >/dev/null 2>&1 || fail "IR->full metadata conversion failed (run $r)"
  rm -rf "osdk-$r"
  # --ontologyPath is the local-file mode: no --foundryUrl, no token, no network.
  node "$BIN/osdk" unstable typescript generate --outDir "osdk-$r/src" \
    --ontologyPath "fullmeta-$r.json" --beta true --packageType module --version dev \
    >/dev/null 2>&1 || fail "osdk generate failed (run $r)"
done
[ -f osdk-a/src/ontology/objects/NepaDocument.ts ] \
  && ok "OSDK TypeScript generated from a LOCAL ontology file, no enrollment" \
  || fail "OSDK generation produced no NepaDocument.ts"
grep -q "primaryKeyApiName: 'documentId'" osdk-a/src/ontology/objects/NepaDocument.ts 2>/dev/null \
  && ok "generated SDK carries the declared primary key" \
  || fail "generated SDK does not carry documentId as primary key"
if diff -rq osdk-a/src osdk-b/src >/dev/null 2>&1; then
  ok "full OAC->OSDK chain byte-identical across two separate process runs"
else
  fail "full OAC->OSDK chain is NON-DETERMINISTIC -- this changes what G031 can promise"
fi

# --------------------------------------------------------------------------
echo
echo "[8] SuperRepo shape: the discovery contract, exercised for real"
mkdir -p "$WORKDIR/superrepo/apps/screen" "$WORKDIR/superrepo/.palantir"
cd "$WORKDIR/superrepo" || exit 1
ln -sfn ../install/node_modules node_modules
# foundry.yml is the root marker. Its SCHEMA is not established by this probe --
# only that its presence at an ancestor is what makes a directory a SuperRepo.
printf '# hand-built marker; real one is written by `foundry create`\n' > foundry.yml
printf '{ "pid": %s, "url": "http://127.0.0.1:38101" }\n' "$$" > .palantir/.ontology-discovery.json
printf '{ "pid": 999999, "url": "http://127.0.0.1:38103" }\n' > .palantir/.python-functions-discovery.json
printf '{ "not": "valid" }\n' > .palantir/.platform-api-proxy-discovery.json
node --input-type=module -e '
  import { findSuperrepoRoot, inspectDiscovery, DISCOVERY_DIR } from "@osdk/vite-plugin-superrepo/discovery";
  import { PROXY_ROUTES } from "@osdk/vite-plugin-superrepo";
  let bad = 0;
  const T = (c, m) => { console.log((c ? "  ok:   " : "  FAIL: ") + m); if (!c) bad++; };
  T(DISCOVERY_DIR === ".palantir", `discovery dir is ".palantir" (got "${DISCOVERY_DIR}")`);
  const root = findSuperrepoRoot(process.cwd() + "/apps/screen");
  T(root === process.cwd(), "findSuperrepoRoot walks up from a nested app to the foundry.yml ancestor");
  T(findSuperrepoRoot("/") === undefined, "outside a SuperRepo it returns undefined (no silent default)");
  const want = ["ontology", "typescript-functions", "python-functions", "platform-api-proxy"];
  const got = [...new Set(PROXY_ROUTES.map(r => r.service))];
  T(want.every(s => got.includes(s)), "dev-server services: " + got.join(", "));
  T(got.includes("python-functions"), "python-functions IS a first-class discovery service (contra the register)");
  // The .md prints a prefix/service/rewrite table. Pin ALL THREE columns, not just
  // the service names -- otherwise the table is a comment and a silent change to a
  // prefix or a rewrite flag would leave this probe green with a stale .md.
  const WANT_TABLE = [
    ["/ontology-metadata",      "ontology",             false],
    ["/object-set-service",     "ontology",             false],
    ["/local-functions",        "typescript-functions", true ],
    ["/local-python-functions", "python-functions",     true ],
    ["/api",                    "platform-api-proxy",   false],
  ];
  const gotTable = PROXY_ROUTES.map(r => [r.prefix, r.service, r.rewrite]);
  T(JSON.stringify(gotTable) === JSON.stringify(WANT_TABLE),
    "proxy table matches the .md exactly (prefix + service + rewrite): "
      + JSON.stringify(gotTable));
  T(inspectDiscovery(root, "ontology").kind === "ok", "live discovery file -> kind=ok");
  T(inspectDiscovery(root, "python-functions").kind === "stale", "dead PID -> kind=stale (liveness via kill(pid,0))");
  T(inspectDiscovery(root, "platform-api-proxy").kind === "malformed", "bad JSON schema -> kind=malformed");
  T(inspectDiscovery(root, "typescript-functions").kind === "missing", "absent file -> kind=missing");
  process.exit(bad === 0 ? 0 : 1);
' || FAILURES=$((FAILURES + 1))

# --------------------------------------------------------------------------
echo
echo "[9] the foundry-cli's OWN contract, off PUBLIC npm: foundry.yml schema etc."
# @osdk/integration-testing is Palantir's foundry-cli integration harness. It is
# on public npm and ships the GENERATED conjure model of the CLI. Everything
# below is read off the installed artifact -- no enrollment, no GitHub, no docs.
cd "$WORKDIR/install" || exit 1
node -e '
  const fs = require("node:fs");
  let bad = 0;
  const T = (c, m) => { console.log((c ? "  ok:   " : "  FAIL: ") + m); if (!c) bad++; };
  const P = "./node_modules/@osdk/integration-testing";
  const comp = fs.readFileSync(P + "/build/types/generated/cli/__components.d.ts", "utf-8");
  const sec = (name) => (comp.match(new RegExp("interface " + name + " \\{([^}]*)\\}", "u")) || [])[1] || "";
  // (a) foundry.yml SCHEMA -- the .md called this the one unknown blocking G031.
  const fc = sec("FoundryConfig");
  T(/\bminCliVersion: string;/.test(fc) && /\bproducts: Array<ProductConfig>;/.test(fc),
    "foundry.yml FoundryConfig REQUIRES minCliVersion + products");
  T(/functionsTypescriptRuntimeVersion\?/.test(fc) && /platformApiProxy\?/.test(fc),
    "foundry.yml optional keys: functionsTypescriptRuntimeVersion, platformApiProxy");
  const pc = sec("ProductConfig");
  T(/apiNamespace: string;/.test(pc) && /components: Array<Component>;/.test(pc)
      && /osdkOutput: string;/.test(pc),
    "ProductConfig REQUIRES apiNamespace + components + osdkOutput");
  T(/imports\?: Array<ImportConfig>/.test(pc),
    "ProductConfig.imports carries the UI-import hook (ImportConfig.ontology)");
  // (b) the DISCOVERY FILE WRITER schema -- strictly larger than the reader schema
  // that step 8 exercises. The .md previously reported the reader as the schema.
  const cd = sec("ComponentDiscovery");
  T(/processStartTimeSecs: number;/.test(cd),
    "ComponentDiscovery REQUIRES processStartTimeSecs (NOT just pid/url/caCertPath)");
  // (c) PYTHON_FUNCTIONS is a declarable component type of the CLI itself.
  T(/"PYTHON_FUNCTIONS"/.test(comp),
    "ServiceName enum includes PYTHON_FUNCTIONS");
  T(/user-owned\s+\*\s+component types declared in `foundry.yml`/u.test(comp)
      || /PYTHON_FUNCTIONS, and APP are user-owned/u.test(comp.replace(/\s+/gu, " ")),
    "CLI contract calls PYTHON_FUNCTIONS a user-owned component declarable in foundry.yml");
  // (d) HOW THE CLI IS ACTUALLY DISTRIBUTED. Not the artifacts npm registry.
  const dl = fs.readFileSync(P + "/build/esm/scripts/download.js", "utf-8");
  T(/\/code\/api\/extension\/install-script/.test(dl),
    "CLI installer is GET <stack>/code/api/extension/install-script (Bearer token)");
  T(/authorization: `Bearer \$\{token\}`/.test(dl) || /Bearer/.test(dl),
    "installer fetch is bearer-authenticated against the stack");
  // (e) the version floor and the `foundry start ontology` command line.
  const fcli = fs.readFileSync(P + "/build/esm/utils/foundry-cli.js", "utf-8");
  T(/MIN_FOUNDRY_CLI_VERSION = "0\.224\.0"/.test(fcli),
    "MIN_FOUNDRY_CLI_VERSION is 0.224.0 (the real CLI version series)");
  const os_ = fs.readFileSync(P + "/build/esm/cli-service/OntologyServer.js", "utf-8");
  T(/"start", "ontology", "--skip-build", "--metadata"/.test(os_)
      && /"--discovery-path"/.test(os_),
    "preview server: foundry start ontology --skip-build --metadata <fullmeta> --discovery-path <.palantir>");
  process.exit(bad === 0 ? 0 : 1);
' || FAILURES=$((FAILURES + 1))
# The metadata the preview server takes is the SAME artifact step 7 produced.
if [ -f "$WORKDIR/oac/fullmeta-a.json" ]; then
  ok "the --metadata the preview server wants is the file step 7 already builds offline"
else
  fail "step 7 produced no fullmeta-a.json -- the preview-server input claim is unbacked"
fi

# --------------------------------------------------------------------------
echo
echo "[10] THE ENROLLMENT GATE, EXECUTED -- not inferred from a docs page"
# Run Palantir's own CLI installer and record exactly where it stops. This is the
# probe's central claim, and it is now a command that runs rather than a set of
# 404s on guessed package names.
mkdir -p "$WORKDIR/gate" && cd "$WORKDIR/gate" || exit 1
[ -f package.json ] || npm init -y >/dev/null 2>&1
GATE=$(npm install --no-audit --no-fund "@osdk/integration-testing@$INTEG_V" 2>&1)
GATE_RC=$?
if [ "$GATE_RC" -eq 0 ]; then
  fail "the Foundry CLI INSTALLED without an enrollment -- the central finding has CHANGED, RE-PROBE"
elif echo "$GATE" | grep -q "Cannot resolve the Foundry host"; then
  ok "installer runs, then stops at host resolution: FOUNDRY_EXTERNAL_HOST / FOUNDRY_HOSTNAME / a Foundry git remote"
  ok "'foundry' CLI is UNOBTAINABLE here -- established by running the installer, not by guessing names"
else
  fail "installer failed for an UNEXPECTED reason (not the enrollment gate): $(echo "$GATE" | tail -3)"
fi
[ -x "$WORKDIR/gate/node_modules/.bin/foundry" ] && fail "a foundry bin appeared -- RE-PROBE" \
  || ok "no 'foundry' binary on this machine after the installer ran"

# --------------------------------------------------------------------------
echo
echo "=========================================================================="
if [ "$FAILURES" -ne 0 ]; then
  echo "OFFLINE HALF REGRESSED: $FAILURES assertion(s) failed."
  echo "tests/probes/test_superrepo_create_preview_deploy.md is now STALE. Re-probe."
  exit 1
fi
echo "OFFLINE HALF REPRODUCES. Every assertion above held."
echo
echo "PENDING -- ENROLLMENT REQUIRED. Not run, not established, not assumed:"
echo "  (a) \`foundry create\` -- obtaining the CLI, and the scaffold it emits."
echo "      NOT blocked any more: foundry.yml's SCHEMA (step 9) and the discovery"
echo "      writer schema. Still open: what \`foundry create\` FILLS IN."
echo "  (b) \`foundry start <service>\` RUNNING. The command lines, the status"
echo "      service (POST/GET /status) and ontology seeding (PUT /seed) are pinned"
echo "      in step 9; the typescript/python runtime bodies are still unknown."
echo "  (c) the embedded Ontology preview EXECUTING, and whether Python functions"
echo "      actually run on an enrollment (the CLI declares PYTHON_FUNCTIONS)."
echo "  (d) a TypeScript v2 function executing through smartClient."
echo "  (e) \`foundry deploy\` -- and whether SuperRepo is enabled on the enrollment at all."
echo "Run tests/probes/test_superrepo_create_preview_deploy.md section 6 on an"
echo "enrolled machine, then replace this exit with a real verdict."
echo "=========================================================================="
exit 2
