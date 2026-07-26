"""
PharmaGuard — typed intermediate models for PharmCAT's report JSON.

These sit between PharmCAT's output and our public API contract. They exist so
that exactly one module has to know PharmCAT's JSON shape; `cpic_engine.py` and
`main.py` work against these types instead.

Everything here mirrors PharmCAT **3.4.0** `-reporterJson` output. The shapes
were read off real output, not documentation — see `infra/PHARMCAT_NOTES.md`
for the commands used and a map of the JSON.

Nothing in this file interprets clinical meaning. It only reports what PharmCAT
said, including when what PharmCAT said is "no result".
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CallStatus(str, Enum):
    """
    How much to trust a gene call. Drives `confidence_score` downstream.

    DEFINITE  - exactly one diplotype matched.
    AMBIGUOUS - several diplotypes matched equally well; PharmCAT cannot choose.
    NO_CALL   - the matcher ran but could not call (usually missing positions).
    NOT_ATTEMPTED - PharmCAT did not try. In practice this is CYP2D6, which is
                not callable from an unphased VCF without copy-number data.
    """

    DEFINITE = "definite"
    AMBIGUOUS = "ambiguous"
    NO_CALL = "no_call"
    NOT_ATTEMPTED = "not_attempted"


class PharmcatVariant(BaseModel):
    """One position PharmCAT looked at, as reported under `genes.<G>.variants`."""

    model_config = ConfigDict(extra="ignore")

    position: int
    chromosome: str
    dbSnpId: str | None = None
    call: str | None = None
    referenceAllele: str | None = None
    # Named alleles this position helps define, e.g. ["*1", "*4", "*17"].
    alleles: list[str] = Field(default_factory=list)


class PharmcatGeneCall(BaseModel):
    """PharmCAT's call for one gene, normalised."""

    model_config = ConfigDict(extra="ignore")

    gene: str
    status: CallStatus
    # "*2/*2", "Reference/Reference", or None when uncalled.
    diplotype: str | None = None
    # All candidate diplotypes; length > 1 means AMBIGUOUS.
    candidate_diplotypes: list[str] = Field(default_factory=list)
    # PharmCAT's own phenotype wording, e.g. "Poor Metabolizer",
    # "Normal Function", "No Result". Deliberately NOT mapped to our enum here.
    phenotype_raw: str | None = None
    activity_score: float | None = None
    # The key CPIC recommendations are looked up by, e.g. ["Poor Metabolizer"].
    # From PharmCAT's `recommendationDiplotypes`, not from the called diplotype:
    # for a compound genotype those differ, and only this one finds a CPIC row.
    lookup_keys: list[str] = Field(default_factory=list)
    # PharmCAT's reduced diplotype that the CPIC row was found by. Differs from
    # `diplotype` only when a compound allele had to be split to assign an
    # activity score (DPYD in practice). Present so a reviewer can see why a
    # recommendation applies without re-deriving PharmCAT's reduction.
    recommendation_diplotype: str | None = None
    # Every DISTINCT phenotype across all candidate diplotypes, `n/a` excluded.
    # Length > 1 means the candidates disagree about function, which is different
    # from — and more consequential than — disagreeing about identity.
    candidate_phenotypes: list[str] = Field(default_factory=list)
    # The corresponding CPIC lookup keys, so a guideline row can still be found
    # when the candidates agree on function but not on the exact diplotype.
    candidate_lookup_keys: list[str] = Field(default_factory=list)
    # Per-allele function text, e.g. "No function".
    allele_functions: list[str] = Field(default_factory=list)
    variants: list[PharmcatVariant] = Field(default_factory=list)
    # PharmCAT's own messages plus any we add while parsing.
    warnings: list[str] = Field(default_factory=list)

    @property
    def is_called(self) -> bool:
        return self.status in (CallStatus.DEFINITE, CallStatus.AMBIGUOUS)


class CpicAnnotation(BaseModel):
    """
    One CPIC recommendation row, verbatim from PharmCAT.

    Every string here is PharmCAT's, copied not composed. `cpic_engine.py` may
    choose *between* annotations but must not rewrite their text.
    """

    model_config = ConfigDict(extra="ignore")

    # e.g. "Avoid clopidogrel if possible. Use prasugrel or ticagrelor..."
    drug_recommendation: str | None = None
    # e.g. ["CYP2C19: Significantly reduced clopidogrel active metabolite..."]
    implications: list[str] = Field(default_factory=list)
    # CPIC *strength of recommendation*: Strong | Moderate | Optional |
    # Unspecified. NOTE: this is NOT the CPIC A/B/C/D level of evidence, which
    # PharmCAT's report JSON does not carry. See cpic_engine.py.
    classification: str | None = None
    # e.g. "CVI ACS PCI" — the patient population the row applies to.
    population: str | None = None
    # Structured flags PharmCAT sets alongside the free text.
    dosing_information: bool = False
    alternate_drug_available: bool = False
    other_prescribing_guidance: bool = False
    # e.g. [{"CYP2C19": "Poor Metabolizer"}]
    lookup_key: list[dict[str, str]] = Field(default_factory=list)


class CpicDrugGuideline(BaseModel):
    """All CPIC guidance PharmCAT reported for one drug."""

    model_config = ConfigDict(extra="ignore")

    drug: str
    guideline_name: str | None = None
    guideline_url: str | None = None
    # Empty when PharmCAT found no annotation matching the called phenotype —
    # which is the normal signal for "no CPIC guidance applies here".
    annotations: list[CpicAnnotation] = Field(default_factory=list)
    # Genes this guideline keys off, e.g. ["CYP2C19"].
    genes: list[str] = Field(default_factory=list)


class PharmcatReport(BaseModel):
    """The parsed whole of one PharmCAT run."""

    model_config = ConfigDict(extra="ignore")

    pharmcat_version: str
    data_version: str | None = None
    timestamp: str | None = None
    sample_id: str | None = None
    genes: dict[str, PharmcatGeneCall] = Field(default_factory=dict)
    drugs: dict[str, CpicDrugGuideline] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    def gene(self, symbol: str) -> PharmcatGeneCall | None:
        return self.genes.get(symbol.upper())

    def drug(self, name: str) -> CpicDrugGuideline | None:
        return self.drugs.get(name.strip().lower())

    @property
    def variants_called(self) -> int:
        """
        Total positions PharmCAT actually read a genotype at.

        Counts positions with a non-null `call`, deduplicated across genes so a
        position shared by two genes is not double-counted.
        """
        seen: set[tuple[str, int]] = set()
        for call in self.genes.values():
            for variant in call.variants:
                if variant.call:
                    seen.add((variant.chromosome, variant.position))
        return len(seen)
