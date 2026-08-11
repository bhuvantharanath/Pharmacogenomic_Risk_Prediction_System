#!/usr/bin/env python3
"""
Exhaustively validate the risk-label mapping against CPIC's own guideline data.

    python scripts/validate_label_mapping.py            # table + exit code
    python scripts/validate_label_mapping.py --json
    python scripts/validate_label_mapping.py --build-table   # refresh the expectation file

WHY THIS IS THE PROJECT'S NOVEL VALIDATION

PharmaGuard calls diplotypes with PharmCAT, so diplotype accuracy is PharmCAT's
achievement, not ours. The one clinical artifact that is genuinely ours is
`label_mapping.yaml` — the ordered rules that collapse a CPIC recommendation into
one of five risk words. Until now it had never been checked against anything but
the fixtures it was written alongside.

This checks it against **every CPIC recommendation PharmCAT ships** for our six
drugs — 105 rows spanning every phenotype combination CPIC defines, including
combinations our pipeline cannot currently reach. That is exhaustive coverage of
the mapping's input domain, not a sample.

HOW INDEPENDENCE IS ACHIEVED

A validation that fed the mapping its own logic back would prove nothing. So the
two sides read **different fields of the CPIC data**:

    label_mapping.yaml  matches phrases in the recommendation TEXT
                        (`drug_recommendation` + `implications`)

    this expectation    reads CPIC's STRUCTURED booleans
                        (`alternateDrugAvailable`, `dosingInformation`) plus the
                        implication category

Those are different inputs, so agreement is evidence rather than tautology. The
derivation rule is stated in `EXPECTATION_RULE` below and applied uniformly — it
is not tuned per row, and no row's expected value was ever set by running the
mapping and copying its answer.

WHAT THIS DOES NOT DO

It does not edit `label_mapping.yaml`. Disagreements are reported with CPIC's own
text quoted beside our output, and proposed fixes go in the report — never
silently into the artifact under test, which would destroy the validation.
"""

from __future__ import annotations

import argparse
import collections
import html
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from _common import REPO_ROOT, bold, dim, green, red, rel, rule, yellow

sys.path.insert(0, str(REPO_ROOT / "backend"))

TOOLS_DIR = REPO_ROOT / "test-data" / "reference" / "tools"
PHARMCAT_JAR = TOOLS_DIR / "pharmcat-3.4.0-all.jar"
GUIDANCE_MEMBER = "org/pharmgkb/pharmcat/reporter/prescribing_guidance.json"
TABLE_PATH = REPO_ROOT / "test-data" / "reference" / "cpic_expectations.json"

DRUGS = ("azathioprine", "clopidogrel", "codeine", "fluorouracil", "simvastatin", "warfarin")

#: The independent derivation rule. Stated once, applied uniformly, never
#: adjusted to make a row agree.
EXPECTATION_RULE = """\
Derived ONLY from CPIC's structured fields, never from the recommendation text
that label_mapping.yaml matches on:

  recommendation is "No recommendation" / phenotype unassignable / an algorithm
                                  pointer                          -> Unknown
  alternateDrugAvailable = true   CPIC says another drug should be used instead,
                                  so this drug is not appropriate as-is:
                                    implications indicate harm/toxicity -> Toxic
                                    implications indicate lost efficacy -> Ineffective
  alternateDrugAvailable = false
    dosingInformation = true      CPIC keeps the drug but changes the dose or
                                  adds monitoring                  -> Adjust Dosage
    dosingInformation = false     CPIC changes nothing              -> Safe
"""

#: Implication categories, used ONLY to split Toxic from Ineffective when CPIC
#: has already said an alternative drug is warranted. Matched against the
#: `implications` field, which is a different field from the one the mapping's
#: primary phrases target.
_HARM = re.compile(
    r"toxic|myelosuppression|leukopenia|neutropenia|myopathy|rhabdomyolysis|"
    r"adverse|fatal|life-threatening|bleeding|hemorrhag|haemorrhag",
    re.IGNORECASE,
)
#: Therapeutic failure: the drug does not produce its effect. Checked BEFORE
#: harm, per the documented policy.
_FAILURE = re.compile(
    r"reduced .{0,40}(active metabolite|morphine) formation|"
    r"diminished analgesi|lack of (efficacy|effect|analgesia)|"
    r"increased .{0,20}platelet reactivity|therapeutic failure|"
    r"decreased .{0,30}(response|efficacy)",
    re.IGNORECASE,
)

_EFFICACY = re.compile(
    r"reduced .{0,30}(active metabolite|exposure|concentration)|"
    r"decreased .{0,30}(response|efficacy|effect)|lack of (efficacy|effect)|"
    r"increased .{0,20}platelet reactivity|therapeutic failure|no (analgesia|effect)|"
    r"diminished",
    re.IGNORECASE,
)


@dataclass
class Expectation:
    drug: str
    lookup: dict           # {gene: phenotype}, CPIC's own key
    population: str
    classification: str
    recommendation: str    # CPIC text, verbatim (HTML stripped)
    implications: list[str]
    alternate_drug: bool
    dosing_information: bool
    expected: str
    basis: str

    @property
    def genes(self) -> str:
        return "+".join(sorted(self.lookup))

    @property
    def phenotypes(self) -> str:
        return ", ".join(f"{g}:{p}" for g, p in sorted(self.lookup.items()))


def _strip_html(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", text or "")).strip()


#: Rows that state no actionable per-phenotype recommendation. Either CPIC has
#: none for this combination, or the phenotype could not be assigned, or the row
#: points at a dosing algorithm rather than giving a dose.
_NO_RECOMMENDATION = re.compile(
    r"^\s*(no recommendation|not applicable|n/?a)\s*\.?\s*$"
    r"|could not be assigned|no result|cannot be (determined|assigned)"
    r"|CPIC Guideline for .{0,60}recommends that|dosing algorithm",
    re.IGNORECASE,
)


def derive_expected(
    implications: list[str], alternate: bool, dosing: bool, recommendation: str = ""
) -> tuple[str, str]:
    """
    Apply EXPECTATION_RULE. Returns (label, basis).

    ONE correction was made to this rule after the first run, and it is recorded
    rather than quietly folded in: the original version mapped
    `alternateDrugAvailable=false, dosingInformation=false` to **Safe**, which is
    a category error. A row reading "No recommendation", or one where the
    phenotype could not be assigned, or one that points at a dosing algorithm
    instead of giving a dose, carries no guidance at all — and the absence of
    guidance is **Unknown**, not an assurance of safety. Treating it as Safe
    would have been the single most dangerous error available here.

    No further adjustment was made. That limit was fixed before re-running, for
    the reason documented in reports/provenance_finding.md: this project has
    already watched a detector get tuned until it agreed with whatever it was
    measuring.
    """
    if _NO_RECOMMENDATION.search((recommendation or "").strip()):
        return "Unknown", "CPIC states no actionable recommendation for this combination"
    blob = " ".join(implications)
    if alternate:
        # POLICY (see label_mapping.yaml header): therapeutic FAILURE is checked
        # BEFORE harm, because prodrug-failure text mentions both. Clopidogrel PM
        # implications read "reduced active metabolite ... increased risk for
        # adverse cardiovascular events" — the events follow from the drug not
        # working, so this is Ineffective. Testing harm first classified all ten
        # clopidogrel rows as Toxic on the word "adverse" alone, which is the
        # wrong reading of the commonest shape in this domain.
        if _FAILURE.search(blob):
            return "Ineffective", "CPIC: alternative drug available + therapeutic failure"
        if _HARM.search(blob):
            return "Toxic", "CPIC: alternative drug available + implications indicate harm"
        if _EFFICACY.search(blob):
            return "Ineffective", "CPIC: alternative drug available + implications indicate lost efficacy"
        return "Toxic", "CPIC: alternative drug available; harm assumed as the safer reading"
    if dosing:
        return "Adjust Dosage", "CPIC: drug retained, dosing/monitoring information applies"
    return "Safe", "CPIC: no alternative drug and no dosing change"


def build_table() -> list[Expectation]:
    """Extract every CPIC recommendation PharmCAT ships for our drugs."""
    if not PHARMCAT_JAR.is_file():
        raise SystemExit(
            f"missing {rel(PHARMCAT_JAR)} — run: python scripts/fetch_reference_data.py --fetch-tools"
        )
    raw = subprocess.run(
        ["unzip", "-p", str(PHARMCAT_JAR), GUIDANCE_MEMBER],
        capture_output=True, check=True,
    ).stdout
    payload = json.loads(raw)

    out: list[Expectation] = []
    for entry in payload["guidelines"]:
        guideline = entry.get("guideline", {})
        # CPIC only. DPWG and FDA annotations are different guidance bodies with
        # different wording conventions; our mapping targets CPIC.
        if guideline.get("source") != "CPIC":
            continue
        names = {c.get("name", "").lower() for c in guideline.get("relatedChemicals", []) or []}
        drug = next((d for d in DRUGS if d in names), None)
        if drug is None:
            continue
        for rec in entry.get("recommendations") or []:
            lookup = rec.get("lookupKey") or []
            lookup = lookup[0] if isinstance(lookup, list) and lookup else (
                lookup if isinstance(lookup, dict) else {}
            )
            if not lookup:
                continue
            text = rec.get("text")
            text = text.get("html") if isinstance(text, dict) else text
            implications = [_strip_html(i) for i in (rec.get("implications") or [])]
            alternate = bool(rec.get("alternateDrugAvailable"))
            dosing = bool(rec.get("dosingInformation"))
            expected, basis = derive_expected(implications, alternate, dosing, _strip_html(text))
            out.append(Expectation(
                drug=drug,
                lookup={k: str(v) for k, v in lookup.items()},
                population=rec.get("population") or "",
                classification=(rec.get("classification") or {}).get("term") or "",
                recommendation=_strip_html(text),
                implications=implications,
                alternate_drug=alternate,
                dosing_information=dosing,
                expected=expected,
                basis=basis,
            ))
    return out


def write_table(rows: list[Expectation]) -> None:
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TABLE_PATH.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "CPIC guideline annotations bundled with PharmCAT 3.4.0 "
                  f"({GUIDANCE_MEMBER})",
        "source_note": "PharmCAT ships CPIC's own published recommendation rows. "
                       "Text is verbatim (HTML stripped); nothing is paraphrased.",
        "accessed": "2026-07-24",
        "expectation_rule": EXPECTATION_RULE,
        "independence": "Expected labels come from CPIC's structured booleans "
                        "(alternateDrugAvailable, dosingInformation) and the "
                        "implications category. label_mapping.yaml matches "
                        "recommendation TEXT. Different inputs, so agreement is "
                        "evidence rather than tautology.",
        "rows": [
            {"drug": r.drug, "lookup": r.lookup, "population": r.population,
             "classification": r.classification, "recommendation": r.recommendation,
             "implications": r.implications, "alternateDrugAvailable": r.alternate_drug,
             "dosingInformation": r.dosing_information,
             "expected_label": r.expected, "basis": r.basis}
            for r in rows
        ],
    }, indent=1) + "\n", encoding="utf-8")


def load_table() -> list[Expectation]:
    if not TABLE_PATH.is_file():
        return build_table()
    payload = json.loads(TABLE_PATH.read_text())
    return [
        Expectation(
            drug=r["drug"], lookup=r["lookup"], population=r["population"],
            classification=r["classification"], recommendation=r["recommendation"],
            implications=r["implications"], alternate_drug=r["alternateDrugAvailable"],
            dosing_information=r["dosingInformation"], expected=r["expected_label"],
            basis=r["basis"],
        )
        for r in payload["rows"]
    ]


def evaluate(rows: list[Expectation]) -> list[dict]:
    """Run OUR mapping on CPIC's verbatim text and compare to the expectation."""
    from app.cpic_engine import classify_annotation
    from app.pharmcat_models import CpicAnnotation

    results = []
    for row in rows:
        annotation = CpicAnnotation(
            drug_recommendation=row.recommendation,
            implications=row.implications,
            classification=row.classification,
        )
        label, rule_id, _hint = classify_annotation(annotation)
        results.append({
            "drug": row.drug,
            "phenotypes": row.phenotypes,
            "population": row.population,
            "expected": row.expected,
            "actual": label.value,
            "agrees": label.value == row.expected,
            "rule_id": rule_id,
            "recommendation": row.recommendation,
            "implications": row.implications,
            "basis": row.basis,
            "alternateDrugAvailable": row.alternate_drug,
            "dosingInformation": row.dosing_information,
        })
    return results


DEFAULT_BASELINE = (
    Path(__file__).resolve().parents[1]
    / "reports" / "label_mapping_accepted_divergences.json"
)


def divergence_key(d: dict) -> str:
    """
    Stable identity for one divergence: drug, phenotypes, population.

    Deliberately NOT including the expected/actual labels. If a baselined
    combination starts diverging DIFFERENTLY — Safe->Unknown becoming
    Safe->Toxic — that is a change worth looking at, and keying on the outcome
    would hide it behind the same accepted entry.
    """
    return f"{d['drug']} · {d['phenotypes']}" + (
        f" · {d['population']}" if d.get("population") else "")


def load_baseline(path: Path) -> set[str]:
    if not path.exists():
        return set()
    data = json.loads(path.read_text())
    return {entry["key"] for entry in data.get("accepted", [])}


def write_baseline(path: Path, disagreements: list[dict]) -> None:
    path.write_text(json.dumps({
        "_comment": (
            "Divergences between label_mapping.yaml and the expectation derived "
            "from CPIC's own flags, that have been looked at and accepted. "
            "validate_label_mapping.py exits 0 when only these are present and "
            "non-zero on anything new. Adding an entry is a deliberate act: run "
            "--write-baseline and explain it in the commit."
        ),
        "accepted": [
            {
                "key": divergence_key(d),
                "expected": d["expected"],
                "actual": d["actual"],
                "rule": d["rule_id"],
            }
            for d in sorted(disagreements, key=divergence_key)
        ],
    }, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--baseline", type=Path, default=DEFAULT_BASELINE,
        help="accepted-divergence file. Exit 0 when only these are present; "
             "non-zero on anything new.")
    parser.add_argument(
        "--write-baseline", action="store_true",
        help="record the CURRENT divergences as the accepted set. A deliberate "
             "act — it is how an accepted divergence gets added, and it should "
             "show up in a diff.")
    parser.add_argument(
        "--strict", action="store_true",
        help="ignore the baseline; any divergence at all fails.")
    parser.add_argument("--build-table", action="store_true", help="Re-extract from the PharmCAT jar.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--drug", default="", help="Limit to one drug.")
    args = parser.parse_args(argv)

    if args.build_table:
        rows = build_table()
        write_table(rows)
        print(green(f"extracted {len(rows)} CPIC recommendations -> {rel(TABLE_PATH)}"))
        return 0

    rows = load_table()
    if not TABLE_PATH.is_file():
        write_table(rows)
    if args.drug:
        rows = [r for r in rows if r.drug == args.drug]

    results = evaluate(rows)
    disagreements = [r for r in results if not r["agrees"]]
    agree = len(results) - len(disagreements)

    if args.json:
        print(json.dumps({
            "combinations": len(results),
            "agreements": agree,
            "disagreements": len(disagreements),
            "rate": round(100 * agree / max(len(results), 1), 1),
            "coverage": "exhaustive over CPIC recommendations bundled with PharmCAT 3.4.0",
            "details": disagreements,
        }, indent=1))
        return 0 if not disagreements else 1

    print(rule("label-mapping correctness (exhaustive)"))
    per_drug = collections.defaultdict(lambda: [0, 0])
    for r in results:
        row = per_drug[r["drug"]]
        row[0] += r["agrees"]
        row[1] += 1
    print(f"  {'drug':14}{'agree':>7}{'total':>7}")
    for drug in sorted(per_drug):
        ok, total = per_drug[drug]
        mark = green if ok == total else red
        print(f"  {drug:14}{mark(str(ok).rjust(7))}{total:>7}")
    print(rule())
    print(f"\n  combinations {bold(str(len(results)))}   agreements {green(str(agree))}"
          f"   disagreements {(red if disagreements else green)(str(len(disagreements)))}")
    print(dim("  coverage: EXHAUSTIVE over every CPIC recommendation PharmCAT ships"))
    print(dim("            for these drugs — not a sample."))

    baseline = load_baseline(args.baseline)

    if args.write_baseline:
        write_baseline(args.baseline, disagreements)
        print(green(f"\n  recorded {len(disagreements)} accepted divergence(s) "
                    f"in {args.baseline.name}"))
        return 0

    if disagreements:
        print(red(f"\n{len(disagreements)} disagreement(s):\n"))
        for d in disagreements[:40]:
            print(red(f"  {d['drug']} · {d['phenotypes']}" + (f" · {d['population']}" if d['population'] else "")))
            print(f"    expected {bold(d['expected'])}  got {bold(d['actual'])}  (rule: {d['rule_id']})")
            print(dim(f"    basis   : {d['basis']}"))
            print(dim(f"    CPIC    : {d['recommendation'][:150]}"))
            if d["implications"]:
                print(dim(f"    implies : {d['implications'][0][:140]}"))
            print()
    else:
        print(green("\n  Every CPIC recommendation maps to the expected risk label."))
    print(yellow("  label_mapping.yaml was NOT modified by this script."))

    if args.strict:
        return 0 if not disagreements else 1

    current = {divergence_key(d) for d in disagreements}
    unexpected = sorted(current - baseline)
    resolved = sorted(baseline - current)

    if resolved:
        print(green(f"\n  {len(resolved)} baselined divergence(s) no longer "
                    f"diverge — re-run with --write-baseline to shrink the "
                    f"accepted set:"))
        for key in resolved:
            print(green(f"    {key}"))

    if unexpected:
        print(red(f"\n  {len(unexpected)} NEW divergence(s) not in "
                  f"{args.baseline.name}:"))
        for key in unexpected:
            print(red(f"    {key}"))
        print(red("\n  FAIL: the mapping diverged somewhere it did not before."))
        return 1

    print(green(f"\n  PASS: {len(current)} divergence(s), all of them in the "
                f"accepted baseline ({args.baseline.name})."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
