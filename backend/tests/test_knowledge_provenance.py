"""
Which CPIC data a response was built from, identified by content (Phase 9 B2).

PharmCAT's `dataVersion` is a name. Two jars can carry the same name and
different tables, and a response that says only the name cannot be tied to the
data that was validated. Every response therefore carries SHA-256 hashes of the
jar's CPIC recommendation table and allele definitions, and these tests hold
them to two independent sources:

- the pinned jar itself, re-read here without going through the runner; and
- `backend/app/data/compatible_bundle.json`, the record of what was validated.

If either disagrees with what the API serves, the response is describing data
other than the data it claims (Part A verification edge E13).
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main
import app.pharmcat_runner as runner
from tests.conftest import REPO_ROOT

PINNED_JAR = REPO_ROOT / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
BUNDLE = REPO_ROOT / "backend/app/data/compatible_bundle.json"
WATCH_WORKFLOW = REPO_ROOT / ".github/workflows/knowledge-watch.yml"

client = TestClient(main.app)


def _independent_identity(jar: Path) -> dict[str, str]:
    """Recompute from the jar's bytes, sharing no code with the runner."""
    with zipfile.ZipFile(jar) as zf:
        guidance = hashlib.sha256(
            zf.read("org/pharmgkb/pharmcat/reporter/prescribing_guidance.json")
        ).hexdigest()
        definitions = sorted(
            n for n in zf.namelist()
            if n.startswith("org/pharmgkb/pharmcat/definition/alleles/")
            and n.endswith("_translation.json")
            and n.rsplit("/", 1)[1].split("_")[0] in {
                "CYP2C19", "CYP2C9", "CYP2D6", "CYP4F2", "DPYD",
                "NUDT15", "SLCO1B1", "TPMT", "VKORC1",
            }
        )
        lines = [f"{n} {hashlib.sha256(zf.read(n)).hexdigest()}" for n in definitions]
        versions = {json.loads(zf.read(n))["version"] for n in definitions}
    assert len(definitions) == 9, definitions
    return {
        "cpic_guidance_sha256": guidance,
        "allele_definitions_sha256": hashlib.sha256("\n".join(lines).encode()).hexdigest(),
        "allele_definitions_version": versions.pop() if len(versions) == 1 else "mixed",
    }


def _bundle_identity() -> dict[str, str]:
    """What the validated bundle says the same three values are."""
    pharmcat = json.loads(BUNDLE.read_text())["pharmcat"]
    lines = sorted(f"{d['member']} {d['sha256']}" for d in pharmcat["definitions"].values())
    return {
        "cpic_guidance_sha256": pharmcat["prescribing_guidance"]["sha256"],
        "allele_definitions_sha256": hashlib.sha256("\n".join(lines).encode()).hexdigest(),
        "allele_definitions_version": pharmcat["data_version"],
    }


@pytest.fixture(scope="module")
def jar_in_use() -> Path:
    jar = runner.find_jar()
    if jar is None:  # pragma: no cover — no jar in this environment
        pytest.skip("PharmCAT jar not found")
    return jar


def _served(body: dict) -> dict[str, str]:
    return {
        key: body[key]
        for key in ("cpic_guidance_sha256", "allele_definitions_sha256", "allele_definitions_version")
    }


# --------------------------------------------------------------------------- #
# AC1 — the served identity is the pinned, validated data
# --------------------------------------------------------------------------- #


def test_the_jar_in_use_is_the_pinned_jar(jar_in_use: Path) -> None:
    """Precondition for everything below: the runner resolves the validated jar."""
    pinned = json.loads(BUNDLE.read_text())["pharmcat"]["jar"]["sha256"]
    assert hashlib.sha256(jar_in_use.read_bytes()).hexdigest() == pinned


def test_provenance_serves_the_identity_recomputed_from_the_jar(jar_in_use: Path) -> None:
    body = client.get("/provenance").json()
    expected = _independent_identity(PINNED_JAR)

    assert _served(body) == expected
    # Positive control: the values are real hashes, not empty agreement.
    assert len(body["cpic_guidance_sha256"]) == 64
    assert len(body["allele_definitions_sha256"]) == 64
    assert body["allele_definitions_version"] == "2026-07-13-11-40"


def test_the_served_identity_is_the_one_the_bundle_validated(jar_in_use: Path) -> None:
    assert _served(client.get("/provenance").json()) == _bundle_identity()


def test_coverage_carries_the_same_identity(jar_in_use: Path, valid_vcf_bytes: bytes) -> None:
    response = client.post(
        "/coverage", files={"file": ("t.vcf", io.BytesIO(valid_vcf_bytes), "text/plain")}
    )
    assert response.status_code == 200
    assert _served(response.json()["guideline_provenance"]) == _bundle_identity()


def test_analyze_carries_the_same_identity(jar_in_use: Path, valid_vcf_bytes: bytes) -> None:
    response = client.post(
        "/analyze",
        files={"file": ("t.vcf", io.BytesIO(valid_vcf_bytes), "text/plain")},
        data={"drugs": "clopidogrel"},
    )
    if response.status_code == 503:  # pragma: no cover — PharmCAT not runnable
        pytest.skip("PharmCAT unavailable")
    assert response.status_code == 200, response.text[:300]
    provenance = response.json()["quality_metrics"]["guideline_provenance"]

    assert _served(provenance) == _bundle_identity()
    # The run's own data stamp and the definitions' stamp agree for this jar.
    assert provenance["cpic_data_version"] == provenance["allele_definitions_version"]


def test_no_pharmvar_release_is_invented() -> None:
    """PharmCAT 3.4.0 records none, so the field stays empty everywhere."""
    assert client.get("/provenance").json()["pharmvar_release"] == ""


# --------------------------------------------------------------------------- #
# Failure modes: provenance is metadata and must never break a response
# --------------------------------------------------------------------------- #


@pytest.fixture
def fresh_identity():
    runner.knowledge_identity.cache_clear()
    yield
    runner.knowledge_identity.cache_clear()


def test_no_jar_means_empty_fields_not_a_guess(
    monkeypatch: pytest.MonkeyPatch, fresh_identity
) -> None:
    monkeypatch.setattr(runner, "find_jar", lambda: None)
    body = client.get("/provenance").json()

    assert body["cpic_guidance_sha256"] == ""
    assert body["allele_definitions_sha256"] == ""
    assert body["allele_definitions_version"] == ""


def test_a_jar_without_the_expected_layout_means_empty_fields(
    monkeypatch: pytest.MonkeyPatch, fresh_identity, tmp_path: Path
) -> None:
    odd = tmp_path / "pharmcat-9.9.9-all.jar"
    with zipfile.ZipFile(odd, "w") as zf:
        zf.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")
    monkeypatch.setattr(runner, "find_jar", lambda: odd)

    response = client.get("/provenance")
    assert response.status_code == 200
    assert response.json()["cpic_guidance_sha256"] == ""


# --------------------------------------------------------------------------- #
# AC6 — the note says what is checked, and when
# --------------------------------------------------------------------------- #


def test_the_note_names_the_weekly_check_and_no_request_time_freshness() -> None:
    note = client.get("/provenance").json()["note"].lower()

    assert "does not monitor" not in note
    assert "weekly" in note
    assert "does not check" in note


def test_the_weekly_check_the_note_names_exists() -> None:
    """The note's claim is only true while the workflow exists and is scheduled."""
    workflow = WATCH_WORKFLOW.read_text()
    assert "schedule:" in workflow
    assert "cron:" in workflow
    assert "scripts/cpic_snapshot.py --check-live" in workflow
