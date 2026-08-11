"""
DPYD requires position IDENTITY, not just percentage.

THE MEASUREMENT THAT WAS WRONG

DPYD's 20% threshold was justified by a measured 0%-wrong rate over a synthetic
sweep. That sweep dropped positions at random across a cohort in which DPYD's
reduced-function variants are rare — so almost every sample was truly
Reference/Reference, and calling it Normal Metabolizer was correct almost every
time whichever positions survived.

A sweep like that cannot establish that a threshold detects the absence of a
variant that is barely present in it. Absence of observed error is not absence
of possible error.

WHAT THE NUMBERS SAY

DPYD has 83 positions, 28 of them decision-critical (they define an allele whose
function assignment is not `Normal function`). At 20%, a file needs 17 of 83 —
so it may omit 66, and all 28 decision-critical positions fit inside that 66.

A file can therefore clear the percentage while carrying **not one position
capable of showing a reduced-function allele**. Every such file reads as
Reference/Reference, which is Normal Metabolizer, which is a confident `Safe` on
fluorouracil — a drug that is fatal at a standard dose in DPYD deficiency.

THE THRESHOLD IS UNCHANGED. This adds a requirement beside it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from app import coverage

REPO = Path(__file__).resolve().parents[2]


def _vcf(rows) -> str:
    head = ["##fileformat=VCFv4.2", "##reference=GRCh38",
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE"]
    return "\n".join(head + [f"{c}\t{p}\t.\tA\tG\t.\tPASS\t.\tGT\t0/0"
                             for c, p in rows]) + "\n"


def _spec(gene: str = "DPYD") -> dict:
    return coverage.load_requirements()["genes"][gene]


# --------------------------------------------------------------------------- #
# The data is derived, not typed
# --------------------------------------------------------------------------- #

def test_the_positions_came_from_pharmcats_own_function_assignments() -> None:
    """
    Sabotage check on provenance. If someone replaces the derived set with a
    hand-picked list, the provenance block goes with it and this fails.
    """
    data = json.loads(
        (REPO / "backend/app/data/position_requirements.json").read_text())
    prov = data.get("decision_critical_provenance")
    assert prov, "the derivation provenance is gone — was this hand-edited?"
    assert "functionValue" in prov["function_source"]
    assert "derive_decision_critical.py" in prov["derived_by"]


def test_dpyd_has_decision_critical_positions_and_they_are_enforced() -> None:
    spec = _spec()
    assert spec["decision_critical_count"] == 28
    assert len(spec["decision_critical_positions"]) == 28
    assert spec["decision_critical_enforced"] is True


def test_the_threshold_was_not_moved() -> None:
    """
    The point of the whole change. A requirement was ADDED; no bar moved.
    """
    assert _spec()["min_coverage_percent"] == 20
    assert _spec("TPMT")["min_coverage_percent"] == 80
    assert _spec("NUDT15")["min_coverage_percent"] == 80
    assert _spec("CYP2C19")["min_coverage_percent"] == 100


# --------------------------------------------------------------------------- #
# The requirement itself
# --------------------------------------------------------------------------- #

def test_percentage_alone_no_longer_suffices_for_dpyd() -> None:
    """
    THE CASE THE OLD RULE MISSED. A file that clears 20% using only
    non-critical positions carries nothing that could reveal a variant.
    """
    spec = _spec()
    critical = {tuple(p) for p in spec["decision_critical_positions"]}
    non_critical = [tuple(p) for p in spec["positions"]
                    if tuple(p) not in critical]
    assert len(non_critical) >= 20, "test premise: enough non-critical positions"

    cov = coverage.assess(_vcf(non_critical[:20])).genes["DPYD"]

    assert cov.percent >= cov.min_percent, "test premise: it clears the bar"
    assert cov.critical_present == 0
    assert cov.sufficient is False, (
        "a file with ZERO decision-critical positions passed DPYD — this is "
        "exactly the confident `Safe` on fluorouracil the requirement exists "
        "to stop"
    )


def test_all_critical_positions_present_still_passes() -> None:
    """The requirement must not refuse a file that genuinely has what it needs."""
    spec = _spec()
    critical = [tuple(p) for p in spec["decision_critical_positions"]]
    others = [tuple(p) for p in spec["positions"] if tuple(p) not in set(critical)]

    cov = coverage.assess(_vcf(critical + others)).genes["DPYD"]
    assert cov.critical_satisfied is True
    assert cov.sufficient is True


def test_the_other_six_genes_are_not_enforced_yet() -> None:
    """
    Measured and reported, deliberately not switched on — that is a separate
    decision. Pinned so turning one on is a visible act.
    """
    for gene in ("CYP2C19", "CYP2C9", "CYP2D6", "NUDT15", "SLCO1B1", "TPMT"):
        assert _spec(gene)["decision_critical_enforced"] is False, (
            f"{gene} enforcement was enabled — intended, or accidental?")


# --------------------------------------------------------------------------- #
# Full-payload sabotage test
# --------------------------------------------------------------------------- #

@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient
    from app import main
    return TestClient(main.app)


def _na12273_payload(client) -> dict:
    path = REPO / "test-data/demo/demo_na12273_1000g.vcf"
    if not path.exists():  # pragma: no cover
        pytest.skip("NA12273 demo file absent")
    r = client.post("/analyze",
                    files={"file": ("na.vcf", path.read_bytes(), "text/plain")},
                    data={"drugs": "fluorouracil,capecitabine"})
    if r.status_code == 503:  # pragma: no cover
        pytest.skip("PharmCAT unavailable")
    return r.json()


@pytest.mark.parametrize("drug", ["fluorouracil", "capecitabine"])
def test_na12273_full_payload_is_a_refusal_not_a_safe(client, drug: str) -> None:
    """
    THE SABOTAGE TEST, asserted on the FULL payload rather than the label.

    Measuring the label alone is what produced the incorrect earlier finding.
    With the requirement removed this sample returns, for both drugs:

        label       Safe
        confidence  0.95
        action      "Based on genotype, there is no indication to change dose
                     or therapy. Use label-recommended dosage"
        source      "Annotation of CPIC Guideline for ... (via PharmCAT)"
        phenotype   NM
    """
    body = _na12273_payload(client)
    result = next(a for a in body["analyses"] if a["drug"] == drug)
    risk, rec = result["risk_assessment"], result["clinical_recommendation"]

    assert risk["risk_label"] == "Unknown", (
        f"{drug}: {risk['risk_label']} — the identity requirement is not in force")
    assert risk["confidence_score"] < 0.5, f"{drug}: confidence {risk['confidence_score']}"
    assert "no indication to change dose" not in rec["action"].lower(), (
        f"{drug}: CPIC's no-change directive is being shown for a genotype "
        f"derived from a file with 8 of 28 decision-critical positions")
    assert "annotation of cpic guideline" not in rec["source"].lower()
    assert result["pharmacogenomic_profile"]["phenotype"] != "NM"


def test_na12273_says_why_it_was_declined(client) -> None:
    """
    A refusal on a gene that MET its percentage must explain itself, or "37% was
    enough and you refused anyway" reads as a bug.
    """
    body = _na12273_payload(client)
    dpyd = body["quality_metrics"]["position_coverage"]["DPYD"]

    assert dpyd["percent"] >= dpyd["minimum_percent"], "test premise"
    assert dpyd["decision_critical_present"] == 8
    assert dpyd["decision_critical_required"] == 28
    assert dpyd["sufficient"] is False

    joined = " ".join(body["quality_metrics"]["warnings"])
    assert "could indicate reduced function" in joined, (
        "the refusal is unexplained — the user sees Unknown on a gene the same "
        "screen says met its coverage minimum")
