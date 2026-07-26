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


# --------------------------------------------------------------------------- #
# sourceDiplotypes vs recommendationDiplotypes (found at scale, 2026-07-25)
# --------------------------------------------------------------------------- #


def test_called_diplotype_is_reported_not_the_lookup_reduction() -> None:
    """
    The DPYD defect the 400-sample fidelity run found.

    PharmCAT publishes what it CALLED (`sourceDiplotypes`, compound alleles
    intact, phenotype possibly "Indeterminate") separately from the reduction it
    uses to FIND a CPIC row (`recommendationDiplotypes`, compound alleles split so
    an activity score can be assigned). Reading the second for both purposes
    displayed `Normal Metabolizer` where PharmCAT had said `Indeterminate`, and
    dropped a real variant from the reported genotype.

    Over-claiming certainty PharmCAT withheld is the mirror of the under-claiming
    in [[limitation #21]]; both misstate what is known.
    """
    from app.pharmcat_runner import _parse_gene

    block = {
        "callSource": "MATCHER",
        "sourceDiplotypes": [{
            "label": "c.85T>C (*9A)/[c.85T>C (*9A) + c.1371C>T]",
            "phenotypes": ["Indeterminate"],
            "lookupKey": ["n/a"],
        }],
        "recommendationDiplotypes": [{
            "label": "c.85T>C (*9A)/c.85T>C (*9A)",
            "phenotypes": ["Normal Metabolizer"],
            "activityScore": 2.0,
            "lookupKey": ["2.0"],
        }],
    }
    call = _parse_gene("DPYD", block)

    # What the patient has -> from the CALLED diplotype.
    assert call.diplotype == "c.85T>C (*9A)/[c.85T>C (*9A) + c.1371C>T]"
    assert "c.1371C>T" in call.diplotype, "a carried variant was dropped"
    assert call.phenotype_raw == "Indeterminate", (
        "reported a definite phenotype PharmCAT explicitly withheld"
    )

    # How CPIC guidance is found -> from the RECOMMENDATION entry, unchanged.
    assert call.lookup_keys == ["2.0"], "CPIC lookup must not regress to 'n/a'"
    assert call.activity_score == 2.0
    assert call.recommendation_diplotype == "c.85T>C (*9A)/c.85T>C (*9A)"


def test_single_list_genes_are_unaffected_by_the_split() -> None:
    """For every gene but DPYD the two lists agree, so nothing should change."""
    from app.pharmcat_runner import _parse_gene

    entry = {
        "label": "*1/*2",
        "phenotypes": ["Intermediate Metabolizer"],
        "lookupKey": ["Intermediate Metabolizer"],
    }
    call = _parse_gene("CYP2C19", {
        "callSource": "MATCHER",
        "sourceDiplotypes": [entry],
        "recommendationDiplotypes": [entry],
    })
    assert call.diplotype == "*1/*2"
    assert call.phenotype_raw == "Intermediate Metabolizer"
    assert call.lookup_keys == ["Intermediate Metabolizer"]


def test_dpyd_indeterminate_routes_to_unknown_not_normal_metabolizer() -> None:
    """
    SAFETY-CRITICAL ROUTING. DPYD deficiency causes fatal fluorouracil toxicity.

    Of every error this pipeline can make, displaying `Normal Metabolizer` for a
    DPYD call PharmCAT declined to classify is the worst available one: it removes
    the single warning that stands between a deficient patient and a lethal dose,
    and it removes it silently, wearing the appearance of a confident result.

    Before the sourceDiplotypes fix, an Indeterminate DPYD call was displayed as
    `Normal Metabolizer` (from PharmCAT's lookup reduction) and routed to the
    `fluorouracil:NM` explanation. It must route to `fluorouracil:Unknown`:
    PharmCAT withheld certainty, so the system withholds it too.

    Measured incidence on the 400-sample validation cohort: 4 of 302 called DPYD
    samples. Rare is not the same as acceptable when the failure mode is fatal.
    """
    from app.cpic_engine import map_phenotype_noted
    from app.pharmcat_runner import _parse_gene

    call = _parse_gene("DPYD", {
        "callSource": "MATCHER",
        "sourceDiplotypes": [{
            "label": "c.85T>C (*9A)/[c.85T>C (*9A) + c.1371C>T]",
            "phenotypes": ["Indeterminate"],
            "lookupKey": ["n/a"],
        }],
        "recommendationDiplotypes": [{
            "label": "c.85T>C (*9A)/c.85T>C (*9A)",
            "phenotypes": ["Normal Metabolizer"],
            "activityScore": 2.0,
            "lookupKey": ["2.0"],
        }],
    })
    phenotype, note = map_phenotype_noted(call.phenotype_raw)

    assert call.phenotype_raw == "Indeterminate"
    assert phenotype is Phenotype.UNKNOWN, (
        "DPYD Indeterminate must not present as a confident metabolizer class"
    )
    assert phenotype.value != "NM", "would route to fluorouracil:NM — the fatal case"
    # The distinction is not merely dropped: the raw call travels in a warning.
    assert note and "Indeterminate" in note

    store = json.loads(
        (Path(__file__).resolve().parents[1] / "app/data/explanations.json").read_text()
    )
    keyed = {e["phenotype"] for e in store["explanations"] if e["drug"] == "fluorouracil"}
    assert phenotype.value in keyed, (
        f"no fluorouracil:{phenotype.value} entry, so this call would fall back to "
        f"a template instead of the reviewed explanation"
    )


def test_recommendation_diplotype_comes_from_its_own_pharmcat_source() -> None:
    """
    The two fields must be populated from the two DIFFERENT PharmCAT lists.

    Asserting they *can* differ is the point: a test that only checked equality
    would pass against the very bug this field documents.
    """
    from app.pharmcat_runner import _parse_gene

    call = _parse_gene("DPYD", {
        "callSource": "MATCHER",
        "sourceDiplotypes": [{
            "label": "c.85T>C (*9A)/[c.85T>C (*9A) + c.1371C>T]",
            "phenotypes": ["Indeterminate"],
        }],
        "recommendationDiplotypes": [{
            "label": "c.85T>C (*9A)/c.85T>C (*9A)",
            "phenotypes": ["Normal Metabolizer"],
            "activityScore": 2.0,
            "lookupKey": ["2.0"],
        }],
    })
    assert call.diplotype != call.recommendation_diplotype, (
        "the compound case must expose two distinct values"
    )
    assert "[" in call.diplotype, "called diplotype lost its compound allele"
    assert "[" not in call.recommendation_diplotype

    # And the API must not echo the same string twice under two names.
    from app.main import _profile

    profile = _profile(call, Phenotype.UNKNOWN)
    assert profile.diplotype == call.diplotype
    assert profile.recommendation_diplotype == call.recommendation_diplotype

    same = _parse_gene("CYP2C19", {
        "callSource": "MATCHER",
        "sourceDiplotypes": [{"label": "*1/*2", "phenotypes": ["Intermediate Metabolizer"]}],
        "recommendationDiplotypes": [{
            "label": "*1/*2", "phenotypes": ["Intermediate Metabolizer"],
            "lookupKey": ["Intermediate Metabolizer"],
        }],
    })
    assert _profile(same, Phenotype.IM).recommendation_diplotype is None, (
        "identical values must not be duplicated into the response"
    )
