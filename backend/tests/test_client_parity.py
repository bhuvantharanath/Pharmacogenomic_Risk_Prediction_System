"""
Pydantic <-> Dart parity, checked by reading the Dart source.

WHY A CROSS-LANGUAGE TEST

The two model definitions are the same contract written twice, and nothing in
either toolchain notices when they diverge. The failure is quiet in the worst
way: adding a field to Pydantic and forgetting the Dart side does not break a
build or throw at runtime — `json['new_field']` is simply null, so the client
renders as though the backend never sent it.

That is how a safety-relevant field disappears silently. `guideline_provenance`
and the whole /coverage payload are exactly that kind of field, so parity is
asserted rather than assumed.

The check is deliberately textual (does the JSON key appear in the Dart file)
rather than a full parse. A stricter check would need a Dart parser in the
Python test suite; this one catches the mistake that actually happens.
"""

from __future__ import annotations

import re

import pytest

from app.models import (
    AnalyzeResponse,
    CoverageResponse,
    GeneReadiness,
    GuidelineProvenance,
    QualityMetrics,
)
from tests.conftest import REPO_ROOT

DART_MODELS = REPO_ROOT / "app/lib/models/analysis.dart"

#: Every model whose JSON the Dart client reads.
SHARED_MODELS = (
    AnalyzeResponse,
    QualityMetrics,
    CoverageResponse,
    GeneReadiness,
    GuidelineProvenance,
)


@pytest.fixture(scope="module")
def dart_source() -> str:
    if not DART_MODELS.exists():  # pragma: no cover — repo layout changed
        pytest.skip(f"Dart models not found at {DART_MODELS}")
    return DART_MODELS.read_text()


@pytest.mark.parametrize("model", SHARED_MODELS, ids=lambda m: m.__name__)
def test_every_backend_field_is_read_by_the_client(model, dart_source: str) -> None:
    """
    Forward direction: a field the backend sends must be a field the client
    reads. This is the direction that breaks in practice, because adding to
    Pydantic is where a change starts.
    """
    missing = [
        name for name in model.model_fields
        if f"'{name}'" not in dart_source and f'"{name}"' not in dart_source
    ]
    assert not missing, (
        f"{model.__name__} sends {missing}, which {DART_MODELS.name} never reads. "
        f"The client will silently render as if the backend omitted them."
    )


def test_the_client_reads_no_coverage_field_the_backend_does_not_send(
    dart_source: str,
) -> None:
    """
    Reverse direction, for the /coverage payload only.

    A client reading a key the backend never sends is a permanently-null field —
    less dangerous than the forward case, but it means dead UI that looks live.
    Scoped to the coverage classes because they are new; the analyze classes
    predate this test and carry Phase 1 keys deliberately.
    """
    known = set()
    for model in (CoverageResponse, GeneReadiness, GuidelineProvenance):
        known |= set(model.model_fields)

    # The Dart toJson maps are the client's declaration of the wire shape.
    block = dart_source[dart_source.index("class GeneReadiness"):]
    block = block[: block.index("class QualityMetrics")]
    keys = set(re.findall(r"'([a-z][a-z0-9_]*)':", block))

    # Keys inherited from the shared GeneCoverage shape, which GeneReadiness
    # converts into rather than receives.
    keys -= set(QualityMetrics.model_fields) | {
        "positions_present", "minimum_percent", "sufficient", "percent",
    }

    unknown = sorted(keys - known)
    assert not unknown, (
        f"{DART_MODELS.name} reads {unknown} on the coverage payload, which no "
        f"backend model sends."
    )


def test_provenance_is_optional_on_the_wire() -> None:
    """
    The client must tolerate a backend that predates provenance. Asserting the
    Pydantic default is what makes the Dart nullability correct rather than
    merely defensive.
    """
    assert QualityMetrics.model_fields["guideline_provenance"].default is None
    assert CoverageResponse.model_fields["guideline_provenance"].default is None
