# node: n.prior_coverage

## assume
[BINDING] origin: specified
- in: n.precedent — page-anchored chunks; every chunk a substring of its named page
- in: n.ontology — canonical paths, prior determinations, programmatic documents, proposal-record items
- in: n.authority_ledger — authority versions with three tri-state disclosure flags

## guarantee
[BINDING] origin: specified
- out: one row per (target_slot_id, candidate); key unique; ranked candidates with the comparison
  surfaced. **This node supplies candidates and evidence. It elects nothing**
- reuse of a prior categorical-exclusion determination is **two distinct affordances**, materially
  different in cost: substantial sameness of the activities only, versus sameness of the activities,
  the potentially affected environment, and the resources considered. Collapsing them into one
  affordance reuses an entire screen that was never compared
- reliance on an existing document or a portion of one carries its three prongs — nature of the
  proposal, potentially affected environment, anticipated effects — as **three separate human
  judgments**, never one verdict, each with its computed evidence beside it
- every candidate carries the three disclosure flags from n.authority_ledger, tri-state, and they
  print into the environmental document; they are not internal warnings
- programmatic reliance carries the source date: under five years, rely unless substantial new
  circumstances; five or more, a documented reevaluation is required and the node says which,
  because most forest plans are decades old
- a `record_supplied` slot with no candidate emits **"no prior coverage found" carrying the corpus
  and the query**, never silence. An absence with no query behind it is indistinguishable from a
  search that never ran

## oracle
type: relational
risk: semantic
MRs below. Retrieval relevance has no ground truth; the prong separation, the flag propagation and
the explicit-absence property are the checkable part and are what the document rests on.

## metamorphic relations
[BINDING] origin: specified
- MR-1 (orphan isolation): add a candidate from a different administrative forest ⇒ it appears
  ranked and no existing candidate's prong values change
- MR-2 (translation): move a programmatic document's date across the five-year boundary ⇒ reliance
  status flips from rely to reevaluation-required and the required documentation changes with it
- MR-3 (permutation): reorder the corpus ⇒ identical candidate set and identical prong evidence;
  rank may differ only by a declared tiebreak
- MR-4 (idempotence): index the same prior determination twice ⇒ one candidate

## demons
- D1: return the top candidate with its prongs pre-marked "substantially the same." Every reliance
  is supported, every document cites a precedent, and no human judged anything — while the three
  prongs are the entire legal content of a reliance.
  kill_test: `tests/prior_coverage/test_prongs_are_unresolved_human_inputs`
  negative_check: pending — install a pre-marked verdict and confirm the unresolved assert goes red
  status: live
- D2: return an empty result silently when the query matches nothing. The slot reads unsatisfied for
  an unstated reason, and the cheapest possible outcome — that no new analysis is needed at all —
  is unreachable because nobody can tell a miss from a search that never ran.
  kill_test: `tests/prior_coverage/test_empty_result_carries_its_query`
  negative_check: pending — return `[]` on no match and confirm the query assert goes red
  status: live

## clauses
- [BINDING] origin: specified — three prongs are three human judgments; a single sameness verdict is not emitted at any confidence (kill_test: `tests/prior_coverage/test_prongs_are_unresolved_human_inputs`)
- [BINDING] origin: specified — the two reuse tiers are surfaced as distinct affordances with distinct requirements (kill_test: `tests/prior_coverage/test_two_reuse_tiers_are_distinct`)
- [ADVISORY] origin: derived — the highest-value output of this node is sometimes "you do not need to build this," and a node that can never return that is not searching

## open gaps
- G024 — substantial sameness has no numeric test in the rule. Assumed: qualitative human judgment
  against computed evidence, never a score, because a score invites a threshold and a threshold is
  a rule nobody wrote. Reversible: yes. Blocks: MR-1.
