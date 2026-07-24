#!/usr/bin/env python3
"""
Adjudicate flagged sentences against their source. This is the real gate.

    python scripts/adjudicate.py --adjudicator "B. Thangavel"
    python scripts/adjudicate.py --adjudicator "..." --only clopidogrel
    python scripts/adjudicate.py --adjudicator "..." --all   # incl. already-passing

WHY A HUMAN STEP, AND WHY IT IS TRACTABLE

The automated checks are filters, not verdicts. The faithfulness guard catches
invented entities; the field-level provenance policy catches claims it cannot
source. Neither can catch a sentence assembled entirely from sourced concepts
that is nevertheless **backwards** — "reduced activity means less active drug"
is right for a prodrug and wrong for a directly-active one, and every word of
both traces. Direction-of-effect needs a reader.

Twenty entries is a readable amount. That is the payoff of pre-generating: the
entire space of things a user can ever be shown is finite and can be examined
once, by a person, before it ships. An LLM in the request path forecloses that.

WHAT THIS IS NOT

**Not clinical expert approval.** This project has no qualified clinical
reviewer and will not get one. What is recorded here is that the project author
compared a sentence against its source and formed a judgement about whether the
sentence is supported by it. That is provenance adjudication. It is weaker than
clinical review and is never labelled as anything else — no field written by this
script implies clinical sign-off, and `clinical_expert_review` stays
NOT_OBTAINED.

HOW DECISIONS PERSIST

Each decision is keyed on a SHA-256 of (case, field, sentence text). Re-running
the checker never re-asks about a sentence already decided — but **editing the
sentence changes the hash**, so modified text returns to the queue automatically.
That is the property that makes this survivable across regenerations: judgements
are attached to exact text, not to positions in a file.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
    rel,
    rule,
    write_json_atomic,
    yellow,
)

SCRIPTS = REPO_ROOT / "scripts"

#: Bumped when the adjudication schema changes.
ADJUDICATION_VERSION = 1

#: Names that are not names. `git config user.name` defaults to "Your Name" on
#: an unconfigured machine, and 160 records were briefly written under it.
_PLACEHOLDER_NAMES = frozenset({
    "", "your name", "unknown", "user", "none", "n/a", "anonymous", "tbd",
})


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sentence_key(case: str, field_name: str, text: str) -> str:
    """
    Stable identity for one adjudicated sentence.

    Includes the text itself so an edit invalidates the decision — a judgement
    about wording that no longer exists would be worse than no judgement.
    """
    digest = hashlib.sha256()
    for part in (case, field_name, " ".join(text.split())):
        digest.update(part.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()[:16]


def wrap(text: str, indent: str = "    ", width: int = 74) -> str:
    out = []
    for para in (text or "").split("\n"):
        if not para.strip():
            out.append("")
            continue
        out.extend(textwrap.wrap(para, width, initial_indent=indent, subsequent_indent=indent))
    return "\n".join(out)


def collect_flagged(vp, entries: list[dict], include_all: bool) -> list[dict]:
    """Every sentence needing a decision, with the source it must follow from."""
    labels, phenos = vp.load_paraphrases()
    items: list[dict] = []
    for entry in entries:
        result = vp.verify_entry(entry, labels, phenos)
        for sentence in result.sentences:
            if sentence.kind in (vp.FRAMING, vp.PROCESS) and not include_all:
                continue
            if sentence.verified and not include_all:
                continue
            items.append({
                "case": result.key,
                "drug": entry.get("drug", ""),
                "phenotype": entry.get("phenotype", ""),
                "field": sentence.field_name,
                "kind": sentence.kind,
                "text": sentence.text,
                "unsupported": sorted(sentence.untraced),
                "auto_verified": sentence.verified,
                "cpic": entry.get("cpic_recommendation_used", ""),
                "implications": entry.get("cpic_implications", []) or [],
                "mechanism_source": entry.get("mechanism_source", ""),
                "key": sentence_key(result.key, sentence.field_name, sentence.text),
            })
    return items


def render(item: dict, index: int, total: int) -> None:
    print("\n" + rule(f"[{index}/{total}]  {item['case']}  ·  {item['field']}"))
    print(f"  {bold('classified')}   {item['kind']}"
          + ("" if item["auto_verified"] else red("   AUTOMATED CHECK COULD NOT SOURCE THIS")))
    if item["unsupported"]:
        print(f"  {bold('unsupported')}  {', '.join(item['unsupported'])}")

    print("\n" + bold("  ── THE SENTENCE ──"))
    print(green(wrap(item["text"])))

    print("\n" + bold("  ── THE SOURCE IT MUST FOLLOW FROM ──"))
    print(dim("  CPIC recommendation (verbatim from PharmCAT):"))
    print(dim(wrap(item["cpic"] or "(none — an Unknown case)")))
    if item["implications"]:
        print(dim("\n  CPIC implications:"))
        for implication in item["implications"]:
            print(dim(wrap(implication)))
    if item["mechanism_source"]:
        print(dim("\n  Mechanism source:"))
        print(dim(wrap(item["mechanism_source"])))

    print("\n" + bold("  ── ASK YOURSELF ──"))
    print(dim("    Is this claim supported by the source above?"))
    print(dim("    Is the DIRECTION right? (prodrug: less enzyme -> LESS active drug)"))
    print(dim("    Does it add a dose, timeline or probability the source lacks?"))


def edit_text(current: str) -> str | None:
    editor = os.environ.get("EDITOR", "nano")
    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as handle:
        handle.write(current)
        path = handle.name
    try:
        subprocess.run([editor, path], check=False)
        new = Path(path).read_text().strip()
    finally:
        os.unlink(path)
    return new if new and new != current.strip() else None


def apply_edit(entry: dict, field_name: str, old: str, new: str) -> bool:
    text = entry.get("explanation", {}).get(field_name, "")
    if old not in text:
        return False
    entry["explanation"][field_name] = text.replace(old, new, 1)
    return True


def record(entry: dict, item: dict, decision: str, rationale: str, adjudicator: str,
           key: str | None = None) -> None:
    """
    Write the decision onto the entry.

    Deliberately named `provenance_adjudications`, never `review` or `approval` —
    this records that a non-clinician checked a sentence against its source, and
    the field name should not be able to be misread as more than that.
    """
    block = entry.setdefault("provenance_adjudications", {})
    block[key or item["key"]] = {
        "version": ADJUDICATION_VERSION,
        "field": item["field"],
        "sentence": item["text"],
        "decision": decision,          # accepted | rejected | edited
        "rationale": rationale,
        "adjudicated_by": adjudicator,
        "adjudicated_at": datetime.now(timezone.utc).isoformat(),
        "note": "provenance adjudication by the project author; NOT clinical approval",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--adjudicator", required=True,
                        help="Your name. Recorded per decision. Not a clinical sign-off.")
    parser.add_argument("--only", action="append", default=[], metavar="DRUG")
    parser.add_argument("--all", action="store_true",
                        help="Include sentences the automated check already sourced.")
    parser.add_argument("-i", "--input", type=Path, default=EXPLANATIONS_PATH)
    parser.add_argument("--redo", action="store_true", help="Re-ask already-decided sentences.")
    parser.add_argument("--bulk-accept-unflagged", action="store_true",
                        help="Record a bulk decision for sentences the filter already sourced. "
                             "The record states it was a bulk decision, not an individual read.")
    args = parser.parse_args(argv)

    # An adjudication record names who made the judgement. A git placeholder is
    # not a person, and writing one would put a false attribution into a
    # clinical artifact — the precise failure mode this project exists to avoid.
    if args.adjudicator.strip().lower() in _PLACEHOLDER_NAMES:
        print(red(f"{args.adjudicator!r} is a placeholder, not a name."), file=sys.stderr)
        print("Adjudication records who judged each sentence; it cannot be nobody.",
              file=sys.stderr)
        print(dim("  Pass your real name:  --adjudicator 'A. Name'"), file=sys.stderr)
        return 2

    vp = _load("verify_provenance")
    store = load_json(args.input)
    entries = store.get("explanations", [])
    if args.only:
        wanted = {d.strip().lower() for d in args.only}
        entries = [e for e in entries if e.get("drug", "").lower() in wanted]
    if not entries:
        print(red("No entries match."), file=sys.stderr)
        return 2

    by_case = {f"{e['drug']}:{e['phenotype']}": e for e in entries}

    if args.bulk_accept_unflagged:
        # Every claim-bearing sentence the filter DID source. Recorded as a bulk
        # decision with its basis stated, so it can never be mistaken for
        # someone having read each line individually.
        every = collect_flagged(vp, entries, include_all=True)
        flagged_keys = {i["key"] for i in collect_flagged(vp, entries, include_all=False)}
        n = 0
        for item in every:
            if item["key"] in flagged_keys:
                continue  # a flagged sentence always needs an individual decision
            entry = by_case[item["case"]]
            if item["key"] in (entry.get("provenance_adjudications") or {}):
                continue
            record(entry, item, "accepted",
                   "bulk: automated filter sourced every assertion in this sentence "
                   "and found no polarity conflict; not individually read",
                   args.adjudicator)
            n += 1
        write_json_atomic(args.input, {**store, "explanations": list(by_case.values())})
        print(green(f"\nBulk-accepted {n} unflagged sentence(s) as {args.adjudicator}."))
        print(dim("  Each record states it was a bulk decision, not an individual read."))
        print(yellow("  Flagged sentences still require individual adjudication."))
        print(dim("\nNext:  python scripts/adjudication_status.py"))
        return 0

    items = collect_flagged(vp, entries, args.all)

    if not args.redo:
        pending = []
        for item in items:
            decided = (by_case[item["case"]].get("provenance_adjudications") or {})
            if item["key"] not in decided:
                pending.append(item)
        skipped = len(items) - len(pending)
        items = pending
    else:
        skipped = 0

    print(bold("\nPharmaGuard provenance adjudication"))
    print(dim(f"  adjudicator={args.adjudicator}   to decide={len(items)}"
              + (f"   already decided={skipped}" if skipped else "")))
    print(yellow("  This records provenance judgement, NOT clinical approval."))
    print(dim("  a=accept  r=reject  e=edit  s=skip  q=quit (saves as you go)"))

    if not items:
        print(green("\nNothing to adjudicate — every flagged sentence has a decision."))
        print(dim("Use --redo to revisit, or --all to review passing sentences too."))
        return 0

    accepted = rejected = edited = skipped_now = 0
    for index, item in enumerate(items, start=1):
        entry = by_case[item["case"]]
        while True:
            render(item, index, len(items))
            try:
                choice = input(bold("\n  [a]ccept  [r]eject  [e]dit  [s]kip  [q]uit > ")).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print(yellow("\n\nInterrupted — decisions so far are saved."))
                choice = "q"

            if choice in ("a", "accept"):
                why = input("  why is it supported? (recorded): ").strip()
                record(entry, item, "accepted", why, args.adjudicator)
                accepted += 1
                print(green("  accepted"))
                break
            if choice in ("r", "reject"):
                why = input("  what is wrong with it? (recorded): ").strip()
                record(entry, item, "rejected", why, args.adjudicator)
                rejected += 1
                print(red("  rejected — this entry must be regenerated or edited before shipping"))
                break
            if choice in ("e", "edit"):
                new = edit_text(item["text"])
                if not new:
                    print(dim("  no change"))
                    continue
                if not apply_edit(entry, item["field"], item["text"], new):
                    print(red("  could not locate the sentence to replace; skipping"))
                    break
                why = input("  why this edit? (recorded): ").strip()
                # Key on the NEW text: the decision belongs to what will ship.
                new_key = sentence_key(item["case"], item["field"], new)
                item_for_record = {**item, "text": new}
                record(entry, item_for_record, "edited", why, args.adjudicator, key=new_key)
                edited += 1
                print(green("  edited and recorded"))
                break
            if choice in ("s", "skip", ""):
                skipped_now += 1
                print(dim("  skipped — still unadjudicated"))
                break
            if choice in ("q", "quit"):
                write_json_atomic(args.input, {**store, "explanations": list(by_case.values())})
                print(f"\n  accepted {accepted}  rejected {rejected}  edited {edited}  skipped {skipped_now}")
                print(dim(f"  saved {rel(args.input)}"))
                return 0
            print(yellow("  unrecognised — use a, r, e, s or q"))

        write_json_atomic(args.input, {**store, "explanations": list(by_case.values())})

    print(rule())
    print(f"\n  accepted {green(str(accepted))}  rejected {red(str(rejected))}  "
          f"edited {yellow(str(edited))}  skipped {dim(str(skipped_now))}")
    print(dim(f"  saved {rel(args.input)}"))
    print(dim("\nNext:  python scripts/adjudication_status.py"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
