"""
PharmaGuard — explanation layer.

One entry point, `generate_explanation(context)`, behind three modes:

    static    (default, deployed) look up a pre-generated, guard-checked,
              human-reviewable explanation and fill slots. No API call.
    live      call Gemini per request, then the guard. For the demo video.
    template  deterministic composition only. Always available.

Every path is guarded and every path degrades downward — live falls back to
static, static falls back to template — so a caller always receives a complete
explanation. `generate_explanation` does not raise.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

from .context import Explanation, ExplanationContext
from .guard import GuardReport, check, log_violation
from . import generator_template, static_store


class ExplanationMode(str, Enum):
    STATIC = "static"
    LIVE = "live"
    TEMPLATE = "template"

    @classmethod
    def from_env(cls, value: str | None = None) -> "ExplanationMode":
        """
        Resolve the configured mode.

        An unrecognised value falls back to STATIC rather than raising: a typo
        in a deployment env var should degrade to the safe default, not take the
        service down.
        """
        raw = (value if value is not None else os.environ.get("EXPLANATION_MODE", "")).strip().lower()
        try:
            return cls(raw) if raw else cls.STATIC
        except ValueError:
            return cls.STATIC


@dataclass
class ExplanationResult:
    """The explanation plus how it was produced — surfaced in quality_metrics."""

    explanation: Explanation
    mode: ExplanationMode
    generator: str
    guard: GuardReport | None = None
    reviewed: bool = False
    notes: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.notes is None:
            self.notes = []

    @property
    def provenance(self) -> str:
        """One line for `quality_metrics.warnings`."""
        bits = [f"explanation mode={self.mode.value}", f"source={self.generator}"]
        if self.guard is not None:
            bits.append("guard=passed" if self.guard.passed else "guard=failed")
        else:
            # The template path is faithful by construction; say so rather than
            # implying a check ran that did not.
            bits.append("guard=n/a (deterministic)")
        if self.generator == "static":
            bits.append("reviewed=yes" if self.reviewed else "reviewed=NO")
        return ", ".join(bits)


def _template_result(
    context: ExplanationContext, mode: ExplanationMode, notes: list[str]
) -> ExplanationResult:
    """The floor. Faithful by construction, so the guard is informational."""
    explanation = generator_template.generate(context)
    return ExplanationResult(
        explanation=explanation.fill_slots(context),
        mode=mode,
        generator=generator_template.GENERATOR_NAME,
        guard=None,
        reviewed=False,
        notes=notes,
    )


def _static_result(
    context: ExplanationContext, mode: ExplanationMode, notes: list[str]
) -> ExplanationResult | None:
    """Look up a pre-generated entry. None means 'fall back'."""
    stored = static_store.lookup(context.drug, context.phenotype.value)
    if stored is None:
        store = static_store.load_store()
        if store.load_error:
            notes.append(store.load_error)
        else:
            notes.append(
                f"No pre-generated explanation for "
                f"({context.drug}, {context.phenotype.value}); using the "
                "deterministic template."
            )
        return None

    return ExplanationResult(
        explanation=stored.explanation.fill_slots(context),
        mode=mode,
        generator="static",
        # The stored guard verdict, recorded at generation time. Re-running the
        # guard here would be theatre: the text has not changed since it passed.
        guard=GuardReport(
            passed=stored.guard_passed,
            action_taken="accepted (pre-generated)",
            generator="static",
        ),
        reviewed=stored.is_reviewed,
        notes=notes,
    )


def _live_result(
    context: ExplanationContext, mode: ExplanationMode, notes: list[str]
) -> ExplanationResult | None:
    """
    Generate now, guard it, retry once, then give up.

    One retry, not several: a second failure on the same context is evidence the
    prompt or the context is the problem, and the template path is right there.
    """
    from . import generator_llm

    last_report: GuardReport | None = None

    for attempt in (1, 2):
        try:
            result = generator_llm.generate(context)
        except generator_llm.LlmUnavailableError as exc:
            notes.append(f"Live generation unavailable: {exc}")
            return None

        report = check(result.explanation, context, generator=generator_llm.GENERATOR_NAME)
        report.attempts = attempt

        if report.passed:
            return ExplanationResult(
                explanation=result.explanation.fill_slots(context),
                mode=mode,
                generator=f"llm:{result.model}",
                guard=report,
                reviewed=False,
                notes=notes,
            )

        report.action_taken = "retried" if attempt == 1 else "fell back to template"
        log_violation(report, context, result.explanation)
        last_report = report
        notes.append(
            f"Live generation attempt {attempt} failed the faithfulness guard: "
            f"{report.summary}"
        )

    fallback = _template_result(context, mode, notes)
    fallback.guard = last_report
    return fallback


def generate_explanation(
    context: ExplanationContext, mode: ExplanationMode | None = None
) -> ExplanationResult:
    """
    Produce an explanation for one drug result. Never raises.

    static -> pre-generated, else template.
    live   -> LLM + guard (one retry), else static, else template.
    template -> deterministic.
    """
    resolved = mode or ExplanationMode.from_env()
    notes: list[str] = []

    if resolved is ExplanationMode.TEMPLATE:
        return _template_result(context, resolved, notes)

    if resolved is ExplanationMode.LIVE:
        live = _live_result(context, resolved, notes)
        if live is not None:
            return live
        # Live was unavailable — prefer reviewed static text over the template.
        static = _static_result(context, resolved, notes)
        return static if static is not None else _template_result(context, resolved, notes)

    static = _static_result(context, resolved, notes)
    return static if static is not None else _template_result(context, resolved, notes)


__all__ = [
    "Explanation",
    "ExplanationContext",
    "ExplanationMode",
    "ExplanationResult",
    "generate_explanation",
]
