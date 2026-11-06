#!/usr/bin/env python3
"""
B10 fixtures: real /analyze responses with a supplied CYP2D6 call, for the client and export tests.

    backend/.venv/bin/python audit/phase9/partb/b10_fixtures.py

The backend in-process (FastAPI TestClient, the real PharmCAT jar, the regression tool's environment) on
test-data/demo/demo_na12273_1000g.vcf:
  X2_supplied_cyp2d6   codeine and clopidogrel, CYP2D6 *4/*4 supplied by Cyrius (codeine Ineffective)
  X3_supplied_xn       codeine, CYP2D6 *1xN/*4 supplied by Cyrius (codeine Unknown: no CPIC phenotype)
Writes app/test/fixtures/responses/. Exits non-zero unless each is a 200 with supplied_by set on codeine.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "app/test/fixtures/responses"
VCF = REPO / "test-data/demo/demo_na12273_1000g.vcf"
CASES = {
    "X2_supplied_cyp2d6": ("codeine,clopidogrel", "*4/*4", "Cyrius", "Ineffective"),
    "X3_supplied_xn": ("codeine", "*1xN/*4", "Cyrius", "Unknown"),
}

os.environ.update(EXPLANATION_MODE="static", CORS_ALLOWED_ORIGINS="http://localhost:8080",
                  PHARMAGUARD_ENV="development")
sys.path.insert(0, str(REPO / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

import app.main as main  # noqa: E402
from app import security  # noqa: E402


def run() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (drugs, diplotype, caller, expected) in CASES.items():
        security.limiter.reset()
        response = TestClient(main.app).post(
            "/analyze", files={"file": (VCF.name, VCF.read_bytes(), "text/plain")},
            data={"drugs": drugs, "cyp2d6_diplotype": diplotype, "cyp2d6_caller": caller})
        body = response.json()
        codeine = next((a for a in body.get("analyses", []) if a["drug"] == "codeine"), None)
        if (response.status_code != 200 or codeine is None
                or codeine["pharmacogenomic_profile"]["supplied_by"] != caller
                or codeine["risk_assessment"]["risk_label"] != expected):
            print(f"{name} failed: status {response.status_code}")
            return 1
        (OUT / f"{name}.json").write_text(json.dumps(body, indent=1) + "\n")
        print(name, [(a["drug"], a["risk_assessment"]["risk_label"], a["pharmacogenomic_profile"]["supplied_by"])
                     for a in body["analyses"]])
    return 0


if __name__ == "__main__":
    sys.exit(run())
