"""
Input coverage — the fourth verification edge, and the only one facing the INPUT.

WHY THIS LAYER EXISTS

Every other check in this project reasons about PharmCAT's *output*:

    provenance guard      explanation -> CPIC
    mapping validation    label       -> CPIC
    consistency check     explanation -> label
    phenotype invariant   phenotype   -> label
    THIS                  input       -> required positions

None of those can see the defect this one catches, because from the output's point
of view nothing is wrong. Measured over 120 synthetic samples: when defining
positions are missing from a VCF, PharmCAT does **not** decline. It confidently
calls the reference haplotype, because a change whose key position is missing
is invisible and every observed position then reads reference. Status `DEFINITE`,
one candidate, phenotype asserted.

    coverage   CYP2C9 wrong   SLCO1B1 wrong   NUDT15 wrong
        80%          17.4%            0.0%           0.0%
        60%          28.6%           15.0%          25.0%
        20%          47.8%           42.9%          37.5%

**Every** wrong call in that sweep replaced a reduced-function phenotype with a
normal one. Never the reverse — which is not a coincidence. In variant-based
genomics the reference allele *is* the low-risk state, so absent data does not read
as uncertainty; it reads as normal.

So the mitigation cannot be an output check. It has to be computed from the input,
before PharmCAT runs, which is what this module does.

WHAT COUNTS AS COVERED

A position counts only when the VCF carries a **complete genotype** for it —
including homozygous reference (`0/0`) — located through `FORMAT`. Named FILTER
failures, `./.`, partial calls, rows without `GT`, and absent rows do not count.
`FILTER=.` remains a separately reported quality-not-established state rather
than being silently treated as either PASS or failure. That distinction is the
whole point: a variants-only VCF, which is the common shape in the wild, looks
exactly like one where those positions were never assayed.
"""

from __future__ import annotations

import functools
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .capabilities import capability_for, presentation_capabilities

REQUIREMENTS_PATH = Path(__file__).parent / "data" / "position_requirements.json"

#: A genotype field that asserts no call. Partial calls are classified
#: separately because they preserve some information but cannot establish a
#: complete genotype.
_NO_CALL = frozenset({".", "./.", ".|.", ""})

#: Homozygous-reference genotypes. Their presence is what distinguishes a
#: fully-called VCF from a variants-only one.
_HOM_REF = frozenset({"0/0", "0|0", "0"})


class EvidenceStatus(str, Enum):
    """Application evidence contract for one required genomic position."""

    VALID = "valid_observed_genotype"
    PARTIAL = "partial_genotype"
    NO_CALL = "no_call"
    GT_NOT_PROVIDED = "gt_not_provided"
    FILTER_FAILED = "filter_failed"
    QUALITY_NOT_ESTABLISHED = "quality_not_established"
    MALFORMED = "malformed_genotype"
    ABSENT = "absent_position"


# If duplicate rows disagree, the less trustworthy state wins. A second PASS
# row must never erase an explicit failure at the same coordinate.
_STATUS_PRIORITY = {
    EvidenceStatus.VALID: 0,
    EvidenceStatus.NO_CALL: 1,
    EvidenceStatus.PARTIAL: 2,
    EvidenceStatus.GT_NOT_PROVIDED: 3,
    EvidenceStatus.QUALITY_NOT_ESTABLISHED: 4,
    EvidenceStatus.MALFORMED: 5,
    EvidenceStatus.FILTER_FAILED: 6,
}


def _sample_evidence(parts: list[str]) -> tuple[EvidenceStatus, str]:
    """Classify the first (and, after validation, only) sample at a VCF row.

    This deliberately does not invent DP, GQ or QUAL thresholds. The contract
    trusts an upstream explicit ``FILTER=PASS``, declines named filter failures,
    and preserves ``FILTER=.`` as a distinct quality-not-established state that
    remains usable with a visible warning. GT is located through FORMAT as
    required by the VCF specification.
    """
    format_keys = parts[8].split(":")
    try:
        gt_index = format_keys.index("GT")
    except ValueError:
        return EvidenceStatus.GT_NOT_PROVIDED, ""

    sample_values = parts[9].split(":")
    genotype = sample_values[gt_index].strip() if gt_index < len(sample_values) else ""

    if genotype in _NO_CALL:
        return EvidenceStatus.NO_CALL, genotype

    alleles = re.split(r"[/|]", genotype)
    if "." in alleles:
        return EvidenceStatus.PARTIAL, genotype
    if not alleles or any(not allele.isdigit() for allele in alleles):
        return EvidenceStatus.MALFORMED, genotype

    filter_value = parts[6].strip()
    if filter_value.upper() == "PASS":
        return EvidenceStatus.VALID, genotype
    if filter_value in {"", "."}:
        return EvidenceStatus.QUALITY_NOT_ESTABLISHED, genotype
    return EvidenceStatus.FILTER_FAILED, genotype


@functools.lru_cache(maxsize=1)
def load_requirements(path: Path | None = None) -> dict:
    """Required positions and measured thresholds. Cached; cache_clear in tests."""
    target = path or REQUIREMENTS_PATH
    return json.loads(target.read_text())


@dataclass
class GeneCoverage:
    gene: str
    required: int
    present: int
    hom_ref_present: int
    min_percent: int
    #: Positions that DEFINE a non-normal allele, derived from PharmCAT's own
    #: function assignments — see `scripts/derive_decision_critical.py`.
    critical_required: int = 0
    critical_present: int = 0
    #: Whether the identity requirement is enforced for this gene. True for
    #: DPYD, TPMT and NUDT15 in the pinned requirements bundle; the remaining
    #: genes retain their measured percentage threshold.
    critical_enforced: bool = False
    #: One mutually exclusive state for every required position. This preserves
    #: why evidence was declined instead of collapsing partial, failed and
    #: absent evidence into a single coverage number.
    evidence_counts: dict[str, int] = field(default_factory=dict)

    @property
    def percent(self) -> float:
        return (self.present / self.required * 100) if self.required else 0.0

    @property
    def critical_missing(self) -> int:
        return max(0, self.critical_required - self.critical_present)

    @property
    def critical_satisfied(self) -> bool:
        """Every decision-critical position carries an explicit genotype."""
        return self.critical_missing == 0

    @property
    def sufficient(self) -> bool:
        """
        Percentage AND position identity.

        The percentage is unchanged and is still checked — this ADDS a
        requirement, it does not move a bar. The two answer different
        questions: the percentage asks how much of the gene was reported, and
        the identity requirement asks whether the specific positions that could
        change the answer were among it.

        DPYD is why. At its 20% threshold a file may omit 66 of 83 positions,
        and all 28 decision-critical ones can be inside that 66 — so a file can
        pass on percentage while carrying not one position capable of showing a
        reduced-function allele. Every such file reads as Reference/Reference,
        which is Normal Metabolizer, which is a confident `Safe` on
        fluorouracil.
        """
        if self.percent < self.min_percent:
            return False
        if self.critical_enforced and not self.critical_satisfied:
            return False
        return True


@dataclass
class CoverageReport:
    genes: dict[str, GeneCoverage] = field(default_factory=dict)
    #: True when the VCF carries no homozygous-reference calls at all at required
    #: positions — the variants-only shape.
    variants_only: bool = False
    positions_seen: int = 0

    def insufficient(self) -> list[GeneCoverage]:
        return [c for c in self.genes.values() if not c.sufficient]

    def as_metrics(self) -> dict[str, dict]:
        """Per-gene coverage for `quality_metrics`, on every response."""
        return {
            gene: {
                "positions_present": c.present,
                "positions_required": c.required,
                "percent": round(c.percent, 1),
                "minimum_percent": c.min_percent,
                "sufficient": c.sufficient,
                "decision_critical_present": c.critical_present,
                "decision_critical_required": c.critical_required,
                "decision_critical_enforced": c.critical_enforced,
                "evidence_counts": dict(c.evidence_counts),
            }
            for gene, c in sorted(self.genes.items())
        }


_CHROM_NORM = re.compile(r"^chr", re.IGNORECASE)


def _norm_chrom(value: str) -> str:
    """`chr10` and `10` are the same contig; compare without the prefix."""
    return _CHROM_NORM.sub("", value.strip())


def assess(vcf_text: str, requirements: dict | None = None) -> CoverageReport:
    """
    Per-gene coverage of PharmCAT's required positions, from the raw VCF text.

    Deliberately runs before PharmCAT: the whole point is to know whether the input
    can support a confident answer *before* one is produced.
    """
    cfg = requirements or load_requirements()
    evidence: dict[tuple[str, int], EvidenceStatus] = {}
    genotypes: dict[tuple[str, int], str] = {}

    for line in vcf_text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 10:
            # No sample column: nothing is genotyped, so nothing is covered.
            continue
        try:
            position = int(parts[1])
        except ValueError:
            continue
        key = (_norm_chrom(parts[0]), position)
        status, genotype = _sample_evidence(parts)
        previous = evidence.get(key)
        if previous is None or _STATUS_PRIORITY[status] > _STATUS_PRIORITY[previous]:
            evidence[key] = status
            genotypes[key] = genotype

    # FILTER=. does not assert that a call failed; it says filtering was not
    # applied. Without an assay-specific policy there is no defensible numeric
    # threshold to substitute, so these complete genotypes remain usable but
    # are counted and surfaced as quality-not-established.
    usable_statuses = {EvidenceStatus.VALID, EvidenceStatus.QUALITY_NOT_ESTABLISHED}
    valid = {key for key, status in evidence.items() if status in usable_statuses}
    hom_ref = {key for key in valid if genotypes.get(key) in _HOM_REF}
    report = CoverageReport(positions_seen=len(valid))
    total_hom_ref = 0
    for gene, spec in cfg["genes"].items():
        wanted = {(_norm_chrom(c), p) for c, p in spec["positions"]}
        present = wanted & valid
        hr = wanted & hom_ref
        total_hom_ref += len(hr)

        critical = {(_norm_chrom(c), p)
                    for c, p in spec.get("decision_critical_positions", [])}
        counts = {status.value: 0 for status in EvidenceStatus}
        for key in wanted:
            counts[evidence.get(key, EvidenceStatus.ABSENT).value] += 1

        report.genes[gene] = GeneCoverage(
            gene=gene,
            required=len(wanted),
            present=len(present),
            hom_ref_present=len(hr),
            min_percent=int(spec.get("min_coverage_percent", 100)),
            critical_required=len(critical),
            critical_present=len(critical & valid),
            critical_enforced=bool(spec.get("decision_critical_enforced")),
            evidence_counts=counts,
        )

    # THE COMMON CASE, not an edge case. Most VCFs in the wild omit
    # homozygous-reference calls entirely, and such a file is indistinguishable
    # from one where those positions were never assayed. Flagged separately from
    # generic low coverage because the remedy is different: the user needs to
    # re-call with all sites emitted, not sequence more.
    report.variants_only = total_hom_ref == 0 and report.positions_seen > 0
    return report


def variants_only_warning() -> str:
    return (
        "This VCF contains no homozygous-reference genotypes at any of PharmCAT's "
        "required positions, which means it is almost certainly a variants-only "
        "file. Such a file is indistinguishable from one where those positions "
        "were never tested. For a genotype caller that reads a missing position "
        "as reference, the consequence is NOT a missing result — it is a "
        "confident WRONG result: a change whose key position is missing is "
        "invisible, so a reduced-function patient is reported as normal. "
        "Measured rate of confidently-wrong calls at 60% position coverage: up "
        "to 28.6%. This application therefore reports genes without their "
        "required positions as Unknown rather than as normal. Produce the file again with "
        "EVERY position reported — including the ones that match the reference "
        "— so each required position carries an explicit genotype. The input "
        "requirements page gives the exact commands. "
        "See docs/input_requirements.md."
    )


def critical_positions_warning(cov: GeneCoverage) -> str:
    """
    Why a gene that met its percentage was still declined.

    Says which requirement failed and why the percentage did not settle it —
    otherwise "37% is enough but you were refused" reads as a bug.
    """
    return (
        f"{cov.gene}: {cov.critical_present} of {cov.critical_required} "
        f"positions that could indicate reduced function carry an explicit "
        f"genotype in this VCF. The gene met its {cov.min_percent}% coverage "
        f"minimum ({cov.percent:.0f}%), but percentage is a proxy: a file can "
        f"clear it while omitting every position capable of showing a variant. "
        f"Reported as Unknown rather than assuming the missing positions match "
        f"the reference — which is what would make a reduced-function result "
        f"read as normal."
    )


def all_genes_gated_warning(assessment: "CoverageReport") -> str:
    """
    One diagnosis, in place of seven near-identical refusals.

    When EVERY gene is declined, the per-gene messages say the same thing seven
    times and none of them says the useful part: this is almost certainly a
    whole-file property, not seven independent coincidences. A visitor who
    downloads a public research VCF or a consumer SNP export hits exactly this,
    and the generic wall of text reads as the site being broken.

    Naming the two likely sources is the difference between "try again" and
    "this class of file cannot work, here is what can".
    """
    total = len(assessment.genes)
    worst = min((c.percent for c in assessment.genes.values()), default=0.0)
    best = max((c.percent for c in assessment.genes.values()), default=0.0)
    return (
        f"Every gene ({total} of {total}) was declined, at {worst:.0f}–{best:.0f}% "
        f"position coverage. That pattern is a property of the FILE, not of "
        f"{total} separate genes — and it has two common causes.\n\n"
        f"This looks like a research-format or SNP-array export.\n\n"
        f"• A research VCF (1000 Genomes, gnomAD, most sequencing pipelines) is "
        f"POLYMORPHIC-FILTERED: it lists only positions where someone differed "
        f"from the reference. The positions that matched are simply absent, and "
        f"absent is indistinguishable from never-tested.\n"
        f"• A consumer export (23andMe, AncestryDNA) is a GENOTYPING ARRAY, not "
        f"sequencing. It reports a few hundred thousand chosen positions across "
        f"the whole genome, which is not the same as reporting every position "
        f"one gene needs.\n\n"
        f"Neither is a bad file. Both are the wrong shape for this question. "
        f"What works is a clinical pharmacogenomic panel, or a sequencing "
        f"pipeline re-run to emit every position including the reference "
        f"matches. The input requirements page lists the specific sources."
    )


def insufficient_warning(cov: GeneCoverage) -> str:
    return (
        f"{cov.gene}: only {cov.present} of {cov.required} required positions "
        f"({cov.percent:.0f}%) carry an acceptable genotype in this VCF, below the "
        f"{cov.min_percent}% minimum measured for this gene. Reported as Unknown. "
        f"A confident call at this coverage would be unreliable — and unreliable in "
        f"one direction: missing positions read as reference, so the error would be "
        f"to report reduced function as normal. {_evidence_reason(cov)}"
    )


def quality_not_established_warning(report: CoverageReport) -> str:
    genes = [
        f"{gene} ({cov.evidence_counts.get(EvidenceStatus.QUALITY_NOT_ESTABLISHED.value, 0)})"
        for gene, cov in sorted(report.genes.items())
        if cov.evidence_counts.get(EvidenceStatus.QUALITY_NOT_ESTABLISHED.value, 0)
    ]
    return (
        "Input quality was not established for required positions marked "
        f"FILTER=. in: {', '.join(genes)}. These complete genotypes were retained "
        "because the VCF does not explicitly mark them as failed and this "
        "application does not invent assay-independent DP/GQ/QUAL thresholds. "
        "Confirm the upstream caller's quality policy before relying on them."
    )


# --------------------------------------------------------------------------- #
# Readiness — the shared view both /coverage and the client consume
# --------------------------------------------------------------------------- #

#: Genes this application does not call from an uploaded VCF, whatever the
#: coverage, with the reason to show in place of a tick bar. A zero bar would
#: blame the user's file for a limit of this application. (VCF itself can carry
#: structural-variant and copy-number records; calling them for CYP2D6 needs
#: specialised read-level analysis this application does not perform.)
NOT_READABLE_FROM_VCF: dict[str, str] = {
    "CYP2D6": (
        "Not called from an uploaded VCF by this application: CYP2D6 results "
        "depend on copy-number and structural variation, which need specialised "
        "read-level calling. Uploading a different VCF here will not resolve it."
    ),
}


@dataclass(frozen=True)
class DrugEligibility:
    """Whether all declared input dependencies for one drug are usable."""

    drug: str
    required_genes: tuple[str, ...]
    failed_genes: tuple[str, ...]
    guidance_capable: bool
    limitation: str

    @property
    def eligible(self) -> bool:
        return (
            bool(self.required_genes)
            and self.guidance_capable
            and not self.failed_genes
        )

    @property
    def valid_genes(self) -> tuple[str, ...]:
        failed = set(self.failed_genes)
        return tuple(gene for gene in self.required_genes if gene not in failed)

    @property
    def reason(self) -> str:
        if self.eligible:
            return ""
        if self.limitation and not self.guidance_capable:
            return self.limitation
        if not self.required_genes:
            return (
                "This drug is outside the audited application scope; no "
                "application guidance is produced."
            )
        return (
            "Required genomic evidence is incomplete for "
            + ", ".join(self.failed_genes)
            + ". Available partner findings are partial evidence only; no complete "
              "drug-level PGx recommendation is made."
        )


def drug_eligibility(
    report: CoverageReport,
    drug: str,
    mapping: dict | None = None,
) -> DrugEligibility:
    """Shared drug-level evidence decision used by preview and final analysis."""
    capability = capability_for(drug)
    required = capability.evidence_dependencies if capability else ()
    failed = tuple(
        gene
        for gene in required
        if gene in NOT_READABLE_FROM_VCF
        or gene not in report.genes
        or not report.genes[gene].sufficient
    )
    return DrugEligibility(
        drug=drug.strip().lower(),
        required_genes=required,
        failed_genes=failed,
        guidance_capable=bool(capability and capability.guidance_capable),
        limitation=capability.limitation if capability else "",
    )


def _evidence_reason(cov: GeneCoverage) -> str:
    labels = {
        EvidenceStatus.PARTIAL.value: "partial genotypes",
        EvidenceStatus.NO_CALL.value: "no-calls",
        EvidenceStatus.GT_NOT_PROVIDED.value: "rows without GT",
        EvidenceStatus.FILTER_FAILED.value: "FILTER-failed calls",
        EvidenceStatus.QUALITY_NOT_ESTABLISHED.value: "unfiltered calls",
        EvidenceStatus.MALFORMED.value: "malformed genotypes",
        EvidenceStatus.ABSENT.value: "absent positions",
    }
    detail = [
        f"{cov.evidence_counts.get(status, 0)} {label}"
        for status, label in labels.items()
        if cov.evidence_counts.get(status, 0)
    ]
    suffix = f" Evidence gaps: {', '.join(detail)}." if detail else ""
    return (
        f"{cov.present} of {cov.required} required positions had acceptable "
        f"genotypes; this gene needs {cov.min_percent}%." + suffix
    )


def readiness(report: CoverageReport, mapping: dict | None = None) -> dict:
    """
    Turn a `CoverageReport` into the per-gene + per-drug view the API returns.

    Kept here rather than in `main` so /coverage and /analyze cannot drift: both
    read the same thresholds from the same file through the same function.
    Drug eligibility comes from the authoritative capability registry. A
    multi-gene drug passes only when every dependency passes this same report,
    and registry-declared abstentions remain unanswerable even with coverage.
    """
    genes: list[dict] = []
    for gene, cov in sorted(report.genes.items()):
        blocked = NOT_READABLE_FROM_VCF.get(gene.upper())
        genes.append({
            "gene": gene,
            "positions_found": cov.present,
            "positions_required": cov.required,
            "threshold_percent": cov.min_percent,
            "percent": round(cov.percent, 1),
            # A gene that no VCF can read never "passes", but it is not a
            # coverage failure either — the reason field carries the difference.
            "passes": bool(cov.sufficient and not blocked),
            "not_readable_from_vcf": bool(blocked),
            "reason": blocked or ("" if cov.sufficient else _evidence_reason(cov)),
        })

    answerable, unanswerable = [], []
    for capability in presentation_capabilities():
        drug = capability.drug
        eligibility = drug_eligibility(report, drug)
        (answerable if eligibility.eligible else unanswerable).append(drug)

    passing = {g["gene"].upper() for g in genes if g["passes"]}

    return {
        "genes": genes,
        "genes_passing": len(passing),
        "genes_total": len(genes),
        "answerable_drugs": answerable,
        "unanswerable_drugs": unanswerable,
        "variants_only": report.variants_only,
    }
