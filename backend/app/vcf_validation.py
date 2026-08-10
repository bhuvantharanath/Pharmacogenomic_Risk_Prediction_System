"""
PharmaGuard — VCF validation.

Phase 2 replaces the Phase 1 "is it non-empty?" check with real structural
validation. Everything here is a *pre-flight* check: the goal is to fail fast
with a message a student or clinician can act on, rather than let PharmCAT die
with a stack trace 90 seconds later.

Every rejection carries a `VcfErrorCode` so clients can branch on the reason
without string-matching the human message.

What this module does NOT do: call variants, interpret genotypes, or check that
positions are biologically sensible. That is PharmCAT's job.
"""

from __future__ import annotations

import gzip
import re
import zlib
from dataclasses import dataclass, field
from enum import Enum

# --------------------------------------------------------------------------- #
# Limits
# --------------------------------------------------------------------------- #

# 5 MB of *uploaded* bytes, per the Phase 2 spec. A PharmCAT-preprocessed
# single-sample PGx VCF is a few hundred KB, so this is generous; a whole-genome
# VCF is far larger and should be preprocessed before upload.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

# Guard against a decompression bomb: a few KB of gzip can expand to gigabytes.
# 20x the upload cap is far more than any legitimate PGx VCF needs.
MAX_DECOMPRESSED_BYTES = 20 * MAX_UPLOAD_BYTES

# Only scan the head of the file for header lines. VCF requires all `##` meta
# lines to precede `#CHROM`, so the header is always at the top.
_HEADER_SCAN_BYTES = 512 * 1024


class VcfErrorCode(str, Enum):
    """Machine-readable rejection reasons. Returned as `error_code` on 400s."""

    EMPTY_FILE = "EMPTY_FILE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    CORRUPT_GZIP = "CORRUPT_GZIP"
    DECOMPRESSED_TOO_LARGE = "DECOMPRESSED_TOO_LARGE"
    NOT_VCF = "NOT_VCF"
    UNSUPPORTED_VCF_VERSION = "UNSUPPORTED_VCF_VERSION"
    MISSING_CHROM_HEADER = "MISSING_CHROM_HEADER"
    NO_SAMPLE_COLUMN = "NO_SAMPLE_COLUMN"
    NO_VARIANTS = "NO_VARIANTS"
    UNSUPPORTED_REFERENCE_BUILD = "UNSUPPORTED_REFERENCE_BUILD"


class ReferenceBuild(str, Enum):
    GRCH38 = "GRCh38"
    GRCH37 = "GRCh37"
    UNKNOWN = "Unknown"


class VcfValidationError(Exception):
    """A rejection the user can understand and act on. Always becomes a 400."""

    def __init__(self, code: VcfErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class VcfMetadata:
    """What validation learned about the file. Feeds `quality_metrics`."""

    sample_ids: list[str]
    reference_build: ReferenceBuild
    variant_count: int
    was_gzipped: bool
    fileformat: str
    # Non-fatal observations to surface in the API response.
    warnings: list[str] = field(default_factory=list)
    # The decompressed bytes, ready to hand to PharmCAT.
    text: str = ""


# --------------------------------------------------------------------------- #
# Build detection
#
# Order matters: `##reference` and contig `assembly=` are explicit statements by
# the file's producer, so they win. The hg19/hg38 aliases are checked as whole
# tokens to avoid matching, say, a sample named "hg19_control".
# --------------------------------------------------------------------------- #

def _token(word: str) -> re.Pattern[str]:
    """
    Match `word` as a standalone token inside a filename or URI.

    `\\b` is wrong here: reference paths separate tokens with underscores
    (`human_g1k_v37.fasta`), and `_` is a word character, so `\\bv37\\b` never
    fires after one. These lookarounds treat anything non-alphanumeric —
    underscore, dot, slash, hyphen — as a separator.
    """
    return re.compile(rf"(?<![a-z0-9]){word}(?![a-z0-9])", re.IGNORECASE)


_GRCH38_PATTERNS = (
    _token("grch38"),
    _token("hg38"),
    _token("b38"),
    _token("v38"),
    re.compile(r"hs38", re.IGNORECASE),
)
# Covers the filename conventions real GRCh37 pipelines leave in `##reference`:
# human_g1k_v37.fasta, hs37d5.fa, ucsc.hg19.fasta, Homo_sapiens_assembly19.fasta.
_GRCH37_PATTERNS = (
    _token("grch37"),
    _token("hg19"),
    _token("b37"),
    _token("v37"),
    re.compile(r"hs37", re.IGNORECASE),
    re.compile(r"assembly19", re.IGNORECASE),
)


def _detect_reference_build(header_lines: list[str]) -> ReferenceBuild:
    """
    Infer the reference build from the header's *declaration* lines.

    Only `##reference`, `##contig` and `##assembly` are consulted. Free-text
    lines like `##source` or `##commandline` frequently mention a build for
    historical reasons (a liftover tool naming its input) and would produce
    false positives.

    Precedence is deliberately asymmetric: **any** GRCh37 signal wins, even when
    GRCh38 is also present. Analysing a GRCh37 file as GRCh38 does not error —
    it silently produces wrong genotype calls at shifted coordinates, which is
    the worst failure available here. A file that declares both is ambiguous,
    and ambiguity should stop the run rather than pick a side.

    Returns UNKNOWN when the file says nothing, which is common and only warns.
    """
    relevant = [
        line
        for line in header_lines
        if line.startswith(("##reference", "##contig", "##assembly"))
    ]
    blob = "\n".join(relevant)

    if any(p.search(blob) for p in _GRCH37_PATTERNS):
        return ReferenceBuild.GRCH37
    if any(p.search(blob) for p in _GRCH38_PATTERNS):
        return ReferenceBuild.GRCH38
    return ReferenceBuild.UNKNOWN


# --------------------------------------------------------------------------- #
# Decompression
# --------------------------------------------------------------------------- #


def _looks_gzipped(raw: bytes) -> bool:
    """Gzip (and therefore bgzip) magic number."""
    return raw[:2] == b"\x1f\x8b"


def _decompress(raw: bytes) -> bytes:
    """
    Decompress gzip/bgzip with a hard output cap.

    bgzip files are a concatenation of gzip members; `gzip.decompress` handles
    that, but it has no size limit, so we drive zlib directly instead.
    """
    out = bytearray()
    stream = memoryview(raw)
    try:
        while stream:
            # wbits=47 => auto-detect gzip/zlib header, needed per member.
            decompressor = zlib.decompressobj(47)
            out += decompressor.decompress(stream, MAX_DECOMPRESSED_BYTES - len(out))
            if len(out) >= MAX_DECOMPRESSED_BYTES:
                raise VcfValidationError(
                    VcfErrorCode.DECOMPRESSED_TOO_LARGE,
                    "The compressed file expands to more than "
                    f"{MAX_DECOMPRESSED_BYTES // (1024 * 1024)} MB. Please upload a "
                    "VCF restricted to pharmacogenomic positions.",
                )
            if not decompressor.eof:
                # Truncated final member.
                break
            stream = decompressor.unused_data
            if not stream:
                break
    except zlib.error as exc:
        raise VcfValidationError(
            VcfErrorCode.CORRUPT_GZIP,
            f"This file looks compressed, but it could not be opened ({exc}). "
            "Re-create the compressed copy, or upload the plain .vcf "
            "instead.",
        ) from exc
    return bytes(out)


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #


def validate_vcf(raw: bytes, filename: str = "upload.vcf") -> VcfMetadata:
    """
    Validate an uploaded VCF and return what we learned about it.

    Raises `VcfValidationError` (-> HTTP 400) for anything wrong. Accepts plain
    and gzip/bgzip-compressed input.
    """
    if not raw or not raw.strip():
        raise VcfValidationError(
            VcfErrorCode.EMPTY_FILE,
            "The uploaded file is empty. Please choose a VCF file with content.",
        )

    if len(raw) > MAX_UPLOAD_BYTES:
        raise VcfValidationError(
            VcfErrorCode.FILE_TOO_LARGE,
            # Actionable, because this rejection is almost always a
            # *shape* problem rather than a genuinely oversized file. A VCF
            # restricted to PharmCAT's 306 required positions is ~194 KB —
            # roughly 25x under the cap — so a 28 MB upload means a
            # whole-chromosome or whole-genome file, not a PGx one. Saying
            # only "too large" invites the wrong fix (raise the limit); saying
            # what a conforming file looks like points at the right one.
            f"The file is {len(raw) / (1024 * 1024):.1f} MB, over the "
            f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.\n\n"
            "This is usually a sign the file covers far more of your DNA "
            "than this analysis needs. A VCF restricted to PharmCAT's "
            "required positions is typically well under 1 MB — around 200 KB "
            "for all seven genes — so there is plenty of room to spare for a "
            "conforming file.\n\n"
            "To fix it, restrict the file to the positions this analysis "
            "needs rather than trimming it arbitrarily. The input "
            "requirements page gives the exact command.\n\n"
            "Keep every required position with an explicit genotype, "
            "including homozygous-reference calls — dropping those produces a "
            "file that is small but unusable. See docs/input_requirements.md.",
        )

    warnings: list[str] = []
    was_gzipped = _looks_gzipped(raw)
    data = _decompress(raw) if was_gzipped else raw

    # A binary (non-VCF) upload usually fails here rather than on the header
    # check, and "is not valid UTF-8" is a clearer diagnosis than "no header".
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VcfValidationError(
            VcfErrorCode.NOT_VCF,
            f"'{filename}' is not a text VCF file — it contains data this "
            "analysis cannot read. Upload a .vcf file, or a compressed "
            ".vcf.gz.",
        ) from exc

    # --- header ------------------------------------------------------------
    head = text[:_HEADER_SCAN_BYTES]
    header_lines = [ln for ln in head.splitlines() if ln.startswith("##")]

    fileformat_line = next(
        (ln for ln in header_lines if ln.startswith("##fileformat=")), None
    )
    if fileformat_line is None:
        raise VcfValidationError(
            VcfErrorCode.NOT_VCF,
            f"'{filename}' does not start with a '##fileformat=VCFv4.x' header, so "
            "it is not a VCF file.",
        )

    fileformat = fileformat_line.split("=", 1)[1].strip()
    version_match = re.fullmatch(r"VCFv(\d+)\.(\d+)", fileformat)
    if version_match is None:
        raise VcfValidationError(
            VcfErrorCode.UNSUPPORTED_VCF_VERSION,
            f"Unrecognised VCF version '{fileformat}'. This analysis expects VCFv4.x "
            "(v4.2 is what PharmCAT is built around).",
        )
    major, minor = int(version_match.group(1)), int(version_match.group(2))
    if major != 4:
        raise VcfValidationError(
            VcfErrorCode.UNSUPPORTED_VCF_VERSION,
            f"VCF version {fileformat} is not supported. Please upload VCFv4.x "
            "(ideally v4.2).",
        )
    if minor != 2:
        # 4.1 and 4.3 are close enough that PharmCAT usually copes; say so
        # rather than blocking a file that would have worked.
        warnings.append(
            f"VCF is {fileformat}; PharmCAT targets VCFv4.2. Processing anyway, "
            "but check results carefully."
        )

    # --- reference build ---------------------------------------------------
    build = _detect_reference_build(header_lines)
    if build is ReferenceBuild.GRCH37:
        raise VcfValidationError(
            VcfErrorCode.UNSUPPORTED_REFERENCE_BUILD,
            "This file uses an older map of the genome (GRCh37/hg19), and this analysis "
            "needs GRCh38/hg38. The two number the same positions differently, "
            "so the file cannot be read as it stands.\n\n"
            "Converting between them is outside what this analysis does. "
            "Convert the file to GRCh38 and upload it again — the input "
            "requirements page lists the tools that do this. "
            "See docs/input_requirements.md.",
        )
    if build is ReferenceBuild.UNKNOWN:
        warnings.append(
            "The VCF header does not state a reference build; assuming GRCh38. "
            "If it is actually GRCh37/hg19, the results will be wrong."
        )

    # --- #CHROM line and samples -------------------------------------------
    chrom_line = next(
        (ln for ln in head.splitlines() if ln.startswith("#CHROM")), None
    )
    if chrom_line is None:
        raise VcfValidationError(
            VcfErrorCode.MISSING_CHROM_HEADER,
            "The VCF has no '#CHROM' column-header line, so its columns cannot be "
            "interpreted.",
        )

    columns = chrom_line.lstrip("#").split("\t")
    if len(columns) == 1:
        # Almost always a file that got space-separated somewhere in transit.
        raise VcfValidationError(
            VcfErrorCode.MISSING_CHROM_HEADER,
            "The '#CHROM' line is not tab-separated. VCF requires tab delimiters.",
        )
    # 8 fixed columns; a genotyped VCF adds FORMAT + >=1 sample.
    if len(columns) < 10:
        raise VcfValidationError(
            VcfErrorCode.NO_SAMPLE_COLUMN,
            "The VCF contains no sample column, so there are no genotypes to "
            "analyse. This analysis needs a VCF with at least one sample.",
        )

    sample_ids = [c.strip() for c in columns[9:] if c.strip()]
    if not sample_ids:
        raise VcfValidationError(
            VcfErrorCode.NO_SAMPLE_COLUMN,
            "The VCF's sample column has no name. Please provide a VCF with a "
            "named sample.",
        )
    if len(sample_ids) > 1:
        warnings.append(
            f"The VCF contains {len(sample_ids)} samples "
            f"({', '.join(sample_ids[:3])}{'…' if len(sample_ids) > 3 else ''}); "
            f"only the first one is analysed ({sample_ids[0]})."
        )

    # --- data rows ---------------------------------------------------------
    variant_count = sum(
        1 for line in text.splitlines() if line and not line.startswith("#")
    )
    if variant_count == 0:
        raise VcfValidationError(
            VcfErrorCode.NO_VARIANTS,
            "The VCF has a valid header but contains no variant rows, so there is "
            "nothing to analyse.",
        )

    return VcfMetadata(
        sample_ids=sample_ids,
        reference_build=build,
        variant_count=variant_count,
        was_gzipped=was_gzipped,
        fileformat=fileformat,
        warnings=warnings,
        text=text,
    )
