"""The new cohort run must bind exact current bytes without rewriting history."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from tests.conftest import REPO_ROOT


SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import compatible_bundle as bundle  # noqa: E402


def test_current_evaluation_requires_exact_candidate_and_evidence() -> None:
    record = bundle.current_evaluation_record()
    checked = json.loads(bundle.MANIFEST_PATH.read_text())

    assert record["evidence_matches"] is True, record["problems"]
    assert record["application_core_sha256"] == bundle.application_core_hash()
    assert record == checked["evaluation_current"]
    assert checked["evaluation"]["migration_identity_matches"] is False
    assert record["fresh_application_individuals"] == 208
    assert record["reused_pharmcat_reports"] == 208
    assert record["new_cohort_caller_executions"] == 0


def test_versioned_evaluation_declares_historical_source_separately() -> None:
    record = bundle.current_evaluation_record()
    source = json.loads((REPO_ROOT / "test-data/benchmark/external/benchmark_manifest.json").read_text())
    current = json.loads(
        (REPO_ROOT / "test-data/benchmark/current-candidate-2026-10-04/evaluation_manifest.json").read_text()
    )
    assert current["historical_benchmark_id"] == source["benchmark_id"]
    assert current["candidate_application_core_sha256"] != source["local_production_artifact_sha256"]
    assert record["historical_benchmark_manifest"]["sha256"] == current["historical_benchmark_manifest"]["sha256"]


def test_current_evidence_is_portable_and_tampering_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "candidate-in-another-parent"
    manifest = json.loads(
        (REPO_ROOT / "test-data/benchmark/current-candidate-2026-10-04/evaluation_manifest.json").read_text()
    )
    refs = [manifest[name]["path"] for name in (
        "frozen_protocol", "frozen_cohort_lock", "independent_truth_workbook",
        "independent_truth_table", "frozen_combined_vcf", "pinned_jar",
        "upstream_report_manifest", "historical_benchmark_manifest",
    )]
    paths = set(bundle.load_hash_policy()["core_paths"])
    paths.update(refs)
    paths.update(item["path"] for item in manifest["outputs"])
    paths.update({
        "scripts/scientific_hash_policy.json",
        "test-data/benchmark/current-candidate-2026-10-04/evaluation_manifest.json",
        "test-data/benchmark/external/external_benchmark_results.json",
    })
    for relative in sorted(paths):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)

    assert bundle.current_evaluation_record(root)["evidence_matches"] is True
    result = root / "test-data/benchmark/current-candidate-2026-10-04/external_benchmark_results.json"
    result.write_bytes(result.read_bytes() + b"\n")
    decision = bundle.current_evaluation_record(root)
    assert decision["evidence_matches"] is False
    assert any("evidence hash or size mismatch" in item for item in decision["problems"])
