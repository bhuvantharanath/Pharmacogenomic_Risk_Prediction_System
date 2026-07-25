"""
The phenotype table: tentative calls, and the Unknown that means two things.

Two properties are pinned here, both found by the label/prose cross-check rather
than by a test — which is why they are now tests.

  1. A TENTATIVE call is still a call. If "X" maps, "possible X" and "likely X"
     must map to the same class. The prefix qualifies confidence, not function.

  2. `Phenotype.UNKNOWN` is overloaded, and the served prose must not resolve the
     ambiguity by asserting the stronger claim.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.cpic_engine import load_mapping, map_phenotype, map_phenotype_noted
from app.models import Phenotype

# Every phenotype string PharmCAT 3.4.0 can emit for our six drugs' genes, taken
# from CPIC's own lookup keys in the shipped JAR — not hand-written. Only these
# four carry a tentative qualifier; there is no "Possible Increased Function"
# anywhere in the data, so mapping one would invent coverage we cannot exercise.
TENTATIVE_STRINGS = [
    "Likely Intermediate Metabolizer",
    "Likely Poor Metabolizer",
    "Possible Decreased Function",
    "Possible Intermediate Metabolizer",
]

_QUALIFIER = re.compile(r"^(?:possible|likely)\s+", re.IGNORECASE)


@pytest.mark.parametrize("raw", TENTATIVE_STRINGS)
def test_tentative_call_maps_where_its_confident_form_maps(raw: str) -> None:
    """
    The asymmetry that produced a real divergence.

    "Possible Decreased Function" (SLCO1B1) was the one string PharmCAT emits
    that had no entry, so it fell through to Unknown — and the served prose then
    said the result was not available, under a red Toxic badge derived from the
    same annotation. The badge was right; the prose was false.
    """
    base = _QUALIFIER.sub("", raw)
    tentative, confident = map_phenotype(raw), map_phenotype(base)

    assert confident is not Phenotype.UNKNOWN, (
        f"test premise broken: {base!r} should itself map"
    )
    assert tentative == confident, (
        f"{raw!r} -> {tentative.value} but {base!r} -> {confident.value}. "
        f"A tentative call must report the real call, not Unknown."
    )


def test_no_tentative_string_is_left_unmapped() -> None:
    """Guards the whole table at once, so a new gene cannot reintroduce the gap."""
    unmapped = [s for s in TENTATIVE_STRINGS if map_phenotype(s) is Phenotype.UNKNOWN]
    assert not unmapped, f"tentative strings falling through to Unknown: {unmapped}"


def test_tentative_phenotype_does_not_reach_the_top_severity() -> None:
    """
    The confidence distinction is kept, just not in the phenotype enum.

    Mapping a tentative call onto a real class must not also promote it to the
    severity reserved for confident extreme phenotypes — otherwise closing the
    table gap would have quietly overstated certainty.
    """
    from app.cpic_engine import derive_severity
    from app.models import RiskLabel

    tentative = derive_severity(RiskLabel.TOXIC, map_phenotype("Possible Decreased Function"), None)
    confident = derive_severity(RiskLabel.TOXIC, map_phenotype("Poor Function"), None)
    assert tentative != confident, (
        "a tentative IM and a confident PM now render identically; the confidence "
        "signal has been lost"
    )


# --------------------------------------------------------------------------- #
# The overloaded Unknown (deferred schema change)
# --------------------------------------------------------------------------- #


def test_indeterminate_is_reported_as_unknown_but_says_so() -> None:
    """
    `Indeterminate` means the gene WAS called. Until the contract has a value for
    that, the raw string must travel in the warnings so the distinction is not
    silently destroyed.
    """
    phenotype, note = map_phenotype_noted("Indeterminate")
    assert phenotype is Phenotype.UNKNOWN
    assert note and "Indeterminate" in note
    assert "WAS obtained" in note


def test_genuine_no_data_carries_no_such_note() -> None:
    """When there really is no result, Unknown is the whole truth — stay quiet."""
    for raw in (None, "", "   "):
        phenotype, note = map_phenotype_noted(raw)
        assert phenotype is Phenotype.UNKNOWN
        assert note is None, f"{raw!r} should not claim a result was obtained"


def test_mapped_phenotype_carries_no_note() -> None:
    for raw in ("Normal Metabolizer", "Poor Metabolizer", "Possible Decreased Function"):
        _, note = map_phenotype_noted(raw)
        assert note is None


_FALSE_ABSENCE = re.compile(
    r"not available|was not called|no genetic (?:result|data)|could not be obtained",
    re.IGNORECASE,
)


def test_unknown_prose_never_asserts_the_data_was_missing() -> None:
    """
    The falsehood itself.

    Unknown-keyed prose is served for BOTH states, so it may not assert either
    one. "your genetic result was not available for this gene" is false whenever
    the gene was called and merely unclassifiable — and that is a claim the
    pipeline makes about its own inputs, not a clinical judgement, so there is no
    reading under which it is acceptable.
    """
    store = json.loads(
        (Path(__file__).resolve().parents[1] / "app/data/explanations.json").read_text()
    )
    offenders = [
        f"{e['drug']}:{e['phenotype']}[{field}] -> {match.group(0)!r}"
        for e in store["explanations"]
        if e["phenotype"] == "Unknown"
        for field, text in e["explanation"].items()
        if (match := _FALSE_ABSENCE.search(text))
    ]
    assert not offenders, (
        "Unknown-keyed prose asserts data was missing, which is false for the "
        f"indeterminate case: {offenders}"
    )


def test_phenotype_enum_still_has_no_indeterminate_value() -> None:
    """
    Pins the DEFERRAL, not the design.

    The right fix is a distinct enum value; it was deliberately not taken now
    because it changes the response contract and the Dart client. If someone adds
    it, this test fails — and the failure is the reminder that the warning
    workaround, the README note, and the PROJECT_STATUS entry all become stale
    and must be removed together.
    """
    assert "Indeterminate" not in {p.value for p in Phenotype}, (
        "Phenotype gained an Indeterminate value — remove the warning workaround "
        "in map_phenotype_noted and update README + PROJECT_STATUS"
    )


def test_every_phenotype_map_value_is_a_real_enum_member() -> None:
    """A typo in the YAML would otherwise degrade silently to Unknown."""
    valid = {p.value for p in Phenotype}
    bad = {k: v for k, v in load_mapping()["phenotype_map"].items() if v not in valid}
    assert not bad, f"phenotype_map values not in the Phenotype enum: {bad}"
