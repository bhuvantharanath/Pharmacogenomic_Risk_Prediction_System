#!/usr/bin/env python3
"""
B12 after deploy: criteria L3 and L4 of audit/phase9/B12.log ("Push and live check").

    b12_live_checks.py bundle SHA VERDICT.json       L4: the deployed bundle carries the commit and the new token
                                                     values, and no longer carries the colour B12 replaced
    b12_live_checks.py fields LIVE_DIR VERDICT.json  L3: live S1-S6 gene_findings and warnings equal the local B12
                                                     run, and each body equals B11's live body

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
LOCAL = REPO / "audit/phase9/partb/B12/s1-s6/s1-s6"
B11_LIVE = REPO / "audit/phase9/partb/B11/live-after-s1s6/s1-s6"

#: Colours, checked in the encoding dart2js actually emits (B12_L4_AMENDMENT.md). Flutter's Color stores its
#: channels as doubles, so no hex string of a colour is in the bundle at all - the first form of this check looked
#: for hex and could not have passed for a correct deployment, and its negative control could not have failed.
#: (name, 0xAARRGGBB, must_be_present)
COLOURS = (
    ("rule (unchanged by B12)", 0xFFD3DACE, True),
    ("accent (unchanged by B12)", 0xFF5A3A5F, True),
    ("ink3, the new value", 0xFF646E67, True),
    ("controlEdge", 0xFF848A80, True),
    ("accentControlEdge", 0xFF968398, True),
    ("ink3, the superseded failing value", 0xFF7D8A81, False),
    ("a colour never used in the app", 0xFF123456, False),
)
#: Plain strings that must not be there: out of scope at B11 and still unimplemented.
ABSENT_TEXT = ("GenomeIndia", "IndiGen")
#: How close the three channel literals must sit to count as one colour.
WINDOW = 300


def _strip(obj):
    """Drop the fields that differ run to run, so two bodies can be compared whole."""
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in ("timestamp", "processing_time_ms")}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def _colour_present(js: str, value: int) -> bool:
    """True when the colour's three channel literals co-occur within WINDOW characters.

    Each channel alone is meaningless - 0.39215686 is only "some channel equal to 100" - so the three have to be
    found together to say the colour itself is in the bundle.
    """
    r, g, b = (repr((value >> shift & 0xFF) / 255) for shift in (16, 8, 0))
    start = 0
    while True:
        i = js.find(r, start)
        if i == -1:
            return False
        segment = js[max(0, i - WINDOW): i + WINDOW]
        if g in segment and b in segment:
            return True
        start = i + 1


def bundle(sha: str, verdict: Path) -> int:
    req = urllib.request.Request(f"{WEB}/main.dart.js?b12={sha[:7]}",
                                 headers={"Cache-Control": "no-cache", "User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        js = resp.read().decode("utf-8", "replace")
    checks = {"bundle contains EXPECTED_BACKEND_SHA": sha in js}
    for name, value, want_present in COLOURS:
        found = _colour_present(js, value)
        label = ("bundle carries" if want_present else "negative control: bundle does NOT carry")
        checks[f"{label} {name} #{value & 0xFFFFFF:06X}"] = found == want_present
    for text in ABSENT_TEXT:
        checks[f"negative control: bundle does NOT contain {text!r}"] = text not in js
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
        checks[f"{path.stem}: gene_findings equal the local B12 run"] = findings(live) == findings(local)
        checks[f"{path.stem}: warnings equal the local B12 run"] = live_warnings == local_warnings

        previous = B11_LIVE / path.name
        if previous.is_file():
            same = _strip(live) == _strip(json.loads(previous.read_text()))
            checks[f"{path.stem}: body equals B11's live body"] = same
            detail[path.stem] = {"compared_to_b11_live": str(previous.relative_to(REPO)), "equal": same}
        else:
            detail[path.stem] = {"compared_to_b11_live": None,
                                 "note": "no B11 live body kept for this scenario"}
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
