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
calls the reference haplotype, because a variant whose defining position is absent
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

A position counts only when the VCF carries an **explicit genotype** for it —
including homozygous reference (`0/0`). `./.` does not count, and neither does a
row that simply is not there. That distinction is the whole point: a
variants-only VCF, which is the common shape in the wild, looks exactly like one
where those positions were never assayed.
"""

from __future__ import annotations

import functools
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

REQUIREMENTS_PATH = Path(__file__).parent / "data" / "position_requirements.json"

#: A genotype field that asserts a call. `./.` and `.` assert nothing.
_NO_CALL = frozenset({".", "./.", ".|.", ""})

#: Homozygous-reference genotypes. Their presence is what distinguishes a
#: fully-called VCF from a variants-only one.
_HOM_REF = frozenset({"0/0", "0|0", "0"})


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

    @property
    def percent(self) -> float:
        return (self.present / self.required * 100) if self.required else 0.0

    @property
    def sufficient(self) -> bool:
        return self.percent >= self.min_percent


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
    called: set[tuple[str, int]] = set()
    hom_ref: set[tuple[str, int]] = set()

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
        genotype = parts[9].split(":", 1)[0].strip()
        if genotype in _NO_CALL:
            continue
        key = (_norm_chrom(parts[0]), position)
        called.add(key)
        if genotype in _HOM_REF:
            hom_ref.add(key)

    report = CoverageReport(positions_seen=len(called))
    total_hom_ref = 0
    for gene, spec in cfg["genes"].items():
        wanted = {(_norm_chrom(c), p) for c, p in spec["positions"]}
        present = wanted & called
        hr = wanted & hom_ref
        total_hom_ref += len(hr)
        report.genes[gene] = GeneCoverage(
            gene=gene,
            required=len(wanted),
            present=len(present),
            hom_ref_present=len(hr),
            min_percent=int(spec.get("min_coverage_percent", 100)),
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
        "were never tested, and the consequence is NOT a missing result — it is a "
        "confident WRONG result: a variant whose defining position is absent is "
        "invisible, so the genotype reads as reference and a reduced-function "
        "patient is reported as normal. Measured rate of confidently-wrong calls "
        "at 60% position coverage: up to 28.6%. Re-call the VCF emitting ALL "
        "sites (e.g. GATK GenotypeGVCFs with --include-non-variant-sites, or "
        "bcftools call without -v) so every required position carries an explicit "
        "genotype. See docs/input_requirements.md."
    )


def insufficient_warning(cov: GeneCoverage) -> str:
    return (
        f"{cov.gene}: only {cov.present} of {cov.required} required positions "
        f"({cov.percent:.0f}%) carry an explicit genotype in this VCF, below the "
        f"{cov.min_percent}% minimum measured for this gene. Reported as Unknown. "
        f"A confident call at this coverage would be unreliable — and unreliable in "
        f"one direction: missing positions read as reference, so the error would be "
        f"to report reduced function as normal."
    )
