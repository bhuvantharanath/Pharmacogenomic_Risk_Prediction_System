"""Portable scientific identity regressions for hash policy v2."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT


SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("compatible_bundle", SCRIPTS / "compatible_bundle.py")
assert SPEC and SPEC.loader
bundle = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bundle
SPEC.loader.exec_module(bundle)
import release_status  # noqa: E402


def _copy_file(root: Path, relative: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / relative, target)


@pytest.fixture
def clean_core(tmp_path: Path) -> Path:
    root = tmp_path / "clean-core"
    for relative in bundle.load_hash_policy()["core_paths"]:
        _copy_file(root, relative)
    _copy_file(root, "scripts/scientific_hash_policy.json")
    return root


def test_clean_scientific_tree_reproduces_candidate_hash(clean_core: Path) -> None:
    assert bundle.application_core_hash(clean_core) == bundle.application_core_hash()


@pytest.mark.parametrize(
    "relative",
    [
        "backend/app/.DS_Store",
        "backend/app/main.py~",
        "backend/app/__pycache__/main.cpython-311.pyc",
        "backend/app/pharmcat.log",
        "backend/app/data/temporary.tmp",
        "backend/app/data/unrelated_local.json",
    ],
)
def test_filesystem_junk_does_not_change_hash(clean_core: Path, relative: str) -> None:
    before = bundle.application_core_hash(clean_core)
    target = clean_core / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"local filesystem artifact")
    assert bundle.application_core_hash(clean_core) == before


@pytest.mark.parametrize(
    "relative",
    [
        "backend/app/cpic_engine.py",
        "backend/app/data/capabilities.json",
        "backend/app/data/position_requirements.json",
        "backend/app/data/explanations.json",
    ],
)
def test_scientific_change_alters_hash(clean_core: Path, relative: str) -> None:
    before = bundle.application_core_hash(clean_core)
    target = clean_core / relative
    target.write_bytes(target.read_bytes() + b"\n")
    assert bundle.application_core_hash(clean_core) != before


def test_same_files_in_different_parent_directories_match(clean_core: Path, tmp_path: Path) -> None:
    other = tmp_path / "another-parent" / "same-core"
    shutil.copytree(clean_core, other)
    assert bundle.application_core_hash(clean_core) == bundle.application_core_hash(other)


def test_release_artifact_identity_ignores_junk_and_parent_path(tmp_path: Path) -> None:
    root = tmp_path / "candidate"
    for relative in set(bundle.load_hash_policy()["core_paths"]) | set(release_status.RELEASE_IDENTITY_EXTRAS):
        _copy_file(root, relative)
    before = release_status.candidate_artifact_hash(root)
    extra = root / "backend/app/.DS_Store"
    extra.write_bytes(b"Finder metadata")
    assert release_status.candidate_artifact_hash(root) == before
    other = tmp_path / "another-parent" / "candidate"
    shutil.copytree(root, other)
    assert release_status.candidate_artifact_hash(other) == before


def test_unlisted_source_is_ignored_until_policy_enrolls_it(clean_core: Path) -> None:
    before = bundle.application_core_hash(clean_core)
    (clean_core / "backend/app/new_interpreter.py").write_text("pass\n")
    assert bundle.application_core_hash(clean_core) == before
    policy_path = clean_core / "scripts/scientific_hash_policy.json"
    policy = json.loads(policy_path.read_text())
    policy["core_paths"].append("backend/app/new_interpreter.py")
    policy["core_paths"].sort()
    policy_path.write_text(json.dumps(policy))
    assert bundle.application_core_hash(clean_core) != before


def test_symlinked_scientific_input_fails_closed(clean_core: Path) -> None:
    original = clean_core / "backend/app/cpic_engine.py"
    alternate = clean_core / "external-copy.py"
    alternate.write_bytes(original.read_bytes())
    original.unlink()
    original.symlink_to(alternate)
    with pytest.raises(ValueError, match="non-regular scientific input"):
        bundle.application_core_hash(clean_core)


def test_clean_isolated_copy_passes_bundle_verification(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "clean-copy"
    required = set(bundle.load_hash_policy()["core_paths"])
    required.update(
        {
            "scripts/scientific_hash_policy.json",
            "scripts/application_hash_migration.json",
            "backend/app/data/compatible_bundle.json",
            "test-data/reference/tools/pharmcat-3.4.0-all.jar",
            "test-data/reference/tools/pharmcat_positions_3.4.0.vcf.bgz",
            "test-data/reference/tools/pharmcat_positions_3.4.0.vcf.bgz.csi",
            "test-data/benchmark/external/protocol.json",
            "test-data/benchmark/external/cohort_lock.json",
            "test-data/benchmark/external/Consolidated_PGx-HLA_table_1-22-25-V4.xlsx",
            "test-data/benchmark/external/genomic/locked_cohort.vcf.gz",
            "test-data/benchmark/external/benchmark_manifest.json",
            "test-data/benchmark/external/external_benchmark_results.json",
            "test-data/benchmark/external/pharmcat_report_manifest.json",
            "test-data/benchmark/external/sample_gene_truth.tsv",
            "reports/external_analytical_benchmark.md",
            "reports/scientific_record_reproduction.json",
            "backend/requirements.txt",
            "backend/requirements-dev.txt",
            ".github/workflows/test.yml",
        }
    )
    required.update(
        str(path.relative_to(REPO_ROOT))
        for path in (REPO_ROOT / "test-data/benchmark/current-candidate-2026-10-14").iterdir()
        if path.is_file()
    )
    for relative in sorted(required):
        _copy_file(root, relative)
    assert not (root / "backend/app/.DS_Store").exists()
    monkeypatch.setattr(bundle, "REPO_ROOT", root)
    monkeypatch.setattr(bundle, "MANIFEST_PATH", root / "backend/app/data/compatible_bundle.json")
    monkeypatch.setattr(bundle, "JAR_PATH", root / "test-data/reference/tools/pharmcat-3.4.0-all.jar")

    result = bundle.verify_manifest(root / "backend/app/data/compatible_bundle.json")
    assert result["compatible"] is True, result["problems"]


def test_explanation_content_changes_its_component_identity(clean_core: Path) -> None:
    relative = "backend/app/data/explanations.json"
    target = clean_core / relative
    original = bundle.sha256(target)
    payload = json.loads(target.read_text())
    payload["explanations"][0]["explanation"]["summary"] += " changed"
    target.write_text(json.dumps(payload))
    assert bundle.sha256(target) != original
