#!/usr/bin/env python3
"""Build and verify the frozen scientific-component bundle."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from _common import REPO_ROOT


MANIFEST_PATH = REPO_ROOT / "backend/app/data/compatible_bundle.json"
JAR_PATH = REPO_ROOT / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
HASH_POLICY_RELATIVE = "scripts/scientific_hash_policy.json"
MIGRATION_RELATIVE = "scripts/application_hash_migration.json"
CURRENT_EVALUATION_RELATIVE = (
    "test-data/benchmark/current-candidate-2026-10-14/evaluation_manifest.json"
)
HASH_POLICY_VERSION = 2
SCOPED_GENES = (
    "CYP2C19",
    "CYP2C9",
    "CYP2D6",
    "CYP4F2",
    "DPYD",
    "NUDT15",
    "SLCO1B1",
    "TPMT",
    "VKORC1",
)
def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_hash_policy(root: Path | None = None) -> dict[str, Any]:
    """Load the exact versioned input list from the candidate being checked."""
    base = root or REPO_ROOT
    policy = json.loads((base / HASH_POLICY_RELATIVE).read_text())
    if policy.get("version") != HASH_POLICY_VERSION:
        raise ValueError("unsupported scientific hash-policy version")
    paths = policy.get("core_paths")
    if not isinstance(paths, list) or not paths or paths != sorted(set(paths)):
        raise ValueError("scientific hash-policy paths must be sorted and unique")
    for relative in paths:
        if (
            not isinstance(relative, str)
            or not relative
            or PurePosixPath(relative).is_absolute()
            or "\\" in relative
            or any(part in {".", "..", ""} for part in relative.split("/"))
            or PurePosixPath(relative).as_posix() != relative
        ):
            raise ValueError(f"invalid scientific hash-policy path: {relative!r}")
    if policy.get("self_referential_manifest") in paths:
        raise ValueError("the self-referential manifest cannot hash itself")
    return policy


def hash_selected_files(root: Path, paths: list[str], domain: str) -> str:
    """Hash normalized relative paths and raw bytes, independent of parent path."""
    digest = hashlib.sha256()
    digest.update(domain.encode("utf-8"))
    digest.update(b"\0")
    for relative in sorted(paths):
        candidate = root / relative
        parts = PurePosixPath(relative).parts
        has_symlink = any(
            root.joinpath(*parts[:depth]).is_symlink()
            for depth in range(1, len(parts) + 1)
        )
        if not candidate.is_file() or has_symlink:
            raise ValueError(f"missing or non-regular scientific input: {relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(candidate.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def tree_identity(path: Path) -> dict[str, Any]:
    root = REPO_ROOT
    directory = path.relative_to(root).as_posix()
    policy = load_hash_policy(root)
    files = [
        relative for relative in policy["core_paths"]
        if relative.startswith(directory + "/")
    ]
    if not files:
        raise ValueError(f"no versioned files in scientific tree: {directory}")
    return {
        "path": directory,
        "sha256": hash_selected_files(root, files, "pharmaguard-scientific-tree-v2"),
        "files": len(files),
        "hash_policy_version": HASH_POLICY_VERSION,
    }


def application_core_hash(root: Path | None = None) -> str:
    """Hash only the exact, versioned application inputs in policy v2."""
    base = root or REPO_ROOT
    policy = load_hash_policy(base)
    return hash_selected_files(base, policy["core_paths"], policy["hash_domain"])


def file_identity(relative: str) -> dict[str, Any]:
    path = REPO_ROOT / relative
    return {"path": relative, "sha256": sha256(path), "bytes": path.stat().st_size}


def _jar_member(zf: zipfile.ZipFile, member: str) -> dict[str, Any]:
    raw = zf.read(member)
    payload = json.loads(raw)
    return {
        "member": member,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source": payload.get("source"),
        "version": payload.get("version"),
        "modification_date": payload.get("modificationDate"),
        "genome_build": payload.get("genomeBuild"),
    }


def _guidance_rows(raw: bytes) -> dict[str, Any]:
    payload = json.loads(raw)
    wanted = {
        "azathioprine": "PA166104933",
        "clopidogrel": "PA166104948",
        "codeine": "PA166104996",
        "fluorouracil": "PA166122686",
        "simvastatin": "PA166105005",
        "warfarin": "PA166104949",
    }
    by_id = {row["guideline"]["id"]: row for row in payload["guidelines"]}
    rows = {}
    for drug, identifier in wanted.items():
        row = by_id[identifier]
        guideline = row["guideline"]
        rows[drug] = {
            "id": identifier,
            "version": guideline["version"],
            "source": guideline["source"],
            "chemicals": [item["name"] for item in guideline["relatedChemicals"]],
            "genes": [item["symbol"] for item in guideline["relatedGenes"]],
            "citation_pmids": [item["pmid"] for item in row.get("citations", [])],
        }
    return rows


def _approval_counts() -> dict[str, Any]:
    payload = json.loads((REPO_ROOT / "backend/app/data/explanation_approvals.json").read_text())
    return {
        "counts": payload["counts"],
        "clinical_expert_review": payload["clinical_expert_review"],
        "policy": payload["policy"],
    }


def _benchmark_record() -> dict[str, Any]:
    base = REPO_ROOT / "test-data/benchmark/external"
    protocol = json.loads((base / "protocol.json").read_text())
    benchmark = json.loads((base / "benchmark_manifest.json").read_text())
    results = json.loads((base / "external_benchmark_results.json").read_text())
    reports = json.loads((base / "pharmcat_report_manifest.json").read_text())
    migration = json.loads((REPO_ROOT / MIGRATION_RELATIVE).read_text())
    core_hash = application_core_hash()
    legacy_hash = benchmark["local_production_artifact_sha256"]
    migration_matches = (
        migration.get("historical_hash_policy_version") == 1
        and migration.get("historical_application_sha256") == legacy_hash
        and migration.get("portable_hash_policy_version") == HASH_POLICY_VERSION
        and migration.get("portable_application_sha256") == core_hash
        and migration.get("versioned_input_count")
        == len(load_hash_policy()["core_paths"])
    )
    return {
        "benchmark_id": benchmark["benchmark_id"],
        "evidence_type": "independent CDC GeT-RM consensus truth plus 1000 Genomes genomic evidence",
        "sample_unit": "individual; gene-specific truth rows are repeated measures within individuals",
        "cohort_samples": results["cohort_samples"],
        "sample_gene_rows": results["sample_gene_truth_rows"],
        "truth_evaluable": results["truth_status_counts"]["evaluable"],
        "pharmcat_reports": reports["report_count"],
        "application_eligible_sample_gene_rows": sum(
            gene["layer_B_application"]["input_eligible"]["numerator"]
            for gene in results["genes"].values()
        ),
        "limitation": "Polymorphic-only 1000 Genomes slices did not satisfy the application evidence contract; Layer B therefore abstained.",
        "application_core_sha256": core_hash,
        "application_hash_policy_version": HASH_POLICY_VERSION,
        "benchmark_historical_application_sha256": legacy_hash,
        "benchmark_historical_hash_policy_version": 1,
        "identity_migration": file_identity(MIGRATION_RELATIVE),
        "migration_identity_matches": migration_matches,
        "benchmark_rerun_for_hash_migration": False,
        "protocol": file_identity("test-data/benchmark/external/protocol.json"),
        "manifest": file_identity("test-data/benchmark/external/benchmark_manifest.json"),
        "truth_table": file_identity("test-data/benchmark/external/sample_gene_truth.tsv"),
        "results": file_identity("test-data/benchmark/external/external_benchmark_results.json"),
        "report": file_identity("reports/external_analytical_benchmark.md"),
        "reproduction_record": file_identity("reports/scientific_record_reproduction.json"),
        "declared_truth_version": protocol["truth_source"]["version"],
    }


def current_evaluation_record(root: Path | None = None) -> dict[str, Any]:
    """Verify new candidate evidence; retain the old migration as historical fact.

    The versioned manifest hashes its outputs, but not itself. The compatible
    bundle separately hashes the manifest. Cached caller reports need not be
    shipped in a clean release copy: their 208 hashes were checked at run time,
    and the frozen report manifest and source VCF are bound here.
    """
    base = root or REPO_ROOT
    path = base / CURRENT_EVALUATION_RELATIVE
    evaluation = json.loads(path.read_text())
    problems: list[str] = []

    def checked(ref: dict[str, Any]) -> None:
        relative = ref.get("path", "")
        candidate = base / relative
        if not candidate.is_file() or candidate.is_symlink():
            problems.append(f"missing or non-regular evidence file: {relative}")
            return
        if candidate.stat().st_size != ref.get("bytes") or sha256(candidate) != ref.get("sha256"):
            problems.append(f"evidence hash or size mismatch: {relative}")

    source_names = (
        "frozen_protocol", "frozen_cohort_lock", "independent_truth_workbook",
        "independent_truth_table", "frozen_combined_vcf", "pinned_jar",
        "upstream_report_manifest", "historical_benchmark_manifest",
    )
    for name in source_names:
        checked(evaluation[name])
    for item in evaluation["outputs"]:
        checked(item)

    core_hash = application_core_hash(base)
    if evaluation.get("schema_version") != 2:
        problems.append("unsupported current evaluation schema")
    if evaluation.get("application_hash_policy_version") != HASH_POLICY_VERSION:
        problems.append("current evaluation hash-policy version differs")
    if evaluation.get("candidate_application_core_sha256") != core_hash:
        problems.append("current evaluation does not bind the candidate scientific core")

    historical = json.loads((base / "test-data/benchmark/external/benchmark_manifest.json").read_text())
    prior_results = json.loads((base / "test-data/benchmark/external/external_benchmark_results.json").read_text())
    outputs = {Path(item["path"]).name: item for item in evaluation["outputs"]}
    current_results = json.loads((base / outputs["external_benchmark_results.json"]["path"]).read_text())
    raw_run = json.loads((base / outputs["raw_benchmark_manifest.json"]["path"]).read_text())
    upstream = json.loads((base / evaluation["upstream_report_manifest"]["path"]).read_text())
    comparison = json.loads((base / outputs["evaluation-comparison.json"]["path"]).read_text())
    f4 = json.loads((base / outputs["f4-fresh-replay.json"]["path"]).read_text())
    expected_counts = {"unique_individuals": 208, "sample_gene_rows": 1456,
                       "truth_evaluable_rows": 596, "pharmcat_reports": 208}
    if evaluation.get("denominators") != expected_counts:
        problems.append("current evaluation denominators differ from the frozen cohort")
    if (current_results.get("cohort_samples") != 208
            or current_results.get("sample_gene_truth_rows") != 1456
            or current_results.get("truth_status_counts", {}).get("evaluable") != 596
            or current_results.get("pharmcat_reports") != 208):
        problems.append("current evaluation result denominators differ")
    if ({k: v for k, v in current_results.items() if k != "generated_at"}
            != {k: v for k, v in prior_results.items() if k != "generated_at"}):
        problems.append("current and historical scored results differ")
    if (raw_run.get("local_production_artifact_sha256") != core_hash
            or raw_run.get("protocol_sha256") != historical.get("protocol_sha256")):
        problems.append("raw application run does not bind candidate and protocol")
    if (upstream.get("report_count") != 208
            or len(upstream.get("reports", [])) != 208
            or upstream.get("source_vcf_sha256") != evaluation["frozen_combined_vcf"]["sha256"]
            or evaluation["upstream_reuse"].get("new_caller_executions_for_208_person_cohort") != 0):
        problems.append("upstream report reuse identity or count differs")
    if (evaluation["fresh_stages"].get("application_individuals") != 208
            or evaluation["fresh_stages"].get("scored_sample_gene_rows") != 1456
            or evaluation["fresh_stages"].get("f4_local_api_cases") != 2
            or len(f4) != 2 or not all(row.get("passed") for row in f4)):
        problems.append("fresh application or F4 stage receipt is incomplete")
    if (not comparison.get("all_metric_fields_equal_except_generation_time")
            or comparison.get("differing_eligibility_fields") != {"vcf_sha256": 1456}
            or not comparison.get("representative_biological_records_equal")):
        problems.append("candidate comparison does not support the declared result")
    return {
        "evaluation_id": evaluation["evaluation_id"],
        "application_core_sha256": core_hash,
        "manifest": {
            "path": CURRENT_EVALUATION_RELATIVE,
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        },
        "historical_benchmark_manifest": evaluation["historical_benchmark_manifest"],
        "fresh_application_individuals": evaluation["fresh_stages"]["application_individuals"],
        "reused_pharmcat_reports": evaluation["upstream_reuse"]["verified_report_count"],
        "new_cohort_caller_executions": evaluation["upstream_reuse"]["new_caller_executions_for_208_person_cohort"],
        "denominators": evaluation["denominators"],
        "outputs": evaluation["outputs"],
        "evidence_matches": not problems,
        "problems": problems,
    }


def _declared_runtime() -> dict[str, Any]:
    dockerfile = (REPO_ROOT / "infra/Dockerfile").read_text()
    base = re.search(r"^FROM\s+(\S+)", dockerfile, re.MULTILINE)
    workflow = (REPO_ROOT / ".github/workflows/test.yml").read_text()
    flutter = re.search(r'flutter-version:\s*"([^"]+)"', workflow)
    return {
        "production_image": base.group(1) if base else None,
        "ci_python": "3.12",
        "ci_flutter": flutter.group(1) if flutter else None,
        "requirements": file_identity("backend/requirements.txt"),
        "requirements_dev": file_identity("backend/requirements-dev.txt"),
        "flutter_lock": file_identity("app/pubspec.lock"),
        "manifest_verifier_python": ">=3.11 (CI and production baseline use 3.12)",
    }


def build_manifest() -> dict[str, Any]:
    with zipfile.ZipFile(JAR_PATH) as zf:
        definitions = {
            gene: _jar_member(
                zf, f"org/pharmgkb/pharmcat/definition/alleles/{gene}_translation.json"
            )
            for gene in SCOPED_GENES
        }
        phenotypes = {
            gene: {
                "member": f"org/pharmgkb/pharmcat/phenotype/{gene}.json",
                "sha256": hashlib.sha256(
                    zf.read(f"org/pharmgkb/pharmcat/phenotype/{gene}.json")
                ).hexdigest(),
            }
            for gene in SCOPED_GENES
            if f"org/pharmgkb/pharmcat/phenotype/{gene}.json" in zf.namelist()
        }
        guidance_raw = zf.read("org/pharmgkb/pharmcat/reporter/prescribing_guidance.json")
        cyp2c19_payload = json.loads(
            zf.read("org/pharmgkb/pharmcat/definition/alleles/CYP2C19_translation.json")
        )
        cyp2c19_star2 = next(
            allele for allele in cyp2c19_payload["namedAlleles"] if allele["name"] == "*2"
        )
        cyp2c19_star2_bases = {
            str(variant["position"]): base
            for variant, base in zip(
                cyp2c19_payload["variants"], cyp2c19_star2["alleles"], strict=True
            )
            if base is not None
        }
    # External reference metadata only; never supplied to the allele caller.
    updated_star2_bases = {
        "94775367": "R", "94775507": "R", "94781859": "A", "94842866": "R",
    }

    return {
        "schema_version": 3,
        "bundle_id": "pharmaguard-scientific-current-candidate-2026-10-14-v4",
        "purpose": "Frozen compatible research/evaluation bundle; not clinical validation or prescribing authority.",
        "application_hash_policy": {
            "version": HASH_POLICY_VERSION,
            "policy": file_identity(HASH_POLICY_RELATIVE),
            "core_file_count": len(load_hash_policy()["core_paths"]),
            "algorithm": "SHA-256 of UTF-8 domain and NUL, then sorted POSIX relative path, NUL, raw bytes, NUL for every allowlisted file",
        },
        "pharmcat": {
            "engine_version": "3.4.0",
            "jar": file_identity("test-data/reference/tools/pharmcat-3.4.0-all.jar"),
            "positions": file_identity("test-data/reference/tools/pharmcat_positions_3.4.0.vcf.bgz"),
            "positions_index": file_identity("test-data/reference/tools/pharmcat_positions_3.4.0.vcf.bgz.csi"),
            "data_version": definitions["CYP2C19"]["version"],
            "definitions": definitions,
            "phenotypes": phenotypes,
            "prescribing_guidance": {
                "member": "org/pharmgkb/pharmcat/reporter/prescribing_guidance.json",
                "sha256": hashlib.sha256(guidance_raw).hexdigest(),
                "scoped_rows": _guidance_rows(guidance_raw),
            },
        },
        "application_contract": {
            "evidence_requirements": file_identity("backend/app/data/position_requirements.json"),
            "genome_build_evidence": file_identity("backend/app/data/build_evidence.json"),
            "mapping_rules": file_identity("backend/app/data/label_mapping.yaml"),
            "capability_registry": file_identity("backend/app/data/capabilities.json"),
        },
        "explanations": {
            "corpus": tree_identity(REPO_ROOT / "rag-corpus/mechanisms"),
            "store": file_identity("backend/app/data/explanations.json"),
            "approval_manifest": file_identity("backend/app/data/explanation_approvals.json"),
            "review_state": _approval_counts(),
        },
        "evaluation": _benchmark_record(),
        "evaluation_current": current_evaluation_record(),
        "source_deltas": {
            "upstream_release_source": "https://github.com/PharmGKB/PharmCAT/releases/tag/v3.4.0",
            "CYP2C19_star2_definition": {
                "metadata_version": 1,
                "status": "not_included_in_pinned_bundle",
                "local_bundle_status": "coherent_older_definition",
                "impact": "known_version_delta",
                "isolated_definition_patch": False,
                "definition_version": definitions["CYP2C19"]["version"],
                "definition_modified": definitions["CYP2C19"]["modification_date"],
                "definition_sha256": definitions["CYP2C19"]["sha256"],
                "pinned_definition_matches_external_update": cyp2c19_star2_bases == updated_star2_bases,
                "external_definition_update": {
                    "source": "https://www.pharmvar.org/haplotype/3110",
                    "history_source": "https://www.pharmvar.org/get-haplotype-history?id=3110",
                    "version_history_source": "https://www.pharmvar.org/get-previous-versions",
                    "pharmvar_id": "PV03110",
                    "replaces_pharmvar_id": "PV00599",
                    "pharmvar_version_at_change": "6.2.28",
                    "definition_changed_at": "2026-07-31T19:30:32.000+00:00",
                    "pharmvar_release_updated_at": "2026-07-31T19:34:56.000+00:00",
                    "core_variant": "NM_000769.4:c.681G>A",
                    "core_variant_grch38": "NC_000010.11:g.94781859G>A",
                    "clinpgx_source": "https://blog.clinpgx.org/cyp2c19-2-core-allele-definition-update/",
                    "clinpgx_announcement_date": "2026-08-07",
                    "clinpgx_required_bases_grch38": updated_star2_bases,
                },
                "source_verification": {
                    "checked_on": "2026-09-30",
                    "pharmvar_current_version": "6.2.29",
                    "pharmvar_current_updated_at": "2026-09-22T21:55:42.000+00:00",
                    "pharmvar_version_source": "https://www.pharmvar.org/get-version",
                    "latest_pharmcat_release": "3.4.0",
                    "latest_pharmcat_published_at": "2026-07-14T01:19:45Z",
                    "pharmcat_release_source": "https://api.github.com/repos/PharmGKB/PharmCAT/releases/latest",
                    "newer_official_pharmcat_release_available": False,
                },
                "targeted_fixture": {
                    "allele": "*2",
                    "core_positions_grch38": cyp2c19_star2["corePositions"],
                    "pinned_required_bases_grch38": cyp2c19_star2_bases,
                },
                "upgrade_decision": "owner_controlled_whole_bundle_upgrade",
            },
            "TPMT_terminology": {
                "status": "use source phenotype/function terminology from pinned bundle; no isolated manual patch",
                "definition_version": definitions["TPMT"]["version"],
                "definition_modified": definitions["TPMT"]["modification_date"],
                "definition_sha256": definitions["TPMT"]["sha256"],
            },
            "DPYD_guideline_material": {
                "status": "pinned finalized row retained; pending/newer material is not silently mixed into this bundle",
                "guideline_source": "https://cpicpgx.org/guidelines/guideline-for-fluoropyrimidines-and-dpyd/",
                "pinned_guidance_id": "PA166122686",
                "pinned_guidance_version": 53,
                "definition_modified": definitions["DPYD"]["modification_date"],
            },
        },
        "runtime": _declared_runtime(),
        "upgrade_policy": {
            "mode": "controlled_whole_bundle_upgrade",
            "required_steps": [
                "record source delta and candidate versions",
                "update engine/data/definitions/guidance together",
                "regenerate evidence requirements and mappings where affected",
                "rerun targeted delta fixtures and complete regression suites",
                "rerun the independent benchmark without tuning on its final set",
                "regenerate this manifest and obtain required explanation review",
            ],
        },
    }


def compare(expected: Any, actual: Any, path: str = "$") -> list[str]:
    if type(expected) is not type(actual):
        return [f"{path}: expected {type(expected).__name__}, found {type(actual).__name__}"]
    if isinstance(expected, dict):
        problems: list[str] = []
        for key in sorted(set(expected) | set(actual)):
            if key not in expected:
                problems.append(f"{path}.{key}: unexpected")
            elif key not in actual:
                problems.append(f"{path}.{key}: missing")
            else:
                problems.extend(compare(expected[key], actual[key], f"{path}.{key}"))
        return problems
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return [f"{path}: expected {len(expected)} entries, found {len(actual)}"]
        problems = []
        for index, (left, right) in enumerate(zip(expected, actual)):
            problems.extend(compare(left, right, f"{path}[{index}]"))
        return problems
    return [] if expected == actual else [f"{path}: expected {expected!r}, found {actual!r}"]


def verify_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    try:
        checked = json.loads(path.read_text())
        current = build_manifest()
        problems = compare(checked, current)
        if not current["evaluation_current"]["evidence_matches"]:
            problems.append(
                "$.evaluation_current.evidence_matches: new candidate evidence is missing or incompatible"
            )
    except (OSError, ValueError, zipfile.BadZipFile, KeyError) as exc:
        return {"compatible": False, "problems": [str(exc)]}
    return {
        "compatible": not problems,
        "bundle_id": checked.get("bundle_id"),
        "manifest_sha256": sha256(path),
        "problems": problems,
    }
