#!/usr/bin/env python3
"""
Interactive review CLI — approve, reject, edit or skip each explanation.

    python scripts/review.py --reviewer "Dr A. Guide"
    python scripts/review.py --reviewer "..." --filter fallback
    python scripts/review.py --reviewer "..." --only clopidogrel

WHY THE GROUNDING CONTEXT IS SHOWN ALONGSIDE
    A reviewer cannot judge faithfulness from the prose alone — that is the
    whole difficulty. Each entry is therefore printed next to the CPIC
    recommendation it was generated from and the mechanism source it cites, so
    the question "does this text follow from that source?" can actually be
    answered on screen.

WHAT THE MACHINE CANNOT DECIDE
    The faithfulness guard verifies that every clinical entity in the text
    appears in the context. It cannot tell that a mechanism has been described
    backwards — "reduced CYP2C19 activity makes the drug accumulate" is fully
    grounded and completely wrong. Direction of effect is exactly what a human
    reviewer is here for.

Decisions are written back immediately, so quitting mid-review never loses work.
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
    status = (
        green("reviewed by " + entry["reviewed_by"])
        if entry.get("reviewed_by")
        else yellow("UNREVIEWED")
    )
    kind = yellow("TEMPLATE FALLBACK") if entry.get("fallback") else green("LLM-generated")

    print("\n" + rule(f"[{index}/{total}]  {entry['drug']} / {entry['phenotype']}"))
    print(f"  {bold('gene')}         {entry.get('gene', '?')}")
    print(f"  {bold('risk label')}   {entry.get('derived_risk_label', '?')}")
    print(f"  {bold('source')}       {kind}   {dim(entry.get('model', ''))}")
    print(f"  {bold('status')}       {status}")
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reviewer", required=True, help="Your name — recorded in reviewed_by.")
    parser.add_argument("--filter", choices=("all", "unreviewed", "fallback", "reviewed"), default="unreviewed")
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
        selected = [e for e in entries if not e.get("reviewed_by")]
    elif args.filter == "reviewed":
        selected = [e for e in entries if e.get("reviewed_by")]
    elif args.filter == "fallback":
        selected = [e for e in entries if e.get("fallback")]
    if args.only:
        wanted = {d.strip().lower() for d in args.only}
        selected = [e for e in selected if e["drug"] in wanted]

    if not selected:
        print(green(f"Nothing matches --filter {args.filter}. Nothing to do."))
        return 0

    print(bold("\nPharmaGuard explanation review"))
    print(dim(f"  reviewer={args.reviewer}  filter={args.filter}  entries={len(selected)}"))
    print(dim("  a=approve  r=reject  e=edit  s=skip  q=quit (saves as you go)"))

    approved = rejected = skipped = 0

    for index, entry in enumerate(selected, start=1):
        while True:
            render_entry(entry, index, len(selected))
            try:
                choice = input(bold("  [a]pprove  [r]eject  [e]dit  [s]kip  [q]uit > ")).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print(yellow("\n\nInterrupted — decisions so far are saved."))
                choice = "q"

            if choice in ("a", "approve"):
                entry["reviewed_by"] = args.reviewer
                entry["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                entry["review_decision"] = "approved"
                approved += 1
                print(green("  approved"))
                break
            if choice in ("r", "reject"):
                reason = input("  reason (recorded): ").strip()
                entry["reviewed_by"] = args.reviewer
                entry["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                entry["review_decision"] = "rejected"
                entry["review_note"] = reason
                rejected += 1
                print(red("  rejected — regenerate or edit this case before shipping"))
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
                print(f"\n  approved {approved}  rejected {rejected}  skipped {skipped}")
                print(dim(f"  saved {args.input.relative_to(REPO_ROOT)}"))
                return 0
            print(yellow("  unrecognised — use a, r, e, s or q"))

        write_json_atomic(args.input, {**store, "explanations": entries})

    print(rule())
    print(f"\n  approved {green(str(approved))}  rejected {red(str(rejected))}  skipped {dim(str(skipped))}")
    print(dim(f"  saved {args.input.relative_to(REPO_ROOT)}"))
    print(dim("\nNext:  python scripts/review_status.py"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
