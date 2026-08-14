#!/usr/bin/env python3
"""
Generate synthetic GRCh38 VCFs with chosen PharmCAT diplotypes.

WHY THIS EXISTS
---------------
To demo a specific phenotype (e.g. a CYP2C19 poor metaboliser for clopidogrel)
we need a VCF that PharmCAT will actually call as that diplotype. Writing one by
hand does not work: a named allele is defined by a *combination* of positions,
not by one "famous" rsID. Setting rs4244285 to A/A and leaving everything else
reference produces **no call at all**, because that combination matches no
defined CYP2C19 haplotype.

So every position and allele emitted here is read out of PharmCAT's own
allele-definition JSONs. Nothing is written from memory.

GETTING THE DEFINITIONS
-----------------------
They ship inside the PharmCAT JAR:

    unzip -j pharmcat.jar 'org/pharmgkb/pharmcat/definition/alleles/*.json' \\
          -d definitions/

or let this script do it:

    ./generate_synthetic_vcf.py --from-jar /path/to/pharmcat.jar --list

Inside the Docker image the JAR lives at /pharmcat/pharmcat.jar.

USAGE
-----
    # What can I build?
    ./generate_synthetic_vcf.py --definitions-dir definitions/ --list CYP2C19

    # A CYP2C19 poor metaboliser (clopidogrel demo)
    ./generate_synthetic_vcf.py --definitions-dir definitions/ \\
        --diplotype CYP2C19=*2/*2 --sample PM_DEMO -o cyp2c19_pm.vcf

    # Multiple genes in one file, plus an untouched reference control
    ./generate_synthetic_vcf.py --definitions-dir definitions/ \\
        --diplotype CYP2C19=*1/*1 --diplotype DPYD=Reference/Reference \\
        --sample CONTROL -o control.vcf

Genes you do not name are omitted entirely, which PharmCAT reports as a no-call
for those genes. Use --pad-genes to emit them at reference instead.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

# IUPAC ambiguity codes. PharmCAT definitions use these where a named allele
# tolerates either base at a position; we must emit one concrete base.
_IUPAC: dict[str, tuple[str, ...]] = {
    "R": ("A", "G"),
    "Y": ("C", "T"),
    "S": ("G", "C"),
    "W": ("A", "T"),
    "K": ("G", "T"),
    "M": ("A", "C"),
    "B": ("C", "G", "T"),
    "D": ("A", "G", "T"),
    "H": ("A", "C", "T"),
    "V": ("A", "C", "G"),
    "N": ("A", "C", "G", "T"),
}

_JAR_DEFINITION_PREFIX = "org/pharmgkb/pharmcat/definition/alleles/"


@dataclass
class ResolvedCall:
    """One VCF row's worth of resolved genotype."""

    chrom: str
    position: int
    rsid: str | None
    ref: str
    alts: list[str]
    gt: str
    gene: str


class DefinitionError(RuntimeError):
    """Raised for anything the caller can fix (bad gene, bad allele name)."""


def load_definition(definitions_dir: Path, gene: str) -> dict:
    path = definitions_dir / f"{gene}_translation.json"
    if not path.is_file():
        available = sorted(
            p.name.replace("_translation.json", "")
            for p in definitions_dir.glob("*_translation.json")
        )
        raise DefinitionError(
            f"No definition for {gene!r} in {definitions_dir}.\n"
            f"Available: {', '.join(available) or '(none — is this the right directory?)'}"
        )
    return json.loads(path.read_text())


def extract_definitions_from_jar(jar: Path, dest: Path) -> Path:
    """Pull the allele-definition JSONs out of a PharmCAT JAR."""
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(jar) as zf:
        for name in zf.namelist():
            if name.startswith(_JAR_DEFINITION_PREFIX) and name.endswith(".json"):
                (dest / Path(name).name).write_bytes(zf.read(name))
                count += 1
    if count == 0:
        raise DefinitionError(
            f"{jar} contains no files under {_JAR_DEFINITION_PREFIX}. "
            "Is it really a PharmCAT JAR?"
        )
    print(f"Extracted {count} allele definitions to {dest}", file=sys.stderr)
    return dest


def _named_allele(definition: dict, name: str) -> dict:
    for na in definition["namedAlleles"]:
        if na["name"] == name:
            return na
    names = [na["name"] for na in definition["namedAlleles"]]
    raise DefinitionError(
        f"{definition['gene']} has no named allele {name!r}.\n"
        f"Available ({len(names)}): {', '.join(names[:25])}"
        + (" …" if len(names) > 25 else "")
    )


def _reference_allele(definition: dict) -> dict:
    for na in definition["namedAlleles"]:
        if na.get("reference"):
            return na
    # Every PharmCAT gene declares exactly one reference allele; if that ever
    # stops being true we want to know loudly rather than guess.
    raise DefinitionError(
        f"{definition['gene']} declares no reference named allele."
    )


def _resolve_allele(raw: str, variant: dict, warnings: list[str]) -> str | None:
    """
    Turn a definition allele string into a concrete VCF allele.

    Definitions mostly use plain bases, but also carry IUPAC ambiguity codes and
    a few "X or Y" alternatives. Returns None if it cannot be resolved, in which
    case the caller falls back to reference and records a warning.
    """
    ref: str = variant["ref"]
    alts: list[str] = list(variant.get("alts") or [])
    valid = [ref, *alts]
    allele_map: dict[str, str] = variant.get("cpicToVcfAlleleMap") or {}

    # 1. The definition's own mapping is authoritative when present.
    mapped = allele_map.get(raw)
    if mapped is not None and mapped in valid:
        return mapped

    # 2. Already a literal VCF allele (covers indel sequences).
    if raw in valid:
        return raw

    # 3. "AGGAGTC or AGGAGTCGGAGTC" — take the first option that is valid.
    if " or " in raw:
        for option in (o.strip() for o in raw.split(" or ")):
            resolved = allele_map.get(option, option)
            if resolved in valid:
                return resolved

    # 4. Single-character IUPAC ambiguity — pick a concrete base, preferring an
    #    ALT so the named allele stays distinguishable from reference.
    if len(raw) == 1 and raw in _IUPAC:
        options = _IUPAC[raw]
        for alt in alts:
            if alt in options:
                return alt
        if ref in options:
            return ref

    warnings.append(
        f"chr{variant['chromosome'].removeprefix('chr')}:{variant['position']} "
        f"({variant.get('rsid') or 'no rsid'}): could not encode allele {raw!r} "
        f"(ref={ref}, alts={alts}); emitted reference instead"
    )
    return None


def build_gene_rows(
    definition: dict,
    hap1: str,
    hap2: str,
    warnings: list[str],
) -> list[ResolvedCall]:
    """
    Emit one VCF row per definition position for a single gene.

    A named allele only pins down the positions that define it; every other
    position inherits the reference allele. That is exactly how PharmCAT's
    matcher reads them, and getting it wrong is what makes hand-written VCFs
    fail to call.
    """
    gene = definition["gene"]
    variants = definition["variants"]
    reference = _reference_allele(definition)
    a1 = _named_allele(definition, hap1)
    a2 = _named_allele(definition, hap2)

    rows: list[ResolvedCall] = []
    for idx, variant in enumerate(variants):
        ref: str = variant["ref"]
        alts: list[str] = list(variant.get("alts") or [])

        calls: list[str] = []
        for named in (a1, a2):
            raw = named["alleles"][idx]
            if raw is None:
                # Undefined at this position -> inherit reference.
                raw = reference["alleles"][idx]
            resolved = (
                _resolve_allele(raw, variant, warnings) if raw is not None else None
            )
            calls.append(resolved if resolved is not None else ref)

        # Convert concrete alleles to VCF GT indices (0 = REF, 1..n = ALT).
        indices: list[str] = []
        for call in calls:
            if call == ref:
                indices.append("0")
            elif call in alts:
                indices.append(str(alts.index(call) + 1))
            else:
                # Should be unreachable — _resolve_allele only returns valid
                # alleles — but never silently emit a wrong genotype.
                warnings.append(
                    f"{gene} {variant['position']}: resolved allele {call!r} is "
                    f"neither REF nor ALT; emitted reference"
                )
                indices.append("0")

        rows.append(
            ResolvedCall(
                chrom=variant["chromosome"],
                position=int(variant["position"]),
                rsid=variant.get("rsid"),
                ref=ref,
                # An empty ALT column is illegal in VCF; "." is the placeholder.
                alts=alts or ["."],
                gt="/".join(indices),
                gene=gene,
            )
        )
    return rows


def render_vcf(rows: list[ResolvedCall], sample: str, provenance: list[str]) -> str:
    """Assemble a minimal but valid VCF 4.2."""
    # Sort by chromosome (numeric where possible) then position, as VCF requires.
    def chrom_key(chrom: str) -> tuple[int, str]:
        bare = chrom.removeprefix("chr")
        return (int(bare), "") if bare.isdigit() else (99, bare)

    rows = sorted(rows, key=lambda r: (chrom_key(r.chrom), r.position))
    chroms = sorted({r.chrom for r in rows}, key=chrom_key)

    lines: list[str] = ["##fileformat=VCFv4.2"]
    lines += [f"##{p}" for p in provenance]
    # assembly= on the contig lines is how PharmCAT detects the reference build.
    lines += [
        f'##contig=<ID={c},assembly=GRCh38.p14,species="Homo sapiens">'
        for c in chroms
    ]
    lines += [
        '##INFO=<ID=PX,Number=.,Type=String,Description="Gene">',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
        "#" + "\t".join(
            "CHROM POS ID REF ALT QUAL FILTER INFO FORMAT".split() + [sample]
        ),
    ]
    for r in rows:
        lines.append(
            "\t".join(
                [
                    r.chrom,
                    str(r.position),
                    r.rsid or ".",
                    r.ref,
                    ",".join(r.alts),
                    ".",
                    "PASS",
                    f"PX={r.gene}",
                    "GT",
                    r.gt,
                ]
            )
        )
    return "\n".join(lines) + "\n"


def parse_diplotype_arg(value: str) -> tuple[str, str, str]:
    """Parse GENE=HAP1/HAP2. Allele names may contain '*', '>' and spaces."""
    if "=" not in value:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not GENE=HAP1/HAP2 (e.g. CYP2C19=*2/*2)"
        )
    gene, _, diplotype = value.partition("=")
    if "/" not in diplotype:
        raise argparse.ArgumentTypeError(
            f"{value!r} is missing the '/' between haplotypes "
            f"(e.g. {gene}=*1/*2)"
        )
    hap1, _, hap2 = diplotype.partition("/")
    if not gene.strip() or not hap1.strip() or not hap2.strip():
        raise argparse.ArgumentTypeError(f"{value!r} has an empty gene or haplotype")
    return gene.strip().upper(), hap1.strip(), hap2.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = parser.add_argument_group("definition source")
    src.add_argument(
        "--definitions-dir",
        type=Path,
        help="Directory of PharmCAT *_translation.json files.",
    )
    src.add_argument(
        "--from-jar",
        type=Path,
        help="PharmCAT JAR to extract definitions from (implies --definitions-dir).",
    )
    parser.add_argument(
        "--diplotype",
        action="append",
        default=[],
        metavar="GENE=HAP1/HAP2",
        type=parse_diplotype_arg,
        help="Repeatable. e.g. --diplotype CYP2C19=*2/*2",
    )
    parser.add_argument(
        "--pad-genes",
        default="",
        metavar="G1,G2",
        help="Also emit these genes at their reference diplotype.",
    )
    parser.add_argument("--sample", default="SYNTHETIC_001", help="Sample column name.")
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path (default: stdout)."
    )
    parser.add_argument(
        "--list",
        nargs="?",
        const="",
        metavar="GENE",
        help="List available genes, or the named alleles of GENE, then exit.",
    )
    args = parser.parse_args(argv)

    definitions_dir = args.definitions_dir
    if args.from_jar:
        definitions_dir = extract_definitions_from_jar(
            args.from_jar, args.definitions_dir or Path("definitions")
        )
    if definitions_dir is None:
        parser.error("one of --definitions-dir or --from-jar is required")
    if not definitions_dir.is_dir():
        parser.error(f"{definitions_dir} is not a directory")

    if args.list is not None:
        if args.list:
            definition = load_definition(definitions_dir, args.list.upper())
            reference = _reference_allele(definition)["name"]
            print(f"{definition['gene']} (reference allele: {reference})")
            print(f"  genome build: {definition.get('genomeBuild')}")
            print(f"  definition version: {definition.get('version')}")
            print(f"  {len(definition['variants'])} positions")
            for na in definition["namedAlleles"]:
                defined = sum(1 for a in na["alleles"] if a is not None)
                flag = "  (reference)" if na.get("reference") else ""
                print(f"    {na['name']:<28} defines {defined:>3} position(s){flag}")
        else:
            genes = sorted(
                p.name.replace("_translation.json", "")
                for p in definitions_dir.glob("*_translation.json")
            )
            print(f"{len(genes)} genes: {', '.join(genes)}")
        return 0

    if not args.diplotype and not args.pad_genes:
        parser.error("nothing to do: pass at least one --diplotype (or --pad-genes)")

    requested: list[tuple[str, str, str]] = list(args.diplotype)
    named_genes = {g for g, _, _ in requested}
    for gene in (g.strip().upper() for g in args.pad_genes.split(",") if g.strip()):
        if gene in named_genes:
            continue
        reference = _reference_allele(load_definition(definitions_dir, gene))["name"]
        requested.append((gene, reference, reference))

    rows: list[ResolvedCall] = []
    warnings: list[str] = []
    provenance: list[str] = ["source=PharmaGuardSyntheticGenerator"]
    for gene, hap1, hap2 in requested:
        definition = load_definition(definitions_dir, gene)
        build = definition.get("genomeBuild", "")
        if "GRCh38" not in str(build):
            raise DefinitionError(
                f"{gene} definition is {build}, but PharmCAT requires GRCh38."
            )
        rows += build_gene_rows(definition, hap1, hap2, warnings)
        provenance.append(
            f"pharmaguard_synthetic_{gene}={hap1}/{hap2} "
            f"(definition {definition.get('source')} {definition.get('version')})"
        )

    vcf = render_vcf(rows, args.sample, provenance)
    if args.output:
        args.output.write_text(vcf)
        print(
            f"Wrote {args.output} — {len(rows)} positions across "
            f"{len(requested)} gene(s), sample {args.sample}",
            file=sys.stderr,
        )
    else:
        sys.stdout.write(vcf)

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    # These files are only useful if PharmCAT calls the diplotype we asked for.
    print(
        "\nVerify with:\n"
        f"  pharmcat_pipeline {args.output or '<file>'} -o out/ -reporterJson\n"
        "and check the diplotype in out/*.match.json.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DefinitionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
