#!/usr/bin/env python3
"""Compare the working tree with a frozen candidate inventory.

Usage: inventory_compare.py <repo> <frozen-inventory.json> <out.json>

Symlinks hash their dereferenced content (the frozen Prompt 7 convention);
link type and target are recorded separately.
"""
import hashlib, json, os, sys
from pathlib import Path

repo, frozen_path, out_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
frozen = json.loads(frozen_path.read_text())

def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

current, diffs = [], []
for e in frozen:
    p = repo / e["path"]
    rec = {"path": e["path"], "intended": e.get("intended"), "symlink": p.is_symlink()}
    if p.is_symlink():
        rec["link_target"] = os.readlink(p)
    if not p.exists():
        rec.update(exists=False)
        diffs.append({"path": e["path"], "kind": "missing", "frozen_sha256": e["sha256"]})
    else:
        rec.update(exists=True, bytes=p.stat().st_size, sha256=sha(p))
        if rec["sha256"] != e["sha256"] or rec["bytes"] != e["bytes"]:
            diffs.append({"path": e["path"], "kind": "changed",
                          "frozen_sha256": e["sha256"], "current_sha256": rec["sha256"],
                          "frozen_bytes": e["bytes"], "current_bytes": rec["bytes"]})
        if bool(e.get("symlink")) != rec["symlink"]:
            diffs.append({"path": e["path"], "kind": "symlink-flag-changed"})
    current.append(rec)

canon = json.dumps(current, sort_keys=True, separators=(",", ":")).encode()
out = {
    "frozen_inventory": str(frozen_path),
    "frozen_inventory_sha256": sha(frozen_path),
    "entries": len(frozen),
    "differences": diffs,
    "current_inventory_canonical_sha256": hashlib.sha256(canon).hexdigest(),
    "current": current,
}
out_path.write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != "current"}, indent=1))
