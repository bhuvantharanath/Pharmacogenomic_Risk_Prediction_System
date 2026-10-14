#!/usr/bin/env python3
"""Prepare a read-only owner packet for claims blocking generated prose.

The packet records evidence and required actions. It never records a decision,
changes the explanation store, or approves an entry.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

from _common import EXPLANATIONS_PATH, REPO_ROOT, load_json

sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.explanation import approval  # noqa: E402


SCRIPTS = REPO_ROOT / "scripts"
DEFAULT_OUTPUT = REPO_ROOT / "reports" / "release_content_review.md"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _candidate_span(item: dict, entry: dict, worksheet) -> str:
    if item["field"] != "mechanism":
        source = str(entry.get("cpic_recommendation_used") or "").strip()
        return source or "No CPIC recommendation text recorded; locate an authoritative source."

    passages, filename, _citation = worksheet.corpus_passages(
        entry.get("gene"), entry["drug"]
    )
    claim_terms = worksheet.domain_tokens(item["text"])
    ranked = sorted(
        (
            (len(claim_terms & worksheet.expand(passage.text)), passage)
            for passage in passages
        ),
        key=lambda row: row[0],
        reverse=True,
    )
    if not ranked or ranked[0][0] == 0:
        return "No candidate supporting span found; locate and assess the source manually."
    passage = ranked[0][1]
    return (
        f"Candidate span in {filename}:{passage.line} "
        f"({passage.section}): {passage.text}"
    )


def pending_items(source: Path = EXPLANATIONS_PATH) -> list[dict]:
    vp = _load("verify_provenance")
    adjudicate = _load("adjudicate")
    worksheet = _load("build_adjudication_worksheet")
    entries = load_json(source).get("explanations") or []
    by_case = {f"{e['drug']}:{e['phenotype']}": e for e in entries}
    pending: list[dict] = []
    for item in adjudicate.collect_flagged(vp, entries, include_all=True):
        entry = by_case[item["case"]]
        record = (entry.get("provenance_adjudications") or {}).get(item["key"]) or {}
        decision = record.get("decision")
        reviewer = str(record.get("adjudicated_by") or "").strip()
        if decision in {"accepted", "edited"} and reviewer and reviewer.lower() != "automated":
            continue
        if decision == "rejected":
            status = "rejected; text still stored"
            action = "Remove or correct the rejected sentence, then obtain new review."
        elif reviewer.lower() == "automated" and decision:
            status = f"automated {decision}; not human review"
            action = "Have a named person assess the exact sentence and source."
        else:
            status = "unresolved; no human decision"
            action = "Obtain a named human decision with rationale; edit or withdraw unsupported text."
        pending.append(
            {
                "entry_id": item["case"],
                "drug": entry["drug"],
                "gene": entry.get("gene") or "",
                "phenotype": entry["phenotype"],
                "field": item["field"],
                "sentence": item["text"],
                "claim": item["text"],
                "claim_key": item["key"],
                "source": (
                    entry.get("mechanism_source")
                    if item["field"] == "mechanism"
                    else "CPIC recommendation via PharmCAT"
                ),
                "candidate_supporting_source_span": _candidate_span(item, entry, worksheet),
                "current_automated_status": (
                    "automated decision" if reviewer.lower() == "automated" and decision
                    else "escalated/undecided" if record.get("escalated")
                    else "no automated decision recorded"
                ),
                "existing_human_status": "no human decision for this claim",
                "entry_read_by_author": (
                    (entry.get("review") or {}).get("read_by_author") or "not recorded"
                ),
                "status": status,
                "required_owner_action": action,
                "content_hash": approval.content_hash(entry.get("explanation") or {}),
            }
        )
    return pending


def render(items: list[dict]) -> str:
    by_entry: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_entry[item["entry_id"]].append(item)
    lines = [
        "# Generated explanation release review packet",
        "",
        f"{len(by_entry)} stored entries contain {len(items)} claims requiring human action.",
        "Candidate source spans below are retrieval aids, not evidence of support or review.",
        "No decision or clinical expert approval is recorded by this packet.",
        "",
        "After genuine review, record claim decisions against their exact sentence keys; "
        "rebuild the approval manifest and rerun the authoritative release gate.",
        "The declared release policy still requires human adjudication of every stored claim.",
        "",
    ]
    for entry_id, claims in sorted(by_entry.items()):
        first = claims[0]
        lines += [
            f"## {entry_id}",
            "",
            f"- Entry ID: `{entry_id}`",
            f"- Drug: {first['drug']}",
            f"- Gene/context: {first['gene']} / {first['phenotype']}",
            f"- Content hash: `{first['content_hash']}`",
            f"- Pending claims: {len(claims)}",
            f"- Entry review status: unapproved; author read by: {first['entry_read_by_author']}",
            "",
        ]
        for number, item in enumerate(claims, start=1):
            lines += [
                f"### Claim {number}: `{item['claim_key']}`",
                "",
                f"- Sentence field: `{item['field']}`",
                f"- Sentence: {item['sentence']}",
                f"- Claim to assess: {item['claim']}",
                f"- Source: {item['source'] or 'No source recorded'}",
                f"- Supporting source span: {item['candidate_supporting_source_span']}",
                f"- Current automated status: {item['current_automated_status']}",
                f"- Existing human status: {item['existing_human_status']}",
                f"- Required owner action: {item['required_owner_action']}",
                f"- Content hash: `{item['content_hash']}`",
                "",
            ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    items = pending_items()
    args.output.write_text(render(items), encoding="utf-8")
    print(f"{len(items)} claims in {len({i['entry_id'] for i in items})} entries: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
