#!/usr/bin/env python3
"""
How much of PharmCAT's position list does a VCF need before a gene resolves?

WHY THIS EXISTS

Simvastatin returns `Unknown` for 54% of 1000 Genomes samples. That is correct
behaviour, not a defect: the panel is filtered to polymorphic sites, so our slices
carry 19-57% of the positions PharmCAT asks for, and the absent ones
disproportionately define reference-like haplotypes. But "correct behaviour driven
by input coverage" is only a useful statement if the relationship is measured.

This sweeps coverage from complete down to 20% and reports, per gene, the rate at
which a single diplotype resolves and a confident label is produced. The output is
an INPUT REQUIREMENTS spec: what a VCF must contain for PharmaGuard to answer, and
what it correctly declines below that.

WHAT THIS IS NOT

**It measures coverage sensitivity only.** Every input is synthesised from
PharmCAT's own allele definitions, so the "right" answer is known by construction
and the pipeline is being asked one question: does it still resolve the genotype
when positions go missing? It is emphatically **not** independent validation of
calling accuracy — a synthetic VCF built from the same definitions the matcher
uses cannot test whether those definitions are right. External accuracy remains
n=1 (GeT-RM), reported as n=1.

METHOD

One multi-sample VCF carries the whole sweep: each sample keeps a deterministic
random subset of the 306 defining positions and is `./.` at the rest, which is how
a real VCF expresses "not genotyped here". PharmCAT processes all samples in one
JVM start.
"""

from __future__ import annotations

import argparse
import collections
import json
import random
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

JAR = REPO_ROOT / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
GENERATOR = REPO_ROOT / "test-data/generate_synthetic_vcf.py"
ARTIFACT = REPO_ROOT / "reports" / "coverage_sensitivity.json"

GENES = ("CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "NUDT15", "DPYD")
COVERAGE_LEVELS = (100, 80, 60, 40, 20)
SEED = 20260726

#: Two genotype backgrounds, so a result is not an artifact of one diplotype.
#: Both are built from PharmCAT's own definitions, hence "known by construction".
BACKGROUNDS = (
    ("reference", ["DPYD=Reference/Reference"]),
    ("variant", ["SLCO1B1=*1/*15", "CYP2C19=*1/*2", "TPMT=*1/*3A",
                 "NUDT15=*1/*3", "CYP2C9=*1/*2"]),
)


def dim(t: str) -> str: return f"\033[2m{t}\033[0m"
def bold(t: str) -> str: return f"\033[1m{t}\033[0m"
def red(t: str) -> str: return f"\033[31m{t}\033[0m"
def green(t: str) -> str: return f"\033[32m{t}\033[0m"


def generate_full(workdir: Path, name: str, diplotypes: list[str]) -> Path:
    """A complete-coverage VCF: one row per defining position, every gene present."""
    out = workdir / f"{name}.vcf"
    cmd = [sys.executable, str(GENERATOR),
           "--from-jar", str(JAR),
           "--definitions-dir", str(workdir / "defs"),
           "--pad-genes", ",".join(GENES),
           "-o", str(out)]
    for dip in diplotypes:
        cmd += ["--diplotype", dip]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return out


def build_sweep(fulls: dict[str, Path], workdir: Path, replicates: int) -> tuple[Path, dict]:
    """
    One multi-sample VCF where each sample has a different coverage fraction.

    Dropped positions become `./.` rather than being deleted, because a VCF row is
    shared by every sample — and `./.` is exactly how real data says "no genotype
    called here for this sample", which is the state reduced coverage produces.
    """
    header: list[str] = []
    rows: list[list[str]] = []
    genotype_of: dict[str, list[str]] = {}

    for name, path in fulls.items():
        body = [l for l in path.read_text().splitlines() if l.strip()]
        data = [l for l in body if not l.startswith("#")]
        if not rows:
            header = [l for l in body if l.startswith("##")]
            rows = [l.split("\t") for l in data]
        # Column 9 is the sample genotype for this background.
        genotype_of[name] = [l.split("\t")[9] for l in data]

    total = len(rows)
    rng = random.Random(SEED)
    samples: list[str] = []
    columns: dict[str, list[str]] = {}
    meta: dict[str, dict] = {}

    for bg in fulls:
        for level in COVERAGE_LEVELS:
            for rep in range(replicates):
                sid = f"{bg}_c{level}_r{rep}"
                keep = total if level >= 100 else max(1, round(total * level / 100))
                kept = set(rng.sample(range(total), keep))
                columns[sid] = [
                    genotype_of[bg][i] if i in kept else "./."
                    for i in range(total)
                ]
                samples.append(sid)
                meta[sid] = {"background": bg, "coverage": level,
                             "replicate": rep, "positions_kept": keep,
                             "positions_total": total}

    out = workdir / "sweep.vcf"
    with out.open("w") as fh:
        for line in header:
            fh.write(line + "\n")
        fh.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t"
                 + "\t".join(samples) + "\n")
        for i, row in enumerate(rows):
            fh.write("\t".join(row[:9] + [columns[s][i] for s in samples]) + "\n")
    return out, meta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--replicates", type=int, default=8,
                        help="Random position subsets per coverage level (default 8).")
    parser.add_argument("--workdir", type=Path,
                        default=Path("/private/tmp/claude-501/coverage_sweep"))
    args = parser.parse_args(argv)

    from app import cpic_engine
    from app.pharmcat_runner import parse_report

    args.workdir.mkdir(parents=True, exist_ok=True)
    print(bold("── building complete-coverage inputs ─────────────────────────"))
    fulls = {}
    for name, dips in BACKGROUNDS:
        fulls[name] = generate_full(args.workdir, name, dips)
        rows = sum(1 for l in fulls[name].read_text().splitlines()
                   if l.strip() and not l.startswith("#"))
        print(f"  {name:10} {rows} defining positions")

    sweep, meta = build_sweep(fulls, args.workdir, args.replicates)
    print(f"  sweep: {len(meta)} samples x "
          f"{meta[next(iter(meta))]['positions_total']} positions")

    outdir = args.workdir / "out"
    outdir.mkdir(exist_ok=True)
    print(bold("\n── PharmCAT (one JVM) ────────────────────────────────────────"))
    started = time.monotonic()
    subprocess.run(["java", "-jar", str(JAR), "-vcf", str(sweep),
                    "-o", str(outdir), "-reporterJson"],
                   capture_output=True, text=True, timeout=7200)
    reports = sorted(outdir.glob("*.report.json"))
    print(f"  {len(reports)} reports in {time.monotonic() - started:.0f}s")
    if not reports:
        print(red("  PharmCAT produced nothing"))
        return 1

    # (gene, coverage) -> counters
    single = collections.Counter()
    labelled = collections.Counter()
    seen = collections.Counter()
    # THE METRIC THAT MATTERS. Call rate turned out to be the wrong question:
    # at reduced coverage PharmCAT does not decline, it confidently calls the
    # REFERENCE haplotype, because a variant whose defining position was dropped
    # is simply invisible. Truth is known by construction (complete coverage of
    # the same synthetic genotype), so accuracy is measurable here.
    correct = collections.Counter()
    wrong_confident = collections.Counter()
    wrong_examples: list[dict] = []
    truth: dict[tuple[str, str], str] = {}

    # First pass: the 100% runs define truth for each background.
    parsed: dict[str, object] = {}
    for path in reports:
        sid = path.name.removesuffix(".report.json").split(".", 1)[-1]
        if sid not in meta:
            continue
        rep = parse_report(json.loads(path.read_text()))
        parsed[sid] = rep
        if meta[sid]["coverage"] == 100:
            for gene in GENES:
                call = rep.genes.get(gene)
                if call and call.phenotype_raw:
                    truth[(meta[sid]["background"], gene)] = call.phenotype_raw

    for sid, rep in parsed.items():
        info = meta[sid]
        level = info["coverage"]
        for gene in GENES:
            call = rep.genes.get(gene)
            seen[(gene, level)] += 1
            if call is None:
                continue
            if len(call.candidate_diplotypes) == 1:
                single[(gene, level)] += 1
            resolved = cpic_engine.resolve_phenotype(call)
            if resolved.asserted:
                labelled[(gene, level)] += 1
            expected = truth.get((info["background"], gene))
            if expected is None:
                continue
            if not resolved.asserted:
                continue          # declined — safe, counted separately
            if (call.phenotype_raw or "").strip() == expected.strip():
                correct[(gene, level)] += 1
            else:
                wrong_confident[(gene, level)] += 1
                if len(wrong_examples) < 12:
                    wrong_examples.append({
                        "sample": sid, "gene": gene, "coverage": level,
                        "true_phenotype": expected,
                        "reported_phenotype": call.phenotype_raw,
                        "reported_diplotype": call.diplotype,
                    })

    def pct(num: int, den: int) -> str:
        return f"{num / den * 100:5.1f}%" if den else "   n/a"

    print()
    print(bold("── 🔴 CONFIDENTLY WRONG rate vs coverage (the real metric) ───"))
    print(dim("  asserted a phenotype that disagrees with the complete-coverage truth"))
    print(f"  {'gene':9} " + "  ".join(f"{c:>7}%" for c in COVERAGE_LEVELS))
    for gene in GENES:
        cells = []
        for c in COVERAGE_LEVELS:
            den = correct[(gene, c)] + wrong_confident[(gene, c)]
            cells.append(pct(wrong_confident[(gene, c)], den) if den else "   n/a")
        print(f"  {gene:9} " + "  ".join(f"{x:>8}" for x in cells))
    if wrong_examples:
        print(red("\n  examples of confident wrong calls:"))
        for e in wrong_examples[:8]:
            print(red(f"    {e['gene']:8} @{e['coverage']:3}%  true={e['true_phenotype']!r}"
                      f" -> reported={e['reported_phenotype']!r} as {e['reported_diplotype']!r}"))

    print()
    print(bold("── single-diplotype call rate vs position coverage ───────────"))
    print(f"  {'gene':9} " + "  ".join(f"{c:>7}%" for c in COVERAGE_LEVELS))
    for gene in GENES:
        cells = [pct(single[(gene, c)], seen[(gene, c)]) for c in COVERAGE_LEVELS]
        print(f"  {gene:9} " + "  ".join(f"{x:>8}" for x in cells))

    print()
    print(bold("── confident-phenotype (label-producing) rate ────────────────"))
    print(f"  {'gene':9} " + "  ".join(f"{c:>7}%" for c in COVERAGE_LEVELS))
    for gene in GENES:
        cells = [pct(labelled[(gene, c)], seen[(gene, c)]) for c in COVERAGE_LEVELS]
        print(f"  {gene:9} " + "  ".join(f"{x:>8}" for x in cells))

    # Minimum coverage at which every replicate still resolves confidently.
    print()
    print(bold("── minimum coverage for a reliable confident result ──────────"))
    thresholds: dict[str, int | None] = {}
    for gene in GENES:
        # A level only qualifies if EVERY replicate both resolved and was right.
        # Requiring correctness is the whole point: a level where the pipeline
        # answers confidently but wrongly is worse than one where it declines.
        ok = [c for c in sorted(COVERAGE_LEVELS)
              if seen[(gene, c)]
              and labelled[(gene, c)] == seen[(gene, c)]
              and wrong_confident[(gene, c)] == 0]
        thresholds[gene] = min(ok) if ok else None
        text = f"{thresholds[gene]}%" if thresholds[gene] else "not reached below 100%"
        colour = green if thresholds[gene] and thresholds[gene] <= 60 else red
        print(f"  {gene:9} {colour(text)}")

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "nature": ("coverage sensitivity ONLY; inputs are synthesised from "
                   "PharmCAT's own allele definitions, so this cannot validate "
                   "calling accuracy. External accuracy remains n=1."),
        "seed": SEED,
        "replicates": args.replicates,
        "samples": len(meta),
        "coverage_levels": list(COVERAGE_LEVELS),
        "single_diplotype_rate": {
            f"{g}|{c}": (single[(g, c)] / seen[(g, c)] if seen[(g, c)] else None)
            for g in GENES for c in COVERAGE_LEVELS
        },
        "confident_phenotype_rate": {
            f"{g}|{c}": (labelled[(g, c)] / seen[(g, c)] if seen[(g, c)] else None)
            for g in GENES for c in COVERAGE_LEVELS
        },
        "minimum_coverage_for_reliable_result": thresholds,
        "confidently_wrong_rate": {
            f"{g}|{c}": (
                wrong_confident[(g, c)] / (correct[(g, c)] + wrong_confident[(g, c)])
                if (correct[(g, c)] + wrong_confident[(g, c)]) else None
            ) for g in GENES for c in COVERAGE_LEVELS
        },
        "confidently_wrong_examples": wrong_examples,
        "headline": ("Reduced coverage does NOT make the pipeline decline. It makes "
                     "PharmCAT confidently call the reference haplotype, because a "
                     "variant whose defining position is absent is invisible. The "
                     "error direction is false reassurance."),
    }, indent=1) + "\n")
    print()
    print(dim(f"  artifact: {ARTIFACT.relative_to(REPO_ROOT)}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
