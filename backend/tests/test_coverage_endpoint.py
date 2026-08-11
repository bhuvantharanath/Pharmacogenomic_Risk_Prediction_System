"""
POST /coverage — the readiness preview, and the promises it has to keep.

WHY THIS ENDPOINT IS TESTED SEPARATELY FROM THE GATE

`test_coverage_gate.py` verifies the arithmetic: does a gene at 79% of an 80%
threshold get gated. This file verifies the *contract* around that arithmetic,
which is where a preview can go wrong in ways the gate cannot see:

  - it must reach the same verdict /analyze would, or a user acts on a promise
    the analysis then breaks;
  - it must accept exactly what /analyze accepts, or the preview rejects files
    that would have worked;
  - it must not run PharmCAT, or it is not a cheap preview at all;
  - it must leave nothing on disk, same as /analyze.

The last two are the ones that decay silently. Nothing about a slow endpoint
that writes temp files looks wrong in a response body.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import coverage
from app.main import app

client = TestClient(app)


def _vcf(rows: list[tuple[str, int, str]]) -> bytes:
    head = ["##fileformat=VCFv4.2", "##reference=GRCh38",
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE"]
    body = [f"{c}\t{p}\t.\tA\tG\t.\tPASS\t.\tGT\t{gt}" for c, p, gt in rows]
    return ("\n".join(head + body) + "\n").encode()


def _positions(gene: str) -> list[tuple[str, int]]:
    return [(c, p) for c, p in coverage.load_requirements()["genes"][gene]["positions"]]


def _at_coverage(gene: str, fraction: float, genotype: str = "0/0") -> bytes:
    pos = _positions(gene)
    return _vcf([(c, p, genotype) for c, p in pos[: max(0, round(len(pos) * fraction))]])


def _post(payload: bytes, name: str = "sample.vcf"):
    return client.post("/coverage", files={"file": (name, payload, "text/plain")})


def _gene(body: dict, symbol: str) -> dict:
    return next(g for g in body["genes"] if g["gene"] == symbol)


GATED_GENES = ("CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "NUDT15", "DPYD")


# --------------------------------------------------------------------------- #
# Thresholds — the preview must agree with the gate, per gene
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("gene", GATED_GENES)
def test_at_the_threshold_the_gene_passes(gene: str) -> None:
    spec = coverage.load_requirements()["genes"][gene]
    minimum = spec["min_coverage_percent"]

    # For an enforced gene the preview must report the COMBINED rule, or it
    # promises an answer the analysis then declines to give — the exact drift
    # this file exists to catch.
    if spec.get("decision_critical_enforced"):
        critical = [(c, p) for c, p in spec["decision_critical_positions"]]
        others = [(c, p) for c, p in spec["positions"]
                  if (c, p) not in set(critical)]
        full = _post(_vcf([(c, p, "0/0") for c, p in critical + others])).json()
        assert _gene(full, gene)["passes"] is True

        need = max(0, round(len(spec["positions"]) * minimum / 100))
        thin = _post(_vcf([(c, p, "0/0") for c, p in others[:need]])).json()
        reported = _gene(thin, gene)
        assert reported["percent"] >= minimum, "test premise: it clears the bar"
        assert reported["passes"] is False
        return
    body = _post(_at_coverage(gene, minimum / 100)).json()
    reported = _gene(body, gene)
    assert reported["passes"] is True, reported
    assert reported["percent"] >= minimum
    # A passing gene explains nothing, because there is nothing to explain.
    assert reported["reason"] == ""


@pytest.mark.parametrize("gene", GATED_GENES)
def test_just_below_the_threshold_the_gene_fails_and_says_why(gene: str) -> None:
    spec = coverage.load_requirements()["genes"][gene]
    minimum = spec["min_coverage_percent"]
    # One position short of the bar, whatever the gene's position count.
    keep = max(0, -1 + int(len(spec["positions"]) * minimum / 100))
    pos = _positions(gene)
    body = _post(_vcf([(c, p, "0/0") for c, p in pos[:keep]])).json()
    reported = _gene(body, gene)

    assert reported["passes"] is False, reported
    # The reason must carry the numbers, not just a verdict: "4 of 35" tells a
    # user whether re-calling will help; "insufficient coverage" does not.
    assert str(reported["positions_found"]) in reported["reason"]
    assert str(reported["positions_required"]) in reported["reason"]
    assert str(minimum) in reported["reason"]


@pytest.mark.parametrize("gene", GATED_GENES)
def test_full_coverage_always_passes(gene: str) -> None:
    assert _gene(_post(_at_coverage(gene, 1.0)).json(), gene)["passes"] is True


def test_preview_and_analysis_thresholds_come_from_the_same_place() -> None:
    """
    Sabotage check. If /coverage grew its own copy of the thresholds, this drifts
    the moment someone edits one file and not the other — and the user would be
    promised an answer the analysis then declines to give.
    """
    body = _post(_at_coverage("CYP2C19", 1.0)).json()
    on_disk = coverage.load_requirements()["genes"]
    for reported in body["genes"]:
        spec = on_disk[reported["gene"]]
        assert reported["threshold_percent"] == spec["min_coverage_percent"]
        assert reported["positions_required"] == len(spec["positions"])


# --------------------------------------------------------------------------- #
# CYP2D6 — a limit of the format, not a deficiency of the file
# --------------------------------------------------------------------------- #


def test_cyp2d6_is_never_reported_as_a_coverage_failure() -> None:
    """
    Even at 100% of its positions, CYP2D6 cannot be called from a VCF: it is
    defined by copy number and structural variation. Reporting it as a coverage
    shortfall would tell a user to re-call their file, which will never work.
    """
    reported = _gene(_post(_at_coverage("CYP2D6", 1.0)).json(), "CYP2D6")

    assert reported["not_readable_from_vcf"] is True
    assert reported["passes"] is False
    # The reason must point at the assay, not at the upload.
    assert "no VCF will resolve it" in reported["reason"]
    assert "required positions were reported" not in reported["reason"]


# --------------------------------------------------------------------------- #
# The drug partition
# --------------------------------------------------------------------------- #


def test_every_drug_lands_on_exactly_one_side() -> None:
    body = _post(_at_coverage("CYP2C19", 1.0)).json()
    answerable, unanswerable = body["answerable_drugs"], body["unanswerable_drugs"]

    assert set(answerable).isdisjoint(unanswerable)
    assert answerable, "a fully-covered CYP2C19 must answer something"
    # Total: a drug silently missing from both lists is a drug the user is never
    # told about, which is the failure this endpoint exists to prevent.
    from app import cpic_engine

    known = set(cpic_engine.load_mapping().get("drug_primary_gene", {}))
    assert set(answerable) | set(unanswerable) == known


def test_a_file_that_answers_nothing_says_so_rather_than_erroring() -> None:
    """An unusable file is a 200 with an honest census, not a 4xx."""
    body = _post(_vcf([("chr1", 100, "0/0")])).json()
    assert body["genes_passing"] == 0
    assert body["answerable_drugs"] == []
    assert body["unanswerable_drugs"]


def test_variants_only_input_is_flagged_with_the_warning_analyze_uses() -> None:
    pos = _positions("CYP2C19")
    body = _post(_vcf([(c, p, "0/1") for c, p in pos])).json()

    assert body["variants_only"] is True
    assert any("variants-only" in w for w in body["warnings"])


# --------------------------------------------------------------------------- #
# Same door as /analyze
# --------------------------------------------------------------------------- #


def test_a_file_analyze_would_reject_is_rejected_here_too() -> None:
    """
    Identical validation, so the preview never green-lights a file the analysis
    refuses. Both go through `_read_and_validate`; this asserts the codes match
    rather than merely that both fail.
    """
    junk = b"this is not a VCF\n"
    preview = _post(junk)
    analysis = client.post(
        "/analyze",
        files={"file": ("sample.vcf", junk, "text/plain")},
        data={"drugs": "clopidogrel"},
    )

    assert preview.status_code == analysis.status_code == 400
    assert preview.json()["error_code"] == analysis.json()["error_code"]


def test_an_oversized_upload_is_refused_before_it_is_parsed() -> None:
    from app.vcf_validation import MAX_UPLOAD_BYTES

    response = _post(b"#" * (MAX_UPLOAD_BYTES + 1))
    assert response.status_code == 413
    assert response.json()["error_code"] == "FILE_TOO_LARGE"


# --------------------------------------------------------------------------- #
# The two promises that decay silently
# --------------------------------------------------------------------------- #


def test_the_preview_does_not_invoke_pharmcat(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The whole value of this endpoint is that it is cheap. If it ever starts a
    JVM, it is no longer a preview — so make invoking PharmCAT an outright error
    rather than trusting the response time to reveal it.
    """
    def _explode(*_args, **_kwargs):  # pragma: no cover — must never run
        raise AssertionError("/coverage invoked PharmCAT")

    monkeypatch.setattr("app.main.run_pharmcat", _explode)
    monkeypatch.setattr("app.main.resolve_invoker", _explode)

    assert _post(_at_coverage("CYP2C19", 1.0)).status_code == 200


def test_the_preview_leaves_nothing_on_disk(monkeypatch: pytest.MonkeyPatch,
                                            tmp_path: Path) -> None:
    """
    Same retention guarantee as /analyze. Genomic data is the one thing this
    project promises never to persist, and a preview handles exactly the same
    upload as the analysis.

    Asserted against a temp root of our own rather than by counting entries in
    the shared one, which other processes write to.
    """
    private = tmp_path / "tmproot"
    private.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(private))

    assert _post(_at_coverage("CYP2C9", 1.0)).status_code == 200
    assert list(private.iterdir()) == [], "the coverage path wrote to disk"


# --------------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------------- #


def test_the_preview_names_the_pinned_version_and_claims_no_data_bundle() -> None:
    """
    /coverage has not run PharmCAT, so it has not observed a data version. It
    reports the pinned release and leaves the bundle stamp empty rather than
    quoting a date it did not read — an unverified date is worse than none.
    """
    from app.pharmcat_runner import PINNED_VERSION

    provenance = _post(_at_coverage("CYP2C19", 1.0)).json()["guideline_provenance"]

    assert provenance["pharmcat_version"] == PINNED_VERSION
    assert provenance["cpic_data_version"] == ""
    assert provenance["explanations_generated_at"]


def test_provenance_never_claims_to_detect_staleness() -> None:
    """
    A date stamp is honest; "up to date" would be a claim this build cannot
    support, because it does not monitor CPIC. Guard the wording.
    """
    note = _post(_at_coverage("CYP2C19", 1.0)).json()["guideline_provenance"]["note"]
    lowered = note.lower()

    assert "does not monitor" in lowered
    for forbidden in ("up to date", "up-to-date", "current as of", "latest"):
        assert forbidden not in lowered, f"provenance note claims freshness: {note!r}"


def test_provenance_is_reachable_without_an_upload() -> None:
    """
    GET /provenance exists so the About screen can state the version with
    nothing uploaded. The version behind an answer is a property of the build,
    not of the file, so requiring a VCF to learn it would be backwards.
    """
    response = client.get("/provenance")

    assert response.status_code == 200
    body = response.json()
    assert body["pharmcat_version"]
    assert body["explanations_generated_at"]


def test_a_real_run_reports_the_versions_it_observed(
    client_fixture_free_vcf: bytes,
) -> None:
    """
    /analyze has run PharmCAT, so it reports what that run said — including the
    data-bundle stamp /coverage cannot know. A pinned constant here would be a
    claim about the build rather than a fact about the result.
    """
    response = client.post(
        "/analyze",
        files={"file": ("sample.vcf", client_fixture_free_vcf, "text/plain")},
        data={"drugs": "clopidogrel"},
    )
    if response.status_code == 503:  # pragma: no cover — no jar in this env
        pytest.skip("PharmCAT unavailable")

    provenance = response.json()["quality_metrics"]["guideline_provenance"]
    assert provenance["pharmcat_version"]
    # Observed, not pinned: a real report always carries a data version.
    assert provenance["cpic_data_version"]


@pytest.fixture
def client_fixture_free_vcf() -> bytes:
    return _at_coverage("CYP2C19", 1.0)


def test_provenance_survives_a_missing_explanation_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provenance is metadata. It must never be the reason a response fails."""
    import app.main as main

    monkeypatch.setattr(main, "Path", None)  # any breakage inside the helper
    provenance = main.guideline_provenance()

    assert provenance.explanations_generated_at == ""
    assert provenance.pharmcat_version
