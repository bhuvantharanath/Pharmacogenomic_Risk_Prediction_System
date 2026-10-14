"""Exercise every evidence-table fixture through the real local API and the pinned JAR.

Usage: api_harness.py <label>
Writes api-harness-<label>/: per-fixture coverage/analyze bodies, direct PharmCAT
reports, parser output and a stage-by-stage trace. Expectations come from the
frozen EVIDENCE-TABLE.json; nothing here edits a fixture or an expectation.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "backend"))
from app.pharmcat_runner import parse_report  # noqa: E402  (stage: parser)

label = sys.argv[1]
OUT = HERE / f"api-harness-{label}"
OUT.mkdir(exist_ok=True)
API = "http://127.0.0.1:8000"
JAVA = "/opt/homebrew/opt/openjdk@17/bin/java"
JAR = REPO / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
table = json.loads((HERE / "fixtures/EVIDENCE-TABLE.json").read_text())


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def post(endpoint: str, path: Path, drugs: str | None):
    data = {"drugs": drugs} if drugs else {}
    started = time.monotonic()
    with httpx.Client(timeout=300) as client, path.open("rb") as handle:
        response = client.post(f"{API}/{endpoint}", files={"file": (path.name, handle)}, data=data)
    elapsed = time.monotonic() - started
    try:
        body = response.json()
    except ValueError:
        body = {"_non_json": response.text[:2000]}
    return response.status_code, body, elapsed, response.content


def direct_pharmcat(fid: str, path: Path):
    dest = OUT / "pharmcat-direct" / fid
    dest.mkdir(parents=True, exist_ok=True)
    argv = [JAVA, "-jar", str(JAR), "-vcf", str(path), "-o", str(dest), "-reporterJson"]
    started = time.monotonic()
    done = subprocess.run(argv, capture_output=True, text=True, timeout=600)
    receipt = {"argv": argv, "exit_code": done.returncode, "seconds": time.monotonic() - started,
               "stdout_tail": done.stdout[-1500:], "stderr_tail": done.stderr[-1500:]}
    reports = sorted(dest.glob("*.report.json"))
    if done.returncode == 0 and reports:
        raw = json.loads(reports[0].read_text())
        receipt["report"] = str(reports[0].relative_to(HERE))
        receipt["report_sha256"] = sha(reports[0].read_bytes())
        receipt["pharmcat_version"] = raw.get("pharmcatVersion")
        receipt["data_version"] = raw.get("dataVersion")
        parsed = parse_report(raw).model_dump(mode="json")
        (dest / "parsed.json").write_text(json.dumps(parsed, indent=1) + "\n")
        receipt["raw_gene_calls"] = {
            g: {
                "source_diplotypes": [d.get("label") for d in (v.get("sourceDiplotypes") or [])],
                "recommendation_diplotypes": [d.get("label") for d in (v.get("recommendationDiplotypes") or [])],
                "phenotypes": [p for d in (v.get("recommendationDiplotypes") or []) for p in (d.get("phenotypes") or [])],
                "call_source": v.get("callSource"),
            }
            for g, v in (raw.get("genes") or {}).items()
            if g in {"CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "NUDT15", "DPYD", "CYP2D6"}
        }
        receipt["parsed_gene_calls"] = {
            g: {k: v.get(k) for k in ("diplotype", "phenotype", "call_status", "candidate_diplotypes") if k in v}
            for g, v in (parsed.get("genes") or {}).items()
        }
    (dest / "execution.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def summarise(body: dict) -> dict:
    rows = {}
    for a in body.get("analyses", []):
        prof = a.get("pharmacogenomic_profile", {})
        rec = a.get("clinical_recommendation", {})
        exp = a.get("llm_generated_explanation", {})
        rows[a["drug"]] = {
            "risk_label": a.get("risk_assessment", {}).get("risk_label"),
            "primary_gene": prof.get("primary_gene"),
            "diplotype": prof.get("diplotype"),
            "phenotype": prof.get("phenotype"),
            "action": rec.get("action"),
            "population": rec.get("population") or rec.get("applicable_population"),
            "cpic_recommendation": (rec.get("cpic_recommendation") or "")[:400],
            "unknown_reasons": [r.get("code") for r in (a.get("unknown_reasons") or [])] or a.get("unknown_reason"),
            "explanation_summary": (exp.get("summary") or "")[:400],
        }
    return rows


results = []
for f in table["fixtures"]:
    path = REPO / f["upload_copy"]
    data = path.read_bytes()
    assert sha(data) == f["source_sha256"], f["id"]
    record = {"id": f["id"], "label": f["label"], "input": f["upload_copy"], "input_sha256": sha(data),
              "drugs": f["drugs"], "expected": f["expected"]}
    cov_status, cov, cov_s, cov_raw = post("coverage", path, None)
    (OUT / f"{f['id']}.coverage.json").write_bytes(cov_raw)
    ana_status, ana, ana_s, ana_raw = post("analyze", path, f["drugs"])
    (OUT / f"{f['id']}.analyze.json").write_bytes(ana_raw)
    record["coverage"] = {"status": cov_status, "seconds": round(cov_s, 3), "sha256": sha(cov_raw),
                          "answerable_drugs": cov.get("answerable_drugs"),
                          "error_code": (cov.get("detail") or {}).get("error_code") if isinstance(cov.get("detail"), dict) else cov.get("error_code")}
    record["analyze"] = {"status": ana_status, "seconds": round(ana_s, 3), "sha256": sha(ana_raw),
                         "error": ana.get("detail") if ana_status != 200 else None,
                         "drugs": summarise(ana) if ana_status == 200 else None,
                         "warnings": (ana.get("quality_metrics") or {}).get("warnings") if ana_status == 200 else None,
                         "guideline_provenance": (ana.get("quality_metrics") or {}).get("guideline_provenance") if ana_status == 200 else None}
    if ana_status == 200:
        record["pharmcat_direct"] = direct_pharmcat(f["id"], path)
    results.append(record)
    print(f["id"], cov_status, ana_status, {d: v["risk_label"] for d, v in (record["analyze"]["drugs"] or {}).items()}, flush=True)

(OUT / "results.json").write_text(json.dumps({"label": label, "api": API, "fixtures": results}, indent=1) + "\n")
