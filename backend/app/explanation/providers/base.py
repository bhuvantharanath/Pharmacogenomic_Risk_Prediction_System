"""
The provider interface every vendor implementation satisfies.

One method, `generate`, returning a `ProviderResult`. The interface is
deliberately thin: a provider turns (prompt, system instruction, schema, model)
into text plus bookkeeping, and normalises its SDK's errors into the typed tree
in `errors.py`. It knows nothing about PharmaGuard's explanation semantics, the
faithfulness guard, or slot filling — those live one layer up, so they are
written once rather than per vendor.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pydantic import BaseModel

#: Shared default. Four short prose fields need well under this; the ceiling
#: exists to stop a runaway or a reasoning model from writing forever. See the
#: 2026-07-23 truncation post-mortem in generator_llm for why it is not tiny.
DEFAULT_MAX_TOKENS = 8192

#: Low but non-zero: near-deterministic prose without the degenerate repetition
#: temperature 0 can produce on short structured outputs.
DEFAULT_TEMPERATURE = 0.2


@dataclass
class ProviderResult:
    """What a provider hands back."""

    #: The model's raw text output. Expected to contain JSON, but not yet parsed
    #: or stripped of reasoning blocks — that is the orchestrator's job, so the
    #: recovery logic is identical across providers.
    text: str

    #: Token accounting, best-effort and normalised to a plain dict:
    #: {"prompt_tokens", "completion_tokens", "total_tokens"}. Empty if the
    #: provider did not report usage.
    usage: dict = field(default_factory=dict)

    #: The raw SDK response object, for debugging and for the benchmark's raw
    #: capture. Never inspected by production code.
    raw: object = None

    #: Which JSON strategy actually produced this output — "response_schema",
    #: "response_format", or "prompt_enforced". Recorded per entry so a model's
    #: quirks are visible rather than folded away.
    json_mode: str = ""

    #: The model id that served the request, as the provider reports it.
    model: str = ""


class Provider(ABC):
    """A vendor that can turn a prompt into JSON text."""

    #: Stable short name used in env selection and recorded on every entry.
    name: str = ""

    @abstractmethod
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
        """
        Produce JSON text for `prompt` under `system`, targeting `schema`.

        Must raise a subclass of `LlmUnavailableError` for every failure —
        missing key, missing SDK, transport error, quota wall, unusable body —
        so no caller ever sees a raw SDK exception, and never a 500.
        """

    @abstractmethod
    def is_configured(self) -> bool:
        """True if this provider has what it needs to make a call (key, SDK)."""

    def default_model(self) -> str:
        """The model id to use when neither the CLI nor LLM_MODEL specifies one."""
        return ""

    # -- helpers shared by concrete providers ------------------------------- #

    @staticmethod
    def _env(*names: str) -> str | None:
        for name in names:
            value = os.environ.get(name)
            if value:
                return value
        return None
