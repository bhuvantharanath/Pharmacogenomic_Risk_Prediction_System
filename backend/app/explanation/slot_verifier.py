"""
PharmaGuard — runtime slot verification.

THE GAP THIS CLOSES
    In `static` mode — the deployed default — the faithfulness guard is a
    BUILD-TIME gate. `scripts/pregenerate_explanations.py` runs `guard.check()`
    over the generated prose, the verdict is stored in `explanations.json`, and
    at request time we replay that verdict rather than re-running the check.
    That is sound for the prose, because the prose does not change.

    But the prose ships with holes in it. `{diplotype}` and `{detected_variants}`
    are filled per request, from the live PharmCAT call, *after* the stored
    verdict was recorded. Nothing checked that the values injected into a
    reviewed sentence were the values PharmCAT actually returned for this
    patient. A bug in context assembly — a stale cache, a mis-threaded object,
    an off-by-one over a list of drugs — would produce a fluent, reviewed,
    guard-passed sentence stating the wrong genotype.

WHAT THIS DOES
    After slot filling, re-derive what each placeholder *should* have become
    from the response's own `pharmacogenomic_profile`, and confirm the filled
    text contains exactly that. Same source of truth the user sees rendered in
    the card above the explanation, so the two can never disagree.

WHAT THIS IS NOT
    Not a second faithfulness guard. It says nothing about whether the prose is
    clinically right, and it cannot: the prose was written offline. It answers
    one narrow question — "are the patient-specific values in this sentence the
    ones we just computed?" — which is exactly the question the build-time guard
    structurally cannot answer.

FAILURE BEHAVIOUR
    Fall back to the deterministic template generator and record a warning in
    `quality_metrics`. Never serve a mismatched explanation: a wrong diplotype
    inside otherwise-correct clinical prose is worse than plainer text, because
    it is more believable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import PharmacogenomicProfile
from .context import SLOT_PATTERN, Explanation, ExplanationContext


@dataclass
class SlotVerification:
    """Outcome of checking one explanation's injected values."""

    passed: bool
    mismatches: list[str] = field(default_factory=list)
    #: Slots that were actually present in the stored prose and therefore
    #: verified. Recorded so a "passed" result cannot be mistaken for
    #: "we checked everything" when the prose used no slots at all.
    verified_slots: set[str] = field(default_factory=set)

    @property
    def summary(self) -> str:
        if self.passed:
            checked = ", ".join(sorted(self.verified_slots)) or "none present"
            return f"slot verification passed (checked: {checked})"
        return (
            f"slot verification FAILED: {len(self.mismatches)} mismatch(es) — "
            + "; ".join(self.mismatches)
        )


def _expected_values(
    context: ExplanationContext, profile: PharmacogenomicProfile
) -> dict[str, str]:
    """
    What each slot must have become, derived from the response's own profile.

    Deliberately re-derived from `profile` rather than reused from
    `context.slot_values()`. Comparing a value against itself would pass
    unconditionally and verify nothing; the point is to cross-check the text
    against the object the client renders.
    """
    from .context import ExplanationContext as _Ctx

    # Rebuild a context whose patient-specific fields come from the profile,
    # then ask it for the same slot values the filler would have produced.
    mirror = _Ctx(
        drug=context.drug,
        risk_label=context.risk_label,
        phenotype=profile.phenotype,
        gene=None if profile.primary_gene == "Unknown" else profile.primary_gene,
        diplotype=None if profile.diplotype == "Unknown" else profile.diplotype,
        activity_score=profile.activity_score,
        detected_variants=list(profile.detected_variants),
        phenotype_label=context.phenotype_label,
    )
    return mirror.slot_values()


def verify(
    filled: Explanation,
    unfilled: Explanation,
    context: ExplanationContext,
    profile: PharmacogenomicProfile,
) -> SlotVerification:
    """
    Confirm every value injected into `filled` matches `profile`.

    `unfilled` is needed to know which slots the stored prose actually used —
    checking for a value that was never meant to appear would be meaningless.
    """
    expected = _expected_values(context, profile)
    mismatches: list[str] = []
    verified: set[str] = set()

    for field_name, unfilled_text in unfilled.fields().items():
        slots = set(SLOT_PATTERN.findall(unfilled_text))
        if not slots:
            continue
        filled_text = filled.fields()[field_name]

        for slot in sorted(slots):
            if slot not in expected:
                # An unknown placeholder is the build-time guard's business
                # (it rejects them); nothing to cross-check here.
                continue
            wanted = expected[slot]
            if wanted and wanted not in filled_text:
                mismatches.append(
                    f"{field_name}.{{{slot}}} should contain {wanted!r} "
                    f"(from pharmacogenomic_profile) but does not"
                )
            else:
                verified.add(slot)

    return SlotVerification(
        passed=not mismatches, mismatches=mismatches, verified_slots=verified
    )
