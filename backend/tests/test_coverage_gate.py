"""
The input coverage gate — tests for a safety gate that had none.

WHY THIS FILE MATTERS MORE THAN MOST

A safety gate with no tests is the exact pattern that produced the defects this
project spent Phase 6 finding: the phenotype->label edge was unverified, and the
consequence was a green `Safe` badge on fluorouracil. This gate is the only check
facing the INPUT, so nothing else can catch what it catches. If it silently stops
working, the failure mode is a confident wrong call.

Every test here therefore has a sabotage counterpart: it must fail if the gate is
disabled or a threshold loosened.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import coverage
from app.models import Phenotype, RiskLabel

REQUIREMENTS = Path(__file__).resolve().parents[1] / "app/data/position_requirements.json"


def _vcf(rows: list[tuple[str, int, str]]) -> str:
    """A minimal single-sample VCF. `rows` are (chrom, pos, genotype)."""
    head = ["##fileformat=VCFv4.2", "##reference=GRCh38",
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE"]
    body = [f"{c}\t{p}\t.\tA\tG\t.\tPASS\t.\tGT\t{gt}" for c, p, gt in rows]
    return "\n".join(head + body) + "\n"


def _positions(gene: str) -> list[tuple[str, int]]:
    spec = coverage.load_requirements()["genes"][gene]
    return [(c, p) for c, p in spec["positions"]]


def _at_coverage(gene: str, fraction: float, genotype: str = "0/0") -> str:
    """A VCF covering `fraction` of `gene`'s required positions."""
    pos = _positions(gene)
    keep = max(0, round(len(pos) * fraction))
    return _vcf([(c, p, genotype) for c, p in pos[:keep]])


ALL_GENES = ("CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "NUDT15", "DPYD")


# --------------------------------------------------------------------------- #
# Threshold enforcement: at, just above, just below
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("gene", ALL_GENES)
def test_exactly_at_the_threshold_passes(gene: str) -> None:
    """The bar is inclusive: meeting it is sufficient, not merely exceeding it."""
    spec = coverage.load_requirements()["genes"][gene]
    minimum = spec["min_coverage_percent"]
    if spec.get("decision_critical_enforced"):
        pytest.skip(
            f"{gene} additionally requires every decision-critical position; "
            f"percentage alone is deliberately no longer sufficient — see "
            f"tests/test_decision_critical_positions.py")
    report = coverage.assess(_at_coverage(gene, minimum / 100))
    got = report.genes[gene]
    assert got.percent >= minimum - 1e-9
    assert got.sufficient, f"{gene} at exactly {minimum}% must pass"


@pytest.mark.parametrize("gene", ALL_GENES)
def test_just_below_the_threshold_is_gated(gene: str) -> None:
    """One position short must gate. This is the assertion that saves a patient."""
    pos = _positions(gene)
    minimum = coverage.load_requirements()["genes"][gene]["min_coverage_percent"]
    keep = max(0, round(len(pos) * minimum / 100) - 1)
    report = coverage.assess(_vcf([(c, p, "0/0") for c, p in pos[:keep]]))
    got = report.genes[gene]
    assert not got.sufficient, (
        f"{gene} at {got.percent:.1f}% (one position below the {minimum}% bar) "
        f"was allowed through"
    )


@pytest.mark.parametrize("gene", ALL_GENES)
def test_complete_coverage_always_passes(gene: str) -> None:
    report = coverage.assess(_at_coverage(gene, 1.0))
    assert report.genes[gene].percent == pytest.approx(100.0)
    assert report.genes[gene].sufficient


def test_empty_and_headerless_input_covers_nothing() -> None:
    """No sample column means nothing is genotyped, so nothing is covered."""
    for text in ("", "##fileformat=VCFv4.2\n", "#CHROM\tPOS\tID\tREF\tALT\n"):
        report = coverage.assess(text)
        assert all(c.present == 0 for c in report.genes.values())


def test_no_call_genotypes_do_not_count_as_coverage() -> None:
    """
    `./.` is the crux of the whole gate.

    A row present with no genotype is exactly as uninformative as an absent row,
    and counting it would defeat the check while appearing to satisfy it.
    """
    pos = _positions("CYP2C19")
    for absent in ("./.", ".|.", ".", ""):
        report = coverage.assess(_vcf([(c, p, absent) for c, p in pos]))
        assert report.genes["CYP2C19"].present == 0, f"{absent!r} counted as covered"
        assert not report.genes["CYP2C19"].sufficient


# --------------------------------------------------------------------------- #
# The variants-only shape — the common case in the wild
# --------------------------------------------------------------------------- #


def test_variants_only_vcf_is_detected_with_its_own_message() -> None:
    """
    Distinct from generic low coverage because the remedy is different: re-call
    emitting all sites, rather than sequence more.
    """
    pos = _positions("CYP2C19")
    variants_only = _vcf([(c, p, "0/1") for c, p in pos[:4]])
    report = coverage.assess(variants_only)

    assert report.variants_only is True
    message = coverage.variants_only_warning()
    assert "variants-only" in message
    assert "confident WRONG result" in message, "must name the real consequence"
    # And it must not be confusable with the generic low-coverage warning.
    assert message != coverage.insufficient_warning(report.genes["CYP2C19"])


def test_a_fully_called_vcf_is_not_flagged_as_variants_only() -> None:
    report = coverage.assess(_at_coverage("CYP2C19", 1.0, genotype="0/0"))
    assert report.variants_only is False


def test_insufficient_warning_names_the_figures_and_the_direction() -> None:
    report = coverage.assess(_at_coverage("CYP2C9", 0.10))
    warning = coverage.insufficient_warning(report.genes["CYP2C9"])
    assert "CYP2C9" in warning
    assert "88" in warning, "must state coverage required"
    assert "100%" in warning, "must state the minimum"
    # The direction of the error is the point, not a decoration.
    assert "reduced function as normal" in warning


# --------------------------------------------------------------------------- #
# Directionality: the gate may only ever remove confidence
# --------------------------------------------------------------------------- #


def test_gate_can_only_remove_confidence_never_add_it() -> None:
    """
    Structural, not statistical. `insufficient()` is the only consumer of the
    thresholds, and it returns genes to SUPPRESS. There is no code path by which a
    gated gene acquires a label, so no input can move Unknown -> confident.
    """
    import inspect

    from app import main

    source = inspect.getsource(main.build_result)
    assert "starved_genes" in source
    # The demotion must be unconditional and must target Unknown specifically.
    assert "RiskLabel.UNKNOWN" in source
    assert "Phenotype.UNKNOWN" in source
    # Nothing in the gated branch may assign any other label.
    gated = source.split("starved_genes", 1)[1].split("recommendation =", 1)[0]
    for label in ("RiskLabel.SAFE", "RiskLabel.TOXIC", "RiskLabel.INEFFECTIVE",
                  "RiskLabel.ADJUST_DOSAGE"):
        assert label not in gated, f"gated branch can assign {label}"


def test_gated_gene_returns_unknown_end_to_end() -> None:
    """A real request through the app, with a deliberately starved VCF."""
    from fastapi.testclient import TestClient

    from app.main import app

    pos = _positions("CYP2C19")
    starved = _vcf([(c, p, "0/1") for c, p in pos[:3]])
    with TestClient(app) as client:
        response = client.post(
            "/analyze",
            files={"file": ("t.vcf", starved.encode(), "text/plain")},
            data={"drugs": "clopidogrel"},
        )
    if response.status_code == 503:
        pytest.skip("PharmCAT unavailable in this environment")
    assert response.status_code == 200
    body = response.json()
    assert body["analyses"][0]["risk_assessment"]["risk_label"] == "Unknown", (
        "a coverage-starved gene produced a confident label"
    )
    joined = " ".join(body["quality_metrics"]["warnings"])
    assert "required positions" in joined or "variants-only" in joined


# --------------------------------------------------------------------------- #
# quality_metrics, on every response
# --------------------------------------------------------------------------- #


def test_coverage_is_reported_pass_or_fail() -> None:
    """
    Reported even when everything passes. A confident result at low coverage is
    the dangerous case, so the reader needs the number either way — reporting it
    only on failure would hide precisely the situation that matters.
    """
    report = coverage.assess(_at_coverage("CYP2C19", 1.0))
    metrics = report.as_metrics()
    assert set(metrics) >= set(ALL_GENES)
    for gene, entry in metrics.items():
        assert set(entry) == {
            "positions_present", "positions_required", "percent",
            "minimum_percent", "sufficient",
            # Added with the position-identity requirement. Reported for EVERY
            # gene, not only the enforced one, so the exposure the other six
            # carry is visible rather than inferable.
            "decision_critical_present", "decision_critical_required",
            "decision_critical_enforced",
        }, f"{gene} metrics shape changed"


# --------------------------------------------------------------------------- #
# The data file and the code must not drift
# --------------------------------------------------------------------------- #


def test_thresholds_live_in_the_data_file_not_in_code() -> None:
    """
    No threshold may be hardcoded. The file also has to carry the measurement
    that produced each number, so a future reader can tell whether 100% was
    measured or guessed.
    """
    raw = json.loads(REQUIREMENTS.read_text())
    assert "threshold_provenance" in raw
    assert "coverage_sensitivity" in raw["threshold_provenance"]

    for gene in ALL_GENES:
        spec = raw["genes"][gene]
        assert isinstance(spec["min_coverage_percent"], int)
        assert 0 < spec["min_coverage_percent"] <= 100
        assert spec["required_positions"] == len(spec["positions"])
        # The measured wrong-rates that justify the threshold travel with it.
        assert "measured_wrong_rate_below" in spec

    source = (Path(__file__).resolve().parents[1] / "app/coverage.py").read_text()
    for literal in ("min_coverage_percent\": 100", "== 80", "== 20"):
        assert literal not in source, f"threshold {literal!r} hardcoded in coverage.py"


def test_positions_come_from_pharmcat_not_a_transcription() -> None:
    """Counts must match PharmCAT 3.4.0's own positions file."""
    raw = json.loads(REQUIREMENTS.read_text())
    assert raw["pharmcat_version"] == "3.4.0"
    expected = {"CYP2C19": 35, "CYP2C9": 88, "SLCO1B1": 35,
                "TPMT": 45, "NUDT15": 20, "DPYD": 83, "CYP2D6": 157}
    actual = {g: raw["genes"][g]["required_positions"] for g in expected}
    assert actual == expected, (
        "position counts diverge from PharmCAT 3.4.0 — regenerate rather than edit"
    )


# --------------------------------------------------------------------------- #
# Sabotage
# --------------------------------------------------------------------------- #


def test_disabling_the_gate_is_detected() -> None:
    """If `sufficient` always returned True, this fails."""
    starved = coverage.assess(_at_coverage("CYP2C9", 0.05))
    assert starved.insufficient(), (
        "a VCF with 5% CYP2C9 coverage produced no insufficient genes — the gate "
        "is disabled"
    )
    assert any(c.gene == "CYP2C9" for c in starved.insufficient())


def test_loosening_a_threshold_is_detected() -> None:
    """
    Pins the three genes measured to need complete coverage. Lowering any of them
    without new measurement fails here, and the message says what to do.
    """
    raw = json.loads(REQUIREMENTS.read_text())
    for gene in ("CYP2C19", "CYP2C9", "SLCO1B1"):
        assert raw["genes"][gene]["min_coverage_percent"] == 100, (
            f"{gene}'s threshold was lowered from the measured 100%. Re-run "
            f"scripts/measure_coverage_sensitivity.py and update the recorded "
            f"wrong-rates before changing this."
        )


def test_hom_ref_is_what_distinguishes_covered_from_absent() -> None:
    """
    Sabotage for the variants-only detector. If `0/0` stopped counting as
    coverage, a complete VCF would look variants-only and the distinction the
    gate rests on would be gone.
    """
    complete = coverage.assess(_at_coverage("TPMT", 1.0, genotype="0/0"))
    assert complete.genes["TPMT"].hom_ref_present == 45
    assert complete.genes["TPMT"].sufficient
    assert complete.variants_only is False
