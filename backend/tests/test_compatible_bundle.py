"""Phase 5 regressions for the frozen compatible scientific record."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import zipfile

from tests.conftest import REPO_ROOT


SCRIPTS = REPO_ROOT / "scripts"


def _load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "compatible_bundle", SCRIPTS / "compatible_bundle.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["compatible_bundle"] = module
    spec.loader.exec_module(module)
    return module


bundle = _load()
CHECKED = json.loads(bundle.MANIFEST_PATH.read_text())


def test_checked_manifest_matches_declared_environment() -> None:
    assert bundle.build_manifest() == CHECKED
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "verify_compatible_bundle.py"), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 0, payload["problems"]
    assert payload["compatible"] is True


def test_content_hash_mismatch_is_detected() -> None:
    altered = copy.deepcopy(CHECKED)
    altered["application_contract"]["mapping_rules"]["sha256"] = "0" * 64

    problems = bundle.compare(altered, CHECKED)

    assert any("mapping_rules.sha256" in problem for problem in problems)


def test_source_row_version_difference_is_detected() -> None:
    altered = copy.deepcopy(CHECKED)
    altered["pharmcat"]["prescribing_guidance"]["scoped_rows"]["fluorouracil"]["version"] += 1

    problems = bundle.compare(altered, CHECKED)

    assert any("fluorouracil.version" in problem for problem in problems)


def test_report_counts_reproduce_with_explicit_units() -> None:
    record = CHECKED["evaluation"]
    results = json.loads((REPO_ROOT / record["results"]["path"]).read_text())
    reports = json.loads(
        (REPO_ROOT / "test-data/benchmark/external/pharmcat_report_manifest.json").read_text()
    )

    assert record["cohort_samples"] == results["cohort_samples"] == 208
    assert record["sample_gene_rows"] == results["sample_gene_truth_rows"] == 1456
    assert record["truth_evaluable"] == results["truth_status_counts"]["evaluable"] == 596
    assert record["pharmcat_reports"] == reports["report_count"] == 208
    assert "repeated measures" in record["sample_unit"]
    assert record["evidence_type"].startswith("independent")
    assert CHECKED["schema_version"] == 3
    assert CHECKED["application_hash_policy"]["version"] == 2
    # The 2026-09-24 hash-only migration remains historical. Its old portable
    # hash does not represent the changed candidate; new v2 evidence does.
    assert record["migration_identity_matches"] is False
    assert record["application_core_sha256"] != record["benchmark_historical_application_sha256"]
    assert record["benchmark_historical_hash_policy_version"] == 1
    assert record["benchmark_rerun_for_hash_migration"] is False
    migration = json.loads((REPO_ROOT / record["identity_migration"]["path"]).read_text())
    assert record["application_core_sha256"] != migration["portable_application_sha256"]
    assert record["benchmark_historical_application_sha256"] == migration["historical_application_sha256"]
    current = CHECKED["evaluation_current"]
    assert current["evidence_matches"] is True
    assert current["application_core_sha256"] == record["application_core_sha256"]
    assert current["fresh_application_individuals"] == 208
    assert current["reused_pharmcat_reports"] == 208
    assert current["new_cohort_caller_executions"] == 0
    reproduction = json.loads((REPO_ROOT / record["reproduction_record"]["path"]).read_text())
    assert reproduction["bundle_id"] == migration["historical_bundle_id"]
    assert reproduction["bundle_id"] != CHECKED["bundle_id"]
    assert reproduction["reproduced_metrics"]["truth_evaluable_denominator"] == 596


def test_targeted_source_deltas_are_pinned_not_manually_mixed() -> None:
    deltas = CHECKED["source_deltas"]

    assert deltas["CYP2C19_star2_definition"]["status"] == "not_included_in_pinned_bundle"
    assert deltas["CYP2C19_star2_definition"]["local_bundle_status"] == "coherent_older_definition"
    assert deltas["CYP2C19_star2_definition"]["impact"] == "known_version_delta"
    assert deltas["CYP2C19_star2_definition"]["isolated_definition_patch"] is False
    assert deltas["CYP2C19_star2_definition"]["definition_sha256"] == CHECKED["pharmcat"]["definitions"]["CYP2C19"]["sha256"]
    assert deltas["CYP2C19_star2_definition"]["targeted_fixture"] == {
        "allele": "*2",
        "core_positions_grch38": [94775367, 94775507, 94781859, 94842866],
        "pinned_required_bases_grch38": {
            "94775367": "G", "94775507": "R", "94781859": "A", "94842866": "G",
        },
    }
    assert "source phenotype/function terminology" in deltas["TPMT_terminology"]["status"]
    assert deltas["TPMT_terminology"]["definition_sha256"] == CHECKED["pharmcat"]["definitions"]["TPMT"]["sha256"]
    assert "pending/newer material is not silently mixed" in deltas["DPYD_guideline_material"]["status"]
    assert deltas["DPYD_guideline_material"]["pinned_guidance_version"] == CHECKED["pharmcat"]["prescribing_guidance"]["scoped_rows"]["fluorouracil"]["version"]


def test_cyp2c19_inclusion_claim_requires_pinned_definition_and_version_evidence() -> None:
    delta = CHECKED["source_deltas"]["CYP2C19_star2_definition"]
    external = delta["external_definition_update"]
    with zipfile.ZipFile(bundle.JAR_PATH) as zf:
        definition = json.loads(zf.read(CHECKED["pharmcat"]["definitions"]["CYP2C19"]["member"]))
    allele = next(row for row in definition["namedAlleles"] if row["name"] == "*2")
    actual = {
        str(variant["position"]): base
        for variant, base in zip(definition["variants"], allele["alleles"], strict=True)
        if base is not None
    }

    assert actual == delta["targeted_fixture"]["pinned_required_bases_grch38"]
    assert external["pharmvar_version_at_change"] == "6.2.28"
    assert external["definition_changed_at"] == "2026-07-31T19:30:32.000+00:00"
    assert external["pharmvar_id"] == "PV03110"
    assert external["core_variant"] == "NM_000769.4:c.681G>A"
    assert external["clinpgx_announcement_date"] == "2026-08-07"
    assert external["clinpgx_required_bases_grch38"] == {
        "94775367": "R", "94775507": "R", "94781859": "A", "94842866": "R",
    }
    bases_match = actual == external["clinpgx_required_bases_grch38"]
    dates_support_inclusion = (
        external["definition_changed_at"][:10]
        <= definition["modificationDate"][:10]
        <= definition["version"][:10]
    )
    assert delta["pinned_definition_matches_external_update"] is bases_match
    assert (delta["status"] == "included_in_pinned_bundle") is (
        bases_match and dates_support_inclusion
    )
    assert bases_match is False  # The frozen bundle retains the companion G requirements.


def test_false_cyp2c19_inclusion_claim_fails_verification(tmp_path) -> None:
    altered = copy.deepcopy(CHECKED)
    altered["source_deltas"]["CYP2C19_star2_definition"]["status"] = "included_in_pinned_bundle"
    path = tmp_path / "falsely-included.json"
    path.write_text(json.dumps(altered))

    result = bundle.verify_manifest(path)

    assert result["compatible"] is False
    assert any("CYP2C19_star2_definition.status" in item for item in result["problems"])
