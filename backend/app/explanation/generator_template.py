"""
PharmaGuard — deterministic template generator.

The floor of the system. No API, no network, no key, no failure mode: whatever
happens upstream, this produces a complete, faithful explanation.

It is faithful by construction rather than by inspection — every sentence is
either fixed English or a value copied verbatim out of the context — so it
passes the guard trivially. That is the point: the guard's fallback path cannot
itself need a guard.

Prose quality is intentionally modest. It reads like a form letter because it is
one. When the pre-generated static explanations exist, they are preferred; this
is what the user gets when they do not.
"""

from __future__ import annotations

from ..models import Phenotype, RiskLabel
from .context import Explanation, ExplanationContext

GENERATOR_NAME = "template"

# What the risk label means, in plain terms. Fixed English keyed by enum — no
# clinical values, so nothing here can contradict PharmCAT.
_RISK_SENTENCE: dict[RiskLabel, str] = {
    RiskLabel.SAFE: (
        "Your genetic results do not suggest a change to how this medicine is "
        "usually prescribed."
    ),
    RiskLabel.ADJUST_DOSAGE: (
        "Your genetic results suggest this medicine may need to be prescribed "
        "differently from the usual approach."
    ),
    RiskLabel.TOXIC: (
        "Your genetic results suggest a higher chance of harmful effects from "
        "this medicine."
    ),
    RiskLabel.INEFFECTIVE: (
        "Your genetic results suggest this medicine may not work as well for "
        "you as intended."
    ),
    RiskLabel.UNKNOWN: (
        "This tool could not reach a conclusion about this medicine for you."
    ),
}

# How the phenotype reads in a sentence. Deliberately descriptive, not advisory.
_PHENOTYPE_SENTENCE: dict[Phenotype, str] = {
    Phenotype.PM: "much lower activity than most people",
    Phenotype.IM: "somewhat lower activity than most people",
    Phenotype.NM: "activity in the usual range",
    Phenotype.RM: "somewhat higher activity than most people",
    Phenotype.URM: "much higher activity than most people",
    Phenotype.UNKNOWN: "activity that could not be determined",
}

_CLOSING = (
    "Discuss this with your doctor or pharmacist before making any change to "
    "your medicines."
)


def _mechanism_text(context: ExplanationContext) -> str:
    """Mechanism background, or an honest statement that we have none."""
    document = context.mechanism
    if document is None:
        return (
            f"No mechanism background is available in this build for "
            f"{context.drug}. The clinical recommendation section above comes "
            "from CPIC via PharmCAT and is the authoritative part of this result."
        )

    # First substantive paragraph of the corpus file, which is the "what the
    # gene product does" opener. Quoting rather than paraphrasing keeps this
    # traceable to a reviewed source. `prose()` (not `snippet()`) so the source
    # file's hard line wrapping does not reach the UI.
    paragraphs = [
        p.strip()
        for p in document.prose().split("\n\n")
        if p.strip() and not p.strip().startswith("#")
    ]
    opener = paragraphs[0] if paragraphs else ""
    return (
        f"{opener}\n\nSource: {document.citation_line}"
        if opener
        else f"Source: {document.citation_line}"
    )


def _variant_rationale(context: ExplanationContext) -> str:
    """State the call and what supported it. Values only, no inference."""
    if context.gene is None or not context.was_called:
        return (
            "No genotype was called for {drug} in this analysis, so there is no "
            "variant-level rationale to report."
        )

    sentences = [
        "PharmCAT called {gene} as {diplotype}, which corresponds to a "
        "{phenotype} result."
    ]
    if context.activity_score is not None:
        sentences.append(f"The reported activity score is {context.activity_score}.")
    # Always the slot, never a branch on what this particular context happens to
    # hold. During pre-generation there are no variants to inspect, and a
    # baked-in "no variants were detected" would then be served to a patient who
    # has several. `variants_display()` already words the empty case correctly.
    sentences.append(
        "The non-reference positions supporting this call were "
        "{detected_variants}."
    )
    return " ".join(sentences)


def _summary(context: ExplanationContext) -> str:
    if context.gene is None:
        return f"{context.drug}: no pharmacogenomic result ({{risk_label}})."
    return "{drug}: {gene} {diplotype} ({phenotype}) — {risk_label}."


def _patient_friendly(context: ExplanationContext) -> str:
    """
    Plain-language paragraph, assembled from fixed clauses.

    Short sentences and everyday words, kept near an 8th-grade reading level to
    match the LLM path's brief.
    """
    parts = [_RISK_SENTENCE.get(context.risk_label, _RISK_SENTENCE[RiskLabel.UNKNOWN])]

    if context.gene is not None and context.phenotype is not Phenotype.UNKNOWN:
        descriptor = _PHENOTYPE_SENTENCE.get(
            context.phenotype, _PHENOTYPE_SENTENCE[Phenotype.UNKNOWN]
        )
        parts.append(
            f"Your {{gene}} gene result shows {descriptor}, which is what this "
            "medicine's handling depends on."
        )
    elif context.risk_label is RiskLabel.UNKNOWN:
        parts.append(
            "That is not a reassuring result or a worrying one — it means this "
            "tool has nothing to say, and the question is still open."
        )

    if context.has_cpic_guidance:
        parts.append(
            "The clinical recommendation shown with this result comes from "
            "published CPIC guidance, not from this tool."
        )

    parts.append(_CLOSING)
    return " ".join(parts)


def generate(context: ExplanationContext) -> Explanation:
    """Build a complete explanation. Cannot fail."""
    return Explanation(
        summary=_summary(context),
        mechanism=_mechanism_text(context),
        variant_rationale=_variant_rationale(context),
        patient_friendly=_patient_friendly(context),
    )
