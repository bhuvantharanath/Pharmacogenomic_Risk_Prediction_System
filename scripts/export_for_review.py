#!/usr/bin/env python3
"""
Export every explanation to a printable Markdown document for offline sign-off.

    python scripts/export_for_review.py
    python scripts/export_for_review.py --only clopidogrel

WHY THIS EXISTS ALONGSIDE review.py
    A faculty guide will not sit at a terminal working through an interactive
    prompt. This produces one document they can read on a screen or on paper,
    with each explanation printed next to the CPIC text it must follow from and
    a signature block per entry.

    `review.py` remains the path for recording decisions in the file; this is
    the path for getting a human to actually make them.
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

OUTPUT_PATH = REPORTS_DIR / "explanations_for_review.md"
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
    reviewed = sum(1 for e in entries if e.get("reviewed_by"))
    fallback = sum(1 for e in entries if e.get("fallback"))

    lines: list[str] = [
        "# PharmaGuard — explanations for review",
        "",
        f"**Exported:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Model:** `{store.get('model', 'unknown')}`  ",
        f"**Entries:** {len(entries)} ({fallback} template fallback, {reviewed} already reviewed)",
        "",
        "---",
        "",
        "## What you are being asked to check",
        "",
        "Each explanation below is printed **next to the CPIC text it was",
        "generated from**. For each one, please judge:",
        "",
        "1. **Faithfulness** — does the explanation follow from the CPIC text",
        "   above it, without adding anything?",
        "2. **Direction of effect** — this is the one a machine cannot check.",
        "   The automated guard verifies that every drug, gene, dose and allele",
        "   mentioned appears in the source. It **cannot** tell that a mechanism",
        "   has been described backwards. \"Reduced enzyme activity causes the",
        "   drug to accumulate\" is fully grounded and completely wrong for a",
        "   prodrug like clopidogrel, where reduced activity means *less* active",
        "   drug. Please check each mechanism points the right way.",
        "3. **Plain language** — is `Patient-friendly` genuinely readable by a",
        "   non-specialist, without being alarming or falsely reassuring?",
        "4. **Honest gaps** — where no result was obtained (CYP2D6, warfarin),",
        "   does the text say so plainly rather than implying a normal result?",
        "",
        "### About the placeholders",
        "",
        "`{diplotype}` and `{detected_variants}` are **intentional**. Each",
        "explanation is reused for every patient with that phenotype, and those",
        "values are substituted per patient at request time (then cross-checked",
        "against the actual genotype call). Please do not replace them with",
        "specific values.",
        "",
        "### Recording your decision",
        "",
        "Sign the block under each entry, or return the document with comments.",
        "Decisions are transcribed with:",
        "",
        "```bash",
        "python scripts/review.py --reviewer \"<your name>\"",
        "```",
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

        already = ""
        if entry.get("reviewed_by"):
            already = (
                f"  \n_Previously reviewed by {entry['reviewed_by']} "
                f"on {entry.get('reviewed_at', '?')[:10]} "
                f"({entry.get('review_decision', 'approved')})._"
            )

        lines += [
            "### Reviewer decision",
            "",
            "| | |",
            "| --- | --- |",
            "| ☐ Approve — faithful, correct direction, readable | |",
            "| ☐ Approve with edits *(note them below)* | |",
            "| ☐ Reject *(state why)* | |",
            "",
            "**Comments:**",
            "",
            "```",
            "",
            "",
            "```",
            "",
            f"**Reviewer:** ______________________  **Date:** ____________{already}",
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
    print(dim(f"  {len(entries)} entries · ~{words:,} words of explanation to review"))
    print(dim("  Share this with the project guide, then transcribe decisions with review.py"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
