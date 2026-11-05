"""
The A4 adversarial inputs, rebuilt at test time (Phase 9 B6, AC6).

Part A built them once, into an untracked directory, with
`audit/phase9/a4/build_inputs.py` and two inline scripts (A4-22; A4-24 to
A4-26). This module rebuilds every one from the tracked demo files, so the
permanent tests need nothing outside the repository. Each transformation is
Part A's, copied unchanged; B6.log records that every rebuilt input equals
Part A's (compressed ones after decompression).

Two deliberate differences:

* bgzip and gzip are done here in Python (BGZF written by hand), not by the
  command-line tools, so compressed bytes differ while the content is the same;
* the BCF is a committed fixture made by `bcftools view --no-version -Ob` from
  the same base: bcftools may be absent where tests run, and Part A's file
  carried a local path in its header. Its records equal Part A's.

The GRCh37 offsets and lengths are Part A's. The offsets were recalled dbSNP
coordinates and only need to put rows in GRCh37 coordinate space; the lengths
equal NCBI's GRCh37.p13 report (`test_input_robustness.py` checks that).
"""

from __future__ import annotations

import gzip
import hashlib
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "test-data" / "demo" / "demo_confident.vcf"
NORMAL = REPO / "test-data" / "demo" / "demo_normal.vcf"
VARIANTS_ONLY = REPO / "test-data" / "demo" / "demo_variants_only.vcf"
BCF_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "a4" / "A4-06_binary.bcf"
BCF_SHA256 = "dffd9b618f319bdbc1dd7dcbcc27488522608be076f6489e3784545bc82b5e67"

OFFSET_37 = {
    "chr10": 96541616 - 94781859,   # rs4244285
    "chr1": 97915614 - 97450058,    # rs3918290
    "chr6": 18130918 - 18130687,    # rs1142345
    "chr12": 21331549 - 21178615,   # rs4149056
    "chr13": 48619855 - 48045719,   # rs116855232
    "chr22": 42524947 - 42128945,   # rs3892097
}
LEN_37 = {"1": 249250621, "6": 171115067, "10": 135534747, "12": 133851895,
          "13": 115169878, "22": 51304566}
CRITICAL_ROW = "rs4244285"
SWAP = {"A": "C", "C": "G", "G": "T", "T": "A"}
DEFAULT_DRUGS = "clopidogrel"
FOUR_DRUGS = "clopidogrel,simvastatin,fluorouracil,azathioprine"


@dataclass(frozen=True)
class Case:
    id: str
    filename: str
    data: bytes
    drugs: str = DEFAULT_DRUGS


def _read(path: Path) -> tuple[list[str], list[list[str]]]:
    header, rows = [], []
    for line in path.read_text().splitlines():
        if line.startswith("#"):
            header.append(line)
        else:
            rows.append(line.split("\t"))
    return header, rows


def _write(header: list[str], rows: list[list[str]], newline: str = "\n") -> bytes:
    return (newline.join(header + ["\t".join(r) for r in rows]) + newline).encode("utf-8")


def _bgzf_block(chunk: bytes) -> bytes:
    deflate = zlib.compressobj(6, zlib.DEFLATED, -15)
    cdata = deflate.compress(chunk) + deflate.flush()
    header = struct.pack("<BBBBIBBH", 31, 139, 8, 4, 0, 0, 255, 6) + b"BC" + struct.pack("<HH", 2, 25 + len(cdata))
    return header + cdata + struct.pack("<II", zlib.crc32(chunk) & 0xFFFFFFFF, len(chunk))


def bgzf(data: bytes) -> bytes:
    """BGZF, as bgzip writes it: gzip members of at most 0xff00 bytes, then the EOF block."""
    blocks = [_bgzf_block(data[i:i + 0xFF00]) for i in range(0, len(data), 0xFF00)]
    return b"".join(blocks) + _bgzf_block(b"")


def bcf() -> bytes:
    data = BCF_FIXTURE.read_bytes()
    if hashlib.sha256(data).hexdigest() != BCF_SHA256:
        raise AssertionError(f"{BCF_FIXTURE} is not the committed BCF fixture")
    return data


def _gvcf_blocks(rows: list[list[str]]) -> list[list[str]]:
    out, block = [], None
    for r in rows:
        if r[9] == "0/0":
            if block and block[0] == r[0]:
                block[7] = f"PX={r[7].split('=')[1]};END={r[1]}"
                continue
            if block:
                out.append(block)
            block = [r[0], r[1], ".", r[3], "<NON_REF>", ".", "PASS", f"END={r[1]}", "GT", "0/0"]
        else:
            if block:
                out.append(block)
                block = None
            r2 = list(r)
            r2[4] = r[4] + ",<NON_REF>"
            out.append(r2)
    if block:
        out.append(block)
    return out


def _wrong_ref_ten(rows: list[list[str]]) -> list[list[str]]:
    out, changed = [], 0
    for r in rows:
        r2 = list(r)
        if "PX=CYP2C19" in r[7] and r[9] == "0/0" and changed < 10 and len(r[3]) == 1 and r[3] in SWAP:
            new_ref = SWAP[r[3]]
            if new_ref == r[4]:
                new_ref = SWAP[new_ref]
            r2[3] = new_ref
            changed += 1
        out.append(r2)
    return out


def _hg19_sliced_at_grch38() -> bytes:
    """A4-22: GRCh38 positions, every SNV REF swapped, GT 0/0, GRCh37 lengths, no build line."""
    base = BASE.read_text().splitlines()
    meta = [line for line in base if line.startswith("##") and not line.startswith("##contig")]
    chrom = next(line for line in base if line.startswith("#CHROM"))
    rows = [line.split("\t") for line in base if not line.startswith("#")]
    lengths = {f"chr{c}": n for c, n in LEN_37.items()}
    out = []
    for r in rows:
        r2 = list(r)
        if len(r[3]) == 1 and r[3] in SWAP:
            new_ref = SWAP[r[3]]
            alts = [a if a != new_ref else SWAP[new_ref] for a in r[4].split(",")]
            r2[3], r2[4] = new_ref, ",".join(alts)
        r2[9] = "0/0"
        out.append("\t".join(r2))
    header = meta[:1] + [f"##contig=<ID={c},length={n}>" for c, n in lengths.items()] + meta[1:] + [chrom]
    return ("\n".join(header + out) + "\n").encode()


def _tpmt(g1: str, g2: str) -> bytes:
    """A4-24 to A4-26: the all-reference file with TPMT rs1142345 and rs1800460 set."""
    out = []
    for line in NORMAL.read_text().splitlines():
        if not line.startswith("#"):
            p = line.split("\t")
            if p[0] == "chr6" and p[1] == "18130687":
                p[9] = g1
            elif p[0] == "chr6" and p[1] == "18138997":
                p[9] = g2
            line = "\t".join(p)
        out.append(line)
    return ("\n".join(out) + "\n").encode()


def bomb() -> bytes:
    """A4-12f: a small .gz that expands past the decompression cap (150 MB)."""
    header, _ = _read(BASE)
    line = b"chr10\t1\t.\tA\tC\t.\tPASS\t.\tGT\t0/0\n"
    body = ("\n".join(header) + "\n").encode() + line * (150 * 1024 * 1024 // len(line))
    return gzip.compress(body, compresslevel=9, mtime=0)


def build() -> dict[str, Case]:
    """Every A4 input except the gzip bomb, which `bomb()` builds on demand."""
    header, rows = _read(BASE)
    meta = [h for h in header if h.startswith("##")]
    chrom_line = header[-1]
    no_contig = [h for h in meta if not h.startswith("##contig")]
    plain = _write(header, rows)

    rows37 = [[r[0].replace("chr", ""), str(int(r[1]) + OFFSET_37[r[0]])] + r[2:] for r in rows]
    h01 = (no_contig[:1] + ["##reference=file:///ref/ucsc.hg19.fasta"]
           + [f"##contig=<ID={c},length={n},assembly=GRCh37>" for c, n in LEN_37.items()]
           + no_contig[1:] + [chrom_line])
    h02 = no_contig[:1] + [f"##contig=<ID={c},length={n}>" for c, n in LEN_37.items()] + no_contig[1:] + [chrom_line]
    h03 = [h.replace("ID=chr", "ID=") for h in header]
    h08 = meta + ['##ALT=<ID=NON_REF,Description="Represents any possible alternative allele">',
                  '##INFO=<ID=END,Number=1,Type=Integer,Description="End position">', chrom_line]
    rows08a = [r[:4] + [r[4] + ",<NON_REF>"] + r[5:7] + [r[7] + f";END={r[1]}"] + r[8:] for r in rows]
    rows09b = [r[:3] + ["C", "A"] + r[5:] if r[2] == CRITICAL_ROW else list(r) for r in rows]
    pad = [["chr10", str(1_000_000 + i), ".", "A", "C", ".", "PASS", "PX=PAD;" + "X" * 200, "GT", "0/0"]
           for i in range(25_000)]
    rows13a = []
    for r in rows:
        if r[2] == CRITICAL_ROW:
            rows13a.append(r[:9] + ["0/0"])
        rows13a.append(list(r))
    h14 = meta + ['##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Depth">', chrom_line]
    h16 = meta + ['##FILTER=<ID=LowQual,Description="Low quality">', chrom_line]
    h20 = [h.replace("ID=chr", "ID=Chr") for h in header]
    h21 = meta + [chrom_line.rsplit("\t", 1)[0] + "\t<img src=x onerror=alert(1)>"]
    readme = (REPO / "README.md").read_bytes()
    hg19 = _hg19_sliced_at_grch38()

    cases = [
        Case("BASE", "_base_copy.vcf", plain),
        Case("A4-01", "A4-01_grch37_declared.vcf", _write(h01, rows37)),
        Case("A4-02", "A4-02_grch37_lengths_only.vcf", _write(h02, rows37)),
        Case("A4-03", "A4-03_no_chr_prefix.vcf", _write(h03, [[r[0].replace("chr", "")] + r[1:] for r in rows])),
        Case("A4-04", "A4-04_bgzip.vcf.gz", bgzf(plain)),
        Case("A4-05", "A4-05_plain_gzip.vcf.gz", gzip.compress(plain, mtime=0)),
        Case("A4-06", "A4-06_binary.bcf", bcf()),
        Case("A4-07", "A4-07_two_samples.vcf",
             _write(meta + [chrom_line + "\tSECOND_SAMPLE"], [r + ["0/0"] for r in rows])),
        Case("A4-08a", "A4-08a_gvcf_explicit.vcf", _write(h08, rows08a)),
        Case("A4-08b", "A4-08b_gvcf_blocks.vcf", _write(h08, _gvcf_blocks(rows))),
        Case("A4-09a", "A4-09a_ref_mismatch_nonvariant.vcf", _write(header, _wrong_ref_ten(rows))),
        Case("A4-09b", "A4-09b_ref_mismatch_critical.vcf", _write(header, rows09b)),
        Case("A4-10", "A4-10_phased.vcf", _write(header, [r[:9] + [r[9].replace("/", "|")] for r in rows])),
        Case("A4-11", "demo_variants_only.vcf", VARIANTS_ONLY.read_bytes()),
        Case("A4-12a", "A4-12a_empty.vcf", b""),
        Case("A4-12b", "A4-12b_header_only.vcf", _write(header, [])),
        Case("A4-12c", "A4-12c_readme.vcf", readme),
        Case("A4-12d", "A4-12d_binary.vcf",
             bytes.fromhex("89504e470d0a1a0a0000000d49484452") + bytes(range(256)) * 64),
        Case("A4-12e", "A4-12e_6mb.vcf", _write(header, rows + pad)),
        Case("A4-13a", "A4-13a_duplicate_conflict.vcf", _write(header, rows13a)),
        Case("A4-13b", "A4-13b_multiallelic.vcf",
             _write(header, [r[:4] + ["A,T"] + r[5:] if r[2] == CRITICAL_ROW else list(r) for r in rows])),
        Case("A4-14a", "A4-14a_no_gt_cyp2c19.vcf",
             _write(h14, [r[:8] + ["DP", "30"] if "PX=CYP2C19" in r[7] else list(r) for r in rows])),
        Case("A4-14b", "A4-14b_nocall_critical.vcf",
             _write(header, [r[:9] + ["./."] if r[2] == CRITICAL_ROW else list(r) for r in rows])),
        Case("A4-15a", "../../etc/passwd.vcf", plain),
        Case("A4-15b", "Ünïcødé_😀_报告.vcf", readme),
        Case("A4-16", "A4-16_filter_lowqual_critical.vcf",
             _write(h16, [r[:6] + ["LowQual"] + r[7:] if r[2] == CRITICAL_ROW else list(r) for r in rows])),
        Case("A4-17", "A4-17_haploid_critical.vcf",
             _write(header, [r[:9] + ["1"] if r[2] == CRITICAL_ROW else list(r) for r in rows])),
        Case("A4-18", "A4-18_format_dp_gt.vcf", _write(h14, [r[:8] + ["DP:GT", f"30:{r[9]}"] for r in rows])),
        Case("A4-19", "A4-19_crlf.vcf", _write(header, rows, newline="\r\n")),
        Case("A4-20", "A4-20_Chr_prefix.vcf", _write(h20, [[r[0].replace("chr", "Chr")] + r[1:] for r in rows])),
        Case("A4-21", "A4-21_hostile_sample.vcf", _write(h21, rows)),
        Case("A4-22", "A4-22_hg19_sliced_at_grch38.vcf", hg19),
        Case("A4-23", "A4-22_hg19_sliced_at_grch38.vcf", hg19, FOUR_DRUGS),
        Case("A4-24", "A4-24_tpmt_trans_phased.vcf", _tpmt("0|1", "1|0"), "azathioprine"),
        Case("A4-25", "A4-25_tpmt_cis_phased.vcf", _tpmt("0|1", "0|1"), "azathioprine"),
        Case("A4-26", "A4-26_tpmt_unphased.vcf", _tpmt("0/1", "0/1"), "azathioprine"),
    ]
    return {case.id: case for case in cases}
