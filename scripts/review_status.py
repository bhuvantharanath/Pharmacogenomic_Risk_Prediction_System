#!/usr/bin/env python3
"""
Review coverage table. Exits non-zero if anything is unreviewed.

    python scripts/review_status.py          # human table
    python scripts/review_status.py --json
    python scripts/review_status.py --quiet  # exit code only

Designed as a release gate: a non-zero exit means "clinical content has not
been signed off", which is exactly the condition that should block a demo or a
submission. Wire it into CI with `python scripts/review_status.py || exit 1`.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from _common import (
    EXPLANATIONS_PATH,
    bold,
    dim,
    green,
    load_json,
    red,
    rule,
    yellow,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input", type=Path, default=EXPLANATIONS_PATH)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true", help="Exit code only.")
    args = parser.parse_args(argv)

    store = load_json(args.input)
    entries = store.get("explanations", [])

    reviewed = [e for e in entries if e.get("reviewed_by")]
    approved = [e for e in reviewed if e.get("review_decision") != "rejected"]
    rejected = [e for e in reviewed if e.get("review_decision") == "rejected"]
    unreviewed = [e for e in entries if not e.get("reviewed_by")]
    fallback = [e for e in entries if e.get("fallback")]
    guard_failed = [e for e in entries if not (e.get("guard_report") or {}).get("passed", True)]

    per_drug = defaultdict(lambda: {"total": 0, "reviewed": 0, "fallback": 0})
    for entry in entries:
        row = per_drug[entry["drug"]]
        row["total"] += 1
        if entry.get("reviewed_by"):
            row["reviewed"] += 1
        if entry.get("fallback"):
            row["fallback"] += 1

    ok = bool(entries) and not unreviewed and not rejected

    if args.json:
        print(json.dumps({
            "total": len(entries), "reviewed": len(reviewed), "approved": len(approved),
            "rejected": len(rejected), "unreviewed": len(unreviewed),
            "fallback": len(fallback), "guard_failed": len(guard_failed),
            "release_ready": ok,
        }, indent=1))
        return 0 if ok else 1

    if args.quiet:
        return 0 if ok else 1

    print(rule("review status"))
    print(f"  {'drug':<16}{'total':>6}{'reviewed':>10}{'fallback':>10}")
    print("  " + "-" * 44)
    for drug in sorted(per_drug):
        row = per_drug[drug]
        mark = green if row["reviewed"] == row["total"] else yellow
        print(f"  {drug:<16}{row['total']:>6}{mark(str(row['reviewed']).rjust(10))}{row['fallback']:>10}")
    print(rule())

    print(f"\n  total       {bold(str(len(entries)))}")
    print(f"  reviewed    {green(str(len(reviewed)))}"
          + (f"  ({len(approved)} approved, {len(rejected)} rejected)" if reviewed else ""))
    print(f"  unreviewed  {yellow(str(len(unreviewed))) if unreviewed else green('0')}")
    print(f"  fallback    {len(fallback)}")
    if guard_failed:
        print(f"  {red('guard failing')} {len(guard_failed)}")

    if not entries:
        print(red("\nNo explanations at all — run pregenerate_explanations.py."))
        return 1
    if unreviewed:
        print(yellow(f"\nNOT RELEASE READY: {len(unreviewed)} entry(ies) unreviewed."))
        print(dim("  python scripts/review.py --reviewer '<name>'"))
        print(dim("  or share reports/explanations_for_review.md for offline sign-off"))
        return 1
    if rejected:
        print(red(f"\nNOT RELEASE READY: {len(rejected)} entry(ies) were REJECTED."))
        for entry in rejected:
            print(red(f"  · {entry['drug']}/{entry['phenotype']}: {entry.get('review_note', '')[:60]}"))
        return 1

    print(green("\nRELEASE READY: every entry reviewed and approved."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
