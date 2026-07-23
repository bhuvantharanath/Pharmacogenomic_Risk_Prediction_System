#!/usr/bin/env python3
"""
Enumerate which (drug, gene, phenotype) cases this system can ACTUALLY produce.

WHY NOT JUST 6 DRUGS x 6 PHENOTYPES
    Because that product is fiction. Three independent things prune it:

      1. Not every gene has every phenotype. SLCO1B1 is a transporter and has
         no "Ultrarapid Metabolizer"; TPMT has no rapid phenotypes. The truth
         lives in PharmCAT's own per-gene phenotype tables, not in our heads.
      2. CYP2D6 is never called from an unphased VCF at all, so only its
         `Unknown` case is reachable — the other five are unreachable no matter
         what the gene's phenotype table says.
      3. A phenotype PharmCAT can emit may still have no CPIC recommendation
         attached, in which case our pipeline produces `Unknown` and there is
         nothing to explain.

    Generating prose for a case we cannot produce would be padding coverage
    numbers with fiction. This script draws the line, records the reason
    machine-readably, and the generator honours it.

SOURCES OF TRUTH
    Phenotypes  : PharmCAT's `org/pharmgkb/pharmcat/phenotype/<GENE>.json`,
                  extracted from the JAR (`--phenotype-dir`), falling back to
                  the phenotypes observed in our checked-in report fixtures.
    Drug -> gene: `backend/app/data/label_mapping.yaml` (`drug_primary_gene`).
    CPIC text   : the checked-in PharmCAT report fixtures.

USAGE
    python scripts/enumerate_cases.py
    python scripts/enumerate_cases.py --phenotype-dir /path/to/extracted/phenotype
    python scripts/enumerate_cases.py --from-jar /path/to/pharmcat.jar
    python scripts/enumerate_cases.py --json
"""

from __future__ import annotations

import argparse
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from _common import (
    CASE_MATRIX_PATH,
    REPO_ROOT,
    bold,
    dim,
    green,
    load_json,
    rule,
    write_json_atomic,
    yellow,
)

from app.cpic_engine import load_mapping, map_phenotype, select_annotation
from app.models import Phenotype
from app.pharmcat_runner import parse_report

FIXTURE_DIR = REPO_ROOT / "backend" / "tests" / "fixtures"
JAR_PHENOTYPE_PREFIX = "org/pharmgkb/pharmcat/phenotype/"

#: Genes PharmCAT cannot call from a plain, unphased VCF, with the reason.
#: Verified empirically in Phase 2: with all 157 CYP2D6 definition positions
#: present, PharmCAT still reports `callSource: NONE` and
#: `matcherMetadata.callCyp2d: false`.
UNCALLABLE_GENES: dict[str, str] = {
    "CYP2D6": (
        "gene not callable from unphased VCF — star alleles depend on "
        "structural/copy-number variation a VCF cannot express; PharmCAT "
        "reports callSource=NONE even with all definition positions present"
    ),
}


def load_phenotypes_from_jar(jar: Path, dest: Path) -> Path:
    """Extract PharmCAT's per-gene phenotype JSONs from the JAR."""
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(jar) as archive:
        for name in archive.namelist():
            if name.startswith(JAR_PHENOTYPE_PREFIX) and name.endswith(".json"):
                (dest / Path(name).name).write_bytes(archive.read(name))
                count += 1
    if count == 0:
        raise SystemExit(f"error: {jar} contains nothing under {JAR_PHENOTYPE_PREFIX}")
    print(dim(f"  extracted {count} phenotype tables to {dest}"))
    return dest


def phenotypes_for_gene(gene: str, phenotype_dir: Path | None) -> tuple[set[str], str]:
    """
    Every phenotype PharmCAT can emit for `gene`, and where we learned it.

    Returns raw PharmCAT wording (e.g. "Poor Metabolizer"), not our enum, so
    the mapping step is visible rather than assumed.
    """
    if phenotype_dir:
        path = phenotype_dir / f"{gene}.json"
        if path.is_file():
            data = load_json(path)
            results = {
                entry.get("generesult")
                for entry in (data.get("diplotypes") or [])
                if entry.get("generesult")
            }
            if results:
                return results, f"PharmCAT phenotype table ({path.name})"

    # Fallback: whatever our own fixtures happen to contain. Weaker evidence,
    # and labelled as such in the output so nobody mistakes it for complete.
    observed: set[str] = set()
    for fixture in sorted(FIXTURE_DIR.glob("pharmcat_report_*.json")):
        report = parse_report(load_json(fixture))
        call = report.gene(gene)
        if call and call.phenotype_raw:
            observed.add(call.phenotype_raw)
    return observed, "observed in checked-in report fixtures (INCOMPLETE)"


def cpic_text_for(drug: str, phenotype: Phenotype) -> tuple[bool, str]:
    """
    Does a CPIC recommendation exist for this (drug, phenotype)?

    Uses the production selector against the real fixtures, so this answers the
    question the runtime would answer — not an approximation of it.
    """
    for fixture in sorted(FIXTURE_DIR.glob("pharmcat_report_*.json")):
        report = parse_report(load_json(fixture))
        guideline = report.drug(drug)
        if guideline is None:
            continue
        for gene_symbol in guideline.genes or []:
            call = report.gene(gene_symbol)
            if call is None or not call.is_called:
                continue
            if map_phenotype(call.phenotype_raw) is not phenotype:
                continue
            annotation, _ = select_annotation(guideline, report)
            if annotation and (annotation.drug_recommendation or "").strip():
                return True, (annotation.drug_recommendation or "")[:120]
    return False, ""


def build_matrix(phenotype_dir: Path | None) -> dict:
    mapping = load_mapping()
    drug_to_gene: dict[str, str] = mapping.get("drug_primary_gene", {})

    # Only the drugs the mechanism corpus covers — those are the ones we can
    # ground an explanation for.
    from app.retrieval import all_documents

    corpus_drugs = {d.drug for d in all_documents()}
    drugs = sorted(corpus_drugs & set(drug_to_gene))

    cases: list[dict] = []
    for drug in drugs:
        gene = drug_to_gene[drug]
        raw_phenotypes, provenance = phenotypes_for_gene(gene, phenotype_dir)

        # Map PharmCAT wording onto our contract enum, keeping only what the
        # mapping recognises. Unknown is always in play: any gene can fail to
        # call, and our pipeline must have something to say when it does.
        enum_phenotypes: dict[Phenotype, str] = {}
        for raw in sorted(raw_phenotypes):
            mapped = map_phenotype(raw)
            if mapped is not Phenotype.UNKNOWN:
                enum_phenotypes.setdefault(mapped, raw)
        enum_phenotypes.setdefault(Phenotype.UNKNOWN, "No Result")

        for phenotype in sorted(enum_phenotypes, key=lambda p: p.value):
            raw = enum_phenotypes[phenotype]
            reachable = True
            reason = ""
            evidence = provenance

            if gene in UNCALLABLE_GENES and phenotype is not Phenotype.UNKNOWN:
                reachable = False
                reason = UNCALLABLE_GENES[gene]
                evidence = "verified empirically in Phase 2 (see infra/PHARMCAT_NOTES.md §4)"
            elif phenotype is Phenotype.UNKNOWN:
                # Always reachable: PharmCAT can fail to call any gene, and a
                # drug outside CPIC always lands here.
                reason = ""
                evidence = "any gene can fail to call; also the no-CPIC-guidance path"
            else:
                has_cpic, sample = cpic_text_for(drug, phenotype)
                if not has_cpic:
                    reachable = False
                    reason = (
                        "no CPIC recommendation text for this gene-phenotype-drug "
                        "triple in the available PharmCAT output — the pipeline "
                        "returns Unknown, so there is no recommendation to explain"
                    )
                else:
                    evidence = f"{provenance}; CPIC text present, e.g. {sample!r}"

            cases.append(
                {
                    "drug": drug,
                    "gene": gene,
                    "phenotype": phenotype.value,
                    "pharmcat_phenotype": raw,
                    "reachable": reachable,
                    "reason": reason,
                    "evidence": evidence,
                }
            )

    reachable_count = sum(1 for c in cases if c["reachable"])
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Which (drug, gene, phenotype) cases this pipeline can actually "
            "produce. Explanations are generated ONLY for reachable cases; "
            "unreachable ones are documented, never authored."
        ),
        "totals": {
            "enumerated": len(cases),
            "reachable": reachable_count,
            "unreachable": len(cases) - reachable_count,
        },
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--phenotype-dir", type=Path, help="Directory of PharmCAT <GENE>.json phenotype tables.")
    parser.add_argument("--from-jar", type=Path, help="Extract phenotype tables from this PharmCAT JAR first.")
    parser.add_argument("-o", "--output", type=Path, default=CASE_MATRIX_PATH)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a table.")
    args = parser.parse_args(argv)

    phenotype_dir = args.phenotype_dir
    if args.from_jar:
        phenotype_dir = load_phenotypes_from_jar(
            args.from_jar, args.phenotype_dir or (REPO_ROOT / "build" / "phenotype")
        )

    if phenotype_dir is None:
        print(
            yellow(
                "No --phenotype-dir or --from-jar given; falling back to phenotypes\n"
                "observed in the checked-in fixtures. That set is INCOMPLETE and the\n"
                "matrix will say so per case."
            )
        )

    matrix = build_matrix(phenotype_dir)

    if args.json:
        print(json.dumps(matrix, indent=1))
    else:
        totals = matrix["totals"]
        print(rule("case matrix"))
        print(f"  {'drug':<14}{'gene':<9}{'phenotype':<10}{'reachable'}")
        print("  " + "-" * 64)
        for case in matrix["cases"]:
            mark = green("yes") if case["reachable"] else yellow("no ")
            print(
                f"  {case['drug']:<14}{case['gene']:<9}{case['phenotype']:<10}{mark}"
                + ("" if case["reachable"] else dim(f"  {case['reason'][:44]}…"))
            )
        print(rule())
        print(
            f"\n  enumerated {bold(str(totals['enumerated']))}   "
            f"reachable {green(str(totals['reachable']))}   "
            f"unreachable {yellow(str(totals['unreachable']))}"
        )

        by_reason: dict[str, int] = {}
        for case in matrix["cases"]:
            if not case["reachable"]:
                key = case["reason"].split("—")[0].strip()[:60]
                by_reason[key] = by_reason.get(key, 0) + 1
        if by_reason:
            print("\n  unreachable, by reason:")
            for reason, count in sorted(by_reason.items(), key=lambda kv: -kv[1]):
                print(f"    {count:>3}  {reason}")

    write_json_atomic(args.output, matrix)
    print(dim(f"\nwrote {args.output.relative_to(REPO_ROOT)}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
