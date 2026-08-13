"""Phase -1 prefab probe: aip.document-intelligence.

prefab:     aip.document-intelligence
used_by:    n.precedent, n.expert_directory
probe_dims: three USFS documents, one scanned, one with a chunk straddling a page break; plus
            one carrying a list-of-preparers section, to measure named-role extraction yield
gaps:       G034 (closed -- the environment no longer blocks this)

STATUS: **NOT COMPLETE, and deliberately so.** Nothing here was executed against a document.
Everything below is read from Palantir's own documentation, and *documentation is not a probe* --
that is a standing ground rule of this build. What follows NARROWS the question; it does not
answer it.

WHY THIS PREFAB GOT MORE IMPORTANT, not less
--------------------------------------------
The NEPATEC2.0 probe established that `prepared_by` names ORGANISATIONS and never individuals --
populated on 208 of 210 USDA documents, 165 of them ';'- or newline-delimited multi-org blobs.
n.expert_directory/c1 requires an attestation naming **document, page and role**. `prepared_by`
supplies none of the three. So named individuals must come from page text, and this prefab is
the only thing that can produce them. See L0023.

WHAT THE DOCUMENTATION SAYS -- narrowing, not answering
------------------------------------------------------
AIP Document Intelligence operates over **media sets**, and exposes two document-to-text media
transformations (the docs mark these as replacing `extractLayoutAwareContent` and `ocrOnPage`):

    extractTextV2               -> a list of strings of extracted document text
    extractLayoutAwareTextV2    -> "a list of layout-aware text blocks ACROSS PAGES"

Both accept:

    pageRange: { startPageInclusive: 0, endPageExclusive: 5 }
    config:    { mode: "SCAN" | "ELECTRONIC" | "AUTO",
                 format: "TEXT" | "MARKDOWN" | "HTML",
                 languages: [...] }

Three things follow, and only the first is close to what the register asked:

  1. **Page range is a first-class input**, and `extractLayoutAwareTextV2` is documented as
     returning blocks *across pages*. The register's requirement was "establish whether it is
     available and whether it returns page numbers". Availability of the OPERATION is documented.
     **Whether the returned block carries a page number as a field is NOT stated by the docs**
     and must be read off a real response. Do not assume it does; page anchoring is the whole
     reason this prefab is on the critical path (n.precedent/c1, demon D1).
  2. `mode: "SCAN"` vs `"ELECTRONIC"` vs `"AUTO"` is exactly the scanned-document dimension the
     probe_dims asked for, and it is a config flag rather than a separate strategy.
  3. The deployment path is a generated **Python transforms repository** over a media set, not a
     callable API -- so exercising this at real dimensions means creating a repo and a media set,
     which lands squarely inside the containment boundary and must go under SignatureReady_v2.

WHAT IS STILL COMPLETELY UNKNOWN
--------------------------------
  - **Is AIP Document Intelligence enabled on THIS enrollment?** Unasked and unanswered. The
    documentation search that produced the above is served to every reader; it says nothing
    about entitlement here.
  - Whether a returned text block carries a page identifier, and in what field.
  - Yield on a list-of-preparers section -- the n.expert_directory question, which is a
    measurement and cannot be inferred at all.
  - Behaviour on a chunk straddling a page break, which is demon D1's kill test in another guise.

THE REMAINING WORK, in order
----------------------------
  1. Establish entitlement: open AIP Document Intelligence on the stack, or fail trying, and
     record which. Everything below is moot if it is off.
  2. Create a media set under SignatureReady_v2 and upload three USFS documents -- one scanned,
     one with a chunk straddling a page break, one carrying a list of preparers. The corpus
     probe's Forest-Service EIS projects are a source for these.
  3. Run `extractLayoutAwareTextV2` with an explicit `pageRange` and **record the raw response
     shape**, specifically whether a page number is present per block and what it is called.
  4. Measure named-role yield on the list-of-preparers document. Report the number found and the
     number of preparers actually present -- a yield with no denominator is not a measurement.
  5. Only then flip `probed`.

DO NOT flip `probed` on the strength of this file. It is a reading list with a runbook attached.
"""

import sys

VERDICT = "blocked"


def main():
    print("Phase -1 probe: aip.document-intelligence\n")
    print("VERDICT: %s -- NOT PROBED. Documentation read, nothing executed.\n" % VERDICT)
    print("NARROWED (from Palantir docs, 2026-08-12):")
    print("  - extractTextV2 and extractLayoutAwareTextV2 are the two document-to-text ops")
    print("  - both take pageRange {startPageInclusive, endPageExclusive}")
    print("  - config.mode SCAN | ELECTRONIC | AUTO covers the scanned-document dimension")
    print("  - extractLayoutAwareTextV2 is documented as returning blocks ACROSS PAGES")
    print("\nSTILL UNKNOWN -- and these are the ones that matter:")
    print("  - is AIP Document Intelligence entitled on THIS enrollment? UNASKED")
    print("  - does a returned block carry a PAGE NUMBER field? docs do not say")
    print("  - named-role yield on a list-of-preparers section: unmeasured")
    print("  - behaviour on a chunk straddling a page break: unmeasured")
    print("\nThis prefab became MORE load-bearing, not less: NEPATEC2.0's prepared_by names")
    print("organisations only, so n.expert_directory/c1's document+page+role attestation has")
    print("no source but page text. See L0023.")
    print("\nExits 2 = PENDING. Documentation is not a probe.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
