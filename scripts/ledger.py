#!/usr/bin/env python3
"""Atomic append to ledger.jsonl and seams.jsonl.

Parallel agents appending to one JSONL will interleave mid-line and corrupt it.
A plain `open(path, "a").write(...)` is only atomic below PIPE_BUF and only on
some filesystems, which means it works right up until the build is big enough
to matter.

This serialises with an advisory lock, allocates the next id under that lock,
and writes one whole line per call.

Usage:
    python ledger.py build/ledger.jsonl --node n.join --surprise "..." \
        --resolution "..." --clause "..." --kill-test tests/x::y

    from ledger import append
    append("build/ledger.jsonl", {"node": "n.join", "surprise": "..."})
"""

import argparse
import fcntl
import json
import os
import sys
from pathlib import Path

ID_PREFIX = {"ledger": "L", "seams": "S"}


def _next_id(fh, prefix):
    fh.seek(0)
    n = 0
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            got = json.loads(line).get("id", "")
        except json.JSONDecodeError:
            continue
        if isinstance(got, str) and got.startswith(prefix) and got[len(prefix):].isdigit():
            n = max(n, int(got[len(prefix):]))
    return f"{prefix}{n + 1:04d}"


def append(path, record, assign_id=True):
    """Append one record atomically. Returns the record as written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = ID_PREFIX.get(path.stem, "L")

    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        with os.fdopen(fd, "r+", encoding="utf-8") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                if assign_id and "id" not in record:
                    record["id"] = _next_id(fh, prefix)
                fh.seek(0, os.SEEK_END)
                if fh.tell() and not _ends_with_newline(path):
                    fh.write("\n")
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
    except Exception:
        raise
    return record


def _ends_with_newline(path):
    with open(path, "rb") as f:
        try:
            f.seek(-1, os.SEEK_END)
        except OSError:
            return True
        return f.read(1) == b"\n"


def query(path, node):
    """Return entries for one node. The ledger is never read whole."""
    out = []
    p = Path(path)
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("node") == node or r.get("seam", "").endswith(f"->{node}"):
            out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path")
    ap.add_argument("--node")
    ap.add_argument("--phase")
    ap.add_argument("--surprise")
    ap.add_argument("--resolution")
    ap.add_argument("--clause")
    ap.add_argument("--kill-test", dest="kill_test")
    ap.add_argument("--origin", default="derived", choices=["specified", "derived"])
    ap.add_argument("--reversible", action="store_true")
    ap.add_argument("--rediscovered", help="clause id whose reasoning was re-derived")
    ap.add_argument("--query", help="print entries for this node and exit")
    a = ap.parse_args()

    if a.query:
        for r in query(a.path, a.query):
            print(json.dumps(r, ensure_ascii=False))
        return 0

    if not a.clause:
        print("refusing: an entry with no clause is a fix that will recur", file=sys.stderr)
        return 1

    rec = {k: v for k, v in {
        "node": a.node, "phase": a.phase, "surprise": a.surprise,
        "resolution": a.resolution, "clause": a.clause, "kill_test": a.kill_test,
        "origin": a.origin, "reversible": a.reversible,
        "rediscovered": a.rediscovered,
    }.items() if v not in (None, "")}

    print(json.dumps(append(a.path, rec), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
