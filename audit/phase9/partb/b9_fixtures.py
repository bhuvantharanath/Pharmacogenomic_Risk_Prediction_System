#!/usr/bin/env python3
"""
B9 fixtures: real /analyze responses for the export tests (audit/phase9/B9_PLAN.md, section 5).

    backend/.venv/bin/python audit/phase9/partb/b9_fixtures.py

Copies S1-S6 from the local B8 run (audit/phase9/partb/B8/s1-s6/s1-s6) and makes X1: the backend in-process
(FastAPI TestClient, the real PharmCAT jar, the regression tool's environment) on demo_confident.vcf with every
capability drug plus ibuprofen, which has none. Writes app/test/fixtures/responses/. Exits non-zero if X1 is not a
200 or does not answer every drug asked.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "app/test/fixtures/responses"
B8_S1S6 = REPO / "audit/phase9/partb/B8/s1-s6/s1-s6"
X1_DRUGS = ["clopidogrel", "fluorouracil", "azathioprine", "simvastatin", "warfarin", "codeine", "ibuprofen"]

os.environ.update(EXPLANATION_MODE="static", CORS_ALLOWED_ORIGINS="http://localhost:8080",
                  PHARMAGUARD_ENV="development")
sys.path.insert(0, str(REPO / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

import app.main as main  # noqa: E402


def main_() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in sorted(B8_S1S6.glob("S*.json")):
        shutil.copyfile(path, OUT / path.name)
        print(f"copied {path.name}")
    vcf = REPO / "test-data/demo/demo_confident.vcf"
    response = TestClient(main.app).post(
        "/analyze", files={"file": (vcf.name, vcf.read_bytes(), "text/plain")}, data={"drugs": ",".join(X1_DRUGS)})
    body = response.json()
    answered = [a["drug"] for a in body.get("analyses", [])] if response.status_code == 200 else []
    if response.status_code != 200 or sorted(answered) != sorted(X1_DRUGS):
        print(f"X1 failed: status {response.status_code}, drugs {answered}")
        return 1
    (OUT / "X1_all_drugs.json").write_text(json.dumps(body, indent=1) + "\n")
    print("X1_all_drugs:", [(a["drug"], a["risk_assessment"]["risk_label"]) for a in body["analyses"]])
    return 0


if __name__ == "__main__":
    sys.exit(main_())
