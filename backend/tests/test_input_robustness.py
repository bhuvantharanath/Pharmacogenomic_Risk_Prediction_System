"""
The rules behind B6's input checks (Phase 9 B6, audit/phase9/B6_PLAN.md).

test_a4_inputs.py proves the behaviour on Part A's files. These pin the parts
those files cannot reach on their own: where the data comes from and that it
re-derives, the edges of each rule, and the one promise a normal file depends
on — that a `chr`-named file reaches PharmCAT byte-identical.
"""

from __future__ import annotations

import hashlib
import json
import sys

import pytest

from app import coverage, reference_check
from app.vcf_validation import (
    ReferenceBuild,
    VcfErrorCode,
    VcfValidationError,
    canonical_contig,
    normalize_contigs,
    validate_vcf,
)
from tests import a4_inputs
from tests.conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

EVIDENCE = json.loads((REPO_ROOT / "backend/app/data/build_evidence.json").read_text())
ALLELES = json.loads((REPO_ROOT / "backend/app/data/reference_alleles.json").read_text())
REQUIREMENTS = json.loads((REPO_ROOT / "backend/app/data/position_requirements.json").read_text())
JAR = REPO_ROOT / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
POSITIONS_VCF = REPO_ROOT / "test-data/reference/tools/pharmcat_positions_3.4.0.vcf.bgz"
GRCH38 = EVIDENCE["contig_lengths"]["GRCh38"]
# .get: a missing table must fail the tests below, not stop collection (sabotage SB6-b).
GRCH37 = EVIDENCE["contig_lengths"].get("GRCh37", {})
COLUMNS = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
OFF_TARGET = "chr10\t100\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\n"  # not a required position


def _vcf(*header: str, rows: str = OFF_TARGET) -> bytes:
    return ("##fileformat=VCFv4.2\n" + "".join(header) + COLUMNS + rows).encode()


def _refuse(payload: bytes, code: VcfErrorCode) -> str:
    with pytest.raises(VcfValidationError) as exc:
        validate_vcf(payload, filename="t.vcf")
    assert exc.value.code is code, (exc.value.code, exc.value.message[:200])
    return exc.value.message


def _row(chrom: str, pos: int, ref: str, alt: str = "N", gt: str = "0/0", info: str = ".") -> str:
    return f"{chrom}\t{pos}\t.\t{ref}\t{alt}\t.\tPASS\t{info}\tGT\t{gt}\n"


# --------------------------------------------------------------------------- #
# Where the data comes from
# --------------------------------------------------------------------------- #


def test_the_ncbi_reports_are_the_files_whose_hashes_are_recorded() -> None:
    for build, source in EVIDENCE["contig_length_sources"].items():
        data = (REPO_ROOT / source["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == source["sha256"], build
        assert source["url"].endswith(source["file"].rsplit("/", 1)[1])


def test_every_primary_chromosome_has_a_length_that_differs_between_builds() -> None:
    expected = {f"chr{n}" for n in [*range(1, 23), "X", "Y"]}
    assert set(GRCH38) == set(GRCH37) == expected
    assert all(GRCH38[c] != GRCH37[c] for c in expected)
    assert GRCH38["chr10"] == 133797422 and GRCH37["chr10"] == 135534747


def test_part_as_recalled_grch37_lengths_match_ncbi() -> None:
    """A4-01/02/22 were built with lengths typed from memory; they were right."""
    assert {f"chr{c}": n for c, n in a4_inputs.LEN_37.items()} == {f"chr{c}": GRCH37[f"chr{c}"]
                                                                    for c in a4_inputs.LEN_37}


@pytest.mark.skipif(not JAR.is_file(), reason="pinned PharmCAT jar absent")
def test_build_evidence_rederives_from_its_sources() -> None:
    import derive_build_evidence

    assert derive_build_evidence.derive() == EVIDENCE


@pytest.mark.skipif(not (JAR.is_file() and POSITIONS_VCF.is_file()), reason="pinned PharmCAT files absent")
def test_reference_alleles_rederive_from_pharmcat() -> None:
    import derive_reference_alleles

    assert derive_reference_alleles.derive() == ALLELES


def test_every_required_position_has_a_reference_base() -> None:
    required = {f"{c}:{p}" for spec in REQUIREMENTS["genes"].values() for c, p in spec["positions"]}
    assert set(ALLELES["alleles"]) == required
    assert ALLELES["count"] == len(required) == 484
    assert {entry["base"] for entry in ALLELES["alleles"].values()} <= set("ACGT")
    assert ALLELES["alleles"]["chr10:94781859"] == {"base": "G", "gene": "CYP2C19", "rsid": "rs4244285"}


# --------------------------------------------------------------------------- #
# Contig names
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("name", "canonical"), [
    ("10", "chr10"), ("Chr10", "chr10"), ("CHR10", "chr10"), ("chr10", "chr10"),
    ("x", "chrX"), ("Y", "chrY"), ("MT", "chrM"), ("M", "chrM"), ("chrM", "chrM"),
    ("23", "23"), ("0", "0"), ("chrUn_KI270302v1", "chrUn_KI270302v1"),
    ("NC_000010.11", "NC_000010.11"), ("HLA-A*01:01:01:01", "HLA-A*01:01:01:01"),
])
def test_only_primary_chromosome_names_are_rewritten(name: str, canonical: str) -> None:
    assert canonical_contig(name) == canonical


def test_a_chr_named_file_reaches_pharmcat_byte_identical() -> None:
    raw = a4_inputs.BASE.read_text()
    text, renamed = normalize_contigs(raw)
    assert text is raw and renamed == {}
    assert validate_vcf(raw.encode()).text == raw


def test_a_rename_keeps_every_other_byte_including_crlf() -> None:
    raw = "##contig=<ID=10,length=133797422>\r\n" + COLUMNS.replace("\n", "\r\n") + "10\t5\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\r\n"
    text, renamed = normalize_contigs(raw)
    assert renamed == {"10": "chr10"}
    assert text == raw.replace("ID=10,", "ID=chr10,").replace("\r\n10\t", "\r\nchr10\t")


# --------------------------------------------------------------------------- #
# Contig lengths
# --------------------------------------------------------------------------- #


def test_grch38_lengths_alone_establish_the_build() -> None:
    meta = validate_vcf(_vcf(f"##contig=<ID=chr10,length={GRCH38['chr10']}>\n"))
    assert meta.reference_build is ReferenceBuild.GRCH38
    assert not [w for w in meta.warnings if "reference build" in w]


def test_a_grch37_and_a_grch38_length_conflict() -> None:
    message = _refuse(_vcf(f"##contig=<ID=chr1,length={GRCH38['chr1']}>\n",
                           f"##contig=<ID=chr10,length={GRCH37['chr10']}>\n"),
                      VcfErrorCode.CONFLICTING_REFERENCE_BUILD)
    assert "GRCh37" in message and "GRCh38" in message


def test_a_declaration_and_a_contradicting_length_conflict() -> None:
    _refuse(_vcf("##reference=GRCh38\n", f"##contig=<ID=10,length={GRCH37['chr10']}>\n"),
            VcfErrorCode.CONFLICTING_REFERENCE_BUILD)


def test_a_length_that_is_neither_build_is_refused() -> None:
    message = _refuse(_vcf(f"##contig=<ID=chr10,length={GRCH38['chr10'] + 1}>\n"),
                      VcfErrorCode.UNSUPPORTED_REFERENCE_BUILD)
    assert f"GRCh38's chr10 is {GRCH38['chr10']:,} bases" in message


def test_a_length_on_a_contig_outside_the_table_is_ignored() -> None:
    meta = validate_vcf(_vcf("##contig=<ID=chrM,length=16571>\n", "##contig=<ID=chrUn_x,length=5>\n"))
    assert meta.reference_build is ReferenceBuild.UNKNOWN


# --------------------------------------------------------------------------- #
# REF identity
# --------------------------------------------------------------------------- #


def _critical(ref: str) -> str:
    return _row("chr10", 94781859, ref, "A", "1/1")


def test_a_lowercase_ref_is_still_grch38s_base() -> None:
    assert validate_vcf(_vcf("##reference=GRCh38\n", rows=_critical("g"))).reference_build is ReferenceBuild.GRCH38


def test_an_indel_is_checked_on_its_anchor_base() -> None:
    """DPYD chr1:97450065 is a deletion, REF `TG` in PharmCAT's definition."""
    assert ALLELES["alleles"]["chr1:97450065"]["base"] == "T"
    validate_vcf(_vcf("##reference=GRCh38\n", rows=_row("chr1", 97450065, "TG", "T")))
    _refuse(_vcf("##reference=GRCh38\n", rows=_row("chr1", 97450065, "AG", "A")),
            VcfErrorCode.REFERENCE_ALLELE_MISMATCH)


def test_a_position_with_two_rows_counts_once() -> None:
    rows = _critical("C") + _critical("C") + _row("chr10", 94761900, "C")
    result = reference_check.check(rows)
    assert result.compared == 2
    assert [(m.pos, m.file_base, m.grch38_base) for m in result.mismatches] == [(94781859, "C", "G")]


def test_the_wording_turns_to_build_only_when_most_of_many_positions_differ() -> None:
    positions = [(c, p) for c, p in REQUIREMENTS["genes"]["CYP2C19"]["positions"]][:12]
    wrong = {"A": "C", "C": "G", "G": "T", "T": "A"}

    def rows(n_wrong: int) -> str:
        out = ""
        for i, (c, p) in enumerate(positions):
            base = ALLELES["alleles"][f"{c}:{p}"]["base"]
            out += _row(c, p, wrong[base] if i < n_wrong else base)
        return out

    _refuse(_vcf(rows=rows(5)), VcfErrorCode.REFERENCE_ALLELE_MISMATCH)     # 5 of 12
    message = _refuse(_vcf(rows=rows(6)), VcfErrorCode.UNSUPPORTED_REFERENCE_BUILD)  # 6 of 12
    assert "6 of the 12 required positions" in message
    nine = "".join(_row(c, p, wrong[ALLELES["alleles"][f"{c}:{p}"]["base"]]) for c, p in positions[:9])
    _refuse(_vcf(rows=nine), VcfErrorCode.REFERENCE_ALLELE_MISMATCH)        # 9 of 9: too few to call a build


def test_a_silent_header_with_verified_refs_says_how_the_build_was_read() -> None:
    meta = validate_vcf(_vcf(rows=_critical("G")))
    assert meta.reference_build is ReferenceBuild.GRCH38
    assert any("REF alleles at all 1 required positions in this file match GRCh38" in w for w in meta.warnings)


# --------------------------------------------------------------------------- #
# gVCF blocks
# --------------------------------------------------------------------------- #


def _gvcf(marker: str, end_offset: int) -> str:
    positions = [p for _, p in REQUIREMENTS["genes"]["CYP2C19"]["positions"]]
    start = min(positions) - 1
    end = max(positions) + end_offset
    return "##fileformat=VCFv4.2\n" + COLUMNS + _row("chr10", start, "N", marker, "0/0", f"END={end}")


@pytest.mark.parametrize("marker", ["<NON_REF>", "<*>"])
def test_required_positions_inside_a_reference_block_are_counted(marker: str) -> None:
    report = coverage.assess(_gvcf(marker, 0))
    assert report.gvcf_block_positions == 35
    assert report.genes["CYP2C19"].present == 0
    assert report.variants_only is False


def test_a_record_ending_where_it_starts_is_not_a_block() -> None:
    text = "##fileformat=VCFv4.2\n" + COLUMNS + _row("chr10", 94781859, "G", "<NON_REF>", "0/0", "END=94781859")
    assert coverage.assess(text).gvcf_block_positions == 0


def test_an_ordinary_end_is_not_a_block() -> None:
    """END= on a structural-variant record, with no gVCF marker, is not a reference block."""
    text = "##fileformat=VCFv4.2\n" + COLUMNS + _row("chr10", 94761000, "N", "<DEL>", "0/1", "END=94790000")
    assert coverage.assess(text).gvcf_block_positions == 0
