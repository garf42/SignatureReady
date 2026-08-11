# node: n.evals

## assume
[BINDING] origin: specified
- in: n.drafter — one claim or refusal per (slot_id, invocation), with an interaction record per invocation
- in: n.verifier — one verdict per (claim_id, verified_at) with a reason on fail

## guarantee
[BINDING] origin: specified
- out: one row per (drafter, evaluation_run, metric); results land in a dataset with a run timestamp
  so the test series and any live series are comparable
- **binding-resolution rate and value-match rate are reported separately.** A drafter that invents
  a plausible acreage fails the second while passing the first, and reporting one number hides it
- refusal rate on insufficient evidence is reported, and is reported alongside coverage — a drafter
  refusing everything scores perfectly on grounding and produces nothing
- single-claim adherence and selection-set adherence are reported per drafter
- every metric names the invocation count it was computed over; a rate with no denominator is not
  emitted
- **no signal from this node reaches a verifier, a constrained value set, or an element
  requirement.** Signals adjust how content is written, never what counts as sufficient

## oracle
type: relational
risk: reproducibility
MRs below. A measurement node's oracle is the behaviour of its own arithmetic on constructed inputs.

## metamorphic relations
[BINDING] origin: specified
- MR-1 (derivable construction): a run where every claim resolves and half mismatch ⇒
  binding-resolution 1.0 and value-match 0.5, reported as two numbers
- MR-2 (scaling): double the invocation count with identical outcomes ⇒ every rate unchanged and
  every denominator doubled
- MR-3 (re-execution): recompute the same run ⇒ identical metric rows

## demons
- D1: report a single "grounding score" that averages resolution and match. Both properties are
  measured, one number is published, and the invented-value failure is exactly the one it hides.
  kill_test: `tests/evals/test_resolution_and_match_are_separate_rows`
  negative_check: pending — install an averaged metric and confirm MR-1 goes red
  status: live
- D2: feed a rejection reason back as a relaxation of the check that rejected it. Acceptance rate
  climbs, every metric improves, the compliance standard drifts, and the drift is invisible
  precisely because everything continues to pass.
  kill_test: `tests/evals/test_signal_path_cannot_weaken_a_gate`
  negative_check: pending — wire a signal into a verifier threshold and confirm the prohibition
  test goes red
  status: live

## clauses
- [BINDING] origin: specified — attempt, through the signal path, to weaken a verifier, relax a constrained value set, and lower an element requirement. All three refused; this is a prohibition test, not a reporting one (kill_test: `tests/evals/test_signal_path_cannot_weaken_a_gate`)
- [ADVISORY] origin: derived — acceptance rate alone rewards bland, unfalsifiable sentences; median edit distance is the counterweight and the two are read together or neither is read

## open gaps
- G020 — the signal hierarchy's authority ordering is asserted, not measured. Assumed: post-
  implementation reality above external challenge above signature above edits and rejections.
  Reversible: yes — ordering is a stored table.
