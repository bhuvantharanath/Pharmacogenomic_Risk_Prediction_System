#!/usr/bin/env python3
"""
Derive each gene's DECISION-CRITICAL positions from PharmCAT's own data.

    python scripts/derive_decision_critical.py            # write the report
    python scripts/derive_decision_critical.py --json     # machine-readable

THE RULE, AND WHY IT IS MECHANICAL

    A position is decision-critical if it defines any named allele whose
    function assignment is not "Normal function".

Nothing here is selected by judgement and no variant identifier is typed from
memory. That constraint is the point: the previous justification for DPYD's 20%
threshold was a measured 0%-wrong rate over a cohort in which DPYD's
reduced-function variants are rare — a sweep that could not detect the failure
it was meant to exclude. Replacing one hand-reasoned answer with another would
repeat the error.

WHERE THE DATA COMES FROM (verified against the files, not from documentation)

Both are shipped inside `pharmcat-3.4.0-all.jar`:

  definition/alleles/<GENE>_translation.json
      `variants[]`      -> chromosome, position, rsid, chromosomeHgvsName
      `namedAlleles[]`  -> name, alleles[] parallel to variants[]; a non-null
                           entry means this allele CONSTRAINS that position

  phenotype/<GENE>.json
      `namedAlleles[]`  -> name, activityValue, functionValue

Joined on the allele `name`. Observed `functionValue` values for DPYD are
exactly {Normal function, Decreased function, No function}; anything that is not
"Normal function" counts.

WHAT THIS IS NOT

It is not a claim about which variants matter clinically — that is CPIC's
judgement, already encoded in `functionValue`. This only reads it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JAR = REPO / "test-data/reference/tools/pharmcat-3.4.0-all.jar"

#: The genes this project reports on.
GENES = ("CYP2C19", "CYP2C9", "CYP2D6", "DPYD", "NUDT15", "SLCO1B1", "TPMT")

DEF_PREFIX = "org/pharmgkb/pharmcat/definition/alleles/"
PHENO_PREFIX = "org/pharmgkb/pharmcat/phenotype/"

#: The one function assignment that is NOT decision-critical. Compared
#: case-insensitively; everything else (Decreased, No function, Uncertain,
#: Possible decreased, Unknown) counts as critical.
NORMAL = "normal function"


def load(gene: str) -> tuple[dict | None, dict | None]:
    """(translation, phenotype) straight out of the jar."""
    if not JAR.exists():
        return None, None
    with zipfile.ZipFile(JAR) as z:
        names = set(z.namelist())
        tpath = f"{DEF_PREFIX}{gene}_translation.json"
        ppath = f"{PHENO_PREFIX}{gene}.json"
        translation = json.loads(z.read(tpath)) if tpath in names else None
        phenotype = json.loads(z.read(ppath)) if ppath in names else None
    return translation, phenotype


def derive(gene: str) -> dict:
    translation, phenotype = load(gene)
    if translation is None:
        return {"gene": gene, "error": "no translation file in the jar"}
    if phenotype is None:
        # Reported, never guessed around. A gene with no function assignments
        # cannot have decision-critical positions derived, and saying so is the
        # correct outcome.
        return {"gene": gene, "error": "no phenotype file — no function "
                                       "assignments available",
                "variants": len(translation.get("variants", []))}

    functions = {
        a["name"]: (a.get("functionValue") or "").strip()
        for a in phenotype.get("namedAlleles", [])
    }
    variants = translation.get("variants", [])
    positions = [
        {
            "chromosome": v.get("chromosome"),
            "position": int(v["position"]),
            "rsid": v.get("rsid"),
            "hgvs": v.get("chromosomeHgvsName"),
        }
        for v in variants
    ]

    critical: dict[int, dict] = {}
    unassigned: list[str] = []

    for allele in translation.get("namedAlleles", []):
        name = allele.get("name")
        if allele.get("reference"):
            continue
        function = functions.get(name)
        if function is None:
            unassigned.append(name)
            continue
        if function.lower() == NORMAL:
            continue

        constrained = [i for i, value in enumerate(allele.get("alleles") or [])
                       if value is not None]
        for index in constrained:
            if index >= len(positions):
                continue
            entry = critical.setdefault(
                positions[index]["position"],
                {**positions[index], "alleles": []})
            entry["alleles"].append({"name": name, "function": function})

    return {
        "gene": gene,
        "total_positions": len(positions),
        "critical_positions": sorted(critical.values(), key=lambda e: e["position"]),
        "critical_count": len(critical),
        "named_alleles": len(translation.get("namedAlleles", [])),
        "alleles_without_function": sorted(unassigned),
        "function_values_seen": sorted({f for f in functions.values() if f}),
        "source_translation": f"{DEF_PREFIX}{gene}_translation.json",
        "source_phenotype": f"{PHENO_PREFIX}{gene}.json",
        "pharmcat_version": translation.get("version"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit-requirements", action="store_true",
                    help="write the derived positions into "
                         "position_requirements.json")
    args = ap.parse_args()

    if args.emit_requirements:
        return emit_requirements()

    results = {gene: derive(gene) for gene in GENES}

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0

    out = [
        "# Decision-critical positions, derived from PharmCAT's own data",
        "",
        "Generated by `scripts/derive_decision_critical.py`. Do not edit by hand.",
        "",
        "## The rule",
        "",
        "> A position is **decision-critical** if it defines any named allele whose",
        "> function assignment is not `Normal function`.",
        "",
        "No variant was selected by judgement and none was typed from memory. The",
        "function assignments are CPIC's, read out of the files PharmCAT ships;",
        "this script only joins them to the positions that define each allele.",
        "",
        "## Source fields (verified against the files, not from documentation)",
        "",
        "| file | field | carries |",
        "| --- | --- | --- |",
        "| `definition/alleles/<GENE>_translation.json` | `variants[]` | chromosome, position, rsid, HGVS |",
        "| | `namedAlleles[].alleles[]` | parallel to `variants[]`; non-null = this allele constrains that position |",
        "| `phenotype/<GENE>.json` | `namedAlleles[].functionValue` | **the function assignment** |",
        "",
        "Joined on the allele `name`.",
        "",
        "## Counts",
        "",
        "| gene | positions | decision-critical | share | function values seen |",
        "| --- | ---: | ---: | ---: | --- |",
    ]

    for gene in GENES:
        r = results[gene]
        if "error" in r:
            out.append(f"| {gene} | — | — | — | **{r['error']}** |")
            continue
        share = (r["critical_count"] / r["total_positions"] * 100
                 if r["total_positions"] else 0)
        out.append(
            f"| {gene} | {r['total_positions']} | **{r['critical_count']}** | "
            f"{share:.1f}% | {', '.join(r['function_values_seen'])} |")

    out.append("")
    for gene in GENES:
        r = results[gene]
        out += [f"## {gene}", ""]
        if "error" in r:
            out += [f"**{r['error']}**", ""]
            continue
        out += [
            f"Source: `{r['source_translation']}` + `{r['source_phenotype']}` "
            f"(data version `{r['pharmcat_version']}`).",
            "",
            f"{r['critical_count']} of {r['total_positions']} positions define at "
            f"least one non-normal allele.",
            "",
        ]
        if r["alleles_without_function"]:
            out += [
                f"**{len(r['alleles_without_function'])} named allele(s) have no "
                f"function assignment** and were skipped rather than assumed "
                f"normal: {', '.join('`' + a + '`' for a in r['alleles_without_function'][:12])}"
                + (" …" if len(r["alleles_without_function"]) > 12 else ""),
                "",
            ]
        out += ["| position | rsid | HGVS | defines |", "| ---: | --- | --- | --- |"]
        for entry in r["critical_positions"]:
            alleles = ", ".join(
                f"`{a['name']}` ({a['function']})" for a in entry["alleles"][:4])
            if len(entry["alleles"]) > 4:
                alleles += f" … +{len(entry['alleles']) - 4}"
            out.append(
                f"| {entry['chromosome']}:{entry['position']} | "
                f"{entry['rsid'] or '—'} | {entry['hgvs'] or '—'} | {alleles} |")
        out.append("")

    (REPO / "reports" / "decision_critical_positions.md").write_text(
        "\n".join(out) + "\n")

    for gene in GENES:
        r = results[gene]
        if "error" in r:
            print(f"  {gene:8s} ERROR: {r['error']}")
        else:
            print(f"  {gene:8s} {r['critical_count']:4d} / {r['total_positions']:4d} "
                  f"decision-critical")
    print("\nwrote reports/decision_critical_positions.md")
    return 0



def emit_requirements() -> int:
    """
    Write the derived positions into `position_requirements.json`.

    Generated, never hand-typed — the same discipline as the position list
    itself. `decision_critical_enforced` is set per gene and is DELIBERATELY
    true only for DPYD: the other six were measured for the same exposure and
    reported, and turning them on is a separate decision.

    No threshold value is touched. This adds a requirement beside the
    percentage; it does not move a bar.
    """
    path = REPO / "backend/app/data/position_requirements.json"
    data = json.loads(path.read_text())
    derived = {gene: derive(gene) for gene in GENES}

    for gene, spec in data["genes"].items():
        r = derived.get(gene, {})
        if "error" in r or not r:
            continue
        spec["decision_critical_positions"] = [
            [e["chromosome"], e["position"]] for e in r["critical_positions"]
        ]
        spec["decision_critical_count"] = r["critical_count"]
        # Enforced for every gene whose percentage threshold is below 100%.
        #
        # NOT because their exposure matches DPYD's — it does not; DPYD can omit
        # all 28 of its critical positions, TPMT caps at 9 and NUDT15 at 4. The
        # reason is that all three sub-100% thresholds rest on the SAME
        # synthetic sweep, and that sweep is now known to be incapable of
        # detecting the failure it was meant to exclude (see Evidence 10 in
        # reports/provenance_finding.md). The justification is common to all
        # three, so its collapse is too.
        #
        # The four 100% genes need no flag: requiring every position already
        # implies requiring every critical one.
        spec["decision_critical_enforced"] = (
            spec.get("min_coverage_percent", 100) < 100)

    data["decision_critical_provenance"] = {
        "rule": "a position is decision-critical if it defines any named allele "
                "whose functionValue is not 'Normal function'",
        "derived_by": "scripts/derive_decision_critical.py",
        "translation_source": "definition/alleles/<GENE>_translation.json "
                              "(variants[], namedAlleles[].alleles[])",
        "function_source": "phenotype/<GENE>.json (namedAlleles[].functionValue)",
        "jar": JAR.name,
        "note": "Generated. Re-run the script rather than editing by hand.",
    }
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"updated {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
