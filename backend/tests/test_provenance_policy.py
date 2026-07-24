"""
The field-level provenance policy.

These tests pin the behaviour that the old lexical gate got wrong, and they pin
the limits of the new one just as deliberately. `reports/provenance_diagnosis.md`
is the evidence: the previous checker failed a faithful paraphrase and passed a
sentence that contradicted its source, producing 15 false positives out of 16
failures on real model output.

The most important test here is `test_it_cannot_detect_a_reversed_claim`, which
asserts a *failure*. A check whose weaknesses are undocumented invites being
trusted past its competence, and this one has a specific blind spot that the
human adjudication step exists to cover.
"""

from __future__ import annotations

import pytest

from app.explanation.provenance import (
    CLAIM_LEVEL,
    FIELD_POLICY,
    NO_NEW_CLAIMS,
    VERBATIM,
    check_sentence,
    check_verbatim,
    extract_assertions,
)

SOURCE = (
    "Reduce starting dose by 50% followed by titration. "
    "Increased risk of severe or fatal toxicity. "
    "Allow 2-4 weeks to reach steady state after each dose adjustment."
)


class TestTheParaphraseFailureIsFixed:
    """The regression that motivated the whole rework."""

    def test_a_faithful_paraphrase_passes(self) -> None:
        """
        The case the old gate got wrong. "Consider dose reduction" restated as
        "your doctor may lower your dose" is the same claim in plain words —
        which is exactly what `patient_friendly` is for.
        """
        verdict = check_sentence(
            "patient_friendly", "Your doctor may lower your dose.", "Consider dose reduction."
        )
        assert verdict.verified, verdict.reason

    def test_pure_framing_passes(self) -> None:
        """Advisory sentences assert nothing clinical and must not be scored."""
        verdict = check_sentence(
            "patient_friendly",
            "Your doctor or pharmacist can help you understand what this means.",
            SOURCE,
        )
        assert verdict.verified
        assert verdict.is_framing, "a sentence with no assertion is framing"

    def test_lay_rendering_of_a_sourced_term_passes(self) -> None:
        """Translating a term of art is the point, not a provenance failure."""
        verdict = check_sentence(
            "patient_friendly",
            "You may be at higher risk of serious side effects.",
            SOURCE,
        )
        assert verdict.verified, verdict.reason


class TestItStillCatchesInvention:
    """A filter that flags nothing is worthless."""

    @pytest.mark.parametrize(
        "sentence, why",
        [
            ("Reduce the dose to 25 mg twice daily.", "dose absent from source"),
            ("This affects 40% of patients.", "percentage absent from source"),
            ("There is a 15% chance of severe toxicity.", "invented probability"),
            ("Improvement usually takes 6 months.", "invented timeline"),
            ("Check blood counts every 3 weeks.", "wrong interval"),
        ],
    )
    def test_unsourced_claims_are_flagged(self, sentence: str, why: str) -> None:
        verdict = check_sentence("patient_friendly", sentence, SOURCE)
        assert not verdict.verified, f"should have flagged ({why}): {sentence}"
        assert verdict.unsupported

    def test_a_sourced_quantity_passes(self) -> None:
        """The other half: the real 50% must not be flagged."""
        verdict = check_sentence("patient_friendly", "Your dose may be reduced by 50%.", SOURCE)
        assert verdict.verified, verdict.reason

    def test_a_sourced_timeline_passes(self) -> None:
        verdict = check_sentence(
            "patient_friendly", "It may take a few weeks to take effect.", SOURCE
        )
        assert verdict.verified, verdict.reason

    def test_quantity_matching_is_unit_aware(self) -> None:
        """
        A real false negative, fixed. Matching a bare number against any digit
        in the source let an invented "15% chance" trace to an unrelated "15"
        in a citation. The number must appear WITH its unit.
        """
        source = "Study of 25 patients published in 2015."
        verdict = check_sentence("patient_friendly", "Take 25 mg daily.", source)
        assert not verdict.verified, "25 mg must not trace to a bare '25 patients'"


class TestFieldPolicies:
    def test_every_contract_field_has_a_policy(self) -> None:
        for name in ("summary", "mechanism", "variant_rationale", "patient_friendly"):
            assert name in FIELD_POLICY

    def test_the_recommendation_is_verbatim_only(self) -> None:
        """It is never model-authored, so nothing about it is negotiable."""
        assert FIELD_POLICY["clinical_recommendation"] == VERBATIM
        assert check_verbatim("Consider  dose reduction.", "Consider dose reduction.")
        assert not check_verbatim("Consider a dose reduction.", "Consider dose reduction.")

    def test_patient_friendly_permits_paraphrase(self) -> None:
        assert FIELD_POLICY["patient_friendly"] == NO_NEW_CLAIMS

    def test_clinical_fields_are_claim_level(self) -> None:
        for name in ("summary", "mechanism", "variant_rationale"):
            assert FIELD_POLICY[name] == CLAIM_LEVEL


class TestAssertionExtraction:
    def test_framing_yields_no_assertions(self) -> None:
        assert extract_assertions("Please talk to your doctor about this.") == []

    def test_quantities_and_timelines_are_literal(self) -> None:
        kinds = {a.kind: a for a in extract_assertions("Take 50 mg for 3 weeks.")}
        assert "quantity" in kinds and kinds["quantity"].literal
        assert "time" in kinds and kinds["time"].literal

    def test_direction_is_conceptual(self) -> None:
        """So that 'lower' can match 'reduction' without sharing a spelling."""
        assertions = extract_assertions("Your dose may be lowered.")
        direction = [a for a in assertions if a.key == "direction_down"]
        assert direction and not direction[0].literal


class TestDocumentedBlindSpots:
    """
    Asserting what this CANNOT do, so the gate is not trusted past its reach.
    """

    def test_it_cannot_detect_a_reversed_claim(self) -> None:
        """
        The known blind spot, pinned deliberately.

        "Reduced TPMT activity lowers TGN accumulation" is backwards — reduced
        TPMT *raises* TGN — but every concept in it (direction_down, mechanism)
        appears in the source, so a concept-level check passes it. Detecting
        this needs a reader, which is precisely why `scripts/adjudicate.py` is
        the release gate and this module is only a filter.

        If this test ever starts failing, the checker has become smarter than
        its documentation and the docstrings must be updated to match.
        """
        source = "TPMT methylates thiopurines; reduced TPMT activity increases TGN accumulation."
        reversed_claim = "Reduced TPMT activity lowers TGN accumulation."
        verdict = check_sentence("mechanism", reversed_claim, source)
        assert verdict.verified, (
            "this SHOULD pass today — it is the documented blind spot that human "
            "adjudication covers. If it now fails, update the docs and this test."
        )


class TestPolarity:
    """
    The negation hole, closed.

    The old checker passed "Do NOT consider dose reduction" against a source
    saying "Consider dose reduction", because both contain the same words. That
    was the single most damaging behaviour it had: a checker that cannot see
    negation cannot certify a clinical claim at all.
    """

    SOURCE = "Consider dose reduction."

    def test_the_demonstrated_negation_failure_is_caught(self) -> None:
        """The exact probe from the diagnosis. This MUST flag."""
        verdict = check_sentence(
            "patient_friendly", "Do NOT consider dose reduction.", self.SOURCE
        )
        assert not verdict.verified, "the negated claim must be flagged"
        assert verdict.polarity, "it must be flagged as a POLARITY conflict"
        assert "direction_down" in verdict.polarity[0]

    def test_the_faithful_paraphrase_is_still_allowed(self) -> None:
        """Closing the hole must not reopen the false-positive problem."""
        verdict = check_sentence(
            "patient_friendly", "Your doctor may lower your dose.", self.SOURCE
        )
        assert verdict.verified, verdict.reason

    def test_the_other_direction_source_prohibits_candidate_directs_use(self) -> None:
        """
        Source says avoid; candidate says use. The candidate contains no
        negation to compare, so this needs its own rule — and it is the
        highest-consequence contradiction possible here.
        """
        verdict = check_sentence(
            "patient_friendly",
            "Use azathioprine at the standard dose.",
            "Avoid azathioprine in poor metabolizers.",
        )
        assert not verdict.verified
        assert any("prohibition" in p for p in verdict.polarity)

    def test_restating_the_prohibition_passes(self) -> None:
        verdict = check_sentence(
            "patient_friendly", "Avoid azathioprine.", "Avoid azathioprine in poor metabolizers."
        )
        assert verdict.verified, verdict.reason

    def test_negation_does_not_leak_across_clauses(self) -> None:
        """
        "Avoid clopidogrel, use prasugrel" prohibits one drug and directs
        another. A checker that let the negation reach the second clause would
        flag every faithful restatement of standard CPIC guidance.
        """
        source = "Avoid clopidogrel if possible. Use prasugrel or ticagrelor at standard dose."
        verdict = check_sentence(
            "patient_friendly", "Your doctor may choose a different medicine instead.", source
        )
        assert verdict.verified, verdict.reason

    def test_a_negated_directive_is_not_a_prohibition_conflict(self) -> None:
        """"Do not start without asking" agrees with a prohibition, not against it."""
        verdict = check_sentence(
            "patient_friendly",
            "Do not start this medicine without talking to your doctor.",
            "Avoid clopidogrel if possible. Use prasugrel at standard dose.",
        )
        assert verdict.verified, verdict.reason
