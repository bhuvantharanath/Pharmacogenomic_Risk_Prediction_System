#!/usr/bin/env python3
"""
Part B regression harness — run once per item, compare with the baseline.

    python audit/phase9/partb/run_regression.py baseline
    python audit/phase9/partb/run_regression.py B1 [--compare-to baseline]

Three measurements, each written under audit/phase9/partb/<tag>/:

  cohort   The 400-sample 1000 Genomes cohort through the REAL pipeline
           (validate_vcf → coverage.assess → cpic_engine via build_response) for
           all six drugs: 2,400 results. PharmCAT is not re-run: each sample's
           cached PharmCAT 3.4.0 report.json is parsed, so the engine under test
           is ours, not PharmCAT's.
  testvcf  PharmCAT's 74 adversarial test VCFs (scripts/validate_testvcfs.py).
           Its tracked output report is copied and then restored, so a
           regression run never rewrites reports/testvcf_fidelity.json.
  s1-s6    The six demo scenarios against a fresh local uvicorn started from
           this working tree.

The comparison reports what the Part B report-back needs: S1–S6 matched
(labels), cohort confident→Unknown and Unknown→confident counts, and 74-VCF
mismatches.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PY = str(REPO / "backend" / ".venv" / "bin" / "python")
COHORT_VCF = REPO / "test-data/reference/cohort/cohort_n400.vcf"
COHORT_REPORTS = REPO / "test-data/reference/cohort/pharmcat_n400"
DRUGS = ["clopidogrel", "warfarin", "codeine", "simvastatin", "azathioprine", "fluorouracil"]
PORT = 8010

sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO / "audit/phase9/live"))


def cohort_labels(dest: Path) -> dict:
    os.environ.setdefault("EXPLANATION_MODE", "static")
    from app import coverage, main  # noqa: PLC0415
    from app.pharmcat_runner import parse_report  # noqa: PLC0415
    from app.vcf_validation import validate_vcf  # noqa: PLC0415

    meta, chrom, rows = [], None, []
    with COHORT_VCF.open() as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("##"):
                meta.append(line)
            elif line.startswith("#CHROM"):
                chrom = line.split("\t")
            elif line:
                rows.append(line.split("\t"))
    samples = chrom[9:]
    results: dict = {}
    for index, sample in enumerate(samples):
        column = 9 + index
        # INFO is blanked: ~1 KB per row would push each sample past the 5 MB
        # upload cap, and neither the coverage gate nor the cached PharmCAT
        # report reads it. Identical for every tag, so comparisons are fair.
        text = "\n".join(meta + ["\t".join(chrom[:9] + [sample])]
                         + ["\t".join(r[:7] + ["."] + [r[8], r[column]]) for r in rows]) + "\n"
        metadata = validate_vcf(text.encode(), filename=f"{sample}.vcf")
        cov = coverage.assess(metadata.text)
        report_path = COHORT_REPORTS / f"cohort_n400.{sample}.report.json"
        report = parse_report(json.loads(report_path.read_text()), sample_hint=sample)
        response = main.build_response(report, DRUGS, metadata, 0, cov=cov)
        results[sample] = {
            a.drug: {
                "label": a.risk_assessment.risk_label.value,
                "phenotype": a.pharmacogenomic_profile.phenotype.value,
                "gene": a.pharmacogenomic_profile.primary_gene,
            }
            for a in response.analyses
        }
    dest.write_text(json.dumps(results, indent=0, sort_keys=True))
    return results


def testvcfs(dest: Path) -> dict:
    tracked = REPO / "reports/testvcf_fidelity.json"
    saved = tracked.read_bytes()
    try:
        subprocess.run([PY, "scripts/validate_testvcfs.py"], cwd=REPO, check=True,
                       capture_output=True, text=True)
        shutil.copyfile(tracked, dest)
    finally:
        tracked.write_bytes(saved)
    data = json.loads(dest.read_text())
    return data


def s1_s6(dest_dir: Path) -> dict:
    env = dict(os.environ, EXPLANATION_MODE="static",
               CORS_ALLOWED_ORIGINS="http://localhost:8080", PHARMAGUARD_ENV="development")
    log = (dest_dir.parent / "server.log").open("w")
    server = subprocess.Popen(
        [str(REPO / "backend/.venv/bin/uvicorn"), "app.main:app", "--port", str(PORT)],
        cwd=REPO / "backend", env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2):
                    break
            except Exception:  # noqa: BLE001 — still starting
                time.sleep(0.5)
        else:
            raise SystemExit("local server did not start; see server.log")
        subprocess.run([PY, str(REPO / "audit/phase9/live/measure_warm.py"),
                        "--base", f"http://127.0.0.1:{PORT}", "--out", str(dest_dir),
                        "--phase", "scenarios", "--no-pace"],
                       check=True, capture_output=True, text=True)
    finally:
        server.terminate()
        server.wait(timeout=20)
        log.close()
    return json.loads((dest_dir / "summary.json").read_text())["scenarios"]


CONFIDENT = {"Ineffective", "Toxic", "Adjust Dosage", "No PGx-guided adjustment identified"}


def compare(tag: str, base: str) -> dict:
    a = json.loads((OUT / base / "cohort_labels.json").read_text())
    b = json.loads((OUT / tag / "cohort_labels.json").read_text())
    shifts = {"confident_to_unknown": [], "unknown_to_confident": [],
              "confident_to_other_confident": []}
    for sample in sorted(set(a) | set(b)):
        for drug in DRUGS:
            before = a.get(sample, {}).get(drug, {}).get("label")
            after = b.get(sample, {}).get(drug, {}).get("label")
            if before == after:
                continue
            row = f"{sample}:{drug}:{before}->{after}"
            if before in CONFIDENT and after == "Unknown":
                shifts["confident_to_unknown"].append(row)
            elif before == "Unknown" and after in CONFIDENT:
                shifts["unknown_to_confident"].append(row)
            else:
                shifts["confident_to_other_confident"].append(row)
    sa = json.loads((OUT / base / "s1-s6" / "summary.json").read_text())["scenarios"]
    sb = json.loads((OUT / tag / "s1-s6" / "summary.json").read_text())["scenarios"]
    s_match = sum(1 for k in sa if sb.get(k, {}).get("labels") == sa[k]["labels"])
    ta = json.loads((OUT / tag / "testvcf_fidelity.json").read_text())
    summary = {
        "tag": tag, "compared_to": base,
        "s1_s6_labels_matched": f"{s_match}/{len(sa)}",
        "cohort_results": sum(len(v) for v in b.values()),
        "cohort_confident_to_unknown": len(shifts["confident_to_unknown"]),
        "cohort_unknown_to_confident": len(shifts["unknown_to_confident"]),
        "cohort_confident_to_other_confident": len(shifts["confident_to_other_confident"]),
        "testvcf_files_compared": ta.get("files_compared"),
        "testvcf_mismatches": (ta.get("integration_fidelity") or {}).get("mismatches"),
        "testvcf_field_comparisons": (ta.get("integration_fidelity") or {}).get("field_comparisons"),
        "shift_examples": {k: v[:10] for k, v in shifts.items()},
    }
    (OUT / tag / "comparison.json").write_text(json.dumps(summary, indent=1))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--compare-to", default="baseline")
    ap.add_argument("--skip", default="", help="comma list of cohort,testvcf,s1s6")
    args = ap.parse_args()
    dest = OUT / args.tag
    dest.mkdir(parents=True, exist_ok=True)
    skip = set(filter(None, args.skip.split(",")))
    started = time.monotonic()
    if "cohort" not in skip:
        labels = cohort_labels(dest / "cohort_labels.json")
        counts: dict = {}
        for per_drug in labels.values():
            for drug, row in per_drug.items():
                counts.setdefault(drug, {}).setdefault(row["label"], 0)
                counts[drug][row["label"]] += 1
        (dest / "cohort_label_counts.json").write_text(json.dumps(counts, indent=1, sort_keys=True))
        print("cohort label counts:", json.dumps(counts, sort_keys=True))
    if "testvcf" not in skip:
        data = testvcfs(dest / "testvcf_fidelity.json")
        print("74 test VCFs:", data.get("files_compared"), data.get("integration_fidelity"))
    if "s1s6" not in skip:
        scen = s1_s6(dest / "s1-s6")
        print("S1-S6:", json.dumps({k: v["labels"] for k, v in scen.items()}))
    if args.tag != args.compare_to:
        print(json.dumps(compare(args.tag, args.compare_to), indent=1))
    print(f"done in {time.monotonic() - started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
