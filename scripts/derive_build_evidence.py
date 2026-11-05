#!/usr/bin/env python3
"""
Vendor the genome-build evidence into `backend/app/data/build_evidence.json`.

    python scripts/derive_build_evidence.py            # rewrite the file
    python scripts/derive_build_evidence.py --check    # exit 1 if it differs
    python scripts/derive_build_evidence.py --fetch    # re-download NCBI's reports first

WHAT PHARMCAT ACTUALLY SHIPS — and what it does not

PharmCAT does not ship contig lengths. Checked:

  definition/chr_build_mapping.tsv    build, chromosome, chr name, RefSeq accession
  pharmcat_positions_3.4.0.vcf.bgz    ##contig=<ID=chrN,assembly=GRCh38.p14,
                                      species="Homo sapiens">   — no length field
  (no .fai, .dict, or chrom.sizes anywhere in the jar)

What PharmCAT does ship is a build-to-RefSeq-accession mapping covering
b36/b37/b38. An accession is unambiguous — `NC_000001.11` IS GRCh38 chr1.

CONTIG LENGTHS (Phase 9 B6)

An earlier brief forbade lengths from memory or an outside source, so they were
not used, and this script said so. That left the commonest real GRCh37 header —
`##contig=<ID=10,length=135534747>` from bcftools, GATK or DeepVariant, with no
accession and no declaration — undetected (audit finding F-06). The Phase 9
brief asks for lengths. They come from NCBI's assembly reports for GRCh38.p14
and GRCh37.p13, committed under test-data/reference/ncbi/ with their URL and
sha256 recorded in the output, so every length traces to a file, never to
memory. Each report's RefSeq accession for each chromosome must equal
PharmCAT's own mapping, or derivation stops: the two sources check each other.

Detection uses, in order of strength:

  1. RefSeq accession in a `##contig` line   -> exact build, PharmCAT-sourced
  2. `length=` of a primary chromosome       -> GRCh38, GRCh37 or neither, NCBI-sourced
  3. `species=` in a `##contig` line         -> refuse non-human
  4. `assembly=` / `##reference=` text       -> declared build (weakest; a
                                                declaration can be wrong)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import urllib.request
import zipfile

REPO = pathlib.Path(__file__).resolve().parents[1]
JAR = REPO / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
MAPPING = "org/pharmgkb/pharmcat/definition/chr_build_mapping.tsv"
OUT = REPO / "backend/app/data/build_evidence.json"
NCBI = REPO / "test-data/reference/ncbi"
BUILD_NAMES = {"b36": "GRCh36", "b37": "GRCh37", "b38": "GRCh38"}
#: build -> (RefSeq assembly accession, assembly name)
ASSEMBLIES = {
    "GRCh38": ("GCF_000001405.40", "GRCh38.p14"),
    "GRCh37": ("GCF_000001405.25", "GRCh37.p13"),
}


def report_name(build: str) -> str:
    accession, name = ASSEMBLIES[build]
    return f"{accession}_{name}_assembly_report.txt"


def report_url(build: str) -> str:
    accession, name = ASSEMBLIES[build]
    return (f"https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/"
            f"{accession}_{name}/{report_name(build)}")


def fetch_reports() -> None:
    NCBI.mkdir(parents=True, exist_ok=True)
    for build in ASSEMBLIES:
        with urllib.request.urlopen(report_url(build), timeout=120) as resp:
            (NCBI / report_name(build)).write_bytes(resp.read())


def jar_contigs() -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    rows = zipfile.ZipFile(JAR).read(MAPPING).decode().splitlines()
    accessions: dict[str, str] = {}
    contigs: dict[str, dict[str, str]] = {}
    for line in rows:
        if not line.strip():
            continue
        build, _num, name, accession = line.split("\t")
        accessions[accession] = BUILD_NAMES[build]
        contigs.setdefault(BUILD_NAMES[build], {})[name] = accession
    return accessions, contigs


def contig_lengths(build: str, text: str, pharmcat: dict[str, str]) -> dict[str, int]:
    """Lengths of chromosomes 1-22, X and Y, keyed `chrN`, from one assembly report."""
    accession, name = ASSEMBLIES[build]
    if f"# Assembly name:  {name}" not in text or f"# RefSeq assembly accession: {accession}" not in text:
        raise SystemExit(f"{report_name(build)} does not describe {name} ({accession})")
    lengths: dict[str, int] = {}
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        fields = line.split("\t")
        seq_name, role, _molecule, location, _genbank, _rel, refseq, _unit, length = fields[:9]
        if role != "assembled-molecule" or location != "Chromosome":
            continue
        contig = f"chr{seq_name}"
        if pharmcat.get(contig) != refseq:
            raise SystemExit(f"{build} {contig}: NCBI says {refseq}, PharmCAT says {pharmcat.get(contig)}")
        lengths[contig] = int(length)
    expected = {f"chr{n}" for n in [*range(1, 23), "X", "Y"]}
    if set(lengths) != expected:
        raise SystemExit(f"{build}: chromosomes {sorted(set(lengths) ^ expected)} missing or extra")
    return lengths


def derive() -> dict:
    accessions, contigs = jar_contigs()
    lengths, sources = {}, {}
    for build in ASSEMBLIES:
        path = NCBI / report_name(build)
        raw = path.read_bytes()
        lengths[build] = contig_lengths(build, raw.decode(), contigs[build])
        sources[build] = {
            "assembly": ASSEMBLIES[build][1],
            "accession": ASSEMBLIES[build][0],
            "url": report_url(build),
            "file": str(path.relative_to(REPO)),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    shared = [c for c in lengths["GRCh38"] if lengths["GRCh38"][c] == lengths["GRCh37"][c]]
    if shared:
        raise SystemExit(f"GRCh38 and GRCh37 share lengths for {shared}; a length could not tell them apart")
    return {
        "_comment": (
            "Build evidence. Accessions are derived from PharmCAT's own "
            "definition/chr_build_mapping.tsv; contig lengths from NCBI's "
            "assembly reports named in contig_length_sources, whose accessions "
            "must equal PharmCAT's. Generated by scripts/derive_build_evidence.py "
            "— do not edit by hand."
        ),
        "source": MAPPING,
        "jar": JAR.name,
        "required_build": "GRCh38",
        "accession_to_build": accessions,
        "build_to_contigs": contigs,
        "contig_lengths": lengths,
        "contig_length_sources": sources,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if the committed file differs")
    parser.add_argument("--fetch", action="store_true", help="re-download NCBI's assembly reports first")
    args = parser.parse_args()
    if args.fetch:
        fetch_reports()
    text = json.dumps(derive(), indent=2, sort_keys=True) + "\n"
    if args.check:
        same = OUT.read_text() == text
        print("build_evidence.json matches its sources" if same else "build_evidence.json DIFFERS from its sources")
        return 0 if same else 1
    OUT.write_text(text)
    data = json.loads(text)
    print(f"{len(data['accession_to_build'])} accessions; lengths for "
          + ", ".join(f"{b} ({len(v)} contigs)" for b, v in sorted(data["contig_lengths"].items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
