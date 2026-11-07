#!/usr/bin/env python3
"""
F-20 after deploy: criterion L3 of audit/phase9/F20.log ("Push and live check").

    f20_live_checks.py fields LIVE_DIR VERDICT.json   live S1-S6 gene_findings and warnings equal the local F20 run,
                                                      and each body equals B12's live body

F-20 closes a branch no real input reaches, so nothing served may change. Exits 0 only when every check passes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LOCAL = REPO / "audit/phase9/partb/F20/s1-s6/s1-s6"
B12_LIVE = REPO / "audit/phase9/partb/B12/live-after-s1s6/s1-s6"


def _strip(obj):
    """Drop the fields that differ run to run, so two bodies can be compared whole."""
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in ("timestamp", "processing_time_ms")}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def fields(live_dir: Path, verdict: Path) -> int:
    checks, detail = {}, {}
    paths = sorted(live_dir.glob("S*.json"))
    checks["all six scenarios present"] = len(paths) == 6
    for path in paths:
        live = json.loads(path.read_text())
        local = json.loads((LOCAL / path.name).read_text())

        def findings(body):
            return {a["drug"]: (a.get("pharmacogenomic_profile") or {}).get("gene_findings")
                    for a in body.get("analyses", [])}

        live_warnings = (live.get("quality_metrics") or {}).get("warnings") or []
        local_warnings = (local.get("quality_metrics") or {}).get("warnings") or []
        checks[f"{path.stem}: gene_findings equal the local F20 run"] = findings(live) == findings(local)
        checks[f"{path.stem}: warnings equal the local F20 run"] = live_warnings == local_warnings
        previous = B12_LIVE / path.name
        same = previous.is_file() and _strip(live) == _strip(json.loads(previous.read_text()))
        checks[f"{path.stem}: body equals B12's live body"] = same
        detail[path.stem] = {"compared_to_b12_live": str(previous.relative_to(REPO)), "equal": same}
    ok = all(checks.values())
    verdict.write_text(json.dumps({"checks": checks, "all_pass": ok, "detail": detail}, indent=1) + "\n")
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
    return 0 if ok else 1


def main() -> int:
    if sys.argv[1] == "fields":
        return fields(Path(sys.argv[2]), Path(sys.argv[3]))
    raise SystemExit(f"unknown command {sys.argv[1]}")


if __name__ == "__main__":
    sys.exit(main())
