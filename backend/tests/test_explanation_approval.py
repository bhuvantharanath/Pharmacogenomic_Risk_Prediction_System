"""Phase 3 regressions for approval and semantic-context enforcement."""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.explanation import ExplanationMode, generate_explanation
from app.explanation import approval, static_store
from app.explanation.context import ExplanationContext
from app.models import Phenotype, RiskLabel
from app.retrieval import retrieve_mechanism


def _context(**overrides) -> ExplanationContext:
    values = {
        "drug": "clopidogrel",
        "risk_label": RiskLabel.INEFFECTIVE,
        "phenotype": Phenotype.PM,
        "gene": "CYP2C19",
        "diplotype": "*2/*2",
        "phenotype_label": "Poor Metabolizer",
        "cpic_recommendation": (
            "Avoid clopidogrel if possible. Use prasugrel or ticagrelor at "
            "standard dose if no contraindication."
        ),
        "mechanism": retrieve_mechanism("CYP2C19", "clopidogrel"),
    }
    values.update(overrides)
    return ExplanationContext(**values)


def _approved_manifest(
    stored: static_store.StoredExplanation,
    context: ExplanationContext,
    **overrides,
) -> approval.ApprovalManifest:
    values = {
        "drug": context.drug,
        "gene": context.gene or "",
        "phenotype": context.phenotype.value,
        "status": approval.APPROVED,
        "content_hash": approval.content_hash(stored.explanation),
        "source_hash": approval.stored_source_hash(stored),
        "context_hash": approval.stored_context_hash(stored),
        "review_kind": approval.AUTHOR_REVIEW,
        "adjudicated_by": ("Repository author",),
        "clinical_expert_review_status": approval.NO_EXPERT_REVIEW,
        "reason": "Synthetic approved control.",
    }
    values.update(overrides)
    record = approval.ApprovalRecord(**values)
    return approval.ApprovalManifest(
        records={record.key: record},
        store_sha256="same",
        actual_store_sha256="same",
        version=1,
    )


def _use_manifest(
    monkeypatch: pytest.MonkeyPatch,
    manifest: approval.ApprovalManifest,
) -> None:
    monkeypatch.setattr(approval, "load_manifest", lambda: manifest)


def test_unresolved_shipped_entry_falls_back() -> None:
    """The current PM entry has automated decisions and is not approved."""
    result = generate_explanation(_context(), ExplanationMode.STATIC)
    assert result.generator == "template"
    assert any("approval" in note.lower() for note in result.notes)


def test_same_drug_and_phenotype_with_wrong_gene_context_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The old two-field lookup must not reuse CYP2C19 prose for another gene."""
    context = _context()
    stored = static_store.lookup(context.drug, context.phenotype.value)
    assert stored is not None
    _use_manifest(monkeypatch, _approved_manifest(stored, context))
    result = generate_explanation(
        _context(
            gene="DPYD",
            mechanism=retrieve_mechanism("DPYD", "fluorouracil"),
        ),
        ExplanationMode.STATIC,
    )
    assert result.generator == "template"
    assert any("context" in note.lower() for note in result.notes)


def test_approved_correct_context_entry_serves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    stored = static_store.lookup(context.drug, context.phenotype.value)
    assert stored is not None
    _use_manifest(monkeypatch, _approved_manifest(stored, context))

    result = generate_explanation(context, ExplanationMode.STATIC)

    assert result.generator == "static"
    assert result.provenance_verified is True


@pytest.mark.parametrize("status", [approval.UNRESOLVED, approval.REJECTED])
def test_nonapproved_status_falls_back(
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    context = _context()
    stored = static_store.lookup(context.drug, context.phenotype.value)
    assert stored is not None
    manifest = _approved_manifest(stored, context)
    record = next(iter(manifest.records.values()))
    changed = replace(record, status=status, reason=f"Synthetic {status} control.")
    manifest.records = {changed.key: changed}
    _use_manifest(monkeypatch, manifest)

    result = generate_explanation(context, ExplanationMode.STATIC)

    assert result.generator == "template"
    assert any(status in note.lower() for note in result.notes)


def test_changed_content_hash_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context()
    stored = static_store.lookup(context.drug, context.phenotype.value)
    assert stored is not None
    manifest = _approved_manifest(stored, context, content_hash="0" * 64)
    _use_manifest(monkeypatch, manifest)

    result = generate_explanation(context, ExplanationMode.STATIC)

    assert result.generator == "template"
    assert any("content hash" in note.lower() for note in result.notes)


def test_changed_source_hash_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context()
    stored = static_store.lookup(context.drug, context.phenotype.value)
    assert stored is not None
    manifest = _approved_manifest(stored, context, source_hash="0" * 64)
    _use_manifest(monkeypatch, manifest)

    result = generate_explanation(context, ExplanationMode.STATIC)

    assert result.generator == "template"
    assert any("source binding" in note.lower() for note in result.notes)


def test_incompatible_source_context_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context(cpic_recommendation="A different indication/context.")
    stored = static_store.lookup(context.drug, context.phenotype.value)
    assert stored is not None
    manifest = _approved_manifest(stored, context)
    _use_manifest(monkeypatch, manifest)

    result = generate_explanation(context, ExplanationMode.STATIC)

    assert result.generator == "template"
    assert any("source context" in note.lower() for note in result.notes)


def test_automated_decision_cannot_masquerade_as_human(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    stored = static_store.lookup(context.drug, context.phenotype.value)
    assert stored is not None
    manifest = _approved_manifest(
        stored,
        context,
        adjudicated_by=("automated",),
    )
    _use_manifest(monkeypatch, manifest)

    result = generate_explanation(context, ExplanationMode.STATIC)

    assert result.generator == "template"
    assert any("automated" in note.lower() for note in result.notes)


def test_reviewed_entry_with_changed_phenotype_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    stored = static_store.lookup(context.drug, context.phenotype.value)
    assert stored is not None
    _use_manifest(monkeypatch, _approved_manifest(stored, context))

    result = generate_explanation(
        _context(phenotype=Phenotype.IM), ExplanationMode.STATIC
    )

    assert result.generator == "template"


def test_reviewed_entry_with_different_source_row_text_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    stored = static_store.lookup(context.drug, context.phenotype.value)
    assert stored is not None
    _use_manifest(monkeypatch, _approved_manifest(stored, context))

    result = generate_explanation(
        _context(cpic_recommendation="Different CPIC source row recommendation."),
        ExplanationMode.STATIC,
    )

    assert result.generator == "template"
    assert any("source context" in note.lower() for note in result.notes)


def test_fabricated_expert_review_in_record_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    stored = static_store.lookup(context.drug, context.phenotype.value)
    assert stored is not None
    manifest = _approved_manifest(
        stored, context, clinical_expert_review_status="approved"
    )
    _use_manifest(monkeypatch, manifest)

    result = generate_explanation(context, ExplanationMode.STATIC)

    assert result.generator == "template"
    assert any("clinical-expert" in note.lower() for note in result.notes)
