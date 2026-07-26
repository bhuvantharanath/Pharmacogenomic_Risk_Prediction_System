"""
PharmaGuard — the context object every explanation generator sees.

`ExplanationContext` is the **single source of truth for what may be said**. The
faithfulness guard validates generated text against exactly this object, so if a
fact is not reachable from here, it is a hallucination by definition.

That makes the class deliberately closed: it carries PharmCAT's CPIC text, the
called genotype, and the retrieved mechanism snippet, and nothing else. Adding a
field widens what the model is permitted to assert, so add carefully.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..models import DetectedVariant, LlmGeneratedExplanation, Phenotype, RiskLabel
from ..retrieval import MechanismDocument

# --------------------------------------------------------------------------- #
# Slots
#
# Pre-generated explanations are reviewed once and then reused, so they must not
# contain patient-specific values. Those are written as placeholders and filled
# deterministically at runtime — the reviewed clinical prose never changes.
# --------------------------------------------------------------------------- #

SLOT_PATTERN = re.compile(r"\{([a-z_]+)\}")

#: The only placeholders a pre-generated explanation may contain.
#:
#: `risk_label` is a slot rather than baked-in text for a subtle but important
#: reason: entries are keyed by (drug, phenotype), while the risk label is
#: derived at runtime from the CPIC text by `cpic_engine`. Those are not the
#: same function. Clopidogrel + Poor Metaboliser, for instance, is labelled
#: `Ineffective`, which a phenotype-keyed guess would not predict. Baking a
#: label into reviewed prose would let the summary contradict the card badge
#: sitting directly above it.
ALLOWED_SLOTS: frozenset[str] = frozenset(
    {"diplotype", "detected_variants", "gene", "drug", "phenotype", "risk_label"}
)


@dataclass(frozen=True)
class ExplanationContext:
    """Everything a generator is allowed to know about one drug result."""

    drug: str
    risk_label: RiskLabel
    phenotype: Phenotype
    gene: str | None = None
    diplotype: str | None = None
    activity_score: float | None = None
    detected_variants: list[DetectedVariant] = field(default_factory=list)

    # --- PharmCAT's CPIC output, verbatim ---------------------------------- #
    cpic_recommendation: str = ""
    cpic_implications: list[str] = field(default_factory=list)
    cpic_strength: str = ""
    cpic_evidence_level: str = "Unknown"

    # --- Retrieved mechanism background ------------------------------------ #
    mechanism: MechanismDocument | None = None

    # PharmCAT's raw phenotype wording, e.g. "Poor Metabolizer". Kept alongside
    # the enum because it reads better in prose than "PM".
    phenotype_label: str = ""

    # Every equally-likely diplotype PharmCAT returned. Length > 1 means the
    # FUNCTION is known while the exact star alleles are not — a state the prose
    # must state rather than paper over by naming one of them.
    candidate_diplotypes: list[str] = field(default_factory=list)

    @property
    def diplotype_is_ambiguous(self) -> bool:
        return len(self.candidate_diplotypes) > 1

    @property
    def gene_display(self) -> str:
        return self.gene or "the relevant gene"

    @property
    def diplotype_display(self) -> str:
        return self.diplotype or "not called"

    #: Spelled-out phenotype names, for when PharmCAT's own wording is absent.
    #: The Python `Phenotype` enum carries only the code (unlike the Dart mirror,
    #: which has a `label`), so the long form lives here.
    _PHENOTYPE_NAMES = {
        "PM": "poor metaboliser",
        "IM": "intermediate metaboliser",
        "NM": "normal metaboliser",
        "RM": "rapid metaboliser",
        "URM": "ultrarapid metaboliser",
    }

    @property
    def phenotype_display(self) -> str:
        if self.phenotype is Phenotype.UNKNOWN:
            return "unknown"
        return self.phenotype_label or self._PHENOTYPE_NAMES.get(
            self.phenotype.value, self.phenotype.value
        )

    @property
    def has_cpic_guidance(self) -> bool:
        return bool(self.cpic_recommendation.strip())

    @property
    def was_called(self) -> bool:
        """
        Did PharmCAT produce a diplotype for this gene?

        Not simply `diplotype is not None`: during offline pre-generation the
        diplotype is the literal placeholder `"{diplotype}"`, because the real
        value differs per patient. Generators must take the "was called" branch
        in that situation, or the reviewed prose ends up asserting that no
        genotype was found for every patient who has one.
        """
        if self.phenotype is Phenotype.UNKNOWN:
            return False
        return bool(self.diplotype)

    @property
    def mechanism_snippet(self) -> str:
        return self.mechanism.snippet() if self.mechanism else ""

    def variants_display(self) -> str:
        """
        Human-readable variant list, used to fill the `{detected_variants}` slot.

        Deliberately plain: rsID, genotype, gene. No interpretation — the whole
        point of the slot is that it is mechanical substitution of values that
        came straight from PharmCAT.
        """
        if not self.detected_variants:
            return "no non-reference variants were detected"
        parts = []
        for variant in self.detected_variants:
            label = variant.rsid or "a structural variant"
            parts.append(f"{label} ({variant.genotype})")
        if len(parts) == 1:
            return parts[0]
        return ", ".join(parts[:-1]) + f" and {parts[-1]}"

    def slot_values(self) -> dict[str, str]:
        """Concrete values for every allowed placeholder."""
        return {
            "diplotype": self.diplotype_display,
            "detected_variants": self.variants_display(),
            "gene": self.gene_display,
            "drug": self.drug,
            "phenotype": self.phenotype_display,
            "risk_label": self.risk_label.value,
        }

    # ----------------------------------------------------------------------- #
    # Guard support
    # ----------------------------------------------------------------------- #

    def grounding_text(self) -> str:
        """
        Everything the generator was allowed to see, as one searchable blob.

        The guard checks extracted entities against this string. It must contain
        every value a faithful explanation could legitimately mention — miss
        something and the guard produces false positives; include something the
        generator never saw and the guard produces false negatives.
        """
        parts: list[str] = [
            self.drug,
            self.risk_label.value,
            self.phenotype.value,
            self.phenotype_display,
            self.gene or "",
            self.diplotype or "",
            "" if self.activity_score is None else str(self.activity_score),
            self.cpic_recommendation,
            *self.cpic_implications,
            self.cpic_strength,
            self.cpic_evidence_level,
            self.mechanism_snippet,
        ]
        if self.mechanism is not None:
            # The document's provenance metadata is part of the supplied
            # context: the template generator quotes the citation line verbatim,
            # so its year and PMID must be groundable. Without this the guard
            # flags its own fallback text as hallucinated.
            parts += [
                self.mechanism.citation_line,
                self.mechanism.source_guideline,
                self.mechanism.source_url,
            ]
        for variant in self.detected_variants:
            parts += [
                variant.rsid or "",
                variant.gene,
                variant.genotype,
                variant.star_allele or "",
                variant.function,
            ]
        return "\n".join(p for p in parts if p)

    def prompt_payload(self) -> dict[str, object]:
        """The structured context handed to the LLM. Nothing else is sent."""
        return {
            "drug": self.drug,
            "gene": self.gene,
            "diplotype": self.diplotype,
            "phenotype_code": self.phenotype.value,
            "phenotype_label": self.phenotype_display,
            "activity_score": self.activity_score,
            "detected_variants": [
                {
                    "rsid": v.rsid,
                    "gene": v.gene,
                    "genotype": v.genotype,
                    "star_allele": v.star_allele,
                    "function": v.function,
                }
                for v in self.detected_variants
            ],
            "risk_label": self.risk_label.value,
            "cpic_recommendation": self.cpic_recommendation,
            "cpic_implications": self.cpic_implications,
            "cpic_strength_of_recommendation": self.cpic_strength,
            "cpic_evidence_level": self.cpic_evidence_level,
            "mechanism_background": self.mechanism_snippet,
        }


@dataclass(frozen=True)
class Explanation:
    """The four narrative fields, before slot filling."""

    summary: str
    mechanism: str
    variant_rationale: str
    patient_friendly: str

    def fields(self) -> dict[str, str]:
        return {
            "summary": self.summary,
            "mechanism": self.mechanism,
            "variant_rationale": self.variant_rationale,
            "patient_friendly": self.patient_friendly,
        }

    def fill_slots(self, context: ExplanationContext) -> "Explanation":
        """
        Substitute `{placeholders}` with this patient's values.

        Unknown placeholders are left **visible** rather than blanked: a stray
        `{foo}` in the UI is an obvious bug report, whereas silently deleting it
        would produce a sentence that reads fine but has lost its subject.
        """
        values = context.slot_values()

        def substitute(text: str) -> str:
            return SLOT_PATTERN.sub(
                lambda m: values.get(m.group(1), m.group(0)), text
            )

        return Explanation(
            summary=substitute(self.summary),
            mechanism=substitute(self.mechanism),
            variant_rationale=substitute(self.variant_rationale),
            patient_friendly=substitute(self.patient_friendly),
        )

    def to_contract(self) -> LlmGeneratedExplanation:
        """Convert to the public contract model (which adds the disclaimer)."""
        return LlmGeneratedExplanation(
            summary=self.summary,
            mechanism=self.mechanism,
            variant_rationale=self.variant_rationale,
            patient_friendly=self.patient_friendly,
        )


def unknown_slots(text: str) -> set[str]:
    """Placeholders in `text` that slot filling would not resolve."""
    return {name for name in SLOT_PATTERN.findall(text) if name not in ALLOWED_SLOTS}
