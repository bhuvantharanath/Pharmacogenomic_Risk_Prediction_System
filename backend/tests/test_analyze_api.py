"""
End-to-end tests for POST /analyze.

PharmCAT itself is stubbed out with a checked-in report fixture, so these run
anywhere. What they exercise for real: validation, the label-mapping engine,
response assembly, and — importantly — that the JSON stays byte-for-byte
compatible with the Phase 1 contract the Flutter client already parses.
"""

from __future__ import annotations

import gzip
import io

import pytest

from pathlib import Path
from fastapi.testclient import TestClient

from app import main
from app.pharmcat_models import PharmcatReport
from app.vcf_validation import MAX_UPLOAD_BYTES

CONTRACT_TOP_LEVEL = {"patient_id", "timestamp", "analyses", "quality_metrics"}
CONTRACT_PER_DRUG = {
    "drug",
    "risk_assessment",
    "pharmacogenomic_profile",
    "clinical_recommendation",
    "llm_generated_explanation",
}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, cyp2c19_pm_report: PharmcatReport):
    """TestClient with PharmCAT replaced by the CYP2C19 poor-metaboliser fixture."""

    async def fake_run_pharmcat(vcf_text: str, *, sample_hint: str = "sample"):
        return cyp2c19_pm_report

    monkeypatch.setattr(main, "run_pharmcat", fake_run_pharmcat)
    return TestClient(main.app)


def post(client: TestClient, content: bytes, drugs: str, name: str = "test.vcf"):
    return client.post(
        "/analyze",
        files={"file": (name, io.BytesIO(content), "text/plain")},
        data={"drugs": drugs},
    )


class TestHealth:
    def test_health(self) -> None:
        response = TestClient(main.app).get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_root_reports_pharmcat_availability(self) -> None:
        body = TestClient(main.app).get("/").json()
        assert "pharmcat_available" in body
        assert isinstance(body["pharmcat_available"], bool)


class TestContractCompatibility:
    """Phase 1's Flutter client must keep working with zero changes."""

    def test_response_shape_is_unchanged(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        body = post(client, valid_vcf_bytes, "clopidogrel,aspirin").json()

        assert set(body) == CONTRACT_TOP_LEVEL
        for analysis in body["analyses"]:
            assert set(analysis) == CONTRACT_PER_DRUG
            assert set(analysis["risk_assessment"]) == {
                "risk_label",
                "confidence_score",
                "severity",
            }
            assert set(analysis["pharmacogenomic_profile"]) == {
                "primary_gene",
                "diplotype",
                # Added Phase 6 as provenance: the reduced diplotype CPIC guidance
                # was found by. Additive and nullable, so existing clients are
                # unaffected — but the key IS in the contract now, and this
                # assertion is what keeps Pydantic and the Dart model in step.
                "recommendation_diplotype",
                "candidate_diplotypes",
                "phenotype",
                "activity_score",
                "detected_variants",
            }
            assert set(analysis["clinical_recommendation"]) == {
                "action",
                "dosing_guidance",
                "cpic_recommendation",
                "cpic_evidence_level",
                "alternatives",
                "source",
            }
            assert set(analysis["llm_generated_explanation"]) == {
                "summary",
                "mechanism",
                "variant_rationale",
                "patient_friendly",
                "disclaimer",
            }
        assert set(body["quality_metrics"]) == {
            "vcf_parsing_success",
            "variants_detected_count",
            "processing_time_ms",
            "warnings",
            # Added Phase 6: per-gene coverage of PharmCAT's required positions,
            # computed from the input before PharmCAT runs. Present pass or fail,
            # because a confident result at low coverage is the dangerous case.
            "position_coverage",
            # Added Feature Set A: which PharmCAT and CPIC data this result came
            # from, and when the explanation store was generated. A frozen store
            # carries an implicit "as of" that was previously invisible.
            "guideline_provenance",
        }

    def test_enum_values_stay_within_the_contract(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        body = post(
            client, valid_vcf_bytes, "clopidogrel,simvastatin,codeine,aspirin"
        ).json()
        for analysis in body["analyses"]:
            assert analysis["risk_assessment"]["risk_label"] in {
                "Safe",
                "Adjust Dosage",
                "Toxic",
                "Ineffective",
                "Unknown",
            }
            assert analysis["risk_assessment"]["severity"] in {
                "none",
                "low",
                "moderate",
                "high",
                "critical",
            }
            assert analysis["pharmacogenomic_profile"]["phenotype"] in {
                "PM",
                "IM",
                "NM",
                "RM",
                "URM",
                "Unknown",
            }
            assert analysis["clinical_recommendation"]["cpic_evidence_level"] in {
                "A",
                "B",
                "C",
                "D",
                "Unknown",
            }

    def test_disclaimer_is_present_on_every_result(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        from app.models import DISCLAIMER

        body = post(client, valid_vcf_bytes, "clopidogrel,aspirin").json()
        for analysis in body["analyses"]:
            assert analysis["llm_generated_explanation"]["disclaimer"] == DISCLAIMER

    def test_the_disclaimer_names_the_missing_clinical_review(self) -> None:
        """
        Pinned because it is the disclosure that matters and the one most
        likely to be trimmed for brevity.

        "Not a medical device" is boilerplate every such tool carries and every
        reader skims. The specific gap — no clinician read this, and here is
        what was done instead — is the part that actually informs, so the text
        must keep both halves: the absence, and the guarantee that replaces it.
        """
        from app.models import DISCLAIMER

        assert "No qualified clinical expert has reviewed" in DISCLAIMER
        assert "machine-verified" in DISCLAIMER
        assert "CPIC" in DISCLAIMER
        # It must not overstate: verification is about provenance, not truth.
        assert "not that it is correct for you" in DISCLAIMER

    def test_client_and_api_disclaimers_are_identical(self) -> None:
        """
        `app/lib/config.dart` renders its own copy in a persistent banner, so
        the two can drift silently — the client would keep showing a weaker
        disclaimer than the API sends, and nothing would flag it.
        """
        import re

        from app.models import DISCLAIMER

        config = (
            Path(__file__).resolve().parents[2] / "app" / "lib" / "config.dart"
        ).read_text()
        match = re.search(r"const String kDisclaimer =\s*(.*?);", config, re.S)
        assert match, "kDisclaimer not found in app/lib/config.dart"
        client_text = "".join(re.findall(r"'([^']*)'", match.group(1)))
        assert client_text == DISCLAIMER, (
            "client and API disclaimers have drifted:\n"
            f"  api:    {DISCLAIMER}\n  client: {client_text}"
        )

    def test_the_short_banner_still_names_the_gap(self) -> None:
        """
        The persistent banner is abbreviated, not softened.

        The full disclosure runs to five lines, which crowded the UI enough to
        push results off-screen — a banner nobody reads past discloses nothing.
        Shortening it is legitimate; dropping the clinical-review clause while
        shortening is the regression this pins. Brevity buys scannability, not
        silence.
        """
        import re

        config = (
            Path(__file__).resolve().parents[2] / "app" / "lib" / "config.dart"
        ).read_text()
        match = re.search(r"const String kDisclaimerShort =\s*(.*?);", config, re.S)
        assert match, "kDisclaimerShort not found in app/lib/config.dart"
        banner = "".join(re.findall(r"'([^']*)'", match.group(1)))

        assert "clinician has reviewed" in banner, (
            f"the always-visible banner no longer names the review gap: {banner!r}"
        )
        assert "Not a medical device" in banner
        # Short enough to actually be read in a one-line strip.
        assert len(banner) < 160, f"banner is {len(banner)} chars — too long to scan"

    def test_the_banner_renders_the_short_form_not_the_full_one(self) -> None:
        """The widget must use the abbreviated constant, or the overflow returns."""
        banner_source = (
            Path(__file__).resolve().parents[2]
            / "app" / "lib" / "widgets" / "disclaimer_banner.dart"
        ).read_text()
        assert "kDisclaimerShort" in banner_source
        assert "\n                  kDisclaimer," not in banner_source


class TestRealResults:
    def test_cyp2c19_poor_metaboliser_clopidogrel(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        """The flagship case: a real diplotype driving a CPIC-derived label."""
        body = post(client, valid_vcf_bytes, "clopidogrel").json()
        analysis = body["analyses"][0]

        assert analysis["drug"] == "clopidogrel"
        assert analysis["risk_assessment"]["risk_label"] == "Ineffective"
        assert analysis["risk_assessment"]["severity"] == "critical"
        assert analysis["risk_assessment"]["confidence_score"] == 0.95

        profile = analysis["pharmacogenomic_profile"]
        assert profile["primary_gene"] == "CYP2C19"
        assert profile["diplotype"] == "*2/*2"
        assert profile["phenotype"] == "PM"
        assert profile["detected_variants"], "expected non-reference variants"

        # The clinical text must be CPIC's, verbatim.
        recommendation = analysis["clinical_recommendation"]
        assert recommendation["action"] == (
            "Avoid clopidogrel if possible. Use prasugrel or ticagrelor at "
            "standard dose if no contraindication."
        )
        # ...and traceable back to the rule that produced the label.
        assert "avoid_for_lack_of_efficacy" in recommendation["source"]
        assert "PharmCAT" in recommendation["source"]

    def test_patient_id_comes_from_the_vcf_sample_column(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        body = post(client, valid_vcf_bytes, "clopidogrel").json()
        assert body["patient_id"] == "CYP2C19_POOR_METABOLIZER"

    def test_multi_gene_drug_reports_the_driving_gene(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        """azathioprine keys off TPMT and NUDT15; both normal here."""
        body = post(client, valid_vcf_bytes, "azathioprine").json()
        profile = body["analyses"][0]["pharmacogenomic_profile"]
        assert profile["primary_gene"] in {"TPMT", "NUDT15"}
        assert body["analyses"][0]["risk_assessment"]["risk_label"] == "Safe"

    def test_codeine_is_unknown_with_the_cyp2d6_warning(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        """Acceptance #4: never a fabricated CYP2D6 call."""
        body = post(client, valid_vcf_bytes, "codeine").json()
        analysis = body["analyses"][0]

        assert analysis["risk_assessment"]["risk_label"] == "Unknown"
        assert analysis["pharmacogenomic_profile"]["phenotype"] == "Unknown"
        assert analysis["pharmacogenomic_profile"]["diplotype"] == "Unknown"
        assert main.CYP2D6_WARNING in body["quality_metrics"]["warnings"]

    def test_unknown_drug_is_a_result_not_an_error(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        body = post(client, valid_vcf_bytes, "aspirin").json()
        analysis = body["analyses"][0]
        assert analysis["risk_assessment"]["risk_label"] == "Unknown"
        assert analysis["risk_assessment"]["confidence_score"] == 0.0
        assert "not covered by any CPIC guideline" in (
            analysis["clinical_recommendation"]["action"]
        )

    def test_one_analysis_per_requested_drug(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        body = post(client, valid_vcf_bytes, "clopidogrel,simvastatin,aspirin").json()
        assert [a["drug"] for a in body["analyses"]] == [
            "clopidogrel",
            "simvastatin",
            "aspirin",
        ]

    def test_duplicate_drugs_are_collapsed_case_insensitively(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        body = post(client, valid_vcf_bytes, "Clopidogrel, clopidogrel ,ASPIRIN").json()
        assert [a["drug"] for a in body["analyses"]] == ["clopidogrel", "aspirin"]

    def test_quality_metrics_are_real(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        metrics = post(client, valid_vcf_bytes, "clopidogrel").json()["quality_metrics"]
        assert metrics["vcf_parsing_success"] is True
        assert metrics["variants_detected_count"] > 0
        assert metrics["processing_time_ms"] >= 0

    def test_explanation_provenance_is_reported(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        """Phase 3: which generator ran, and the guard verdict, must be visible."""
        metrics = post(client, valid_vcf_bytes, "clopidogrel").json()["quality_metrics"]
        provenance = [w for w in metrics["warnings"] if w.startswith("explanation mode=")]
        assert provenance, metrics["warnings"]
        assert "source=" in provenance[0]
        assert "guard=" in provenance[0]

    def test_explanation_is_populated_and_not_a_stub(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        """Phase 3 replaced the placeholder text with grounded content."""
        explanation = post(client, valid_vcf_bytes, "clopidogrel").json()["analyses"][
            0
        ]["llm_generated_explanation"]

        for field, text in explanation.items():
            assert text.strip(), f"{field} is empty"
        assert "STUB" not in explanation["mechanism"]
        assert "TODO" not in explanation["mechanism"]
        # Real mechanism content, drawn from the corpus.
        # The gene is named in `variant_rationale`, which is COMPOSED BY CODE from
        # the profile. `summary` is deliberately genotype-agnostic now: the model
        # is no longer allowed to state a gene or diplotype, so asserting the gene
        # appears in its prose would pin a property the design removed.
        assert "CYP2C19" in explanation["variant_rationale"]

    def test_no_unfilled_slots_reach_the_client(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        """A literal '{diplotype}' in the UI would be a visible bug."""
        body = post(client, valid_vcf_bytes, "clopidogrel,codeine,aspirin").json()
        for analysis in body["analyses"]:
            for field, text in analysis["llm_generated_explanation"].items():
                assert "{" not in text, f"unfilled slot in {analysis['drug']}.{field}: {text}"

    def test_gzipped_upload_is_accepted(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        response = post(
            client, gzip.compress(valid_vcf_bytes), "clopidogrel", "sample.vcf.gz"
        )
        assert response.status_code == 200


class TestErrorResponses:
    """Acceptance #3 — clear 400s with machine-readable codes, never a 500."""

    def _assert_error(self, response, status: int, code: str) -> None:
        assert response.status_code == status, response.text
        body = response.json()
        assert body["error_code"] == code
        # `detail` must stay a plain string: the Phase 1 Flutter client renders it.
        assert isinstance(body["detail"], str) and body["detail"]

    def test_grch37_vcf(self, client: TestClient, valid_vcf_bytes: bytes) -> None:
        text = valid_vcf_bytes.decode().replace(
            "##fileformat=VCFv4.2\n",
            "##fileformat=VCFv4.2\n##reference=file:///ref/human_g1k_v37.fasta\n",
        )
        response = post(client, text.encode(), "clopidogrel", "grch37.vcf")
        self._assert_error(response, 400, "UNSUPPORTED_REFERENCE_BUILD")
        # The remedy in words, not the tool that performs it — the commands
        # moved to docs/input_requirements.md, which the message points at.
        detail = response.json()["detail"].lower()
        assert "convert" in detail
        assert "input_requirements" in detail

    def test_oversized_vcf(self, client: TestClient) -> None:
        response = post(client, b"x" * (MAX_UPLOAD_BYTES + 1), "clopidogrel", "big.vcf")
        self._assert_error(response, 413, "FILE_TOO_LARGE")

    def test_non_vcf_upload(self, client: TestClient) -> None:
        response = post(client, b"\x89PNG\r\n\x1a\n\x00\x00garbage", "clopidogrel", "x.png")
        self._assert_error(response, 400, "NOT_VCF")

    def test_empty_file(self, client: TestClient) -> None:
        self._assert_error(post(client, b"", "clopidogrel"), 400, "EMPTY_FILE")

    def test_sites_only_vcf(self, client: TestClient) -> None:
        vcf = (
            "##fileformat=VCFv4.2\n"
            "##contig=<ID=chr10,assembly=GRCh38.p14>\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            "chr10\t94781859\trs4244285\tG\tA\t.\tPASS\t.\n"
        )
        self._assert_error(
            post(client, vcf.encode(), "clopidogrel"), 400, "NO_SAMPLE_COLUMN"
        )

    def test_no_drugs(self, client: TestClient, valid_vcf_bytes: bytes) -> None:
        self._assert_error(post(client, valid_vcf_bytes, "  , ,"), 422, "NO_DRUGS")

    def test_too_many_drugs(self, client: TestClient, valid_vcf_bytes: bytes) -> None:
        drugs = ",".join(f"drug{i}" for i in range(main.MAX_DRUGS_PER_REQUEST + 1))
        self._assert_error(post(client, valid_vcf_bytes, drugs), 422, "TOO_MANY_DRUGS")


class TestStaticModeIsApiFree:
    """
    Acceptance #1: the deployed path needs no paid or keyed service.

    These tests delete GEMINI_API_KEY from the environment and additionally
    poison the LLM generator, so a regression that reintroduced a network call
    in the default path would fail here rather than at deploy time.
    """

    @pytest.fixture(autouse=True)
    def _no_api_key(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("EXPLANATION_MODE", "static")

        from app.explanation import generator_llm

        def forbidden(*args, **kwargs):
            raise AssertionError(
                "static mode called the LLM generator; the deployed path must "
                "make no API call"
            )

        monkeypatch.setattr(generator_llm, "generate", forbidden)

    def test_explanations_are_complete_without_a_key(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        body = post(client, valid_vcf_bytes, "clopidogrel,simvastatin,codeine").json()
        assert body["analyses"]

        for analysis in body["analyses"]:
            explanation = analysis["llm_generated_explanation"]
            for field, text in explanation.items():
                assert text.strip(), f"{analysis['drug']}.{field} is empty"
            # Acceptance #6 — the disclaimer, on every result.
            assert "Not a medical device" in explanation["disclaimer"]

    def test_static_source_is_used_where_available(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        metrics = post(client, valid_vcf_bytes, "clopidogrel").json()["quality_metrics"]
        assert any(
            "source=static" in w for w in metrics["warnings"]
        ), metrics["warnings"]

    def test_absent_clinical_review_is_disclosed(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        """
        The gap must be stated, not implied by an absence.

        This project has no qualified clinical reviewer. The earlier wording
        ("not yet been reviewed by the faculty guide") described a review that
        was pending; it was not pending, it was never going to happen. A reader
        has to be told the difference.
        """
        metrics = post(client, valid_vcf_bytes, "clopidogrel").json()["quality_metrics"]
        warnings = " ".join(metrics["warnings"])
        assert "No qualified clinical expert has reviewed" in warnings
        # And it must say what WAS done, or the disclosure reads as a bare
        # disclaimer rather than a description of the actual guarantee.
        assert "trace to a CPIC recommendation" in warnings
        assert "provenance, not correctness" in warnings
        # Nothing may imply a review is merely outstanding.
        assert "faculty" not in warnings.lower()
        assert "not yet been reviewed" not in warnings

    def test_root_reports_no_key_required(self) -> None:
        body = TestClient(main.app).get("/").json()
        assert body["requires_api_key"] is False
        assert body["explanation_mode"] == "static"


class TestPharmcatFailure:
    def test_pharmcat_unavailable_returns_503_not_500(
        self, monkeypatch: pytest.MonkeyPatch, valid_vcf_bytes: bytes
    ) -> None:
        """A broken server must not look like a bad request."""
        from app.pharmcat_runner import PharmcatExecutionError

        async def boom(vcf_text: str, *, sample_hint: str = "sample"):
            raise PharmcatExecutionError("PharmCAT is not installed on this server.")

        monkeypatch.setattr(main, "run_pharmcat", boom)
        response = post(TestClient(main.app), valid_vcf_bytes, "clopidogrel")
        assert response.status_code == 503
        assert response.json()["error_code"] == "PHARMCAT_UNAVAILABLE"
