"""
PharmaGuard — VCF validation.

Phase 2 replaces the Phase 1 "is it non-empty?" check with real structural
validation. Everything here is a *pre-flight* check: the goal is to fail fast
with a message a student or clinician can act on, rather than let PharmCAT die
with a stack trace 90 seconds later.

Every rejection carries a `VcfErrorCode` so clients can branch on the reason
without string-matching the human message.

What this module does NOT do: call variants or interpret genotypes. That is
PharmCAT's job. It does check one biological fact, because nothing downstream
does: that the REF allele at each required position is GRCh38's
(`reference_check`, Phase 9 B6).
"""

from __future__ import annotations

import functools
import json
import gzip
import re
import zlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from . import reference_check

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
    CONFLICTING_REFERENCE_BUILD = "CONFLICTING_REFERENCE_BUILD"
    NON_HUMAN_GENOME = "NON_HUMAN_GENOME"
    UNSUPPORTED_MULTISAMPLE = "UNSUPPORTED_MULTISAMPLE"
    REFERENCE_ALLELE_MISMATCH = "REFERENCE_ALLELE_MISMATCH"


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


@functools.lru_cache(maxsize=1)
def _build_evidence() -> dict:
    """
    PharmCAT's own build-to-RefSeq-accession mapping, plus contig lengths.

    PharmCAT ships no lengths (no .fai/.dict/chrom.sizes in the jar, no
    `length=` in its positions VCF). The lengths come from NCBI's GRCh38.p14
    and GRCh37.p13 assembly reports, committed with their sha256, and
    derivation stops unless each report's accessions equal PharmCAT's — never
    from memory. An accession is still the stronger signal: `NC_000001.11` IS
    GRCh38 chr1. A length is what the commonest real header carries instead
    (`##contig=<ID=10,length=135534747>`; Phase 9 B6, finding F-06).

    See `scripts/derive_build_evidence.py`.
    """
    path = Path(__file__).parent / "data" / "build_evidence.json"
    if not path.exists():
        return {"accession_to_build": {}, "required_build": "GRCh38"}
    return json.loads(path.read_text())


# --------------------------------------------------------------------------- #
# Contig names
#
# PharmCAT matches CHROM against GRCh38's `chr`-prefixed names and nothing
# else; its own preprocessor renames, but the jar path used here has none. A
# file saying `10` or `Chr10` was therefore previewed as answerable by the
# coverage gate (which compared without the prefix) and then analysed as if
# every position were missing (A4-03, A4-20; finding F-05).
# --------------------------------------------------------------------------- #

_PRIMARY_CONTIG = re.compile(r"(?:chr)?(\d{1,2}|X|Y|M|MT)", re.IGNORECASE)
_CONTIG_ID = re.compile(r"^(##contig=<ID=)([^,>]+)")
_CONTIG_FIELD = re.compile(r'(\w+)=("[^"]*"|[^,>]*)')


def canonical_contig(name: str) -> str:
    """`10`, `Chr10`, `CHR10` -> `chr10`; `M`/`MT` -> `chrM`; anything else unchanged."""
    match = _PRIMARY_CONTIG.fullmatch(name)
    if match is None:
        return name
    core = match.group(1).upper()
    if core in ("M", "MT"):
        return "chrM"
    if core in ("X", "Y"):
        return f"chr{core}"
    number = int(core)
    return f"chr{number}" if 1 <= number <= 22 else name


def normalize_contigs(text: str) -> tuple[str, dict[str, str]]:
    """
    Rewrite primary-chromosome names to `chrN` in the rows and `##contig` IDs.

    Returns the text and {old: new} for every name changed. A file that already
    uses `chrN` comes back as the very same string, so PharmCAT reads it
    byte-identical. Splitting on "\\n" alone keeps every other byte, CRs
    included, exactly where it was.
    """
    renamed: dict[str, str] = {}
    canonical: dict[str, str] = {}
    lines = text.split("\n")
    changed = False
    for i, line in enumerate(lines):
        if line.startswith("#"):
            match = _CONTIG_ID.match(line) if line.startswith("##contig") else None
            if match is None:
                continue
            head, old, cut = match.group(1), match.group(2), match.end()
        else:
            cut = line.find("\t")
            if cut <= 0:
                continue
            head, old = "", line[:cut]
        new = canonical.get(old)
        if new is None:
            new = canonical[old] = canonical_contig(old)
        if new != old:
            renamed[old] = new
            lines[i] = head + new + line[cut:]
            changed = True
    return ("\n".join(lines) if changed else text), renamed


def contig_rename_warning(renamed: dict[str, str]) -> str:
    pairs = sorted(renamed.items(), key=lambda kv: kv[1])
    shown = ", ".join(f"'{old}' as '{new}'" for old, new in pairs[:3])
    more = f" and {len(pairs) - 3} more" if len(pairs) > 3 else ""
    return (
        f"Chromosome names were read in GRCh38's 'chr' form: {shown}{more}. "
        "PharmCAT recognises only names that begin with 'chr'; the positions "
        "themselves are unchanged."
    )


def contig_length_evidence(header_lines: list[str]) -> list[tuple[str, int, str]]:
    """
    (contig, length, verdict) for each primary chromosome whose `##contig` line
    gives a length; the verdict is "GRCh38", "GRCh37" or "neither". Every
    primary chromosome's length differs between the two builds, which
    `derive_build_evidence.py` asserts, so a length is never ambiguous.
    """
    lengths = _build_evidence().get("contig_lengths", {})
    grch38, grch37 = lengths.get("GRCh38", {}), lengths.get("GRCh37", {})
    found = []
    for line in header_lines:
        if not line.startswith("##contig=<"):
            continue
        fields = dict(_CONTIG_FIELD.findall(line[len("##contig=<"):]))
        name = canonical_contig(fields.get("ID", "").strip('"'))
        if name not in grch38 or not fields.get("length", "").isdigit():
            continue
        length = int(fields["length"])
        verdict = ("GRCh38" if length == grch38[name]
                   else "GRCh37" if length == grch37.get(name) else "neither")
        found.append((name, length, verdict))
    return found


#: `species="Mus musculus"` and friends. A VCF that names a non-human species
#: cannot carry human star alleles, so every position lookup misses and the
#: result is a screen of confident Unknowns — wasted work presented as an
#: answer.
_SPECIES = re.compile(r'species\s*=\s*"?([^",>]+)', re.IGNORECASE)
_HUMAN = ("homo sapiens", "human", "h. sapiens", "hsapiens")

#: `ID=NC_000001.11` — a RefSeq accession pins the build exactly.
_ACCESSION = re.compile(r"\b(NC_0000\d{2}\.\d+)\b")


def detect_species(header_lines: list[str]) -> str | None:
    """The species a `##contig` line declares, or None if it declares none."""
    for line in header_lines:
        if not line.startswith(("##contig", "##reference", "##assembly")):
            continue
        found = _SPECIES.search(line)
        if found:
            return found.group(1).strip()
    return None


def detect_build_from_accessions(header_lines: list[str]) -> str | None:
    """
    Build inferred from RefSeq accessions, using PharmCAT's own mapping.

    The strongest signal available: an accession names a build outright, where a
    `##reference=` string is a claim the file makes about itself and can be
    stale or simply wrong.
    """
    table = _build_evidence().get("accession_to_build", {})
    seen = set()
    for line in header_lines:
        if not line.startswith(("##contig", "##reference", "##assembly")):
            continue
        for accession in _ACCESSION.findall(line):
            build = table.get(accession)
            if build:
                seen.add(build)
    if len(seen) == 1:
        return seen.pop()
    # Two builds' accessions in one file is a broken file, not a build.
    return None


def _declared_builds(header_lines: list[str]) -> set[str]:
    """Every build asserted by authoritative header fields.

    Keeping the full set is essential: collapsing contradictory declarations
    to ``Unknown`` or preferring the convenient build would turn a broken file
    into an apparently usable one.
    """
    relevant = [
        line
        for line in header_lines
        if line.startswith(("##reference", "##contig", "##assembly"))
    ]
    table = _build_evidence().get("accession_to_build", {})
    seen: set[str] = set()
    for line in relevant:
        for accession in _ACCESSION.findall(line):
            build = table.get(accession)
            if build:
                seen.add(build)

    blob = "\n".join(relevant)
    if any(pattern.search(blob) for pattern in _GRCH37_PATTERNS):
        seen.add("GRCh37")
    if any(pattern.search(blob) for pattern in _GRCH38_PATTERNS):
        seen.add("GRCh38")
    # A length that is neither build's is refused on its own in validate_vcf.
    seen.update(verdict for _c, _l, verdict in contig_length_evidence(relevant)
                if verdict != "neither")
    return seen


def _detect_reference_build(header_lines: list[str]) -> ReferenceBuild:
    """
    Infer the reference build from the header's *declaration* lines.

    Only `##reference`, `##contig` and `##assembly` are consulted. Free-text
    lines like `##source` or `##commandline` frequently mention a build for
    historical reasons (a liftover tool naming its input) and would produce
    false positives.

    Contradictory declarations are rejected by ``validate_vcf`` before this
    helper is called. Analysing a GRCh37 file as GRCh38 would silently produce
    wrong genotype calls at shifted coordinates, so ambiguity is never resolved
    by choosing a convenient declaration.

    Returns UNKNOWN when the file says nothing, which is common and only warns.
    """
    builds = _declared_builds(header_lines)
    if builds == {"GRCh38"}:
        return ReferenceBuild.GRCH38
    if builds and "GRCh38" not in builds:
        return ReferenceBuild.GRCH37
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
                raise VcfValidationError(
                    VcfErrorCode.CORRUPT_GZIP,
                    "This compressed VCF ended before its compressed-data member was "
                    "complete. Re-create the compressed copy, or upload the "
                    "plain .vcf instead.",
                )
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
# REF identity
# --------------------------------------------------------------------------- #

#: At least this many positions compared, and at least half of them wrong, reads
#: as a different build rather than a damaged file. Wording only: either way
#: the whole file is declined.
_WRONG_BUILD_MIN_COMPARED = 10


def _reference_mismatch(ref: reference_check.ReferenceCheck) -> tuple[VcfErrorCode, str]:
    wrong, compared = len(ref.mismatches), ref.compared
    examples = "; ".join(m.describe() for m in ref.mismatches[:5])
    more = f"; and {wrong - 5} more" if wrong > 5 else ""
    if compared >= _WRONG_BUILD_MIN_COMPARED and 2 * wrong >= compared:
        return VcfErrorCode.UNSUPPORTED_REFERENCE_BUILD, (
            f"The REF alleles at {wrong} of the {compared} required positions in "
            f"this file differ from GRCh38 (for example {examples}). A file this "
            "far from GRCh38 was almost certainly aligned to a different build, "
            "such as GRCh37/hg19, and its genotypes cannot be read at GRCh38 "
            "positions. Re-export it against GRCh38 and upload it again. "
            "See docs/input_requirements.md."
        )
    return VcfErrorCode.REFERENCE_ALLELE_MISMATCH, (
        f"At {wrong} of the {compared} required positions in this file, the REF "
        f"allele is not GRCh38's: {examples}{more}. A genotype is read relative to "
        "its REF allele, so these rows say something other than what they appear "
        "to, and a file that disagrees with GRCh38 anywhere cannot be trusted "
        "elsewhere: no drug is assessed from it. Check that the file was produced "
        "against GRCh38, with the same reference throughout, and upload it again. "
        "See docs/input_requirements.md."
    )


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

    # BCF is VCF's binary form, BGZF-compressed like a .vcf.gz, so it decompresses
    # cleanly and then fails as "not text". Naming the format turns a dead end
    # into a known conversion (A4-06); the command itself is on the input
    # requirements page, as every tool name is.
    if data[:3] == b"BCF":
        raise VcfValidationError(
            VcfErrorCode.NOT_VCF,
            f"'{filename}' is a BCF file, the binary form of VCF, and this "
            "analysis reads text VCF. Convert it to a .vcf (or a compressed "
            ".vcf.gz) and upload that; the input requirements page gives the "
            "command. See docs/input_requirements.md.",
        )

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

    # NUL anywhere, not just in the header.
    #
    # The decode above catches most binary uploads, but a NUL byte is valid
    # UTF-8 and sails through it — so a file that is text at the top and binary
    # further down was being accepted, with the corrupt rows silently failing to
    # parse as genotypes. The whole file is scanned because "is this text?"
    # cannot be answered from a prefix.
    nul_at = data.find(b"\x00")
    if nul_at >= 0:
        line_no = data.count(b"\n", 0, nul_at) + 1
        raise VcfValidationError(
            VcfErrorCode.NOT_VCF,
            f"'{filename}' contains a NUL byte on line {line_no}, so it is not "
            f"a text VCF file. This usually means the file was truncated mid-"
            f"write or corrupted in transfer. Re-export it and upload again.",
        )

    # --- contig names --------------------------------------------------------
    # Before anything reads a row, so the coverage gate, the REF check and
    # PharmCAT all see the same `chrN` names.
    text, renamed = normalize_contigs(text)

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

    # --- species -----------------------------------------------------------
    # Before the build check: a mouse genome is not a GRCh37-vs-GRCh38 problem,
    # and telling someone to lift it over would be useless advice.
    species = detect_species(header_lines)
    if species and species.strip().lower() not in _HUMAN:
        raise VcfValidationError(
            VcfErrorCode.NON_HUMAN_GENOME,
            f"This file declares the species '{species}', and this analysis "
            f"only works on human data (Homo sapiens, GRCh38). Star alleles "
            f"are defined for the human genome, so no result could be produced "
            f"from this file.",
        )

    # --- reference build ---------------------------------------------------
    declared_builds = _declared_builds(header_lines)
    if len(declared_builds) > 1:
        raise VcfValidationError(
            VcfErrorCode.CONFLICTING_REFERENCE_BUILD,
            "The VCF header contains contradictory genome-build declarations "
            f"({', '.join(sorted(declared_builds))}). The analysis cannot choose "
            "one without risking shifted-coordinate genotype calls. Re-export "
            "the file with one internally consistent GRCh38 reference.",
        )

    build = _detect_reference_build(header_lines)
    lengths = contig_length_evidence(header_lines)
    grch38_lengths = _build_evidence().get("contig_lengths", {}).get("GRCh38", {})
    if build is ReferenceBuild.GRCH37:
        grch37 = next(((c, n) for c, n, verdict in lengths if verdict == "GRCh37"), None)
        evidence = (
            f" The header gives {grch37[0]} a length of {grch37[1]:,} bases, which "
            f"is GRCh37's {grch37[0]}; GRCh38's is {grch38_lengths[grch37[0]]:,}."
            if grch37 else ""
        )
        raise VcfValidationError(
            VcfErrorCode.UNSUPPORTED_REFERENCE_BUILD,
            "This file uses an older map of the genome (GRCh37/hg19), and this analysis "
            "needs GRCh38/hg38. The two number the same positions differently, "
            "so the file cannot be read as it stands."
            f"{evidence}\n\n"
            "Converting between them is outside what this analysis does. "
            "Convert the file to GRCh38 and upload it again — the input "
            "requirements page lists the tools that do this. "
            "See docs/input_requirements.md.",
        )
    unknown_length = next(((c, n) for c, n, verdict in lengths if verdict == "neither"), None)
    if unknown_length is not None:
        contig, length = unknown_length
        raise VcfValidationError(
            VcfErrorCode.UNSUPPORTED_REFERENCE_BUILD,
            f"The header gives {contig} a length of {length:,} bases. GRCh38's "
            f"{contig} is {grch38_lengths[contig]:,} bases, so this file was "
            "aligned to a different reference, and its positions cannot be read "
            "as GRCh38 positions. Re-export the file against GRCh38 and upload it "
            "again. See docs/input_requirements.md.",
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
        raise VcfValidationError(
            VcfErrorCode.UNSUPPORTED_MULTISAMPLE,
            f"The VCF contains {len(sample_ids)} samples "
            f"({', '.join(sample_ids[:3])}{'…' if len(sample_ids) > 3 else ''}). "
            "This analysis currently accepts exactly one sample per upload; "
            "split the file by sample and upload one sample at a time.",
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

    # --- REF identity --------------------------------------------------------
    # The whole file, not the rows: a REF that contradicts GRCh38 says the file
    # was made against another reference, which cannot be confined to the rows
    # where it happens to show (A4-09a/b, A4-22; finding F-02).
    ref = reference_check.check(text)
    if ref.mismatches:
        raise VcfValidationError(*_reference_mismatch(ref))

    if build is ReferenceBuild.UNKNOWN:
        if ref.compared:
            # The header is silent, but the file is not: every REF it gives at a
            # required position is GRCh38's.
            build = ReferenceBuild.GRCH38
            warnings.append(
                "The VCF header does not state a reference build. The REF alleles "
                f"at all {ref.compared} required positions in this file match "
                "GRCh38, so it is read as GRCh38."
            )
        else:
            warnings.append(
                "The VCF header does not state a reference build; assuming GRCh38. "
                "If it is actually GRCh37/hg19, the results will be wrong."
            )
    if renamed:
        warnings.append(contig_rename_warning(renamed))

    return VcfMetadata(
        sample_ids=sample_ids,
        reference_build=build,
        variant_count=variant_count,
        was_gzipped=was_gzipped,
        fileformat=fileformat,
        warnings=warnings,
        text=text,
    )
