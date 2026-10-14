"""Regression tests for the R1 evidence-validity boundary.

These tests use synthetic VCF text and checked-in PharmCAT reports only.  They
pin the rule that a drug-level conclusion is complete only when every declared
gene dependency has acceptable input evidence.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import coverage, main
from app import cpic_engine
from app.pharmcat_models import PharmcatReport
from app.pharmcat_runner import parse_report
from app.vcf_validation import VcfErrorCode, VcfValidationError, validate_vcf


FIXTURES = Path(__file__).parent / "fixtures"


def _one_position_vcf(
    *,
    format_field: str = "GT",
    sample_field: str = "0/0",
    filter_field: str = "PASS",
) -> str:
    return (
        "##fileformat=VCFv4.2\n"
        "##reference=GRCh38\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
        f"chr1\t100\t.\tA\tG\t.\t{filter_field}\t.\t"
        f"{format_field}\t{sample_field}\n"
    )


ONE_POSITION_REQUIREMENTS = {
    "genes": {
        "TEST": {
            "positions": [["chr1", 100]],
            "min_coverage_percent": 100,
            "decision_critical_positions": [],
            "decision_critical_enforced": False,
        }
    }
}


def _test_gene(vcf: str) -> coverage.GeneCoverage:
    return coverage.assess(vcf, ONE_POSITION_REQUIREMENTS).genes["TEST"]


class TestGenotypeEvidenceParsing:
    def test_valid_complete_call_counts(self) -> None:
        result = _test_gene(_one_position_vcf(sample_field="0/1"))
        assert result.present == 1
        assert result.sufficient is True

    def test_gt_is_read_from_its_format_position(self) -> None:
        result = _test_gene(
            _one_position_vcf(format_field="DP:GT:GQ", sample_field=".:0/1:99")
        )
        assert result.present == 1
        assert result.evidence_counts["valid_observed_genotype"] == 1

    @pytest.mark.parametrize("genotype", ["0/.", "./1", "0|.", ".|1"])
    def test_partial_genotype_does_not_count(self, genotype: str) -> None:
        result = _test_gene(_one_position_vcf(sample_field=genotype))
        assert result.present == 0
        assert result.evidence_counts["partial_genotype"] == 1

    def test_format_without_gt_does_not_count(self) -> None:
        result = _test_gene(
            _one_position_vcf(format_field="DP:GQ", sample_field="20:99")
        )
        assert result.present == 0
        assert result.evidence_counts["gt_not_provided"] == 1

    def test_explicit_filter_failure_does_not_count(self) -> None:
        result = _test_gene(_one_position_vcf(filter_field="LowQual"))
        assert result.present == 0
        assert result.evidence_counts["filter_failed"] == 1

    def test_unfiltered_quality_is_classified_without_inventing_a_threshold(self) -> None:
        result = _test_gene(_one_position_vcf(filter_field="."))
        assert result.present == 1
        assert result.sufficient is True
        assert result.evidence_counts["quality_not_established"] == 1
        warning = coverage.quality_not_established_warning(
            coverage.assess(_one_position_vcf(filter_field="."), ONE_POSITION_REQUIREMENTS)
        )
        assert "FILTER=." in warning
        assert "does not explicitly mark them as failed" in warning


def test_every_known_drug_has_one_explicit_evidence_dependency_entry() -> None:
    from app.capabilities import load_registry

    entries = load_registry()
    assert len(entries) == 6
    assert next(
        entry.evidence_dependencies
        for entry in entries
        if entry.drug == "azathioprine"
    ) == ("TPMT", "NUDT15")


MINIMAL_VCF = _one_position_vcf().encode()


class TestInvalidContainersAreRejected:
    def test_conflicting_build_declarations_are_rejected(self) -> None:
        conflicting = MINIMAL_VCF.replace(
            b"##reference=GRCh38\n",
            b"##reference=GRCh38\n##assembly=hg19\n",
        )
        with pytest.raises(VcfValidationError) as excinfo:
            validate_vcf(conflicting)
        assert excinfo.value.code is VcfErrorCode.CONFLICTING_REFERENCE_BUILD

    def test_truncated_gzip_is_rejected(self) -> None:
        truncated = gzip.compress(MINIMAL_VCF)[:-8]
        with pytest.raises(VcfValidationError) as excinfo:
            validate_vcf(truncated, "truncated.vcf.gz")
        assert excinfo.value.code is VcfErrorCode.CORRUPT_GZIP

    def test_multisample_input_is_rejected(self) -> None:
        multisample = MINIMAL_VCF.replace(
            b"FORMAT\tSAMPLE\n", b"FORMAT\tSAMPLE_A\tSAMPLE_B\n"
        ).replace(b"GT\t0/0\n", b"GT\t0/0\t0/1\n")
        with pytest.raises(VcfValidationError) as excinfo:
            validate_vcf(multisample)
        assert excinfo.value.code is VcfErrorCode.UNSUPPORTED_MULTISAMPLE


def _load_report(name: str) -> PharmcatReport:
    return parse_report(json.loads((FIXTURES / name).read_text()))


def _nudt15_im_report() -> PharmcatReport:
    """Synthetic mirror of the TPMT-IM fixture with NUDT15 as the driver."""
    report = _load_report("pharmcat_report_tpmt_im.json")
    tpmt = report.gene("TPMT")
    nudt15 = report.gene("NUDT15")
    assert tpmt is not None and nudt15 is not None

    genes = dict(report.genes)
    genes["TPMT"] = nudt15.model_copy(update={"gene": "TPMT"})
    genes["NUDT15"] = tpmt.model_copy(update={"gene": "NUDT15"})

    guideline = report.drug("azathioprine")
    assert guideline is not None
    annotations = []
    for annotation in guideline.annotations:
        swapped = []
        for key in annotation.lookup_key:
            swapped.append({
                "TPMT": key.get("NUDT15", ""),
                "NUDT15": key.get("TPMT", ""),
            })
        annotations.append(annotation.model_copy(update={"lookup_key": swapped}))
    drugs = dict(report.drugs)
    drugs["azathioprine"] = guideline.model_copy(
        update={"annotations": annotations}
    )
    return report.model_copy(update={"genes": genes, "drugs": drugs})


def _positions(gene: str) -> list[tuple[str, int]]:
    spec = coverage.load_requirements()["genes"][gene]
    return [(chrom, pos) for chrom, pos in spec["positions"]]


def _thiopurine_vcf(*, omit: str | None = None) -> bytes:
    rows: list[str] = []
    for gene in ("TPMT", "NUDT15"):
        if gene == omit:
            continue
        rows.extend(
            f"{chrom}\t{pos}\t.\tA\tG\t.\tPASS\t.\tGT\t0/0"
            for chrom, pos in _positions(gene)
        )
    return (
        "##fileformat=VCFv4.2\n"
        "##reference=GRCh38\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
        + "\n".join(rows)
        + "\n"
    ).encode()


def _post_pair(
    monkeypatch: pytest.MonkeyPatch,
    report: PharmcatReport,
    payload: bytes,
) -> tuple[dict, dict]:
    async def fake_run_pharmcat(vcf_text: str, *, sample_hint: str = "sample"):
        return report

    monkeypatch.setattr(main, "run_pharmcat", fake_run_pharmcat)
    with TestClient(main.app) as client:
        preview = client.post(
            "/coverage", files={"file": ("sample.vcf", payload, "text/plain")}
        )
        final = client.post(
            "/analyze",
            files={"file": ("sample.vcf", payload, "text/plain")},
            data={"drugs": "azathioprine"},
        )
    assert preview.status_code == 200, preview.text
    assert final.status_code == 200, final.text
    return preview.json(), final.json()


@pytest.mark.parametrize(
    ("missing_gene", "report_factory"),
    [
        ("NUDT15", lambda: _load_report("pharmcat_report_tpmt_im.json")),
        ("TPMT", _nudt15_im_report),
    ],
)
def test_missing_partner_is_partial_in_preview_and_final(
    monkeypatch: pytest.MonkeyPatch,
    missing_gene: str,
    report_factory,
) -> None:
    preview, final = _post_pair(
        monkeypatch, report_factory(), _thiopurine_vcf(omit=missing_gene)
    )

    assert "azathioprine" in preview["unanswerable_drugs"]
    assert "azathioprine" not in preview["answerable_drugs"]
    result = final["analyses"][0]
    assert result["risk_assessment"]["risk_label"] == "Unknown"
    assert result["risk_assessment"]["confidence_score"] == 0.0
    assert missing_gene in result["clinical_recommendation"]["action"]
    assert "partial" in " ".join(final["quality_metrics"]["warnings"]).lower()
    # The valid partner remains visible, but cannot become a complete verdict.
    assert result["pharmacogenomic_profile"]["primary_gene"] != missing_gene
    assert result["pharmacogenomic_profile"]["diplotype"] != "Unknown"
    assert result["pharmacogenomic_profile"]["phenotype"] == "Unknown"
    rendered = " ".join(result["llm_generated_explanation"].values()).lower()
    assert "normal metabolizer" not in rendered
    assert "safe risk" not in rendered


@pytest.mark.parametrize(
    ("report_factory", "expected_label"),
    [
        (
            lambda: _load_report("pharmcat_report_all_normal.json"),
            "No PGx-guided adjustment identified",
        ),
        (lambda: _load_report("pharmcat_report_tpmt_im.json"), "Adjust Dosage"),
        (_nudt15_im_report, "Adjust Dosage"),
    ],
)
def test_complete_partner_evidence_preserves_valid_results(
    monkeypatch: pytest.MonkeyPatch,
    report_factory,
    expected_label: str,
) -> None:
    preview, final = _post_pair(monkeypatch, report_factory(), _thiopurine_vcf())

    assert "azathioprine" in preview["answerable_drugs"]
    assert "azathioprine" not in preview["unanswerable_drugs"]
    assert final["analyses"][0]["risk_assessment"]["risk_label"] == expected_label


def test_preview_and_final_use_the_same_drug_dependency_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app import security

    for omit, expected in ((None, True), ("TPMT", False), ("NUDT15", False)):
        security.limiter.reset()
        preview, final = _post_pair(
            monkeypatch,
            _load_report("pharmcat_report_all_normal.json"),
            _thiopurine_vcf(omit=omit),
        )
        preview_eligible = "azathioprine" in preview["answerable_drugs"]
        final_eligible = (
            final["analyses"][0]["risk_assessment"]["risk_label"] != "Unknown"
        )
        assert preview_eligible is expected
        assert final_eligible is expected

    security.limiter.reset()
    quality_unknown = _thiopurine_vcf().replace(b"\tPASS\t", b"\t.\t")
    preview, final = _post_pair(
        monkeypatch,
        _load_report("pharmcat_report_all_normal.json"),
        quality_unknown,
    )
    for warnings in (preview["warnings"], final["quality_metrics"]["warnings"]):
        joined = " ".join(warnings)
        assert "Input quality was not established" in joined
        assert "FILTER=." in joined
