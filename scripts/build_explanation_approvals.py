#!/usr/bin/env python3
"""Build the exact-content approval manifest from recorded adjudications.

This does not approve anything. It projects the decisions already present in
explanations.json into the runtime manifest. Missing, escalated, rejected, or
automated decisions remain non-approved.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

from _common import EXPLANATIONS_PATH, REPO_ROOT, load_json, write_json_atomic

sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.explanation.approval import (  # noqa: E402
    APPROVED,
    AUTHOR_REVIEW,
    NO_EXPERT_REVIEW,
    REJECTED,
    UNRESOLVED,
    content_hash,
    file_sha256,
    semantic_context_hash,
    source_hash,
)
from app.retrieval import retrieve_mechanism  # noqa: E402


TARGET = REPO_ROOT / "backend/app/data/explanation_approvals.json"
SCRIPTS = REPO_ROOT / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _status(
    entry: dict,
    items: list[dict],
) -> tuple[str, str, list[str]]:
    records = entry.get("provenance_adjudications") or {}
    people: set[str] = set()
    problems: list[str] = []
    rejected = False

    for item in items:
        record = records.get(item["key"])
        if record is None or (record.get("escalated") and not record.get("decision")):
            problems.append("unresolved adjudication")
            continue
        if record.get("decision") == "rejected":
            rejected = True
            problems.append("rejected sentence remains in content")
            continue
        who = str(record.get("adjudicated_by") or "").strip()
        if who.lower() == "automated":
            problems.append("automated decision awaiting human adjudication")
            continue
        if record.get("decision") not in {"accepted", "edited"} or not who:
            problems.append("incomplete adjudication record")
            continue
        people.add(who)

    review = entry.get("review") or {}
    if not review.get("provenance_verified"):
        problems.append("provenance is not verified")
    if not (entry.get("guard_report") or {}).get("passed"):
        problems.append("generation guard did not pass")
    if review.get("clinical_expert_review"):
        problems.append("unsupported clinical-expert review claim")
    if review.get("clinical_expert_review_status") != NO_EXPERT_REVIEW:
        problems.append("clinical-expert review status is not NOT_OBTAINED")

    if rejected:
        return REJECTED, "; ".join(sorted(set(problems))), sorted(people)
    if problems:
        return UNRESOLVED, "; ".join(sorted(set(problems))), sorted(people)
    return APPROVED, "Every claim was adjudicated by a named person.", sorted(people)


def build(source: Path = EXPLANATIONS_PATH) -> dict:
    vp = _load("verify_provenance")
    adjudicate = _load("adjudicate")
    store = load_json(source)
    entries = store.get("explanations") or []
    items = adjudicate.collect_flagged(vp, entries, include_all=True)
    by_case: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_case[item["case"]].append(item)

    manifest_entries = []
    for entry in entries:
        case = f"{entry['drug']}:{entry['phenotype']}"
        status, reason, people = _status(entry, by_case[case])
        mechanism = retrieve_mechanism(entry.get("gene"), entry["drug"])
        manifest_entries.append(
            {
                "drug": entry["drug"].strip().lower(),
                "gene": str(entry.get("gene") or "").strip().upper(),
                "phenotype": entry["phenotype"],
                "status": status,
                "content_hash": content_hash(entry.get("explanation") or {}),
                "source_hash": source_hash(
                    str(entry.get("cpic_recommendation_used") or ""),
                    str(entry.get("mechanism_source") or ""),
                    mechanism.snippet() if mechanism else "",
                    mechanism.source_url if mechanism else "",
                ),
                "context_hash": semantic_context_hash(
                    drug=entry["drug"],
                    gene=entry.get("gene"),
                    phenotype=entry["phenotype"],
                    risk_label=str(entry.get("derived_risk_label") or ""),
                ),
                "review_kind": (
                    AUTHOR_REVIEW if status == APPROVED else "incomplete_or_automated"
                ),
                "adjudicated_by": people,
                "clinical_expert_review_status": NO_EXPERT_REVIEW,
                "reason": reason,
            }
        )

    counts = {
        state: sum(1 for entry in manifest_entries if entry["status"] == state)
        for state in (APPROVED, UNRESOLVED, REJECTED)
    }
    return {
        "version": 1,
        "store_sha256": file_sha256(source),
        "policy": (
            "Exact content/source/context approval by named project-author "
            "provenance adjudication; not clinical expert review."
        ),
        "clinical_expert_review": NO_EXPERT_REVIEW,
        "counts": counts,
        "entries": manifest_entries,
    }


def main() -> int:
    payload = build()
    write_json_atomic(TARGET, payload)
    print(json.dumps(payload["counts"], sort_keys=True))
    print(TARGET.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
