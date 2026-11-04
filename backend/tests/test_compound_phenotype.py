"""
Phase 9 B1: the 2025 TPMT/NUDT15 compound intermediate metabolizer.

CPIC's 2025 thiopurine update (PMID 41618934, embedded in PharmCAT 3.4.0's
data) keys some azathioprine rows on BOTH genes: TPMT IM + NUDT15 IM starts at
20-50% of the standard dose, where either gene alone gives 30-80%. The label was
already right; the response named only TPMT, so the gene that moved the
recommendation was invisible (Phase 9 audit F-13).

Pre-committed criteria: audit/phase9/B1_PLAN.md AC4 and AC7.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace

import pytest

from app import cpic_engine
from app.explanation import approval, static_store
from app.explanation.context import ExplanationContext
from app.models import Phenotype, RiskLabel
from app.pharmcat_models import CpicAnnotation
from app.pharmcat_runner import parse_report
from app.retrieval import retrieve_mechanism
from tests.conftest import REPO_ROOT

FIXTURES = REPO_ROOT / "backend" / "tests" / "fixtures"
COMPOUND_MARK = "CPIC's recommendation here is for the combined result"
REDUCED = {"Intermediate Metabolizer", "Possible Intermediate Metabolizer"}


def _report(name: str):
    return parse_report(json.loads((FIXTURES / f"pharmcat_report_{name}.json").read_text()))


def _compound_rows() -> list[dict]:
    table = json.loads((REPO_ROOT / "test-data/reference/cpic_expectations.json").read_text())
    return [
        row for row in table["rows"]
        if row["drug"] == "azathioprine"
        and row["lookup"].get("TPMT") in REDUCED
        and row["lookup"].get("NUDT15") in REDUCED
    ]


def test_cpic_has_exactly_four_compound_reduced_rows() -> None:
    """Positive control for the parametrised test below: it must not run on nothing."""
    assert len(_compound_rows()) == 4


@pytest.mark.parametrize(
    "row", _compound_rows(), ids=lambda r: f"TPMT {r['lookup']['TPMT']} + NUDT15 {r['lookup']['NUDT15']}"
)
def test_every_compound_reduced_row_maps_to_adjust_dosage(row: dict) -> None:
    annotation = CpicAnnotation(
        drug_recommendation=row["recommendation"],
        implications=row["implications"],
        dosing_information=row["dosingInformation"],
        alternate_drug_available=row["alternateDrugAvailable"],
    )

    label, rule_id, _hint = cpic_engine.classify_annotation(annotation)

    assert "20%-50% of standard starting dose" in row["recommendation"]
    assert label is RiskLabel.ADJUST_DOSAGE
    assert rule_id == "modified_dose_instruction"


def test_the_compound_case_names_both_genes() -> None:
    assessment, recommendation, call, warnings = cpic_engine.evaluate(
        "azathioprine", _report("tpmt_im_nudt15_im")
    )

    assert assessment.risk_label is RiskLabel.ADJUST_DOSAGE
    assert "20%-50% of standard starting dose" in recommendation.action
    named = [w for w in warnings if COMPOUND_MARK in w]
    assert len(named) == 1
    assert "TPMT Intermediate Metabolizer and NUDT15 Intermediate Metabolizer" in named[0]
    assert call is not None and call.gene in named[0]


def test_a_single_gene_reduction_gets_no_compound_warning() -> None:
    assessment, recommendation, _call, warnings = cpic_engine.evaluate(
        "azathioprine", _report("tpmt_im_nudt15_nm")
    )

    assert assessment.risk_label is RiskLabel.ADJUST_DOSAGE
    assert "30-80% of standard starting dose" in recommendation.action
    assert not [w for w in warnings if COMPOUND_MARK in w]


@pytest.mark.parametrize("fixture,drug", [("cyp2c19_pm", "clopidogrel"),
                                          ("slco1b1_pm", "simvastatin"),
                                          ("dpyd_im", "fluorouracil")])
def test_single_gene_guidelines_never_get_it(fixture: str, drug: str) -> None:
    _assessment, _rec, _call, warnings = cpic_engine.evaluate(drug, _report(fixture))
    assert not [w for w in warnings if COMPOUND_MARK in w]


def test_approved_single_im_prose_is_not_served_for_the_compound_row(monkeypatch) -> None:
    """
    AC7. Approval binds the exact CPIC row an entry was written from, so prose
    written for TPMT IM (30-80%) cannot be served beside the compound row
    (20-50%) even once approved.
    """
    store = static_store.load_store()
    stored = next(e for e in store.entries.values()
                  if e.drug == "azathioprine" and e.phenotype == "IM")
    manifest = approval.load_manifest()
    record = manifest.get(stored.drug, stored.gene, stored.phenotype)
    approved = replace(record, status=approval.APPROVED, review_kind=approval.AUTHOR_REVIEW,
                       adjudicated_by=("Synthetic reviewer in test only",))
    test_manifest = replace(manifest, records={**manifest.records, approved.key: approved})

    def context(cpic_text: str, label: RiskLabel) -> ExplanationContext:
        return ExplanationContext(
            drug="azathioprine", gene="TPMT", phenotype=Phenotype.IM,
            risk_label=label, cpic_recommendation=cpic_text,
            mechanism=retrieve_mechanism("TPMT", "azathioprine"),
        )

    _a, compound_rec, _c, _w = cpic_engine.evaluate("azathioprine", _report("tpmt_im_nudt15_im"))
    # The entry's own bound identity. It predates the Phase 6 mapping fixes and
    # still records "Safe" for TPMT IM (see the stale-label test below), so the
    # positive control has to use it to isolate the SOURCE binding.
    bound = RiskLabel.SAFE if stored.derived_risk_label == "Safe" else RiskLabel(stored.derived_risk_label)

    # Positive control: the exact identity it was written for is servable once approved.
    assert approval.evaluate(stored, context(stored.cpic_recommendation_used, bound), test_manifest).approved
    # Same identity, compound CPIC row: refused on the source binding alone.
    source_only = approval.evaluate(stored, context(compound_rec.action, bound), test_manifest)
    assert not source_only.approved
    assert "source" in source_only.reason.lower()
    # The real compound request: refused.
    real = context(compound_rec.action, RiskLabel.ADJUST_DOSAGE)
    assert not approval.evaluate(stored, real, test_manifest).approved


def _current_label_for_row(drug: str, text: str) -> set[str]:
    import html
    import re

    def clean(value: str) -> str:
        value = html.unescape(re.sub(r"</?[a-zA-Z][^>]*>", " ", value or ""))
        return re.sub(r"\s+", " ", value).strip()

    table = json.loads((REPO_ROOT / "test-data/reference/cpic_expectations.json").read_text())
    labels = set()
    for row in table["rows"]:
        if row["drug"] == drug and clean(row["recommendation"]) == clean(text):
            annotation = CpicAnnotation(
                drug_recommendation=row["recommendation"], implications=row["implications"],
                dosing_information=row["dosingInformation"],
                alternate_drug_available=row["alternateDrugAvailable"],
            )
            labels.add(cpic_engine.classify_annotation(annotation)[0].value)
    return labels


def test_entries_bound_to_a_superseded_label_cannot_be_served(monkeypatch) -> None:
    """
    Found in Phase 9 B1. The store was generated on 2026-07-24, before the Phase 6
    mapping fixes, and three entries still carry the old label in their bound
    identity: azathioprine IM ("Safe", now Adjust Dosage — the substring
    collision) and simvastatin IM and PM ("Adjust Dosage", now Toxic — the
    prescribe-an-alternative rows). Their prose does not contradict the current
    labels (test_consistency passes), but even a human approval could never
    serve them, because the runtime label differs from the bound one.

    Pinned at 3 so the number is visible and any change is deliberate. Whether to
    re-derive their identity or regenerate them is the owner's decision
    (regeneration spends LLM quota and invalidates their adjudication).
    """
    store = static_store.load_store()
    manifest = approval.load_manifest()
    stale = []
    for entry in store.entries.values():
        if not entry.cpic_recommendation_used:
            continue
        bound = "No PGx-guided adjustment identified" if entry.derived_risk_label == "Safe" \
            else entry.derived_risk_label
        current = _current_label_for_row(entry.drug, entry.cpic_recommendation_used)
        if bound in current:
            continue
        stale.append(f"{entry.drug}/{entry.phenotype}")
        # Safety property: approve it synthetically; the real runtime context
        # (current label, its own CPIC row) must still be refused.
        record = manifest.get(entry.drug, entry.gene, entry.phenotype)
        approved = replace(record, status=approval.APPROVED, review_kind=approval.AUTHOR_REVIEW,
                           adjudicated_by=("Synthetic reviewer in test only",))
        test_manifest = replace(manifest, records={**manifest.records, approved.key: approved})
        (label,) = current
        runtime = ExplanationContext(
            drug=entry.drug, gene=entry.gene, phenotype=Phenotype(entry.phenotype),
            risk_label=RiskLabel(label), cpic_recommendation=entry.cpic_recommendation_used,
            mechanism=retrieve_mechanism(entry.gene, entry.drug),
        )
        assert not approval.evaluate(entry, runtime, test_manifest).approved, entry.drug

    assert sorted(stale) == ["azathioprine/IM", "simvastatin/IM", "simvastatin/PM"]


def test_end_to_end_compound_vcf_through_pharmcat(tmp_path) -> None:
    """The whole path: a VCF built from PharmCAT's definitions, through /analyze."""
    from fastapi.testclient import TestClient

    from app import main

    jar = REPO_ROOT / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
    if not jar.is_file():  # pragma: no cover
        pytest.skip("pinned PharmCAT jar absent — run: python scripts/fetch_pinned_artifacts.py")
    vcf = tmp_path / "compound.vcf"
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "test-data/generate_synthetic_vcf.py"),
         "--from-jar", str(jar), "--diplotype", "TPMT=*1/*3C", "--diplotype", "NUDT15=*1/*3",
         "--pad-genes", "CYP2C19,CYP2C9,SLCO1B1,DPYD,CYP2D6", "--sample", "COMPOUND_IM",
         "-o", str(vcf)],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    )
    response = TestClient(main.app).post(
        "/analyze", files={"file": ("compound.vcf", vcf.read_bytes(), "text/plain")},
        data={"drugs": "azathioprine"},
    )
    if response.status_code == 503:  # pragma: no cover
        pytest.skip("PharmCAT unavailable")
    body = response.json()
    analysis = body["analyses"][0]

    assert analysis["risk_assessment"]["risk_label"] == "Adjust Dosage"
    assert "20%-50% of standard starting dose" in analysis["clinical_recommendation"]["action"]
    assert any(COMPOUND_MARK in w and "NUDT15 Intermediate Metabolizer" in w
               for w in body["quality_metrics"]["warnings"])
