"""
Typed provider errors, normalised across vendors.

WHY A HIERARCHY

Each SDK raises its own exception zoo. Callers should not have to know that
Gemini says `RESOURCE_EXHAUSTED` in a string while NVIDIA returns HTTP 402 —
they should be able to ask "was this a hard quota wall, or a transient rate
limit?" and act on the answer. The providers translate; everything above them
sees these types.

BACKWARD COMPATIBILITY

`LlmUnavailableError` was the single exception the old Gemini-only code raised,
and several call sites still `except generator_llm.LlmUnavailableError`. Keeping
it as the base of this tree means those catches keep working unchanged, while
new code can catch a specific subtype when it wants to react differently — most
importantly, to fall through to a different provider on `QuotaExhausted` rather
than degrading straight to the template.
"""

from __future__ import annotations


class LlmUnavailableError(RuntimeError):
    """
    Generation could not produce a usable result. Callers fall back.

    The base of the provider error tree, and the type existing call sites catch.
    Anything that reaches a caller as this (or a subclass) means "no model output
    this time" — never a reason to 500.
    """


class ProviderError(LlmUnavailableError):
    """Base for failures attributable to a specific provider call."""

    #: Set by providers so a caught error can be attributed without parsing text.
    provider: str = ""


class QuotaExhausted(ProviderError):
    """
    A hard wall: the account/key is out of quota or credits.

    NVIDIA returns HTTP 402 when credits are depleted; Gemini says
    `RESOURCE_EXHAUSTED` / 429 against a daily cap. Retrying does not help and
    backing off does not help — the correct response is to switch providers or
    stop. Distinct from `RateLimited` precisely so a caller can tell the
    difference between "wait" and "this key is done".
    """


class RateLimited(ProviderError):
    """
    A transient per-minute/second limit. Backing off and retrying may succeed.

    Kept separate from `QuotaExhausted` because the right reaction is opposite:
    here you wait, there you give up on this key.
    """

    #: Seconds the provider asked us to wait, if it said so (Retry-After).
    retry_after: float | None = None


class ModelUnavailable(ProviderError):
    """The requested model id does not exist, or this key cannot access it."""


class InvalidResponse(ProviderError):
    """
    The call returned, but the body was not usable: empty, truncated mid-JSON,
    or not parseable into the schema after every recovery attempt.
    """


__all__ = [
    "LlmUnavailableError",
    "ProviderError",
    "QuotaExhausted",
    "RateLimited",
    "ModelUnavailable",
    "InvalidResponse",
]
