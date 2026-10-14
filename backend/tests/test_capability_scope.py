"""Regression tests for the audited application capability boundary."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import cpic_engine, coverage, main
from app.models import RiskAssessment, RiskLabel
from app.pharmcat_runner import parse_report
from tests.conftest import REPO_ROOT


FIXTURES = Path(__file__).parent / "fixtures"
CAPABILITIES = REPO_ROOT / "backend/app/data/capabilities.json"
AUDITED_DRUGS = {
    "azathioprine",
    "clopidogrel",
    "codeine",
    "fluorouracil",
    "simvastatin",
    "warfarin",
}
GUIDANCE_CAPABLE = {
    "azathioprine",
    "clopidogrel",
    "fluorouracil",
    "simvastatin",
}


def _large_report():
    raw = json.loads((FIXTURES / "pharmcat_report_dpyd_compound_het.json").read_text())
    return parse_report(raw)


def _registry() -> dict:
    return json.loads(CAPABILITIES.read_text())


def test_registry_is_the_six_drug_audited_surface() -> None:
    entries = _registry()["capabilities"]
    assert {entry["drug"] for entry in entries} == AUDITED_DRUGS
    assert {
        entry["drug"] for entry in entries if entry["guidance_capable"]
    } == GUIDANCE_CAPABLE


def test_registry_declares_dependencies_and_explicit_negative_capabilities() -> None:
    entries = {entry["drug"]: entry for entry in _registry()["capabilities"]}
    assert entries["azathioprine"]["evidence_dependencies"] == ["TPMT", "NUDT15"]
    assert entries["codeine"]["guidance_capable"] is False
    assert "CYP2D6" in entries["codeine"]["limitation"]
    assert entries["warfarin"]["guidance_capable"] is False
    assert "automated" in entries["warfarin"]["limitation"].lower()
    for entry in entries.values():
        assert entry["ui_available"] is True
        assert entry["export_available"] is True
        assert entry["explanation_available"] is True


def test_capability_api_exposes_the_same_six_entries() -> None:
    with TestClient(main.app) as client:
        response = client.get("/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert {entry["drug"] for entry in body["capabilities"]} == AUDITED_DRUGS
    assert {
        entry["drug"]
        for entry in body["capabilities"]
        if entry["guidance_capable"]
    } == GUIDANCE_CAPABLE


def test_coverage_uses_capability_status_not_gene_coverage_alone() -> None:
    genes = {
        gene: coverage.GeneCoverage(
            gene=gene,
            required=1,
            present=1,
            hom_ref_present=1,
            min_percent=100,
        )
        for gene in ("CYP2C19", "DPYD", "TPMT", "NUDT15", "SLCO1B1", "CYP2C9", "CYP2D6")
    }
    readiness = coverage.readiness(coverage.CoverageReport(genes=genes))
    assert set(readiness["answerable_drugs"]) == GUIDANCE_CAPABLE
    assert set(readiness["unanswerable_drugs"]) == {"codeine", "warfarin"}


def test_full_upstream_drug_sweep_cannot_escape_audited_boundary() -> None:
    report = _large_report()
    assert len(report.drugs) > len(AUDITED_DRUGS)

    escaped = {}
    for drug in report.drugs:
        assessment, recommendation, _, _ = cpic_engine.evaluate(drug, report)
        if drug not in AUDITED_DRUGS and assessment.risk_label is not RiskLabel.UNKNOWN:
            escaped[drug] = assessment.risk_label.value
        if drug not in AUDITED_DRUGS:
            assert "audited application scope" in recommendation.action.lower()

    assert escaped == {}


def test_codeine_and_warfarin_are_explicitly_limited() -> None:
    report = _large_report()
    for drug, expected in (
        ("codeine", "CYP2D6"),
        ("warfarin", "automated"),
    ):
        assessment, recommendation, _, _ = cpic_engine.evaluate(drug, report)
        assert assessment.risk_label is RiskLabel.UNKNOWN
        assert expected.lower() in recommendation.action.lower()


def test_source_qualifiers_and_transporter_gene_are_preserved() -> None:
    report = _large_report()
    _, recommendation, call, _ = cpic_engine.evaluate("simvastatin", report)
    assert call is not None and call.gene == "SLCO1B1"
    assert "CPIC strength of recommendation:" in recommendation.cpic_recommendation
    assert "Population:" in recommendation.cpic_recommendation
    assert "Implications:" in recommendation.cpic_recommendation
    assert "SLCO1B1:" in recommendation.cpic_recommendation


def test_no_unconditional_safe_wire_label() -> None:
    assert RiskLabel.SAFE.value == "No PGx-guided adjustment identified"


def test_user_facing_explanations_do_not_make_unconditional_safety_claims() -> None:
    report = parse_report(
        json.loads((FIXTURES / "pharmcat_report_all_normal.json").read_text())
    )
    forbidden = (
        "safe risk",
        "safe candidate",
        "likely to be safe",
        "without any problems",
        "without concern",
        "without worrying",
    )
    for drug in GUIDANCE_CAPABLE:
        result, _, _ = main.build_result(drug, report)
        rendered = " ".join(result.llm_generated_explanation.model_dump().values()).lower()
        assert not any(phrase in rendered for phrase in forbidden), (drug, rendered)


def test_legacy_certainty_fields_are_documented_as_non_clinical() -> None:
    schema = RiskAssessment.model_json_schema()["properties"]
    for field in ("confidence_score", "severity"):
        assert schema[field]["deprecated"] is True
        description = schema[field]["description"].lower()
        assert "not" in description
        assert "clinical" in description


def test_generated_flutter_capabilities_match_registry() -> None:
    generated = (REPO_ROOT / "app/lib/generated/capabilities.g.dart").read_text()
    for entry in _registry()["capabilities"]:
        assert f"drug: '{entry['drug']}'" in generated
        assert f"primaryGene: '{entry['primary_gene']}'" in generated
        assert f"guidanceCapable: {str(entry['guidance_capable']).lower()}" in generated
