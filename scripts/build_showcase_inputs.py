#!/usr/bin/env python3
"""
Build a conforming PharmaGuard input from a public DRAGEN gVCF (Phase 10 §3.3).

WHY THIS EXISTS

The application requires an explicit genotype at every decision-critical
position, homozygous-reference included. A variants-only VCF cannot supply
that: it lists only positions where the sample differed, and an absent position
is indistinguishable from one that was never assayed. That is not a defect in
the pipeline, it is a property of the input -- which is why the 400-sample
1000 Genomes cohort dropped to 12.58% usable, and why the fix is a better
source rather than a weaker gate.

A gVCF carries what the variants-only file lacks. Its reference blocks are the
caller's own positive statement -- genotype 0/0, with a depth and a genotype
quality -- that a span of positions was read and matched the reference. This
script expands those blocks to one row per required position. That repeats the
caller's statement at single-position resolution. It adds no information, and
it assumes none.

WHAT THIS SCRIPT WILL NOT DO

Everything here is a transcription. Nothing is inferred, upgraded or guessed:

  * A required position with no covering record gets NO ROW. It is never
    written as reference. (PharmCAT's `--absent-to-ref` is the thing this
    project exists to argue against, and it is not used.)
  * FILTER is carried from the source record. A row is never promoted to PASS.
    A position the caller flagged LowGQ stays flagged, and the coverage gate
    then declines the gene -- which is the correct outcome, not a problem to
    work around.
  * A genotype is transcribed only when every called allele is identical, base
    for base, to PharmCAT's REF or one of PharmCAT's ALTs at that position. An
    allele PharmCAT does not list is a refusal, not an approximation.
  * Phase is dropped. DRAGEN's phase sets do not span a gene, while PharmCAT
    reads `|` as phased across one, so carrying the separator would state more
    than the source does.
  * The file is emitted only if it conforms. `--out` is written after the
    repository's own validator and coverage checker accept it, so a
    non-conforming file never reaches the demo directory at all.

USAGE

    python scripts/build_showcase_inputs.py --sample NA12878 \\
        --out demo/samples/NA12878.vcf

    python scripts/build_showcase_inputs.py --sample NA12878 \\
        --gvcf local.regions.vcf.gz --out demo/samples/NA12878.vcf

    python scripts/build_showcase_inputs.py --sample NA12878 --report-only

`--gvcf` takes an already-fetched region slice (the remote fetch costs ~20s per
sample); without it the slice is pulled from the public bucket over HTTPS.
`--report-only` prints the per-gene census and exits without writing.
"""

from __future__ import annotations

import argparse
import bisect
import gzip
import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from _common import rel, scrub  # noqa: E402

from app import coverage as coverage_mod  # noqa: E402
from app.vcf_validation import VcfValidationError, validate_vcf  # noqa: E402

REQUIREMENTS = REPO_ROOT / "backend" / "app" / "data" / "position_requirements.json"
POSITIONS_VCF = (
    REPO_ROOT / "test-data" / "reference" / "tools" / "pharmcat_positions_3.4.0.vcf.bgz"
)

#: The public DRAGEN v4.4.7 reanalysis. Anonymous HTTPS; no credentials.
BUCKET = "1000genomes-dragen-v4-4-7"
PREFIX = "data/individuals/hg38-alt_masked.cnv.graph.hla.methyl_cg.rna-11-r5.0-2"
DRAGEN_VERSION = "v4.4.7"

#: How far either side of a gene's required positions to pull. A reference
#: block may start well before the first required position, and a block is only
#: usable if its whole record is in hand.
REGION_PAD = 10_000

#: The genes this application reads from a VCF. CYP2D6 is excluded on purpose:
#: its star alleles depend on copy number and structural variation, so no VCF
#: content makes this application call it, and its rows must not decide whether
#: a file is fit to emit. They are still carried where the source supports them.
VCF_READABLE_GENES = (
    "CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "NUDT15", "DPYD", "VKORC1", "CYP4F2",
)

#: `<NON_REF>` (GATK) and `<*>` (bcftools) mark a gVCF reference record.
GVCF_REF_ALTS = ("<NON_REF>", "<*>")

#: The source's own targeted-caller output, which carries its CYP2D6 call.
#: Deliberately a SEPARATE object from the gVCF: a CYP2D6 diplotype is not
#: something a VCF establishes, so it must not arrive inside one.
TARGETED_OBJECT = "{sample}.targeted.json"

#: The name this project records for the caller that produced a supplied
#: CYP2D6 diplotype. Must be one of `app.outside_calls.CALLERS`, which the
#: emitter asserts rather than assumes.
CYP2D6_CALLER = "DRAGEN"


class BuildRefused(RuntimeError):
    """The sample cannot produce a conforming file. Never partially written."""


@dataclass
class PositionOutcome:
    """What the source said about one required position, and why."""

    chrom: str
    pos: int
    gene: str
    #: "variant" | "reference_block" | "uncovered" | "refused"
    source: str
    genotype: str = ""
    filter_value: str = ""
    depth: int | None = None
    quality: int | None = None
    reason: str = ""

    @property
    def usable(self) -> bool:
        return self.source in {"variant", "reference_block"} and not self.reason


@dataclass
class GeneCensus:
    gene: str
    required: int = 0
    from_block: int = 0
    from_variant: int = 0
    uncovered: int = 0
    refused: int = 0
    non_pass: int = 0
    min_depth: int | None = None
    min_quality: int | None = None
    problems: list[str] = field(default_factory=list)

    @property
    def present(self) -> int:
        return self.from_block + self.from_variant


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


def required_positions() -> dict[tuple[str, int], str]:
    """(chrom, pos) -> gene, from the pinned requirements bundle."""
    spec = json.loads(REQUIREMENTS.read_text())
    wanted: dict[tuple[str, int], str] = {}
    for gene, entry in spec["genes"].items():
        for chrom, pos in entry["positions"]:
            wanted[(str(chrom), int(pos))] = gene
    if not wanted:
        raise BuildRefused(f"{rel(REQUIREMENTS)} declares no required positions.")
    return wanted


def pharmcat_rows() -> dict[tuple[str, int], tuple[str, str, list[str], str]]:
    """
    (chrom, pos) -> (id, ref, alts, info), read from PharmCAT's own positions VCF.

    The emitted file must use PharmCAT's REF and ALT spellings, because that is
    what its matcher reads. Transcribing the source's own spelling would
    produce rows PharmCAT silently discards.
    """
    if not POSITIONS_VCF.is_file():
        raise BuildRefused(
            f"PharmCAT's positions file is missing at {rel(POSITIONS_VCF)}. "
            f"Fix: python scripts/fetch_reference_data.py --fetch-tools"
        )
    result = subprocess.run(
        ["bcftools", "view", "-H", str(POSITIONS_VCF)],
        capture_output=True, text=True, check=True,
    )
    if result.returncode != 0:  # defensive: check=True should have raised
        raise BuildRefused(f"bcftools exited {result.returncode} reading the positions file")
    rows: dict[tuple[str, int], tuple[str, str, list[str], str]] = {}
    for line in result.stdout.splitlines():
        if not line or line.startswith("#"):
            continue
        f = line.split("\t")
        rows[(f[0], int(f[1]))] = (f[2], f[3], f[4].split(","), f[7])
    if not rows:
        raise BuildRefused(
            f"{rel(POSITIONS_VCF)} yielded no rows. An empty query result is a "
            f"failure here, not an empty answer."
        )
    return rows


def regions_for(wanted: dict[tuple[str, int], str]) -> list[str]:
    """One padded region per gene, as bcftools `-r` expects (comma-joined)."""
    spans: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for (chrom, pos), gene in wanted.items():
        spans[gene][chrom].append(pos)
    out: list[str] = []
    for gene in sorted(spans):
        for chrom in sorted(spans[gene]):
            positions = sorted(spans[gene][chrom])
            out.append(
                f"{chrom}:{max(1, positions[0] - REGION_PAD)}-{positions[-1] + REGION_PAD}"
            )
    return sorted(out)


def fetch_slice(sample: str, regions: list[str], destination: Path) -> str:
    """
    Pull the gene regions of one sample's gVCF over anonymous HTTPS.

    Returns the source URL. `check=True` and an explicit returncode read: a
    failed fetch that merely printed a warning would leave an empty file, and
    an empty file is the one shape this script must never treat as "no data".
    """
    url = f"https://{BUCKET}.s3.amazonaws.com/{PREFIX}/{sample}/{sample}.hard-filtered.gvcf.gz"
    destination.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["bcftools", "view", "-r", ",".join(regions), "-Oz", "-o", str(destination), url],
        capture_output=True, text=True, check=True,
    )
    if completed.returncode != 0:
        raise BuildRefused(
            f"bcftools exited {completed.returncode} fetching {sample}: "
            f"{scrub(completed.stderr)[-400:]}"
        )
    if not destination.is_file() or destination.stat().st_size == 0:
        raise BuildRefused(f"the fetch produced no data for {sample}")
    return url


# --------------------------------------------------------------------------- #
# Reading the source
# --------------------------------------------------------------------------- #


def _open_text(path: Path):
    if path.suffix == ".gz" or path.name.endswith(".bgz"):
        return gzip.open(path, "rt")
    return path.open("rt")


def _record_end(fields: list[str], pos: int) -> int:
    """A gVCF record's last position: END= when present, else its REF span."""
    for item in fields[7].split(";"):
        if item.startswith("END="):
            try:
                return int(item[4:])
            except ValueError:
                break
    return pos + len(fields[3]) - 1


def read_source(path: Path) -> tuple[dict[tuple[str, int], list[list[str]]],
                                     dict[str, list[tuple[int, int, list[str]]]]]:
    """
    Split the slice into variant records (keyed by start) and reference records.

    A record whose only ALT is the gVCF reference symbol is a reference record,
    whether it spans one position or a thousand. Everything else is a variant
    record and is keyed by the position it starts at -- a variant that merely
    overlaps a required position is deliberately not matched to it, because
    its genotype is written against a different REF.
    """
    variants: dict[tuple[str, int], list[list[str]]] = defaultdict(list)
    reference: dict[str, list[tuple[int, int, list[str]]]] = defaultdict(list)
    with _open_text(path) as handle:
        for line in handle:
            if not line or line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 10:
                continue
            try:
                pos = int(fields[1])
            except ValueError:
                continue
            real_alts = [a for a in fields[4].split(",") if a not in GVCF_REF_ALTS]
            if real_alts:
                variants[(fields[0], pos)].append(fields)
            else:
                reference[fields[0]].append((pos, _record_end(fields, pos), fields))
    if not variants and not reference:
        raise BuildRefused(
            f"{rel(path)} contains no records. An empty slice is a failure, not "
            f"an empty answer -- check the sample id and the region list."
        )
    for chrom in reference:
        reference[chrom].sort(key=lambda item: item[0])
    return variants, reference


class ReferenceIndex:
    """Find the reference record covering a position, if any."""

    def __init__(self, reference: dict[str, list[tuple[int, int, list[str]]]]) -> None:
        self._by_chrom = reference
        self._starts = {c: [r[0] for r in rows] for c, rows in reference.items()}

    def covering(self, chrom: str, pos: int) -> list[str] | None:
        rows = self._by_chrom.get(chrom)
        if not rows:
            return None
        starts = self._starts[chrom]
        index = bisect.bisect_right(starts, pos) - 1
        # Blocks do not overlap in a gVCF, but walk back a bounded distance
        # rather than trusting that: a wrong answer here would invent evidence.
        while index >= 0 and starts[index] >= pos - 1_000_000:
            start, end, fields = rows[index]
            if start <= pos <= end:
                return fields
            index -= 1
        return None


def _sample_field(fields: list[str], key: str) -> str:
    keys = fields[8].split(":")
    values = fields[9].split(":")
    if key not in keys:
        return ""
    index = keys.index(key)
    return values[index] if index < len(values) else ""


def _as_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Transcription
# --------------------------------------------------------------------------- #


def transcribe(
    chrom: str,
    pos: int,
    gene: str,
    pharmcat: tuple[str, str, list[str], str],
    variants: dict[tuple[str, int], list[list[str]]],
    reference: ReferenceIndex,
) -> PositionOutcome:
    """
    One required position, turned into an outcome. Never guesses.

    Order matters: a variant record that starts exactly here is the most
    specific statement the caller made, so it wins over a reference record that
    merely spans the position (the two co-occur in CYP2D6, where DRAGEN's
    targeted caller emits both).
    """
    _, pharmcat_ref, pharmcat_alts, _ = pharmcat
    rows = variants.get((chrom, pos), [])

    if rows:
        fields = rows[0]
        genotype_raw = _sample_field(fields, "GT").strip()
        if not genotype_raw:
            return PositionOutcome(chrom, pos, gene, "refused",
                                   reason="the source record carries no GT")
        source_ref = fields[3]
        source_alts = [a for a in fields[4].split(",") if a not in GVCF_REF_ALTS]
        if source_ref != pharmcat_ref:
            # The two files describe the same change with different anchors
            # (an indel's padding base, or an MNV written as one record).
            # Re-deriving the equivalence is exactly the kind of guess this
            # script refuses to make.
            return PositionOutcome(
                chrom, pos, gene, "refused",
                reason=(f"the source writes REF {source_ref} where PharmCAT has "
                        f"{pharmcat_ref}; the two spellings are not interchangeable"),
            )
        alleles = [source_ref] + source_alts
        allowed = [pharmcat_ref] + pharmcat_alts
        indices: list[str] = []
        for call in genotype_raw.replace("|", "/").split("/"):
            if call == ".":
                return PositionOutcome(chrom, pos, gene, "refused",
                                       reason=f"the source genotype is a partial call ({genotype_raw})")
            number = _as_int(call)
            if number is None or number >= len(alleles):
                return PositionOutcome(chrom, pos, gene, "refused",
                                       reason=f"the source genotype {genotype_raw} names an allele the record does not define")
            base = alleles[number]
            if base not in allowed:
                return PositionOutcome(
                    chrom, pos, gene, "refused",
                    reason=(f"the source calls allele {base!r}, which is not among "
                            f"PharmCAT's alleles at this position "
                            f"({', '.join(allowed)})"),
                )
            indices.append(str(allowed.index(base)))
        return PositionOutcome(
            chrom, pos, gene, "variant",
            genotype="/".join(indices),          # unphased, deliberately
            filter_value=fields[6].strip() or ".",
            depth=_as_int(_sample_field(fields, "DP")),
            quality=_as_int(_sample_field(fields, "GQ")),
        )

    block = reference.covering(chrom, pos)
    if block is None:
        return PositionOutcome(chrom, pos, gene, "uncovered",
                               reason="no record in the source covers this position")
    genotype_raw = _sample_field(block, "GT").strip()
    if genotype_raw not in {"0/0", "0|0", "0"}:
        # A reference record whose genotype is not homozygous reference is not
        # evidence of anything this script may transcribe.
        return PositionOutcome(
            chrom, pos, gene, "refused",
            reason=f"the covering reference record carries GT {genotype_raw or '(absent)'}",
        )
    ploidy = 1 if genotype_raw == "0" else 2
    return PositionOutcome(
        chrom, pos, gene, "reference_block",
        genotype="0" if ploidy == 1 else "0/0",
        filter_value=block[6].strip() or ".",
        depth=_as_int(_sample_field(block, "MIN_DP")) or _as_int(_sample_field(block, "DP")),
        quality=_as_int(_sample_field(block, "GQ")),
    )


def build_census(outcomes: list[PositionOutcome]) -> dict[str, GeneCensus]:
    census: dict[str, GeneCensus] = {}
    for item in outcomes:
        entry = census.setdefault(item.gene, GeneCensus(gene=item.gene))
        entry.required += 1
        if item.source == "reference_block":
            entry.from_block += 1
        elif item.source == "variant":
            entry.from_variant += 1
        elif item.source == "uncovered":
            entry.uncovered += 1
            entry.problems.append(f"{item.chrom}:{item.pos} {item.reason}")
            continue
        else:
            entry.refused += 1
            entry.problems.append(f"{item.chrom}:{item.pos} {item.reason}")
            continue
        if item.filter_value.upper() != "PASS":
            entry.non_pass += 1
            entry.problems.append(
                f"{item.chrom}:{item.pos} the source caller marked this position "
                f"FILTER={item.filter_value}"
            )
        if item.depth is not None:
            entry.min_depth = min(entry.min_depth, item.depth) if entry.min_depth is not None else item.depth
        if item.quality is not None:
            entry.min_quality = min(entry.min_quality, item.quality) if entry.min_quality is not None else item.quality
    return census


# --------------------------------------------------------------------------- #
# Emission
# --------------------------------------------------------------------------- #


def render_vcf(
    sample: str,
    outcomes: list[PositionOutcome],
    pharmcat: dict[tuple[str, int], tuple[str, str, list[str], str]],
    provenance: dict[str, str],
) -> str:
    """
    The conforming VCF, as text.

    Deterministic: the header carries no timestamp and rows are emitted in
    contig-then-position order, so two runs over the same slice are
    byte-identical and a recorded checksum means something.
    """
    usable = [o for o in outcomes if o.usable]
    contigs = sorted({o.chrom for o in usable}, key=_contig_sort_key)
    lines = [
        "##fileformat=VCFv4.2",
        '##FILTER=<ID=PASS,Description="All filters passed">',
        "##source=PharmaGuard showcase input, transcribed from a public DRAGEN gVCF",
        f"##pharmaguard_source_bucket=s3://{BUCKET}",
        f"##pharmaguard_source_object={PREFIX}/{sample}/{sample}.hard-filtered.gvcf.gz",
        f"##pharmaguard_source_caller=DRAGEN {DRAGEN_VERSION}",
        f"##pharmaguard_source_retrieved={provenance['retrieved']}",
        "##pharmaguard_transcription=reference blocks expanded to one row per "
        "required position; genotypes and FILTER carried from the source; "
        "no position inferred as reference",
        "##reference=GRCh38",
    ]
    for chrom in contigs:
        lines.append(f'##contig=<ID={chrom},assembly=GRCh38.p14,species="Homo sapiens">')
    lines += [
        '##INFO=<ID=PX,Number=.,Type=String,Description="Gene">',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
        f"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{sample}",
    ]
    for item in sorted(usable, key=lambda o: (_contig_sort_key(o.chrom), o.pos)):
        identifier, ref, alts, info = pharmcat[(item.chrom, item.pos)]
        lines.append("\t".join([
            item.chrom, str(item.pos), identifier or ".", ref, ",".join(alts),
            ".", item.filter_value or ".", info or f"PX={item.gene}",
            "GT", item.genotype,
        ]))
    return "\n".join(lines) + "\n"


def _contig_sort_key(chrom: str) -> tuple[int, str]:
    bare = chrom[3:] if chrom.lower().startswith("chr") else chrom
    return (int(bare), "") if bare.isdigit() else (99, bare)


def verify(text: str, sample: str) -> tuple[object, coverage_mod.CoverageReport]:
    """
    The repository's own gates, applied before anything is written.

    This is deliberately the application's code rather than a second opinion:
    a file that this script considers good and the application rejects would be
    worse than no file at all.
    """
    try:
        metadata = validate_vcf(text.encode("utf-8"), filename=f"{sample}.vcf")
    except VcfValidationError as exc:
        raise BuildRefused(
            f"the application's own validator rejected the generated file "
            f"({exc.code.value}): {exc.message}"
        ) from exc
    return metadata, coverage_mod.assess(text)


def assert_conforming(report: coverage_mod.CoverageReport) -> None:
    """
    Every required position of every VCF-readable gene must be a complete,
    unfiltered, observed genotype.

    Stricter than the application's gate on purpose, and never weaker: the gate
    decides what is safe to answer, this decides what is fit to ship as a
    showcase input. A file that only just clears the gate would make the demo
    depend on a threshold rather than on the data.
    """
    shortfalls: list[str] = []
    for gene in VCF_READABLE_GENES:
        entry = report.genes.get(gene)
        if entry is None:
            shortfalls.append(f"{gene}: absent from the coverage report")
            continue
        valid = entry.evidence_counts.get(
            coverage_mod.EvidenceStatus.VALID.value, 0
        )
        if valid != entry.required:
            other = {
                name: count
                for name, count in entry.evidence_counts.items()
                if count and name != coverage_mod.EvidenceStatus.VALID.value
            }
            shortfalls.append(
                f"{gene}: {valid} of {entry.required} positions carry an "
                f"observed, unfiltered genotype" + (f" ({other})" if other else "")
            )
    if shortfalls:
        raise BuildRefused(
            "the generated file does not meet the showcase input requirement, "
            "so nothing was written:\n  - " + "\n  - ".join(shortfalls)
        )


def cyp2d6_call(sample: str) -> dict | None:
    """
    The source's own CYP2D6 diplotype, as an OPTIONAL second input.

    This is the one legitimate route to a codeine result, and it is deliberately
    not a route through the VCF. CYP2D6 star alleles depend on copy number and
    on hybrids with CYP2D7; no amount of single-position genotype establishes
    them, so this application declines CYP2D6 from any VCF and goes on doing so.
    What changes here is that a diplotype produced by a caller that DID read the
    reads can be supplied alongside the file, labelled as supplied.

    Returns None rather than guessing when the source did not make a confident
    call: a non-PASS filter, a missing genotype, or notation this application's
    own grammar would refuse. Emitting any of those would move the uncertainty
    out of sight instead of reporting it.
    """
    from app import outside_calls

    url = (f"https://{BUCKET}.s3.amazonaws.com/{PREFIX}/{sample}/"
           f"{TARGETED_OBJECT.format(sample=sample)}")
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            if response.status != 200:
                raise BuildRefused(f"the targeted-caller object returned HTTP {response.status}")
            payload = json.loads(response.read())
    except urllib.error.URLError as exc:
        raise BuildRefused(f"could not read the targeted-caller object: {scrub(exc)}") from exc

    entry = payload.get("cyp2d6") or {}
    diplotype = str(entry.get("genotype") or "").strip()
    filter_value = str(entry.get("genotypeFilter") or "").strip()
    if not diplotype:
        return None
    if filter_value.upper() != "PASS":
        # The caller declined to stand behind it; so does this.
        return None

    # The application's own door decides what is well-formed, so a call that
    # would be refused at upload is never written beside a sample.
    try:
        outside_calls.parse(diplotype, CYP2D6_CALLER)
    except outside_calls.OutsideCallError:
        return None
    assert CYP2D6_CALLER in outside_calls.CALLERS, (
        f"{CYP2D6_CALLER} is not an accepted caller; the sidecar would be refused"
    )

    return {
        "gene": "CYP2D6",
        "diplotype": diplotype,
        "caller": CYP2D6_CALLER,
        "caller_version": str(payload.get("softwareVersion") or ""),
        "genotype_quality": entry.get("genotypeQuality"),
        "total_copy_number": entry.get("totalCopyNumber"),
        "filter": filter_value,
        "source_object": f"{PREFIX}/{sample}/{TARGETED_OBJECT.format(sample=sample)}",
        "source_url": url,
        "not_called_by_pharmaguard": (
            "This diplotype was produced by DRAGEN's targeted CYP2D6 caller "
            "from the sequencing reads. PharmaGuard did not call it, does not "
            "call CYP2D6 from a VCF, and labels every result that rests on it "
            "as supplied."
        ),
    }


def sidecar(
    sample: str,
    url: str,
    text: str,
    census: dict[str, GeneCensus],
    report: coverage_mod.CoverageReport,
    provenance: dict[str, str],
) -> dict:
    """Provenance beside the file: where it came from and how strong it is."""
    return {
        "sample_id": sample,
        "source": {
            "bucket": f"s3://{BUCKET}",
            "object": f"{PREFIX}/{sample}/{sample}.hard-filtered.gvcf.gz",
            "url": url,
            "caller": f"DRAGEN {DRAGEN_VERSION}",
            "reference_build": "GRCh38",
            "registry": "https://registry.opendata.aws/ilmn-dragen-1kgp",
            "retrieved": provenance["retrieved"],
        },
        "transcription": {
            "tool": "scripts/build_showcase_inputs.py",
            "rule": (
                "reference blocks expanded to one row per required position; "
                "genotypes and FILTER carried from the source; alleles matched "
                "base-for-base against PharmCAT's own positions file; phase "
                "dropped; no position inferred as reference"
            ),
            "pharmcat_positions": POSITIONS_VCF.name,
        },
        "output": {
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "bytes": len(text.encode("utf-8")),
            "rows": sum(1 for line in text.splitlines() if not line.startswith("#")),
        },
        "evidence": {
            gene: {
                "required": entry.required,
                "from_reference_block": entry.from_block,
                "from_variant_record": entry.from_variant,
                "uncovered": entry.uncovered,
                "refused": entry.refused,
                "non_pass": entry.non_pass,
                "min_depth": entry.min_depth,
                "min_genotype_quality": entry.min_quality,
            }
            for gene, entry in sorted(census.items())
        },
        "coverage_as_the_application_sees_it": report.as_metrics(),
    }


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def build(sample: str, slice_path: Path, url: str, out: Path | None,
          with_cyp2d6: bool = False) -> dict:
    wanted = required_positions()
    pharmcat = pharmcat_rows()
    missing_rows = [key for key in wanted if key not in pharmcat]
    if missing_rows:
        raise BuildRefused(
            f"{len(missing_rows)} required positions have no row in "
            f"{POSITIONS_VCF.name}; the requirements bundle and the positions "
            f"file disagree, so nothing can be emitted safely."
        )

    variants, reference = read_source(slice_path)
    index = ReferenceIndex(reference)
    outcomes = [
        transcribe(chrom, pos, gene, pharmcat[(chrom, pos)], variants, index)
        for (chrom, pos), gene in sorted(wanted.items(), key=lambda kv: (kv[0][0], kv[0][1]))
    ]
    census = build_census(outcomes)
    provenance = {"retrieved": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    text = render_vcf(sample, outcomes, pharmcat, provenance)
    _, report = verify(text, sample)
    assert_conforming(report)

    meta = sidecar(sample, url, text, census, report, provenance)

    # The CYP2D6 call never enters the VCF. It is written beside it, so that
    # supplying it stays an explicit, separate act by whoever runs the
    # analysis -- and so that the file on its own still produces the decline.
    supplied = cyp2d6_call(sample) if with_cyp2d6 else None
    meta["cyp2d6_outside_call"] = supplied or {
        "available": False,
        "reason": ("the source made no confident CYP2D6 call for this sample; "
                   "codeine stays Unknown, which is the correct output"),
    }

    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        out.with_suffix(".provenance.json").write_text(
            json.dumps(meta, indent=1, sort_keys=False) + "\n", encoding="utf-8"
        )
        if supplied is not None:
            out.with_suffix(".cyp2d6.json").write_text(
                json.dumps(supplied, indent=1, sort_keys=False) + "\n", encoding="utf-8"
            )
    return meta


def print_census(sample: str, census: dict[str, GeneCensus]) -> None:
    print(f"\n  {sample}")
    print(f"  {'gene':9} {'present':>9} {'block':>6} {'variant':>8} "
          f"{'gaps':>5} {'minDP':>6} {'minGQ':>6}")
    for gene in VCF_READABLE_GENES:
        entry = census.get(gene)
        if entry is None:
            continue
        gaps = entry.uncovered + entry.refused + entry.non_pass
        print(f"  {gene:9} {entry.present:>4}/{entry.required:<4} {entry.from_block:>6} "
              f"{entry.from_variant:>8} {gaps:>5} "
              f"{entry.min_depth if entry.min_depth is not None else '-':>6} "
              f"{entry.min_quality if entry.min_quality is not None else '-':>6}")
    for gene in VCF_READABLE_GENES:
        entry = census.get(gene)
        for problem in (entry.problems if entry else []):
            print(f"    ! {gene}: {problem}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--sample", required=True, help="1000 Genomes sample id, e.g. NA12878")
    parser.add_argument("--gvcf", type=Path, help="An already-fetched region slice.")
    parser.add_argument("--out", type=Path, help="Where to write the conforming VCF.")
    parser.add_argument("--report-only", action="store_true",
                        help="Print the census and exit without writing.")
    parser.add_argument("--with-cyp2d6", action="store_true",
                        help="Also write the source's CYP2D6 diplotype as a "
                             "separate optional input (never inside the VCF).")
    args = parser.parse_args(argv)

    if not args.report_only and args.out is None:
        parser.error("either --out or --report-only is required")

    wanted = required_positions()
    url = (f"https://{BUCKET}.s3.amazonaws.com/{PREFIX}/{args.sample}/"
           f"{args.sample}.hard-filtered.gvcf.gz")
    try:
        if args.gvcf is not None:
            if not args.gvcf.is_file():
                raise BuildRefused(f"no such slice: {args.gvcf}")
            slice_path = args.gvcf
        else:
            slice_path = REPO_ROOT / "tmp" / f"{args.sample}.regions.vcf.gz"
            url = fetch_slice(args.sample, regions_for(wanted), slice_path)

        if args.report_only:
            variants, reference = read_source(slice_path)
            pharmcat = pharmcat_rows()
            outcomes = [
                transcribe(c, p, g, pharmcat[(c, p)], variants, ReferenceIndex(reference))
                for (c, p), g in sorted(wanted.items(), key=lambda kv: (kv[0][0], kv[0][1]))
            ]
            print_census(args.sample, build_census(outcomes))
            return 0

        meta = build(args.sample, slice_path, url, args.out, with_cyp2d6=args.with_cyp2d6)
        print(f"  wrote {rel(args.out)}  "
              f"{meta['output']['rows']} rows, {meta['output']['bytes']:,} bytes")
        print(f"  sha256 {meta['output']['sha256']}")
        call = meta.get("cyp2d6_outside_call") or {}
        if call.get("diplotype"):
            print(f"  CYP2D6 {call['diplotype']} supplied by {call['caller']} "
                  f"(copy number {call['total_copy_number']}), written beside the "
                  f"VCF, not inside it")
        elif args.with_cyp2d6:
            print(f"  CYP2D6 none: {call.get('reason')}")
        return 0
    except BuildRefused as exc:
        print(f"\n  REFUSED for {args.sample}: {scrub(exc)}\n", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"\n  {exc.cmd[0]} exited {exc.returncode} for {args.sample}: "
              f"{scrub(exc.stderr)[-400:]}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
