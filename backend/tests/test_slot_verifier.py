"""
Runtime slot verification — closing the build-time guard's blind spot.

THE GAP
    In static mode the faithfulness guard runs at PRE-GENERATION time, over
    prose that still contains `{diplotype}` and `{detected_variants}`. Those
    holes are filled per request, from the live PharmCAT call, long after the
    stored verdict was recorded. So the guard's verdict — genuinely earned —
    says nothing about the patient-specific values in the sentence a user
    actually reads.

    A context-assembly bug (stale cache, wrong object threaded through, an
    off-by-one across a multi-drug request) would produce a fluent, reviewed,
    guard-passed sentence stating someone else's genotype. Nothing checked.

WHAT THESE TESTS PIN
    That the injected values are cross-checked against the response's own
    `pharmacogenomic_profile` — the same object the client renders in the card
    directly above the explanation — and that a mismatch demotes the result to
    the deterministic template rather than being served.
"""

from __future__ import annotations

import io
import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.explanation import ExplanationMode, generate_explanation
from app.explanation.context import Explanation, ExplanationContext
from app.explanation.slot_verifier import verify
from app.models import (
    DetectedVariant,
    PharmacogenomicProfile,
    Phenotype,
    RiskLabel,
)
from app.pharmcat_models import PharmcatReport


def make_context(**overrides) -> ExplanationContext:
    defaults = dict(
        drug="clopidogrel",
        risk_label=RiskLabel.INEFFECTIVE,
        phenotype=Phenotype.PM,
        gene="CYP2C19",
        diplotype="*2/*2",
        phenotype_label="Poor Metabolizer",
        detected_variants=[
            DetectedVariant(
                rsid="rs4244285",
                gene="CYP2C19",
                genotype="A/A",
                star_allele=None,
                function="No function",
            )
        ],
    )
    defaults.update(overrides)
    return ExplanationContext(**defaults)


def make_profile(**overrides) -> PharmacogenomicProfile:
    defaults = dict(
        primary_gene="CYP2C19",
        diplotype="*2/*2",
        phenotype=Phenotype.PM,
        activity_score=None,
        detected_variants=[
            DetectedVariant(
                rsid="rs4244285",
                gene="CYP2C19",
                genotype="A/A",
                star_allele=None,
                function="No function",
            )
        ],
    )
    defaults.update(overrides)
    return PharmacogenomicProfile(**defaults)


UNFILLED = Explanation(
    summary="{drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.",
    mechanism="CYP2C19 activates clopidogrel.",
    variant_rationale="Positions found: {detected_variants}.",
    patient_friendly="Speak with your doctor.",
)


class TestVerifierUnit:
    def test_matching_values_pass(self) -> None:
        context = make_context()
        filled = UNFILLED.fill_slots(context)
        result = verify(filled, UNFILLED, context, make_profile())

        assert result.passed, result.mismatches
        assert "diplotype" in result.verified_slots
        assert "detected_variants" in result.verified_slots

    def test_wrong_diplotype_is_caught(self) -> None:
        """The headline case: the sentence says *2/*2, the card says *1/*1."""
        context = make_context(diplotype="*2/*2")
        filled = UNFILLED.fill_slots(context)

        result = verify(filled, UNFILLED, context, make_profile(diplotype="*1/*1"))

        assert not result.passed
        assert any("diplotype" in m for m in result.mismatches)
        assert "*1/*1" in result.mismatches[0]

    def test_wrong_gene_is_caught(self) -> None:
        context = make_context(gene="CYP2C19")
        filled = UNFILLED.fill_slots(context)
        result = verify(filled, UNFILLED, context, make_profile(primary_gene="DPYD"))
        assert not result.passed
        assert any("gene" in m for m in result.mismatches)

    def test_wrong_variants_are_caught(self) -> None:
        context = make_context()
        filled = UNFILLED.fill_slots(context)
        result = verify(
            filled,
            UNFILLED,
            context,
            make_profile(
                detected_variants=[
                    DetectedVariant(
                        rsid="rs9999999",
                        gene="CYP2C19",
                        genotype="C/T",
                        star_allele=None,
                        function="No function",
                    )
                ]
            ),
        )
        assert not result.passed
        assert any("detected_variants" in m for m in result.mismatches)

    def test_prose_without_slots_verifies_nothing_and_says_so(self) -> None:
        """A pass on slot-free prose must not read as 'everything checked'."""
        context = make_context()
        slotless = Explanation("No slots here.", "Nor here.", "Or here.", "Plain.")
        result = verify(slotless, slotless, context, make_profile())

        assert result.passed
        assert result.verified_slots == set()
        assert "none present" in result.summary

    def test_uncalled_gene_profile_is_handled(self) -> None:
        """CYP2D6 returns Unknown/Unknown; that must verify, not explode."""
        context = make_context(
            drug="codeine",
            gene=None,
            diplotype=None,
            phenotype=Phenotype.UNKNOWN,
            phenotype_label="",
            detected_variants=[],
            risk_label=RiskLabel.UNKNOWN,
        )
        filled = UNFILLED.fill_slots(context)
        result = verify(
            filled,
            UNFILLED,
            context,
            make_profile(
                primary_gene="Unknown",
                diplotype="Unknown",
                phenotype=Phenotype.UNKNOWN,
                detected_variants=[],
            ),
        )
        assert result.passed, result.mismatches


class TestDispatcherFallsBackOnMismatch:
    """A mismatched explanation must never be served."""

    def test_static_mismatch_falls_back_to_template(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        context = make_context()
        # The profile disagrees with the context the prose was filled from.
        lying_profile = make_profile(diplotype="*17/*17")

        result = generate_explanation(
            context, ExplanationMode.STATIC, profile=lying_profile
        )

        assert result.generator == "template", (
            "a pre-generated explanation whose injected diplotype contradicts "
            "the reported profile was served instead of being demoted"
        )
        assert any("slot verification" in n for n in result.notes)

    def test_matching_profile_keeps_the_static_explanation(self) -> None:
        result = generate_explanation(
            make_context(), ExplanationMode.STATIC, profile=make_profile()
        )
        assert result.generator == "static"
        assert result.slots is not None and result.slots.passed
        assert "slots=verified" in result.provenance

    def test_omitting_the_profile_skips_verification(self) -> None:
        """Optional by design, so the layer stays testable in isolation."""
        result = generate_explanation(make_context(), ExplanationMode.STATIC)
        assert result.slots is None
        assert "slots=" not in result.provenance

    def test_template_mismatch_is_reported_but_still_served(self) -> None:
        """
        The template is the floor — there is nothing safer to fall back to, so
        a mismatch is surfaced loudly rather than leaving the user with nothing.
        """
        result = generate_explanation(
            make_context(),
            ExplanationMode.TEMPLATE,
            profile=make_profile(diplotype="*17/*17"),
        )
        assert result.generator == "template"
        assert result.slots is not None and not result.slots.passed
        assert any("disagree" in n for n in result.notes)
        # Still a complete explanation.
        for value in result.explanation.fields().values():
            assert value.strip()


class TestThroughTheApi:
    @pytest.fixture
    def client(self, monkeypatch: pytest.MonkeyPatch, cyp2c19_pm_report: PharmcatReport):
        async def fake_run_pharmcat(vcf_text: str, *, sample_hint: str = "sample"):
            return cyp2c19_pm_report

        monkeypatch.setattr(main, "run_pharmcat", fake_run_pharmcat)
        return TestClient(main.app)

    def _post(self, client: TestClient, vcf: bytes, drugs: str):
        return client.post(
            "/analyze",
            files={"file": ("t.vcf", io.BytesIO(vcf), "text/plain")},
            data={"drugs": drugs},
        )

    def test_provenance_reports_slot_verification(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        body = self._post(client, valid_vcf_bytes, "clopidogrel").json()
        provenance = [
            w for w in body["quality_metrics"]["warnings"] if w.startswith("explanation mode=")
        ]
        assert provenance
        assert any("slots=verified" in p for p in provenance), provenance

    def test_sentence_and_card_always_agree(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        """
        The property this whole mechanism exists to guarantee: whatever
        diplotype the card shows, the explanation states the same one.
        """
        body = self._post(
            client, valid_vcf_bytes, "clopidogrel,fluorouracil,codeine"
        ).json()

        for analysis in body["analyses"]:
            diplotype = analysis["pharmacogenomic_profile"]["diplotype"]
            summary = analysis["llm_generated_explanation"]["summary"]
            if diplotype != "Unknown" and "{" not in summary:
                assert diplotype in summary, (
                    f"{analysis['drug']}: card shows {diplotype!r} but the "
                    f"explanation says {summary!r}"
                )
