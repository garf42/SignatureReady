# node: n.expert_directory

## assume
[BINDING] origin: specified
- in: n.precedent — page-anchored chunks; every chunk a substring of its named page
- in: n.slot_register — the qualification and artifact type an `expert_required` slot needs
- in: n.ontology — positions, disciplines, cooperating-agency designations, privilege markings,
  engagement records, canonical paths

## guarantee
[BINDING] origin: specified
- out: `qualification_holder` one row per holder; `attestation` one row per (holder, document, page,
  role); `contact_channel` one row per (holder, channel); `engagement` one row per (holder, slot,
  request). Keys unique
- **a holder is an organisation, an agency, or a position by default.** An individual is a holder
  only where a contact channel is published by the agency as a point of contact, or where that
  person has opted in. The useful discriminator is discipline plus attested work, not identity
- **an unattested holder is not emitted.** Every holder carries at least one attestation naming the
  document, the page, and the role they are named in — the same page-anchoring discipline the
  precedent corpus is held to, for the same reason: a claim about who did what is checkable or it
  is gossip
- **a contact channel carries published-or-opted-in provenance or is not stored.** A personal detail
  harvested from a document body is never a channel. Those documents were filed for another purpose
- **four sourcing lanes, presented in this order, cheapest first**, because a county officer who is
  not a NEPA expert will not know the first two exist:
  1. **Lead-agency participation** — the Forest Service's own specialists. The subcomponent is
     obliged to outline the information required, provide guidance, and participate in preparation
  2. **Cooperating agency designation** — a Federal, State, Tribal or local agency with jurisdiction
     by law or special expertise. The node surfaces the shall-invite and shall-accept branches,
     because they are obligations rather than options and a denial must be documented and reasoned
  3. **Prior preparer**, attested from the corpus and filtered by discipline and administrative forest
  4. **County roster** — holders this county has engaged, carrying their own outcome record
- **track record is attested facts, never a score**: documents prepared by discipline, dates, and —
  for roster entries — whether the delivered artifact closed the element's coverage gaps, and
  elapsed time against the quoted lead time. No aggregate rating and no ranking by one
- a request package is generated per engagement carrying: the qualification, the artifact type, the
  **element citations the artifact must address**, the lead time, the preparer disclosure statement
  the rule requires of any third-party preparer, and — where the holder is a non-Federal agency — a
  confidentiality commitment, which is required, and no waiver of the right to judicial review,
  which may not be
- a holder record carries privilege marking where the underlying item falls within the withholding
  provisions; outside production, every individual name is synthetic and flagged as such
- **the directory is searched by qualification, never by slot content.** It never sees the analysis

## oracle
type: relational
risk: semantic
MRs below. Retrieval relevance and suitability have no ground truth. The attestation anchoring, the
channel provenance, the absence of an aggregate score, and the lane ordering are the checkable part,
and they are what protects a user who cannot evaluate the answer.

## metamorphic relations
[BINDING] origin: specified
- MR-1 (orphan isolation): index a document naming a new holder ⇒ one new holder, or one new
  attestation on an existing one, and no existing attestation's evidence changes
- MR-2 (permutation): reorder the corpus ⇒ identical holder set and identical attestation evidence;
  rank differs only by a declared tiebreak
- MR-3 (idempotence): index the same document twice ⇒ one attestation per (holder, document, page,
  role)
- MR-4 (translation): move an engagement's delivery date ⇒ the elapsed-against-quoted figure moves
  with it and nothing aggregates, because there is nothing to aggregate

## demons
- D1: rank holders by how often they appear in the corpus. Every result is attested, every page
  anchor resolves, the list looks authoritative — and it measures volume of output rather than
  whether any artifact ever closed a gap. The county with no NEPA expertise takes the top result,
  which is exactly the user this node exists for.
  kill_test: `tests/expert_directory/test_ranking_evidence_is_gap_closure_not_frequency`
  negative_check: pending — install a frequency sort and confirm the evidence-type assert goes red
  status: live
- D2: harvest a personal email from a document body and store it as a channel. Every holder becomes
  contactable, the workflow runs end to end, and the app has assembled a contact database out of
  names that appeared in public filings for an unrelated purpose.
  kill_test: `tests/expert_directory/test_channel_requires_published_or_optin_provenance`
  negative_check: pending — install body extraction and confirm the provenance assert goes red
  status: live
- D3: emit an aggregate suitability score. It sorts cleanly, it hides the small sample behind every
  holder, and the moment it exists someone sets a threshold — which is a qualification rule nobody
  wrote and no regulation supports.
  kill_test: `tests/expert_directory/test_no_aggregate_score_is_emitted`
  negative_check: pending — add a weighted score and confirm the assert goes red
  status: live
- D4: present only the procurement lanes. Every search returns results, every slot gets routed, and
  the two lanes that cost nothing — the lead agency's own specialists, and a cooperating agency the
  responsible official may be obliged to accept — are never offered.
  kill_test: `tests/expert_directory/test_four_lanes_present_in_order`
  negative_check: pending — drop the first two lanes and confirm the lane assert goes red
  status: live

## clauses
- [BINDING] origin: specified — a holder is emitted only with an attestation naming document, page and role (kill_test: `tests/expert_directory/test_holder_requires_attestation`) (clause: n.expert_directory/c1)
- [BINDING] origin: specified — a contact channel carries published-or-opted-in provenance or it is not stored, in any environment (kill_test: `tests/expert_directory/test_channel_requires_published_or_optin_provenance`) (clause: n.expert_directory/c2)
- [BINDING] origin: specified — track record is attested facts; no aggregate rating is computed, stored or displayed (kill_test: `tests/expert_directory/test_no_aggregate_score_is_emitted`) (clause: n.expert_directory/c3)
- [BINDING] origin: derived — the request package carries the element citations the artifact must address, so the returning artifact can be coverage-gap checked against the same list it was requested against (kill_test: `tests/expert_directory/test_request_carries_element_citations`) (clause: n.expert_directory/c4)
- [ADVISORY] origin: derived — for several disciplines the right answer is a cooperating-agency designation rather than a procurement, and the statutory path has shall-invite and shall-accept branches a county officer has no reason to know exist (clause: n.expert_directory/c5)
## open gaps
- G028 — whether preparer and consulted-persons sections are consistently present in the corpus and
  extractable at useful precision. Assumed: present in a minority; the node reports its extraction
  yield rather than implying coverage. Reversible: yes.
  Blocks: lane 3's usefulness, and MR-1.
- G029 — the standing tension: the constitution forbids real personally identifiable information in
  any environment, and this capability's value depends on knowing who did the work.
  Assumed: holder is an organisation, agency or position by default; an individual only with a
  published or opted-in channel; outside production every individual name is synthetic and flagged.
  Reversible: yes — the resolution is a policy on one field. Blocks: any production deployment.
- G030 — whether "in-app contact" means the app transmits the request, or composes a request package
  the user sends. Assumed: the app composes, tracks and receives — every piece of state is in-app —
  and transmission is a channel integration probed before it is built. Reversible: yes.
  Blocks: the engagement's send step.
