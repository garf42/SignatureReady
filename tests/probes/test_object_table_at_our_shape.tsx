/**
 * PHASE -1 PREFAB PROBE — @osdk/react-components  (used_by: n.surface)
 * ============================================================================
 * gap: G022 (currently assumes hand-built)
 * probe_dims: ONE list of 6 required elements, each row carrying
 *             (a) a constrained select, (b) a one-line free-text justification,
 *             (c) 2 evidence links.
 *
 * THE REGISTER'S CLAIM
 * --------------------
 *   "no prior evidence. Buy-before-build candidate for the one repeated
 *    component. If ObjectTable cannot host a constrained select plus a
 *    free-text justification per row, the prebuilt path costs more than it
 *    saves."
 *
 * VERDICT: the claim's premise is REFUTED, and G022's hand-built default
 * SURVIVES anyway — for a different reason than the register guessed.
 *
 *   ObjectTable CAN host all three. (a) constrained select, (b) free-text
 *   justification, (c) two evidence links all type-check clean against the
 *   shipped .d.ts at our exact 6-element shape. The register's stated
 *   disqualifier does not fire.
 *
 *   What disqualifies `ObjectTable` is a thing the register never asked about:
 *   `objectType` is a REQUIRED prop (A7). ObjectTable is hard-wired to
 *   `useOsdkObjects`/`useObjectSet` and fetches its own rows from a live
 *   Foundry ontology. It cannot be handed 6 rows. Our 6 required elements are
 *   a fixed checklist, not an object set, and this build has no Foundry
 *   enrollment.
 *
 *   The real find is the escape hatch: `BaseTable` is exported from the same
 *   subpath, is generic over ANY row type, and hosts our full shape — 6 static
 *   rows, constrained dropdown, validated one-line justification, two links —
 *   with no ontology and no OSDK client (A11). That is a genuine partial buy.
 *
 * WHAT THE "BUY" ACTUALLY BUYS, AND WHAT IT DOES NOT
 * --------------------------------------------------
 *   BUYS:      the grid, virtualization, the DROPDOWN cell editor, the text
 *              cell editor, per-cell async validation with error tooltips, the
 *              edit-mode footer (Edit / Cancel / Submit + modification count).
 *   DOES NOT:  write-back. The table NEVER calls a Foundry action (A9). It
 *              collects edits and hands you `CellEditInfo[]`; you write the
 *              persistence yourself either way.
 *   DOES NOT:  bind the select to an ontology value set. `DropdownEditConfig`
 *              takes a caller-supplied `items: V[]` at `V = unknown`. Numbers
 *              type-check as items for a string property (A8). The "constrained"
 *              select is constrained by your array at runtime and by nothing at
 *              compile time. Nothing in the package reads `valueTypeApiName`.
 *
 * THE PRICE: 194 KB gzipped (611 KB minified), React excluded, for the
 * object-table subpath alone. For one 6-row checklist. Measured, not guessed
 * — see the OPTIONAL BUNDLE WEIGHT section below.
 *
 * BUY-OR-BUILD AT THIS SHAPE: BUILD. 6 rows need no virtualization, no
 * infinite scroll, no column config, no pinning or resizing — which is what
 * the 194 KB is mostly for. You still hand-write the write-back and the value
 * set either way. Taking `BaseTable` means also taking @tanstack/react-table,
 * @base-ui/react, @dnd-kit/*, and a peer floor of @osdk/api + @osdk/client +
 * @osdk/react at ^2.8.0, plus a `0.x` beta-tagged package that shipped 449
 * versions and moved 0.43 -> 0.48 in three weeks. G022's hand-built default
 * STANDS. Revisit only if n.surface grows a second, larger, ontology-backed
 * table — then ObjectTable earns its weight and this file's A7 stops mattering.
 *
 * These assertions are written to FAIL WHEN THE LIBRARY CHANGES. A red run is
 * not automatically bad news — read the failure line:
 *   - A7 red  => `objectType` became optional. ObjectTable can now take local
 *                rows; re-open the buy decision.
 *   - A8 red  => dropdown items became type-bound. The select is now genuinely
 *                constrained by the compiler; that is a real gain.
 *   - A9 red  => the table learned to apply actions itself. Write-back is no
 *                longer yours to write; re-open the buy decision.
 *   - A5 red  => a free-text field component was added, or DROPDOWN was
 *                removed/renamed.
 *   - A11 red => the BaseTable escape hatch closed. The only path back in is a
 *                live ontology. CHECK A11a FIRST: if A11a is also red the cause is
 *                a TanStack major swap, not the escape hatch.
 *   - A11a red=> @osdk/react-components moved off TanStack v8. Any consumer app on
 *                a different TanStack major cannot pass BaseTable a `table` at all.
 *   - A6 red  => our shape stopped compiling. Read the captured diagnostic.
 *   - A6c red => renderCell became property-checked. That is a GAIN, not a loss.
 *   - A12css red => the mandatory stylesheet grew. The price is JS + this CSS.
 *
 * HOW TO RUN
 * ----------
 *   1. Install the deps somewhere (NEVER inside this repo):
 *        mkdir -p /tmp/osdk-ct && cd /tmp/osdk-ct && npm init -y
 *        npm install @osdk/react-components@0.48.0 @osdk/foundry.admin \
 *          react@18 react-dom@18 @types/react@18 @types/react-dom@18 \
 *          typescript tsx
 *        # Do NOT add `@tanstack/react-table` to that line. @osdk/react-components
 *        # pins ^8.21.3 itself; `npm i @tanstack/react-table` installs v9, which
 *        # renamed useReactTable/getCoreRowModel and turned A11 red for a reason
 *        # unrelated to the escape hatch. A11 now resolves the library's own copy
 *        # explicitly and A11a pins the major, so this is belt-and-braces.
 *        # optional, only for the bundle-weight section:
 *        npm install esbuild
 *   2. Point the probe at that install and run it:
 *        OSDK_PROBE_DEPS=/tmp/osdk-ct \
 *          npx --prefix /tmp/osdk-ct tsx \
 *          /home/user/SignatureReady/tests/probes/test_object_table_at_our_shape.tsx
 *
 *   Run it TWICE in two separate processes and diff the RESULT-DIGEST line:
 *        for i in 1 2; do <cmd> > run$i.txt 2>&1; done; diff run1.txt run2.txt
 *
 * EXIT CODES
 * ----------
 *   0  every assertion held AND every assertion actually ran.
 *   1  an assertion failed: the library changed. READ THE FAILURE LINE.
 *   2  PENDING/BLOCKED: the probe could not run (deps missing, no tsc, etc), OR
 *      it ran but SKIPPED one or more assertions. A skipped assertion is not a
 *      held assertion — a run with skips must never report itself green, because
 *      A11 (the escape hatch) and A12 (the price) are both skippable and both are
 *      load-bearing for the verdict. Never a pass.
 *
 * NOTES FOR WHOEVER RUNS THIS NEXT
 * --------------------------------
 *   - No Foundry enrollment is needed and none was available. Every assertion
 *     here is a type-level or shipped-artifact fact. This probe deliberately
 *     does NOT render ObjectTable: rendering it requires a live ontology and an
 *     OsdkProvider, and the sibling probe test_osdk_react_module_load.tsx
 *     already pins that useOsdkObjects throws under renderToString. A7 below
 *     records the ontology requirement statically instead, which is the fact
 *     that actually drives the buy decision.
 *   - typescript@7 ships the native port. `require("typescript")` no longer
 *     exposes ts.createProgram / ts.sys / ts.getPreEmitDiagnostics (all
 *     `undefined` on 7.0.2). This probe therefore SPAWNS the `tsc` binary
 *     rather than using the JS API. Do not "modernize" it back to
 *     ts.createProgram without checking that the API exists again.
 *   - The package's ESM build imports CSS Modules (`Table.module.css`), so a
 *     bare `node --import tsx` of the library throws ERR_UNKNOWN_FILE_EXTENSION.
 *     Runtime assertions here bundle through esbuild with `--loader:.css=empty`
 *     first, and are SKIPPED (not failed) when esbuild is absent.
 *   - Deliberately no JSX and no top-level await, despite the .tsx extension the
 *     register names — same reasoning as the sibling probe. All React usage
 *     lives inside fixture SOURCE STRINGS, which are compiled, never executed.
 */

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, resolve as pathResolve } from "node:path";
import { fileURLToPath } from "node:url";

// ---------------------------------------------------------------------------
// harness
// ---------------------------------------------------------------------------

const HERE = dirname(fileURLToPath(import.meta.url));
const DEPS = pathResolve(process.env.OSDK_PROBE_DEPS ?? join(HERE, "..", ".."));
const NM = join(DEPS, "node_modules");
const PKG = "@osdk/react-components";
const SUBPATH = "@osdk/react-components/experimental/object-table";

const lines: string[] = [];
let failures = 0;
let skipped = 0;

function log(s: string): void {
  lines.push(s);
  console.log(s);
}

function pending(why: string): never {
  log("");
  log("PENDING/BLOCKED — the probe did not run. This is NOT a pass.");
  log("  reason: " + why);
  log("  fix: install the deps and set OSDK_PROBE_DEPS (see header).");
  process.exit(2);
}

function assert(id: string, ok: boolean, claim: string, got: string): void {
  if (ok) {
    log("  PASS " + id + "  " + claim);
  } else {
    failures++;
    log("  FAIL " + id + "  " + claim);
    log("       got: " + got);
  }
}

function skip(id: string, claim: string, why: string): void {
  skipped++;
  log("  SKIP " + id + "  " + claim + "  (" + why + ")");
}

// ---------------------------------------------------------------------------
// preflight
// ---------------------------------------------------------------------------

if (!existsSync(NM)) pending("no node_modules at " + NM);

const pkgJsonPath = join(NM, PKG, "package.json");
if (!existsSync(pkgJsonPath)) pending("cannot find " + PKG + " at " + pkgJsonPath);

const pkgJson = JSON.parse(readFileSync(pkgJsonPath, "utf8"));
const VERSION: string = pkgJson.version;

const TSC = join(NM, ".bin", "tsc");
if (!existsSync(TSC)) pending("no tsc binary at " + TSC + " (npm i typescript)");

const FIXDIR = join(DEPS, ".probe-fixtures-object-table");
rmSync(FIXDIR, { recursive: true, force: true });
mkdirSync(FIXDIR, { recursive: true });

log("PROBE  @osdk/react-components ObjectTable at our shape (G022)");
log("  package        " + PKG + "@" + VERSION);
log("  deps root      " + DEPS);
log("  node           " + process.version);

function depVersion(name: string): string {
  try {
    return JSON.parse(readFileSync(join(NM, name, "package.json"), "utf8")).version;
  } catch {
    return "ABSENT";
  }
}
for (const d of ["@osdk/api", "@osdk/client", "@osdk/react", "react", "typescript", "@tanstack/react-table"]) {
  log("  dep            " + d + " " + depVersion(d));
}

// ---------------------------------------------------------------------------
// type-check helper: write a fixture, spawn tsc, return diagnostics
// ---------------------------------------------------------------------------

/**
 * The object type definition every fixture shares: our 6 signature elements as
 * a Foundry object type. Declared by hand so the probe needs no generated OSDK
 * and no ontology.
 */
const OBJECT_TYPE_PRELUDE = `
import type { ObjectTypeDefinition, PropertyDef } from "@osdk/api";
export interface SigElement extends ObjectTypeDefinition {
  type: "object"; apiName: "SigElement";
  primaryKeyApiName: "elementId"; primaryKeyType: "string";
  __DefinitionMetadata: {
    type: "object"; apiName: "SigElement"; displayName: "Signature Element";
    description: undefined; primaryKeyApiName: "elementId";
    titleProperty: "elementId"; primaryKeyType: "string";
    rid: "ri.ontology.main.object-type.sig-element";
    pluralDisplayName: "Signature Elements";
    icon: undefined; visibility: undefined; status: undefined;
    links: {}; interfaceMap: {}; inverseInterfaceMap: {};
    properties: {
      elementId:    PropertyDef<"string", "non-nullable", "single">;
      elementLabel: PropertyDef<"string", "non-nullable", "single">;
      determination: PropertyDef<"string", "nullable", "single">;
      justification: PropertyDef<"string", "nullable", "single">;
      evidenceUrl1: PropertyDef<"string", "nullable", "single">;
      evidenceUrl2: PropertyDef<"string", "nullable", "single">;
    };
  };
}
export const SigElement = { type: "object", apiName: "SigElement" } as SigElement;
`;

interface TscResult {
  ok: boolean;
  out: string;
}

function typecheck(name: string, source: string, paths?: Record<string, string[]>): TscResult {
  const dir = join(FIXDIR, name);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "prelude.ts"), OBJECT_TYPE_PRELUDE, "utf8");
  writeFileSync(join(dir, "fixture.tsx"), source, "utf8");
  writeFileSync(
    join(dir, "tsconfig.json"),
    JSON.stringify(
      {
        compilerOptions: {
          strict: true,
          noEmit: true,
          target: "ES2022",
          module: "preserve",
          moduleResolution: "bundler",
          jsx: "react-jsx",
          skipLibCheck: true,
          types: [],
          // NOTE: no `baseUrl` — typescript@7 removed it (TS5102). The path
          // mappings below are absolute, so none is needed.
          ...(paths ? { paths } : {}),
        },
        include: ["fixture.tsx"],
      },
      null,
      2,
    ),
    "utf8",
  );
  const r = spawnSync(TSC, ["-p", join(dir, "tsconfig.json")], {
    encoding: "utf8",
    cwd: dir,
  });
  const out = ((r.stdout ?? "") + (r.stderr ?? "")).trim();
  return { ok: r.status === 0, out };
}

// ---------------------------------------------------------------------------
// SECTION 1 — does the package exist, and where does ObjectTable live?
// ---------------------------------------------------------------------------

log("");
log("SECTION 1  package identity and export surface");

const exportKeys = Object.keys(pkgJson.exports ?? {});

assert(
  "A1",
  typeof VERSION === "string" && VERSION.length > 0,
  "@osdk/react-components is published and installed",
  "version=" + String(VERSION),
);

assert(
  "A2",
  exportKeys.includes("./experimental/object-table"),
  "ObjectTable lives at the ./experimental/object-table subpath",
  "exports=" + JSON.stringify(exportKeys),
);

// Pinned because it is a stability signal, not decoration: the component this
// build would depend on is behind an `experimental/` door in a 0.x package.
assert(
  "A3",
  !exportKeys.includes("./object-table") && exportKeys.includes("./experimental"),
  "there is NO stable (non-experimental) object-table entry point",
  "exports=" + JSON.stringify(exportKeys),
);

const rootTypesPath = join(NM, PKG, "build", "types", "index.d.ts");
const rootTypesBytes = existsSync(rootTypesPath) ? readFileSync(rootTypesPath).length : -1;
assert(
  "A4",
  rootTypesBytes === 0,
  "the package ROOT exports nothing — importing from '@osdk/react-components' gets you no ObjectTable",
  "build/types/index.d.ts is " + rootTypesBytes + " bytes",
);

// ---------------------------------------------------------------------------
// SECTION 2 — the three things that decide buy-vs-build
// ---------------------------------------------------------------------------

log("");
log("SECTION 2  can a row host select + justification + 2 links?");

// --- A5: what cell editors exist at all? -----------------------------------
// EditFieldConfig is a mapped type over EditFieldPropsByType. If a free-text
// component is ever added, "TEXT" stops being an error and this goes red.
const a5 = typecheck(
  "a5-field-components",
  `
import type { ColumnDefinition } from "${SUBPATH}";
import type { SigElement } from "./prelude.js";
export const c: ColumnDefinition<SigElement> = {
  locator: { type: "property", id: "determination" },
  editable: true,
  editFieldConfig: {
    // @ts-expect-error only DROPDOWN | DATE_PICKER exist. If a free-text field
    // component is added, this @ts-expect-error becomes unused and tsc errors,
    // flipping A5 red — which is the point.
    fieldComponent: "TEXT",
    getFieldComponentProps: () => ({ items: [] }),
  },
};
`,
);
assert(
  "A5",
  a5.ok,
  "the only declared cell editors are DROPDOWN and DATE_PICKER — there is no free-text field component; free text is the DEFAULT editor",
  a5.out || "(fixture compiled when it should not have)",
);

// --- A6: THE SHAPE. 6 elements, select + justification + 2 links. ----------
const OUR_SHAPE = `
import * as React from "react";
import { ObjectTable } from "${SUBPATH}";
import type { CellEditInfo, ColumnDefinition } from "${SUBPATH}";
import { SigElement } from "./prelude.js";

const DETERMINATIONS = ["MET", "NOT_MET", "NOT_APPLICABLE"] as const;
type Determination = (typeof DETERMINATIONS)[number];

const columns: Array<ColumnDefinition<typeof SigElement>> = [
  { locator: { type: "property", id: "elementLabel" }, columnName: "Element" },

  // (a) CONSTRAINED SELECT bound to a value set
  {
    locator: { type: "property", id: "determination" },
    columnName: "Determination",
    editable: true,
    editFieldConfig: {
      fieldComponent: "DROPDOWN",
      getFieldComponentProps: () => ({
        items: DETERMINATIONS as readonly Determination[] as Determination[],
        itemToStringLabel: (i) => (i == null ? "-- select --" : String(i)),
        isSearchable: false,
        isMultiple: false,
        placeholder: "Select a determination",
      }),
    },
    validateEdit: async (value) =>
      DETERMINATIONS.includes(value as Determination)
        ? undefined
        : "Value not in the permitted set",
  },

  // (b) FREE-TEXT ONE-LINE JUSTIFICATION (the default text editor)
  {
    locator: { type: "property", id: "justification" },
    columnName: "Justification",
    editable: true,
    validateEdit: async (value) => {
      const s = typeof value === "string" ? value : "";
      if (s.trim().length === 0) return "Justification is required";
      if (s.includes("\\n")) return "Justification must be one line";
      return undefined;
    },
  },

  // (c) TWO EVIDENCE LINKS in one custom cell
  {
    locator: { type: "custom", id: "evidence" },
    columnName: "Evidence",
    renderCell: (object) =>
      React.createElement(
        "span",
        null,
        React.createElement("a", { href: object.evidenceUrl1 }, "[1]"),
        React.createElement("a", { href: object.evidenceUrl2 }, "[2]"),
      ),
  },
];

export function SignatureChecklist(): React.ReactElement {
  return React.createElement(ObjectTable<typeof SigElement>, {
    objectType: SigElement,
    columnDefinitions: columns,
    editMode: "manual",
    pageSize: 6,
    onSubmitEdits: async (
      edits: CellEditInfo<any, unknown>[],
    ): Promise<boolean> => {
      // Write-back is CALLER-implemented. See A9.
      void edits.map((e) => [e.rowId, e.columnId, e.newValue]);
      return true;
    },
  });
}
`;
const a6 = typecheck("a6-our-shape", OUR_SHAPE);
assert(
  "A6",
  a6.ok,
  "ObjectTable DOES host our shape: constrained select + one-line justification + 2 evidence links, all three, type-clean",
  a6.out,
);

// --- A6c: how much of leg (c) is actually TYPE-checked? Less than it looks. -
// A6 compiles, but "type-clean" is doing less work on the evidence-links column
// than on the other two. On a `custom` locator, an unknown property read off the
// row object does NOT error — it resolves through Osdk.Instance's catch-all — and
// React.createElement("a", {...}) with a string tag does not check `href` either.
// So a MISSPELLED evidence property stays green. Legs (a) and (b) are genuinely
// checked (bad locator id, bad fieldComponent and missing `items` all error);
// leg (c) is not. This assertion pins the weakness so it goes red if the library
// ever tightens renderCell — which would be a real gain, not a regression.
const a6c = typecheck(
  "a6c-rendercell-unchecked",
  `
import * as React from "react";
import type { ColumnDefinition } from "${SUBPATH}";
import { SigElement } from "./prelude.js";
export const c: ColumnDefinition<typeof SigElement> = {
  locator: { type: "custom", id: "evidence" },
  columnName: "Evidence",
  // \`evidenceUrl1\` deliberately misspelled. If this ever stops compiling,
  // renderCell became property-checked and A6's leg (c) got real teeth.
  renderCell: (object) => React.createElement("a", { href: object.evidenceUrlOne }, "[1]"),
};
`,
);
assert(
  "A6c",
  a6c.ok,
  "leg (c) is NOT property-checked: a misspelled row property in a custom-locator renderCell still compiles — A6's 'type-clean' covers the select and the justification, but the evidence links only structurally",
  a6c.ok ? "" : "renderCell is now property-checked (a GAIN): " + a6c.out,
);

// --- A7: ...but only against a live ontology. THE DISQUALIFIER. ------------
const a7 = typecheck(
  "a7-objecttype-required",
  `
import * as React from "react";
import { ObjectTable } from "${SUBPATH}";
import type { SigElement } from "./prelude.js";
// No objectType, no objectSet — i.e. "here are my 6 local rows".
export const noOntology = () =>
  React.createElement(ObjectTable<SigElement>, { columnDefinitions: [], pageSize: 6 });
`,
);
assert(
  "A7",
  !a7.ok && /objectType/.test(a7.out),
  "`objectType` is REQUIRED — ObjectTable fetches its own rows from an ontology and cannot be handed 6 local ones",
  a7.ok ? "fixture compiled; objectType is now optional" : a7.out,
);

// --- A8: the select is not actually constrained by anything typed. --------
const a8 = typecheck(
  "a8-items-untyped",
  `
import type { ColumnDefinition } from "${SUBPATH}";
import type { SigElement } from "./prelude.js";
// determination is a STRING property. Offer it numbers.
export const c: ColumnDefinition<SigElement> = {
  locator: { type: "property", id: "determination" },
  editable: true,
  editFieldConfig: {
    fieldComponent: "DROPDOWN",
    getFieldComponentProps: () => ({ items: [1, 2, 3] }),
  },
};
`,
);
assert(
  "A8",
  a8.ok,
  "DropdownEditConfig items are `V[]` at V=unknown — numbers are accepted for a string property; the select is constrained by YOUR array at runtime, by nothing at compile time",
  a8.out,
);

// Corroborating source fact: nothing in the object-table reads the ontology's
// value type, so the dropdown cannot be auto-bound to a Foundry value set.
const otTypesDir = join(NM, PKG, "build", "types", "object-table");
const grepValueType = spawnSync(
  "grep",
  ["-rl", "valueTypeApiName", otTypesDir],
  { encoding: "utf8" },
);
assert(
  "A8b",
  (grepValueType.stdout ?? "").trim() === "",
  "nothing in object-table reads `valueTypeApiName` — the dropdown is never auto-bound to an ontology value set",
  "matches: " + (grepValueType.stdout ?? "").trim(),
);

// ---------------------------------------------------------------------------
// SECTION 3 — what the buy does NOT include
// ---------------------------------------------------------------------------

log("");
log("SECTION 3  write-back and the default text editor (shipped artifact facts)");

const otEsmDir = join(NM, PKG, "build", "esm", "object-table");

// --- A9: the table never persists anything. -------------------------------
const grepAction = spawnSync(
  "grep",
  ["-rlE", "applyAction|createAction", otEsmDir],
  { encoding: "utf8" },
);
assert(
  "A9",
  (grepAction.stdout ?? "").trim() === "",
  "the shipped object-table NEVER calls a Foundry action — write-back is 100% caller-implemented via onSubmitEdits(edits): Promise<boolean>",
  "files calling an action: " + (grepAction.stdout ?? "").trim(),
);

// --- A10: the free-text editor is real, and it is single-line. ------------
const editableCellPath = join(otEsmDir, "EditableCell.js");
if (!existsSync(editableCellPath)) {
  skip("A10", "default editor is a single-line text input", "EditableCell.js not found — layout changed");
} else {
  const cellSrc = readFileSync(editableCellPath, "utf8");
  const hasTextInput = /TextInputCellField/.test(cellSrc);
  const hasInputTypeText = /NUMBER_TYPES\.includes\(dataType\)\s*\?\s*"number"\s*:\s*"text"/.test(cellSrc);
  const noTextarea = !/textarea/i.test(cellSrc);
  assert(
    "A10",
    hasTextInput && hasInputTypeText && noTextarea,
    "the default editor for a string property is TextInputCellField with inputType 'text' — a single-line input, not a textarea; exactly the justification field we need",
    "TextInputCellField=" + hasTextInput + " inputTypeTernary=" + hasInputTypeText + " noTextarea=" + noTextarea,
  );
}

// ---------------------------------------------------------------------------
// SECTION 4 — the escape hatch: BaseTable with no ontology at all
// ---------------------------------------------------------------------------

log("");
log("SECTION 4  BaseTable — our 6 static rows with NO ontology");

const BASE_TABLE_SHAPE = `
import * as React from "react";
import { createColumnHelper, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { BaseTable } from "${SUBPATH}";
import type { CellEditInfo, EditableConfig } from "${SUBPATH}";

type Row = {
  elementId: string; label: string;
  determination: string | null; justification: string | null;
  evidence1: string; evidence2: string;
};
// OUR SHAPE: exactly 6 required elements, held locally.
const SIX: Row[] = Array.from({ length: 6 }, (_, i) => ({
  elementId: \`E\${i + 1}\`, label: \`Element \${i + 1}\`,
  determination: null, justification: null,
  evidence1: \`https://example/e\${i + 1}/a\`, evidence2: \`https://example/e\${i + 1}/b\`,
}));
const DET = ["MET", "NOT_MET", "NOT_APPLICABLE"];
const h = createColumnHelper<Row>();

export function Checklist(): React.ReactElement {
  const [edits, setEdits] = React.useState<Record<string, CellEditInfo<Row, unknown>>>({});
  const [errs, setErrs] = React.useState(new Map<string, string>());
  const [active, setActive] = React.useState(false);

  const columns = React.useMemo(() => [
    h.accessor("label", { header: "Element" }),
    h.accessor("determination", {
      header: "Determination",
      meta: {
        editable: true, dataType: "string",
        editFieldConfig: {
          fieldComponent: "DROPDOWN",
          getFieldComponentProps: () => ({ items: DET, isSearchable: false }),
        },
        validateEdit: async (v: unknown) =>
          DET.includes(v as string) ? undefined : "not in permitted set",
      },
    }),
    h.accessor("justification", {
      header: "Justification",
      meta: {
        editable: true, dataType: "string",
        validateEdit: async (v: unknown) => {
          const s = typeof v === "string" ? v : "";
          if (!s.trim()) return "required";
          if (s.includes("\\n")) return "must be one line";
          return undefined;
        },
      },
    }),
    h.display({
      id: "evidence", header: "Evidence",
      cell: (ctx) => React.createElement("span", null,
        React.createElement("a", { href: ctx.row.original.evidence1 }, "[1]"),
        React.createElement("a", { href: ctx.row.original.evidence2 }, "[2]")),
    }),
  ], []);

  // NOTE: useEditableTable() is generic over ObjectOrInterfaceDefinition and
  // returns EditableConfig<Osdk.Instance<...>>, so it does NOT type against
  // plain rows. The edit state machine below is hand-written — that is part of
  // what "buying" BaseTable still leaves you to build.
  const editableConfig: EditableConfig<Row, unknown> = {
    cellEdits: edits,
    onCellEdit: (cellId, info) => setEdits((p) => ({ ...p, [cellId]: info })),
    onSubmitEdits: async () => { return true; },
    clearEdits: () => setEdits({}),
    editModeState: { type: "manual", isActive: active, setActive },
    onCellValidationError: (id, e) => setErrs((m) => new Map(m).set(id, e)),
    validationErrors: errs,
    clearCellValidationError: (id) =>
      setErrs((m) => { const n = new Map(m); n.delete(id); return n; }),
  };

  const table = useReactTable({
    data: SIX, columns, getCoreRowModel: getCoreRowModel(),
    getRowId: (r) => r.elementId,
    meta: {
      onCellEdit: editableConfig.onCellEdit,
      cellEdits: edits, isInEditMode: active, validationErrors: errs,
    },
  });

  return React.createElement(BaseTable<Row>, { table, editableConfig, showEditFooter: true });
}
`;

// BaseTable's `table: Table<TData>` comes from the @tanstack/react-table copy that
// @osdk/react-components ITSELF pins (dependency "^8.21.3"), not from whatever the
// consumer hoisted. Resolve the library's own copy explicitly. Without this the
// fixture binds to a top-level @tanstack/react-table — and `npm i @tanstack/react-table`
// today installs v9, whose API renamed useReactTable/getCoreRowModel, turning A11 red
// for a reason that has nothing to do with the escape hatch being open or closed.
const TANSTACK_NESTED = join(NM, PKG, "node_modules", "@tanstack", "react-table");
const TANSTACK_HOISTED = join(NM, "@tanstack", "react-table");
const TANSTACK_DIR = existsSync(TANSTACK_NESTED) ? TANSTACK_NESTED : TANSTACK_HOISTED;
const tanstackVer = existsSync(join(TANSTACK_DIR, "package.json"))
  ? JSON.parse(readFileSync(join(TANSTACK_DIR, "package.json"), "utf8")).version
  : "ABSENT";
const tanstackDeclared: string =
  (pkgJson.dependencies ?? {})["@tanstack/react-table"] ?? "(not a declared dependency)";

// A11a exists so that a red A11 can never be MISREAD as "the escape hatch closed"
// when the real cause is a TanStack major swap underneath it.
assert(
  "A11a",
  tanstackVer.startsWith("8."),
  "the @tanstack/react-table that BaseTable's `table` prop is typed against is still v8 (@osdk/react-components declares " +
    tanstackDeclared + ") — a consumer app on TanStack v9 CANNOT hand BaseTable its table",
  "resolved " + tanstackVer + " at " + TANSTACK_DIR,
);

if (tanstackVer === "ABSENT") {
  skip("A11", "BaseTable hosts 6 static rows at our full shape with no ontology", "@tanstack/react-table not resolvable");
} else {
  const a11 = typecheck("a11-basetable-static", BASE_TABLE_SHAPE, {
    "@tanstack/react-table": [TANSTACK_DIR],
    "@tanstack/react-table/*": [join(TANSTACK_DIR, "*")],
  });
  assert(
    "A11",
    a11.ok,
    "BaseTable hosts our EXACT shape — 6 local rows, constrained dropdown, validated one-line justification, 2 links — with NO ontology and NO OSDK client",
    a11.out,
  );
}

// ---------------------------------------------------------------------------
// SECTION 5 — the price (optional; needs esbuild)
// ---------------------------------------------------------------------------

log("");
log("SECTION 5  bundle weight of the buy");

// --- A12css: the stylesheet the JS number does NOT contain. ---------------
// The browser build imports no CSS: styles ship as a SEPARATE `./styles.css`
// export that a consumer must import for the table to render correctly. So the
// esbuild figure below is JS-only and understates the real page weight of the
// buy. Measured here so the price is the whole price.
const stylesPath = join(NM, PKG, "build", "browser", "styles.css");
if (!existsSync(stylesPath)) {
  skip("A12css", "the mandatory stylesheet is counted in the price", "build/browser/styles.css not found");
} else {
  const cssBuf = readFileSync(stylesPath);
  const cssGz = (require("node:zlib") as typeof import("node:zlib")).gzipSync(cssBuf, { level: 9 }).length;
  log("  INFO      mandatory ./styles.css (NOT in the JS number): raw=" + cssBuf.length + "B gzip=" + cssGz + "B");
  assert(
    "A12css",
    cssGz < 60_000,
    "the separately-imported ./styles.css is still under 60 KB gzipped (recorded at 48,288 B for 0.48.0) — it is a single un-tree-shakeable file, so the whole library's CSS ships for one table",
    "gzip=" + cssGz + "B",
  );
}

const esbuildBin = join(NM, ".bin", "esbuild");
let weightFact = "SKIPPED";
if (!existsSync(esbuildBin)) {
  skip("A12", "object-table subpath weighs under 250 KB gzipped", "esbuild not installed (optional dep)");
} else {
  const entry = join(FIXDIR, "weight-entry.mjs");
  const outfile = join(FIXDIR, "weight.min.js");
  writeFileSync(entry, `import { ObjectTable } from "${SUBPATH}";\nconsole.log(typeof ObjectTable);\n`, "utf8");
  const b = spawnSync(
    esbuildBin,
    [
      entry, "--bundle", "--platform=browser", "--format=esm", "--minify",
      "--loader:.css=empty", '--define:process.env.NODE_ENV="production"',
      "--external:react", "--external:react-dom",
      "--outfile=" + outfile, "--log-level=error",
    ],
    { encoding: "utf8", cwd: DEPS },
  );
  if (b.status !== 0 || !existsSync(outfile)) {
    skip("A12", "object-table subpath weighs under 250 KB gzipped", "esbuild failed: " + ((b.stderr ?? "") + (b.stdout ?? "")).slice(0, 300));
  } else {
    const buf = readFileSync(outfile);
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const zlib = require("node:zlib") as typeof import("node:zlib");
    const gz = zlib.gzipSync(buf, { level: 9 }).length;
    weightFact = "min=" + buf.length + "B gzip=" + gz + "B";
    log("  INFO      ObjectTable subpath, React excluded: " + weightFact);
    assert(
      "A12",
      gz < 250_000,
      "the object-table subpath still weighs under 250 KB gzipped (recorded at 198,928 B for 0.48.0) — this is the price of the buy for ONE 6-row checklist",
      weightFact,
    );
  }
}

// ---------------------------------------------------------------------------
// verdict + digest
// ---------------------------------------------------------------------------

log("");
log("VERDICT (G022)");
log("  ObjectTable CAN host the shape (A6) — the register's stated disqualifier does NOT fire.");
log("  It is disqualified instead by A7: objectType is required, so it cannot take 6 local rows.");
log("  BaseTable (A11) is the ontology-free escape hatch and DOES host the shape.");
log("  But write-back (A9) and the value set (A8/A8b) stay hand-written either way,");
log("  and the price (A12) is ~194 KB gzipped for one 6-row checklist.");
log("  => BUILD. G022's hand-built default STANDS.");

const digest = createHash("sha256")
  .update(
    JSON.stringify({
      pkg: PKG,
      version: VERSION,
      exports: exportKeys.slice().sort(),
      rootTypesBytes,
      results: lines.filter((l) => /^ {2}(PASS|FAIL|SKIP) /.test(l)).map((l) => l.trim().split(/\s+/).slice(0, 2).join(" ")),
    }),
  )
  .digest("hex");

log("");
log("RESULT-DIGEST " + digest);
log("SUMMARY failures=" + failures + " skipped=" + skipped);

rmSync(FIXDIR, { recursive: true, force: true });

if (failures > 0) {
  log("");
  log("RED. The library changed. Read the FAIL line(s) above and the header's");
  log("'what a red run means' table before touching n.surface.");
  process.exit(1);
}
// A SKIPPED assertion is not a held assertion. Exiting 0 here would let a run in
// which A11 (the escape hatch) or A12 (the price) never executed report itself as
// "every assertion held" — a green that hides a blocked. Exit 2 instead.
if (skipped > 0) {
  log("");
  log("PENDING/BLOCKED — " + skipped + " assertion(s) never ran (see SKIP lines).");
  log("This is NOT a pass: the verdict below rests on assertions that did not execute.");
  process.exit(2);
}
process.exit(0);
