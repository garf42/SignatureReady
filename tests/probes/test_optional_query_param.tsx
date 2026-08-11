/**
 * Phase -1 prefab probe: @osdk/react::useOsdkFunction, optional nullable query parameter.
 *
 * prefab:     @osdk/react::useOsdkFunction
 * used_by:    n.surface
 * probe_dims: one query publishing an optional nullable string parameter documented
 *             as omittable.
 *
 * CARRIED CLAIM UNDER TEST (from a parallel build, unconfirmed there):
 *   "the hook's params type wraps the query's in NotOptionalParams, so the React binding
 *    cannot express an absent optional parameter without a cast. The mismatch is in the
 *    binding, not in the function."
 *
 * VERDICT AT THE PINNED VERSIONS: the claim is PARTLY right and its stated symptom is
 * BACKWARDS. See "WHAT THIS PROBE ESTABLISHES" below. This file pins the real behavior,
 * so it goes RED the day the binding is fixed.
 *
 * ---------------------------------------------------------------------------
 * PINNED VERSIONS -- the exact artifacts this verdict was produced against.
 * ---------------------------------------------------------------------------
 *   @osdk/react                     2.56.0
 *   @osdk/client                    2.56.0
 *   @osdk/api                       2.56.0
 *   @osdk/client.unstable           2.56.0
 *   @osdk/generator-converters      2.56.0
 *   @osdk/foundry.core              2.70.0
 *   @osdk/foundry.ontologies        2.70.0
 *   @osdk/foundry.functions         2.70.0
 *   @osdk/shared.client             1.0.1
 *   @osdk/shared.client2            1.0.0
 *   @osdk/shared.client.impl        1.13.0
 *   @osdk/shared.net.errors         2.12.0
 *   @osdk/shared.net.fetch          1.12.0
 *   @osdk/shared.net.platformapi    1.7.0
 *   react                           19.2.8
 *   @types/react                    19.2.18
 *   typescript                      7.0.2  AND  5.9.3   (identical results; see RUN)
 *
 * ---------------------------------------------------------------------------
 * RUN -- the exact invocation. Run it from a scratch dir, not from the repo root;
 * this repo intentionally has no node_modules.
 * ---------------------------------------------------------------------------
 *
 *   WORK=$(mktemp -d) && cd "$WORK"
 *   npm init -y >/dev/null
 *   npm install --save-exact \
 *       @osdk/react@2.56.0 @osdk/client@2.56.0 @osdk/api@2.56.0 \
 *       react@19.2.8 @types/react@19.2.18 typescript@7.0.2
 *   cp /path/to/SignatureReady/tests/probes/test_optional_query_param.tsx .
 *   npx tsc --ignoreConfig --noEmit --strict \
 *       --target ES2022 --module NodeNext --moduleResolution nodenext \
 *       --jsx react-jsx --skipLibCheck \
 *       test_optional_query_param.tsx
 *   echo "exit=$?"    # 0 == the binding still behaves as pinned below
 *
 * Cross-check under the TypeScript major the package was built with:
 *   npm install --save-exact typescript@5.9.3
 *   npx tsc --noEmit --strict --target ES2022 --module NodeNext \
 *       --moduleResolution nodenext --jsx react-jsx --skipLibCheck \
 *       test_optional_query_param.tsx
 *
 * NOTE on `--ignoreConfig`: TypeScript 7 errors with TS5112 if a tsconfig.json is present
 * and files are also named on the command line. TypeScript 5.9 has no such flag and does
 * not need it. That is the only difference between the two invocations.
 *
 * ---------------------------------------------------------------------------
 * RUN IT UNDER BOTH MODULE RESOLUTIONS. This is not optional -- see finding 5.
 * ---------------------------------------------------------------------------
 * @osdk/client 2.56.0 ships TWO SEPARATE declaration trees and `moduleResolution: nodenext`
 * picks between them by the nearest package.json `type` field:
 *
 *   CJS consumer (no `"type"` field)  -> build/cjs/Client-ClFX5q-o.d.cts   (bundled)
 *   ESM consumer (`"type": "module"`) -> build/types/queries/types.d.ts    (per-file)
 *
 * A real Vite/React app is ESM and gets the second. `npm init -y` produces the first. Both
 * were verified for this probe and both give identical results, but a later session that
 * checks only one is checking a tree its app may never load. To exercise the ESM tree:
 *
 *   mkdir -p esm && printf '{"name":"esm-probe","type":"module","private":true}\n' > esm/package.json
 *   cp test_optional_query_param.tsx esm/
 *   npx tsc --ignoreConfig --noEmit --strict --target ES2022 --module NodeNext \
 *       --moduleResolution nodenext --jsx react-jsx --skipLibCheck \
 *       esm/test_optional_query_param.tsx
 *
 * Confirm the tree actually loaded with `--traceResolution | grep observable`.
 *
 * ---------------------------------------------------------------------------
 * HOW THIS FILE FAILS -- it is a tripwire, not a green rubber stamp.
 * ---------------------------------------------------------------------------
 * Every deviation is pinned with an expect-error directive. If Palantir fixes the binding,
 * each pinned error stops occurring and tsc raises TS2578 "Unused directive" -> non-zero
 * exit. The `expectTrue<Equals<...>>()` assertions fail the same way if the resolved types
 * merely change shape. There is no branch of this file that passes silently on a changed
 * binding.
 *
 * THIS WAS MUTATION-TESTED, not assumed. Three INDEPENDENT fixes were each applied to the
 * shipped declarations and each took this file from exit 0 to exit 1; every one was then
 * reverted and exit 0 restored. A probe that has not been shown to fail is not evidence
 * that anything passed.
 *
 *   MUTATION A -- the polarity fix in @osdk/client, applied to BOTH trees:
 *     `T[K] extends { nullable: true } ? never : K`  ->  `? K : never`
 *     10 errors: 6x TS2344 (A.1, A.2, B.1 x2, C.1 x2), 3x TS2578 (A.4, A.5, B.2),
 *     1x TS2322 (B.3).  [counts verified by re-run; an earlier note here said 2x/7x]
 *
 *   MUTATION B -- fixing only the degenerate collapse, leaving polarity alone:
 *     `PartialByNotStrict<T,K> = K extends keyof T ? ... : "never"`
 *       -> `[K] extends [never] ? T : K extends keyof T ? ... : "never"`
 *     3 errors: 2x TS2344 (A.1, A.2), 1x TS2578 (A.4).
 *
 *   MUTATION D -- the fix at the locus this probe actually names, in @osdk/react:
 *     `params?: ... QueryParameterType<CompileTimeMetadata<Q>["parameters"]>`
 *       -> `params?: ... Parameters<CompileTimeMetadata<Q>["signature"]>[0]`
 *     5 errors: 1x TS2344 (A.2), 3x TS2578 (A.4, A.5, B.2), 1x TS2741 (B.3).
 *     NOTE: in the CJS tree this declaration lives in
 *     @osdk/react/build/cjs/public/experimental.d.cts, NOT in index.d.cts. Patching
 *     build/types/new/useOsdkFunction.d.ts alone leaves a CJS consumer GREEN -- the exact
 *     two-tree trap described above, re-encountered while mutating @osdk/react.
 *
 * The probe is therefore not overfitted to one mutation: it goes red whether the fix lands
 * in @osdk/client's polarity, @osdk/client's degenerate-never fallback, or @osdk/react's
 * choice of type. A.1 correctly stays GREEN under Mutation D, because A.1 pins @osdk/client
 * and Mutation D only changes @osdk/react.
 *
 * ---------------------------------------------------------------------------
 * WHAT THIS PROBE ESTABLISHES, by running the real tsc against the real .d.ts files
 * ---------------------------------------------------------------------------
 *
 * 1. THE HOOK DOES NOT WRAP ANYTHING IN `NotOptionalParams`. `NotOptionalParams` is not a
 *    @osdk/react type at all, and it is not exported from anywhere. Two unrelated,
 *    module-local declarations of that name ship in @osdk/client 2.56.0:
 *
 *      node_modules/@osdk/client/build/types/actions/applyAction.d.ts:9
 *        type NotOptionalParams<X extends ActionParametersDefinition> =
 *          { [P in keyof X] : MaybeArrayType<X[P]> };
 *
 *      node_modules/@osdk/client/build/types/queries/types.d.ts:12
 *        type NotOptionalParams<T extends Record<any, QueryDataTypeDefinition>> =
 *          { [K in keyof T] : MaybeArrayType<T[K]> };
 *
 *    Only the second governs queries. Neither is "the hook's params type". What
 *    useOsdkFunction actually declares (@osdk/react/build/types/new/useOsdkFunction.d.ts)
 *    is:
 *
 *      params?: CompileTimeMetadata<Q>["parameters"] extends Record<string, never>
 *        ? undefined
 *        : QueryParameterType<CompileTimeMetadata<Q>["parameters"]>;
 *
 *    with `QueryParameterType` imported from "@osdk/client/observable". So the locus is
 *    @osdk/client, reached through the hook -- not @osdk/react's own type algebra.
 *
 * 2. THE ACTUAL DEFECT IS AN INVERTED POLARITY IN @osdk/client, one level below
 *    `NotOptionalParams`. From queries/types.d.ts, verbatim:
 *
 *      export type QueryParameterType<T extends Record<any, QueryDataTypeDefinition>> =
 *        PartialByNotStrict<NotOptionalParams<T>, OptionalQueryParams<T>>;
 *
 *      type OptionalQueryParams<T extends Record<any, QueryDataTypeDefinition>> =
 *        { [K in keyof T] : T[K] extends { nullable: true } ? never : K }[keyof T];
 *
 *    and from util/partialBy.d.ts, verbatim:
 *
 *      export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
 *      export type PartialByNotStrict<T, K> = K extends keyof T ? PartialBy<T, K> : "never";
 *
 *    `OptionalQueryParams` yields K when the parameter is NOT nullable and `never` when it
 *    IS. Despite the name it collects the REQUIRED keys. Those are then the keys handed to
 *    `PartialBy`, i.e. the required parameters are the ones made optional, and the nullable
 *    ones are left required. The polarity is exactly reversed. Section MIXED below pins it.
 *
 * 3. FOR THIS BUILD'S PROBE DIMENSION -- a query whose ONLY parameter is an optional
 *    nullable string -- `OptionalQueryParams` is `never`. `PartialByNotStrict` is a naked
 *    distributive conditional, and distributing over `never` yields `never`. So:
 *
 *      QueryParameterType<{ q: { type: "string"; nullable: true } }>  ===  never
 *
 *    and the hook's slot collapses to `never | undefined`, i.e. `undefined`. Consequences,
 *    all pinned as executable assertions below:
 *
 *      - OMITTING the parameter COMPILES. `useOsdkFunction(q, {})`, `useOsdkFunction(q)`
 *        and `{ params: undefined }` are all accepted with no cast.
 *      - SUPPLYING the parameter DOES NOT COMPILE, and neither does an empty params object:
 *          TS2322: Type '{ q: string; }' is not assignable to type 'undefined'.
 *          TS2322: Type '{}' is not assignable to type 'undefined'.
 *
 *    So the carried claim has the symptom backwards. Absence is the ONLY thing this hook
 *    can express for such a query. Presence is what needs the cast.
 *
 * 4. THE CARRIED CLAIM'S LOCUS SENTENCE HOLDS: the mismatch is in the binding, not in the
 *    function. The direct client path for the SAME query definition is correct, because it
 *    prefers the generator-emitted signature rather than recomputing it:
 *
 *      @osdk/client/build/types/queries/types.d.ts:3
 *        export type QuerySignatureFromDef<T extends QueryDefinition<any>> = {
 *          executeFunction: CompileTimeMetadata<T> extends never
 *            ? QuerySignature<T>
 *            : CompileTimeMetadata<T>["signature"]
 *        };
 *
 *    `client(searchClauses).executeFunction` accepts `()`, `({})` and `({ q: "lease" })`.
 *    Section CONTRAST below compiles all three with no error and no cast. Same definition,
 *    same package, opposite outcome -- the divergence is that useOsdkFunction reaches for
 *    `QueryParameterType` where the client reaches for `["signature"]`.
 *
 * 5. THE TWO SHIPPED DECLARATION TREES AGREE. The definitions quoted in (1) and (2) are
 *    from the ESM tree (build/types/...). The CJS bundle carries its own copies at
 *    build/cjs/Client-ClFX5q-o.d.cts lines 16-17 and 41-49, alpha-renamed
 *    (the actions-side `NotOptionalParams` becomes `NotOptionalParams$1`) but semantically
 *    identical. This probe was compiled against BOTH and produced identical results, so the
 *    finding does not depend on which tree a consumer resolves.
 *
 * ---------------------------------------------------------------------------
 * WHAT THIS PROBE DOES NOT ESTABLISH (tie-break rule 3: no value the source does not state)
 * ---------------------------------------------------------------------------
 *   - No END-TO-END wire call. There is no Foundry enrollment in this environment, so no
 *     real query was executed against a live ontology.
 *
 *     BUT the runtime half is NOT simply unknown. The shipped runtime JS was read AND
 *     EXECUTED locally (no enrollment required), and it is PARAMETER-POLARITY-AGNOSTIC:
 *
 *       @osdk/client/build/esm/queries/applyQuery.js
 *         parameters: params ? await remapQueryParams(params, client, ...) : {}
 *
 *       @osdk/client/.../function/FunctionParamsCanonicalizer.js
 *         canonicalize(params) { if (params == null) return undefined; ... }
 *
 *     Executed directly: canonicalize(undefined) -> undefined (no throw); an undefined
 *     `params` makes applyQuery send `parameters: {}`; and remapQueryParams accepts
 *     {}, { q }, { r } and { r, q } alike, since it just walks Object.entries(params).
 *     @osdk/react's useOsdkFunction passes `options.params` straight through to
 *     observableClient.observeFunction with no reshaping.
 *
 *     CONSEQUENCE, and it is the practically important one: THE DEFECT IS ENTIRELY
 *     TYPE-LEVEL. Nothing at runtime enforces the inverted polarity. A cast at the call
 *     site is therefore a SOUND workaround, not merely a silencing one -- the value that
 *     reaches the wire is the one you wrote. This is what makes the bug survivable.
 *
 *   - Nothing about how a REAL generated SDK's metadata is shaped. The fixtures here are
 *     hand-written to the QueryDefinition contract in @osdk/api (verified: CompileTimeMetadata
 *     <T> = NonNullable<T["__DefinitionMetadata"]>, and the fixtures resolve through the
 *     QueryParameterType branch, not the Record<string, never> branch -- see A.1/A.2).
 *   - Nothing about `useOsdkFunctions` (plural). It reuses `UseOsdkFunctionOptions<Q>` but
 *     erases Q to `QueryDefinition<unknown>` in its array element type, which is a
 *     different resolution path and was not probed.
 *   - No claim about versions other than those pinned above.
 */

import type { QueryDefinition } from "@osdk/api";
import type { Client } from "@osdk/client";
import type { QueryParameterType } from "@osdk/client/observable";
import type { UseOsdkFunctionOptions } from "@osdk/react";
import { useOsdkFunction } from "@osdk/react";

// ===========================================================================
// Type-level assertion helpers.
// `Equals` is the invariant-position trick: it is exact, so `never` vs `undefined`
// vs `{} | undefined` are all distinguished. A widened or narrowed type fails.
// ===========================================================================

type Equals<X, Y> =
  (<T>() => T extends X ? 1 : 2) extends (<T>() => T extends Y ? 1 : 2) ? true
    : false;

declare function expectTrue<_T extends true>(): void;

/** One-directional assignability. Used to state a DISAGREEMENT between two types. */
type Assignable<X, Y> = [X] extends [Y] ? true : false;

/**
 * Is key K optional on T? `{}` is assignable to a Pick of an optional key and not to a
 * Pick of a required one. Used instead of `Equals` where the resolved type is an
 * intersection (`Omit<..> & Partial<Pick<..>>`), which is mutually assignable to the
 * flattened object type but not IDENTICAL to it -- `Equals` would reject the flattened
 * form and the assertion would be about tsc's normalization rather than about optionality.
 */
type IsOptionalKey<T, K extends keyof T> = {} extends Pick<T, K> ? true : false;

/** The exact type useOsdkFunction will accept in its `params` slot for query Q. */
type ParamsSlot<Q extends QueryDefinition<unknown>> = UseOsdkFunctionOptions<Q>["params"];

// ===========================================================================
// FIXTURE A -- the build's probe dimension.
// One query. One parameter. Optional, nullable, string. This is the shape the OSDK
// code generator emits for a Foundry function parameter documented as omittable:
// the wire metadata carries `nullable: true`, and the emitted `signature` marks the
// parameter with `?`.
// ===========================================================================

type OptionalOnlyParams = {
  readonly q: { readonly type: "string"; readonly nullable: true };
};
type OptionalOnlySignature = (params?: { q?: string }) => Promise<string>;

interface searchClauses extends QueryDefinition<OptionalOnlySignature> {
  type: "query";
  apiName: "searchClauses";
  __DefinitionMetadata?: {
    type: "query";
    apiName: "searchClauses";
    version: "1.0.0";
    parameters: OptionalOnlyParams;
    output: { type: "string" };
    rid: "ri.function-registry.main.function.searchClauses";
    signature: OptionalOnlySignature;
  };
}
declare const searchClauses: searchClauses;

// --- A.1  QueryParameterType collapses to `never` for an all-nullable param record.
// If Palantir fixes OptionalQueryParams' polarity, this resolves to `{ q?: string }`
// and the assertion fails.
expectTrue<Equals<QueryParameterType<OptionalOnlyParams>, never>>();

// --- A.2  ...so the hook's params slot is exactly `undefined`, not `{ q?: string } | undefined`.
expectTrue<Equals<ParamsSlot<searchClauses>, undefined>>();

// --- A.3  Omitting the parameter COMPILES TODAY. No cast. The carried claim says this is
// impossible; it is not. These three call sites deliberately carry NO expect-error
// directive -- if a future version breaks them, tsc goes red right here.
// (Do not write the directive's name in prose anywhere in this file: tsc treats any
// comment line beginning with it as a live directive, wherever it appears.)
export function OmitOptionsEntirely(): unknown {
  return useOsdkFunction(searchClauses).data;
}
export function OmitParamsKey(): unknown {
  return useOsdkFunction(searchClauses, {}).data;
}
export function ExplicitUndefinedParams(): unknown {
  return useOsdkFunction(searchClauses, { params: undefined }).data;
}

// --- A.4  SUPPLYING the parameter DOES NOT COMPILE. This is the real defect.
// Pinned error, verbatim from tsc 7.0.2 and 5.9.3:
//   error TS2322: Type '{ q: string; }' is not assignable to type 'undefined'.
export function SupplyOptionalParam(): unknown {
  return useOsdkFunction(searchClauses, {
    // @ts-expect-error PINNED @osdk/react 2.56.0: params slot collapsed to `undefined`
    // because QueryParameterType<OptionalOnlyParams> is `never`. Delete this directive
    // when the binding is fixed.
    params: { q: "lease" },
  }).data;
}

// --- A.5  Even an EMPTY params object does not compile.
// Pinned error: TS2322: Type '{}' is not assignable to type 'undefined'.
export function SupplyEmptyParamsObject(): unknown {
  return useOsdkFunction(searchClauses, {
    // @ts-expect-error PINNED @osdk/react 2.56.0: `{}` is not assignable to `undefined`.
    params: {},
  }).data;
}

// ===========================================================================
// FIXTURE B -- MIXED. One required (non-nullable) param, one optional (nullable) param.
// This is where the inverted polarity is visible as a plain wrong-way-round type.
// ===========================================================================

type MixedParams = {
  readonly r: { readonly type: "string" };
  readonly q: { readonly type: "string"; readonly nullable: true };
};
type MixedSignature = (params: { r: string; q?: string }) => Promise<string>;

interface mixedQuery extends QueryDefinition<MixedSignature> {
  type: "query";
  apiName: "mixedQuery";
  __DefinitionMetadata?: {
    type: "query";
    apiName: "mixedQuery";
    version: "1.0.0";
    parameters: MixedParams;
    output: { type: "string" };
    rid: "ri.function-registry.main.function.mixedQuery";
    signature: MixedSignature;
  };
}
declare const mixedQuery: mixedQuery;

// --- B.1  The polarity is inverted: `q` (nullable, omittable per the ontology) is
// REQUIRED, and `r` (non-nullable, genuinely required) is OPTIONAL. Asserted per-key so
// the assertion is about optionality itself, not about how tsc aliases the intersection.
type MixedSlot = QueryParameterType<MixedParams>;

/** The NULLABLE parameter is REQUIRED. Wrong. Goes red when the polarity is fixed. */
expectTrue<Equals<IsOptionalKey<MixedSlot, "q">, false>>();
/** The NON-NULLABLE parameter is OPTIONAL. Wrong. Goes red when the polarity is fixed. */
expectTrue<Equals<IsOptionalKey<MixedSlot, "r">, true>>();
/** Both are still strings -- this is a polarity flip, not a value-type change. */
expectTrue<Equals<NonNullable<MixedSlot["q"]>, string>>();
expectTrue<Equals<NonNullable<MixedSlot["r"]>, string>>();

// --- B.2  Supplying only the genuinely-required param fails.
// Pinned error, verbatim:
//   error TS2322: Type '{ r: string; }' is not assignable to type
//     'PartialBy<NotOptionalParams<MixedParams>, "r">'.
//     Property 'q' is missing in type '{ r: string; }' but required in type
//     'Omit<NotOptionalParams<MixedParams>, "r">'.
export function MixedOmitTheOmittableOne(): unknown {
  return useOsdkFunction(mixedQuery, {
    // @ts-expect-error PINNED @osdk/react 2.56.0: the NULLABLE param `q` is required and
    // the NON-NULLABLE param `r` is optional. OptionalQueryParams has reversed polarity.
    params: { r: "lease" },
  }).data;
}

// --- B.3  Dropping the genuinely-required param and supplying only the omittable one
// COMPILES. This is the inversion stated positively; it goes red when the binding is fixed.
export function MixedOmitTheRequiredOne(): unknown {
  return useOsdkFunction(mixedQuery, { params: { q: "lease" } }).data;
}

// ===========================================================================
// FIXTURE C -- CONTRAST. Same query definitions, direct client path.
// Establishes that the mismatch is in the binding and not in the function definition:
// nothing here errors, and nothing here needs a cast.
// ===========================================================================

declare const client: Client;

export function DirectClientPathIsCorrect(): void {
  const executeFunction = client(searchClauses).executeFunction;
  void executeFunction();                 // omitted   -- OK
  void executeFunction({});               // present, key omitted -- OK
  void executeFunction({ q: "lease" });   // key supplied -- OK

  const executeMixed = client(mixedQuery).executeFunction;
  void executeMixed({ r: "lease" });              // omittable param omitted -- OK
  void executeMixed({ r: "lease", q: "term" });   // both supplied -- OK
}

// --- C.1  The direct path's params type is the generator-emitted signature's, and it has
// the optionality the ontology declares. Pinning it makes the divergence machine-checkable
// rather than a narrative claim.
type GeneratedMixedSlot = Parameters<
  NonNullable<mixedQuery["__DefinitionMetadata"]>["signature"]
>[0];

expectTrue<Equals<GeneratedMixedSlot, { r: string; q?: string }>>();
expectTrue<Equals<IsOptionalKey<GeneratedMixedSlot, "q">, true>>();
expectTrue<Equals<IsOptionalKey<GeneratedMixedSlot, "r">, false>>();

// The binding and the function disagree about the SAME parameter record, and the
// disagreement is total: NEITHER type is assignable to the other. That is this probe's
// finding, stated as a compilable assertion. When the binding is fixed both directions
// become `true` and both assertions go red.
expectTrue<Equals<Assignable<GeneratedMixedSlot, MixedSlot>, false>>();
expectTrue<Equals<Assignable<MixedSlot, GeneratedMixedSlot>, false>>();
