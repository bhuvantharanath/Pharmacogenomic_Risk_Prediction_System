#!/usr/bin/env python3
"""
Adjudication coverage — the release gate.

    python scripts/adjudication_status.py
    python scripts/adjudication_status.py --json
    python scripts/adjudication_status.py --quiet     # exit code only

WHY THIS REPLACED THE PROVENANCE GATE

`verify_provenance.py` used to be the gate, and it was the wrong instrument for
the job. `reports/provenance_diagnosis.md` shows why: it scored lexical overlap,
so it failed faithful paraphrase and passed a sentence that contradicted its
source. A gate that can be satisfied by copying and defeated by rewording is not
measuring what matters.

The automated layer is now a **filter**: it narrows twenty entries to the
sentences a person should actually look at. This script is the gate, and it
checks something a machine genuinely can determine — whether a human has made a
decision about every shipped claim, and whether any decision was "reject".

EXIT CODES
    0  every claim-bearing sentence is adjudicated and none was rejected
    1  something is unadjudicated, or a rejected sentence is still in the store

NOT CLINICAL APPROVAL
    Adjudication is the project author checking a sentence against its source.
    There is no qualified clinical reviewer on this project and none is expected.
    This script prints that on every run so the number it reports cannot be
    quoted as something stronger than it is.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

from _common import (
    EXPLANATIONS_PATH,
    REPO_ROOT,
    bold,
    dim,
    green,
    load_json,
    red,
    rule,
    yellow,
)

SCRIPTS = REPO_ROOT / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input", type=Path, default=EXPLANATIONS_PATH)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true", help="Exit code only.")
    args = parser.parse_args(argv)

    vp = _load("verify_provenance")
    adj = _load("adjudicate")

    store = load_json(args.input)
    entries = store.get("explanations", [])
    if not entries:
        print(red("No explanations at all."), file=sys.stderr)
        return 1

    # The gate covers EVERY claim-bearing sentence, not only the flagged ones:
    # the filter is triage, so "the filter sourced it" is not by itself a
    # decision. Unflagged sentences may be bulk-accepted, but the record must
    # exist and name who made it.
    flagged = adj.collect_flagged(vp, entries, include_all=True)
    needs_individual = {i["key"] for i in adj.collect_flagged(vp, entries, include_all=False)}
    by_case = {f"{e['drug']}:{e['phenotype']}": e for e in entries}

    outstanding: list[dict] = []
    rejected: list[dict] = []
    decided = 0
    per_drug: dict[str, dict[str, int]] = defaultdict(lambda: {"flagged": 0, "decided": 0})

    for item in flagged:
        entry = by_case[item["case"]]
        decisions = entry.get("provenance_adjudications") or {}
        row = per_drug[item["drug"]]
        row["flagged"] += 1
        record = decisions.get(item["key"])
        if record is None:
            outstanding.append(item)
            continue
        decided += 1
        row["decided"] += 1
        if record.get("decision") == "rejected":
            rejected.append({**item, "rationale": record.get("rationale", "")})

    # A rejected sentence that is still present is a release blocker: the entry
    # must be regenerated or edited, not shipped with a known-bad claim.
    ok = not outstanding and not rejected

    if args.json:
        print(json.dumps({
            "entries": len(entries),
            "flagged_sentences": len(flagged),
            "adjudicated": decided,
            "outstanding": len(outstanding),
            "rejected": len(rejected),
            "clinical_expert_review": "NOT_OBTAINED",
            "release_ready": ok,
        }, indent=1))
        return 0 if ok else 1

    if args.quiet:
        return 0 if ok else 1

    print(rule("adjudication status"))
    if per_drug:
        print(f"  {'drug':<16}{'flagged':>9}{'decided':>9}")
        print("  " + "-" * 34)
        for drug in sorted(per_drug):
            row = per_drug[drug]
            mark = green if row["decided"] == row["flagged"] else yellow
            print(f"  {drug:<16}{row['flagged']:>9}{mark(str(row['decided']).rjust(9))}")
    else:
        print(dim("  no sentences flagged — the automated filter sourced every claim"))
    print(rule())

    print(f"\n  entries              {bold(str(len(entries)))}")
    print(f"  claim sentences      {len(flagged)}   {dim(f'({len(needs_individual)} flagged by the filter)')}")
    print(f"  adjudicated          {green(str(decided)) if not outstanding else yellow(str(decided))}")
    print(f"  outstanding          {red(str(len(outstanding))) if outstanding else green('0')}")
    if rejected:
        print(f"  {red('rejected, still present')}  {len(rejected)}")
    print(f"  clinical expert      {red('NOT_OBTAINED')}   {dim('(no qualified reviewer on this project)')}")

    if rejected:
        print(red(f"\nNOT RELEASE READY: {len(rejected)} rejected sentence(s) are still in the store."))
        for item in rejected[:6]:
            print(red(f"  · {item['case']} / {item['field']}: {item['rationale'][:60]}"))
        print(dim("  Regenerate or edit those entries, then re-adjudicate."))
        return 1

    if outstanding:
        print(yellow(f"\nNOT RELEASE READY: {len(outstanding)} flagged sentence(s) have no decision."))
        for item in outstanding[:6]:
            print(yellow(f"  · {item['case']} / {item['field']}: {item['text'][:58]}"))
        if len(outstanding) > 6:
            print(dim(f"    … and {len(outstanding) - 6} more"))
        print(dim("\n  python scripts/adjudicate.py --adjudicator '<your name>'"))
        return 1

    print(green("\nRELEASE READY: every flagged claim has been adjudicated, none rejected."))
    print(dim("  Adjudicated means a person compared the sentence to its source."))
    print(dim("  It does NOT mean a clinician has agreed the sentence is correct."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
