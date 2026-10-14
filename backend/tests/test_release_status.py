"""Phase 3 regressions for the single authoritative release decision."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from app.explanation import approval, static_store
from tests.conftest import REPO_ROOT


SCRIPTS = REPO_ROOT / "scripts"


def _load(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


release_status = _load("release_status")


def _checks(passed: bool = True) -> list[dict]:
    return [
        {"name": name, "passed": passed, "exit_code": 0 if passed else 1}
        for name, _command, _cwd in release_status.REQUIRED_COMMANDS
    ]


def _evaluate(**overrides) -> dict:
    values = {
        "required_checks": _checks(),
        "adjudication": {
            "human_adjudication_complete": True,
            "rejected": 0,
            "outstanding": 0,
            "clinical_expert_review": "NOT_OBTAINED",
        },
        "review": {
            "provenance_complete": True,
            "clinical_expert_review": "NOT_OBTAINED",
        },
        "manifest": {
            "compatible": True,
            "all_entries_approved": True,
            "approved_entries_human_bound": True,
        },
        "compatible_bundle": {"compatible": True},
        "tested_artifact_hash": "artifact",
        "candidate_artifact_hash_value": "artifact",
        "tested_revision": "candidate",
        "candidate_revision": "candidate",
    }
    values.update(overrides)
    return release_status.evaluate_release(**values)


def _script_json(name: str, *args: str) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args, "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    return result.returncode, json.loads(result.stdout)


def test_only_authoritative_tool_emits_release_ready() -> None:
    _adj_code, adjudication = _script_json("adjudication_status.py")
    _review_code, review = _script_json("review_status.py")
    release_code, release = _script_json("release_status.py", "--content-only")

    assert "release_ready" not in adjudication
    assert "release_ready" not in review
    assert adjudication["state"] not in {"ready", "not-ready"}
    assert release["release_ready"] is False
    assert release["adjudication"]["human_adjudication_complete"] is False
    assert release_code == 1


def test_deliberately_failing_required_gate_blocks_release() -> None:
    checks = _checks()
    checks[0] = {**checks[0], "passed": False, "exit_code": 1}

    result = _evaluate(required_checks=checks)

    assert result["release_ready"] is False
    assert result["prerequisites"]["required_checks_passed"] is False


def test_incompatible_scientific_bundle_blocks_release() -> None:
    result = _evaluate(compatible_bundle={"compatible": False})

    assert result["release_ready"] is False
    assert result["prerequisites"]["scientific_bundle_compatible"] is False


def test_deploy_jobs_depend_on_the_authoritative_gate() -> None:
    workflow = (REPO_ROOT / ".github/workflows/deploy-web.yml").read_text()
    assert "release-gate:" in workflow
    assert "python scripts/release_status.py --run-required" in workflow
    backend_job = workflow.split("\n  backend:", 1)[1].split("\n  deploy:", 1)[0]
    assert "needs: release-gate" in backend_job


def test_tested_and_candidate_artifact_hash_must_match() -> None:
    assert _evaluate()["release_ready"] is True
    mismatch = _evaluate(candidate_artifact_hash_value="different")
    assert mismatch["release_ready"] is False
    assert mismatch["prerequisites"]["artifact_hashes_match"] is False


def test_checked_manifest_is_reproducible_and_hash_compatible() -> None:
    builder = _load("build_explanation_approvals")
    checked = json.loads(
        (REPO_ROOT / "backend/app/data/explanation_approvals.json").read_text()
    )

    assert builder.build() == checked
    detail = release_status.manifest_detail()
    assert detail["compatible"] is True
    assert detail["store_sha256"] == detail["manifest_store_sha256"]
    assert detail["counts"] == {
        "approved": 0,
        "unresolved": 20,
        "rejected": 0,
    }
    assert detail["approved_generated_entries"] == 0
    assert detail["unapproved_generated_entries"] == 20
    assert detail["releasable_generated_entries"] == 0
    assert detail["fallback_only_cases"] == 20
    assert detail["human_review_complete_for_releasable_set"] is None


def test_gate_and_runtime_use_same_stored_eligibility(
    monkeypatch,
) -> None:
    manifest = approval.load_manifest()
    stored = next(iter(static_store.load_store().entries.values()))
    record = manifest.get(stored.drug, stored.gene, stored.phenotype)
    assert record is not None
    approved = replace(
        record,
        status=approval.APPROVED,
        review_kind=approval.AUTHOR_REVIEW,
        adjudicated_by=("Synthetic reviewer in test only",),
    )
    test_manifest = replace(manifest, records={**manifest.records, approved.key: approved})
    monkeypatch.setattr(approval, "load_manifest", lambda: test_manifest)

    assert release_status.stored_runtime_decision(stored, test_manifest).approved
    detail = release_status.manifest_detail()
    assert detail["approved_generated_entries"] == 1
    assert detail["releasable_generated_entries"] == 1
    assert detail["fallback_only_cases"] == 19
    assert detail["all_entries_approved"] is False


@pytest.mark.parametrize(
    "mutated_field", ["content_hash", "source_hash", "context_hash"]
)
def test_mutated_approved_identity_blocks_gate(monkeypatch, mutated_field: str) -> None:
    manifest = approval.load_manifest()
    stored = next(iter(static_store.load_store().entries.values()))
    record = manifest.get(stored.drug, stored.gene, stored.phenotype)
    assert record is not None
    invalid = replace(
        record,
        status=approval.APPROVED,
        review_kind=approval.AUTHOR_REVIEW,
        adjudicated_by=("Synthetic reviewer in test only",),
        **{mutated_field: "0" * 64},
    )
    test_manifest = replace(manifest, records={**manifest.records, invalid.key: invalid})
    monkeypatch.setattr(approval, "load_manifest", lambda: test_manifest)

    assert not release_status.stored_runtime_decision(stored, test_manifest).approved
    detail = release_status.manifest_detail()
    assert detail["compatible"] is False
    assert detail["releasable_generated_entries"] == 0
    assert any(f"{mutated_field.split('_')[0]} hash mismatch" in problem for problem in detail["problems"])


def test_release_status_describes_fallback_without_declaring_release_ready() -> None:
    result = _evaluate(
        manifest={
            "compatible": True,
            "all_entries_approved": False,
            "approved_entries_human_bound": False,
            "approved_generated_entries": 0,
            "unapproved_generated_entries": 20,
            "releasable_generated_entries": 0,
            "fallback_only_cases": 20,
            "human_review_complete_for_releasable_set": None,
            "clinical_expert_review": "NOT_OBTAINED",
        }
    )

    assert result["effective_explanation_mode"] == "deterministic_template_only"
    assert result["declared_explanation_release_policy"] == (
        "human_review_all_stored_generated_entries"
    )
    assert result["release_ready"] is False


def test_owner_review_packet_lists_pending_claims_without_deciding_them() -> None:
    packet = _load("build_release_review_packet")
    items = packet.pending_items()
    rendered = packet.render(items)

    assert len(items) == 55
    assert len({item["entry_id"] for item in items}) == 20
    assert sum(item["current_automated_status"] == "automated decision" for item in items) == 36
    assert sum("unresolved" in item["status"] for item in items) == 19
    assert all(item["content_hash"] and item["required_owner_action"] for item in items)
    assert "No decision or clinical expert approval is recorded" in rendered
    assert (REPO_ROOT / "reports/release_content_review.md").read_text() == rendered
