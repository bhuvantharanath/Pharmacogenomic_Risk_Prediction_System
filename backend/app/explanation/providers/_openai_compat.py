"""
Shared implementation for OpenAI-compatible endpoints.

NVIDIA NIM and a local Ollama both speak the OpenAI chat-completions dialect, so
the request/response/error handling is written once here and the two concrete
providers differ only in base URL, key, defaults, and how they read a "you are
out of credits" signal. The `openai` SDK is imported lazily so importing this
module never requires it — only calling `generate` does.
"""

from __future__ import annotations

from pydantic import BaseModel

from .base import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, Provider, ProviderResult
from .errors import (
    InvalidResponse,
    ModelUnavailable,
    ProviderError,
    QuotaExhausted,
    RateLimited,
)
from .redact import scrub

#: Appended to the system instruction when we cannot rely on a native JSON mode.
#: Names the exact keys so a model that ignores `response_format` still has an
#: unambiguous target.
_JSON_DIRECTIVE = """

OUTPUT FORMAT — MANDATORY
Return ONLY a single JSON object, no prose before or after it, no markdown
fences, no explanation of your reasoning. The object must have exactly these
string keys: {keys}. Every value must be a non-empty string."""


class OpenAICompatibleProvider(Provider):
    """Base for any endpoint that speaks OpenAI chat-completions."""

    #: Subclasses set these.
    base_url: str = ""
    key_env: tuple[str, ...] = ()
    _default_model: str = ""

    #: Words in a 429/402 body that mean "credits/quota gone", not "slow down".
    _QUOTA_WORDS = ("insufficient", "credit", "quota", "exhaust", "balance", "payment")

    def api_key(self) -> str | None:
        return self._env(*self.key_env)

    def default_model(self) -> str:
        return self._default_model

    def _client(self):
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise ProviderError(
                "the 'openai' package is not installed — "
                "pip install -r requirements-llm.txt"
            ) from exc
        return OpenAI(base_url=self.base_url, api_key=self.api_key() or "unused")

    def generate(
        self,
        *,
        prompt: str,
        system: str,
        schema: type[BaseModel],
        model: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> ProviderResult:
        if not self.is_configured():
            raise ProviderError(
                f"{self.name} is not configured "
                f"(set {', '.join(self.key_env) or 'the endpoint'})"
            )

        client = self._client()
        keys = ", ".join(schema.model_fields)

        # Least-invasive first: ask for a JSON object natively. If the endpoint
        # rejects response_format (many NIM models do), retry with the format
        # baked into the prompt. Record which rung worked.
        for json_mode in ("response_format", "prompt_enforced"):
            messages = [
                {
                    "role": "system",
                    "content": system
                    + (_JSON_DIRECTIVE.format(keys=keys) if json_mode == "prompt_enforced" else ""),
                },
                {"role": "user", "content": prompt},
            ]
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode == "response_format":
                kwargs["response_format"] = {"type": "json_object"}

            try:
                response = client.chat.completions.create(**kwargs)
            except Exception as exc:  # noqa: BLE001 — normalise every SDK error
                if json_mode == "response_format" and self._is_unsupported_format(exc):
                    continue  # try prompt-enforced
                raise self._normalise(exc) from exc

            text = self._extract_text(response)
            if not text.strip():
                # An empty body on the native path might just be format
                # confusion; let the prompt-enforced pass try before giving up.
                if json_mode == "response_format":
                    continue
                raise InvalidResponse(f"{self.name} returned an empty response")

            return ProviderResult(
                text=text,
                usage=self._usage(response),
                raw=response,
                json_mode=json_mode,
                model=getattr(response, "model", model) or model,
            )

        raise InvalidResponse(f"{self.name} returned no usable content in either JSON mode")

    # -- error / response normalisation ------------------------------------- #

    @staticmethod
    def _extract_text(response: object) -> str:
        try:
            return response.choices[0].message.content or ""
        except (AttributeError, IndexError):
            return ""

    @staticmethod
    def _usage(response: object) -> dict:
        usage = getattr(response, "usage", None)
        if usage is None:
            return {}
        return {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        }

    @staticmethod
    def _is_unsupported_format(exc: Exception) -> bool:
        """A 400 complaining specifically about response_format."""
        status = getattr(exc, "status_code", None)
        text = str(getattr(exc, "message", "") or exc).lower()
        return status == 400 and ("response_format" in text or "json" in text)

    def _normalise(self, exc: Exception) -> ProviderError:
        """Translate an openai SDK exception into our typed tree, key-scrubbed."""
        status = getattr(exc, "status_code", None)
        body = scrub(getattr(exc, "message", "") or exc)
        low = body.lower()

        def carry(err: ProviderError) -> ProviderError:
            err.provider = self.name
            return err

        # Credits depleted. NVIDIA uses 402; some report it as 429 with a
        # payment/credit message. Either way, retrying and backing off are both
        # pointless — this is a wall, not a speed bump.
        if status == 402 or (status in (402, 429) and any(w in low for w in self._QUOTA_WORDS)):
            return carry(QuotaExhausted(
                f"{self.name}: out of quota/credits (HTTP {status}). "
                f"Switch LLM_PROVIDER or top up. {body}"
            ))
        if status == 429:
            err = RateLimited(f"{self.name}: rate limited (HTTP 429). {body}")
            err.retry_after = self._retry_after(exc)
            return carry(err)
        if status == 404 or "model" in low and "not" in low and "found" in low:
            return carry(ModelUnavailable(f"{self.name}: model not available. {body}"))
        if status in (401, 403):
            return carry(ProviderError(f"{self.name}: authentication failed (HTTP {status})."))
        return carry(ProviderError(f"{self.name}: call failed. {body}"))

    @staticmethod
    def _retry_after(exc: Exception) -> float | None:
        headers = getattr(getattr(exc, "response", None), "headers", None)
        if not headers:
            return None
        value = headers.get("retry-after") or headers.get("Retry-After")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
