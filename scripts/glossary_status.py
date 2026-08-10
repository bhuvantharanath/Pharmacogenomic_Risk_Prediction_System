#!/usr/bin/env python3
"""
The gate: does every domain term a user meets have an answer?

    python scripts/glossary_status.py           # report; exit 0
    python scripts/glossary_status.py --gate    # fail the build on gaps

WHY IT IS NOT BLOCKING BY DEFAULT

The extractor's false-positive rate on ordinary English was measured at
**41.5%** — above the 25% recorded in `glossary_precommitment.md` before it was
run. The pre-commitment named the branch in advance:

    FP < 25%  -> gate
    FP >= 25% -> report the rate, do NOT gate, and say so

so it reports. This is the same branch the mechanism vocabulary check took at
30%, and for the same reason: a threshold moved after seeing the number is not a
threshold. The rule was not loosened to obtain a green build, and the check was
not narrowed to make the number smaller.

What replaces enforcement is not nothing. The report runs on every push, the
count is visible in CI output, and a regeneration that introduces new vocabulary
shows up as a rising number rather than silence. Turning `--gate` on is a
one-flag change once the candidate list has been sorted by a person.

WHAT WOULD MAKE IT BLOCKING

Sorting the list once (`glossary_review.py`) collapses it to the terms that
genuinely have no answer. At that point the false-positive rate stops mattering,
because every false positive has been recorded as ordinary English and never
reappears. The rate gates the *rule*, not the *outcome*.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import glossary_lib as g  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true",
                    help="exit non-zero when undefined terms remain")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    snippets = g.collect_snippets()
    found = g.extract(snippets)
    gaps = g.undefined(found)

    known = g.defined_forms()
    ordinary = g.decided_ordinary()
    drafted = g.decided_defined()

    # A definition that itself introduces undefined vocabulary is a gap of the
    # same kind, one level down. Checked here so it cannot be introduced by
    # editing glossary.dart directly and skipping the review tool.
    bad_definitions: list[tuple[str, list[str]]] = []
    for term, record in g.load_decisions().get("decisions", {}).items():
        definition = record.get("definition")
        if not definition:
            continue
        introduced = g.definition_gaps(term, definition)
        if introduced:
            bad_definitions.append((term, introduced))

    if not args.quiet:
        print(f"user-facing strings scanned : {len(snippets)}")
        print(f"candidate terms             : {len(found)}")
        print(f"  defined in the glossary   : {sum(1 for t in found if t in known)}")
        print(f"  marked ordinary English   : {sum(1 for t in found if t in ordinary)}")
        print(f"  defined, not yet shipped  : {sum(1 for t in found if t in drafted)}")
        print(f"  UNDEFINED and undecided   : {len(gaps)}")
        if gaps:
            print()
            for cand in gaps[:20]:
                print(f"    {cand.term:<24} zipf {cand.zipf:4.2f}  "
                      f"x{cand.count}")
            if len(gaps) > 20:
                print(f"    … and {len(gaps) - 20} more — see "
                      f"reports/glossary_candidates.md")
        if bad_definitions:
            print("\n  definitions that introduce undefined terms:")
            for term, introduced in bad_definitions:
                print(f"    {term}: {', '.join(introduced)}")

    failed = bool(gaps) or bool(bad_definitions)

    if not failed:
        if not args.quiet:
            print("\nEvery domain term a user meets has an answer.")
        return 0

    if args.gate:
        print(f"\nFAIL: {len(gaps)} undefined term(s), "
              f"{len(bad_definitions)} circular definition(s).", file=sys.stderr)
        print("Run: python scripts/glossary_review.py --reviewer \"Your Name\"",
              file=sys.stderr)
        return 1

    print(f"\nREPORTED, NOT GATED: {len(gaps)} undefined term(s). The "
          f"extractor's false-positive rate on ordinary English (41.5%) is "
          f"above the 25% recorded in reports/glossary_precommitment.md, so "
          f"this does not fail the build. See that file for why the threshold "
          f"was not moved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
