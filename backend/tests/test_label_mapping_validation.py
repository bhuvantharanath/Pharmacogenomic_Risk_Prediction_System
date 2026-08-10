"""
Findings from the exhaustive CPIC label-mapping validation (Phase 6).

`scripts/validate_label_mapping.py` checks `label_mapping.yaml` against every
CPIC recommendation PharmCAT ships for our six drugs — 105 rows. These tests pin
what that found, including a **confirmed bug that is deliberately NOT fixed
here**: the validation is worthless if the artifact under test gets quietly
tuned to pass it. The fix needs its own review.
"""

from __future__ import annotations

import pytest

from app.cpic_engine import classify_annotation
from app.models import RiskLabel
from app.pharmcat_models import CpicAnnotation


def label_for(recommendation: str, implications: list[str] | None = None):
    annotation = CpicAnnotation(
        drug_recommendation=recommendation, implications=implications or []
    )
    return classify_annotation(annotation)


class TestSubstringCollisionFixed:
    """
    🔴 A real, clinically consequential mislabel found by the exhaustive run.

    CPIC's azathioprine text says to *reduce* the starting dose to 30-80% of
    standard. The `standard_dosing` rule matches the substring
    "standard starting dose" inside "30-80% of standard starting dose" and
    returns **Safe** — telling a patient who needs a dose reduction that normal
    dosing is fine. It affects 16 of the 35 azathioprine rows.

    These tests assert the CURRENT (wrong) behaviour so the bug is recorded and
    cannot regress unnoticed. When the mapping is fixed, they must be inverted
    deliberately, by someone who has read why.
    """

    REDUCED_DOSE_TEXT = (
        "Initiate therapy with reduced starting doses (30-80% of standard "
        "starting dose) if standard starting dose is ≥2 mg/kg/day. If "
        "starting dose is already below standard starting dose, dose reduction "
        "might not be needed."
    )

    def test_the_bug_is_FIXED(self) -> None:
        """
        **INVERTED DELIBERATELY.** This test previously asserted the bug was
        present (`label is RiskLabel.SAFE`), to record it without silently
        tuning the artifact under test. The fix has now landed as a general
        precedence correction — `modified_dose_instruction` is evaluated before
        `standard_dosing` — so the assertion is reversed.

        CPIC says reduce the dose to 30-80% of standard. The label must reflect
        that a dose change is required.
        """
        label, rule_id, _ = label_for(
            self.REDUCED_DOSE_TEXT,
            ["Increased risk of thiopurine-related leukopenia, neutropenia and "
             "myelosuppression."],
        )
        assert label is RiskLabel.ADJUST_DOSAGE, (
            "the substring collision has regressed: CPIC's reduced-dose text is "
            "being labelled as unchanged dosing again"
        )
        assert rule_id == "modified_dose_instruction", (
            f"expected the precedence rule to claim this row, got {rule_id}"
        )

    def test_genuine_standard_dosing_is_unaffected(self) -> None:
        """The other half: a real 'use standard dose' must still be Safe."""
        label, _, _ = label_for("Use standard starting dose.")
        assert label is RiskLabel.SAFE

    def test_a_percentage_reduction_is_what_distinguishes_them(self) -> None:
        """
        The signal a fix should key on: CPIC pairs a percentage with the word
        'reduced' when it means a reduction. Recorded so a fix has a target.
        """
        assert "reduced starting doses" in self.REDUCED_DOSE_TEXT
        assert "30-80%" in self.REDUCED_DOSE_TEXT


class TestMappingBehaviourConfirmedCorrect:
    """Rows the exhaustive run agreed on — pinned so they cannot silently drift."""

    def test_alternative_therapy_is_not_safe(self) -> None:
        label, _, _ = label_for(
            "Consider alternative nonthiopurine immunosuppressant therapy.",
            ["Greatly increased risk of thiopurine-related leukopenia."],
        )
        assert label is not RiskLabel.SAFE

    def test_avoid_is_never_safe(self) -> None:
        label, _, _ = label_for(
            "Avoid use of 5-fluorouracil or 5-fluorouracil prodrug-based regimens.",
            ["Increased risk of severe or fatal drug toxicity."],
        )
        assert label in (RiskLabel.TOXIC, RiskLabel.INEFFECTIVE)

    def test_absence_of_guidance_is_unknown_not_safe(self) -> None:
        """
        The category error the validation caught in its OWN expectation rule:
        "No recommendation" is not an assurance of safety. Pinned because
        getting this backwards is the most dangerous single error available.
        """
        label, _, _ = label_for("No recommendation")
        assert label is not RiskLabel.SAFE


class TestContradictionGuard:
    """
    CPIC's structured booleans used as a CROSS-CHECK, never as mapping input.

    The mapping deliberately keeps reading recommendation text. The exhaustive
    validation derives its expectations from these booleans, so if the mapping
    consumed them the two sides would share an input and the validation would
    agree by construction — it would stop catching anything.

    As an assertion the booleans are genuinely independent: they cannot make the
    mapping right, but they can prove it wrong.
    """

    def test_it_would_have_caught_the_collision_bug_alone(self) -> None:
        """
        The point of the guard. The 16 mislabelled rows all carried
        `dosingInformation = true` alongside a `Safe` label — "nothing needs to
        change" against "the dose must change". No expectation table required.
        """
        from app.cpic_engine import check_label_contradiction

        annotation = CpicAnnotation(
            drug_recommendation=(
                "Initiate therapy with reduced starting doses (30-80% of standard "
                "starting dose)."
            ),
            dosing_information=True,
        )
        problem = check_label_contradiction(annotation, RiskLabel.SAFE)
        assert problem is not None
        # The warning used to quote CPIC's field name at the reader. It now
        # says what the flag means, because `dosingInformation=true` is a
        # schema detail and the person seeing this warning cannot act on one.
        assert "dose change or monitoring requirement" in problem

    def test_alternate_drug_versus_no_action_is_a_contradiction(self) -> None:
        from app.cpic_engine import check_label_contradiction

        annotation = CpicAnnotation(
            drug_recommendation="Consider an alternative agent.",
            alternate_drug_available=True,
        )
        assert check_label_contradiction(annotation, RiskLabel.SAFE) is not None

    def test_genuine_standard_dosing_is_not_flagged(self) -> None:
        from app.cpic_engine import check_label_contradiction

        annotation = CpicAnnotation(
            drug_recommendation="Use standard starting dose.", dosing_information=False
        )
        assert check_label_contradiction(annotation, RiskLabel.SAFE) is None

    def test_it_only_polices_no_action_labels(self) -> None:
        """A Toxic label plus a dosing flag is not a contradiction."""
        from app.cpic_engine import check_label_contradiction

        annotation = CpicAnnotation(
            drug_recommendation="Avoid.", dosing_information=True,
            alternate_drug_available=True,
        )
        assert check_label_contradiction(annotation, RiskLabel.TOXIC) is None

    def test_the_checked_wrapper_raises(self) -> None:
        from app.cpic_engine import LabelContradiction, classify_annotation_checked

        annotation = CpicAnnotation(
            drug_recommendation="Use standard dose.", dosing_information=True
        )
        with pytest.raises(LabelContradiction):
            classify_annotation_checked(annotation)

    def test_no_false_positives_across_every_cpic_row(self) -> None:
        """
        Swept over all 105 CPIC recommendations after the fix: the guard must fire
        on none of them. A guard that cries wolf gets switched off.
        """
        import json
        from pathlib import Path

        from app.cpic_engine import check_label_contradiction

        table = Path(__file__).resolve().parents[2] / "test-data" / "reference" / "cpic_expectations.json"
        if not table.is_file():
            pytest.skip("expectation table not built; run validate_label_mapping.py --build-table")
        fired = []
        for row in json.loads(table.read_text())["rows"]:
            annotation = CpicAnnotation(
                drug_recommendation=row["recommendation"],
                implications=row["implications"],
                classification=row["classification"],
                dosing_information=row["dosingInformation"],
                alternate_drug_available=row["alternateDrugAvailable"],
            )
            label, _, _ = classify_annotation(annotation)
            if check_label_contradiction(annotation, label):
                fired.append(f"{row['drug']} {row['lookup']}")
        assert not fired, f"guard fired on consistent rows: {fired[:5]}"


class TestProvenanceOfLabels:
    """
    The mapping may not assert a label CPIC did not support.

    This is the promise the explanation layer has always enforced, and the
    exhaustive validation found the mapping layer unguarded: two clopidogrel rows
    reading literally "No recommendation" were labelled **Adjust Dosage**,
    because their *implications* prose mentioned monitoring.
    """

    def test_no_recommendation_yields_unknown(self) -> None:
        label, rule_id, _ = label_for("No recommendation")
        assert label is RiskLabel.UNKNOWN
        assert rule_id == "no_cpic_guidance"

    def test_implications_cannot_manufacture_a_directive(self) -> None:
        """
        The specific defect: rich implications must not create a recommendation
        CPIC declined to give.
        """
        label, rule_id, _ = label_for(
            "No recommendation",
            ["CYP2C19: monitor platelet reactivity; consider dose adjustment."],
        )
        assert label is RiskLabel.UNKNOWN, (
            "implications prose is being read as a directive again"
        )
        assert rule_id == "no_cpic_guidance"


class TestToxicVersusIneffectivePolicy:
    """
    One uniform policy, not ten case-by-case calls.

    TOXIC = harm from exposure. INEFFECTIVE = therapeutic failure, even when the
    failure is dangerous. The distinguishing question is whether the harm comes
    from the drug acting or from the drug failing to act.
    """

    def test_prodrug_failure_is_ineffective_not_toxic(self) -> None:
        """
        Clopidogrel PM. The cardiovascular events follow from the ABSENCE of
        antiplatelet effect, so this is failure, not poisoning — even though the
        implications contain the word "adverse".
        """
        label, _, _ = label_for(
            "Avoid clopidogrel if possible. Use prasugrel or ticagrelor at standard dose.",
            ["CYP2C19: Significantly reduced clopidogrel active metabolite formation; "
             "increased on-treatment platelet reactivity; increased risk for adverse "
             "cardiovascular events"],
        )
        assert label is RiskLabel.INEFFECTIVE

    def test_diminished_analgesia_is_ineffective(self) -> None:
        """Codeine PM: no morphine formed, so no pain relief. Failure, not harm."""
        label, _, _ = label_for(
            "Avoid codeine use.",
            ["CYP2D6: Greatly reduced morphine formation leading to diminished analgesia."],
        )
        assert label is RiskLabel.INEFFECTIVE

    def test_exposure_harm_is_toxic(self) -> None:
        """Simvastatin + decreased SLCO1B1: drug accumulates and causes myopathy."""
        label, _, _ = label_for(
            "Prescribe an alternative statin depending on the desired potency.",
            ["SLCO1B1: Increased simvastatin acid exposure as compared to normal "
             "function; increased risk of myopathy"],
        )
        assert label is RiskLabel.TOXIC

    def test_an_alternative_drug_directive_is_never_unknown(self) -> None:
        """
        It previously fell through to Unknown, silently dropping a toxicity
        warning. Unknown reads as "no information", not "use something else".
        """
        label, _, _ = label_for(
            "Prescribe an alternative statin depending on the desired potency.",
            ["SLCO1B1: increased risk of myopathy"],
        )
        assert label is not RiskLabel.UNKNOWN
