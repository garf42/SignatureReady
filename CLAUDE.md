# Working on SignatureReady

Orientation for a new session. Everything here was established by execution on **2026-08-12** and
is recorded so it is not re-derived. Where something is unverified, it says so.

Read [`build/README.md`](build/README.md) for the plan itself and
[`PHASE-MINUS-1.md`](PHASE-MINUS-1.md) for probe status. This file is about the environment.

## The enrollment

| | |
|---|---|
| stack | `https://ontologize.palantirfoundry.com` |
| identity | `christianpinkerton2@gmail.com` — orgs *American Tech Fellowship*, *Public* |
| ontology RID | `ri.ontology.main.ontology.aa2788ae-95a9-4704-8e7b-97ef0a3a366c` |
| namespace folder | `/American Tech Fellowship-051c39` — `ri.compass.main.folder.d051d386-fffb-40ae-bb88-87faac54e6a1` |

**It is a shared training enrollment.** The ontology holds ~1,225 object types by many authors, and
every other participant's `PERSONAL PROJECT: <handle>` folder is readable from this token. Read
access being enrollment-wide does not make write access appropriate.

## Where work goes — this is a hard boundary

Everything this build creates lands under:

```
/American Tech Fellowship-051c39/PERSONAL PROJECT: christianpinkerton2
  ri.compass.main.folder.dafae169-ed9c-40b2-8226-9cc7299785bc
└── Capstone                    ri.compass.main.folder.38bd3e1c-a98f-49f1-ad9d-d2f24d9aa609
    └── SignatureReady_v2       ri.compass.main.folder.33efbf75-6ac5-4a72-a445-dc84fa6809b5   ← here
```

Before any create/update/delete, resolve the target's parent and confirm it sits under that
personal-project RID.

**Object types are the sharp edge.** They are created into the *shared* ontology, not into a
folder, so a folder check cannot contain them. They carry the display prefix `[SR2]` and the
apiName prefix `Sr2` instead — see the constitution's *Namespace and non-collision* section, which
is BINDING.

## The prior build — do not touch it

`Capstone/SignatureReady_county-prepared NEPA proposal records under GNA` is an earlier generation
of this same project, built in Palantir's AI FDE. It holds 6 `[SignatureReady]` object types
(apiName prefix `Sr`), 6 relations, an action type, Magritte sources S1–S9, three repos and a
deployed app.

It is **superseded, not extended.** Nothing in it is read as an input, imported, or modified. Its
`DEC-###` / `REQ-####` / `GAP-A-##` identifiers are not this build's identifiers — this build uses
`G0##` for gaps and `L0###` for the ledger. Do not reconcile the two numbering schemes; do not
inherit its claims.

## What works

- **Palantir MCP** — `palantir-mcp@0.14.0`, configured in `~/.mcp.json`. This is the correct
  server: it is for ontology *builders* and creates/modifies object, link and action types.
  It **cannot write ontology data** (G016) — data goes through datasets plus a pipeline, or Actions.
  *Ontology MCP (OMCP)* is a different product for ontology *consumers*; it is not an npm package
  and we do not need it.
- **SuperRepo** — available, contrary to the register's hedge. See G032. The CLI is **already
  installed** at `~/.local/bin/foundry` — 179,411,392 bytes, x86-64 ELF,
  sha256 `062130e9041a6195245a497e8ae726484cd0c1a7280562a3ea9099b651ed9318`, fetched from
  `ri.foundry.cli.artifacts.repository` on 2026-08-12. It has **never been executed** and
  `foundry login` has **never been run**, so no subcommand and no `minCliVersion` is confirmed.
  It was placed by hand rather than by the vendor installer, deliberately: that installer also
  appends a PATH export to `~/.bashrc` and runs `foundry login --non-interactive`, and neither
  belongs in a probe. `~/.local/bin` may not be on PATH — invoke it by full path.
  Authenticate with `foundry login refresh`, which is a browser OAuth flow and needs no static
  token. Re-downloading it would need a credential, so do not delete it casually.
- **GitHub** — `gh` authenticated as `garf42`, scopes `gist, read:org, repo, workflow`.
  `git push` works. Remote `github.com/garf42/SignatureReady`.
- **Egress** — open to eCFR, Federal Register, HuggingFace, npm, raw.githubusercontent.
- **Toolchain** — Node v24.19.0 + npm 11.17.0 at `/usr/local`; Python 3.11.2 **stdlib only** (no
  pip, no `requests`, no `pytest` — probes use `urllib.request`, suites run standalone).

## Credentials — read this before debugging an auth failure

There are **two independent credentials**, and they fail independently:

1. `FOUNDRY_TOKEN` in `~/.mcp.json` — a static user token. It was found **expired** on 2026-08-12
   while MCP was working fine.
2. `~/.palantir/mcp-config.json` (mode 600) — the credential `@palantir/mcp` holds for itself.

**A working MCP server is not evidence that the configured token is valid.** Test them apart:
`/multipass/api/me` returns 200 for a good token, and `Default:Unauthorized` with
`parameters.error = EXPIRED` for a dead one. Use `scripts/foundry_api.sh` — it never prints the
token.

**Expect source 1 to be dead.** The `FOUNDRY_TOKEN` in `~/.mcp.json` is the expired one, and the
short-lived user token that answered on 2026-08-12 was deactivated deliberately after the CLI was
fetched. So `scripts/foundry_api.sh` will fail until a credential exists, and that is the correct
state, not a regression. **Do not ask the operator for a pasted user token** — prefer, in order:
the in-platform SuperRepo flow at `<stack>/workspace/code/superrepo`, which provisions a
restricted install token; then `foundry login refresh`, a browser OAuth flow. Neither needs a
long-lived secret in a config file, and MCP is unaffected by all of this because it holds its own
credential.

`palantir-mcp` on npm is only a **wrapper**; it downloads and runs `@palantir/mcp` from the
enrollment's own artifacts registry (`ri.artifacts.repository.discovered.foundry-mcp`). That is the
same channel the CLI uses.

Prefer OAuth over static tokens. The install token is needed *only* to fetch the CLI and can be
deactivated afterwards; `foundry login refresh` re-authorizes in a browser.

## Permission rules

The auto-mode classifier blocks reading a credential from a file and sending it to a host, and
blocks executing a freshly downloaded binary. Both are correct. Claude **cannot** grant itself
these — editing `.claude/settings.local.json` is itself blocked. Ask the user to approve the rules
listed in that file's history, or run the command yourself with a `!` prefix.

## Order of work

Run the gate first; it is red **on purpose** and its red is the work order:

```bash
python3 scripts/check.py build/ --phase 0     # 11 violations, all `probed is false`
python3 tests/build/test_gate.py              # must be green
python3 tests/build/test_packet.py            # must be green
python3 tests/build/test_plan_prose.py        # must be green — it re-derives the plan's own counts
```

`test_plan_prose.py` binds `build/README.md`'s stated numbers to reality. **If you change the
constitution's line count, the gap count, the prefab split or the violation count, update
`build/README.md` in the same commit** or it goes red.

Never hand-edit `build/ledger.jsonl` or `build/seams.jsonl` — parallel appends interleave. Use
`scripts/ledger.py`.

Agents never read `build/` directly. Assemble a packet:

```bash
python3 scripts/packet.py build/ n.ontology
```
