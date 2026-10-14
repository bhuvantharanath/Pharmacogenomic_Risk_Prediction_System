#!/usr/bin/env python3
"""The single authoritative release-readiness decision.

Detail tools report provenance and adjudication facts. Only this command may
combine those facts with the required test results and the exact candidate
artifact identity and emit release_ready.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from _common import REPO_ROOT, scrub
from compatible_bundle import hash_selected_files, load_hash_policy

sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.explanation import approval, static_store  # noqa: E402
from app.explanation.context import ExplanationContext  # noqa: E402
from app.models import Phenotype, RiskLabel  # noqa: E402
from app.retrieval import retrieve_mechanism  # noqa: E402


RELEASE_IDENTITY_EXTRAS = (
    "backend/app/data/compatible_bundle.json",
    "scripts/scientific_hash_policy.json",
    "scripts/application_hash_migration.json",
    "test-data/benchmark/current-candidate-2026-10-04/evaluation_manifest.json",
    "test-data/benchmark/current-candidate-2026-10-04/raw_benchmark_manifest.json",
    "test-data/benchmark/current-candidate-2026-10-04/external_benchmark_results.json",
    "test-data/benchmark/current-candidate-2026-10-04/input_eligibility.tsv",
    "test-data/benchmark/current-candidate-2026-10-04/exclusions.tsv",
    "test-data/benchmark/current-candidate-2026-10-04/discrepancies.tsv",
    "test-data/benchmark/current-candidate-2026-10-04/raw_scoring_report.md",
    "test-data/benchmark/current-candidate-2026-10-04/evaluation-comparison.json",
    "test-data/benchmark/current-candidate-2026-10-04/f4-fresh-replay.json",
    "test-data/benchmark/current-candidate-2026-10-04/stage-command-receipts.json",
    "test-data/benchmark/current-candidate-2026-10-04/EVALUATION-REPORT.md",
    "scripts/compatible_bundle.py",
    "scripts/verify_compatible_bundle.py",
    "scripts/release_status.py",
    ".github/workflows/deploy-web.yml",
)

REQUIRED_COMMANDS = (
    (
        "compatible-bundle",
        (sys.executable, "scripts/verify_compatible_bundle.py"),
        REPO_ROOT,
    ),
    ("backend-tests", (sys.executable, "-m", "pytest", "backend/tests", "-q"), REPO_ROOT),
    (
        "provenance",
        (sys.executable, "scripts/verify_provenance.py", "--no-report"),
        REPO_ROOT,
    ),
    (
        "label-mapping",
        (sys.executable, "scripts/validate_label_mapping.py"),
        REPO_ROOT,
    ),
    ("flutter-analyze", ("flutter", "analyze"), REPO_ROOT / "app"),
    ("flutter-tests", ("flutter", "test"), REPO_ROOT / "app"),
)


def candidate_artifact_hash(root: Path = REPO_ROOT) -> str:
    """Hash versioned release inputs with the same portable path encoding."""
    policy = load_hash_policy(root)
    paths = list(policy["core_paths"]) + list(RELEASE_IDENTITY_EXTRAS)
    return hash_selected_files(root, paths, "pharmaguard-release-artifact-v2")


def _json_detail(script: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {
            "status_error": f"{script} did not return JSON: {scrub(exc)}",
            "exit_code": result.returncode,
        }
    payload["exit_code"] = result.returncode
    return payload


def stored_runtime_decision(stored, manifest: approval.ApprovalManifest):
    """Ask the runtime approval function about this entry's own exact context."""
    try:
        label = (
            RiskLabel.SAFE
            if stored.derived_risk_label == "Safe"
            else RiskLabel(stored.derived_risk_label)
        )
        context = ExplanationContext(
            drug=stored.drug,
            gene=stored.gene,
            phenotype=Phenotype(stored.phenotype),
            risk_label=label,
            cpic_recommendation=stored.cpic_recommendation_used,
            mechanism=retrieve_mechanism(stored.gene, stored.drug),
        )
    except ValueError as exc:
        return approval.ApprovalDecision(
            False, f"Invalid stored context: {scrub(exc)}"
        )
    return approval.evaluate(stored, context, manifest)


def manifest_detail() -> dict:
    manifest = approval.load_manifest()
    store = static_store.load_store()
    problems: list[str] = []

    if manifest.load_error:
        problems.append(manifest.load_error)
    if store.load_error:
        problems.append(store.load_error)
    if not manifest.store_compatible:
        problems.append("approval manifest and explanation-store hashes differ")
    try:
        raw_manifest = json.loads(approval.DEFAULT_MANIFEST_PATH.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raw_manifest = {}
        problems.append(f"cannot inspect approval manifest policy: {scrub(exc)}")
    clinical_status = raw_manifest.get("clinical_expert_review")
    if clinical_status != approval.NO_EXPERT_REVIEW:
        problems.append("approval manifest makes an unsupported clinical-expert review claim")
    if len(manifest.records) != len(store.entries):
        problems.append("approval manifest does not cover every stored entry")

    decisions = []
    for stored in store.entries.values():
        record = manifest.get(stored.drug, stored.gene, stored.phenotype)
        if record is None:
            problems.append(
                f"missing manifest identity: {stored.drug}/{stored.gene}/{stored.phenotype}"
            )
            decisions.append(stored_runtime_decision(stored, manifest))
            continue
        if approval.content_hash(stored.explanation) != record.content_hash:
            problems.append(f"content hash mismatch: {stored.drug}/{stored.phenotype}")
        if approval.stored_source_hash(stored) != record.source_hash:
            problems.append(f"source hash mismatch: {stored.drug}/{stored.phenotype}")
        if approval.stored_context_hash(stored) != record.context_hash:
            problems.append(f"context hash mismatch: {stored.drug}/{stored.phenotype}")
        if record.status == approval.APPROVED and (
            not stored.guard_passed
            or not stored.is_provenance_verified
            or stored.review.clinical_expert_review
            or stored.review.clinical_expert_review_status
            != approval.NO_EXPERT_REVIEW
        ):
            problems.append(
                f"approved entry lacks required guard/provenance/review state: "
                f"{stored.drug}/{stored.phenotype}"
            )
        decisions.append(stored_runtime_decision(stored, manifest))

    counts = {
        state: sum(1 for record in manifest.records.values() if record.status == state)
        for state in (approval.APPROVED, approval.UNRESOLVED, approval.REJECTED)
    }
    releasable = sum(decision.approved for decision in decisions)
    approved = counts[approval.APPROVED]
    total = len(store.entries)
    human_bound = bool(releasable) and all(
        decision.record is not None
        and decision.record.review_kind == approval.AUTHOR_REVIEW
        and bool(decision.record.adjudicated_by)
        for decision in decisions
        if decision.approved
    )
    return {
        "compatible": not problems,
        "all_entries_approved": bool(total) and releasable == total,
        "approved_entries_human_bound": human_bound,
        "stored_generated_entries": total,
        "approved_generated_entries": approved,
        "unapproved_generated_entries": total - approved,
        "releasable_generated_entries": releasable,
        "fallback_only_cases": total - releasable,
        "human_review_complete_for_releasable_set": (
            all(
                decision.record is not None
                and decision.record.review_kind == approval.AUTHOR_REVIEW
                and bool(decision.record.adjudicated_by)
                for decision in decisions
                if decision.approved
            )
            if releasable
            else None
        ),
        "clinical_expert_review": clinical_status,
        "counts": counts,
        "store_sha256": manifest.actual_store_sha256,
        "manifest_store_sha256": manifest.store_sha256,
        "problems": problems,
    }


def compatible_bundle_detail() -> dict:
    """Return the exact scientific-bundle compatibility decision."""
    return _json_detail("verify_compatible_bundle.py")


def run_required_commands() -> list[dict]:
    results: list[dict] = []
    for name, command, cwd in REQUIRED_COMMANDS:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=1800,
            check=False,
        )
        output = (completed.stdout + "\n" + completed.stderr).strip()
        results.append(
            {
                "name": name,
                "passed": completed.returncode == 0,
                "exit_code": completed.returncode,
                "output_tail": output[-1200:],
            }
        )
        if completed.returncode != 0:
            break
    return results


def evaluate_release(
    *,
    required_checks: list[dict],
    adjudication: dict,
    review: dict,
    manifest: dict,
    compatible_bundle: dict,
    tested_artifact_hash: str,
    candidate_artifact_hash_value: str,
    tested_revision: str,
    candidate_revision: str,
) -> dict:
    checks_complete = (
        len(required_checks) == len(REQUIRED_COMMANDS)
        and all(check.get("passed") for check in required_checks)
    )
    prerequisites = {
        "required_checks_passed": checks_complete,
        "human_adjudication_complete": bool(
            adjudication.get("human_adjudication_complete")
        ),
        "no_rejected_or_outstanding_claims": (
            adjudication.get("rejected") == 0
            and adjudication.get("outstanding") == 0
        ),
        "provenance_complete": bool(review.get("provenance_complete")),
        "manifest_compatible": bool(manifest.get("compatible")),
        "scientific_bundle_compatible": bool(compatible_bundle.get("compatible")),
        "all_entries_approved": bool(manifest.get("all_entries_approved")),
        "approved_entries_human_bound": bool(
            manifest.get("approved_entries_human_bound")
        ),
        "artifact_hashes_match": bool(
            tested_artifact_hash
            and tested_artifact_hash == candidate_artifact_hash_value
        ),
        "candidate_revision_matches": bool(
            tested_revision and tested_revision == candidate_revision
        ),
        "no_clinical_expert_review_claim": (
            adjudication.get("clinical_expert_review")
            == approval.NO_EXPERT_REVIEW
            and review.get("clinical_expert_review")
            == approval.NO_EXPERT_REVIEW
        ),
    }
    ready = all(prerequisites.values())
    return {
        "release_ready": ready,
        "state": "ready" if ready else "not-ready",
        "declared_explanation_release_policy": "human_review_all_stored_generated_entries",
        "effective_explanation_mode": (
            "approved_static_with_template_fallback"
            if manifest.get("releasable_generated_entries", 0)
            else "deterministic_template_only"
        ),
        "approved_generated_entries": manifest.get("approved_generated_entries", 0),
        "unapproved_generated_entries": manifest.get("unapproved_generated_entries", 0),
        "releasable_generated_entries": manifest.get("releasable_generated_entries", 0),
        "fallback_only_cases": manifest.get("fallback_only_cases", 0),
        "human_review_complete_for_releasable_set": manifest.get(
            "human_review_complete_for_releasable_set"
        ),
        "clinical_expert_review": manifest.get(
            "clinical_expert_review", approval.NO_EXPERT_REVIEW
        ),
        "candidate_revision": candidate_revision,
        "tested_revision": tested_revision,
        "candidate_artifact_hash": candidate_artifact_hash_value,
        "tested_artifact_hash": tested_artifact_hash,
        "prerequisites": prerequisites,
        "required_checks": required_checks,
        "adjudication": adjudication,
        "review": review,
        "manifest": manifest,
        "compatible_bundle": compatible_bundle,
    }


def _revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-required", action="store_true")
    parser.add_argument(
        "--content-only",
        action="store_true",
        help="Check content prerequisites only; never reports final readiness.",
    )
    parser.add_argument("--candidate-sha", default=os.environ.get("GITHUB_SHA", ""))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    tested_hash = candidate_artifact_hash()
    tested_revision = _revision()
    checks = run_required_commands() if args.run_required else []
    candidate_hash = candidate_artifact_hash()
    candidate_revision = args.candidate_sha or tested_revision
    adjudication = _json_detail("adjudication_status.py")
    review = _json_detail("review_status.py")
    manifest = manifest_detail()
    compatible_bundle = compatible_bundle_detail()
    payload = evaluate_release(
        required_checks=checks,
        adjudication=adjudication,
        review=review,
        manifest=manifest,
        compatible_bundle=compatible_bundle,
        tested_artifact_hash=tested_hash,
        candidate_artifact_hash_value=candidate_hash,
        tested_revision=tested_revision,
        candidate_revision=candidate_revision,
    )

    content_ready = all(
        payload["prerequisites"][name]
        for name in (
            "human_adjudication_complete",
            "no_rejected_or_outstanding_claims",
            "provenance_complete",
            "manifest_compatible",
            "all_entries_approved",
            "approved_entries_human_bound",
            "no_clinical_expert_review_claim",
        )
    )
    payload["content_ready"] = content_ready
    if args.content_only:
        payload["release_ready"] = False
        payload["state"] = (
            "content-ready-not-release-attested" if content_ready else "not-ready"
        )

    if args.json:
        print(json.dumps(payload, indent=1))
    else:
        print("release status")
        print(f"  state                  {payload['state']}")
        print(f"  content ready          {content_ready}")
        print(f"  required checks        {payload['prerequisites']['required_checks_passed']}")
        print(f"  artifact hashes match  {payload['prerequisites']['artifact_hashes_match']}")
        print(f"  clinical expert review {approval.NO_EXPERT_REVIEW}")
        for name, passed in payload["prerequisites"].items():
            if not passed:
                print(f"  BLOCKED: {name}")

    return 0 if (content_ready if args.content_only else payload["release_ready"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
