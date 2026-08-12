"""
Two fixes that live in mapping DATA, asserted at the row level.

WHY THIS FILE EXISTS

The mutation harness in audit A could reach every fix that lives in CODE — flip
a branch, run the guard, see it go red. It could not reach these two, because
they are rules in `label_mapping.yaml`. They were recorded as **unverified**,
not as passing, and this closes that.

Each assertion is keyed on the ROW'S IDENTITY (`id:` in the mapping) and on the
CPIC text that motivated it, not on a code path — so it fails if the rule is
deleted, renamed, reordered below a rule that would swallow it, or has its
matching narrowed.

THE TWO ROWS

`no_cpic_guidance` — two clopidogrel rows whose recommendation text is literally
"No recommendation" were labelled **Adjust Dosage**, because the *implications*
prose mentioned monitoring. The label was ours, not CPIC's: the mapping-layer
version of the provenance rule the explanation layer had always enforced.

`prescribe_alternative_drug` — three simvastatin rows reading "Prescribe an
alternative statin depending on the desired potency", implications "increased
risk of myopathy", fell through to `fallback_unmatched` -> Unknown. Unknown
reads as "no information", not "use something else", so returning it there
silently DROPS a toxicity warning.
"""

from __future__ import annotations

import pytest
import yaml

from app import cpic_engine
from app.models import RiskLabel
from app.pharmcat_models import CpicAnnotation


def _rules() -> list[dict]:
    return yaml.safe_load(cpic_engine.MAPPING_PATH.read_text())["risk_label_rules"]


def _rule(rule_id: str) -> dict:
    match = [r for r in _rules() if r.get("id") == rule_id]
    assert match, (
        f"mapping rule {rule_id!r} is gone. It was added to fix a measured "
        f"defect — see the rationale block above it in label_mapping.yaml.")
    return match[0]


def _classify(recommendation: str, implications: list[str], **flags):
    annotation = CpicAnnotation(
        drug_recommendation=recommendation,
        implications=implications,
        classification=flags.pop("classification", "Strong"),
        dosing_information=flags.pop("dosing_information", False),
        alternate_drug_available=flags.pop("alternate_drug_available", False),
        other_prescribing_guidance=flags.pop("other_prescribing_guidance", False),
    )
    return cpic_engine.classify_annotation(annotation)


# --------------------------------------------------------------------------- #
# "No recommendation" must not become a directive
# --------------------------------------------------------------------------- #

def test_the_no_cpic_guidance_row_exists_and_yields_unknown() -> None:
    rule = _rule("no_cpic_guidance")
    assert str(rule["label"]).strip() == "Unknown"


def test_it_is_still_first() -> None:
    """
    Order is load-bearing. Any later rule that matches the implications text
    would win if this were moved, which is precisely the defect it fixed.
    """
    assert _rules()[0].get("id") == "no_cpic_guidance", (
        "no_cpic_guidance is no longer the first rule — a rule matching the "
        "implications prose can now claim these rows first")


def test_it_reads_the_recommendation_field_only() -> None:
    """
    The whole mechanism. Implications describe biology and may mention dose or
    monitoring even where CPIC gives no directive; only the recommendation
    field can establish that a directive exists.
    """
    assert _rule("no_cpic_guidance").get("match_field") == "recommendation"


def test_the_clopidogrel_row_that_motivated_it() -> None:
    """
    The real shape: no directive, but implications that mention monitoring.
    Before the fix this was Adjust Dosage.
    """
    label, rule_id, _ = _classify(
        "No recommendation",
        ["CYP2C19: Monitor for reduced platelet inhibition and consider "
         "alternative antiplatelet therapy"],
        dosing_information=True,
    )
    assert label is RiskLabel.UNKNOWN, (
        f"CPIC said 'No recommendation' and we produced {label.value!r} via "
        f"{rule_id!r} — the label is ours, not CPIC's")
    assert rule_id == "no_cpic_guidance"


@pytest.mark.parametrize("text", [
    "No recommendation", "no recommendation",
    "There is no recommendation for this combination.",
])
def test_the_wordings_cpic_actually_uses(text: str) -> None:
    label, _rule_id, _ = _classify(text, ["increased risk of adverse events"])
    assert label is RiskLabel.UNKNOWN


# --------------------------------------------------------------------------- #
# "Prescribe an alternative" must not fall through to Unknown
# --------------------------------------------------------------------------- #

def test_the_prescribe_alternative_row_exists_and_yields_toxic() -> None:
    rule = _rule("prescribe_alternative_drug")
    assert str(rule["label"]).strip() == "Toxic", (
        "the row now yields something else — Toxic was chosen because CPIC's "
        "stated concern here is harm from exposure (myopathy), not therapeutic "
        "failure")
    assert rule.get("severity_hint") == "high"


def test_the_simvastatin_row_that_motivated_it() -> None:
    """Before the fix this reached fallback_unmatched and returned Unknown."""
    label, rule_id, _ = _classify(
        "Prescribe an alternative statin depending on the desired potency",
        ["increased risk of myopathy"],
        alternate_drug_available=True,
    )
    assert label is RiskLabel.TOXIC, (
        f"got {label.value!r} via {rule_id!r} — Unknown here silently drops a "
        f"toxicity warning, because Unknown reads as 'no information' rather "
        f"than 'use something else'")
    assert rule_id == "prescribe_alternative_drug"


@pytest.mark.parametrize("text", [
    "Prescribe an alternative statin depending on the desired potency",
    "Consider an alternative agent",
    "Use an alternative drug",
    "Select alternative therapy",
])
def test_the_phrasings_the_regex_was_written_for(text: str) -> None:
    label, _rule_id, _ = _classify(text, ["increased risk of myopathy"])
    assert label is not RiskLabel.UNKNOWN, (
        f"{text!r} fell through to Unknown — a directive to use a different "
        f"drug was dropped")


def test_it_does_not_fire_on_prose_that_merely_mentions_alternatives() -> None:
    """
    The other half. A rule broad enough to catch every phrasing would also
    catch text that mentions alternatives without directing one, which would
    manufacture a Toxic label CPIC never gave.
    """
    label, _rule_id, _ = _classify(
        "Use label-recommended dosage. No alternative is required.",
        ["normal metabolism"])
    assert label is not RiskLabel.TOXIC
