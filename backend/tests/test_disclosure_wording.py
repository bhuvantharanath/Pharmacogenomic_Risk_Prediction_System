"""
Disclosure wording has to describe what the system actually does.

Each case below was reproduced through the real local API, browser, JSON export
and printed PDF on 2026-10-14
(`audit-output/2026-10-14-prompt8-4da1199df2/DEFECTS.md`):

* Automated provenance described as a guarantee. The per-result disclaimer and
  the analysis warning said every clinical statement is machine-verified and
  that this "checks that nothing was invented", while the same responses were
  served by the deterministic template (`source=template`), which no provenance
  check reads, and `scripts/verify_provenance.py` documents itself as a filter
  that cannot detect a reversed claim. Automated checks must not be presented
  as human review or as proof that invented content is impossible.
* An application limit presented as a file-format limit. CYP2D6 readiness said a
  VCF "cannot express" copy-number and structural variation and that "no VCF
  will resolve it". VCF 4.3 section 5.3 defines structural-variant and
  copy-number records; the limit is that this application does not call CYP2D6
  from an uploaded VCF.
* An upstream hazard presented as this application's output. The variants-only
  warning said the consequence "is NOT a missing result" without saying that
  this application reports those genes as Unknown — which the same response does.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app import coverage, main
from app.models import DISCLAIMER
from app.pharmcat_models import PharmcatReport

#: Phrases that turn an automated provenance filter into a guarantee.
OVERCLAIMS = (
    "nothing was invented",
    "invented nothing",
    "every clinical statement is machine",
    "machine-verified to come from",
    "machine-verified to trace",
    "writes no clinical content of its own",
)

#: Phrases that attribute this application's CYP2D6 limit to the VCF format.
FORMAT_CLAIMS = (
    "cannot express",
    "cannot represent",
    "no vcf will resolve",
    "cannot be read from any vcf",
    "no way to express",
)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, cyp2c19_pm_report: PharmcatReport):
    async def fake_run_pharmcat(vcf_text: str, *, sample_hint: str = "sample"):
        return cyp2c19_pm_report

    monkeypatch.setattr(main, "run_pharmcat", fake_run_pharmcat)
    return TestClient(main.app)


def _post(client: TestClient, path: str, content: bytes, drugs: str | None = None):
    return client.post(
        path,
        files={"file": ("test.vcf", io.BytesIO(content), "text/plain")},
        data={"drugs": drugs} if drugs else {},
    )


def test_disclaimer_bounds_automated_checks() -> None:
    text = DISCLAIMER.lower()
    for phrase in OVERCLAIMS:
        assert phrase not in text, f"disclaimer overclaims: {phrase!r}"
    assert "no qualified clinical expert has reviewed" in text
    assert "cpic" in text
    # The automated check is named for what it is, not offered in place of review.
    assert "not human review" in text
    assert "correct for you" in text


def test_analysis_response_does_not_overclaim_provenance(
    client: TestClient, valid_vcf_bytes: bytes
) -> None:
    body = _post(client, "/analyze", valid_vcf_bytes, "clopidogrel,codeine").json()
    warnings = " ".join(body["quality_metrics"]["warnings"]).lower()
    for phrase in OVERCLAIMS:
        assert phrase not in warnings, f"analysis warning overclaims: {phrase!r}"
    assert "not human review" in warnings
    for analysis in body["analyses"]:
        disclaimer = analysis["llm_generated_explanation"]["disclaimer"].lower()
        for phrase in OVERCLAIMS:
            assert phrase not in disclaimer, f"{analysis['drug']} disclaimer overclaims: {phrase!r}"


def test_cyp2d6_reason_names_the_application_boundary(valid_vcf_bytes: bytes) -> None:
    reason = coverage.NOT_READABLE_FROM_VCF["CYP2D6"].lower()
    for phrase in FORMAT_CLAIMS:
        assert phrase not in reason, f"CYP2D6 reason blames the file format: {phrase!r}"
    assert "this application" in reason

    reported = next(
        g
        for g in TestClient(main.app)
        .post("/coverage", files={"file": ("t.vcf", io.BytesIO(valid_vcf_bytes), "text/plain")})
        .json()["genes"]
        if g["gene"] == "CYP2D6"
    )
    assert reported["not_readable_from_vcf"] is True
    assert reported["reason"] == coverage.NOT_READABLE_FROM_VCF["CYP2D6"]


def test_variants_only_warning_states_that_this_application_withholds() -> None:
    message = coverage.variants_only_warning()
    lower = message.lower()
    # The hazard is still named — and attributed to callers that read an
    # absent position as reference — and the application's own behaviour is stated.
    assert "confident WRONG result" in message
    assert "genotype caller" in lower
    assert "this application" in lower
    assert "unknown" in lower
