"""
NVIDIA NIM provider.

NVIDIA's hosted inference (https://build.nvidia.com) exposes an OpenAI-compatible
endpoint at https://integrate.api.nvidia.com/v1, authenticated with an
`nvapi-…` key in NVIDIA_API_KEY. So the whole implementation is the shared
OpenAI-compatible base plus configuration.

CREDITS
    A depleted account returns HTTP 402, which the base maps to `QuotaExhausted`
    with a distinct message — the failure mode this whole provider phase exists
    to survive, after the Gemini key hit its own wall.
"""

from __future__ import annotations

from ._openai_compat import OpenAICompatibleProvider


class NvidiaNimProvider(OpenAICompatibleProvider):
    name = "nvidia"
    base_url = "https://integrate.api.nvidia.com/v1"
    key_env = ("NVIDIA_API_KEY",)

    #: No hardcoded model default. A NIM id written from memory is a guess with a
    #: shelf life; `scripts/list_models.py` discovers the real ones and
    #: `benchmark_models.py` picks. LLM_MODEL or --model must supply it.
    _default_model = ""

    def is_configured(self) -> bool:
        return bool(self.api_key())
