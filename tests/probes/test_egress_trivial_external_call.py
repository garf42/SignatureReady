"""Phase -1 prefab probe: foundry.egress.

prefab:     foundry.egress
used_by:    n.rule_corpus, n.authority_ledger, n.precedent
probe_dims: one trivial external call to one public endpoint
gaps:       G034 (closed -- the environment no longer blocks this)

STATUS: **NOT COMPLETE.** No external call has been made from inside Foundry. What this file
establishes is the PRECONDITION, and the precondition is absent.

WHAT RAN, 2026-08-12, through palantir-mcp as christianpinkerton2:

    get_or_create_network_egress_policy(hostname="www.ecfr.gov",  mode="GET")
      -> "No existing network policies found for www.ecfr.gov:443"
    get_or_create_network_egress_policy(hostname="huggingface.co", mode="GET")
      -> "No existing network policies found for huggingface.co:443"

So **this enrollment has no egress policy for either host this build would call**, and a
user workload therefore cannot reach them today. That is a finding, not a failure: the
register already recorded the fallback and it stands --

    "If egress is unavailable, every source is downloadable and bulk upload is the path;
     the build proceeds unaffected. Do not spend a session fighting the network."

WHY THIS FILE STOPS HERE, DELIBERATELY:

`mode="CREATE"` would create the policy, and a **network egress policy is enrollment-scoped,
not folder-scoped.** It is the same class of object as an object type: nothing about the
containment boundary in CLAUDE.md can hold it, because it does not live in a folder. On a
shared training enrollment with ~1,225 object types by many authors, creating enrollment-wide
network configuration is not a probe -- it is a change to everyone's environment. It needs a
decision from the operator, and it is recorded here as such rather than taken quietly.

THE REMAINING WORK, in order:

  1. DECIDE whether an egress policy may be created on this enrollment at all. If no, the
     prefab resolves to "unavailable, bulk upload is the path" and every dependent node is
     unaffected -- that is a legitimate terminal answer and closes this probe.
  2. If yes: `get_or_create_network_egress_policy(hostname=..., mode="CREATE")` for one host.
  3. Make ONE trivial call to it from inside Foundry -- an external transform or a
     TypeScript/Python function -- and record the status code and body.
  4. Record whether the policy had to be attached to the workload explicitly, or whether
     existence at enrollment level was sufficient. That distinction is what the dependent
     nodes actually need, and it is not answerable from documentation.

DO NOT flip `probed` on this prefab until step 3 has produced a real response from a real
external host. A policy that exists is not a call that succeeded.
"""

import sys

VERDICT = "blocked"
ESTABLISHED = [
    "no egress policy exists for www.ecfr.gov:443 on this enrollment",
    "no egress policy exists for huggingface.co:443 on this enrollment",
    "creating one is an enrollment-scoped write and needs an operator decision",
]
REMAINING = [
    "operator decision: may an egress policy be created on a shared training enrollment?",
    "create one policy for one host",
    "make one trivial external call from inside Foundry and record status + body",
    "record whether the policy must be attached to the workload or enrollment-level suffices",
]


def main():
    print("Phase -1 probe: foundry.egress\n")
    print("VERDICT: %s -- the probe has NOT run. Precondition established only.\n" % VERDICT)
    print("ESTABLISHED (via palantir-mcp, 2026-08-12):")
    for line in ESTABLISHED:
        print("  - %s" % line)
    print("\nREMAINING:")
    for i, line in enumerate(REMAINING, 1):
        print("  %d. %s" % (i, line))
    print("\nThis file exits 2 = PENDING A DECISION. It cannot exit 0 until an external call "
          "has actually been made from inside Foundry.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
