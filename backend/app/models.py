"""
PharmaGuard — shared JSON contract, expressed as Pydantic v2 models.

This module is the single source of truth for the API schema. The Dart models in
`/app/lib/models/` mirror these one-for-one; if you change anything here, change
them there too (and bump the docs in the root README).

PROVENANCE OF CLINICAL VALUES
    Diplotypes and phenotypes come from PharmCAT (`pharmcat_runner.py`).
    All recommendation text is CPIC's, copied verbatim out of PharmCAT's report
    by `cpic_engine.py` — this codebase never composes clinical prose. The one
    derived value is `risk_label`, produced by the ordered, commented rules in
    `data/label_mapping.yaml`, and every result records which rule fired.

    (Historical note: an earlier phase served hardcoded demo values from a
    `stub_analyzer.py`. That file has been deleted — it contained fabricated
    diplotypes and dosing text and was a standing hazard even unreferenced.)
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# The disclaimer is a constant, not free text: it must appear verbatim on every
# result so the UI can render it prominently and so nobody can mistake this
# project for a regulated clinical tool.
DISCLAIMER = (
    "Research/educational decision support only. "
    "Not a medical device. Not for clinical use."
)


# --------------------------------------------------------------------------- #
# Enums — mirrored as Dart enums in /app/lib/models/enums.dart
# --------------------------------------------------------------------------- #


class RiskLabel(str, Enum):
    """Top-line verdict for a single drug. Drives the card colour in the UI."""

    SAFE = "Safe"
    ADJUST_DOSAGE = "Adjust Dosage"
    TOXIC = "Toxic"
    INEFFECTIVE = "Ineffective"
    UNKNOWN = "Unknown"


class Severity(str, Enum):
    """How bad the consequence is if the risk is ignored."""

    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Phenotype(str, Enum):
    """
    CPIC metaboliser phenotype.

    PM  = Poor metaboliser
    IM  = Intermediate metaboliser
    NM  = Normal metaboliser
    RM  = Rapid metaboliser
    URM = Ultrarapid metaboliser
    """

    PM = "PM"
    IM = "IM"
    NM = "NM"
    RM = "RM"
    URM = "URM"
    UNKNOWN = "Unknown"


class CpicEvidenceLevel(str, Enum):
    """CPIC strength-of-evidence grade for the guideline being cited."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    UNKNOWN = "Unknown"


# --------------------------------------------------------------------------- #
# Leaf models
# --------------------------------------------------------------------------- #


class DetectedVariant(BaseModel):
    """
    One pharmacogenomic variant call.

    TODO(pharmcat): Phase 2 populates this from the PharmCAT `named_allele_matcher`
    output instead of the hard-coded demo table.
    """

    model_config = ConfigDict(extra="forbid")

    # Nullable because structural variants (e.g. a CYP2D6 gene duplication) have
    # no dbSNP identifier.
    rsid: str | None = Field(default=None, examples=["rs3892097"])
    gene: str = Field(examples=["CYP2D6"])
    genotype: str = Field(examples=["0/1"])
    star_allele: str | None = Field(default=None, examples=["*4"])
    function: str = Field(examples=["No function"])


class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_label: RiskLabel
    confidence_score: float = Field(ge=0.0, le=1.0)
    severity: Severity


class PharmacogenomicProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_gene: str = Field(examples=["CYP2D6"])
    diplotype: str = Field(examples=["*1/*1"])
    phenotype: Phenotype
    # Only defined for genes that use an activity-score model (CYP2D6, CYP2C9,
    # DPYD). Null everywhere else — do not coerce to 0.0, that means something.
    activity_score: float | None = None
    detected_variants: list[DetectedVariant] = Field(default_factory=list)


class ClinicalRecommendation(BaseModel):
    """
    What a clinician should do. Every field here is STUB text in Phase 1.

    TODO(pharmcat): Phase 2 replaces this with the matched CPIC guideline
    recommendation for the (gene, phenotype, drug) triple.
    """

    model_config = ConfigDict(extra="forbid")

    action: str
    dosing_guidance: str
    cpic_recommendation: str
    cpic_evidence_level: CpicEvidenceLevel
    alternatives: list[str] = Field(default_factory=list)
    # "STUB" now; becomes e.g. "CPIC 2021 Guideline for CYP2D6 and Codeine" later.
    source: str = "STUB"


class LlmGeneratedExplanation(BaseModel):
    """
    Narrative layer. TODO(llm): Phase 3 generates these fields with a RAG-grounded
    LLM call over /rag-corpus; today they are canned strings.
    """

    model_config = ConfigDict(extra="forbid")

    summary: str
    mechanism: str
    variant_rationale: str
    patient_friendly: str
    disclaimer: str = DISCLAIMER


class PerDrugResult(BaseModel):
    """One entry in `analyses` — exactly one per drug the caller asked about."""

    model_config = ConfigDict(extra="forbid")

    drug: str
    risk_assessment: RiskAssessment
    pharmacogenomic_profile: PharmacogenomicProfile
    clinical_recommendation: ClinicalRecommendation
    llm_generated_explanation: LlmGeneratedExplanation


class QualityMetrics(BaseModel):
    """Pipeline telemetry — lets the UI show *how much to trust* the result."""

    model_config = ConfigDict(extra="forbid")

    vcf_parsing_success: bool
    variants_detected_count: int = Field(ge=0)
    processing_time_ms: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    """The 200 body of POST /analyze."""

    model_config = ConfigDict(extra="forbid")

    # TODO(pharmcat): derive from the VCF sample column once real parsing lands.
    patient_id: str = "PATIENT_001"
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    analyses: list[PerDrugResult]
    quality_metrics: QualityMetrics


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "ok"
