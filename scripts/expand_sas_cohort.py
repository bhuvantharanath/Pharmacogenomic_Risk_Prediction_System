"""
Every South Asian sample in the 1000 Genomes panel, not a 75-sample slice of it.

WHY

The SAS figure (CYP2C19 reduced-function 53.3%) is the only quantitative
evidence behind this project's stated Indian-population motivation, and it came
from **75** samples split five ways — per-subpopulation n of 8 to 23. At n=8 a
single carrier moves the rate by 12.5 percentage points, so the per-population
numbers supported nothing and the aggregate rested on a cohort chosen for
overall balance rather than for this question.

The panel contains **601** SAS samples. They were always available; the 75 was a
consequence of proportional stratification across five superpopulations at a
total of 400, not of any limit on what could be fetched.

WHAT THIS DOES NOT FIX

The 1000 Genomes SAS cohorts are **diaspora and regional samples** — Gujarati in
Houston, Indian and Sri Lankan Tamil in the UK, Punjabi in Lahore, Bengali in
Bangladesh. They are not a representative Indian national sample, and four of
the five were collected outside India. Increasing n makes the estimate more
precise; it does not make it representative of a population it never sampled.

The input also remains polymorphic-filtered research-format VCF, so the coverage
gate declines most genes. That is left ACTIVE here on purpose: reporting
frequencies from calls the pipeline would refuse to show a user would measure a
system nobody is running.

Reuses `validate_integration.py` for panel loading and remote slicing rather
than restating either — a second copy of the gene coordinates or the cohort
loader is exactly the duplication that goes stale.
"""

from __future__ import annotations

import collections
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "validate_integration", Path(__file__).parent / "validate_integration.py")
_vi = importlib.util.module_from_spec(_spec)
sys.modules["validate_integration"] = _vi
_spec.loader.exec_module(_vi)

SAS_SUBPOPULATIONS = ("BEB", "GIH", "ITU", "PJL", "STU")

#: Where each cohort was actually collected. Stated because "South Asian" hides
#: it, and four of the five were sampled outside India.
COLLECTED = {
    "GIH": "Gujarati Indian, Houston, USA",
    "ITU": "Indian Telugu, UK",
    "STU": "Sri Lankan Tamil, UK",
    "PJL": "Punjabi, Lahore, Pakistan",
    "BEB": "Bengali, Bangladesh",
}

OUT = REPO / "reports/sas_cohort_expanded.json"


def sas_panel() -> list:
    panel = _vi.load_panel()
    return sorted((s for s in panel if s.superpopulation == "SAS"),
                  key=lambda s: s.sample_id)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    resume = "--no-resume" not in argv
    limit = None
    for i, a in enumerate(argv):
        if a == "--limit" and i + 1 < len(argv):
            limit = int(argv[i + 1])

    cohort = sas_panel()
    if limit:
        cohort = cohort[:limit]

    counts = collections.Counter(s.population for s in cohort)
    print(f"SAS samples in the 1000G panel: {len(cohort)}")
    for pop in SAS_SUBPOPULATIONS:
        print(f"  {pop}  {counts[pop]:4d}   {COLLECTED[pop]}")

    started = time.monotonic()
    print("\nSlicing the seven gene regions for all of them (remote, no whole "
          "genomes)…")
    combined = _vi.slice_cohort(cohort, resume=resume)
    if combined is None:
        print("slice FAILED", file=sys.stderr)
        return 1
    slice_seconds = time.monotonic() - started

    parts = sorted((REPO / "test-data/reference/cohort").glob(
        f"chr*_n{len(cohort)}.vcf.gz"))
    total_bytes = sum(p.stat().st_size for p in parts) + combined.stat().st_size

    print(f"\nsliced in {slice_seconds:.0f}s, "
          f"{total_bytes / 1e6:.1f} MB on disk")

    outdir = REPO / "test-data/reference/cohort" / f"pharmcat_sas_n{len(cohort)}"
    print("\nRunning PharmCAT per sample…")
    run_started = time.monotonic()
    # Returns a BOOL, not a list of paths — count the files it wrote instead.
    ok = _vi.run_pharmcat_cohort(combined, outdir, resume=resume)
    run_seconds = time.monotonic() - run_started
    reports = sorted(outdir.glob("*.report.json"))
    print(f"  {len(reports)} reports in {run_seconds:.0f}s (ok={ok})")

    OUT.write_text(json.dumps({
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "panel_source": "1000G_3202_populations.txt (3202 samples)",
        "sas_total": len(cohort),
        "by_subpopulation": {p: counts[p] for p in SAS_SUBPOPULATIONS},
        "collected_where": COLLECTED,
        "slice_seconds": round(slice_seconds, 1),
        "slice_megabytes": round(total_bytes / 1e6, 1),
        "pharmcat_seconds": round(run_seconds, 1),
        "reports": len(reports),
        "report_dir": str(outdir.relative_to(REPO)),
        "combined_vcf": str(combined.relative_to(REPO)),
        "nature": (
            "1000 Genomes SAS cohorts are diaspora and regional samples, not a "
            "representative Indian national sample. Input remains "
            "polymorphic-filtered research format and the coverage gate is "
            "active."),
    }, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
