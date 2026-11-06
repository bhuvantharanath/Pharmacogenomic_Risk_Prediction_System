#!/usr/bin/env python3
"""
B9 after deploy: criteria L4 and L5 of audit/phase9/B9.log ("Push and live check").

    b9_live_checks.py bundle SHA VERDICT.json       L4: the deployed web bundle carries the commit and the new control
    b9_live_checks.py exports LIVE_DIR VERDICT.json L5: the live S1-S6 responses, exported by the same code, validate

No uploads: the bundle is a static file, and the export runs on responses already fetched.
Exits 0 only when every check passes.
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
WEB = "https://pharmaguard-web.pages.dev"
# Cloudflare refuses Python-urllib's default User-Agent (B5.log); name the client plainly.
AGENT = "curl/8.7.1 (phase9-audit)"
CONTROL_TEXT = ("Download report", "PDF summary (.pdf)", "FHIR Genomics Report (.json)")


def bundle(sha: str, verdict: Path) -> int:
    req = urllib.request.Request(f"{WEB}/main.dart.js?b9={sha[:7]}",
                                 headers={"Cache-Control": "no-cache", "User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        js = resp.read().decode("utf-8", "replace")
    checks = {"bundle contains EXPECTED_BACKEND_SHA": sha in js}
    for text in CONTROL_TEXT:
        checks[f"bundle contains {text!r}"] = text in js
    ok = all(checks.values())
    verdict.write_text(json.dumps({"checks": checks, "all_pass": ok, "bundle_bytes": len(js)}, indent=1) + "\n")
    print(f"bundle live checks: {sum(checks.values())}/{len(checks)} pass")
    return 0 if ok else 1


def exports(live_dir: str, verdict: Path) -> int:
    proc = subprocess.run([sys.executable, str(REPO / "scripts/validate_fhir_exports.py"),
                           "--responses", live_dir, "--report", str(verdict)],
                          cwd=REPO, capture_output=True, text=True, check=False)
    print(proc.stdout, end="")
    print(proc.stderr, end="", file=sys.stderr)
    return proc.returncode


def main() -> int:
    command, arg, verdict = sys.argv[1:4]
    if command == "bundle":
        return bundle(arg, Path(verdict))
    if command == "exports":
        return exports(arg, Path(verdict))
    raise SystemExit(f"unknown command {command}")


if __name__ == "__main__":
    sys.exit(main())
