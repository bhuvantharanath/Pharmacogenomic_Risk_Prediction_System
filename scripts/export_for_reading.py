#!/usr/bin/env python3
"""
Export every explanation to one readable document, for the author's own pass.

    python scripts/export_for_reading.py
    python scripts/export_for_reading.py --only clopidogrel

RETARGETED, NOT DELETED
    This was `export_for_review.py`, built to hand a faculty guide a document
    with a signature block per entry. **That reviewer does not exist**, so the
    signature blocks are gone — an unsigned approval box in a checked-in
    artifact is an invitation to treat it as merely unsigned rather than
    unobtainable.

    What survives is genuinely useful: twenty explanations printed next to the
    CPIC text each must follow from, in one document that can be read straight
    through. Reading them in sequence surfaces what per-entry review does not —
    an inconsistency between two phenotypes of the same drug, or a hedge that
    is present in five cases and missing in the sixth.

    `author_read.py` records that a read happened. This is the artifact to read.
"""

from __future__ import annotations

import argparse
import textwrap
from datetime import datetime, timezone
from pathlib import Path

from _common import (
    EXPLANATIONS_PATH,
    REPO_ROOT,
    REPORTS_DIR,
    bold,
    dim,
    green,
    load_json,
    red,
)

OUTPUT_PATH = REPORTS_DIR / "explanations_for_reading.md"
FIELD_LABELS = {
    "summary": "Summary",
    "mechanism": "Mechanism",
    "variant_rationale": "Variant rationale",
    "patient_friendly": "Patient-friendly",
}


def quote(text: str, width: int = 88) -> str:
    if not (text or "").strip():
        return "> _(empty)_"
    out: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            out.append(">")
            continue
        out.extend("> " + line for line in textwrap.wrap(paragraph, width))
    return "\n".join(out)


def render(entries: list[dict], store: dict) -> str:
    reviewed = sum(1 for e in entries if (e.get("review") or {}).get("read_by_author"))
    fallback = sum(1 for e in entries if e.get("fallback"))

    lines: list[str] = [
        "# PharmaGuard — every explanation, for reading straight through",
        "",
        f"**Exported:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Model:** `{store.get('model', 'unknown')}`  ",
        f"**Entries:** {len(entries)} ({fallback} template fallback, {reviewed} read by the author)",
        "",
        "---",
        "",
        "## ⚠️ There is no clinical reviewer for this document",
        "",
        "This project has **no qualified clinical expert**, and is not going to",
        "get one. Nothing in this document is an approval form, and nobody here",
        "is in a position to sign one.",
        "",
        "What has been done instead is narrower and machine-checked: every",
        "sentence making a clinical claim is verified to trace, word by word, to",
        "a CPIC recommendation issued by PharmCAT or to a cited mechanism",
        "document. See `reports/provenance_report.md`. That establishes the",
        "system invented nothing. It does **not** establish that the text is",
        "clinically correct.",
        "",
        "## Why read it anyway",
        "",
        "Reading twenty explanations in sequence catches things per-entry checks",
        "and automated ones both miss:",
        "",
        "1. **Direction of effect.** The one no check here can make. The guard",
        "   verifies every drug, gene, dose and allele appears in the source; the",
        "   provenance verifier additionally requires the whole claim to appear.",
        "   Neither can tell that a mechanism has been described **backwards**.",
        "   \"Reduced enzyme activity causes the drug to accumulate\" is fully",
        "   traced and completely wrong for a prodrug like clopidogrel, where",
        "   reduced activity means *less* active drug.",
        "2. **Inconsistency between phenotypes of one drug** — a hedge present in",
        "   five cases and missing in the sixth.",
        "3. **Plain language** — is `Patient-friendly` readable by a",
        "   non-specialist, without being alarming or falsely reassuring?",
        "4. **Honest gaps** — where no result was obtained (CYP2D6, warfarin),",
        "   does the text say so plainly rather than implying a normal result?",
        "",
        "### About the placeholders",
        "",
        "`{diplotype}` and `{detected_variants}` are **intentional**. Each",
        "explanation is reused for every patient with that phenotype, and those",
        "values are substituted per patient at request time (then cross-checked",
        "against the actual genotype call). Do not replace them with specific",
        "values.",
        "",
        "### Recording what you noticed",
        "",
        "```bash",
        "python scripts/author_read.py --author \"<your name>\"",
        "```",
        "",
        "`d` records that you read an entry; `f` records a concern. Neither is",
        "clinical approval, and the CLI has no action that is.",
        "",
        "---",
        "",
        "## Contents",
        "",
    ]

    for index, entry in enumerate(entries, start=1):
        flag = " ⚠️ *(template fallback)*" if entry.get("fallback") else ""
        lines.append(
            f"{index}. [{entry['drug']} — {entry['phenotype']}]"
            f"(#{index}-{entry['drug']}-{entry['phenotype'].lower()}){flag}"
        )
    lines += ["", "---", ""]

    for index, entry in enumerate(entries, start=1):
        guard = entry.get("guard_report") or {}
        lines += [
            f"<a id=\"{index}-{entry['drug']}-{entry['phenotype'].lower()}\"></a>",
            "",
            f"## {index}. {entry['drug']} — {entry['phenotype']}",
            "",
            "| | |",
            "| --- | --- |",
            f"| Gene | `{entry.get('gene', '?')}` |",
            f"| Phenotype | `{entry['phenotype']}` |",
            f"| Risk label | **{entry.get('derived_risk_label', '?')}** |",
            f"| Source | {'⚠️ template fallback' if entry.get('fallback') else 'LLM-generated'} |",
            f"| Model | `{entry.get('model', '—')}` |",
            f"| Prompt hash | `{entry.get('prompt_hash', '—')}` |",
            f"| Generated | {entry.get('generated_at', '—')} |",
            f"| Automated guard | {'✅ passed' if guard.get('passed') else '❌ FAILED'} |",
            "",
        ]
        if entry.get("fallback_reason"):
            lines += [f"> ⚠️ **Fallback reason:** {entry['fallback_reason']}", ""]

        lines += [
            "### Grounding — the source this must follow from",
            "",
            "**CPIC recommendation (verbatim, via PharmCAT):**",
            "",
            quote(entry.get("cpic_recommendation_used") or "_(none — this is an Unknown case)_"),
            "",
        ]
        if entry.get("mechanism_source"):
            lines += ["**Mechanism source:**", "", quote(entry["mechanism_source"]), ""]

        lines += ["### Explanation as a user would see it", ""]
        for field, label in FIELD_LABELS.items():
            lines += [f"**{label}**", "", quote(entry.get("explanation", {}).get(field, "")), ""]

        review = entry.get("review") or {}
        already = ""
        if review.get("read_by_author"):
            already = (
                f"  \n_Read by {review['read_by_author']} "
                f"on {str(review.get('read_at', '?'))[:10]}. Not clinical approval._"
            )
        if entry.get("author_concern"):
            already += f"  \n⚠️ _Author concern: {entry['author_concern']}_"

        # No approval checkboxes and no signature line. Nobody on this project
        # is qualified to tick "faithful, correct direction" for clinical text,
        # and a blank approval box in a checked-in document reads as awaiting a
        # signature rather than as awaiting a reviewer who is never coming.
        lines += [
            "### While reading, ask",
            "",
            "- Is the **direction of effect** right? Reduced enzyme activity means",
            "  more drug or less, depending on whether it is a prodrug — this is the",
            "  error no automated check here can catch, because such a sentence is",
            "  fully traced to its source and still wrong.",
            "- Does any sentence say more than the CPIC text above it?",
            "- Is `patient_friendly` genuinely plain language, and does it avoid",
            "  telling the reader what to do?",
            "- Does the *Unknown* case avoid implying a normal result?",
            "",
            "Anything that looks wrong: record it with",
            "`python scripts/author_read.py --author '<name>'` and press `f`.",
            f"{already}",
            "",
            "---",
            "",
        ]

    lines += [
        "## Sign-off",
        "",
        "I have reviewed the explanations in this document. Those marked approved",
        "are, to the best of my knowledge, faithful to the cited CPIC guidance and",
        "correct in the direction of effect they describe.",
        "",
        "I understand this is a research/educational prototype and **not a medical",
        "device**, and that approval here is not clinical validation.",
        "",
        "**Name:** ____________________________________",
        "",
        "**Role / department:** _______________________",
        "",
        "**Signature:** _______________  **Date:** ____________",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input", type=Path, default=EXPLANATIONS_PATH)
    parser.add_argument("-o", "--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--only", action="append", default=[], metavar="DRUG")
    args = parser.parse_args(argv)

    store = load_json(args.input)
    entries = store.get("explanations", [])
    if not entries:
        print(red(f"No explanations in {args.input}."))
        return 2
    if args.only:
        wanted = {d.strip().lower() for d in args.only}
        entries = [e for e in entries if e["drug"] in wanted]

    entries = sorted(entries, key=lambda e: (e["drug"], e["phenotype"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(entries, store), encoding="utf-8")

    words = sum(
        len(v.split()) for e in entries for v in e.get("explanation", {}).values()
    )
    print(green(f"Wrote {args.output.relative_to(REPO_ROOT)}"))
    print(dim(f"  {len(entries)} entries · ~{words:,} words to read"))
    print(dim("  Read it through, then record what you noticed:"))
    print(dim("    python scripts/author_read.py --author '<name>'"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
