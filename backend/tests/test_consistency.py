"""
Label/prose consistency — the check that closed a real gap.

Three divergences were found in Phase 6 and they trace to one missing layer:

    provenance guard      verifies  explanation -> CPIC
    mapping validation    verifies  label       -> CPIC
    (nothing, until now)  verifies  explanation -> label

Two artifacts can each be faithfully traceable to the same source and still
contradict each other, because they trace to *different parts* of it. All three
real cases are fixtures here.
"""

from __future__ import annotations

import pytest

from app.explanation.consistency import (
    INTERVENTION,
    NO_DATA,
    STANDARD,
    check_consistency,
    classify_action,
)
from app.models import Phenotype, RiskLabel


def check(label: RiskLabel, phenotype: Phenotype, **fields):
    return check_consistency(label=label, phenotype=phenotype, fields=fields)


class TestTheThreeKnownDivergences:
    """Every one must be caught. These are the reason the layer exists."""

    def test_wrong_label_over_correct_prose(self) -> None:
        """
        azathioprine:IM shipped a green `Safe` badge above prose reading "your
        doctor may need to start you on a lower dose". The substring-collision
        bug produced the label; the model's text was right.
        """
        report = check(
            RiskLabel.SAFE, Phenotype.IM,
            patient_friendly="Your doctor may need to start you on a lower dose "
                             "to help your body handle the medication.",
        )
        assert not report.consistent
        assert "intervention" in report.summary

    def test_correct_label_over_wrong_prose(self) -> None:
        """
        SLCO1B1 "Possible Decreased Function" derives Toxic but collapses to
        Phenotype.UNKNOWN, so the served prose claimed the result was "not
        available" — under a red Toxic badge. The result WAS available.
        """
        report = check(
            RiskLabel.TOXIC, Phenotype.UNKNOWN,
            summary="The recommendation for your genetic result and simvastatin is "
                    "unknown because your genetic result was not available for this gene.",
        )
        assert not report.consistent
        assert "no_data" in report.summary

    def test_stale_prose_after_a_label_change(self) -> None:
        """Fixing the mapping moved labels while generated text stayed put."""
        report = check(
            RiskLabel.TOXIC, Phenotype.PM,
            patient_friendly="Your genetic results do not suggest a change to how "
                             "this medicine is usually prescribed.",
        )
        assert not report.consistent
        assert "standard_use" in report.summary


class TestConsistentPairsAreNotFlagged:
    """A check that cries wolf gets switched off. These must stay silent."""

    @pytest.mark.parametrize(
        "label, phenotype, text",
        [
            (RiskLabel.SAFE, Phenotype.NM,
             "Your genetic results do not suggest a change to how this medicine "
             "is usually prescribed."),
            (RiskLabel.TOXIC, Phenotype.PM,
             "Your doctor may choose a different medicine that is safer for you."),
            (RiskLabel.UNKNOWN, Phenotype.UNKNOWN,
             "This tool could not reach a conclusion about this medicine for you."),
            (RiskLabel.ADJUST_DOSAGE, Phenotype.IM,
             "Please discuss this result with your doctor or pharmacist."),
        ],
    )
    def test_consistent(self, label, phenotype, text) -> None:
        assert check(label, phenotype, patient_friendly=text).consistent


class TestFalsePositivesFoundOnRealProse:
    """
    Four real false positives, each an instance of the describes-vs-directs error
    the mapping file now documents. The check made the same mistake it was built
    to catch, which is why these are pinned.
    """

    def test_avoid_the_standard_dose_is_not_standard_use(self) -> None:
        """"standard dose" as the OBJECT of an avoidance means the opposite."""
        report = check(
            RiskLabel.INEFFECTIVE, Phenotype.IM,
            summary="Your genetic result affects how well you respond to clopidogrel. "
                    "It's recommended to avoid the standard dose of clopidogrel if possible.",
        )
        assert report.consistent, report.summary

    def test_standard_dose_of_an_alternative_drug(self) -> None:
        """"prasugrel or ticagrelor, at the standard dose" describes a DIFFERENT drug."""
        report = check(
            RiskLabel.INEFFECTIVE, Phenotype.PM,
            patient_friendly="It's best to avoid clopidogrel if possible. If you can't, "
                             "your doctor may recommend a different medication, such as "
                             "prasugrel or ticagrelor, at the standard dose.",
        )
        assert report.consistent, report.summary

    def test_a_metabolite_described_as_a_different_medicine(self) -> None:
        """
        "turns codeine into a different medicine that helps with pain" is
        metabolism — morphine — not a drug substitution.
        """
        report = check(
            RiskLabel.UNKNOWN, Phenotype.UNKNOWN,
            patient_friendly="We don't know how your body will handle codeine because "
                             "we can't determine how active the enzyme is. This enzyme "
                             "turns codeine into a different medicine that helps with pain.",
        )
        assert report.consistent, report.summary

    def test_mechanism_prose_is_not_action_checked(self) -> None:
        """
        `mechanism` DESCRIBES biology and legitimately mentions risk or dose.
        Action-checking it is a category error — it produced false positives on
        four shipped entries.
        """
        report = check(
            RiskLabel.SAFE, Phenotype.NM,
            mechanism="Azathioprine is a prodrug converted into active metabolites. "
                      "Reduced enzyme function increases the risk of myelosuppression, "
                      "so doctors monitor blood counts and may lower the dose.",
        )
        assert report.consistent, (
            "mechanism prose must not be action-checked: " + report.summary
        )


class TestActionClassification:
    def test_no_data_prose(self) -> None:
        assert NO_DATA in classify_action("Your result was not available for this gene.")

    def test_standard_prose(self) -> None:
        assert STANDARD in classify_action(
            "Your results do not suggest a change to how this is usually prescribed."
        )

    def test_intervention_prose(self) -> None:
        assert INTERVENTION in classify_action("Your doctor may prescribe a lower dose.")

    def test_pure_framing_asserts_nothing(self) -> None:
        assert classify_action("Please talk to your pharmacist.") == set()


class TestWholeStoreIsConsistent:
    def test_every_shipped_entry_agrees_with_its_derived_label(self) -> None:
        """
        Build-time sweep. Any divergence here would be served to a user, so this
        gates rather than reports.
        """
        import importlib.util
        import json
        import sys
        from pathlib import Path

        scripts = Path(__file__).resolve().parents[2] / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        spec = importlib.util.spec_from_file_location(
            "pregenerate_explanations", scripts / "pregenerate_explanations.py"
        )
        pg = importlib.util.module_from_spec(spec)
        sys.modules["pregenerate_explanations"] = pg
        spec.loader.exec_module(pg)

        store = json.loads(
            (Path(__file__).resolve().parents[1] / "app" / "data" / "explanations.json").read_text()
        )
        cases = {c.key: c for c in pg.load_reachable_cases()}
        divergent = []
        for entry in store["explanations"]:
            key = f"{entry['drug']}:{entry['phenotype']}"
            if key not in cases:
                continue
            context, _ = pg.build_context(cases[key])
            report = check_consistency(
                label=context.risk_label,
                phenotype=context.phenotype,
                fields=entry["explanation"],
            )
            if not report.consistent:
                divergent.append(f"{key}: {report.summary}")
        assert not divergent, "shipped entries contradict their labels:\n  " + "\n  ".join(divergent)
