"""
Retrieval, slot filling, mode dispatch, and the corpus provenance rule.

Everything here runs with no API key. The live-mode test skips itself when
GEMINI_API_KEY is absent, which is the normal case in CI.
"""

from __future__ import annotations

import os
import re

import pytest

from app.explanation import (
    ExplanationMode,
    generate_explanation,
    generator_template,
    static_store,
)
from app.explanation.context import (
    ALLOWED_SLOTS,
    Explanation,
    ExplanationContext,
    unknown_slots,
)
from app.explanation.guard import check
from app.models import DetectedVariant, Phenotype, RiskLabel
from app.retrieval import (
    CORPUS_DIR,
    all_documents,
    canonical_drug,
    known_genes,
    retrieve_mechanism,
)

TARGET_PAIRS = {
    ("CYP2C19", "clopidogrel"),
    ("CYP2C9", "warfarin"),
    ("CYP2D6", "codeine"),
    ("DPYD", "fluorouracil"),
    ("SLCO1B1", "simvastatin"),
    ("TPMT", "azathioprine"),
}


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
        cpic_recommendation="Avoid clopidogrel if possible.",
        mechanism=retrieve_mechanism("CYP2C19", "clopidogrel"),
    )
    defaults.update(overrides)
    return ExplanationContext(**defaults)


class TestCorpus:
    def test_all_six_pairs_are_present(self) -> None:
        found = {(d.gene, d.drug) for d in all_documents()}
        assert found == TARGET_PAIRS

    def test_every_document_has_provenance(self) -> None:
        for document in all_documents():
            assert document.source_guideline, f"{document.drug} has no guideline"
            assert document.source_url.startswith("http"), document.drug
            assert document.primary_citation, f"{document.drug} has no citation"
            assert document.retrieved, f"{document.drug} has no retrieval date"

    def test_no_dosing_content_in_the_corpus(self) -> None:
        """
        The provenance rule, enforced.

        Mechanism lives in the corpus; dosing lives in PharmCAT's CPIC output.
        Two sources stating a dose is how a system contradicts itself, and a
        contradiction in a clinical number is the worst kind.
        """
        dose_like = re.compile(
            r"\d+\s*(?:mg|mcg|µg|g/m2|mg/kg|units?)\b|\breduce (?:the )?dose by\b",
            re.IGNORECASE,
        )
        for path in sorted(CORPUS_DIR.glob("*.md")):
            body = path.read_text()
            # Drop front matter; `contains_dosing: false` would self-match.
            body = re.sub(r"\A---.*?\n---\s*\n", "", body, flags=re.DOTALL)
            matches = dose_like.findall(body)
            assert not matches, f"{path.name} contains dosing language: {matches}"

    def test_every_document_declares_no_dosing(self) -> None:
        for document in all_documents():
            assert document.contains_dosing is False, document.drug

    def test_corpus_is_flagged_unreviewed(self) -> None:
        """Until a faculty guide signs off, this must be visible."""
        for document in all_documents():
            assert document.reviewed_by is None or isinstance(document.reviewed_by, str)


class TestRetrieval:
    def test_exact_pair_lookup(self) -> None:
        document = retrieve_mechanism("CYP2C19", "clopidogrel")
        assert document is not None
        assert document.gene == "CYP2C19"

    def test_lookup_is_case_insensitive(self) -> None:
        assert retrieve_mechanism("cyp2c19", "CLOPIDOGREL") is not None

    def test_falls_back_to_drug_when_gene_mismatches(self) -> None:
        """azathioprine may be attributed to NUDT15 rather than TPMT."""
        document = retrieve_mechanism("NUDT15", "azathioprine")
        assert document is not None
        assert document.gene == "TPMT"

    def test_falls_back_when_gene_is_unknown(self) -> None:
        assert retrieve_mechanism(None, "clopidogrel") is not None

    @pytest.mark.parametrize(
        "alias,expected",
        [
            ("5-FU", "fluorouracil"),
            ("5-fluorouracil", "fluorouracil"),
            ("Plavix", "clopidogrel"),
            ("plavix", "clopidogrel"),
            ("Coumadin", "warfarin"),
            ("thiopurine", "azathioprine"),
        ],
    )
    def test_alias_resolution(self, alias: str, expected: str) -> None:
        assert canonical_drug(alias) == expected

    def test_alias_retrieval(self) -> None:
        document = retrieve_mechanism(None, "5-FU")
        assert document is not None and document.drug == "fluorouracil"

    def test_miss_returns_none(self) -> None:
        assert retrieve_mechanism("XYZ", "aspirin") is None
        assert canonical_drug("aspirin") is None

    def test_known_genes_covers_the_corpus(self) -> None:
        assert {"CYP2C19", "DPYD", "TPMT", "SLCO1B1", "CYP2C9", "CYP2D6"} <= known_genes()

    def test_snippet_excludes_front_matter(self) -> None:
        """The model must not see (and copy) citation metadata."""
        snippet = retrieve_mechanism("CYP2C19", "clopidogrel").snippet()
        assert "source_url:" not in snippet
        assert "retrieved:" not in snippet


class TestSlotFilling:
    def test_all_slots_are_substituted(self) -> None:
        context = make_context()
        filled = Explanation(
            summary="{drug} {gene} {diplotype} {phenotype} {risk_label}",
            mechanism="{detected_variants}",
            variant_rationale="",
            patient_friendly="",
        ).fill_slots(context)

        assert "{" not in filled.summary
        assert filled.summary == (
            "clopidogrel CYP2C19 *2/*2 Poor Metabolizer Ineffective"
        )
        assert "rs4244285" in filled.mechanism

    def test_unknown_slot_is_left_visible(self) -> None:
        """A stray '{foo}' is an obvious bug report; blanking it hides one."""
        filled = Explanation("{nope}", "", "", "").fill_slots(make_context())
        assert filled.summary == "{nope}"

    def test_no_variants_reads_correctly(self) -> None:
        context = make_context(detected_variants=[])
        assert "no non-reference variants" in context.variants_display()

    def test_multiple_variants_are_listed(self) -> None:
        context = make_context(
            detected_variants=[
                DetectedVariant(rsid="rs1", gene="G", genotype="A/A", star_allele=None, function="f"),
                DetectedVariant(rsid="rs2", gene="G", genotype="C/T", star_allele=None, function="f"),
            ]
        )
        display = context.variants_display()
        assert "rs1" in display and "rs2" in display and " and " in display

    def test_structural_variant_without_rsid(self) -> None:
        context = make_context(
            detected_variants=[
                DetectedVariant(rsid=None, gene="CYP2D6", genotype="N/A", star_allele="*2xN", function="f")
            ]
        )
        assert "structural variant" in context.variants_display()

    def test_allowed_slots_are_recognised(self) -> None:
        text = " ".join(f"{{{name}}}" for name in ALLOWED_SLOTS)
        assert unknown_slots(text) == set()


class TestTemplateGenerator:
    def test_always_produces_four_populated_fields(self) -> None:
        for phenotype in Phenotype:
            context = make_context(phenotype=phenotype)
            explanation = generator_template.generate(context)
            for name, value in explanation.fields().items():
                assert value.strip(), f"{phenotype.value}: {name} is empty"

    def test_output_passes_the_guard(self) -> None:
        """The fallback path cannot itself need a fallback."""
        for phenotype in Phenotype:
            for label in RiskLabel:
                context = make_context(phenotype=phenotype, risk_label=label)
                report = check(
                    generator_template.generate(context), context, generator="template"
                )
                assert report.passed, (
                    f"{phenotype.value}/{label.value}: "
                    f"{[str(v) for v in report.violations]}"
                )

    def test_works_without_a_mechanism_document(self) -> None:
        context = make_context(drug="aspirin", gene=None, mechanism=None)
        explanation = generator_template.generate(context)
        assert "No mechanism background" in explanation.mechanism

    def test_uncalled_gene_does_not_imply_a_phenotype(self) -> None:
        """Absence of a result must never read as a normal result."""
        context = make_context(
            drug="codeine", gene="CYP2D6", diplotype=None,
            phenotype=Phenotype.UNKNOWN, risk_label=RiskLabel.UNKNOWN,
            phenotype_label="", mechanism=retrieve_mechanism("CYP2D6", "codeine"),
        )
        filled = generator_template.generate(context).fill_slots(context)
        assert "No genotype was called" in filled.variant_rationale
        assert "normal" not in filled.patient_friendly.lower()


class TestStaticStore:
    def test_store_loads(self) -> None:
        store = static_store.load_store()
        assert store.load_error is None, store.load_error
        assert len(store) > 0

    def test_flagship_case_is_present(self) -> None:
        entry = static_store.lookup("clopidogrel", "PM")
        assert entry is not None
        assert entry.gene == "CYP2C19"
        assert entry.guard_passed

    def test_entries_use_slots_not_literals(self) -> None:
        """
        Stored prose must not bake in one patient's values.

        Reviewed text is reused across patients, so a literal diplotype here
        would be served to everyone who shares the phenotype.
        """
        for (drug, phenotype), entry in static_store.load_store().entries.items():
            if phenotype == "Unknown":
                continue  # nothing was called, so there is nothing to slot
            blob = " ".join(entry.explanation.fields().values())
            assert "{diplotype}" in blob, f"{drug}/{phenotype} has no diplotype slot"

    def test_provenance_and_reading_are_tracked_separately(self) -> None:
        """
        Two different states, never one number.

        Collapsing them is what the old `reviewed_by` field did, and it made the
        weak signal (a human glanced at it) look like the strong one.
        """
        store = static_store.load_store()
        # Provenance is machine-checked and currently complete.
        assert store.unverified_count == 0, "verify_provenance.py --write not run?"
        # Nobody has read them. That is a real and separate gap.
        assert store.unread_count == len(store)

    def test_no_entry_claims_a_clinical_expert_review(self) -> None:
        """
        The invariant that must hold forever on this project.

        There is no qualified clinical reviewer. A populated
        `clinical_expert_review` could only be a mistake or a fabrication, and
        either would be the most consequential untruth in the codebase.
        """
        store = static_store.load_store()
        for entry in store.entries.values():
            assert entry.review.clinical_expert_review is None, entry.drug
            assert entry.review.clinical_expert_review_status == "NOT_OBTAINED"
            assert not entry.review.has_clinical_expert_review

    def test_missing_file_degrades(self, tmp_path) -> None:
        store = static_store.load_store(tmp_path / "nope.json")
        assert store.load_error is not None
        assert len(store) == 0

    def test_corrupt_file_degrades(self, tmp_path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{not json")
        store = static_store.load_store(path)
        assert store.load_error is not None


class TestModeDispatch:
    def test_default_mode_is_static(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("EXPLANATION_MODE", raising=False)
        assert ExplanationMode.from_env() is ExplanationMode.STATIC

    def test_unrecognised_mode_falls_back_to_static(self) -> None:
        """A typo in a deploy env var should not take the service down."""
        assert ExplanationMode.from_env("banana") is ExplanationMode.STATIC

    @pytest.mark.parametrize("value,expected", [
        ("live", ExplanationMode.LIVE),
        ("TEMPLATE", ExplanationMode.TEMPLATE),
        ("  static  ", ExplanationMode.STATIC),
    ])
    def test_mode_parsing(self, value: str, expected: ExplanationMode) -> None:
        assert ExplanationMode.from_env(value) is expected

    def test_static_hits_the_store(self) -> None:
        result = generate_explanation(make_context(), ExplanationMode.STATIC)
        assert result.generator == "static"
        assert "mode=static" in result.provenance

    def test_static_miss_degrades_to_template(self) -> None:
        """A lookup miss must never be an error."""
        context = make_context(drug="aspirin", gene=None, mechanism=None)
        result = generate_explanation(context, ExplanationMode.STATIC)
        assert result.generator == "template"
        assert any("No pre-generated explanation" in n for n in result.notes)

    def test_template_mode_never_touches_the_store(self) -> None:
        result = generate_explanation(make_context(), ExplanationMode.TEMPLATE)
        assert result.generator == "template"

    def test_every_mode_returns_populated_fields(self) -> None:
        for mode in ExplanationMode:
            if mode is ExplanationMode.LIVE and not os.environ.get("GEMINI_API_KEY"):
                continue
            result = generate_explanation(make_context(), mode)
            for name, value in result.explanation.fields().items():
                assert value.strip(), f"{mode.value}: {name} empty"

    def test_no_slots_survive_dispatch(self) -> None:
        for mode in (ExplanationMode.STATIC, ExplanationMode.TEMPLATE):
            result = generate_explanation(make_context(), mode)
            for name, value in result.explanation.fields().items():
                assert not re.search(r"\{[a-z_]+\}", value), f"{mode.value}/{name}"


class TestLiveModeWithMockedModel:
    """
    Live-mode control flow, without spending quota or needing a key.

    The model is mocked so retry, fallback and violation logging can be asserted
    deterministically. `TestLiveMode` below exercises the real API when a key is
    available.
    """

    @staticmethod
    def _result(explanation: Explanation):
        from app.explanation.generator_llm import LlmResult

        return LlmResult(explanation=explanation, model="mock-model", raw_text="")

    FAITHFUL = Explanation(
        summary="{gene} {diplotype} is {phenotype}.",
        mechanism="CYP2C19 activates clopidogrel into its active metabolite.",
        variant_rationale="Found {detected_variants}.",
        patient_friendly="Speak with your doctor.",
    )
    HALLUCINATED = Explanation(
        summary="ok",
        mechanism="Reduce the dose to 75 mg daily.",
        variant_rationale="ok",
        patient_friendly="ok",
    )

    def test_faithful_output_is_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.explanation import generator_llm

        monkeypatch.setenv("GEMINI_API_KEY", "mock")
        monkeypatch.setattr(
            generator_llm, "generate", lambda *a, **k: self._result(self.FAITHFUL)
        )
        result = generate_explanation(make_context(), ExplanationMode.LIVE)

        assert result.generator == "llm:mock-model"
        assert result.guard is not None and result.guard.passed
        assert result.explanation.summary.startswith("CYP2C19 *2/*2")

    def test_persistent_hallucination_falls_back_to_template(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        """The invented dose must never reach the response."""
        from app.explanation import generator_llm, guard as guard_module

        monkeypatch.setenv("GEMINI_API_KEY", "mock")
        monkeypatch.setattr(guard_module, "DEFAULT_LOG_PATH", tmp_path / "g.jsonl")
        monkeypatch.setattr(
            generator_llm, "generate", lambda *a, **k: self._result(self.HALLUCINATED)
        )
        result = generate_explanation(make_context(), ExplanationMode.LIVE)

        assert result.generator == "template"
        assert result.guard is not None and not result.guard.passed
        assert result.guard.attempts == 2
        assert "75 mg" not in " ".join(result.explanation.fields().values())

        # Both failed attempts are on record for the hallucination-rate report.
        records = guard_module.read_violation_log(tmp_path / "g.jsonl")
        assert len(records) == 2
        assert records[0]["violations"][0]["kind"] == "dose"

    def test_retry_recovers_from_a_transient_failure(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        from app.explanation import generator_llm, guard as guard_module

        monkeypatch.setenv("GEMINI_API_KEY", "mock")
        monkeypatch.setattr(guard_module, "DEFAULT_LOG_PATH", tmp_path / "g.jsonl")
        outputs = iter([self.HALLUCINATED, self.FAITHFUL])
        monkeypatch.setattr(
            generator_llm, "generate", lambda *a, **k: self._result(next(outputs))
        )
        result = generate_explanation(make_context(), ExplanationMode.LIVE)

        assert result.generator == "llm:mock-model"
        assert result.guard.passed and result.guard.attempts == 2

    def test_sdk_error_degrades_without_raising(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.explanation import generator_llm

        monkeypatch.setenv("GEMINI_API_KEY", "mock")

        def boom(*args, **kwargs):
            raise generator_llm.LlmUnavailableError("network is down")

        monkeypatch.setattr(generator_llm, "generate", boom)
        result = generate_explanation(make_context(), ExplanationMode.LIVE)

        assert result.generator in ("static", "template")
        for value in result.explanation.fields().values():
            assert value.strip()


class TestLiveMode:
    """Skipped without a key — which is the normal, deployed condition."""

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set; live mode is optional by design",
    )
    def test_live_generation_passes_the_guard(self) -> None:
        context = make_context()
        result = generate_explanation(context, ExplanationMode.LIVE)

        assert result.guard is not None
        assert result.guard.passed, [str(v) for v in result.guard.violations]
        assert result.generator.startswith("llm:")
        for name, value in result.explanation.fields().items():
            assert value.strip(), f"{name} is empty"

    def test_live_without_a_key_falls_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The important half: no key must degrade, not fail."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        result = generate_explanation(make_context(), ExplanationMode.LIVE)
        assert result.generator in ("static", "template")
        for value in result.explanation.fields().values():
            assert value.strip()
