"""
The coverage gate's invariant, checked a second time on PharmCAT's own evidence.

WHY A SECOND IMPLEMENTATION

`coverage.assess` reads the VCF text and counts a position as evidence when its
row carries a usable genotype at that contig and position. It never compares REF
with GRCh38, and it strips a `chr` prefix itself. PharmCAT reads the same file
independently: its matcher drops a genotype whose REF contradicts the reference
it expects, does not recognise `10` as `chr10`, and reports per gene and per
position whether it ended up with a usable call. Part A found files where the two
views disagree and the disagreement decides the answer — A4-09b and A4-22 got
confident labels from genotypes PharmCAT itself had discarded.

So the same thresholds are applied twice: once by `coverage` to the positions
our parser accepted, and once here to the positions PharmCAT reports a call for.
A drug gets a confident label only when both say its genes are covered. This
module never reads the VCF and shares no code with `coverage`; the only thing
the two have in common is the requirement file that defines the invariant.

WHAT PHARMCAT ITSELF ENFORCES

PharmCAT 3.4.0's own minimum-data rule — `requiredPositions` in the jar's
`exemptions.json` — names positions for NAT2 only, so for every gene here it
cannot fire. It is applied anyway, read from the jar the runner uses, so a
PharmCAT release that adds requirements is honoured; the test that pins the
current lists fails until such a change is reviewed. AMP Tier 1 positions are
listed in the same file, but PharmCAT 3.4.0 left `missingAmp1Positions` empty in
every probe (audit/phase9/B3_PLAN.md), so nothing here relies on them.
"""

from __future__ import annotations

import functools
import json
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from .pharmcat_models import PharmcatReport
from .pharmcat_runner import find_jar

if TYPE_CHECKING:  # pragma: no cover — typing only
    from .coverage import DrugEligibility

REQUIREMENTS_PATH = Path(__file__).parent / "data" / "position_requirements.json"
EXEMPTIONS_MEMBER = "org/pharmgkb/pharmcat/definition/alleles/exemptions.json"
#: How many unused positions a warning names before summarising the rest.
EXAMPLES = 3


@functools.lru_cache(maxsize=1)
def pharmcat_required_positions() -> dict[str, frozenset[int]]:
    """PharmCAT's own required positions per gene, from the jar the runner uses."""
    jar = find_jar()
    if jar is None:
        return {}
    with zipfile.ZipFile(jar) as zf:
        exemptions = json.loads(zf.read(EXEMPTIONS_MEMBER))
    return {
        gene: frozenset(int(p) for p in (entry.get("requiredPositions") or []))
        for gene, entry in exemptions.items()
    }


@functools.lru_cache(maxsize=1)
def _requirements() -> dict:
    return json.loads(REQUIREMENTS_PATH.read_text())


@dataclass(frozen=True)
class UnusedPosition:
    position: int
    rsid: str | None
    #: PharmCAT's own words for why it had no genotype, when it gave any.
    reason: str


@dataclass(frozen=True)
class PharmcatEvidence:
    """One gene's coverage, counted over the positions PharmCAT used."""

    gene: str
    required: int
    used: int
    min_percent: int
    critical_required: int
    critical_used: int
    critical_enforced: bool
    #: PharmCAT's own required positions it had no genotype for.
    missing_required: tuple[int, ...]
    #: Required positions PharmCAT had no genotype for, in position order.
    unused: tuple[UnusedPosition, ...]

    @property
    def percent(self) -> float:
        return (self.used / self.required * 100) if self.required else 0.0

    @property
    def sufficient(self) -> bool:
        if self.missing_required:
            return False
        if self.percent < self.min_percent:
            return False
        if self.critical_enforced and self.critical_used < self.critical_required:
            return False
        return True


def assess(report: PharmcatReport, requirements: dict | None = None) -> dict[str, PharmcatEvidence]:
    """
    Per gene, the coverage verdict on PharmCAT's evidence.

    A gene PharmCAT reports no positions for (CYP2D6, which it does not call
    from a VCF) is left out: there is no second view to compare, and the coverage
    module already declines it.
    """
    cfg = requirements or _requirements()
    native = pharmcat_required_positions()
    out: dict[str, PharmcatEvidence] = {}
    for gene, spec in cfg["genes"].items():
        call = report.gene(gene)
        if call is None or not call.variants:
            continue
        by_position = {v.position: v for v in call.variants}
        used = {v.position for v in call.variants if v.call}
        wanted = {int(p) for _, p in spec["positions"]}
        critical = {int(p) for _, p in spec.get("decision_critical_positions", [])}
        unused = tuple(
            UnusedPosition(
                position=p,
                rsid=by_position[p].dbSnpId if p in by_position else None,
                reason=("; ".join(by_position[p].warnings) if p in by_position else "")
                or "no usable genotype at this position",
            )
            for p in sorted(wanted - used)
        )
        out[gene] = PharmcatEvidence(
            gene=gene,
            required=len(wanted),
            used=len(wanted & used),
            min_percent=int(spec.get("min_coverage_percent", 100)),
            critical_required=len(critical),
            critical_used=len(critical & used),
            critical_enforced=bool(spec.get("decision_critical_enforced")),
            missing_required=tuple(sorted(native.get(gene, frozenset()) - used)),
            unused=unused,
        )
    return out


def disagreement_warning(evidence: PharmcatEvidence) -> str:
    """The refusal, in terms a reader can check against the file."""
    # Positions PharmCAT gave a reason for come first: they explain the gap.
    shown = sorted(evidence.unused, key=lambda u: (u.reason.startswith("no usable"), u.position))
    examples = "; ".join(
        f"position {u.position}{f' ({u.rsid})' if u.rsid else ''}: {u.reason}"
        for u in shown[:EXAMPLES]
    )
    more = len(shown) - EXAMPLES
    if more > 0:
        examples += f"; and {more} more"
    need = f"{evidence.min_percent}% needed"
    if evidence.critical_enforced:
        need += (f", and all {evidence.critical_required} positions that can show a "
                 f"reduced-function allele")
    if evidence.missing_required:
        need += f"; PharmCAT itself requires {len(evidence.missing_required)} of the missing ones"
    return (
        f"{evidence.gene}: the coverage check counted this file's genotypes as complete, "
        f"but PharmCAT did not use {len(evidence.unused)} of them ({examples}). Counting "
        # Floored, so a shortfall can never print as the 100% it falls short of.
        f"only what PharmCAT used, {evidence.used} of {evidence.required} positions "
        f"({int(evidence.percent)}%) remain ({need}), so no recommendation that depends "
        f"on {evidence.gene} is given."
    )


def restrict(eligibility: "DrugEligibility", evidence: dict[str, PharmcatEvidence]) -> "DrugEligibility":
    """A drug stays eligible only if PharmCAT's evidence also covers its genes."""
    failed = set(eligibility.failed_genes)
    newly = tuple(
        gene for gene in eligibility.required_genes
        if gene not in failed and gene in evidence and not evidence[gene].sufficient
    )
    if not newly:
        return eligibility
    return replace(
        eligibility,
        failed_genes=eligibility.failed_genes + newly,
        findings=eligibility.findings + tuple(
            f"PharmCAT did not use genotypes the coverage check counted for {gene}."
            for gene in newly
        ),
    )


def annotate(metrics: dict[str, dict], evidence: dict[str, PharmcatEvidence]) -> dict[str, dict]:
    """Add PharmCAT's count and verdict beside the coverage check's, per gene."""
    for gene, row in metrics.items():
        if gene in evidence:
            row["pharmcat_positions_used"] = evidence[gene].used
            row["pharmcat_sufficient"] = evidence[gene].sufficient
    return metrics
