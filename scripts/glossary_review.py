#!/usr/bin/env python3
"""
Sort the candidate list, once, by hand.

    python scripts/glossary_review.py --reviewer "Your Name"

Walks every undefined candidate, shows where it appears in the shipped text,
and takes one of three answers:

    d   define it        — you type the definition
    o   ordinary English — no definition needed, never asked again
    s   skip for now     — stays undefined, the gate keeps reporting it

WHY A PERSON HAS TO DO THIS

Deciding that a word needs no explanation is a judgement about a reader, and
this project has one standing rule about judgements: whoever made it is
recorded, and an automated decision is recorded as automated. Nothing here
writes a decision on anyone's behalf. There is no `--accept-all`, and adding one
would defeat the point rather than speed it up.

The alternative — a model deciding which words a patient understands — is the
same circularity this project already rejected for grading its own explanations.

WHAT IT ENFORCES

A definition is refused if it introduces another undefined term. That check is
not advisory: it is the failure this audit exists to prevent, one level down.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import glossary_lib as g  # noqa: E402

MAX_SENTENCES = 3


def _save(data: dict) -> None:
    g.DECISIONS_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _prompt_definition(term: str, draft: str | None) -> str | None:
    """Take a definition and refuse it until it stands on its own."""
    while True:
        if draft:
            print(f"\n  drafted: {draft}")
            answer = input("  accept draft? [y/n] ").strip().lower()
            if answer == "y":
                text = draft
            else:
                text = input("  definition: ").strip()
        else:
            text = input("  definition: ").strip()

        if not text:
            return None

        sentences = g.sentence_count(text)
        if sentences > MAX_SENTENCES:
            print(f"  ✗ {sentences} sentences. One or two — longer than that is "
                  f"an article, which is not what someone mid-sentence wants.")
            draft = None
            continue

        gaps = g.definition_gaps(term, text)
        if gaps:
            # Hard stop, not a warning. A definition that needs a glossary of
            # its own is the exact defect being audited.
            print(f"  ✗ introduces undefined terms: {', '.join(gaps)}")
            print("    Define those first, mark them ordinary English, or say "
                  "it another way.")
            draft = None
            continue

        return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviewer", required=True,
                    help="who is deciding; recorded against every decision")
    ap.add_argument("--drafts", type=Path,
                    help="optional JSON of {term: definition} to offer for "
                         "approval. Nothing is written without a yes.")
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after N decisions; the rest stay undecided")
    ap.add_argument("--category", default="A",
                    choices=sorted(g.CATEGORIES) + ["all"],
                    help="which bucket to work through (default A — the terms "
                         "that actually need definitions)")
    args = ap.parse_args()

    reviewer = args.reviewer.strip()
    # The same guard the adjudication store carries: a placeholder identity is
    # worse than no identity, because it looks like accountability.
    placeholders = {"", "tbd", "todo", "n/a", "na", "unknown", "anonymous",
                    "reviewer", "me", "claude", "ai", "assistant", "automated"}
    if reviewer.lower() in placeholders:
        print(f"Refusing to record decisions as {reviewer!r}. A false "
              f"attribution in an academic artifact is worse than an "
              f"unadjudicated term.", file=sys.stderr)
        return 2

    drafts: dict[str, str] = {}
    if args.drafts and args.drafts.exists():
        drafts = json.loads(args.drafts.read_text())

    data = g.load_decisions()
    data.setdefault("decisions", {})
    data.setdefault("about", (
        "Human decisions about glossary candidates extracted by "
        "scripts/extract_glossary_candidates.py. Each record names who decided "
        "and when. Nothing in this file may be written by an automated process "
        "without recording itself as one."
    ))

    snippets = g.collect_snippets()
    gaps = g.undefined(g.extract(snippets))

    if args.category != "all":
        by_term = {c.term: c for c in gaps}
        wanted = set(g.triage(by_term, snippets)[args.category])
        gaps = [c for c in gaps if c.term in wanted]
        print(f"category {args.category}: {g.CATEGORIES[args.category]}")

        # Foundational terms first. The definition checker refuses anything
        # leaning on an undefined term, so alphabetical order means refusal
        # after refusal — `diplotype` before `gene` cannot be answered.
        order, cycles = g.review_order([c.term for c in gaps], by_term)
        rank = {term: i for i, term in enumerate(order)}
        gaps.sort(key=lambda c: rank[c.term])
        if cycles:
            print(f"\n{len(cycles)} mutually-dependent cluster(s). Each needs a "
                  f"deliberate entry point — pick one and say it in plainer "
                  f"words than the others:")
            for cluster in cycles[:5]:
                print("    " + ", ".join(cluster))
            print()

    # A drug's description is already written, on the About screen. Offering it
    # means nothing is reworded and the two places cannot drift apart.
    drug_blurbs = g.about_table_descriptions()
    drafts.update({d: b for d, b in drug_blurbs.items() if d not in drafts})

    if not gaps:
        print("Nothing undecided. The gate has everything it needs.")
        return 0

    print(f"{len(gaps)} undecided candidates. Reviewer: {reviewer}")
    print("d = define · o = ordinary English · s = skip · q = save and quit\n")

    decided = 0
    for i, cand in enumerate(gaps, 1):
        if args.limit and decided >= args.limit:
            break

        print("─" * 72)
        print(f"[{i}/{len(gaps)}]  {cand.term}   (zipf {cand.zipf:.2f}, "
              f"{cand.count} use{'s' if cand.count != 1 else ''})")
        for source, line in cand.contexts:
            print(f"    {source}")
            print(f"    “{line}”")

        answer = input("\n  [d/o/s/q] ").strip().lower()
        if answer == "q":
            break
        if answer == "s" or answer not in {"d", "o"}:
            continue

        record = {
            "decided_by": reviewer,
            "decided_at": datetime.now(timezone.utc).isoformat(),
            "decided_how": "human review via scripts/glossary_review.py",
            "zipf": round(cand.zipf, 3),
            "uses": cand.count,
        }

        if answer == "o":
            record["decision"] = "ordinary"
            note = input("  why is it ordinary English? (optional) ").strip()
            if note:
                record["note"] = note
        else:
            definition = _prompt_definition(cand.term, drafts.get(cand.term))
            if definition is None:
                print("  (no definition given — left undecided)")
                continue
            record["decision"] = "define"
            record["definition"] = definition
            if drafts.get(cand.term) == definition:
                record["definition_source"] = "drafted, approved by reviewer"
            else:
                record["definition_source"] = "written by reviewer"

        data["decisions"][cand.term] = record
        _save(data)
        decided += 1
        print(f"  ✓ recorded ({record['decision']})")

    print(f"\n{decided} decision(s) recorded in "
          f"{g.DECISIONS_PATH.relative_to(g.REPO)}")
    print("Terms marked 'define' still need adding to app/lib/glossary/"
          "glossary.dart before they reach a reader.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
