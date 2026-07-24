"""
The provider abstraction — selection, error normalisation, JSON recovery, and
the guarantee that a quota wall degrades to the template rather than a 500.

None of these tests touch a network. The OpenAI-compatible providers are driven
with a fake client so every error path can be exercised deterministically, which
is the only way to prove that a 402 becomes `QuotaExhausted` without waiting for
a real account to run out of credits.
"""

from __future__ import annotations

import os
import types

import pytest
from pydantic import BaseModel

from app.explanation.providers import (
    InvalidResponse,
    LlmUnavailableError,
    ModelUnavailable,
    QuotaExhausted,
    RateLimited,
    get_provider,
    resolve_model,
    resolve_provider_name,
)
from app.explanation.providers.json_output import (
    extract_json_text,
    parse_into,
    strip_think,
)


class _Schema(BaseModel):
    summary: str
    mechanism: str
    variant_rationale: str
    patient_friendly: str


# --------------------------------------------------------------------------- #
# Selection
# --------------------------------------------------------------------------- #


class TestSelection:
    def test_default_is_gemini_for_backward_compatibility(self, monkeypatch) -> None:
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        assert resolve_provider_name() == "gemini"

    def test_env_selects_the_provider(self, monkeypatch) -> None:
        monkeypatch.setenv("LLM_PROVIDER", "nvidia")
        assert resolve_provider_name() == "nvidia"

    def test_explicit_argument_wins_over_env(self, monkeypatch) -> None:
        monkeypatch.setenv("LLM_PROVIDER", "nvidia")
        assert resolve_provider_name("ollama") == "ollama"

    def test_unknown_provider_is_rejected(self) -> None:
        with pytest.raises(ModelUnavailable):
            resolve_provider_name("does-not-exist")

    def test_model_precedence_explicit_over_env_over_default(self, monkeypatch) -> None:
        provider = get_provider("gemini")
        monkeypatch.setenv("LLM_MODEL", "from-env")
        assert resolve_model(provider, "explicit") == "explicit"
        assert resolve_model(provider) == "from-env"
        monkeypatch.delenv("LLM_MODEL", raising=False)
        assert resolve_model(provider) == provider.default_model()

    def test_every_typed_error_is_an_llm_unavailable_error(self) -> None:
        # So existing `except LlmUnavailableError` catches keep working.
        for err in (QuotaExhausted, RateLimited, ModelUnavailable, InvalidResponse):
            assert issubclass(err, LlmUnavailableError)


# --------------------------------------------------------------------------- #
# JSON recovery
# --------------------------------------------------------------------------- #


class TestJsonRecovery:
    def test_strip_think_removes_a_closed_reasoning_block(self) -> None:
        assert strip_think("<think>deliberating</think>{\"a\": 1}") == '{"a": 1}'

    def test_strip_think_handles_a_truncated_open_block(self) -> None:
        # A reasoning model that ran out of tokens mid-thought.
        assert strip_think('{"a": 1}\n<think>still thinking...') == '{"a": 1}'

    def test_extract_unwraps_a_json_fence(self) -> None:
        text = 'Here you go:\n```json\n{"a": 1}\n```\nHope that helps!'
        assert extract_json_text(text) == '{"a": 1}'

    def test_extract_finds_a_balanced_object_amid_prose(self) -> None:
        text = 'Sure. {"a": {"b": 2}} — let me know if you need more.'
        assert extract_json_text(text) == '{"a": {"b": 2}}'

    def test_extract_ignores_braces_inside_strings(self) -> None:
        text = '{"note": "a } brace in text"}'
        assert extract_json_text(text) == text

    def test_parse_into_validates_the_schema(self) -> None:
        payload = (
            '{"summary": "s", "mechanism": "m", '
            '"variant_rationale": "v", "patient_friendly": "p"}'
        )
        result = parse_into(_Schema, payload)
        assert result.summary == "s"

    def test_parse_into_reports_missing_fields_without_the_key(self, monkeypatch) -> None:
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-secret-value-1234567890")
        with pytest.raises(ValueError) as exc:
            parse_into(_Schema, '{"summary": "s"}')
        assert "mechanism" in str(exc.value)
        assert "nvapi-secret-value-1234567890" not in str(exc.value)

    def test_parse_into_rejects_non_json(self) -> None:
        with pytest.raises(ValueError, match="no JSON object"):
            parse_into(_Schema, "I cannot help with that.")

    def test_reasoning_model_output_is_recovered(self) -> None:
        """The whole point: a think-block then a fenced object still parses."""
        raw = (
            "<think>The user wants four fields. Let me be faithful.</think>\n"
            '```json\n{"summary":"s","mechanism":"m",'
            '"variant_rationale":"v","patient_friendly":"p"}\n```'
        )
        assert parse_into(_Schema, raw).mechanism == "m"


# --------------------------------------------------------------------------- #
# Error normalisation (OpenAI-compatible providers)
# --------------------------------------------------------------------------- #


class _FakeAPIError(Exception):
    """Mimics openai.APIStatusError enough for the normaliser."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.response = types.SimpleNamespace(headers={})


def _nvidia_raising(exc: Exception):
    """An NVIDIA provider whose underlying client always raises `exc`."""
    provider = get_provider("nvidia")

    class _Client:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(**kwargs):
                    raise exc

    provider._client = lambda: _Client()  # type: ignore[method-assign]
    return provider


class TestErrorNormalisation:
    @pytest.fixture(autouse=True)
    def _key(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test-key-abcdefghijklmnop")

    def test_402_becomes_quota_exhausted(self) -> None:
        provider = _nvidia_raising(_FakeAPIError(402, "payment required"))
        with pytest.raises(QuotaExhausted):
            provider.generate(prompt="p", system="s", schema=_Schema, model="m")

    def test_429_with_credit_language_is_quota_exhausted(self) -> None:
        provider = _nvidia_raising(_FakeAPIError(429, "insufficient credits on account"))
        with pytest.raises(QuotaExhausted):
            provider.generate(prompt="p", system="s", schema=_Schema, model="m")

    def test_plain_429_is_rate_limited(self) -> None:
        provider = _nvidia_raising(_FakeAPIError(429, "too many requests, slow down"))
        with pytest.raises(RateLimited):
            provider.generate(prompt="p", system="s", schema=_Schema, model="m")

    def test_404_is_model_unavailable(self) -> None:
        provider = _nvidia_raising(_FakeAPIError(404, "The model 'x' was not found"))
        with pytest.raises(ModelUnavailable):
            provider.generate(prompt="p", system="s", schema=_Schema, model="m")

    def test_auth_failure_is_a_provider_error_not_a_crash(self) -> None:
        provider = _nvidia_raising(_FakeAPIError(401, "invalid api key"))
        with pytest.raises(LlmUnavailableError):
            provider.generate(prompt="p", system="s", schema=_Schema, model="m")

    def test_the_error_message_never_contains_the_key(self, monkeypatch) -> None:
        secret = "nvapi-leak-me-if-you-can-9876543210"
        monkeypatch.setenv("NVIDIA_API_KEY", secret)
        provider = _nvidia_raising(_FakeAPIError(400, f"bad request with key {secret}"))
        with pytest.raises(LlmUnavailableError) as exc:
            provider.generate(prompt="p", system="s", schema=_Schema, model="m")
        assert secret not in str(exc.value)
        assert "<<REDACTED_API_KEY>>" in str(exc.value)


# --------------------------------------------------------------------------- #
# Quota degrades to template, never to a 500
# --------------------------------------------------------------------------- #


class TestQuotaDegradesToTemplate:
    def test_live_generation_falls_back_when_quota_is_exhausted(self, monkeypatch) -> None:
        """
        The failure this whole provider phase exists to survive.

        A depleted provider must produce honest template text, marked as such —
        never a 500, never a gap.
        """
        import importlib.util
        import sys
        from pathlib import Path

        scripts = Path(__file__).resolve().parents[2] / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        spec = importlib.util.spec_from_file_location(
            "pregenerate_explanations", scripts / "pregenerate_explanations.py"
        )
        pregen = importlib.util.module_from_spec(spec)
        sys.modules["pregenerate_explanations"] = pregen
        spec.loader.exec_module(pregen)

        from app.explanation import ExplanationMode, generate_explanation, generator_llm

        def out_of_credits(*args, **kwargs):
            raise QuotaExhausted("nvidia: out of quota/credits (HTTP 402).")

        monkeypatch.setenv("GEMINI_API_KEY", "mock")
        monkeypatch.setattr(generator_llm, "generate", out_of_credits)

        context, _ = pregen.build_context(pregen.load_reachable_cases()[0])
        result = generate_explanation(context, ExplanationMode.LIVE)

        assert result.generator in ("static", "template")
        for value in result.explanation.fields().values():
            assert value.strip(), "quota exhaustion produced an empty field"


# --------------------------------------------------------------------------- #
# The deployed path needs no key
# --------------------------------------------------------------------------- #


class TestNoKeyAtAll:
    def test_no_provider_is_configured_without_keys(self, monkeypatch) -> None:
        for name in ("NVIDIA_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"):
            monkeypatch.delenv(name, raising=False)
        assert get_provider("nvidia").is_configured() is False
        assert get_provider("gemini").is_configured() is False
        # template needs nothing and is always ready.
        assert get_provider("template").is_configured() is True

    def test_template_provider_generates_without_a_key(self, monkeypatch) -> None:
        """`LLM_PROVIDER=template` produces a complete explanation, no network."""
        for name in ("NVIDIA_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
            monkeypatch.delenv(name, raising=False)
        import importlib.util
        import sys
        from pathlib import Path

        scripts = Path(__file__).resolve().parents[2] / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        spec = importlib.util.spec_from_file_location(
            "pregenerate_explanations", scripts / "pregenerate_explanations.py"
        )
        pregen = importlib.util.module_from_spec(spec)
        sys.modules["pregenerate_explanations"] = pregen
        spec.loader.exec_module(pregen)

        from app.explanation import generator_llm

        context, _ = pregen.build_context(pregen.load_reachable_cases()[0])
        result = generator_llm.generate(context, provider="template")
        assert result.provider == "template"
        assert result.json_mode == "none"
        for value in result.explanation.fields().values():
            assert value.strip()
