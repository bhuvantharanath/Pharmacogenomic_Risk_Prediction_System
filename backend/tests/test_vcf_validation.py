"""
VCF validation tests — one per rejection path, plus the accept paths.

Every rejection must produce a specific `VcfErrorCode`, because the API turns
that into a machine-readable `error_code`. A test asserting only "it raised"
would let a regression silently collapse all errors into one code.
"""

from __future__ import annotations

import gzip

import pytest

from app.vcf_validation import (
    MAX_UPLOAD_BYTES,
    ReferenceBuild,
    VcfErrorCode,
    VcfValidationError,
    validate_vcf,
)

MINIMAL_HEADER = (
    "##fileformat=VCFv4.2\n"
    '##contig=<ID=chr10,assembly=GRCh38.p14,species="Homo sapiens">\n'
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n'
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE_1\n"
)
MINIMAL_ROW = "chr10\t94781859\trs4244285\tG\tA\t.\tPASS\t.\tGT\t1/1\n"
MINIMAL_VCF = MINIMAL_HEADER + MINIMAL_ROW


def _expect(raw: bytes, code: VcfErrorCode, filename: str = "test.vcf") -> str:
    with pytest.raises(VcfValidationError) as excinfo:
        validate_vcf(raw, filename)
    assert excinfo.value.code is code, (
        f"expected {code.value}, got {excinfo.value.code.value}: "
        f"{excinfo.value.message}"
    )
    return excinfo.value.message


class TestAccepts:
    def test_minimal_valid_vcf(self) -> None:
        meta = validate_vcf(MINIMAL_VCF.encode())
        assert meta.sample_ids == ["SAMPLE_1"]
        assert meta.reference_build is ReferenceBuild.GRCH38
        assert meta.variant_count == 1
        assert meta.was_gzipped is False

    def test_real_generated_vcf(self, valid_vcf_bytes: bytes) -> None:
        meta = validate_vcf(valid_vcf_bytes, "cyp2c19_poor_metabolizer.vcf")
        assert meta.sample_ids == ["CYP2C19_POOR_METABOLIZER"]
        assert meta.reference_build is ReferenceBuild.GRCH38
        assert meta.variant_count == 306

    def test_gzipped_vcf_is_accepted_and_decompressed(self) -> None:
        meta = validate_vcf(gzip.compress(MINIMAL_VCF.encode()), "test.vcf.gz")
        assert meta.was_gzipped is True
        assert meta.sample_ids == ["SAMPLE_1"]
        # The decompressed text must be what gets handed to PharmCAT.
        assert "rs4244285" in meta.text

    def test_multi_sample_warns_but_accepts(self) -> None:
        vcf = MINIMAL_VCF.replace("SAMPLE_1\n", "SAMPLE_1\tSAMPLE_2\n").replace(
            "GT\t1/1", "GT\t1/1\t0/0"
        )
        meta = validate_vcf(vcf.encode())
        assert meta.sample_ids == ["SAMPLE_1", "SAMPLE_2"]
        assert any("2 samples" in w for w in meta.warnings)

    def test_missing_build_warns_but_accepts(self) -> None:
        vcf = MINIMAL_VCF.replace(
            '##contig=<ID=chr10,assembly=GRCh38.p14,species="Homo sapiens">\n', ""
        )
        meta = validate_vcf(vcf.encode())
        assert meta.reference_build is ReferenceBuild.UNKNOWN
        assert any("does not state a reference build" in w for w in meta.warnings)

    def test_vcf_4_3_warns_but_accepts(self) -> None:
        meta = validate_vcf(MINIMAL_VCF.replace("VCFv4.2", "VCFv4.3").encode())
        assert any("VCFv4.2" in w for w in meta.warnings)


class TestRejects:
    def test_empty_file(self) -> None:
        _expect(b"", VcfErrorCode.EMPTY_FILE)

    def test_whitespace_only_file(self) -> None:
        _expect(b"   \n\n  \t\n", VcfErrorCode.EMPTY_FILE)

    def test_oversized_file(self) -> None:
        oversized = MINIMAL_HEADER.encode() + b"x" * (MAX_UPLOAD_BYTES + 1)
        message = _expect(oversized, VcfErrorCode.FILE_TOO_LARGE)
        assert "5 MB" in message

    def test_binary_upload(self) -> None:
        # A PNG header — not gzip, not UTF-8.
        message = _expect(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xfe\xfd", VcfErrorCode.NOT_VCF,
            filename="photo.png",
        )
        assert "photo.png" in message

    def test_plain_text_that_is_not_vcf(self) -> None:
        _expect(b"hello world\nthis is not a vcf\n", VcfErrorCode.NOT_VCF)

    def test_corrupt_gzip(self) -> None:
        # Correct magic bytes, garbage payload.
        _expect(b"\x1f\x8b" + b"\x00" * 200, VcfErrorCode.CORRUPT_GZIP, "broken.vcf.gz")

    @pytest.mark.parametrize(
        "reference_line",
        [
            "##reference=file:///ref/human_g1k_v37.fasta",
            "##reference=file:///ref/hs37d5.fa",
            "##reference=GRCh37",
            "##reference=file:///ref/ucsc.hg19.fasta",
            "##reference=file:///ref/Homo_sapiens_assembly19.fasta",
        ],
    )
    def test_grch37_reference_lines_are_rejected(self, reference_line: str) -> None:
        """The filename conventions real GRCh37 pipelines actually emit."""
        vcf = MINIMAL_VCF.replace(
            '##contig=<ID=chr10,assembly=GRCh38.p14,species="Homo sapiens">\n',
            reference_line + "\n",
        )
        message = _expect(vcf.encode(), VcfErrorCode.UNSUPPORTED_REFERENCE_BUILD)
        assert "GRCh38" in message
        assert "liftover" in message.lower()

    def test_conflicting_build_declarations_fail_closed(self) -> None:
        """
        A file declaring both builds must be rejected, not silently treated as
        GRCh38 — mis-analysing GRCh37 coordinates produces wrong calls quietly.
        """
        vcf = MINIMAL_VCF.replace(
            "##fileformat=VCFv4.2\n",
            "##fileformat=VCFv4.2\n##reference=file:///ref/human_g1k_v37.fasta\n",
        )
        _expect(vcf.encode(), VcfErrorCode.UNSUPPORTED_REFERENCE_BUILD)

    def test_build_mention_outside_declaration_lines_is_ignored(self) -> None:
        """`##source`/`##commandline` often name a build for historical reasons."""
        vcf = MINIMAL_VCF.replace(
            "##fileformat=VCFv4.2\n",
            "##fileformat=VCFv4.2\n##source=LiftoverVcf from GRCh37 to GRCh38\n",
        )
        meta = validate_vcf(vcf.encode())
        assert meta.reference_build is ReferenceBuild.GRCH38

    def test_hg19_contig_assembly_is_rejected(self) -> None:
        vcf = MINIMAL_VCF.replace("assembly=GRCh38.p14", "assembly=hg19")
        _expect(vcf.encode(), VcfErrorCode.UNSUPPORTED_REFERENCE_BUILD)

    def test_unsupported_vcf_major_version(self) -> None:
        _expect(
            MINIMAL_VCF.replace("VCFv4.2", "VCFv3.3").encode(),
            VcfErrorCode.UNSUPPORTED_VCF_VERSION,
        )

    def test_unparseable_version_string(self) -> None:
        _expect(
            MINIMAL_VCF.replace("VCFv4.2", "banana").encode(),
            VcfErrorCode.UNSUPPORTED_VCF_VERSION,
        )

    def test_missing_chrom_line(self) -> None:
        vcf = "##fileformat=VCFv4.2\n##contig=<ID=chr10,assembly=GRCh38>\n"
        _expect(vcf.encode(), VcfErrorCode.MISSING_CHROM_HEADER)

    def test_space_separated_chrom_line(self) -> None:
        vcf = MINIMAL_VCF.replace("\t", " ")
        _expect(vcf.encode(), VcfErrorCode.MISSING_CHROM_HEADER)

    def test_sites_only_vcf_has_no_sample_column(self) -> None:
        vcf = (
            "##fileformat=VCFv4.2\n"
            "##contig=<ID=chr10,assembly=GRCh38.p14>\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            "chr10\t94781859\trs4244285\tG\tA\t.\tPASS\t.\n"
        )
        message = _expect(vcf.encode(), VcfErrorCode.NO_SAMPLE_COLUMN)
        assert "no sample column" in message.lower()

    def test_header_only_vcf_has_no_variants(self) -> None:
        _expect(MINIMAL_HEADER.encode(), VcfErrorCode.NO_VARIANTS)

    def test_gzip_bomb_is_capped(self) -> None:
        # ~100 MB of zeros compresses to well under the 5 MB upload cap but
        # exceeds the decompression cap.
        bomb = gzip.compress(MINIMAL_HEADER.encode() + b"\0" * (100 * 1024 * 1024))
        assert len(bomb) < MAX_UPLOAD_BYTES, "test bomb must pass the upload check"
        _expect(bomb, VcfErrorCode.DECOMPRESSED_TOO_LARGE, "bomb.vcf.gz")
