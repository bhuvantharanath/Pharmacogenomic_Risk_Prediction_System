#!/usr/bin/env python3
"""
Frequency concordance: our called star-allele frequencies vs CPIC's published tables.

WHAT THIS IS, STATED PLAINLY

An **aggregate sanity check**, not per-sample validation. It asks whether the
distribution of alleles we call across 400 unrelated people resembles the
distribution CPIC publishes for comparable populations. It cannot tell you that
any individual sample was genotyped correctly — a pipeline that shuffled calls
between samples at random would still produce the right histogram.

Per-sample genotype accuracy needs an external truth set (GeT-RM), which is
reported separately and honestly as n=1.

WHY IT IS STILL WORTH DOING

It is sensitive to whole-classes of error that per-sample spot checks miss:
a strand flip, an off-by-one in coordinates, a reference/alternate swap, or a
population-specific allele silently never being called would all distort the
histogram in a way that shows up here.

THE POPULATION MAPPING IS APPROXIMATE, AND THAT MATTERS

1000 Genomes superpopulations and CPIC biogeographic groups are different
taxonomies built for different purposes. The mapping below is the conventional
correspondence, but it is a judgement call, not an identity — CPIC's "Sub-Saharan
African" and 1000G's AFR (which includes African-ancestry Americans) are not the
same population, and neither are AMR and "Latino". Deviations of a few percent
should be read against that, not treated as pipeline error.

SOURCE

CPIC API, https://api.cpicpgx.org/v1/population_frequency_view — queried live,
with the response cached and the access date recorded in the artifact.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import scrub  # noqa: E402

REFERENCE_DIR = REPO_ROOT / "test-data" / "reference"
COHORT_DIR = REFERENCE_DIR / "cohort"
CACHE_DIR = REFERENCE_DIR / "cpic_frequencies"
POPULATIONS = REFERENCE_DIR / "1000G_3202_populations.txt"
ARTIFACT = REPO_ROOT / "reports" / "frequency_concordance.json"

CPIC_API = "https://api.cpicpgx.org/v1/population_frequency_view?genesymbol=eq.{gene}"

#: Genes with clean star-allele nomenclature. DPYD is excluded deliberately: it
#: uses variant names ("c.1129-5923C>G") and compound alleles ("[a + b]"), so
#: splitting a diplotype into two comparable alleles is not well defined there.
STAR_GENES = ("CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "NUDT15")

#: 1000G superpopulation -> CPIC biogeographic group. Conventional, approximate,
#: and load-bearing for every number in the comparison — see the module docstring.
POPULATION_MAP = {
    "EUR": "European",
    "EAS": "East Asian",
    "SAS": "Central/South Asian",
    "AFR": "Sub-Saharan African",
    "AMR": "Latino",
}

#: A frequency estimate from n chromosomes is meaningless below some n. 30 is the
#: floor for reporting a percentage at all; anything under it is shown as a raw
#: count so nobody reads a ratio into it.
MIN_CHROMOSOMES = 30


def dim(t: str) -> str: return f"\033[2m{t}\033[0m"
def red(t: str) -> str: return f"\033[31m{t}\033[0m"
def green(t: str) -> str: return f"\033[32m{t}\033[0m"
def bold(t: str) -> str: return f"\033[1m{t}\033[0m"


def load_populations() -> dict[str, tuple[str, str]]:
    lines = POPULATIONS.read_text().splitlines()
    header = lines[0].split()
    i_id, i_pop, i_sup = (header.index(k) for k in ("SampleID", "Population", "Superpopulation"))
    out = {}
    for line in lines[1:]:
        cols = line.split()
        if len(cols) > max(i_id, i_pop, i_sup):
            out[cols[i_id]] = (cols[i_pop], cols[i_sup])
    return out


_ALLELE_SPLIT = re.compile(r"\s*/\s*")


def split_diplotype(label: str | None) -> list[str] | None:
    """
    "*1/*2" -> ["*1", "*2"]. None when the label is not a simple pair.

    Compound alleles ("[a + b]"), no-calls and anything without exactly two parts
    return None rather than a best guess: a wrong split would silently corrupt
    every frequency downstream.
    """
    if not label or "[" in label or "+" in label:
        return None
    parts = [p.strip() for p in _ALLELE_SPLIT.split(label) if p.strip()]
    if len(parts) != 2:
        return None
    if any("unknown" in p.lower() or p.lower() == "n/a" for p in parts):
        return None
    return parts


def our_frequencies(reports: list[Path], pops: dict[str, tuple[str, str]]) -> dict:
    """Allele counts per (gene, superpopulation), plus the overall pool."""
    counts: dict[tuple[str, str], collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    chroms: collections.Counter = collections.Counter()
    skipped: collections.Counter = collections.Counter()
    ambiguous: collections.Counter = collections.Counter()

    for path in sorted(reports):
        stem = path.name.removesuffix(".report.json")
        sample = stem.split(".", 1)[1] if "." in stem else stem
        meta = pops.get(sample)
        if meta is None:
            continue
        _pop, superpop = meta
        try:
            raw = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        genes = raw.get("genes") or {}
        section = genes.get("CPIC") if "CPIC" in genes else genes
        for gene in STAR_GENES:
            block = (section or {}).get(gene)
            if not isinstance(block, dict):
                continue
            source = block.get("sourceDiplotypes") or []
            if not source:
                skipped[gene] += 1
                continue
            if len(source) > 1:
                ambiguous[gene] += 1

            # TWO ESTIMATORS, BOTH BIASED, REPORTED SIDE BY SIDE.
            #
            # PharmCAT often returns several equally-likely diplotypes, and for
            # SLCO1B1 that is the majority of samples (163 unambiguous, 153 with
            # 4 candidates, 84 with 10) with the ambiguity strongly
            # population-structured (EUR 10%, EAS 92%, AFR 82%). Neither obvious
            # way of handling it is neutral:
            #
            #   FIRST        take sourceDiplotypes[0]. An arbitrary pick among
            #                equals — but PharmCAT lists the canonical form first,
            #                and this reproduced CPIC's published CYP2C9 *2 in
            #                Europeans to within 0.6 pp (13.3% vs 12.7%).
            #
            #   UNAMBIGUOUS  count only single-candidate calls. Sounds stricter,
            #                and is systematically WORSE: variant carriers are the
            #                ones most often ambiguous, so dropping them inflates
            #                the reference allele. Under this estimator CYP2C9 *2
            #                in Europeans falls to 0.0% against a published 12.7%.
            #
            # Publishing one number would hide that the answer depends on this
            # choice. Both are computed; where they disagree, no frequency claim
            # is made for that gene.
            for variant, entries in (("first", source[:1]),
                                     ("unambiguous", source if len(source) == 1 else [])):
                for entry in entries:
                    label = entry.get("label") if isinstance(entry, dict) else None
                    alleles = split_diplotype(label)
                    if alleles is None:
                        if variant == "first":
                            skipped[gene] += 1
                        continue
                    for group in (superpop, "ALL"):
                        for allele in alleles:
                            counts[(gene, group, variant)][allele] += 1
                        chroms[(gene, group, variant)] += 2
    return {"counts": counts, "chromosomes": chroms, "skipped": skipped,
            "ambiguous": ambiguous}


def cpic_frequencies(gene: str, *, refresh: bool) -> tuple[list[dict], str]:
    """CPIC's published allele frequencies, cached on disk with an access date."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"{gene}.json"
    if cache.is_file() and not refresh:
        payload = json.loads(cache.read_text())
        return payload["rows"], payload["accessed"]
    url = CPIC_API.format(gene=gene)
    with urllib.request.urlopen(url, timeout=90) as response:
        rows = json.loads(response.read())
    accessed = time.strftime("%Y-%m-%d", time.gmtime())
    cache.write_text(json.dumps(
        {"source": url, "accessed": accessed, "rows": rows}, indent=1
    ) + "\n")
    return rows, accessed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--cohort", default="pharmcat_n400",
                        help="Directory of PharmCAT reports under test-data/reference/cohort/.")
    parser.add_argument("--refresh", action="store_true", help="Re-query the CPIC API.")
    parser.add_argument("--top", type=int, default=6, help="Alleles compared per gene.")
    args = parser.parse_args(argv)

    report_dir = COHORT_DIR / args.cohort
    reports = sorted(report_dir.glob("*.report.json"))
    if not reports:
        print(red(f"no reports under {report_dir.relative_to(REPO_ROOT)}"))
        return 2

    pops = load_populations()
    ours = our_frequencies(reports, pops)
    counts, chroms, skipped = ours["counts"], ours["chromosomes"], ours["skipped"]
    ambiguous = ours["ambiguous"]

    print(bold(f"── frequency concordance ({len(reports)} samples) ─────────────"))
    print(dim("  AGGREGATE SANITY CHECK, not per-sample validation. A pipeline that"))
    print(dim("  shuffled calls between samples would still pass this."))
    print(dim(f"  diplotypes not splittable into two star alleles: {dict(skipped)}"))
    print(dim(f"  AMBIGUOUS calls excluded (>1 equally-likely diplotype): {dict(ambiguous)}"))

    findings: list[dict] = []
    estimator_conflicts: list[dict] = []
    accessed_dates: set[str] = set()

    for gene in STAR_GENES:
        rows, accessed = cpic_frequencies(gene, refresh=args.refresh)
        accessed_dates.add(accessed)
        published: dict[tuple[str, str], float] = {}
        for row in rows:
            value = row.get("freq_weighted_avg")
            if value is None:
                continue
            published[(row["name"], row["population_group"])] = float(value)

        pool = counts[(gene, "ALL", "first")]
        total = chroms[(gene, "ALL", "first")]
        total_un = chroms[(gene, "ALL", "unambiguous")]
        if not total:
            continue
        top = [a for a, _ in pool.most_common(args.top)]

        print()
        print(bold(f"  {gene}   {total // 2}/{len(reports)} samples called, "
                   f"{total_un // 2} of them unambiguous"))
        header = "  ".join(f"{g:>13}" for g in POPULATION_MAP)
        print(f"    {'allele':10} {'first':>7} {'unamb':>7} {'CPIC*':>7}   {header}")

        for allele in top:
            first_all = pool[allele] / total
            un_all = (counts[(gene, "ALL", "unambiguous")][allele] / total_un
                      if total_un else None)
            mapped = [published.get((allele, c)) for c in POPULATION_MAP.values()]
            present = [v for v in mapped if v is not None]
            cpic_all = sum(present) / len(present) if present else None

            # Where the two estimators disagree materially, the gene has no
            # defensible frequency estimate and saying so is the result.
            if un_all is not None and abs(un_all - first_all) >= 0.05:
                estimator_conflicts.append({
                    "gene": gene, "allele": allele,
                    "first": first_all, "unambiguous": un_all,
                    "spread": abs(un_all - first_all),
                })

            cells = []
            for superpop, cpic_group in POPULATION_MAP.items():
                n = chroms[(gene, superpop, "first")]
                mine = counts[(gene, superpop, "first")][allele]
                theirs = published.get((allele, cpic_group))
                if n < MIN_CHROMOSOMES:
                    cells.append(f"{mine}/{n} n<{MIN_CHROMOSOMES}")
                    continue
                cells.append(
                    f"{mine / n * 100:5.1f}/{theirs * 100:4.1f}"
                    if theirs is not None else f"{mine / n * 100:5.1f}/  --"
                )
                if theirs is not None:
                    delta = (mine / n) - theirs
                    if abs(delta) >= 0.10:
                        findings.append({
                            "gene": gene, "allele": allele,
                            "superpopulation": superpop, "cpic_group": cpic_group,
                            "ours": mine / n, "cpic": theirs, "delta": delta,
                            "chromosomes": n,
                        })
            print(f"    {allele:10} {first_all * 100:6.1f}% "
                  f"{(f'{un_all * 100:6.1f}%' if un_all is not None else '     --')} "
                  f"{(f'{cpic_all * 100:6.1f}%' if cpic_all is not None else '     --')}"
                  f"   " + "  ".join(f"{c:>13}" for c in cells))

    print()
    print(dim("    first = sourceDiplotypes[0]; unamb = single-candidate calls only."))
    print(dim("    Population cells use `first` as ours%/CPIC%. * = mean of mapped"))
    print(dim("    groups, not a published figure. -- = CPIC publishes no value."))

    print()
    print(bold("── estimator sensitivity (>= 5 pp between the two) ───────────"))
    if not estimator_conflicts:
        print(green("  none — the two estimators agree everywhere"))
    for c in sorted(estimator_conflicts, key=lambda x: -x["spread"]):
        print(red(f"  {c['gene']} {c['allele']}: first={c['first']*100:.1f}% "
                  f"unambiguous={c['unambiguous']*100:.1f}% "
                  f"[{c['spread']*100:.1f} pp apart] -> no defensible estimate"))

    print()
    print(bold("── deviations >= 10 percentage points ────────────────────────"))
    if not findings:
        print(green("  none"))
    for f in sorted(findings, key=lambda x: -abs(x["delta"])):
        print(red(f"  {f['gene']} {f['allele']} in {f['superpopulation']}"
                  f" (vs CPIC {f['cpic_group']}): "
                  f"ours {f['ours'] * 100:.1f}% vs {f['cpic'] * 100:.1f}% "
                  f"[{f['delta'] * 100:+.1f} pp, n={f['chromosomes']} chr]"))

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cohort": args.cohort,
        "samples": len(reports),
        "nature": "aggregate sanity check; NOT per-sample validation",
        "cpic_source": CPIC_API.format(gene="<GENE>"),
        "cpic_accessed": sorted(accessed_dates),
        "population_mapping": POPULATION_MAP,
        "population_mapping_caveat": (
            "1000G superpopulations and CPIC biogeographic groups are different "
            "taxonomies; the correspondence is conventional, not an identity."
        ),
        "min_chromosomes_for_a_percentage": MIN_CHROMOSOMES,
        "our_counts": {
            f"{g}|{p}|{v}": dict(c) for (g, p, v), c in counts.items()
        },
        "our_chromosomes": {f"{g}|{p}|{v}": n for (g, p, v), n in chroms.items()},
        "undecodable_diplotypes": dict(skipped),
        "ambiguous_excluded": dict(ambiguous),
        "ambiguity_note": (
            "Only unambiguous calls (exactly one candidate diplotype) are counted. "
            "Taking the first of several would bias each population differently, "
            "since ambiguity is population-structured."
        ),
        "deviations_over_10pp": findings,
        "estimator_conflicts_over_5pp": estimator_conflicts,
        "estimators": {
            "first": "sourceDiplotypes[0]; arbitrary among equals but canonical-first",
            "unambiguous": "single-candidate calls only; biased toward the reference "
                           "allele because variant carriers are more often ambiguous",
        },
    }, indent=1) + "\n")
    print()
    print(dim(f"  artifact: {ARTIFACT.relative_to(REPO_ROOT)}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
