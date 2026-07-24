"""
Google Gemini provider.

The original PharmaGuard generator, now behind the provider interface and still
selectable with `LLM_PROVIDER=gemini`. It uses google-genai's native structured
output (`response_schema`), so its `json_mode` is always `response_schema` and
the prompt-enforced ladder never runs for it.

The token-ceiling post-mortem that lives here is load-bearing history: on
2026-07-23 `max_output_tokens` was shared with the model's thinking budget, the
JSON was truncated mid-string, and every failure surfaced as an opaque parse
error. `reject_if_truncated` exists so that never costs a run again.
"""

from __future__ import annotations

from pydantic import BaseModel

from .base import Provider, ProviderResult
from .errors import InvalidResponse, ProviderError, QuotaExhausted, RateLimited
from .redact import scrub

#: Four prose fields need perhaps 600 tokens.2048 looked generous and was not:
#: on a thinking model, reasoning tokens draw from this same budget. See module
#: docstring.
GEMINI_MAX_OUTPUT_TOKENS = 8192

#: Zero disables thinking. This task is not reasoning — the model composes prose
#: from a closed context and the guard decides acceptability, so thinking tokens
#: buy nothing and, under a finite ceiling, compete with the answer.
GEMINI_THINKING_BUDGET = 0

#: Words that mark a Gemini error as a quota wall rather than a transient limit.
_QUOTA_WORDS = ("resource_exhausted", "quota", "exhaust")


def reject_if_truncated(response: object) -> None:
    """
    Raise with the real cause when the model ran out of output budget.

    Without this a truncated response falls through to JSON parsing and reports
    `Invalid JSON: EOF while parsing a string at line 4 column 84` — true, and
    useless, because it points at the parser rather than the ceiling that caused
    it. `thoughts_token_count` is surfaced because it is the number that makes
    the cause obvious.
    """
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return
    reason = getattr(candidates[0], "finish_reason", None)
    if reason is None or getattr(reason, "name", str(reason)) != "MAX_TOKENS":
        return

    usage = getattr(response, "usage_metadata", None)
    thoughts = getattr(usage, "thoughts_token_count", None) or 0
    emitted = getattr(usage, "candidates_token_count", None) or 0
    raise InvalidResponse(
        f"Gemini hit the {GEMINI_MAX_OUTPUT_TOKENS}-token output ceiling and the "
        f"response was cut off mid-JSON "
        f"({thoughts} thinking tokens, {emitted} output tokens). "
        "Raise the ceiling or lower the thinking budget."
    )


class GeminiProvider(Provider):
    name = "gemini"
    _default_model = "gemini-3.6-flash"

    def is_configured(self) -> bool:
        if not self._env("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            return False
        try:
            import google.genai  # noqa: F401
        except ImportError:
            return False
        return True

    def default_model(self) -> str:
        return self._default_model

    def generate(
        self,
        *,
        prompt: str,
        system: str,
        schema: type[BaseModel],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = GEMINI_MAX_OUTPUT_TOKENS,
    ) -> ProviderResult:
        key = self._env("GEMINI_API_KEY", "GOOGLE_API_KEY")
        if not key:
            raise ProviderError("GEMINI_API_KEY is not set.")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ProviderError(
                "google-genai is not installed — pip install -r requirements-llm.txt"
            ) from exc

        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=GEMINI_THINKING_BUDGET
                    ),
                ),
            )
        except Exception as exc:  # noqa: BLE001 — SDK raises a wide range
            raise self._normalise(exc) from exc

        reject_if_truncated(response)
        text = (getattr(response, "text", None) or "").strip()
        if not text:
            raise InvalidResponse("Gemini returned an empty response.")

        return ProviderResult(
            text=text,
            usage=self._usage(response),
            raw=response,
            json_mode="response_schema",
            model=model,
        )

    def _normalise(self, exc: Exception) -> ProviderError:
        body = scrub(exc)
        low = body.lower()
        if any(word in low for word in _QUOTA_WORDS):
            err: ProviderError = QuotaExhausted(
                f"gemini: out of quota (RESOURCE_EXHAUSTED). "
                f"Switch LLM_PROVIDER or wait for the daily reset. {body}"
            )
        elif "429" in low or "rate" in low:
            err = RateLimited(f"gemini: rate limited. {body}")
        else:
            err = ProviderError(f"Gemini call failed: {body}")
        err.provider = self.name
        return err

    @staticmethod
    def _usage(response: object) -> dict:
        usage = getattr(response, "usage_metadata", None)
        if usage is None:
            return {}
        return {
            "prompt_tokens": getattr(usage, "prompt_token_count", None),
            "completion_tokens": getattr(usage, "candidates_token_count", None),
            "total_tokens": getattr(usage, "total_token_count", None),
            "thoughts_tokens": getattr(usage, "thoughts_token_count", None),
        }
