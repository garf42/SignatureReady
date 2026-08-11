# node: n.det_core

## assume
[BINDING] origin: specified
- in: n.ontology — canonical path index; every input value has exactly one path and is a stored
  property, never a constant supplied at the call site
- in: n.ce_catalog — typed constraints carrying measure, value, unit and parsed strictness

## guarantee
[BINDING] origin: specified
- out: one row per (function, invocation); every result carries its inputs' canonical paths, the
  algorithm version, and the state change that invalidates it
- **no model dependency is reachable from any deterministic entry point.** Reachability is walked
  from the entry points through the package dependency graph; the runner reports entry points read,
  files walked, packages reachable, packages matching a model pattern, and names any declared but
  unreachable model package rather than hiding it
- the reachable-package set is pinned; the runner fails when that set changes at all — addition,
  removal or rename
- the runner exits non-zero when it cannot run; an absent dependency tree never reads as a passing zero
- every cap comparison uses the stored strictness and the elected basis; no denominator is
  hardcoded and no elected basis is defaulted
- a failing cap test names the failing measure, its computed value, its limit and its strictness
- `computeCoveredPortion` returns both readings and the divergence and elects nothing

## oracle
type: derivable
risk: semantic,reproducibility
fixture: `fixtures/det_core/boundaries.json` — for every numeric limit, the boundary value, one
below and one above, each carrying its citation. A case resting on an unverified value is authored
**non-asserting** against its gap id and is reported provisional, never as passing or blocked.

## metamorphic relations
[BINDING] origin: specified
- MR-1 (scaling): multiply all treatment acreages by k ⇒ the elected covered portion scales by k
  and the verdict flips exactly at the boundary, in the direction the stored strictness dictates
- MR-2 (permutation): reorder units ⇒ identical verdict and identical failing-test name
- MR-3 (idempotence): duplicate a treatment row ⇒ verdict unchanged under the geometric-union
  basis and changed under the treatment-sum basis. Agreement between the two is the defect
- MR-4 (re-execution): run twice in separate processes ⇒ byte-identical output including the
  algorithm version stamp

## demons
- D1: default `electedBasis` to the treatment sum when none is recorded. Every function returns,
  every fixture passes, and the panel that exists to surface a 68-vs-106-acre straddle reports one
  number with no election behind it.
  kill_test: `tests/det_core/test_absent_election_refuses_rather_than_defaults`
  negative_check: pending — install a default and confirm the refusal assert goes red
  status: live
- D2: import a convenience helper that transitively pulls a model package. The import list looks
  clean, every unit test passes, and the determinism gate is walking imports rather than the
  resolved graph beneath them.
  kill_test: `tests/det_core/test_reachability_pin`
  negative_check: pending — add a transitive model dependency and confirm the pin diff goes red
  status: live
- D3: compute a page count without rendering. Every number is plausible, and an oversize map
  counts as zero pages or as many, depending on nothing in particular.
  kill_test: `tests/det_core/test_oversize_graphic_counts_as_one_page`
  negative_check: pending — install a character-count estimator
  status: live

## clauses
- [BINDING] origin: specified — a T3 reachability failure blocks delivery of the whole build, not just this node; the assertion is reachability from entry points, which is checkable, rather than absence from the repository, which the functions template makes impossible (kill_test: `tests/det_core/test_reachability_pin`)
- [BINDING] origin: derived — accepting a template upgrade requires re-running the reachability assertion, reading the diff, and re-pinning in the same commit (kill_test: `tests/det_core/test_reachability_pin`)
- [ADVISORY] origin: derived — the objection-process reviewing-officer derivation is an EA/EIS-branch function and is not needed on the categorical-exclusion branch at any phase

## open gaps
- G005 — calendar basis for the +1yr EA and +2yr EIS deadline arithmetic is not declared in the
  statute text. Assumed: calendar year from the trigger date. Fixture authored non-asserting.
  Blocks: MR-1 on the deadline functions.
- G017 — Palantir MCP creates Python transforms repositories but exposes no tool to create a
  TypeScript Functions repository; it can clone one. Assumed: the repository is created once by
  hand and cloned thereafter. Reversible: yes — the alternative is a Python transform, which
  costs the OSDK function binding. Blocks: the walking skeleton's function step.
