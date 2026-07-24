#!/usr/bin/env python3
"""
Author read-through — record that a human has read each explanation.

    python scripts/author_read.py --author "B. Thangavel"
    python scripts/author_read.py --author "..." --filter fallback
    python scripts/author_read.py --author "..." --only clopidogrel

THIS IS NOT CLINICAL REVIEW, AND CANNOT BECOME IT

    This project has **no qualified clinical reviewer**. This script therefore
    records exactly one thing: that the project author read an entry. It has no
    "approve" action, because the author is not qualified to approve clinical
    text and a CLI that offered the verb would manufacture an authority nobody
    holds. `clinical_expert_review` stays None and is never writable from here.

    Renamed from `review.py`, whose approve/reject vocabulary implied a sign-off
    that was never going to happen.

WHAT READING STILL ACHIEVES

    "Nobody has looked at this" and "a non-clinician read it and nothing jumped
    out" are different states, and the second is worth recording. A read-through
    catches what no machine here can: prose that is fluent, fully traced to its
    source, and still describes the direction of effect backwards. Flagging such
    an entry is genuinely useful; certifying it is not the author's to do.

WHY THE GROUNDING CONTEXT IS SHOWN ALONGSIDE

    Faithfulness cannot be judged from prose alone — that is the whole
    difficulty. Each entry prints next to the CPIC recommendation it came from
    and the mechanism source it cites, so "does this text follow from that
    source?" can actually be answered on screen.

Decisions are written back immediately, so quitting mid-pass never loses work.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime, timezone
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
    write_json_atomic,
    yellow,
)

FIELD_ORDER = ("summary", "mechanism", "variant_rationale", "patient_friendly")


def wrap(text: str, indent: str = "    ", width: int = 76) -> str:
    out: list[str] = []
    for paragraph in (text or "").split("\n"):
        if not paragraph.strip():
            out.append("")
            continue
        out.extend(textwrap.wrap(paragraph, width, initial_indent=indent, subsequent_indent=indent))
    return "\n".join(out)


def render_entry(entry: dict, index: int, total: int) -> None:
    review = entry.get("review") or {}
    status = (
        green("read by " + review["read_by_author"])
        if review.get("read_by_author")
        else yellow("NOT YET READ")
    )
    provenance = (
        green("verified") if review.get("provenance_verified") else red("UNVERIFIED")
    )
    kind = yellow("TEMPLATE FALLBACK") if entry.get("fallback") else green("LLM-generated")

    print("\n" + rule(f"[{index}/{total}]  {entry['drug']} / {entry['phenotype']}"))
    print(f"  {bold('gene')}         {entry.get('gene', '?')}")
    print(f"  {bold('risk label')}   {entry.get('derived_risk_label', '?')}")
    print(f"  {bold('source')}       {kind}   {dim(entry.get('model', ''))}")
    print(f"  {bold('status')}       {status}")
    print(f"  {bold('provenance')}   {provenance}   {dim(review.get('verified_by', ''))}")
    print(f"  {bold('clinical')}     {red('NOT REVIEWED BY ANY CLINICAL EXPERT')}")
    if entry.get("fallback_reason"):
        print(f"  {bold('fallback')}     {dim(entry['fallback_reason'][:70])}")

    guard = entry.get("guard_report") or {}
    guard_mark = green("passed") if guard.get("passed") else red("FAILED")
    print(f"  {bold('guard')}        {guard_mark}")

    print("\n" + bold("  ── GROUNDING (what this must follow from) ──"))
    cpic = entry.get("cpic_recommendation_used") or "(no CPIC recommendation — an Unknown case)"
    print(dim("  CPIC recommendation, verbatim:"))
    print(dim(wrap(cpic)))
    if entry.get("mechanism_source"):
        print(dim("\n  Mechanism source:"))
        print(dim(wrap(entry["mechanism_source"])))

    print("\n" + bold("  ── EXPLANATION (what a user would read) ──"))
    for field in FIELD_ORDER:
        value = entry.get("explanation", {}).get(field, "")
        print(f"\n  {bold(field)}:")
        print(wrap(value))
    print()


def edit_entry(entry: dict) -> bool:
    """Open the four fields in $EDITOR. Returns True if anything changed."""
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"
    original = {f: entry.get("explanation", {}).get(f, "") for f in FIELD_ORDER}

    header = (
        "# Edit the four fields below. Lines starting with '#' are ignored.\n"
        "#\n"
        "# KEEP the {diplotype} and {detected_variants} placeholders intact —\n"
        "# they are filled per patient at request time and cross-checked against\n"
        "# the called profile. Replacing them with literal values would ship one\n"
        "# patient's genotype to everyone.\n"
        "#\n"
        "# Do NOT introduce any dose, number, gene, drug or allele that is not in\n"
        "# the CPIC grounding text — the guard will reject it.\n"
        "#\n"
    )
    body = "".join(f"=== {field} ===\n{original[field]}\n\n" for field in FIELD_ORDER)

    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False) as handle:
        handle.write(header + body)
        path = Path(handle.name)

    try:
        subprocess.call([editor, str(path)])
        edited_text = path.read_text()
    finally:
        path.unlink(missing_ok=True)

    parsed: dict[str, str] = {}
    current: str | None = None
    for line in edited_text.splitlines():
        if line.startswith("#"):
            continue
        if line.startswith("=== ") and line.endswith(" ==="):
            current = line[4:-4].strip()
            parsed[current] = ""
            continue
        if current:
            parsed[current] += line + "\n"

    changed = False
    for field in FIELD_ORDER:
        new_value = parsed.get(field, original[field]).strip()
        if new_value and new_value != original[field]:
            entry.setdefault("explanation", {})[field] = new_value
            changed = True

    if changed:
        entry["edited_by_reviewer"] = True
        # Text a human edited is no longer purely model output; say so rather
        # than letting the provenance quietly drift.
        entry["generator"] = entry.get("generator", "") + "+human-edited"
    return changed


def re_guard(entry: dict) -> tuple[bool, list[str]]:
    """Re-run the faithfulness guard after an edit."""
    from pregenerate_explanations import Case, build_context
    from app.explanation.context import Explanation
    from app.explanation.guard import check

    case = Case(entry["drug"], entry.get("gene", ""), entry["phenotype"])
    context, _ = build_context(case)
    explanation = Explanation(**{f: entry["explanation"].get(f, "") for f in FIELD_ORDER})
    report = check(explanation, context, generator="human-edit")
    entry["guard_report"] = report.to_dict()
    return report.passed, [f"{v.kind}:{v.token}" for v in report.violations]


def _mark_read(entry: dict, author: str) -> None:
    """
    Record the read in the entry's review block.

    Touches `read_by_author` and nothing else. `clinical_expert_review` is
    deliberately not writable from this script — there is no clinician to write
    it, and a CLI that could set the field would eventually be used to.
    """
    review = entry.setdefault("review", {})
    review["read_by_author"] = author
    review["read_at"] = datetime.now(timezone.utc).isoformat()
    review.setdefault("provenance_verified", False)
    review.setdefault("clinical_expert_review", None)
    review["clinical_expert_review_status"] = "NOT_OBTAINED"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--author", required=True,
        help="Your name — recorded in review.read_by_author. Not an approval.",
    )
    parser.add_argument("--filter", choices=("all", "unread", "fallback", "read"), default="unread")
    parser.add_argument("--only", action="append", default=[], metavar="DRUG")
    parser.add_argument("-i", "--input", type=Path, default=EXPLANATIONS_PATH)
    args = parser.parse_args(argv)

    store = load_json(args.input)
    entries = store.get("explanations", [])
    if not entries:
        print(red(f"No explanations in {args.input}."), file=sys.stderr)
        return 2

    selected = entries
    if args.filter == "unreviewed":
        selected = [e for e in entries if not (e.get("review") or {}).get("read_by_author")]
    elif args.filter == "reviewed":
        selected = [e for e in entries if (e.get("review") or {}).get("read_by_author")]
    elif args.filter == "fallback":
        selected = [e for e in entries if e.get("fallback")]
    if args.only:
        wanted = {d.strip().lower() for d in args.only}
        selected = [e for e in selected if e["drug"] in wanted]

    if not selected:
        print(green(f"Nothing matches --filter {args.filter}. Nothing to do."))
        return 0

    print(bold("\nPharmaGuard author read-through"))
    print(dim(f"  author={args.author}  filter={args.filter}  entries={len(selected)}"))
    print(dim("  d=mark read  f=flag concern  e=edit  s=skip  q=quit (saves as you go)"))
    print(yellow("  This records that you READ an entry. It is not clinical approval."))

    read = flagged = skipped = 0

    for index, entry in enumerate(selected, start=1):
        while True:
            render_entry(entry, index, len(selected))
            try:
                choice = input(bold("  [a]pprove  [r]eject  [e]dit  [s]kip  [q]uit > ")).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print(yellow("\n\nInterrupted — decisions so far are saved."))
                choice = "q"

            if choice in ("d", "read", "done"):
                _mark_read(entry, args.author)
                read += 1
                print(green("  marked read (not approved — no clinical sign-off exists)"))
                break
            if choice in ("f", "flag"):
                concern = input("  what looks wrong (recorded): ").strip()
                _mark_read(entry, args.author)
                entry["author_concern"] = concern
                flagged += 1
                print(yellow("  concern recorded — investigate before this ships"))
                break
            if choice in ("e", "edit"):
                if edit_entry(entry):
                    passed, violations = re_guard(entry)
                    if passed:
                        print(green("  edit saved; guard re-run and passed"))
                    else:
                        print(red(f"  edit saved BUT the guard now fails: {', '.join(violations[:4])}"))
                        print(red("  fix it or the entry will ship with a failing guard report"))
                else:
                    print(dim("  no change"))
                write_json_atomic(args.input, {**store, "explanations": entries})
                continue  # re-render with the edit applied
            if choice in ("s", "skip", ""):
                skipped += 1
                print(dim("  skipped"))
                break
            if choice in ("q", "quit"):
                write_json_atomic(args.input, {**store, "explanations": entries})
                print(f"\n  read {read}  flagged {flagged}  skipped {skipped}")
                print(dim(f"  saved {args.input.relative_to(REPO_ROOT)}"))
                return 0
            print(yellow("  unrecognised — use d, f, e, s or q"))

        write_json_atomic(args.input, {**store, "explanations": entries})

    print(rule())
    print(f"\n  read {green(str(read))}  flagged {yellow(str(flagged))}  skipped {dim(str(skipped))}")
    print(dim(f"  saved {args.input.relative_to(REPO_ROOT)}"))
    print(yellow("\n  Reading is not clinical approval. No clinical expert has reviewed"))
    print(yellow("  this content, and `clinical_expert_review` remains NOT_OBTAINED."))
    print(dim("\nNext:  python scripts/review_status.py"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
