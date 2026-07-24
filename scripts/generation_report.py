#!/usr/bin/env python3
"""
Emit reports/generation_report.md — the real numbers for the project report.

Every figure here is computed from `explanations.json`, `case_matrix.json` and
`logs/guard_events.jsonl`. Nothing is estimated; if a number is unavailable the
report says so rather than guessing.

    python scripts/generation_report.py
    python scripts/generation_report.py --json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from _common import (
    CASE_MATRIX_PATH,
    EXPLANATIONS_PATH,
    GUARD_EVENTS_PATH,
    REPO_ROOT,
    REPORTS_DIR,
    bold,
    dim,
    green,
    load_json,
    read_jsonl,
    rule,
    yellow,
)

OUTPUT_PATH = REPORTS_DIR / "generation_report.md"


def collect() -> dict:
    matrix = load_json(CASE_MATRIX_PATH)
    store = load_json(EXPLANATIONS_PATH)
    entries = store.get("explanations", [])
    cases = matrix.get("cases", [])

    reachable = [c for c in cases if c.get("reachable")]
    unreachable = [c for c in cases if not c.get("reachable")]
    by_key = {f"{e['drug']}:{e['phenotype']}": e for e in entries}

    # Classify by the `generator` field, NOT by "not fallback". Phase 3 entries
    # predate the fallback flag entirely, so absence-of-flag would silently
    # count deterministic template text as LLM-generated — exactly the
    # misreporting this phase exists to end.
    generated = [e for e in entries if str(e.get("generator", "")).startswith("llm")]
    fallback = [e for e in entries if e.get("fallback")]
    template_legacy = [
        e for e in entries
        if not str(e.get("generator", "")).startswith("llm") and not e.get("fallback")
    ]
    missing = [c for c in reachable if f"{c['drug']}:{c['phenotype']}" not in by_key]

    events = list(read_jsonl(GUARD_EVENTS_PATH))
    pregen_events = [e for e in events if e.get("source") == "pregenerate"]
    passed = [e for e in pregen_events if e.get("passed")]
    failed = [e for e in pregen_events if not e.get("passed")]

    llm_entries = [e for e in entries if str(e.get("generator", "")).startswith("llm")]
    models = sorted({e.get("model", "") for e in entries if e.get("model")})
    reviewed = [e for e in entries if (e.get("review") or {}).get("read_by_author")]

    per_drug: dict[str, dict] = defaultdict(lambda: {"reachable": 0, "generated": 0, "fallback": 0, "unreachable": 0})
    for case in cases:
        bucket = per_drug[case["drug"]]
        if case.get("reachable"):
            bucket["reachable"] += 1
        else:
            bucket["unreachable"] += 1
    for entry in entries:
        bucket = per_drug[entry["drug"]]
        if entry.get("fallback"):
            bucket["fallback"] += 1
        else:
            bucket["generated"] += 1

    return {
        "matrix": matrix,
        "store": store,
        "entries": entries,
        "reachable": reachable,
        "unreachable": unreachable,
        "generated": generated,
        "fallback": fallback,
        "template_legacy": template_legacy,
        "missing": missing,
        "events": pregen_events,
        "guard_passed": passed,
        "guard_failed": failed,
        "llm_entries": llm_entries,
        "models": models,
        "reviewed": reviewed,
        "per_drug": dict(per_drug),
    }


def render(data: dict) -> str:
    store = data["store"]
    entries = data["entries"]
    events = data["events"]

    guard_total = len(events)
    guard_pass_rate = (
        f"{len(data['guard_passed']) / guard_total * 100:.1f}%" if guard_total else "n/a (no events logged)"
    )

    lines: list[str] = [
        "# Explanation generation report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}  ",
        f"**Explanation store:** `{EXPLANATIONS_PATH.relative_to(REPO_ROOT)}`  ",
        f"**Store generator:** `{store.get('generator', 'unknown')}`  ",
        f"**Store written:** {store.get('generated_at', 'unknown')}",
        "",
        "All figures below are computed from the generated artefacts, not estimated.",
        "",
        "## Coverage",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Cases enumerated | {len(data['matrix'].get('cases', []))} |",
        f"| **Reachable** | **{len(data['reachable'])}** |",
        f"| Unreachable (documented, never authored) | {len(data['unreachable'])} |",
        f"| Entries in store | {len(entries)} |",
        f"| — LLM-generated, guard-passed | {len(data['generated'])} |",
        f"| — Template fallback (guard rejected or API failed) | {len(data['fallback'])} |",
        f"| — Template, pre-LLM legacy | {len(data['template_legacy'])} |",
        f"| Reachable but missing | {len(data['missing'])} |",
        f"| Human-reviewed | {len(data['reviewed'])} / {len(entries)} |",
        "",
    ]

    if data["missing"]:
        lines += [
            "> ⚠️ **Gaps.** These reachable cases have no entry, so they fall back to",
            "> the deterministic template at runtime:",
            "",
        ]
        for case in data["missing"]:
            lines.append(f"> - `{case['drug']}` / `{case['phenotype']}`")
        lines.append("")

    lines += [
        "## Reproducibility",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Model(s) | {', '.join(f'`{m}`' for m in data['models']) or '_none recorded_'} |",
        f"| Entries with a prompt hash | {sum(1 for e in entries if e.get('prompt_hash'))} / {len(entries)} |",
        f"| Distinct prompt hashes | {len({e.get('prompt_hash') for e in entries if e.get('prompt_hash')})} |",
        "",
        "Each entry records the exact model id, a SHA-256 prefix of "
        "(model + system instruction + user prompt), and an ISO timestamp. A "
        "prompt change is therefore visible as a hash change rather than having "
        "to be remembered.",
        "",
        "## Faithfulness guard",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Guard evaluations logged | {guard_total} |",
        f"| Passed | {len(data['guard_passed'])} |",
        f"| Rejected | {len(data['guard_failed'])} |",
        f"| Pass rate | {guard_pass_rate} |",
        "",
    ]

    if data["guard_failed"]:
        lines += [
            "### Every rejection, with its case",
            "",
            "| Case | Attempt | Violations | Action |",
            "| --- | ---: | --- | --- |",
        ]
        for event in data["guard_failed"]:
            violations = ", ".join(
                f"`{v['kind']}:{v['token']}`" for v in event.get("violations", [])[:5]
            ) or "_none recorded_"
            lines.append(
                f"| `{event.get('case', '?')}` | {event.get('attempt', '?')} | "
                f"{violations} | {event.get('action_taken', '?')} |"
            )
        lines.append("")

        kinds = Counter(
            v["kind"] for e in data["guard_failed"] for v in e.get("violations", [])
        )
        if kinds:
            lines += ["**Rejections by entity kind:**", ""]
            for kind, count in kinds.most_common():
                lines.append(f"- `{kind}`: {count}")
            lines.append("")
    else:
        lines += [
            "_No guard rejections recorded._",
            "",
            "For a run against a real model this is worth interrogating rather than",
            "celebrating: check `logs/guard_events.jsonl` is actually being written,",
            "and see `reports/guard_experiment.md` for the adversarial validation",
            "that deliberately provokes fabrication.",
            "",
        ]

    lines += ["## Per-drug coverage", "", "| Drug | Reachable | Generated | Fallback | Unreachable |", "| --- | ---: | ---: | ---: | ---: |"]
    for drug in sorted(data["per_drug"]):
        row = data["per_drug"][drug]
        lines.append(
            f"| `{drug}` | {row['reachable']} | {row['generated']} | {row['fallback']} | {row['unreachable']} |"
        )
    lines.append("")

    if data["fallback"]:
        lines += ["### Fallback entries and why", "", "| Case | Reason |", "| --- | --- |"]
        for entry in data["fallback"]:
            reason = (entry.get("fallback_reason") or "unrecorded").replace("|", "\\|")
            lines.append(f"| `{entry['drug']}` / `{entry['phenotype']}` | {reason[:150]} |")
        lines.append("")

    lines += [
        "## Unreachable cases",
        "",
        "Explanations are **not** authored for these. Writing prose for a case the",
        "pipeline cannot produce would inflate the coverage figure with fiction.",
        "",
        "| Drug | Gene | Phenotype | Why unreachable |",
        "| --- | --- | --- | --- |",
    ]
    for case in data["unreachable"]:
        reason = case.get("reason", "").replace("|", "\\|")
        lines.append(
            f"| `{case['drug']}` | {case['gene']} | {case['phenotype']} | {reason[:160]} |"
        )

    lines += [
        "",
        "## Review status",
        "",
        f"**{len(data['reviewed'])} of {len(entries)}** entries have been read by the "
        "project author. No qualified clinical expert has reviewed any of them, and "
        "none is expected to — see `reports/provenance_report.md` for what is "
        "machine-verified in place of that.",
        "",
    ]
    if len(data["reviewed"]) < len(entries):
        lines += [
            "> ⚠️ **Not approved for demo or submission.** The API reports the",
            "> unreviewed count in `quality_metrics.warnings` on every response.",
            "> Run `python scripts/review.py --reviewer '<name>'` or share",
            "> `reports/explanations_for_review.md` with the project guide.",
            "",
        ]

    lines += [
        "---",
        "",
        "_Regenerate with `python scripts/generation_report.py`._",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    data = collect()

    if args.json:
        print(
            json.dumps(
                {
                    "reachable": len(data["reachable"]),
                    "unreachable": len(data["unreachable"]),
                    "entries": len(data["entries"]),
                    "generated": len(data["generated"]),
                    "fallback": len(data["fallback"]),
                    "missing": [f"{c['drug']}:{c['phenotype']}" for c in data["missing"]],
                    "guard_evaluations": len(data["events"]),
                    "guard_passed": len(data["guard_passed"]),
                    "guard_failed": len(data["guard_failed"]),
                    "reviewed": len(data["reviewed"]),
                    "models": data["models"],
                },
                indent=1,
            )
        )
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(data), encoding="utf-8")

    print(rule("generation report"))
    print(f"  reachable        {bold(str(len(data['reachable'])))}")
    print(f"  generated (LLM)  {green(str(len(data['generated'])))}")
    print(f"  fallback         {yellow(str(len(data['fallback'])))}")
    if data["template_legacy"]:
        print(f"  template (legacy){yellow(str(len(data['template_legacy'])).rjust(3))}"
              + dim("  pre-LLM entries — regenerate with --force"))
    print(f"  missing          {yellow(str(len(data['missing'])))}")
    print(f"  guard events     {len(data['events'])}  "
          f"({len(data['guard_passed'])} passed, {len(data['guard_failed'])} rejected)")
    print(f"  reviewed         {len(data['reviewed'])}/{len(data['entries'])}")
    print(rule())
    print(dim(f"\nwrote {args.output.relative_to(REPO_ROOT)}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
