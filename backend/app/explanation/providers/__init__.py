"""
Provider registry and selection.

One place that knows the set of providers and how the environment chooses among
them, so nothing else hardcodes a vendor. Selection precedence, most specific
first:

    explicit argument  →  LLM_PROVIDER env  →  default ("gemini")

and for the model id:

    explicit argument  →  LLM_MODEL env  →  the provider's own default

The default is `gemini` only for backward compatibility with the code and tests
that predate this package; set `LLM_PROVIDER=nvidia` (or `ollama`, `template`)
to switch. Nothing here makes a network call — resolving a provider is free, so
`available()` and the CLIs can probe configuration without spending anything.
"""

from __future__ import annotations

import os

from .base import Provider, ProviderResult
from .errors import (
    InvalidResponse,
    LlmUnavailableError,
    ModelUnavailable,
    ProviderError,
    QuotaExhausted,
    RateLimited,
)
from .gemini import GeminiProvider
from .nvidia_nim import NvidiaNimProvider
from .ollama import OllamaProvider
from .template import TemplateProvider

#: Instantiated lazily and cached; providers are cheap and stateless.
_REGISTRY: dict[str, type[Provider]] = {
    "gemini": GeminiProvider,
    "nvidia": NvidiaNimProvider,
    "ollama": OllamaProvider,
    "template": TemplateProvider,
}

_CACHE: dict[str, Provider] = {}

DEFAULT_PROVIDER = "gemini"


def provider_names() -> list[str]:
    return list(_REGISTRY)


def resolve_provider_name(explicit: str | None = None) -> str:
    name = (explicit or os.environ.get("LLM_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    if name not in _REGISTRY:
        raise ModelUnavailable(
            f"unknown provider {name!r}; choose one of {', '.join(_REGISTRY)}"
        )
    return name


def get_provider(name: str | None = None) -> Provider:
    """Return the provider instance for `name` (or the resolved default)."""
    resolved = resolve_provider_name(name)
    if resolved not in _CACHE:
        _CACHE[resolved] = _REGISTRY[resolved]()
    return _CACHE[resolved]


def resolve_model(provider: Provider, explicit: str | None = None) -> str:
    """Model id precedence: explicit → LLM_MODEL → provider default."""
    return (explicit or os.environ.get("LLM_MODEL") or provider.default_model() or "").strip()


__all__ = [
    "Provider",
    "ProviderResult",
    "LlmUnavailableError",
    "ProviderError",
    "QuotaExhausted",
    "RateLimited",
    "ModelUnavailable",
    "InvalidResponse",
    "get_provider",
    "resolve_provider_name",
    "resolve_model",
    "provider_names",
    "DEFAULT_PROVIDER",
]
