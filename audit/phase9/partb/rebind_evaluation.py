#!/usr/bin/env python3
"""
Controlled re-binding of the external evaluation after a scientific-core change.

    python audit/phase9/partb/rebind_evaluation.py --tag 2026-11-04-b1 --why "<one sentence>"

The application core (scripts/scientific_hash_policy.json) is hash-bound to a
versioned external evaluation. Any change inside it — B1 touched
backend/app/cpic_engine.py — means the current evaluation no longer binds the
candidate, so the release gate fails closed until the application is re-run over
the frozen 208-person cohort and the result is shown to be unchanged.

This mirrors the 2026-10-14 procedure step for step
(audit-output/2026-10-14-prompt8-4da1199df2/refresh/: prepare_evaluation_copy.py,
compare_evaluation.py, replay_f4.py):

  1. Isolated copy outside the repository: every git-tracked file as it stands in
     the working tree, plus the benchmark cache, each cache file verified against
     the frozen manifests. The copy's application core hash must equal the repo's.
  2. scripts/benchmark_external.py prepare / fetch --resume / evaluate --resume in
     the copy. The 208 cached PharmCAT reports are reused; no new caller run.
  3. Comparison with the historical benchmark AND the current package: scored
     results equal except generated_at; eligibility rows differ only in vcf_sha256
     (the path-bearing bcftools header), shown on a representative projection;
     exclusions, discrepancies, truth, lock and report manifest byte-identical.
  4. F4 replay: the two frozen read-backed VCFs through a local API started from
     this working tree, with the nine checks used since Prompt 5.
  5. Publish test-data/benchmark/current-candidate-<tag>/, point
     scripts/compatible_bundle.py at it and rebuild the bundle manifest through
     scripts/build_compatible_bundle.py.

The first failed comparison stops the run with a non-zero exit and nothing is
published. The previous package and the historical benchmark are never written.
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

R = Path(__file__).resolve().parents[3]
WORK_BASE = Path(__file__).resolve().parent / "rebind"
WORK = WORK_BASE  # set per tag in main()
PY = str(R / "backend/.venv/bin/python")
B = "test-data/benchmark/external/"
F4 = R / "audit-output/2026-09-30-f4"
PORT = 8020

sys.path.insert(0, str(R / "scripts"))
import compatible_bundle as bundle  # noqa: E402


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ref(path: Path) -> dict:
    return {"path": str(path.relative_to(R)), "bytes": path.stat().st_size, "sha256": sha(path)}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def prepare_copy(copy: Path) -> dict:
    assert R not in copy.parents, "the evaluation copy must live outside the repository"
    assert not copy.exists(), "evaluation copy already exists; preserve the first run"
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=R, check=True,
                             capture_output=True).stdout.decode().split("\0")
    copied = 0
    for rel in filter(None, tracked):
        src, dst = R / rel, copy / rel
        if not src.exists() and not src.is_symlink():
            continue  # deleted in the working tree: not part of the candidate
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_symlink():
            dst.symlink_to(os.readlink(src))
        else:
            shutil.copy2(src, dst)
        copied += 1
    bench = R / B
    manifest = json.loads((bench / "benchmark_manifest.json").read_text())
    reports = json.loads((bench / "pharmcat_report_manifest.json").read_text())
    assert reports["report_count"] == len(reports["reports"]) == 208
    assert sha(R / manifest["genomic"]["combined_path"]) == manifest["genomic"]["combined_sha256"] \
        == reports["source_vcf_sha256"]
    assert sha(R / manifest["truth"]["local_path"]) == manifest["truth"]["sha256"]
    assert sha(bench / "sample_gene_truth.tsv") == manifest["sample_gene_truth_sha256"]
    assert sha(bench / "cohort_lock.json") == manifest["cohort_lock_sha256"]
    assert sha(bench / "protocol.json") == manifest["protocol_sha256"]
    for subdir in ("genomic", "pharmcat_reports"):
        shutil.copytree(bench / subdir, copy / B / subdir, dirs_exist_ok=True)
    for record in reports["reports"]:
        path = copy / record["local_cache_path"]
        assert path.stat().st_size == record["bytes"] and sha(path) == record["sha256"], record["sample_id"]
    tools = R / "test-data/reference/tools"
    shutil.copytree(tools, copy / "test-data/reference/tools", dirs_exist_ok=True)
    core_repo, core_copy = bundle.application_core_hash(R), bundle.application_core_hash(copy)
    assert core_repo == core_copy, (core_repo, core_copy)
    return {"copy_root": str(copy), "tracked_files_copied": copied,
            "verified_cached_reports": len(reports["reports"]),
            "application_core_sha256_repo_and_copy": core_repo}


def run_stage(name: str, argv: list[str], cwd: Path, receipts: list) -> None:
    started = now()
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
    (WORK / f"{name}.stdout").write_text(proc.stdout)
    (WORK / f"{name}.stderr").write_text(proc.stderr)
    receipts.append({"name": name, "argv": argv, "cwd": str(cwd), "started_at": started,
                     "ended_at": now(), "exit_code": proc.returncode,
                     "stdout": f"{name}.stdout", "stderr": f"{name}.stderr"})
    if proc.returncode != 0:
        raise SystemExit(f"stage {name} failed with exit {proc.returncode}; see {WORK / (name + '.stderr')}")


def tsv(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def differing(before: list[dict], after: list[dict]) -> tuple[dict, set]:
    assert len(before) == len(after) == 1456
    counter, samples = collections.Counter(), set()
    for a, b in zip(before, after):
        assert (a["sample_id"], a["gene"]) == (b["sample_id"], b["gene"])
        for key in a:
            if a[key] != b[key]:
                counter[key] += 1
                samples.add(a["sample_id"])
    return dict(counter), samples


def compare(copy: Path, previous: Path, why: str) -> dict:
    strip = lambda d: {k: v for k, v in d.items() if k != "generated_at"}  # noqa: E731
    old = json.loads((R / B / "external_benchmark_results.json").read_text())
    new = json.loads((copy / B / "external_benchmark_results.json").read_text())
    prev = json.loads((previous / "external_benchmark_results.json").read_text())
    assert strip(old) == strip(new) == strip(prev), "scored results changed"
    assert new["cohort_samples"] == 208 and new["sample_gene_truth_rows"] == 1456
    assert new["truth_status_counts"]["evaluable"] == 596 and new["pharmcat_reports"] == 208
    vs_hist, hist_samples = differing(tsv(R / B / "input_eligibility.tsv"), tsv(copy / B / "input_eligibility.tsv"))
    vs_prev, _ = differing(tsv(previous / "input_eligibility.tsv"), tsv(copy / B / "input_eligibility.tsv"))
    assert vs_hist == {"vcf_sha256": 1456}, vs_hist
    assert vs_prev == {"vcf_sha256": 1456}, vs_prev
    assert len(hist_samples) == 208
    for name in ("exclusions.tsv", "discrepancies.tsv", "sample_gene_truth.tsv", "cohort_lock.json",
                 "pharmcat_report_manifest.json"):
        assert sha(R / B / name) == sha(copy / B / name), name
    for name in ("exclusions.tsv", "discrepancies.tsv"):
        assert sha(previous / name) == sha(copy / B / name), name
    assert sha(R / "reports/external_analytical_benchmark.md") == sha(copy / "reports/external_analytical_benchmark.md")
    source_manifest = json.loads((R / B / "benchmark_manifest.json").read_text())
    sample = "HG00111"
    positions = R / "test-data/reference/tools/pharmcat_positions_3.4.0.vcf.bgz"
    projections = []
    for label, root in (("historical-path", R), ("isolated-path", copy)):
        source = root / source_manifest["genomic"]["combined_path"]
        target = WORK / f"{label}.{sample}.vcf"
        subprocess.run(["bcftools", "view", "-R", str(positions), "-s", sample, "-Ov", "-o",
                        str(target), str(source)], check=True, capture_output=True)
        lines = target.read_text().splitlines()
        projections.append({"label": label, "path": target.name, "sha256": sha(target),
                            "command_lines": [x for x in lines if x.startswith("##bcftools_viewCommand=")],
                            "records": [x for x in lines if not x.startswith("#")],
                            "rest": [x for x in lines if not x.startswith("##bcftools_viewCommand=")]})
    assert projections[0]["sha256"] != projections[1]["sha256"]
    assert projections[0]["rest"] == projections[1]["rest"]
    assert projections[0]["records"] == projections[1]["records"]
    prev_manifest = json.loads((previous / "evaluation_manifest.json").read_text())
    return {
        "historical_benchmark_id": old["benchmark_id"],
        "historical_generated_at": old["generated_at"],
        "previous_evaluation": prev_manifest["evaluation_id"],
        "previous_generated_at": prev["generated_at"],
        "new_generated_at": new["generated_at"],
        "individuals": 208, "sample_gene_rows": 1456, "evaluable_truth_rows": 596,
        "all_metric_fields_equal_except_generation_time": True,
        "equal_to_previous_evaluation_except_generation_time": True,
        "eligibility_rows": 1456, "differing_eligibility_fields": vs_hist,
        "differing_eligibility_fields_vs_previous_evaluation": vs_prev,
        "individuals_with_vcf_sha_difference": len(hist_samples),
        "exclusions_sha256": sha(copy / B / "exclusions.tsv"),
        "discrepancies_sha256": sha(copy / B / "discrepancies.tsv"),
        "report_manifest_sha256": sha(copy / B / "pharmcat_report_manifest.json"),
        "representative_projection": [{k: v for k, v in p.items() if k not in ("records", "rest")}
                                      for p in projections],
        "representative_projection_record_count": len(projections[0]["records"]),
        "representative_biological_records_equal": True,
        "interpretation": why + (" Its application rerun over the same 208 individuals reproduces "
                                 "every scored metric, exclusion and discrepancy of both the historical "
                                 "benchmark and the previous evaluation. The only differing eligibility "
                                 "field is the hash of each regenerated single-sample VCF, explained by "
                                 "the path-bearing bcftools header shown in the representative projection. "
                                 "No new genotype concordance or clinical claim follows."),
    }


def replay_f4() -> list[dict]:
    sys.path.insert(0, str(R / "scripts"))
    from run_demo import post_analyze  # noqa: PLC0415
    artifacts = {row["path"]: row for row in json.loads((F4 / "artifact-checksums.json").read_text())["files"]}
    protocol = json.loads((F4 / "frozen-protocol.json").read_text())
    truth = {row["sample_id"]: row for row in protocol["truth"]}
    assert protocol["before_genotype_calling"] and protocol["before_application_scoring"]
    env = dict(os.environ, EXPLANATION_MODE="static", CORS_ALLOWED_ORIGINS="http://localhost:8080",
               PHARMAGUARD_ENV="development")
    log = (WORK / "f4-server.log").open("w")
    server = subprocess.Popen([str(R / "backend/.venv/bin/uvicorn"), "app.main:app", "--port", str(PORT)],
                              cwd=R / "backend", env=env, stdout=log, stderr=subprocess.STDOUT)
    receipts = []
    try:
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2):
                    break
            except Exception:  # noqa: BLE001 — still starting
                time.sleep(0.5)
        else:
            raise SystemExit("F4 server did not start")
        for sample, diplotype, phenotype, label in (("NA18526", "*1/*1", "NM", "No PGx-guided adjustment identified"),
                                                    ("NA12878", "*1/*2", "IM", "Ineffective")):
            vcf = F4 / f"{sample}.observed.vcf"
            data = vcf.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            frozen = artifacts[vcf.name]
            assert frozen["bytes"] == len(data) and frozen["sha256"] == digest
            assert truth[sample]["truth_normalized"] == diplotype
            response = post_analyze(f"http://127.0.0.1:{PORT}", vcf, "clopidogrel")
            body_path = WORK / f"{sample}.fresh-api.json"
            body_path.write_text(json.dumps(response.body, indent=2) + "\n")
            assert response.status == 200, (sample, response.status, response.error)
            analysis = response.body["analyses"][0]
            profile = analysis["pharmacogenomic_profile"]
            warnings = response.body["quality_metrics"]["warnings"]
            disclaimer = analysis["llm_generated_explanation"]["disclaimer"]
            checks = {
                "independent_truth": truth[sample]["truth_normalized"] == diplotype,
                "profile_diplotype": profile["diplotype"] == diplotype,
                "phenotype": profile["phenotype"] == phenotype,
                "label": analysis["risk_assessment"]["risk_label"] == label,
                "acs_pci_qualifier_retained": "CVI ACS PCI" in analysis["clinical_recommendation"]["cpic_recommendation"],
                "deterministic_fallback": any("source=template" in w for w in warnings),
                "no_static_prose": not any("source=static" in w for w in warnings),
                "no_clinical_review_claim": "No qualified clinical expert" in disclaimer,
                "no_invention_guarantee": "nothing was invented" not in disclaimer,
            }
            receipts.append({"sample": sample, "source_accession": protocol["samples"][sample],
                             "observed_vcf_sha256": digest, "historical_frozen_artifact_sha256": frozen["sha256"],
                             "response_sha256": sha(body_path), "latency_ms": response.latency_ms,
                             "checks": checks, "passed": all(checks.values()),
                             "scope": ("fresh current API/PharmCAT replay of a previously frozen read-backed "
                                       "VCF; not a new raw-read extraction or independent genotype call")})
    finally:
        server.terminate()
        server.wait(timeout=20)
        log.close()
    assert all(r["passed"] for r in receipts), receipts
    return receipts


def report_text(evaluation_id: str, core: str, protocol_sha: str, previous_id: str, why: str,
                results: dict) -> str:
    rows = []
    for gene, data in results["genes"].items():
        eligible = data["layer_B_application"]["input_eligible"]
        rows.append(f"| {gene} | {data['truth_evaluable']} | {eligible['numerator']}/{eligible['denominator']} |")
    return "\n".join([
        f"# Current candidate evaluation", "",
        f"Evaluation ID: `{evaluation_id}`.",
        f"Current portable scientific core: `{core}`.",
        f"Historic frozen protocol: `{protocol_sha}`. Truth and cohort locks are unchanged.", "",
        f"Why a new version: {why} The changed file is inside the scientific-core allowlist, so the "
        f"previous evaluation (`{previous_id}`) no longer bound the candidate. It is preserved unchanged.", "",
        "The 208 public-cohort PharmCAT reports were reused only after all 208 report hashes, the exact "
        "combined VCF, pinned JAR, truth table, workbook and cohort lock were checked. No new 208-person "
        "PharmCAT caller run is claimed. The application reprojected each of the 208 people and rescored all "
        "1,456 sample-gene rows in an isolated copy. The two frozen F4 read-backed VCF controls were "
        "replayed through a local API started from the candidate; they are bounded positives, not a "
        "replacement for the cohort.", "",
        "Compared with the historical run and the previous evaluation, per-gene metrics, exclusions and "
        "discrepancies are equal. The only changed field in all 1,456 eligibility rows is the temporary "
        "single-sample VCF SHA-256, explained by the path-bearing bcftools header.", "",
        "| Gene | Evaluable truth rows | Application input eligible (individuals) |",
        "|---|---:|---:|", *rows, "",
        "The source VCF is polymorphic-filtered; missing required coordinates remain unknown. No pooled "
        "accuracy or clinical utility claim follows. Generated explanations remain unapproved and use the "
        "deterministic runtime fallback; human adjudication is outstanding.", ""])


def publish(tag: str, copy: Path, summary: dict, f4: list, receipts: list, why: str, prep: dict) -> Path:
    previous_rel = bundle.CURRENT_EVALUATION_RELATIVE
    previous = R / previous_rel
    package = R / f"test-data/benchmark/current-candidate-{tag}"
    assert not package.exists(), f"{package} exists; tags are never reused"
    package.mkdir(parents=True)
    for src, name in ((copy / B / "external_benchmark_results.json", "external_benchmark_results.json"),
                      (copy / B / "input_eligibility.tsv", "input_eligibility.tsv"),
                      (copy / B / "exclusions.tsv", "exclusions.tsv"),
                      (copy / B / "discrepancies.tsv", "discrepancies.tsv"),
                      (copy / B / "benchmark_manifest.json", "raw_benchmark_manifest.json"),
                      (copy / "reports/external_analytical_benchmark.md", "raw_scoring_report.md")):
        shutil.copyfile(src, package / name)
    (package / "evaluation-comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
    (package / "f4-fresh-replay.json").write_text(json.dumps(f4, indent=2) + "\n")
    (package / "stage-command-receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
    core = bundle.application_core_hash(R)
    raw = json.loads((package / "raw_benchmark_manifest.json").read_text())
    assert raw["local_production_artifact_sha256"] == core
    old = json.loads(previous.read_text())
    evaluation_id = f"pharmaguard-external-current-candidate-{tag}"
    results = json.loads((package / "external_benchmark_results.json").read_text())
    (package / "EVALUATION-REPORT.md").write_text(
        report_text(evaluation_id, core, old["frozen_protocol"]["sha256"], old["evaluation_id"], why, results))
    manifest = dict(old)
    manifest.update({
        "evaluation_id": evaluation_id,
        "created_at": now(),
        "candidate_application_core_sha256": core,
        "base_head_metadata_only": subprocess.run(["git", "rev-parse", "HEAD"], cwd=R, check=True,
                                                  capture_output=True, text=True).stdout.strip(),
        "previous_evaluation": ref(previous),
        "fresh_stages": {"application_individuals": 208, "scored_sample_gene_rows": 1456,
                         "f4_local_api_cases": len(f4)},
        "comparison": {
            "all_metrics_equal_except_generation_time": summary["all_metric_fields_equal_except_generation_time"],
            "equal_to_previous_evaluation_except_generation_time":
                summary["equal_to_previous_evaluation_except_generation_time"],
            "differing_eligibility_field": "vcf_sha256",
            "differing_eligibility_rows": summary["differing_eligibility_fields"]["vcf_sha256"],
            "representative_biological_records_equal": summary["representative_biological_records_equal"],
        },
        "outputs": [ref(path) for path in sorted(package.iterdir()) if path.name != "evaluation_manifest.json"],
    })
    for name in ("frozen_protocol", "frozen_cohort_lock", "independent_truth_workbook", "independent_truth_table",
                 "frozen_combined_vcf", "pinned_jar", "upstream_report_manifest", "historical_benchmark_manifest"):
        assert ref(R / old[name]["path"]) == old[name], f"frozen source changed: {name}"
    (package / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    # Point the bundle at the new package; the bundle id names the version.
    source = (R / "scripts/compatible_bundle.py").read_text()
    new_rel = str((package / "evaluation_manifest.json").relative_to(R))
    assert source.count(f'"{previous_rel}"') == 1
    source = source.replace(f'"{previous_rel}"', f'"{new_rel}"')
    import re  # noqa: PLC0415
    ids = re.findall(r'"bundle_id": "([^"]+)"', source)
    assert len(ids) == 1
    source = source.replace(ids[0], f"pharmaguard-scientific-current-candidate-{tag}")
    (R / "scripts/compatible_bundle.py").write_text(source)
    return package


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, help="e.g. 2026-11-04-b1; names the new package")
    ap.add_argument("--why", required=True, help="one sentence: what changed in the core")
    ap.add_argument("--copy-root", required=True, help="scratch directory outside the repository")
    args = ap.parse_args()
    global WORK
    WORK = WORK_BASE / args.tag
    WORK.mkdir(parents=True, exist_ok=True)
    copy = Path(args.copy_root).resolve() / f"evaluation-copy-{args.tag}"
    receipts: list = []
    started = now()
    prep = prepare_copy(copy)
    receipts.append({"name": "prepare-evaluation-copy", "started_at": started, "ended_at": now(),
                     "exit_code": 0, "detail": prep})
    script = str(copy / "scripts/benchmark_external.py")
    run_stage("cohort-prepare", [PY, script, "prepare"], copy, receipts)
    run_stage("cohort-fetch-resume", [PY, script, "fetch", "--resume"], copy, receipts)
    run_stage("cohort-evaluate-resume", [PY, script, "evaluate", "--resume"], copy, receipts)
    previous = (R / bundle.CURRENT_EVALUATION_RELATIVE).parent
    summary = compare(copy, previous, args.why)
    receipts.append({"name": "compare-evaluation", "ended_at": now(), "exit_code": 0})
    f4 = replay_f4()
    receipts.append({"name": "f4-fresh-replay", "ended_at": now(), "exit_code": 0,
                     "cases": len(f4), "passed": sum(r["passed"] for r in f4)})
    package = publish(args.tag, copy, summary, f4, receipts, args.why, prep)
    run = subprocess.run([PY, "scripts/build_compatible_bundle.py"], cwd=R, capture_output=True, text=True)
    (WORK / "build-compatible-manifest.stdout").write_text(run.stdout + run.stderr)
    if run.returncode != 0:
        raise SystemExit("build_compatible_bundle.py failed")
    verify = subprocess.run([PY, "scripts/verify_compatible_bundle.py"], cwd=R, capture_output=True, text=True)
    (WORK / "verify-compatible-bundle.stdout").write_text(verify.stdout + verify.stderr)
    shutil.rmtree(copy)
    (WORK / f"evaluation-copy-{args.tag}-deleted.json").write_text(json.dumps(
        {"copy_root": str(copy), "deleted_at": now(), **prep}, indent=1))
    print(json.dumps({"package": str(package.relative_to(R)), "core": bundle.application_core_hash(R),
                      "f4": [r["passed"] for r in f4], "verify_rc": verify.returncode,
                      "verify": verify.stdout.strip()[-200:]}, indent=1))
    return 0 if verify.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
