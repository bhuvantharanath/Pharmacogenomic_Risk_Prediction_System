#!/usr/bin/env python3
"""
B11 after deploy: criteria L3 and L4 of audit/phase9/B11.log ("Push and live check").

    b11_live_checks.py bundle SHA VERDICT.json       L4: the deployed web bundle carries the commit, the context
                                                     strings and the pooled CYP2C19 figure, and does NOT carry the
                                                     two strings this item deliberately never implemented
    b11_live_checks.py fields LIVE_DIR VERDICT.json  L3: live S1-S6 gene_findings and warnings equal the local B11
                                                     run, and each body equals B10's live body

Exits 0 only when every check passes.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
WEB = "https://pharmaguard-web.pages.dev"
# Cloudflare refuses Python-urllib's default User-Agent (B5.log); name the client plainly.
AGENT = "curl/8.7.1 (phase9-audit)"
LOCAL = REPO / "audit/phase9/partb/B11/s1-s6/s1-s6"
B10_LIVE = REPO / "audit/phase9/partb/B10/live-after-s1s6/s1-s6"

#: Must be in the bundle: the row label, the headline's population phrase, and fragments only the generated table
#: has. A bare "57.1" would be weak evidence in a 3.7 MB bundle, so the figure is checked quoted exactly as the
#: table writes it, and `bundle` additionally requires its interval bounds to sit beside it.
PRESENT = ("South Asian context", "not used for this result", "1000 Genomes cohorts",
           '"reduced_definition"', '"positions_required"', '"PJL"',
           "Poor Metabolizer or Intermediate Metabolizer", '"57.1"')
#: Must NOT be in the bundle. Both are named in the plan as out of scope, so a hit would mean something was built
#: that no plan authorised. They are the negative control for the presence checks above: the same fetch, the same
#: matcher, a string that cannot be there.
ABSENT = ("GenomeIndia", "IndiGen")


def _strip(obj):
    """Drop the fields that differ run to run, so two bodies can be compared whole."""
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items()
                if k not in ("timestamp", "processing_time_ms")}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def bundle(sha: str, verdict: Path) -> int:
    req = urllib.request.Request(f"{WEB}/main.dart.js?b11={sha[:7]}",
                                 headers={"Cache-Control": "no-cache", "User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        js = resp.read().decode("utf-8", "replace")
    checks = {"bundle contains EXPECTED_BACKEND_SHA": sha in js}
    for text in PRESENT:
        checks[f"bundle contains {text!r}"] = text in js
    for text in ABSENT:
        checks[f"negative control: bundle does NOT contain {text!r}"] = text not in js
    # The pooled CYP2C19 figure must carry its own interval, not merely appear somewhere.
    at = js.find('"57.1"')
    window = js[max(0, at - 400):at + 400] if at != -1 else ""
    checks['CYP2C19 57.1 sits beside its interval 53.1-61.0'] = "53.1" in window and "61.0" in window
    ok = all(checks.values())
    verdict.write_text(json.dumps({"checks": checks, "all_pass": ok, "bundle_bytes": len(js)}, indent=1) + "\n")
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
    return 0 if ok else 1


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
        checks[f"{path.stem}: gene_findings equal the local B11 run"] = findings(live) == findings(local)
        checks[f"{path.stem}: warnings equal the local B11 run"] = live_warnings == local_warnings

        # B11 changed no backend file, so the served body must also equal B10's live body.
        previous = B10_LIVE / path.name
        if previous.is_file():
            same = _strip(live) == _strip(json.loads(previous.read_text()))
            checks[f"{path.stem}: body equals B10's live body"] = same
            detail[path.stem] = {"compared_to_b10_live": str(previous.relative_to(REPO)), "equal": same}
        else:
            detail[path.stem] = {"compared_to_b10_live": None,
                                 "note": "no B10 live body kept for this scenario"}
    ok = all(checks.values())
    verdict.write_text(json.dumps({"checks": checks, "all_pass": ok, "detail": detail}, indent=1) + "\n")
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
    return 0 if ok else 1


def main() -> int:
    if sys.argv[1] == "bundle":
        return bundle(sys.argv[2], Path(sys.argv[3]))
    if sys.argv[1] == "fields":
        return fields(Path(sys.argv[2]), Path(sys.argv[3]))
    raise SystemExit(f"unknown command {sys.argv[1]}")


if __name__ == "__main__":
    sys.exit(main())
