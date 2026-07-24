"""
Code-composed factual fields.

WHY THIS EXISTS

`variant_rationale` states what the genotype call actually was. That is a
factual claim about a specific patient, and it was being written by a language
model asked to emit `{diplotype}` placeholders for later substitution. The model
complied 4 times out of 14: ten shipped entries had no diplotype slot at all, so
they could not show the patient's genotype, and the runtime slot verifier — the
Phase-4 check that catches a wrong genotype being injected into reviewed prose —
had nothing to verify and was inert for those cases.

Prompting harder was the wrong fix. A prose model is being asked to emit
templating syntax, which is not a prose task, and no amount of instruction makes
compliance guaranteed. So authorship is reassigned instead:

    variant_rationale        composed HERE, from the PharmCAT profile
    summary/mechanism/
      patient_friendly       model-generated, genotype-agnostic
    clinical_recommendation  verbatim CPIC, never model-authored

Composed at **request time**, from the profile in the response being returned.
That is what makes the guarantee structural rather than procedural: the sentence
cannot disagree with the profile, because it is derived from it in the same
call. Storing a pre-rendered one would reintroduce the possibility of drift.

The runtime slot verifier stays as defence in depth. It should now never fire on
this field — but a check that becomes unnecessary is not a check worth deleting,
because "should never fire" is exactly the assumption worth monitoring.
"""

from __future__ import annotations

from .context import ExplanationContext


def compose_variant_rationale(context: ExplanationContext) -> str:
    """
    State the genotype call and what supported it. Values only, no inference.

    Returns finished prose — no placeholders, nothing left to substitute. Every
    value comes from `context`, so the sentence and the response's own
    `pharmacogenomic_profile` cannot disagree.
    """
    if context.gene is None or not context.was_called:
        return (
            f"No genotype was called for {context.drug} in this analysis, so "
            "there is no variant-level rationale to report."
        )

    sentences = [
        f"PharmCAT called {context.gene} as {context.diplotype_display}, which "
        f"corresponds to a {context.phenotype_display} result."
    ]
    if context.activity_score is not None:
        sentences.append(f"The reported activity score is {context.activity_score}.")
    sentences.append(
        "The non-reference positions supporting this call were "
        f"{context.variants_display()}."
    )
    return " ".join(sentences)
