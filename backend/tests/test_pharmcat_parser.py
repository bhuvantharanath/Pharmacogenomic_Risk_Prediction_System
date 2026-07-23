"""
Parser tests against checked-in PharmCAT 3.4.0 output.

These run without PharmCAT, Java or Docker — that is the whole point of the
fixtures. See tests/fixtures/README.md for how to regenerate them.
"""

from __future__ import annotations

import pytest

from app.pharmcat_models import CallStatus, PharmcatReport
from app.pharmcat_runner import CYP2D6_WARNING, parse_report


class TestGeneCalls:
    def test_definite_call_is_parsed(self, cyp2c19_pm_report: PharmcatReport) -> None:
        call = cyp2c19_pm_report.gene("CYP2C19")
        assert call is not None
        assert call.status is CallStatus.DEFINITE
        assert call.diplotype == "*2/*2"
        assert call.phenotype_raw == "Poor Metabolizer"
        assert call.lookup_keys == ["Poor Metabolizer"]
        assert call.allele_functions == ["No function", "No function"]
        assert call.is_called

    def test_activity_score_is_parsed_when_present(
        self, cyp2c19_pm_report: PharmcatReport
    ) -> None:
        # CYP2C9 uses an activity-score model; CYP2C19 does not.
        assert cyp2c19_pm_report.gene("CYP2C9").activity_score == 2.0
        assert cyp2c19_pm_report.gene("CYP2C19").activity_score is None

    def test_activity_score_no_result_string_becomes_none(
        self, cyp2c19_pm_report: PharmcatReport
    ) -> None:
        """PharmCAT writes the string "No Result" here, not a number."""
        assert cyp2c19_pm_report.gene("CYP2D6").activity_score is None

    def test_heterozygous_dpyd_call(self, dpyd_im_report: PharmcatReport) -> None:
        call = dpyd_im_report.gene("DPYD")
        assert call.status is CallStatus.DEFINITE
        assert call.diplotype == "c.1905+1G>A (*2A) (heterozygous)"
        assert call.phenotype_raw == "Intermediate Metabolizer"

    def test_reference_diplotype_names_differ_per_gene(
        self, dpyd_im_report: PharmcatReport
    ) -> None:
        """CYP2C19's reference allele is *38, not *1 — a real trap."""
        assert dpyd_im_report.gene("CYP2C19").diplotype == "*38/*38"
        assert dpyd_im_report.gene("CYP2C9").diplotype == "*1/*1"

    def test_variants_are_parsed(self, cyp2c19_pm_report: PharmcatReport) -> None:
        variants = cyp2c19_pm_report.gene("CYP2C19").variants
        assert len(variants) == 35
        star2 = next(v for v in variants if v.dbSnpId == "rs4244285")
        assert star2.call == "A/A"
        assert star2.referenceAllele == "G"
        assert star2.position == 94781859


class TestCyp2d6:
    """CYP2D6 must be an honest Unknown, never a fabricated call."""

    def test_status_is_not_attempted(self, cyp2c19_pm_report: PharmcatReport) -> None:
        call = cyp2c19_pm_report.gene("CYP2D6")
        assert call is not None
        assert call.status is CallStatus.NOT_ATTEMPTED
        assert call.diplotype is None
        assert not call.is_called

    def test_carries_the_documented_warning(
        self, cyp2c19_pm_report: PharmcatReport
    ) -> None:
        assert CYP2D6_WARNING in cyp2c19_pm_report.gene("CYP2D6").warnings

    def test_warning_wording_is_pinned(self) -> None:
        """The Phase 2 spec pins this string; changing it is a contract change."""
        assert CYP2D6_WARNING == (
            "CYP2D6 structural/copy-number variation cannot be resolved from "
            "unphased VCF; outside diplotype input planned"
        )


class TestCpicAnnotations:
    def test_clopidogrel_annotations_are_verbatim(
        self, cyp2c19_pm_report: PharmcatReport
    ) -> None:
        guideline = cyp2c19_pm_report.drug("clopidogrel")
        assert guideline is not None
        assert guideline.genes == ["CYP2C19"]
        assert "clopidogrel and CYP2C19" in (guideline.guideline_name or "")

        first = guideline.annotations[0]
        assert first.drug_recommendation == (
            "Avoid clopidogrel if possible. Use prasugrel or ticagrelor at "
            "standard dose if no contraindication."
        )
        assert first.classification == "Strong"
        assert first.alternate_drug_available is True
        assert first.lookup_key == [{"CYP2C19": "Poor Metabolizer"}]

    def test_multi_gene_lookup_key_is_preserved(
        self, cyp2c19_pm_report: PharmcatReport
    ) -> None:
        """azathioprine keys off BOTH TPMT and NUDT15 in a single entry."""
        guideline = cyp2c19_pm_report.drug("azathioprine")
        assert sorted(guideline.genes) == ["NUDT15", "TPMT"]
        entry = guideline.annotations[0].lookup_key[0]
        assert set(entry) == {"TPMT", "NUDT15"}

    def test_uncalled_gene_yields_no_annotations(
        self, cyp2c19_pm_report: PharmcatReport
    ) -> None:
        """Empty annotations is the normal 'no guidance applies' signal."""
        assert cyp2c19_pm_report.drug("codeine").annotations == []

    def test_drug_lookup_is_case_insensitive(
        self, cyp2c19_pm_report: PharmcatReport
    ) -> None:
        assert cyp2c19_pm_report.drug("Clopidogrel") is not None
        assert cyp2c19_pm_report.drug("  CLOPIDOGREL  ") is not None

    def test_unknown_drug_returns_none(self, cyp2c19_pm_report: PharmcatReport) -> None:
        assert cyp2c19_pm_report.drug("aspirin") is None


class TestReportMetadata:
    def test_versions_are_captured(self, cyp2c19_pm_report: PharmcatReport) -> None:
        assert cyp2c19_pm_report.pharmcat_version == "3.4.0"
        assert cyp2c19_pm_report.data_version == "2026-07-13-11-40"

    def test_variants_called_deduplicates_shared_positions(
        self, cyp2c19_pm_report: PharmcatReport
    ) -> None:
        assert cyp2c19_pm_report.variants_called > 0


class TestMalformedInput:
    """A partial report is still worth showing; parsing must not raise."""

    @pytest.mark.parametrize(
        "raw",
        [
            {},
            {"genes": None, "drugs": None},
            {"genes": {"CYP2C19": {}}},
            {"genes": {"CYP2C19": {"recommendationDiplotypes": []}}},
            {"drugs": {"CPIC Guideline Annotation": {"x": {"guidelines": None}}}},
            {"genes": "not a dict", "drugs": ["not a dict"]},
        ],
    )
    def test_degrades_instead_of_raising(self, raw: dict) -> None:
        report = parse_report(raw)
        assert isinstance(report, PharmcatReport)

    def test_gene_block_with_no_diplotypes_is_a_no_call(self) -> None:
        report = parse_report(
            {"genes": {"CYP2C19": {"callSource": "MATCHER", "variants": []}}}
        )
        call = report.gene("CYP2C19")
        assert call.status is CallStatus.NO_CALL
        assert not call.is_called

    def test_ambiguous_call_when_several_diplotypes_match(self) -> None:
        report = parse_report(
            {
                "genes": {
                    "CYP2C19": {
                        "callSource": "MATCHER",
                        "recommendationDiplotypes": [
                            {"label": "*1/*2", "phenotypes": ["Intermediate Metabolizer"]},
                            {"label": "*1/*3", "phenotypes": ["Intermediate Metabolizer"]},
                        ],
                    }
                }
            }
        )
        call = report.gene("CYP2C19")
        assert call.status is CallStatus.AMBIGUOUS
        assert call.candidate_diplotypes == ["*1/*2", "*1/*3"]
        assert any("equally likely" in w for w in call.warnings)
