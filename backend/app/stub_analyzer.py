"""
PharmaGuard — STUB analyzer.

============================================================================
EVERYTHING IN THIS FILE IS FAKE. It exists only to prove the FastAPI <-> Flutter
seam with a schema-valid, visually varied payload. No genotype is read, no
guideline is consulted, no model is called.

Phase 2 (TODO(pharmcat)) replaces `_DEMO_TABLE` with:
    VCF -> PharmCAT named_allele_matcher -> diplotype
        -> CPIC phenotype mapping -> CPIC guideline lookup
Phase 3 (TODO(llm)) replaces `llm_generated_explanation` with a RAG-grounded
generation over /rag-corpus.

Deliberate constraint: the stub contains NO numeric dosing (no mg, no %, no
"reduce by N"). Fabricated dose numbers are the one thing that could make a demo
genuinely dangerous if screenshotted out of context, so the guidance strings stay
qualitative until real CPIC text is wired in.
============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import (
    ClinicalRecommendation,
    CpicEvidenceLevel,
    DetectedVariant,
    LlmGeneratedExplanation,
    PerDrugResult,
    PharmacogenomicProfile,
    Phenotype,
    RiskAssessment,
    RiskLabel,
    Severity,
)


@dataclass(frozen=True)
class _DemoEntry:
    """One row of the hard-coded demo table. STUB — see module docstring."""

    gene: str
    diplotype: str
    phenotype: Phenotype
    risk_label: RiskLabel
    severity: Severity
    confidence: float
    activity_score: float | None
    variants: list[DetectedVariant]
    # Narrative bits, all canned. TODO(llm): generate these instead.
    mechanism: str
    variant_rationale: str
    patient_friendly: str
    action: str
    alternatives: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# THE DEMO TABLE — six drugs, chosen so the UI shows every card colour.
# rsIDs are real public dbSNP identifiers (they are stable reference labels, not
# clinical claims); the genotypes and diplotypes attached to them are invented.
# --------------------------------------------------------------------------- #

_DEMO_TABLE: dict[str, _DemoEntry] = {
    # --- Toxic (red) : too much active drug ---------------------------------
    "codeine": _DemoEntry(
        gene="CYP2D6",
        diplotype="*1/*2xN",  # STUB: gene duplication => ultrarapid
        phenotype=Phenotype.URM,
        risk_label=RiskLabel.TOXIC,
        severity=Severity.HIGH,
        confidence=0.88,  # STUB: not a calibrated probability
        activity_score=3.0,  # STUB
        variants=[
            DetectedVariant(
                rsid="rs16947",
                gene="CYP2D6",
                genotype="1/1",
                star_allele="*2",
                function="Normal function",
            ),
            DetectedVariant(
                # Structural variant: no dbSNP id exists, hence rsid=None.
                rsid=None,
                gene="CYP2D6",
                genotype="N/A",
                star_allele="*2xN",
                function="Increased function (gene duplication)",
            ),
        ],
        mechanism=(
            "STUB: CYP2D6 converts codeine into morphine. An ultrarapid "
            "metaboliser performs this conversion faster than normal, so a "
            "standard dose yields unusually high morphine exposure."
        ),
        variant_rationale=(
            "STUB: a duplicated normal-function allele (*2xN) was called "
            "alongside *2, giving an activity score above the normal range."
        ),
        patient_friendly=(
            "STUB: your body appears to turn codeine into morphine faster than "
            "most people. That can make a normal dose feel much stronger and "
            "raise the chance of side effects. Talk to your doctor before "
            "taking codeine."
        ),
        action="Avoid codeine; select an alternative analgesic.",
        alternatives=["morphine", "non-opioid analgesia"],
    ),
    # --- Adjust Dosage (amber) : reduced clearance --------------------------
    "warfarin": _DemoEntry(
        gene="CYP2C9",
        diplotype="*1/*2",
        phenotype=Phenotype.IM,
        risk_label=RiskLabel.ADJUST_DOSAGE,
        severity=Severity.MODERATE,
        confidence=0.82,
        activity_score=1.5,  # STUB
        variants=[
            DetectedVariant(
                rsid="rs1799853",
                gene="CYP2C9",
                genotype="0/1",
                star_allele="*2",
                function="Decreased function",
            ),
        ],
        mechanism=(
            "STUB: CYP2C9 clears the more active warfarin enantiomer. Reduced "
            "enzyme activity slows clearance, so a standard dose produces a "
            "stronger anticoagulant effect."
        ),
        variant_rationale=(
            "STUB: one decreased-function allele (*2) was called, placing this "
            "sample in the intermediate-metaboliser range."
        ),
        patient_friendly=(
            "STUB: warfarin is likely to stay in your body longer than average, "
            "so the usual starting dose may be too strong for you. Your doctor "
            "may start lower and monitor your blood tests more closely."
        ),
        action="Dose adjustment and closer INR monitoring likely warranted.",
        alternatives=["direct oral anticoagulant (clinician's choice)"],
    ),
    # --- Ineffective (red) : prodrug never activated ------------------------
    "clopidogrel": _DemoEntry(
        gene="CYP2C19",
        diplotype="*2/*2",
        phenotype=Phenotype.PM,
        risk_label=RiskLabel.INEFFECTIVE,
        severity=Severity.HIGH,
        confidence=0.91,
        activity_score=0.0,  # STUB
        variants=[
            DetectedVariant(
                rsid="rs4244285",
                gene="CYP2C19",
                genotype="1/1",
                star_allele="*2",
                function="No function",
            ),
        ],
        mechanism=(
            "STUB: clopidogrel is a prodrug that CYP2C19 must activate. With no "
            "functional enzyme, little active metabolite is formed and platelet "
            "inhibition is reduced."
        ),
        variant_rationale=(
            "STUB: two no-function alleles (*2/*2) were called, giving a poor-"
            "metaboliser phenotype."
        ),
        patient_friendly=(
            "STUB: your body may not activate clopidogrel properly, which means "
            "it might not protect you as intended. A different antiplatelet "
            "medicine may work better — ask your doctor."
        ),
        action="Consider an alternative antiplatelet agent.",
        alternatives=["prasugrel", "ticagrelor"],
    ),
    # --- Safe (green) ------------------------------------------------------
    "simvastatin": _DemoEntry(
        gene="SLCO1B1",
        diplotype="*1/*1",
        phenotype=Phenotype.NM,
        risk_label=RiskLabel.SAFE,
        severity=Severity.NONE,
        confidence=0.95,
        activity_score=None,  # SLCO1B1 has no activity-score model
        variants=[
            DetectedVariant(
                rsid="rs4149056",
                gene="SLCO1B1",
                genotype="0/0",
                star_allele="*1",
                function="Normal function",
            ),
        ],
        mechanism=(
            "STUB: SLCO1B1 transports simvastatin into the liver. Normal "
            "transporter function keeps muscle exposure in the expected range."
        ),
        variant_rationale=(
            "STUB: no decreased-function SLCO1B1 alleles were called; the "
            "reference diplotype *1/*1 was assigned."
        ),
        patient_friendly=(
            "STUB: nothing in this (simulated) result suggests simvastatin would "
            "behave unusually for you. Keep taking it as prescribed."
        ),
        action="No genotype-driven change indicated.",
        alternatives=[],
    ),
    # --- Toxic (red) : critical severity ------------------------------------
    "azathioprine": _DemoEntry(
        gene="TPMT",
        diplotype="*3A/*3A",
        phenotype=Phenotype.PM,
        risk_label=RiskLabel.TOXIC,
        severity=Severity.CRITICAL,
        confidence=0.90,
        activity_score=None,
        variants=[
            DetectedVariant(
                rsid="rs1800460",
                gene="TPMT",
                genotype="1/1",
                star_allele="*3A",
                function="No function",
            ),
            DetectedVariant(
                rsid="rs1142345",
                gene="TPMT",
                genotype="1/1",
                star_allele="*3A",
                function="No function",
            ),
        ],
        mechanism=(
            "STUB: TPMT inactivates thiopurine metabolites. Without functional "
            "enzyme those metabolites accumulate in bone marrow, risking severe "
            "myelosuppression."
        ),
        variant_rationale=(
            "STUB: two no-function alleles (*3A/*3A) were called, giving a poor-"
            "metaboliser phenotype."
        ),
        patient_friendly=(
            "STUB: this (simulated) result suggests azathioprine could build up "
            "to harmful levels and affect your blood cell counts. This is one to "
            "raise with your doctor before starting treatment."
        ),
        action="Avoid standard dosing; specialist review required.",
        alternatives=["non-thiopurine immunosuppressant (clinician's choice)"],
    ),
    # --- Adjust Dosage (amber) : high severity ------------------------------
    "fluorouracil": _DemoEntry(
        gene="DPYD",
        diplotype="*1/*2A",
        phenotype=Phenotype.IM,
        risk_label=RiskLabel.ADJUST_DOSAGE,
        severity=Severity.HIGH,
        confidence=0.85,
        activity_score=1.0,  # STUB
        variants=[
            DetectedVariant(
                rsid="rs3918290",
                gene="DPYD",
                genotype="0/1",
                star_allele="*2A",
                function="No function",
            ),
        ],
        mechanism=(
            "STUB: DPD (encoded by DPYD) breaks down fluorouracil. Partial DPD "
            "deficiency slows that breakdown and increases exposure to the drug."
        ),
        variant_rationale=(
            "STUB: one no-function allele (*2A) was called against a normal-"
            "function allele, indicating partial DPD deficiency."
        ),
        patient_friendly=(
            "STUB: your body may clear this chemotherapy drug more slowly than "
            "average, so a standard dose could cause stronger side effects. Your "
            "oncology team would normally adjust for this."
        ),
        action="Reduced starting dose with titration likely warranted.",
        alternatives=["non-fluoropyrimidine regimen (clinician's choice)"],
    ),
}


# Exposed so /health and the docs can report what the demo actually covers.
SUPPORTED_DRUGS: tuple[str, ...] = tuple(sorted(_DEMO_TABLE))


def _stub_recommendation(entry: _DemoEntry) -> ClinicalRecommendation:
    """Build the STUB clinical block. TODO(pharmcat): real CPIC lookup."""
    return ClinicalRecommendation(
        action=entry.action,
        # No numbers, on purpose — see module docstring.
        dosing_guidance=(
            "STUB: no dosing numbers are produced in Phase 1. "
            "TODO(pharmcat): populate from the CPIC guideline table."
        ),
        cpic_recommendation=(
            f"STUB: a CPIC guideline exists for {entry.gene} and this drug, but "
            "its text is not yet loaded. TODO(pharmcat): substitute the real "
            "recommendation for this gene/phenotype/drug triple."
        ),
        # STUB grade. TODO(pharmcat): read the actual assigned level.
        cpic_evidence_level=CpicEvidenceLevel.UNKNOWN,
        alternatives=list(entry.alternatives),
        source="STUB",
    )


def _unknown_result(drug: str) -> PerDrugResult:
    """
    Fallback for any drug outside the demo table.

    This is the whole point of the Unknown enum members: an unrecognised drug is
    a normal, well-typed answer, never a 500.
    """
    return PerDrugResult(
        drug=drug,
        risk_assessment=RiskAssessment(
            risk_label=RiskLabel.UNKNOWN,
            confidence_score=0.0,
            severity=Severity.NONE,
        ),
        pharmacogenomic_profile=PharmacogenomicProfile(
            primary_gene="Unknown",
            diplotype="Unknown",
            phenotype=Phenotype.UNKNOWN,
            activity_score=None,
            detected_variants=[],
        ),
        clinical_recommendation=ClinicalRecommendation(
            action=(
                f"No pharmacogenomic association is available for '{drug}' in "
                "this build."
            ),
            dosing_guidance="Not applicable — drug not covered.",
            cpic_recommendation=(
                "No CPIC guideline is loaded for this drug. TODO(pharmcat): the "
                "Phase 2 lookup will distinguish 'no guideline exists' from "
                "'guideline exists but is not loaded'."
            ),
            cpic_evidence_level=CpicEvidenceLevel.UNKNOWN,
            alternatives=[],
            source="STUB",
        ),
        llm_generated_explanation=LlmGeneratedExplanation(
            summary=f"'{drug}' is not in the Phase 1 demo drug set.",
            mechanism="Not available — no gene association loaded for this drug.",
            variant_rationale="No variants were evaluated for this drug.",
            patient_friendly=(
                f"We do not have genetic information about '{drug}' in this "
                "demo. That is not a safety finding either way — it simply "
                "means this tool has nothing to say about it."
            ),
        ),
    )


def analyze_drug(drug: str) -> PerDrugResult:
    """
    Return a STUB PerDrugResult for one drug name.

    Lookup is case-insensitive and whitespace-tolerant. Anything not in the demo
    table comes back as a well-formed Unknown result.

    TODO(pharmcat): this signature is wrong for Phase 2 — the real analyzer needs
    the parsed variant calls too, i.e. analyze_drug(drug, variant_calls).
    """
    key = drug.strip().lower()
    entry = _DEMO_TABLE.get(key)
    if entry is None:
        return _unknown_result(drug.strip())

    return PerDrugResult(
        # Echo the canonical (lower-cased) name so clients get stable keys.
        drug=key,
        risk_assessment=RiskAssessment(
            risk_label=entry.risk_label,
            confidence_score=entry.confidence,
            severity=entry.severity,
        ),
        pharmacogenomic_profile=PharmacogenomicProfile(
            primary_gene=entry.gene,
            diplotype=entry.diplotype,
            phenotype=entry.phenotype,
            activity_score=entry.activity_score,
            detected_variants=list(entry.variants),
        ),
        clinical_recommendation=_stub_recommendation(entry),
        llm_generated_explanation=LlmGeneratedExplanation(
            summary=(
                f"STUB: {key} — {entry.gene} {entry.diplotype} "
                f"({entry.phenotype.value}) → {entry.risk_label.value}."
            ),
            mechanism=entry.mechanism,
            variant_rationale=entry.variant_rationale,
            patient_friendly=entry.patient_friendly,
        ),
    )


def count_stub_variants(results: list[PerDrugResult]) -> int:
    """
    Total variant calls across all results, for `quality_metrics`.

    TODO(pharmcat): Phase 2 counts variants found in the VCF itself, which is a
    property of the *file*, not of the drugs requested.
    """
    return sum(len(r.pharmacogenomic_profile.detected_variants) for r in results)
