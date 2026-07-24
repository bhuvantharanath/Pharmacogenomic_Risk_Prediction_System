"""
Ollama provider — a local model, for zero-quota development.

Ollama serves an OpenAI-compatible endpoint at http://localhost:11434/v1 and
needs no key, so the same base does the work. Its reason for existing is being
able to develop and test the whole generation path — prompt, JSON extraction,
guard, provenance — without spending anyone's credits, after two hosted keys hit
their walls in a row.

The base URL honours OLLAMA_HOST (matching Ollama's own convention) so a model
running on another machine still works.
"""

from __future__ import annotations

import os

from ._openai_compat import OpenAICompatibleProvider


class OllamaProvider(OpenAICompatibleProvider):
    name = "ollama"
    #: No key. `is_configured` is about the server being reachable, checked at
    #: call time by the SDK rather than pinged here.
    key_env = ()
    _default_model = os.environ.get("OLLAMA_MODEL", "")

    @property
    def base_url(self) -> str:  # type: ignore[override]
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        if not host.startswith("http"):
            host = f"http://{host}"
        return f"{host}/v1"

    def api_key(self) -> str | None:
        # Ollama ignores the key but the OpenAI SDK insists on a non-empty one.
        return "ollama"

    def is_configured(self) -> bool:
        # A local server is assumed available when the provider is explicitly
        # selected; a connection error surfaces as a normalised ProviderError at
        # call time rather than a misleading "not configured" here.
        return True
