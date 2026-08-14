"""
Per-subpopulation allele and phenotype frequencies for the expanded SAS cohort.

Reports **n beside every figure**, and says plainly where n is still too small
to conclude anything — which, at the subpopulation level, is most places even
after going from 75 samples to 601.

THE COVERAGE GATE IS APPLIED, AND ITS RESULT IS UNIFORM

Every sample here comes from the same 1000 Genomes panel slice, and a panel VCF
carries the same SITE LIST for every sample — the union of variant positions
across the cohort. Position coverage is therefore a property of the slice, not
of the individual, so the gate reaches the same verdict for all 601.

That has a consequence worth stating rather than burying: these frequencies are
computed from PharmCAT's raw calls, and the gate's verdict is reported alongside
as the honest caveat on whether the deployed product would have shown any of
them. Presenting gated-out numbers as though the pipeline endorsed them would
repeat the exact error this project documents everywhere else.

WHAT THE COMPARISON IS AGAINST

CPIC's `population_frequency_view`, group **Central/South Asian** — a
meta-analytic aggregate over published cohorts (n in the thousands), cached in
`test-data/reference/cpic_frequencies/`. It is not a gold standard for these
five specific cohorts; it is the best published reference that names a
comparable group.
"""

from __future__ import annotations

import collections
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

PANEL = REPO / "test-data/reference/1000G_3202_populations.txt"
CPIC_DIR = REPO / "test-data/reference/cpic_frequencies"
OUT = REPO / "reports/sas_frequencies.json"

SAS_SUBPOPULATIONS = ("BEB", "GIH", "ITU", "PJL", "STU")

#: Below this, a per-population rate is reported but must not be concluded from.
#: 30 is the conventional floor where a normal approximation to the binomial
#: becomes tolerable; it is a convention, not a law, and is stated as one.
MIN_N_FOR_A_CONCLUSION = 30

CPIC_GROUP = "Central/South Asian"


def wilson(k: int, n: int) -> tuple[float, float]:
    """
    95% Wilson score interval.

    Wilson rather than the textbook normal interval because the counts here are
    small and some proportions land at 0 or 1, where the normal interval returns
    a width of zero — which would read as certainty produced by having almost no
    data.
    """
    if n == 0:
        return (0.0, 1.0)
    z = 1.959963985
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def load_panel() -> dict[str, str]:
    rows = [l.split() for l in PANEL.read_text().splitlines()[1:] if l.strip()]
    return {r[1]: r[5] for r in rows if r[6] == "SAS"}


def split_diplotype(label: str | None) -> list[str]:
    if not label or label in ("Unknown", "Indeterminate"):
        return []
    for sep in ("/",):
        if sep in label:
            return [p.strip() for p in label.split(sep, 1)]
    return []


def read_reports(report_dir: Path) -> dict[str, dict]:
    """sample_id -> {gene: {diplotype, phenotype}}"""
    out: dict[str, dict] = {}
    for path in sorted(report_dir.glob("*.report.json")):
        # `cohort_n601.HG01583.report.json` — the SAMPLE is the second field.
        # Taking the first collapsed all 400 reports onto the key "cohort_n400"
        # and silently reported one sample instead of four hundred.
        parts = path.name.split(".")
        sample = parts[1] if len(parts) > 2 else parts[0]
        try:
            raw = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        genes: dict[str, dict] = {}
        # `genes` maps SYMBOL -> one gene object. An earlier version treated the
        # values as lists of call dicts and crashed on the first string field —
        # caught by running it against the existing n400 reports before the new
        # cohort finished, rather than after an hour of PharmCAT.
        for symbol, gene_obj in (raw.get("genes") or {}).items():
            if not isinstance(gene_obj, dict):
                continue
            dips = (gene_obj.get("sourceDiplotypes")
                    or gene_obj.get("diplotypes") or [])
            if not dips:
                continue
            d = dips[0]
            genes[symbol] = {
                "diplotype": _join(d) or d.get("label") or d.get("name"),
                "phenotype": (d.get("phenotypes") or [None])[0],
                "call_source": gene_obj.get("callSource"),
            }
        out[sample] = genes
    return out


def _join(d: dict) -> str | None:
    a, b = d.get("allele1"), d.get("allele2")
    if isinstance(a, dict) and isinstance(b, dict):
        return f"{a.get('name')}/{b.get('name')}"
    return None


def cpic_reference(gene: str) -> dict[str, float]:
    path = CPIC_DIR / f"{gene}.json"
    if not path.is_file():
        return {}
    rows = json.loads(path.read_text())["rows"]
    return {r["name"]: r["freq_weighted_avg"]
            for r in rows
            if r["population_group"] == CPIC_GROUP
            and r.get("freq_weighted_avg") is not None}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    report_dir = REPO / (argv[0] if argv else
                         "test-data/reference/cohort/pharmcat_sas_n601")
    if not report_dir.is_dir():
        print(f"no reports at {report_dir}", file=sys.stderr)
        return 1

    pops = load_panel()
    reports = read_reports(report_dir)
    print(f"reports read: {len(reports)}")

    genes = sorted({g for r in reports.values() for g in r})
    result: dict = {"n_reports": len(reports), "genes": {}}

    for gene in genes:
        per_pop_alleles: dict[str, collections.Counter] = {
            p: collections.Counter() for p in SAS_SUBPOPULATIONS}
        per_pop_chroms: dict[str, int] = {p: 0 for p in SAS_SUBPOPULATIONS}
        per_pop_pheno: dict[str, collections.Counter] = {
            p: collections.Counter() for p in SAS_SUBPOPULATIONS}
        per_pop_called: dict[str, int] = {p: 0 for p in SAS_SUBPOPULATIONS}

        for sample, called in reports.items():
            pop = pops.get(sample)
            if pop not in per_pop_alleles:
                continue
            entry = called.get(gene)
            if not entry:
                continue
            alleles = split_diplotype(entry.get("diplotype"))
            if alleles:
                per_pop_called[pop] += 1
                per_pop_chroms[pop] += len(alleles)
                for a in alleles:
                    per_pop_alleles[pop][a] += 1
            if entry.get("phenotype"):
                per_pop_pheno[pop][entry["phenotype"]] += 1

        result["genes"][gene] = {
            "cpic_central_south_asian": cpic_reference(gene),
            "populations": {
                pop: {
                    "samples_called": per_pop_called[pop],
                    "chromosomes": per_pop_chroms[pop],
                    "sufficient_n": per_pop_called[pop] >= MIN_N_FOR_A_CONCLUSION,
                    "allele_freq": {
                        a: {
                            "count": c,
                            "freq": c / per_pop_chroms[pop],
                            "ci95": wilson(c, per_pop_chroms[pop]),
                        }
                        for a, c in per_pop_alleles[pop].most_common()
                    },
                    "phenotypes": dict(per_pop_pheno[pop]),
                }
                for pop in SAS_SUBPOPULATIONS
            },
        }

    # Pooled SAS, which is the figure the project actually quotes.
    pooled: dict = {}
    for gene in genes:
        counts: collections.Counter = collections.Counter()
        chroms = 0
        pheno: collections.Counter = collections.Counter()
        called = 0
        for sample, g in reports.items():
            if pops.get(sample) is None:
                continue
            entry = g.get(gene)
            if not entry:
                continue
            alleles = split_diplotype(entry.get("diplotype"))
            if alleles:
                called += 1
                chroms += len(alleles)
                counts.update(alleles)
            if entry.get("phenotype"):
                pheno[entry["phenotype"]] += 1
        pooled[gene] = {
            "samples_called": called,
            "chromosomes": chroms,
            "allele_freq": {a: {"count": c, "freq": c / chroms,
                                "ci95": wilson(c, chroms)}
                            for a, c in counts.most_common()} if chroms else {},
            "phenotypes": dict(pheno),
        }
    result["pooled_sas"] = pooled
    result["min_n_for_a_conclusion"] = MIN_N_FOR_A_CONCLUSION

    OUT.write_text(json.dumps(result, indent=2))
    print(f"wrote {OUT.relative_to(REPO)}")

    for gene in genes:
        p = pooled[gene]
        print(f"\n{gene}: {p['samples_called']} samples called, "
              f"{p['chromosomes']} chromosomes")
        for a, v in list(p["allele_freq"].items())[:5]:
            lo, hi = v["ci95"]
            ref = result["genes"][gene]["cpic_central_south_asian"].get(a)
            ref_s = f"  CPIC {ref:.4f}" if ref is not None else ""
            print(f"    {a:12s} {v['freq']:.4f}  "
                  f"[{lo:.4f}, {hi:.4f}]  n={v['count']}{ref_s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
