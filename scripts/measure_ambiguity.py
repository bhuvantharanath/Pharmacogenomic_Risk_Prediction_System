#!/usr/bin/env python3
"""
Is an ambiguous DIPLOTYPE also an ambiguous PHENOTYPE?

THE QUESTION

SLCO1B1 returns a diplotype for 398/400 validation samples but a *unique* one for
only 39.8%. The pipeline collapses every ambiguous call to `Unknown`. That is only
correct if the candidates actually disagree about function — and they need not.
PharmCAT may be unable to choose between `*5/*37` and `*5/*42` while both mean
decreased function, in which case collapsing to Unknown discards a phenotype we
could state with confidence.

THREE DEFINITIONS, because the answer depends on which one you mean

  STRICT       every candidate carries the identical phenotype string.
  INFORMATIVE  every candidate that says anything carries the identical string.
               `n/a` is PharmCAT's marker for a diplotype with no CPIC phenotype
               assignment — it is an absence of information, not a competing
               claim, so counting it as disagreement would understate concordance.
  CLASS        every informative candidate maps to the same value of OUR
               `Phenotype` enum. This is the actionable one: it is exactly the
               condition under which we could report a confident phenotype
               alongside an ambiguous diplotype.

`Indeterminate` is treated as informative and NOT merged into the classes above:
it is PharmCAT's positive statement that the genotype has no phenotype
assignment, which is different from `n/a` on a single candidate.

This script measures. It proposes nothing and changes nothing.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

COHORT_DIR = REPO_ROOT / "test-data" / "reference" / "cohort"
ARTIFACT = REPO_ROOT / "reports" / "ambiguity_concordance.json"

TARGET_GENES = ("CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "NUDT15", "DPYD", "CYP2D6")

#: PharmCAT's "this candidate has no CPIC phenotype" marker. Absence of a claim.
NO_INFO = {"n/a", "", "no result"}


def dim(t: str) -> str: return f"\033[2m{t}\033[0m"
def red(t: str) -> str: return f"\033[31m{t}\033[0m"
def green(t: str) -> str: return f"\033[32m{t}\033[0m"
def bold(t: str) -> str: return f"\033[1m{t}\033[0m"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", default="pharmcat_n400")
    args = parser.parse_args(argv)

    from app.cpic_engine import map_phenotype

    reports = sorted((COHORT_DIR / args.cohort).glob("*.report.json"))
    if not reports:
        print(red(f"no reports under {args.cohort}"))
        return 2

    # gene -> counters
    total = collections.Counter()
    ambiguous = collections.Counter()
    strict = collections.Counter()
    informative = collections.Counter()
    class_conc = collections.Counter()
    #: gene -> Counter of the resolved enum value when CLASS-concordant
    resolved = collections.defaultdict(collections.Counter)
    #: gene -> examples of genuine disagreement, for the report
    discordant_examples = collections.defaultdict(list)

    for path in reports:
        raw = json.loads(path.read_text())
        genes = raw.get("genes") or {}
        section = genes.get("CPIC") if "CPIC" in genes else genes
        sample = path.name.removesuffix(".report.json").split(".", 1)[-1]
        for gene in TARGET_GENES:
            block = (section or {}).get(gene)
            if not isinstance(block, dict):
                continue
            candidates = block.get("sourceDiplotypes") or []
            if not candidates:
                continue
            total[gene] += 1
            if len(candidates) == 1:
                continue
            ambiguous[gene] += 1

            phenotypes = []
            for entry in candidates:
                if not isinstance(entry, dict):
                    continue
                values = entry.get("phenotypes") or []
                phenotypes.append((values[0] if values else "").strip())

            if len({p.lower() for p in phenotypes}) == 1:
                strict[gene] += 1

            said = [p for p in phenotypes if p.lower() not in NO_INFO]
            if not said:
                continue
            if len({p.lower() for p in said}) == 1:
                informative[gene] += 1

            classes = {map_phenotype(p) for p in said}
            if len(classes) == 1:
                class_conc[gene] += 1
                resolved[gene][next(iter(classes)).value] += 1
            elif len(discordant_examples[gene]) < 4:
                discordant_examples[gene].append({
                    "sample": sample,
                    "candidates": [
                        f"{(c.get('label') or '?')} -> "
                        f"{((c.get('phenotypes') or ['?'])[0])}"
                        for c in candidates if isinstance(c, dict)
                    ][:6],
                    "classes": sorted(c.value for c in classes),
                })

    print(bold(f"── ambiguous diplotype vs ambiguous phenotype ({len(reports)} samples) ──"))
    print(f"  {'gene':9} {'called':>7} {'ambig':>7} {'strict':>14} "
          f"{'informative':>14} {'same class':>14}")
    for gene in TARGET_GENES:
        n_amb = ambiguous[gene]
        if not total[gene]:
            continue
        if not n_amb:
            print(f"  {gene:9} {total[gene]:7} {0:7} " + " " * 14 +
                  dim("       (no ambiguous calls)"))
            continue
        def pct(c: int) -> str:
            return f"{c:4}/{n_amb:<4} {c / n_amb * 100:4.1f}%"
        print(f"  {gene:9} {total[gene]:7} {n_amb:7} "
              f"{pct(strict[gene]):>14} {pct(informative[gene]):>14} "
              f"{pct(class_conc[gene]):>14}")

    print()
    print(bold("── where CLASS-concordant, what phenotype would be recoverable ──"))
    any_recoverable = False
    for gene in TARGET_GENES:
        if not resolved[gene]:
            continue
        any_recoverable = True
        pretty = ", ".join(f"{k}={v}" for k, v in resolved[gene].most_common())
        print(f"  {gene:9} {sum(resolved[gene].values()):4} calls -> {pretty}")
    if not any_recoverable:
        print(dim("  none — no ambiguous call resolves to a single phenotype class"))

    print()
    print(bold("── genuine disagreement, examples ────────────────────────────"))
    for gene in TARGET_GENES:
        for ex in discordant_examples[gene][:2]:
            print(f"  {gene} {ex['sample']} -> classes {ex['classes']}")
            for c in ex["candidates"][:4]:
                print(dim(f"      {c}"))

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cohort": args.cohort,
        "samples": len(reports),
        "definitions": {
            "strict": "all candidates carry the identical phenotype string",
            "informative": "all candidates that say anything agree; n/a ignored",
            "class": "all informative candidates map to one Phenotype enum value",
        },
        "per_gene": {
            gene: {
                "called": total[gene],
                "ambiguous": ambiguous[gene],
                "strict_concordant": strict[gene],
                "informative_concordant": informative[gene],
                "class_concordant": class_conc[gene],
                "class_concordant_rate": (
                    class_conc[gene] / ambiguous[gene] if ambiguous[gene] else None
                ),
                "recoverable_phenotypes": dict(resolved[gene]),
            }
            for gene in TARGET_GENES if total[gene]
        },
        "discordant_examples": {g: v for g, v in discordant_examples.items() if v},
    }, indent=1) + "\n")
    print()
    print(dim(f"  artifact: {ARTIFACT.relative_to(REPO_ROOT)}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
