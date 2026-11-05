#!/usr/bin/env python3
"""
B6 after deploy: criterion L4 of audit/phase9/B6.log ("Push and live check").

    b6_live_checks.py a4 OUT_DIR VERDICT.json

Five A4 files rebuilt by backend/tests/a4_inputs.py, each posted to the live API
(drug clopidogrel) and run locally against this working tree, compared, and
checked for the rule it exercises. L3 and L5 reuse b5_live_checks.py.
Exits 0 only when every check passes.
"""

from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BASE = "https://pharmaguard-api-baml.onrender.com"
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO / "audit/phase9/live"))

#: case -> (status, error_code, text the rule must show, clopidogrel label for a 200)
EXPECT = {
    "A4-02": (400, "UNSUPPORTED_REFERENCE_BUILD", "GRCh37's chr1", None),
    "A4-03": (200, None, "Chromosome names were read in GRCh38's 'chr' form", "Ineffective"),
    "A4-06": (400, "NOT_VCF", "is a BCF file", None),
    "A4-08b": (200, None, "This file is a gVCF:", "Unknown"),
    "A4-09b": (400, "REFERENCE_ALLELE_MISMATCH", "chr10:94781859", None),
}


def _core(status: int, body: dict) -> dict:
    if status != 200:
        return {"status": status, "error_code": body.get("error_code"), "detail": body.get("detail")}
    labels = {a["drug"]: a["risk_assessment"]["risk_label"] for a in body["analyses"]}
    return {"status": status, "labels": labels, "warnings": body["quality_metrics"]["warnings"]}


def a4(out: Path, verdict_path: Path) -> int:
    os.environ.setdefault("EXPLANATION_MODE", "static")  # as audit/phase9/partb/run_regression.py
    os.chdir(REPO / "backend")
    from fastapi.testclient import TestClient  # noqa: PLC0415

    import measure_warm  # noqa: PLC0415
    from app import main  # noqa: PLC0415
    from tests import a4_inputs  # noqa: PLC0415

    out.mkdir(parents=True, exist_ok=True)
    cases = a4_inputs.build()
    log = out / "requests.jsonl"
    checks, live_cores = {}, {}
    for case_id, (status, code, marker, label) in EXPECT.items():
        case = cases[case_id]
        path = out / f"{case_id}{Path(case.filename).suffix}"
        path.write_bytes(case.data)
        local = TestClient(main.app).post(
            "/analyze", files={"file": (path.name, io.BytesIO(case.data), "text/plain")},
            data={"drugs": "clopidogrel"})
        live = measure_warm.post(BASE, "/analyze", path, "clopidogrel", log, case_id)
        live_body = live["body"] if isinstance(live["body"], dict) else {}
        (out / f"{case_id}.live.json").write_text(json.dumps(live_body, indent=2, sort_keys=True))
        (out / f"{case_id}.local.json").write_text(json.dumps(local.json(), indent=2, sort_keys=True))
        live_core = _core(live["record"]["status"], live_body)
        live_cores[case_id] = live_core
        checks[f"{case_id} live equals local"] = live_core == _core(local.status_code, local.json())
        checks[f"{case_id} status {status}"] = live_core["status"] == status
        if status == 200:
            checks[f"{case_id} clopidogrel {label}"] = live_core["labels"].get("clopidogrel") == label
            checks[f"{case_id} shows {marker!r}"] = any(w.startswith(marker) for w in live_core["warnings"])
        else:
            checks[f"{case_id} {code}"] = live_core["error_code"] == code
            checks[f"{case_id} shows {marker!r}"] = marker in (live_core["detail"] or "")
    ok = all(checks.values())
    verdict_path.write_text(json.dumps({"checks": checks, "all_pass": ok, "live": live_cores}, indent=1) + "\n")
    print(f"a4 live checks: {sum(checks.values())}/{len(checks)} pass")
    return 0 if ok else 1


def main() -> int:
    command, *rest = sys.argv[1:]
    if command == "a4":
        return a4(Path(rest[0]).resolve(), Path(rest[1]).resolve())
    raise SystemExit(f"unknown command {command}")


if __name__ == "__main__":
    sys.exit(main())
