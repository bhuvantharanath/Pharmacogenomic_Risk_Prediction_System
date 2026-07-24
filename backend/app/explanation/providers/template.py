"""
Template provider — the deterministic, no-network fallback, as a provider.

This is the generator that composes explanations from the CPIC context with no
model at all. It already exists as `generator_template`; wrapping it in the
provider interface means "no LLM available" and "LLM explicitly disabled" are
the same code path (`LLM_PROVIDER=template`), and the benchmark can include the
template as an honest baseline to measure the models against.

It never makes a network call and never needs a key, so it is always configured
and can never raise a provider error.
"""

from __future__ import annotations

import json

from pydantic import BaseModel

from .base import Provider, ProviderResult


class TemplateProvider(Provider):
    name = "template"

    def is_configured(self) -> bool:
        return True

    def default_model(self) -> str:
        return "deterministic-template"

    def generate(
        self,
        *,
        prompt: str,
        system: str,
        schema: type[BaseModel],
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 0,
    ) -> ProviderResult:
        # The template generator works from the structured context, not the
        # rendered prompt string, so it is invoked one layer up (generator_llm
        # holds the context). This method exists to satisfy the interface and to
        # make the misuse obvious if something calls it directly.
        raise NotImplementedError(
            "TemplateProvider is handled specially by generator_llm, which has "
            "the ExplanationContext the deterministic generator needs. It is not "
            "driven through the text-prompt interface."
        )

    @staticmethod
    def as_json(explanation) -> str:
        """Serialise a template Explanation to the JSON the schema expects."""
        return json.dumps(explanation.fields(), ensure_ascii=False)
