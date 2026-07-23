"""
Faithfulness guard tests.

The guard is the control that makes an LLM acceptable in this project, so these
tests are adversarial by design: each one is an attempt to smuggle a clinical
claim past it.

`TestSubstringFalseNegatives` is the important class. It pins a bug that made
the guard useless in exactly the case it exists for.
"""

from __future__ import annotations

import json

import pytest

from app.explanation.context import Explanation, ExplanationContext
from app.explanation.guard import (
    GuardReport,
    check,
    extract_entities,
    log_violation,
    read_violation_log,
)
from app.models import DetectedVariant, Phenotype, RiskLabel
from app.retrieval import retrieve_mechanism


@pytest.fixture
def context() -> ExplanationContext:
    """A realistic context: CYP2C19 poor metaboliser on clopidogrel."""
    return ExplanationContext(
        drug="clopidogrel",
        risk_label=RiskLabel.INEFFECTIVE,
        phenotype=Phenotype.PM,
        gene="CYP2C19",
        diplotype="*2/*2",
        phenotype_label="Poor Metabolizer",
        detected_variants=[
            DetectedVariant(
                rsid="rs4244285",
                gene="CYP2C19",
                genotype="A/A",
                star_allele=None,
                function="No function",
            )
        ],
        cpic_recommendation=(
            "Avoid clopidogrel if possible. Use prasugrel or ticagrelor at "
            "standard dose if no contraindication."
        ),
        cpic_implications=[
            "CYP2C19: Significantly reduced clopidogrel active metabolite formation"
        ],
        cpic_strength="Strong",
        mechanism=retrieve_mechanism("CYP2C19", "clopidogrel"),
    )


def explanation(mechanism: str = "ok", **kwargs: str) -> Explanation:
    return Explanation(
        summary=kwargs.get("summary", "ok"),
        mechanism=mechanism,
        variant_rationale=kwargs.get("variant_rationale", "ok"),
        patient_friendly=kwargs.get("patient_friendly", "ok"),
    )


class TestRejectsFabrications:
    """Every case here is a hallucination the guard must catch."""

    @pytest.mark.parametrize(
        "text,expected_kind",
        [
            # Doses — the highest-stakes category.
            ("Reduce the dose to 50 mg daily.", "dose"),
            ("Give a 300 mg loading dose.", "dose"),
            ("Use 2.5 mg/kg for this patient.", "dose"),
            ("Activity is reduced to 30%.", "dose"),
            ("Take 75 mcg twice daily.", "dose"),
            # Identifiers.
            ("The variant rs9999999 was detected.", "rsid"),
            ("They also carry *17.", "star_allele"),
            # Entities from other gene-drug pairs.
            ("TPMT activity is also reduced.", "gene"),
            ("Consider warfarin instead.", "drug"),
        ],
    )
    def test_fabricated_entity_fails(
        self, context: ExplanationContext, text: str, expected_kind: str
    ) -> None:
        report = check(explanation(text), context, generator="test")
        assert not report.passed, f"guard let {text!r} through"
        assert expected_kind in {v.kind for v in report.violations}

    def test_violation_records_the_field(self, context: ExplanationContext) -> None:
        report = check(
            explanation("ok", patient_friendly="Take 20 mg each morning."),
            context,
            generator="test",
        )
        assert not report.passed
        assert report.violations[0].field_name == "patient_friendly"

    def test_unfillable_slot_fails(self, context: ExplanationContext) -> None:
        """A stray placeholder would reach the user as literal '{foo}'."""
        report = check(explanation("Your {bogus} result."), context, generator="test")
        assert not report.passed
        assert "slot" in {v.kind for v in report.violations}


class TestAcceptsFaithfulText:
    def test_context_values_pass(self, context: ExplanationContext) -> None:
        report = check(
            Explanation(
                summary="{gene} {diplotype} gives a {phenotype} result.",
                mechanism=(
                    "CYP2C19 converts clopidogrel into its active metabolite; "
                    "CPIC names prasugrel and ticagrelor as alternatives."
                ),
                variant_rationale="The positions found were {detected_variants}.",
                patient_friendly="Speak with your doctor before changing anything.",
            ),
            context,
            generator="test",
        )
        assert report.passed, [str(v) for v in report.violations]

    def test_allowed_slots_pass(self, context: ExplanationContext) -> None:
        report = check(
            explanation("{drug} {gene} {diplotype} {phenotype} {risk_label}"),
            context,
            generator="test",
        )
        assert report.passed, [str(v) for v in report.violations]

    def test_dose_quoted_from_cpic_passes(self) -> None:
        """A number IS allowed when CPIC actually said it."""
        ctx = ExplanationContext(
            drug="clopidogrel",
            risk_label=RiskLabel.SAFE,
            phenotype=Phenotype.NM,
            gene="CYP2C19",
            diplotype="*1/*1",
            cpic_recommendation="If considering clopidogrel, use at standard dose (75 mg/day)",
        )
        report = check(
            explanation("CPIC suggests the standard 75 mg/day dose."),
            ctx,
            generator="test",
        )
        assert report.passed, [str(v) for v in report.violations]

    def test_empty_fields_are_not_violations(self, context: ExplanationContext) -> None:
        report = check(Explanation("", "", "", ""), context, generator="test")
        assert report.passed


class TestSubstringFalseNegatives:
    """
    Regression tests for a bug that made the guard useless.

    The first implementation checked containment with `needle in haystack`. The
    mechanism corpus says "cytochrome P450", and "P450" contains "50" — so an
    invented "50 mg" was silently accepted. A fabricated dose passing the dose
    check is the worst failure this module can have.

    Entity matching is now boundary-aware. These tests pin that.
    """

    def test_dose_does_not_match_inside_a_larger_number(
        self, context: ExplanationContext
    ) -> None:
        assert "P450" in context.grounding_text()
        report = check(explanation("Take 50 mg daily."), context, generator="test")
        assert not report.passed, "'50 mg' matched the '50' inside 'P450'"

    @pytest.mark.parametrize("dose", ["45", "5", "0", "244"])
    def test_digits_of_other_tokens_do_not_ground_a_dose(
        self, context: ExplanationContext, dose: str
    ) -> None:
        """rs4244285 and *2/*2 must not license arbitrary dose numbers."""
        report = check(explanation(f"Give {dose} mg."), context, generator="test")
        assert not report.passed, f"{dose} mg was grounded by an unrelated token"

    def test_star_allele_prefix_does_not_ground_a_longer_one(
        self, context: ExplanationContext
    ) -> None:
        """Context has *2; *22 must not pass on the strength of its first digit."""
        report = check(explanation("They carry *22."), context, generator="test")
        assert not report.passed

    def test_rsid_prefix_does_not_ground_a_longer_one(
        self, context: ExplanationContext
    ) -> None:
        """Context has rs4244285; rs42442850 must not pass."""
        report = check(explanation("Variant rs42442850 found."), context, generator="test")
        assert not report.passed


class TestExtraction:
    def test_extracts_each_kind(self) -> None:
        entities = extract_entities(
            "Give 50 mg of clopidogrel; rs4244285 and *2 affect CYP2C19."
        )
        assert "50" in entities["dose"]
        assert "rs4244285" in entities["rsid"]
        assert "*2" in entities["star_allele"]
        assert "CYP2C19" in entities["gene"]
        assert "clopidogrel" in entities["drug"]

    def test_small_counting_numbers_are_ignored(self) -> None:
        """'one of two copies' is grammar, not a clinical quantity."""
        entities = extract_entities("Both 2 copies were inherited from 1 parent.")
        assert entities["number"] == set()

    def test_a_dose_is_not_double_counted_as_a_number(self) -> None:
        entities = extract_entities("Take 50 mg.")
        assert entities["dose"] == {"50"}
        assert "50" not in entities["number"]


class TestReportShape:
    def test_passing_report(self, context: ExplanationContext) -> None:
        report = check(explanation("ok"), context, generator="template")
        assert report.passed
        assert report.action_taken == "accepted"
        assert "passed" in report.summary

    def test_failing_report_is_serialisable(self, context: ExplanationContext) -> None:
        report = check(explanation("Take 999 mg."), context, generator="llm:test")
        payload = report.to_dict()
        assert payload["passed"] is False
        assert payload["violations"][0]["kind"] == "dose"
        json.dumps(payload)  # must not raise


class TestViolationLog:
    def test_writes_jsonl(self, tmp_path, context: ExplanationContext) -> None:
        log = tmp_path / "guard.jsonl"
        bad = explanation("Take 999 mg.")
        report = check(bad, context, generator="llm:test")

        log_violation(report, context, bad, path=log)
        log_violation(report, context, bad, path=log)

        records = read_violation_log(log)
        assert len(records) == 2
        assert records[0]["drug"] == "clopidogrel"
        assert records[0]["passed"] is False
        assert records[0]["violations"][0]["token"] == "999"
        # The offending text is kept so a reviewer can see what was said.
        assert "999" in records[0]["rejected_text"]["mechanism"]

    def test_unwritable_path_does_not_raise(self, context: ExplanationContext) -> None:
        """Logging must never be able to fail a request."""
        report = GuardReport(passed=False, action_taken="test")
        log_violation(report, context, path=None if False else _UNWRITABLE)

    def test_missing_log_reads_as_empty(self, tmp_path) -> None:
        assert read_violation_log(tmp_path / "nope.jsonl") == []


# A path that cannot be created — used by the "never raises" test above.
_UNWRITABLE = __import__("pathlib").Path("/proc/nonexistent/guard.jsonl")
