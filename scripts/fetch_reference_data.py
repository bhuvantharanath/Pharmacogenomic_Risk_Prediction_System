#!/usr/bin/env python3
"""
Acquire reference-material genotypes and matching sample VCFs.

    python scripts/fetch_reference_data.py --verify        # check sources, no download
    python scripts/fetch_reference_data.py --dry-run       # plan, no download
    python scripts/fetch_reference_data.py --limit 5       # fetch 5 samples
    python scripts/fetch_reference_data.py --resume

WHY REMOTE SLICING, NOT DOWNLOADS

The 1000 Genomes GRCh38 high-coverage panel is ~2 TB whole-genome. We need seven
gene regions. `bcftools` reads the remote `.tbi` index over HTTPS and pulls only
the byte ranges covering the requested regions, so one sample costs ~2.6 MB and a
few seconds instead of gigabytes. Verified against the live FTP mirror on
2026-07-24.

EVERY URL AND COORDINATE HERE WAS VERIFIED LIVE, NOT REMEMBERED

  * The 1000G release path and filename pattern were confirmed by listing the
    directory (a guessed path returned 404 first — see VERIFIED_SOURCES).
  * Gene coordinates are derived from PharmCAT's OWN positions file
    (`pharmcat_positions_<version>.vcf.bgz`, INFO/PX field), not from a
    genome browser or memory. Run with --show-coords to print them.
  * The GeT-RM consensus table is fetched from Coriell, because CDC's own
    GeT-RM pages return HTTP 403 to non-browser clients. See LIMITATIONS.

WHAT THIS CANNOT GET

The Coriell GeT-RM PGx table covers CYP2D6, CYP2C19, CYP2C9, VKORC1 and UGT1A1
for 107 samples. It does NOT cover TPMT, NUDT15, DPYD or SLCO1B1 — those were
characterised in later GeT-RM studies whose tables are published on CDC pages
that block automated access. And of the 107, only **one** (NA12273) is in the
1000 Genomes high-coverage panel: 98 of them are NA17xxxx Coriell cell lines
that were never 1000G-sequenced. Both facts are reported rather than worked
around, because they bound what diplotype concordance can be measured on.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from _common import REPO_ROOT, bold, dim, green, red, rel, rule, yellow

REFERENCE_DIR = REPO_ROOT / "test-data" / "reference"
TOOLS_DIR = REFERENCE_DIR / "tools"
SLICE_DIR = REFERENCE_DIR / "slices"
MANIFEST_PATH = REFERENCE_DIR / "manifest.json"

#: Genes PharmaGuard maps. CYP2D6 is included as a NEGATIVE CONTROL: it must
#: never be called from an unphased VCF, and a call appearing would be a bug.
TARGET_GENES = ("CYP2C19", "CYP2C9", "DPYD", "NUDT15", "SLCO1B1", "TPMT", "CYP2D6")

PHARMCAT_VERSION = "3.4.0"
PHARMCAT_RELEASE = f"https://github.com/PharmGKB/PharmCAT/releases/download/v{PHARMCAT_VERSION}"
PHARMCAT_JAR = TOOLS_DIR / f"pharmcat-{PHARMCAT_VERSION}-all.jar"
PHARMCAT_POSITIONS = TOOLS_DIR / f"pharmcat_positions_{PHARMCAT_VERSION}.vcf.bgz"

#: 1000 Genomes GRCh38 high-coverage, 3202 samples, phased SNV+INDEL+SV.
#: Directory listing confirmed 2026-07-24; a shorter guessed path 404'd.
THOUSAND_GENOMES_BASE = (
    "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/"
    "1000G_2504_high_coverage/working/20220422_3202_phased_SNV_INDEL_SV"
)
THOUSAND_GENOMES_PATTERN = (
    "1kGP_high_coverage_Illumina.{chrom}.filtered.SNV_INDEL_SV_phased_panel.vcf.gz"
)

#: GeT-RM PGx consensus genotypes. Hosted by Coriell; CDC's equivalent pages
#: return 403 to scripted clients.
GETRM_URL = (
    "https://www.coriell.org/1/media/8433aa41-b6e9-405b-9096-4537dd8d42a7/UFTJ2Q/"
    "NIGMS/Documents/Get-RM%20Confirmed%20Mutations/Get-RM_Pharmacogenomics.xls"
)
GETRM_LOCAL = REFERENCE_DIR / "getrm_pharmacogenomics.xls"

VERIFIED_SOURCES = [
    {
        "name": "PharmCAT release assets",
        # A real asset, not the release directory: the directory path 404s even
        # when every asset under it downloads fine, which made --verify lie.
        "url": f"{PHARMCAT_RELEASE}/pharmcat-{PHARMCAT_VERSION}-all.jar",
        "verified": "2026-07-24",
        "note": f"pharmcat-{PHARMCAT_VERSION}-all.jar (32 MB) + positions VCF; "
                "runs under OpenJDK 25, reports 'PharmCAT 3.4.0'",
    },
    {
        "name": "1000 Genomes GRCh38 high coverage (3202 samples)",
        "url": THOUSAND_GENOMES_BASE,
        "verified": "2026-07-24",
        "note": "directory listing confirmed the filename pattern; remote .tbi "
                "present (.csi absent). A guessed shorter path returned 404 — "
                "this one was found by listing, not recalled.",
    },
    {
        "name": "GeT-RM PGx consensus genotypes (Coriell mirror)",
        "url": GETRM_URL,
        "verified": "2026-07-24",
        "note": "107 samples; CYP2D6/CYP2C19/CYP2C9/VKORC1/UGT1A1 only. "
                "CDC GeT-RM pages return HTTP 403 to non-browser clients, so "
                "TPMT/NUDT15/DPYD/SLCO1B1 consensus data is NOT obtainable "
                "programmatically.",
    },
]


# --------------------------------------------------------------------------- #
# Gene coordinates, from PharmCAT's own definition data
# --------------------------------------------------------------------------- #


@dataclass
class GeneRegion:
    gene: str
    chrom: str
    start: int
    end: int
    positions: int

    @property
    def region(self) -> str:
        return f"{self.chrom}:{self.start}-{self.end}"


def gene_regions() -> dict[str, GeneRegion]:
    """
    Derive each gene's coordinate span from PharmCAT's positions VCF.

    Deliberately not hardcoded. PharmCAT's allele definitions move between
    releases, and a coordinate written from memory is a guess that silently
    slices the wrong window — producing a no-call that looks like a data problem
    rather than a coordinate bug.
    """
    if not PHARMCAT_POSITIONS.is_file():
        raise SystemExit(
            f"missing {rel(PHARMCAT_POSITIONS)} — run with --fetch-tools first"
        )
    proc = subprocess.run(
        ["bcftools", "query", "-f", "%CHROM\t%POS\t%INFO/PX\n", str(PHARMCAT_POSITIONS)],
        capture_output=True, text=True, check=True,
    )
    spans: dict[str, list] = {}
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        chrom, pos_text, px = parts[0], parts[1], parts[2]
        for gene in (g.strip() for g in px.split(",")):
            if gene not in TARGET_GENES:
                continue
            pos = int(pos_text)
            span = spans.setdefault(gene, [chrom, pos, pos, 0])
            span[1] = min(span[1], pos)
            span[2] = max(span[2], pos)
            span[3] += 1
    return {
        gene: GeneRegion(gene, s[0], s[1], s[2], s[3]) for gene, s in spans.items()
    }


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_tools() -> None:
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    for name in (
        f"pharmcat-{PHARMCAT_VERSION}-all.jar",
        f"pharmcat_positions_{PHARMCAT_VERSION}.vcf.bgz",
        f"pharmcat_positions_{PHARMCAT_VERSION}.vcf.bgz.csi",
    ):
        target = TOOLS_DIR / name
        if target.is_file():
            print(dim(f"  have {name}"))
            continue
        print(f"  fetching {name} …")
        subprocess.run(
            ["curl", "-sSL", "--max-time", "600", "-o", str(target),
             f"{PHARMCAT_RELEASE}/{name}"], check=True,
        )


def fetch_getrm() -> list[dict]:
    """The GeT-RM consensus table, parsed to rows."""
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    if not GETRM_LOCAL.is_file():
        print("  fetching GeT-RM consensus table …")
        subprocess.run(
            ["curl", "-sSL", "--max-time", "120", "-A", "Mozilla/5.0",
             "-o", str(GETRM_LOCAL), GETRM_URL], check=True,
        )
    import xlrd

    book = xlrd.open_workbook(str(GETRM_LOCAL))
    sheet = book.sheet_by_index(0)
    # Row 2 carries the column names; rows above are a merged title banner.
    header = [str(sheet.cell_value(2, c)).strip() for c in range(sheet.ncols)]
    rows = []
    for r in range(3, sheet.nrows):
        values = [str(sheet.cell_value(r, c)).strip() for c in range(sheet.ncols)]
        if values and values[0].startswith(("NA", "GM", "HG")):
            rows.append(dict(zip(header, values)))
    return rows


def panel_samples(regions: dict[str, GeneRegion]) -> list[str]:
    """Sample IDs in the 1000G panel, read from one chromosome's header."""
    any_region = next(iter(regions.values()))
    url = f"{THOUSAND_GENOMES_BASE}/{THOUSAND_GENOMES_PATTERN.format(chrom=any_region.chrom)}"
    proc = subprocess.run(
        ["bcftools", "query", "-l", url], capture_output=True, text=True, check=True,
    )
    return proc.stdout.split()


def slice_sample(sample: str, regions: dict[str, GeneRegion]) -> Path | None:
    """
    Remote-slice every target gene region for one sample into a single VCF.

    Per-chromosome slices are concatenated because the panel is split by
    chromosome. Only the requested byte ranges cross the network.
    """
    SLICE_DIR.mkdir(parents=True, exist_ok=True)
    final = SLICE_DIR / f"{sample}.vcf.gz"
    if final.is_file():
        return final

    by_chrom: dict[str, list[GeneRegion]] = collections.defaultdict(list)
    for region in regions.values():
        by_chrom[region.chrom].append(region)

    parts: list[Path] = []
    for chrom in sorted(by_chrom, key=lambda c: (len(c), c)):
        url = f"{THOUSAND_GENOMES_BASE}/{THOUSAND_GENOMES_PATTERN.format(chrom=chrom)}"
        spec = ",".join(r.region for r in by_chrom[chrom])
        part = SLICE_DIR / f"{sample}.{chrom}.part.vcf.gz"
        try:
            subprocess.run(
                ["bcftools", "view", "-r", spec, "-s", sample, "-Oz", "-o", str(part), url],
                check=True, capture_output=True, timeout=600,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            print(red(f"    {chrom}: slice failed ({type(exc).__name__})"))
            for stale in parts:
                stale.unlink(missing_ok=True)
            return None
        parts.append(part)

    subprocess.run(
        ["bcftools", "concat", "-Oz", "-o", str(final), *[str(p) for p in parts]],
        check=True, capture_output=True,
    )
    subprocess.run(["bcftools", "index", "-f", "-t", str(final)], check=True,
                   capture_output=True)
    for part in parts:
        part.unlink(missing_ok=True)
    return final


# --------------------------------------------------------------------------- #
# Manifest
# --------------------------------------------------------------------------- #


def write_manifest(regions, getrm_rows, panel, sliced, overlap) -> dict:
    """
    A committed, checksummed record of exactly what was acquired.

    The VCF slices themselves are gitignored (megabytes, and re-derivable), so
    the manifest is what makes the set reproducible: same sources, same
    coordinates, same checksums.
    """
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verified_sources": VERIFIED_SOURCES,
        "pharmcat_version": PHARMCAT_VERSION,
        "gene_regions": {
            g: {"chrom": r.chrom, "start": r.start, "end": r.end,
                "pharmcat_positions": r.positions, "region": r.region}
            for g, r in sorted(regions.items())
        },
        "coordinate_provenance":
            "derived from PharmCAT's own positions VCF (INFO/PX), not hardcoded",
        "getrm": {
            "samples": len(getrm_rows),
            "genes_covered": ["CYP2D6", "CYP2C19", "CYP2C9", "VKORC1", "UGT1A1"],
            "genes_NOT_covered": ["TPMT", "NUDT15", "DPYD", "SLCO1B1"],
            "source_sha256": sha256(GETRM_LOCAL) if GETRM_LOCAL.is_file() else None,
        },
        "thousand_genomes": {
            "panel_samples": len(panel),
            "getrm_overlap": sorted(overlap),
            "overlap_count": len(overlap),
        },
        "slices": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in sorted(sliced)
        },
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true", help="Check sources are live; fetch nothing.")
    parser.add_argument("--show-coords", action="store_true", help="Print gene regions and exit.")
    parser.add_argument("--fetch-tools", action="store_true", help="Download PharmCAT only.")
    parser.add_argument("--dry-run", action="store_true", help="Plan without slicing.")
    parser.add_argument("--limit", type=int, default=0, help="Max samples to slice.")
    parser.add_argument("--sample", action="append", default=[], help="Specific sample id(s).")
    parser.add_argument("--resume", action="store_true", help="Skip samples already sliced.")
    args = parser.parse_args(argv)

    if args.verify:
        print(rule("verifying sources"))
        for source in VERIFIED_SOURCES:
            code = subprocess.run(
                ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
                 "--max-time", "25", "-A", "Mozilla/5.0", "-L", source["url"]],
                capture_output=True, text=True,
            ).stdout.strip()
            ok = code.startswith("2") or code.startswith("3")
            print(f"  {green('OK ') if ok else red('BAD')} [{code}] {source['name']}")
            print(dim(f"      {source['note']}"))
        return 0

    if args.fetch_tools:
        fetch_tools()
        return 0

    if not PHARMCAT_POSITIONS.is_file():
        fetch_tools()

    regions = gene_regions()
    if args.show_coords:
        print(rule("gene regions (from PharmCAT positions VCF)"))
        print(f"  {'gene':10}{'region':32}{'positions':>10}")
        for gene, region in sorted(regions.items()):
            print(f"  {gene:10}{region.region:32}{region.positions:>10}")
        return 0

    print(rule("reference data"))
    getrm_rows = fetch_getrm()
    getrm_ids = [r["Coriell DNA Ref"] for r in getrm_rows]
    panel = panel_samples(regions)
    overlap = [s for s in getrm_ids if s in set(panel)]

    print(f"  GeT-RM consensus samples      {len(getrm_rows)}")
    print(f"  1000G high-coverage panel     {len(panel)}")
    print(f"  {bold('overlap (both sources)')}       {len(overlap)}  {overlap}")
    if len(overlap) < 5:
        print(yellow(f"  ⚠ only {len(overlap)} sample(s) have BOTH a consensus genotype and"))
        print(yellow("    sequence data — diplotype concordance is bounded by this."))
        print(dim("    98 of 107 GeT-RM ids are NA17xxxx Coriell PGx lines, never 1000G-sequenced."))

    # Slice: the overlap first (they carry consensus truth), then extra panel
    # samples, which still support integration fidelity and the CYP2D6 control.
    wanted = list(args.sample) if args.sample else overlap + [
        s for s in panel if s not in set(overlap)
    ]
    if args.resume:
        wanted = [s for s in wanted if not (SLICE_DIR / f"{s}.vcf.gz").is_file()]
    if args.limit:
        wanted = wanted[: args.limit]

    if args.dry_run:
        print(f"\n  would slice {bold(str(len(wanted)))} sample(s): {wanted[:6]}"
              + (" …" if len(wanted) > 6 else ""))
        print(dim(f"  regions: {', '.join(r.region for r in regions.values())}"))
        print(dim("  no network slice performed"))
        return 0

    sliced: list[Path] = []
    for index, sample in enumerate(wanted, start=1):
        print(f"  [{index}/{len(wanted)}] {sample} … ", end="", flush=True)
        path = slice_sample(sample, regions)
        if path is None:
            print(red("failed"))
            continue
        sliced.append(path)
        print(green(f"{path.stat().st_size / 1e6:.1f} MB"))

    existing = sorted(SLICE_DIR.glob("*.vcf.gz")) if SLICE_DIR.is_dir() else []
    manifest = write_manifest(regions, getrm_rows, panel, existing, overlap)
    print(rule())
    print(f"\n  sliced this run {len(sliced)}   total cached {len(existing)}")
    print(dim(f"  manifest: {rel(MANIFEST_PATH)}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
