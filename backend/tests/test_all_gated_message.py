"""
An all-declined file gets one diagnosis, not seven repetitions.

WHY

The deployed site's most likely first experience is a visitor downloading a
public research VCF or a consumer SNP export, uploading it, and receiving seven
near-identical "insufficient coverage" messages. That reads as the site being
broken. It is in fact the central behaviour working — but nothing in seven
repeated paragraphs says which kind of file this is, or that the pattern is a
property of the file rather than seven independent coincidences.

So when EVERY gene is declined, the per-gene generic messages are replaced by a
single message that names the two causes. The per-gene numbers are not lost:
they remain in `quality_metrics.position_coverage` and in the readiness card.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app import coverage as cov

REPO = Path(__file__).resolve().parents[2]
DEMO = REPO / "test-data/demo"


def _assess(name: str):
    return cov.assess((DEMO / name).read_text())


@pytest.mark.parametrize("name", ["demo_variants_only.vcf",
                                  "demo_na12273_1000g.vcf"])
def test_a_wholly_gated_file_is_diagnosed_not_just_refused(name: str) -> None:
    assessment = _assess(name)
    gated = [g for g, c in assessment.genes.items() if not c.sufficient]
    assert len(gated) == len(assessment.genes), (
        f"{name} no longer gates every gene; this test needs a new fixture")

    message = cov.all_genes_gated_warning(assessment)

    # It must name the pattern, not just repeat the refusal.
    assert "property of the FILE" in message
    # It must name BOTH likely sources — a visitor knows which one they have.
    assert "research-format" in message and "array" in message
    assert "POLYMORPHIC-FILTERED" in message
    assert "23andMe" in message or "AncestryDNA" in message
    # And it must not leave them thinking the file is broken.
    assert "Neither is a bad file" in message


def test_it_quotes_the_real_coverage_range() -> None:
    """
    The numbers come from the assessment, not from prose. A hardcoded range
    would be the stale-derived-value defect this project keeps finding.
    """
    assessment = _assess("demo_na12273_1000g.vcf")
    message = cov.all_genes_gated_warning(assessment)
    worst = min(c.percent for c in assessment.genes.values())
    best = max(c.percent for c in assessment.genes.values())
    assert f"{worst:.0f}" in message and f"{best:.0f}" in message
    assert f"{len(assessment.genes)} of {len(assessment.genes)}" in message


def test_a_good_file_gets_no_such_message() -> None:
    """
    The control. If this fired on a complete-coverage file it would tell a user
    with a perfectly good VCF that their file is the wrong shape.
    """
    assessment = _assess("demo_confident.vcf")
    gated = [g for g, c in assessment.genes.items() if not c.sufficient]
    assert not gated, "the complete-coverage fixture now gates something"


def test_the_repetition_is_actually_suppressed() -> None:
    """
    The point of the change. Emitting the summary AND seven generic messages
    would be strictly worse than before — the same wall of text plus one more
    paragraph.
    """
    source = (REPO / "backend/app/main.py").read_text()
    assert "all_gated = bool(cov.genes) and len(insufficient) == len(cov.genes)" in source
    assert "elif not all_gated:" in source, (
        "the per-gene generic warning is no longer suppressed when every gene "
        "is gated — the summary would be added to the repetition, not replace it")


def test_the_critical_position_message_survives_the_suppression() -> None:
    """
    `critical_positions_warning` says something the summary does not — that a
    gene met its percentage and was still refused, on position identity. That
    is the project's sharpest point and must not be swallowed by a blanket
    "everything was gated" summary.
    """
    source = (REPO / "backend/app/main.py").read_text()
    block = source[source.index("all_gated = bool(cov.genes)"):]
    block = block[:block.index("for drug in drugs:")]
    critical_at = block.index("critical_positions_warning")
    guarded_at = block.index("elif not all_gated:")
    assert critical_at < guarded_at, (
        "critical_positions_warning is now behind the all_gated guard, so the "
        "identity refusal goes unexplained on exactly the files that need it")
