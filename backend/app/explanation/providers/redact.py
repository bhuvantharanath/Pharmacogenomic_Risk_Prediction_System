"""
Key scrubbing, in a dependency-free module so every provider can share it.

Lives here rather than in `generator_llm` to avoid an import cycle: the
providers need it, and `generator_llm` imports the providers. It reads the key
names for every provider, so an error string from any of them is covered.
"""

from __future__ import annotations

import os

#: Every environment variable that could hold a live credential.
_KEY_NAMES = ("NVIDIA_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY")


def scrub(text: object) -> str:
    """
    Replace any known API key value found in `text` with a marker.

    Applied at every site that renders a third-party exception, because those
    strings come from SDKs whose behaviour we do not control. A leaked key in a
    committed report or a captured terminal log is unrecoverable, so this runs
    even where the exception provably cannot contain one — cheap insurance on a
    failure-only path.
    """
    rendered = str(text)
    for name in _KEY_NAMES:
        secret = os.environ.get(name)
        if secret and len(secret) > 8 and secret in rendered:
            rendered = rendered.replace(secret, "<<REDACTED_API_KEY>>")
    return rendered
