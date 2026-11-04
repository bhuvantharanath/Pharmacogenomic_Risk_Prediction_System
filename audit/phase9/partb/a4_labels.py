#!/usr/bin/env python3
"""
The Part A adversarial inputs (A4) through a fresh local API, all six drugs.

    python audit/phase9/partb/a4_labels.py <tag>

Writes audit/phase9/partb/<tag>/a4_labels.json: per case the HTTP status, error
code, every drug's label and the warnings. Unlike audit/phase9/a4/run_a4.py it
never writes into Part A's own `a4/out/`, and it asks for all six drugs, so a
before/after comparison covers every gene the cross-check touches.

The local server runs with RATE_LIMIT_REQUESTS raised: ~35 uploads from one
client would otherwise be refused by the per-client limit after ten, which
measures the limiter rather than the analysis.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PORT = 8011
DRUGS = "clopidogrel,warfarin,codeine,simvastatin,azathioprine,fluorouracil"
INPUTS = REPO / "audit/phase9/a4/inputs"

sys.path.insert(0, str(REPO / "audit/phase9/a4"))
import run_a4  # noqa: E402  (upload() and FILENAMES are reused as-is)


def cases() -> dict[str, Path]:
    manifest = json.loads((INPUTS / "manifest.json").read_text())
    found = {case: REPO / rel for case, rel in manifest.items()}
    found["BASE"] = REPO / "test-data/demo/demo_confident.vcf"
    found["A4-11"] = REPO / "test-data/demo/demo_variants_only.vcf"
    # Added to the inputs directory after the manifest was written.
    for path in sorted(INPUTS.glob("A4-2[2-9]_*.vcf")):
        found.setdefault(path.name.split("_", 1)[0], path)
    return found


def main() -> int:
    tag = sys.argv[1]
    dest = OUT / tag
    dest.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, EXPLANATION_MODE="static", PHARMAGUARD_ENV="development",
               CORS_ALLOWED_ORIGINS="http://localhost:8080", RATE_LIMIT_REQUESTS="1000")
    log = (dest / "a4-server.log").open("w")
    server = subprocess.Popen(
        [str(REPO / "backend/.venv/bin/uvicorn"), "app.main:app", "--port", str(PORT)],
        cwd=REPO / "backend", env=env, stdout=log, stderr=subprocess.STDOUT)
    results = {}
    try:
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2):
                    break
            except Exception:  # noqa: BLE001 — still starting
                time.sleep(0.5)
        else:
            raise SystemExit("local server did not start; see a4-server.log")
        for case, path in sorted(cases().items()):
            name = run_a4.FILENAMES.get(case, path.name)
            status, body, secs = run_a4.upload(
                f"http://127.0.0.1:{PORT}", "/analyze", path.read_bytes(), name, DRUGS)
            body = body or {}
            ok = status == 200
            results[case] = {
                "file": str(path.relative_to(REPO)),
                "status": status,
                "error_code": body.get("error_code"),
                "labels": ({a["drug"]: a["risk_assessment"]["risk_label"]
                            for a in body.get("analyses", [])} if ok else {}),
                "warnings": body.get("quality_metrics", {}).get("warnings", []) if ok else [],
                "position_coverage": body.get("quality_metrics", {}).get("position_coverage", {})
                if ok else {},
                "seconds": round(secs, 2),
            }
            print(f"{case:7} {status} {results[case]['labels'] or results[case]['error_code']}",
                  flush=True)
    finally:
        server.terminate()
        server.wait(timeout=20)
        log.close()
    (dest / "a4_labels.json").write_text(json.dumps(results, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
