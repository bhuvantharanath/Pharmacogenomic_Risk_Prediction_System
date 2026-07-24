"""
No patient genomic data ever reaches a third-party LLM provider.

This is a real architectural property, not a policy promise, and it holds at both
times a provider could possibly be called:

  BUILD TIME — pregeneration sends the model a *generic* case: a (gene, phenotype,
      drug) triple plus the published CPIC recommendation text. Patient-specific
      fields are placeholders (`{diplotype}`) or empty, because one reviewed
      sentence is reused for every patient sharing a phenotype. There is no
      patient at build time at all.

  RUN TIME — the deployed service runs in static mode: it looks the pre-generated
      explanation up by (drug, phenotype) and fills slots locally. It imports no
      provider and opens no socket. A real patient's diplotype and variants are
      substituted on the server, never sent anywhere.

So the only text that ever leaves for a model is text that already exists in a
public CPIC guideline. These tests pin that, because it is the property that lets
the system handle genomes without becoming a way to leak them.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _pregen():
    spec = importlib.util.spec_from_file_location(
        "pregenerate_explanations", SCRIPTS / "pregenerate_explanations.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["pregenerate_explanations"] = module
    spec.loader.exec_module(module)
    return module


#: Fields in the prompt payload that would carry patient-derived genomic data if
#: they were ever populated with real values at build time.
_PATIENT_FIELDS = ("diplotype", "activity_score", "detected_variants")

#: A real diplotype looks like *2/*2; a placeholder looks like {diplotype}. This
#: separates "we sent a genotype" from "we sent a slot to be filled later".
_PLACEHOLDER_PREFIX = "{"


class TestBuildTimePayloadCarriesNoPatientData:
    """
    Every case pregeneration would send is a generic one.

    Checked against the *actual* prompt payload the generator builds, for every
    reachable case, so this cannot drift from what is really transmitted.
    """

    @pytest.fixture(scope="class")
    def pregen(self):
        return _pregen()

    def test_no_case_sends_a_concrete_diplotype(self, pregen) -> None:
        offenders = []
        for case in pregen.load_reachable_cases():
            context, _ = pregen.build_context(case)
            diplotype = context.prompt_payload().get("diplotype")
            # Allowed: a placeholder string, or None (nothing called). Forbidden:
            # a real diplotype like *2/*2.
            if diplotype and not str(diplotype).startswith(_PLACEHOLDER_PREFIX):
                offenders.append(f"{case.key}: diplotype={diplotype!r}")
        assert not offenders, f"concrete diplotypes would be sent to the model: {offenders}"

    def test_no_case_sends_detected_variants(self, pregen) -> None:
        """The variant list is where rsIDs and genotypes would live. It is empty."""
        offenders = []
        for case in pregen.load_reachable_cases():
            context, _ = pregen.build_context(case)
            variants = context.prompt_payload().get("detected_variants")
            if variants:
                offenders.append(f"{case.key}: {len(variants)} variant(s)")
        assert not offenders, f"detected variants would be sent to the model: {offenders}"

    def test_no_case_sends_an_activity_score(self, pregen) -> None:
        for case in pregen.load_reachable_cases():
            context, _ = pregen.build_context(case)
            assert context.prompt_payload().get("activity_score") is None, case.key

    def test_the_payload_is_only_generic_and_public_fields(self, pregen) -> None:
        """
        Whatever the payload does contain must be a generic identifier or public
        CPIC text — never anything that identifies or derives from a person.

        A rendered payload that contained a real star allele, an rsID, or a
        genotype string would be a leak; the placeholders that stand in for them
        are not.
        """
        import re

        star_or_rsid = re.compile(r"\brs\d{3,}\b|\*\d+\s*/\s*\*\d+")
        for case in pregen.load_reachable_cases():
            context, _ = pregen.build_context(case)
            payload = context.prompt_payload()
            for field in _PATIENT_FIELDS:
                rendered = json.dumps(payload.get(field))
                assert not star_or_rsid.search(rendered), (
                    f"{case.key}: patient field {field!r} carries genomic data: {rendered}"
                )


class TestRunTimeSendsNothingToAnyProvider:
    """
    The deployed path imports no provider and makes no call.

    The strong version of the privacy claim: at run time there is nothing to
    leak because nothing is transmitted. Verified by driving a real request with
    the LLM generator poisoned to raise if touched.
    """

    def test_static_mode_never_calls_a_provider(self, monkeypatch) -> None:
        from app.explanation import ExplanationMode, generate_explanation, generator_llm
        from app.explanation.providers import get_provider

        def forbidden(*args, **kwargs):
            raise AssertionError(
                "static mode reached a provider — patient data path must send nothing"
            )

        # Poison both the high-level generate and every provider's generate.
        monkeypatch.setattr(generator_llm, "generate", forbidden)
        for name in ("nvidia", "gemini", "ollama"):
            monkeypatch.setattr(get_provider(name), "generate", forbidden)

        # A real reachable-case context, built the same way pregeneration does.
        context, _ = _pregen().build_context(_pregen().load_reachable_cases()[0])
        result = generate_explanation(context, ExplanationMode.STATIC)
        for value in result.explanation.fields().values():
            assert value.strip()

    def test_deployed_app_does_not_import_a_provider_at_module_load(self) -> None:
        """
        `providers/` is imported lazily by the live path, never at app import.

        A top-level `import providers` in a request-handling module would mean
        the deployed image carried the client SDKs and could, in principle,
        call out. The live generator imports them inside the function instead.
        """
        main_source = (REPO_ROOT / "backend" / "app" / "main.py").read_text()
        assert "import providers" not in main_source
        assert "from .explanation.providers" not in main_source
