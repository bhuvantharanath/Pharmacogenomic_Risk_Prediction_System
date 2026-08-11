"""
`sourceDiplotypes` vs `recommendationDiplotypes` — the case the corpus lacked.

WHY THIS FILE EXISTS

Pre-deployment audit A reverted the one-word fix in `pharmcat_runner` and the
entire 630-test suite stayed green, while the live API turned

    fluorouracil  Unknown, confidence 0.1
into
    fluorouracil  SAFE,    confidence 0.95

on a real file. The regression was invisible because **every fixture in the
corpus had the two lists agreeing**, so the two code paths were
indistinguishable on the available test data. The most consequential fix in the
project rested on a distinction nothing exercised.

`pharmcat_report_dpyd_compound_het.json` is a real PharmCAT 3.4.0 report,
captured from `demo_dpyd_indeterminate.vcf`, where they differ:

    sourceDiplotypes          c.85T>C (*9A)/[c.85T>C (*9A) + c.1371C>T]
    recommendationDiplotypes  c.85T>C (*9A)/c.85T>C (*9A)

The second is PharmCAT's own reduction for LOOKING UP a CPIC row. It is not what
the matcher called, and rendering it as the patient's genotype drops a variant.

WHAT MAKES THIS A SABOTAGE TEST

It is verified to fail when the fix is reverted — see
`test_this_file_actually_catches_the_revert`, which performs the revert in
memory rather than trusting that it would.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import cpic_engine
from app.models import Phenotype, RiskLabel
from app.pharmcat_runner import parse_report

FIXTURE = Path(__file__).parent / "fixtures" / "pharmcat_report_dpyd_compound_het.json"

#: What the matcher actually called. The bracketed half is a compound
#: heterozygote: two variants in cis on one chromosome.
COMPOUND = "c.85T>C (*9A)/[c.85T>C (*9A) + c.1371C>T]"

#: What PharmCAT reduced it to for the CPIC lookup. Never a genotype to show.
REDUCED = "c.85T>C (*9A)/c.85T>C (*9A)"


@pytest.fixture(scope="module")
def raw() -> dict:
    if not FIXTURE.exists():  # pragma: no cover
        pytest.skip("compound-het fixture not captured")
    return json.loads(FIXTURE.read_text())


@pytest.fixture(scope="module")
def report(raw: dict):
    return parse_report(raw, sample_hint="dpyd")


def test_the_fixture_really_does_differ(raw: dict) -> None:
    """
    Test premise, asserted rather than assumed. If a future PharmCAT release
    stops producing divergent lists for this input, this file silently stops
    testing anything — so it says so instead.
    """
    blocks = []
    genes = raw.get("genes", {})
    for value in (genes.values() if isinstance(genes, dict) else genes):
        blocks.extend(value if isinstance(value, list) else [value])

    divergent = [
        b for b in blocks
        if isinstance(b, dict)
        and sorted(d.get("label", "") for d in (b.get("sourceDiplotypes") or []))
        != sorted(d.get("label", "") for d in (b.get("recommendationDiplotypes") or []))
    ]
    assert divergent, (
        "the fixture no longer contains a gene whose sourceDiplotypes and "
        "recommendationDiplotypes differ — recapture it, or this suite is inert"
    )


def test_the_called_diplotype_is_the_one_the_matcher_produced(report) -> None:
    """The compound half must survive into what a reader is shown."""
    call = report.gene("DPYD")
    assert call is not None
    assert call.diplotype == COMPOUND
    assert call.diplotype != REDUCED, (
        "the reduced lookup key is being rendered as the patient's genotype — "
        "a variant has been dropped from the displayed result"
    )
    assert "+" in call.diplotype, "the compound heterozygote was flattened"


def test_the_lookup_reduction_is_kept_but_kept_separate(report) -> None:
    """
    It is not discarded — auditors need to see which row CPIC guidance came
    from. It simply is not the diplotype.
    """
    call = report.gene("DPYD")
    assert call.recommendation_diplotype == REDUCED
    assert call.recommendation_diplotype != call.diplotype


def test_the_phenotype_is_not_upgraded(report) -> None:
    """
    The reduction collapses a compound heterozygote into an apparent
    homozygote, which reads as Normal Metabolizer. Nothing may assert that.
    """
    resolved = cpic_engine.resolve_phenotype(report.gene("DPYD"))
    assert resolved.asserted is False, (
        "a phenotype was asserted from a diplotype PharmCAT did not call"
    )
    assert resolved.phenotype is not Phenotype.NM


@pytest.mark.parametrize("drug", ["fluorouracil", "capecitabine"])
def test_neither_fluoropyrimidine_gets_a_confident_label(report, drug: str) -> None:
    """
    The consequence, stated as the audit measured it. These are the two drugs
    where DPYD deficiency is fatal at a standard dose, and the reverted code
    returned `Safe` at 0.95 confidence for both.
    """
    risk, _rec, _call, _warnings = cpic_engine.evaluate(drug, report)

    assert risk.risk_label is RiskLabel.UNKNOWN, (
        f"{drug}: got {risk.risk_label.value!r} from a diplotype that was never "
        f"called — this is the exact regression audit A measured"
    )
    assert risk.confidence_score < 0.5, (
        f"{drug}: confidence {risk.confidence_score} on an unasserted phenotype"
    )


def test_this_file_actually_catches_the_revert(raw: dict) -> None:
    """
    THE POINT OF THIS FILE. Performs the one-word revert in memory and asserts
    the result changes — proving these are sabotage tests rather than assertions
    that happen to hold.

    Simulated by swapping the two keys in the raw report before parsing, which
    is exactly what reading `recommendationDiplotypes` would do.
    """
    reverted = json.loads(json.dumps(raw))
    genes = reverted.get("genes", {})
    swapped = 0
    for value in (genes.values() if isinstance(genes, dict) else genes):
        for block in (value if isinstance(value, list) else [value]):
            if isinstance(block, dict) and block.get("recommendationDiplotypes"):
                block["sourceDiplotypes"] = block["recommendationDiplotypes"]
                swapped += 1
    assert swapped, "test premise: something to revert"

    bad = parse_report(reverted, sample_hint="dpyd")
    call = bad.gene("DPYD")

    # The revert reproduces the defect...
    assert call.diplotype == REDUCED
    assert "+" not in call.diplotype

    # ...and the assertions above would have caught it.
    assert call.diplotype != COMPOUND, (
        "the revert did not change the diplotype, so the tests above cannot be "
        "guarding anything — investigate before trusting this suite"
    )
    resolved = cpic_engine.resolve_phenotype(call)
    assert resolved.phenotype is Phenotype.NM and resolved.asserted, (
        "the revert no longer produces the false confident Normal Metabolizer; "
        "the failure mode has changed and this file needs revisiting"
    )
