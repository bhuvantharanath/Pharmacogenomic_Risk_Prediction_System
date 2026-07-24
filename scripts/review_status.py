#!/usr/bin/env python3
"""
Review coverage — provenance and author-read, reported separately.

    python scripts/review_status.py
    python scripts/review_status.py --json
    python scripts/review_status.py --quiet        # exit code only

THE TWO COLUMNS MEAN DIFFERENT THINGS, AND NEITHER IS CLINICAL APPROVAL

    provenance   machine-checked: every clinical-claim sentence traces to a
                 CPIC recommendation or a cited mechanism document. This is the
                 release gate, and scripts/verify_provenance.py sets it.

    author read  a human read the entry. Not qualified clinical review -- this
                 project has none -- but "nobody looked" and "a non-clinician
                 looked" are different states.

    clinical     NOT_OBTAINED, on every entry, permanently. Printed on every run
                 so it cannot quietly drop out of the picture.

Reporting these as one "reviewed" number, as this script used to, made the weak
signal look like the strong one.

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

    def review(entry: dict) -> dict:
        return entry.get("review") or {}

    verified = [e for e in entries if review(e).get("provenance_verified")]
    unverified = [e for e in entries if not review(e).get("provenance_verified")]
    read = [e for e in entries if review(e).get("read_by_author")]
    unread = [e for e in entries if not review(e).get("read_by_author")]
    flagged = [e for e in entries if e.get("author_concern")]
    fallback = [e for e in entries if e.get("fallback")]
    guard_failed = [e for e in entries if not (e.get("guard_report") or {}).get("passed", True)]
    # Should be every entry, forever. Checked rather than assumed: a stray
    # value here would be the project claiming an authority it does not have.
    claims_expert = [e for e in entries if review(e).get("clinical_expert_review")]

    per_drug = defaultdict(lambda: {"total": 0, "verified": 0, "read": 0, "fallback": 0})
    for entry in entries:
        row = per_drug[entry["drug"]]
        row["total"] += 1
        row["verified"] += bool(review(entry).get("provenance_verified"))
        row["read"] += bool(review(entry).get("read_by_author"))
        row["fallback"] += bool(entry.get("fallback"))

    # The gate is provenance. Author reading is reported, never required --
    # gating on it would imply the read carries an authority it does not.
    ok = bool(entries) and not unverified and not claims_expert

    if args.json:
        print(json.dumps({
            "total": len(entries),
            "provenance_verified": len(verified),
            "provenance_unverified": len(unverified),
            "read_by_author": len(read),
            "unread": len(unread),
            "author_concerns": len(flagged),
            "clinical_expert_review": "NOT_OBTAINED",
            "fallback": len(fallback),
            "guard_failed": len(guard_failed),
            "release_ready": ok,
        }, indent=1))
        return 0 if ok else 1

    if args.quiet:
        return 0 if ok else 1

    print(rule("review status"))
    print(f"  {'drug':<16}{'total':>6}{'provenance':>12}{'read':>7}{'fallback':>10}")
    print("  " + "-" * 53)
    for drug in sorted(per_drug):
        row = per_drug[drug]
        vmark = green if row["verified"] == row["total"] else red
        rmark = green if row["read"] == row["total"] else yellow
        print(f"  {drug:<16}{row['total']:>6}"
              f"{vmark(str(row['verified']).rjust(12))}"
              f"{rmark(str(row['read']).rjust(7))}{row['fallback']:>10}")
    print(rule())

    print(f"\n  total                {bold(str(len(entries)))}")
    print(f"  provenance verified  {green(str(len(verified))) if not unverified else red(str(len(verified)))}"
          f"  {dim('(machine-checked against CPIC + corpus)')}")
    print(f"  read by author       {green(str(len(read))) if not unread else yellow(str(len(read)))}"
          f"  {dim('(a human read it; NOT clinical approval)')}")
    if flagged:
        print(f"  {yellow('author concerns')}      {len(flagged)}")
    print(f"  clinical expert      {red('NOT_OBTAINED')}"
          f"  {dim('(no qualified reviewer on this project)')}")
    print(f"  fallback             {len(fallback)}")
    if guard_failed:
        print(f"  {red('guard failing')}        {len(guard_failed)}")

    if not entries:
        print(red("\nNo explanations at all — run pregenerate_explanations.py."))
        return 1
    if claims_expert:
        print(red(f"\nSTOP: {len(claims_expert)} entry(ies) claim a clinical expert review."))
        print(red("  No such reviewer exists on this project. Investigate before shipping."))
        return 1
    if unverified:
        print(red(f"\nNOT RELEASE READY: {len(unverified)} entry(ies) have unverified clinical content."))
        print(dim("  python scripts/verify_provenance.py -v      # see which sentences"))
        return 1

    print(green("\nRELEASE READY (provenance): every clinical claim traces to a cited source."))
    if unread:
        print(yellow(f"  {len(unread)} entry(ies) have not been read by anyone."))
        print(dim("  python scripts/author_read.py --author '<name>'"))
    if flagged:
        print(yellow(f"  {len(flagged)} entry(ies) carry an unresolved author concern:"))
        for entry in flagged:
            print(yellow(f"    · {entry['drug']}/{entry['phenotype']}: {entry['author_concern'][:60]}"))
    print(dim("\n  Provenance-verified means every clinical word came from a cited source."))
    print(dim("  It does NOT mean a clinician has agreed the text is correct."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
