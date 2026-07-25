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
from dataclasses import dataclass, replace
from enum import Enum

from ..models import PharmacogenomicProfile
from .compose import compose_variant_rationale
from .consistency import check_consistency
from .context import Explanation, ExplanationContext
from .guard import GuardReport, check, log_violation
from .slot_verifier import SlotVerification, verify as verify_slots
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
    #: Renamed from `reviewed`. Nothing here records clinical review, because
    #: this project has no clinical reviewer; what it records is that every
    #: clinical claim traces to a cited source.
    provenance_verified: bool = False
    #: Runtime cross-check of the values injected into the reviewed prose.
    #: None when no profile was supplied to verify against.
    slots: SlotVerification | None = None
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
        if self.slots is not None:
            bits.append(
                "slots=verified" if self.slots.passed else "slots=MISMATCH"
            )
        if self.generator == "static":
            bits.append(
                "provenance=verified" if self.provenance_verified else "provenance=UNVERIFIED"
            )
        return ", ".join(bits)


def _template_result(
    context: ExplanationContext,
    mode: ExplanationMode,
    notes: list[str],
    profile: PharmacogenomicProfile | None = None,
) -> ExplanationResult:
    """
    The floor. Faithful by construction, so the guard is informational.

    Slot verification still runs when a profile is supplied — a mismatch here
    means the context and the profile disagree, which is a real bug worth
    surfacing. But we serve the result anyway: this generator IS the fallback,
    so there is nothing safer to fall back to.
    """
    unfilled = generator_template.generate(context)
    filled = unfilled.fill_slots(context)

    verification: SlotVerification | None = None
    if profile is not None:
        verification = verify_slots(filled, unfilled, context, profile)
        if not verification.passed:
            notes.append(
                "Template explanation failed runtime slot verification "
                f"({verification.summary}). Serving it regardless — it is the "
                "safest text available — but this indicates the analysis "
                "context and the reported profile disagree."
            )

    return ExplanationResult(
        explanation=filled,
        mode=mode,
        generator=generator_template.GENERATOR_NAME,
        guard=None,
        provenance_verified=False,
        slots=verification,
        notes=notes,
    )


def _static_result(
    context: ExplanationContext,
    mode: ExplanationMode,
    notes: list[str],
    profile: PharmacogenomicProfile | None = None,
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

    filled = stored.explanation.fill_slots(context)

    # The stored guard verdict covers the PROSE, which has not changed since it
    # was checked. It does not cover the values injected just now, so those get
    # cross-checked against the profile the client will render.
    verification: SlotVerification | None = None
    if profile is not None:
        verification = verify_slots(filled, stored.explanation, context, profile)
        if not verification.passed:
            notes.append(
                "Pre-generated explanation failed runtime slot verification "
                f"({verification.summary}); falling back to the deterministic "
                "template. A reviewed sentence carrying the wrong genotype is "
                "more dangerous than plainer text, because it is more credible."
            )
            return None

    # `variant_rationale` is never model-authored and never slot-filled: it is
    # composed here from the profile in this very response, so the sentence and
    # the reported genotype cannot disagree. See explanation/compose.py.
    filled = replace(filled, variant_rationale=compose_variant_rationale(context))

    # LABEL/PROSE CONSISTENCY — the check that was missing.
    #
    # The provenance guard verifies explanation -> CPIC and the mapping
    # validation verifies label -> CPIC, but nothing verified explanation ->
    # label. Two artifacts can each trace to the same source and still
    # contradict each other, because they trace to different parts of it. Three
    # real divergences were found this way, including a green "Safe" badge over
    # prose telling the reader they need a lower dose.
    #
    # Degrade rather than serve the pair: a fluent contradiction is more
    # dangerous than plainer text, because it is more credible.
    consistency = check_consistency(
        label=context.risk_label,
        phenotype=context.phenotype,
        fields=filled.fields(),
    )
    if not consistency.consistent:
        notes.append(
            "Pre-generated explanation contradicts its own risk label "
            f"({consistency.summary}); falling back to the deterministic "
            "template. Text that disagrees with the label beside it is worse "
            "than plainer text, because the reader has no way to tell which "
            "one to believe."
        )
        return None

    return ExplanationResult(
        explanation=filled,
        mode=mode,
        generator="static",
        guard=GuardReport(
            passed=stored.guard_passed,
            action_taken="accepted (pre-generated)",
            generator="static",
        ),
        provenance_verified=stored.is_provenance_verified,
        slots=verification,
        notes=notes,
    )


def _live_result(
    context: ExplanationContext,
    mode: ExplanationMode,
    notes: list[str],
    profile: PharmacogenomicProfile | None = None,
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
            filled = result.explanation.fill_slots(context)
            verification: SlotVerification | None = None
            if profile is not None:
                verification = verify_slots(
                    filled, result.explanation, context, profile
                )
                if not verification.passed:
                    notes.append(
                        "Live explanation passed the faithfulness guard but "
                        f"failed slot verification ({verification.summary}); "
                        "falling back to the template."
                    )
                    break
            return ExplanationResult(
                explanation=filled,
                mode=mode,
                generator=f"llm:{result.model}",
                guard=report,
                provenance_verified=False,
                slots=verification,
                notes=notes,
            )

        report.action_taken = "retried" if attempt == 1 else "fell back to template"
        log_violation(report, context, result.explanation)
        last_report = report
        notes.append(
            f"Live generation attempt {attempt} failed the faithfulness guard: "
            f"{report.summary}"
        )

    fallback = _template_result(context, mode, notes, profile)
    fallback.guard = last_report
    return fallback


def generate_explanation(
    context: ExplanationContext,
    mode: ExplanationMode | None = None,
    profile: PharmacogenomicProfile | None = None,
) -> ExplanationResult:
    """
    Produce an explanation for one drug result. Never raises.

    static -> pre-generated, else template.
    live   -> LLM + guard (one retry), else static, else template.
    template -> deterministic.

    `profile` is the `pharmacogenomic_profile` this response will carry. When
    supplied, every value injected into the prose is cross-checked against it
    (see `slot_verifier`), and a mismatch demotes the result to the template.
    It is optional so the explanation layer stays testable in isolation, but
    the request path always passes it.
    """
    resolved = mode or ExplanationMode.from_env()
    notes: list[str] = []

    if resolved is ExplanationMode.TEMPLATE:
        return _template_result(context, resolved, notes, profile)

    if resolved is ExplanationMode.LIVE:
        live = _live_result(context, resolved, notes, profile)
        if live is not None:
            return live
        # Live was unavailable — prefer reviewed static text over the template.
        static = _static_result(context, resolved, notes, profile)
        return (
            static
            if static is not None
            else _template_result(context, resolved, notes, profile)
        )

    static = _static_result(context, resolved, notes, profile)
    return (
        static
        if static is not None
        else _template_result(context, resolved, notes, profile)
    )


__all__ = [
    "Explanation",
    "ExplanationContext",
    "ExplanationMode",
    "ExplanationResult",
    "generate_explanation",
]
