"""
Two filters, applied to every allele before any deviation is called a finding.

WHY THIS EXISTS

Of the deviations found at n=601, two were checked by hand and both dissolved:

  * **CYP2C9 `*2`** — its single defining position, rs1799853, is absent from
    the sliced input, so every carrier is invisible. An INPUT ARTIFACT.
  * **CYP2C19 `*38`** — the reference haplotype, which CPIC's table folds into
    `*1`. A NAMING ARTIFACT.

The rest were never checked. Reporting them beside the two known artifacts would
present a table in which some rows are population findings and others are
measurement failures, with nothing distinguishing them — precisely the error
this project documents everywhere else.

So both filters are applied MECHANICALLY, to every allele, from source data:

  1. **Coverage** — defining positions come from PharmCAT's own
     `<GENE>_translation.json`; present positions are read from the sliced VCF.
     If any defining position is absent, carriers cannot be seen, and the
     frequency is an artifact of the input rather than a fact about the people.
  2. **Nomenclature** — an allele CPIC does not name at all cannot be compared
     against CPIC. Absence of a row is not a frequency of zero.

Whatever survives both is a candidate population deviation. If nothing survives,
that is a legitimate and reportable result.
"""

from __future__ import annotations

import json
import math
import subprocess
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JAR = REPO / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
DEF_PREFIX = "org/pharmgkb/pharmcat/definition/alleles/"
SLICE = REPO / "test-data/reference/cohort/cohort_n601.vcf"
FREQS = REPO / "reports/sas_frequencies.json"
CPIC_DIR = REPO / "test-data/reference/cpic_frequencies"
OUT = REPO / "reports/sas_deviation_filtered.json"

#: Genes with both a CPIC frequency table and a meaningful call rate here.
GENES = ("CYP2C19", "CYP2C9", "NUDT15", "SLCO1B1", "TPMT")
CPIC_GROUP = "Central/South Asian"


def defining_positions(gene: str) -> dict[str, list[tuple[str, int, str | None]]]:
    """
    allele -> [(chromosome, position, rsid)] for every position that DEFINES it.

    The CHROMOSOME is carried deliberately. A bare POS is not an identity: the
    first version of this pooled positions across all six contigs, so a position
    number on chr1 could satisfy a lookup for chr10 and vice versa.
    """
    with zipfile.ZipFile(JAR) as z:
        data = json.loads(z.read(f"{DEF_PREFIX}{gene}_translation.json"))
    variants = data["variants"]
    chrom = data.get("chromosome")
    out: dict[str, list[tuple[str, int, str | None]]] = {}
    for allele in data["namedAlleles"]:
        positions = []
        for i, value in enumerate(allele["alleles"]):
            if value is not None and i < len(variants):
                v = variants[i]
                positions.append((v.get("chromosome") or chrom,
                                  v["position"], v.get("rsid")))
        out[allele["name"]] = positions
    return out


def sliced_positions() -> set[tuple[str, int]]:
    """
    Every (chromosome, position) present in the sliced cohort VCF.

    READ BY LINEAR SCAN, NOT `bcftools -r`. The combined VCF is uncompressed and
    unindexed, and `bcftools query -r` on such a file fails with "not compressed
    with bgzip" — on stderr, returning exit 0 and NO rows. An earlier check
    piped stderr away and built its position set from that empty output, so
    every membership test returned False and every position looked absent. It
    produced a confident, wrong finding: that rs1799853 was missing and
    explained the CYP2C9 *2 shortfall. rs1799853 is present.
    """
    out: set[tuple[str, int]] = set()
    with SLICE.open() as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            chrom, pos, _ = line.split("\t", 2)
            out.add((chrom, int(pos)))
    if not out:
        raise SystemExit("no positions parsed from the slice — refusing to "
                         "report every allele as an artifact on an empty set")
    return out


def cpic_names(gene: str) -> set[str]:
    path = CPIC_DIR / f"{gene}.json"
    if not path.is_file():
        return set()
    rows = json.loads(path.read_text())["rows"]
    return {r["name"] for r in rows if r["population_group"] == CPIC_GROUP}


def cpic_freq(gene: str) -> dict[str, float]:
    path = CPIC_DIR / f"{gene}.json"
    if not path.is_file():
        return {}
    rows = json.loads(path.read_text())["rows"]
    return {r["name"]: r["freq_weighted_avg"] for r in rows
            if r["population_group"] == CPIC_GROUP
            and r.get("freq_weighted_avg") is not None}


def main() -> int:
    freqs = json.loads(FREQS.read_text())
    present = sliced_positions()
    print(f"(chromosome, position) pairs in the slice: {len(present)}\n")

    input_artifacts: list[dict] = []
    naming_artifacts: list[dict] = []
    survivors: list[dict] = []
    agreements: list[dict] = []

    for gene in GENES:
        pooled = freqs["pooled_sas"].get(gene)
        if not pooled or not pooled["allele_freq"]:
            continue
        defs = defining_positions(gene)
        published = cpic_freq(gene)
        named = cpic_names(gene)

        for allele, v in pooled["allele_freq"].items():
            lo, hi = v["ci95"]
            ref = published.get(allele)

            required = defs.get(allele, [])
            missing = [(c, p, r) for c, p, r in required
                       if (c, p) not in present]

            row = {
                "gene": gene, "allele": allele,
                "ours": v["freq"], "count": v["count"],
                "ci95": [lo, hi], "cpic": ref,
                "positions_required": len(required),
                "positions_present": len(required) - len(missing),
                "missing_positions": [
                    {"chromosome": c, "position": p, "rsid": r}
                    for c, p, r in missing],
            }

            # FILTER 1 — coverage. A missing defining position means carriers
            # cannot be distinguished from reference, so the frequency measures
            # the input, not the population.
            if missing:
                row["classification"] = "input_artifact"
                row["why"] = (
                    f"{len(missing)} of {len(required)} defining position(s) "
                    f"absent from the slice; carriers are invisible and are "
                    f"called something else")
                input_artifacts.append(row)
                continue

            # FILTER 2 — nomenclature. No CPIC row means no comparison exists.
            if allele not in named:
                row["classification"] = "naming_artifact"
                row["why"] = (
                    "CPIC's Central/South Asian table has no row for this "
                    "allele — it is folded into another name or not used. "
                    "Absence of a row is not a frequency of zero")
                naming_artifacts.append(row)
                continue

            if ref is None:
                row["classification"] = "naming_artifact"
                row["why"] = "CPIC names the allele but publishes no frequency"
                naming_artifacts.append(row)
                continue

            # Survived both filters: is it actually a deviation?
            if lo <= ref <= hi:
                row["classification"] = "agrees"
                agreements.append(row)
            else:
                row["classification"] = "population_deviation"
                row["direction"] = "higher" if v["freq"] > ref else "lower"
                survivors.append(row)

    def show(title: str, rows: list[dict]) -> None:
        print(f"\n{'=' * 78}\n{title}  —  {len(rows)}\n{'=' * 78}")
        for r in rows:
            ref = f"{r['cpic']:.4f}" if r["cpic"] is not None else "  n/a "
            print(f"  {r['gene']:8s} {r['allele']:26s} ours={r['ours']:.4f} "
                  f"cpic={ref}  pos={r['positions_present']}/{r['positions_required']}")
            if r.get("missing_positions"):
                for m in r["missing_positions"][:3]:
                    print(f"      MISSING {m['chromosome']}:{m['position']} "
                          f"({m['rsid']})")

    show("INPUT ARTIFACTS — a defining position is absent", input_artifacts)
    show("NAMING ARTIFACTS — CPIC does not name it comparably", naming_artifacts)
    show("GENUINE POPULATION DEVIATIONS — survived both filters", survivors)
    show("AGREES WITH CPIC — survived both filters, CI contains published",
         agreements)

    OUT.write_text(json.dumps({
        "slice_positions": len(present),
        "counts": {
            "input_artifacts": len(input_artifacts),
            "naming_artifacts": len(naming_artifacts),
            "population_deviations": len(survivors),
            "agrees": len(agreements),
        },
        "input_artifacts": input_artifacts,
        "naming_artifacts": naming_artifacts,
        "population_deviations": survivors,
        "agrees": agreements,
    }, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
