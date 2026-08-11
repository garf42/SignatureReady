# node: n.verifier

## assume
[BINDING] origin: specified
- in: n.rule_corpus — verbatim, unnormalised source text addressable by citation
- in: n.ontology — canonical path index; one path per value, one value per path

## guarantee
[BINDING] origin: specified
- out: one verdict row per (claim_id, verified_at); verdict ∈ {pass, fail} with a reason on fail
- **two grounding kinds exist and only two.** A third requires an amendment to this guarantee,
  and that clause is the substance of the rule rather than a formality attached to it
- source-grounded: the claim's `verbatim_span` is a literal substring of its named source text.
  Any normalisation applied is named in the verdict; an undeclared transformation fails
- state-grounded: every `{canonical_path, asserted_value}` binding resolves and matches.
  **All-or-nothing** — one unresolvable or mismatched binding rejects the whole claim. There is
  no partial pass and no render with the unresolved part removed
- resolution is against a named path; the verifier never searches for a value that matches
- a claim declaring no `grounding_kind` is refused, never defaulted to the weaker check
- no model dependency is reachable from any verifier entry point; a model may draft a sentence
  and may never verify one

## oracle
type: derivable
risk: semantic
fixture: `fixtures/verifier/four_binding_claim.json` — a claim with four bindings, and its
variants: all matching, one mismatched, one unresolvable, one path absent

## metamorphic relations
[BINDING] origin: specified
- MR-1 (orphan isolation): mutate exactly one of four bindings ⇒ the whole claim fails; no other
  claim's verdict changes
- MR-2 (equivalent rewrite): apply a **declared** normalisation to a verbatim span ⇒ identical
  verdict, with the normalisation named. Apply an undeclared one ⇒ fail
- MR-3 (translation): change the ontology value at an asserted path ⇒ a claim carrying the old
  value fails. A pass here means the verifier is reading a cache
- MR-4 (re-execution): verify the same claim twice in separate processes ⇒ identical verdict

## demons
- D1: return `pass` when a canonical path does not resolve, on the reading that an absent value
  cannot contradict the claim. Every claim renders, no verdict is ever anything but pass, and the
  all-or-nothing rule is satisfied by never reaching the "nothing" branch.
  kill_test: `tests/verifier/test_unresolvable_path_fails`
  negative_check: pending — install `if path not found: return PASS` and confirm the test goes red
  status: live
- D2: on a claim with no declared kind, try the state check and fall back to the source check.
  Every claim gets verified, the refusal path is never exercised, and the producer's declaration
  becomes decoration.
  kill_test: `tests/verifier/test_undeclared_kind_is_refused`
  negative_check: pending — install the fallback chain
  status: live

## clauses
- [BINDING] origin: specified — the kind is declared by the producer and never inferred by the verifier (kill_test: `tests/verifier/test_undeclared_kind_is_refused`)
- [BINDING] origin: specified — a claim is never displayed with a warning attached; it passes or it does not render (kill_test: `tests/verifier/test_no_render_with_warning`)
- [ADVISORY] origin: derived — a source is immutable and ontology state is not. A source-grounded claim verified once stays verified; a state-grounded claim is a statement about the present made from the past, which is why n.assembly re-verifies at emission

## open gaps
- G018 — what "literal substring" admits: whitespace collapse, unicode dash folding, case.
  Assumed: byte-exact, no normalisation, until a declared normalisation rule exists.
  Reversible: yes — each rule is added named and tested.
  Blocks: MR-2.
