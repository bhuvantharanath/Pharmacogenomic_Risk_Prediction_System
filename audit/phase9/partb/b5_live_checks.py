#!/usr/bin/env python3
"""
B5 after deploy: criteria L3-L5 of audit/phase9/B5.log ("Push and live check").

    b5_live_checks.py s1s6 LIVE_DIR LOCAL_DIR     # L3
    b5_live_checks.py warfarin OUT_DIR            # L4 (2 live uploads)
    b5_live_checks.py sample OUT_DIR              # local warfarin run of the bundled sample (L5's reference)
    b5_live_checks.py bundle SHA                  # L5, the deployed web bundle

Each prints a JSON verdict and exits 0 only when every check passes.
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BASE = "https://pharmaguard-api-baml.onrender.com"
WEB = "https://pharmaguard-web.pages.dev"
JAR = REPO / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
SAMPLE = REPO / "app/assets/samples/pharmaguard_sample_reduced_function.vcf"
CPIC_TEXT = (
    "CPIC Guideline for Pharmacogenetics-Guided Warfarin Dosing: 2017 Update [Article: 28198005 ] "
    "recommends that pharmacogenetic warfarin dosing be accomplished through the use of one of the "
    "pharmacogenetic dosing algorithms, as summarized in Figure 2. See CPIC guideline annotation for details."
)
DOSE = re.compile(r"\d+(?:\.\d+)?\s*(?:mg|%)", re.IGNORECASE)
VKORC1_TT = "rs9923231 variant (T)/rs9923231 variant (T)"
PANEL_TEXT = ("Genes in this result", "shown for reference only; it does not change this result")


def _verdict(checks: dict, extra: dict | None = None) -> int:
    ok = all(checks.values())
    print(json.dumps({"checks": checks, "all_pass": ok, **(extra or {})}, indent=1))
    return 0 if ok else 1


def _local_client():
    sys.path.insert(0, str(REPO / "backend"))
    os.chdir(REPO / "backend")
    from fastapi.testclient import TestClient

    from app import main

    return TestClient(main.app)


def _local_warfarin(client, vcf: Path) -> dict:
    response = client.post("/analyze", files={"file": (vcf.name, io.BytesIO(vcf.read_bytes()), "text/plain")},
                           data={"drugs": "warfarin"})
    if response.status_code != 200:
        raise SystemExit(f"local /analyze returned {response.status_code}: {response.text[:300]}")
    return response.json()


def _core(body: dict) -> dict:
    [result] = body["analyses"]
    return {"risk_label": result["risk_assessment"]["risk_label"],
            "action": result["clinical_recommendation"]["action"],
            "gene_findings": result["gene_findings"]}


def s1s6(live_dir: Path, local_dir: Path) -> int:
    checks, detail = {}, {}
    for local_path in sorted(local_dir.glob("S*.json")):
        live = json.loads((live_dir / local_path.name).read_text())
        local = json.loads(local_path.read_text())
        findings = lambda b: {a["drug"]: a.get("gene_findings", []) for a in b["analyses"]}  # noqa: E731
        checks[f"{local_path.stem} gene_findings equal"] = findings(live) == findings(local)
        checks[f"{local_path.stem} warnings equal"] = (
            live["quality_metrics"]["warnings"] == local["quality_metrics"]["warnings"])
        detail[local_path.stem] = {"warnings": len(local["quality_metrics"]["warnings"]),
                                   "drugs_with_findings": sorted(d for d, f in findings(local).items() if f)}
    checks["six scenarios compared"] = len(detail) == 6
    return _verdict(checks, {"scenarios": detail})


def _synthetic(out: Path, name: str, *diplotypes: str, drop: str | None = None) -> Path:
    path = out / f"{name}.vcf"
    args = [sys.executable, str(REPO / "test-data/generate_synthetic_vcf.py"),
            "--from-jar", str(JAR), "--sample", name.upper(), "-o", str(path)]
    for diplotype in diplotypes:
        args += ["--diplotype", diplotype]
    proc = subprocess.run(args, cwd=out, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"generate_synthetic_vcf.py exited {proc.returncode}: {proc.stderr[-500:]}")
    if drop:
        lines = path.read_text().splitlines()
        kept = [line for line in lines if line.startswith("#") or not line.startswith(drop)]
        if len(kept) == len(lines):
            raise SystemExit(f"{name}: no {drop} rows to drop")
        path.write_text("\n".join(kept) + "\n")
    return path


def warfarin(out: Path) -> int:
    sys.path.insert(0, str(REPO / "audit/phase9/live"))
    import measure_warm

    out.mkdir(parents=True, exist_ok=True)
    full = _synthetic(out, "b5_live_pm_tt_cyp4f2", "CYP2C9=*3/*3", f"VKORC1={VKORC1_TT}", "CYP4F2=*1/*3")
    no_vkorc1 = _synthetic(out, "b5_live_no_vkorc1", "CYP2C9=*3/*3", f"VKORC1={VKORC1_TT}", "CYP4F2=*1/*3",
                           drop="chr16")
    client = _local_client()
    log = out / "requests.jsonl"
    checks, cores = {}, {}
    for vcf in (full, no_vkorc1):
        local = _local_warfarin(client, vcf)
        live = measure_warm.post(BASE, "/analyze", vcf, "warfarin", log, vcf.stem)
        (out / f"{vcf.stem}.local.json").write_text(json.dumps(local, indent=2, sort_keys=True))
        (out / f"{vcf.stem}.live.json").write_text(json.dumps(live["body"], indent=2, sort_keys=True))
        checks[f"{vcf.stem} live status 200"] = live["record"]["status"] == 200
        if live["record"]["status"] != 200:
            continue
        cores[vcf.stem] = core = _core(live["body"])
        checks[f"{vcf.stem} live equals local (label, action, gene_findings)"] = core == _core(local)
        checks[f"{vcf.stem} label Unknown"] = core["risk_label"] == "Unknown"
        checks[f"{vcf.stem} no dose in result"] = not DOSE.search(json.dumps(live["body"]["analyses"]))
    if full.stem in cores:
        f = {g["gene"]: g for g in cores[full.stem]["gene_findings"]}
        checks["full: CPIC text in action"] = CPIC_TEXT in cores[full.stem]["action"]
        checks["full: CYP2C9 *3/*3 assessed"] = f["CYP2C9"]["assessed"] and f["CYP2C9"]["call"] == "*3/*3"
        checks["full: VKORC1 T/T assessed"] = f["VKORC1"]["assessed"] and f["VKORC1"]["call"] == VKORC1_TT
        checks["full: CYP4F2 *1/*3 reference"] = (f["CYP4F2"]["role"] == "reference"
                                                  and f["CYP4F2"]["call"] == "*1/*3")
    if no_vkorc1.stem in cores:
        f = {g["gene"]: g for g in cores[no_vkorc1.stem]["gene_findings"]}
        checks["no chr16: action names VKORC1"] = cores[no_vkorc1.stem]["action"].startswith(
            "Required genomic evidence is incomplete for VKORC1.")
        checks["no chr16: VKORC1 not assessed, no call"] = (f["VKORC1"]["assessed"] is False
                                                           and f["VKORC1"]["call"] == "")
    return _verdict(checks, {"live": cores})


def sample(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    body = _local_warfarin(_local_client(), SAMPLE)
    (out / "sample_reduced_function.warfarin.local.json").write_text(json.dumps(body, indent=2, sort_keys=True))
    core = _core(body)
    print(json.dumps(core, indent=1))
    return 0


def bundle(sha: str) -> int:
    # Cloudflare answers Python-urllib's default User-Agent with 403 (first run,
    # B5.live-after.stdout); curl's is served, so name the client plainly.
    req = urllib.request.Request(f"{WEB}/main.dart.js?b5={sha[:7]}",
                                 headers={"Cache-Control": "no-cache", "User-Agent": "curl/8.7.1 (phase9-audit)"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        js = resp.read().decode("utf-8", "replace")
    checks = {"bundle contains EXPECTED_BACKEND_SHA": sha in js}
    for text in PANEL_TEXT:
        checks[f"bundle contains {text!r}"] = text in js
    return _verdict(checks, {"bundle_bytes": len(js)})


def main() -> int:
    command, *rest = sys.argv[1:]
    if command == "s1s6":
        return s1s6(Path(rest[0]), Path(rest[1]))
    if command == "warfarin":
        return warfarin(Path(rest[0]).resolve())
    if command == "sample":
        return sample(Path(rest[0]).resolve())
    if command == "bundle":
        return bundle(rest[0])
    raise SystemExit(f"unknown command {command}")


if __name__ == "__main__":
    sys.exit(main())
