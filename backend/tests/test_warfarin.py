"""
Warfarin: VKORC1 and CYP4F2 are read and shown; the label stays Unknown
(Phase 9 B5, audit finding F-14; label by owner decision, audit/phase9/B5_AC2_AMENDMENT.md).

CPIC's warfarin guidance is a pharmacogenetic dosing algorithm, not a
recommendation per genotype. PharmCAT calls VKORC1 and CYP4F2, and the
application used to discard them, so the warfarin card could only ever say
Unknown with nothing behind it. It still says Unknown — the independent
expectation table reads an algorithm pointer as Unknown, and the owner chose to
keep it — but it now shows what the file established, quotes CPIC, never
quotes a dose, and says what it cannot assess.
"""

from __future__ import annotations

import html
import io
import json
import re
import subprocess
import sys
import zipfile

import pytest
from fastapi.testclient import TestClient

from app import capabilities, main
from app.pharmcat_runner import GENOTYPE_ONLY_GENES, TARGET_GENES
from tests.conftest import REPO_ROOT

JAR = REPO_ROOT / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
REQUIREMENTS = json.loads((REPO_ROOT / "backend/app/data/position_requirements.json").read_text())
CPIC_TEXT = (
    "CPIC Guideline for Pharmacogenetics-Guided Warfarin Dosing: 2017 Update [Article: 28198005 ] "
    "recommends that pharmacogenetic warfarin dosing be accomplished through the use of one of the "
    "pharmacogenetic dosing algorithms, as summarized in Figure 2. See CPIC guideline annotation for details."
)
DOSE = re.compile(r"\d+(?:\.\d+)?\s*(?:mg|%)", re.IGNORECASE)
VKORC1_TT = "rs9923231 variant (T)/rs9923231 variant (T)"
VKORC1_CC = "rs9923231 reference (C)/rs9923231 reference (C)"

client = TestClient(main.app)


def _jar_texts() -> list[str]:
    with zipfile.ZipFile(JAR) as zf:
        guidance = json.loads(zf.read("org/pharmgkb/pharmcat/reporter/prescribing_guidance.json"))
    texts = []
    for guideline in guidance["guidelines"]:
        if guideline["guideline"]["source"] != "CPIC":
            continue
        for rec in guideline.get("recommendations", []):
            if any(c["name"] == "warfarin" for c in rec.get("relatedChemicals", [])):
                raw = html.unescape(re.sub(r"</?[a-zA-Z][^>]*>", " ", rec["text"]["html"]))
                texts.append(re.sub(r"\s+", " ", raw).strip())
    return texts


@pytest.fixture(scope="module")
def jar() -> None:
    if not JAR.is_file():  # pragma: no cover
        pytest.skip("pinned PharmCAT jar absent — run: python scripts/fetch_pinned_artifacts.py")


def _vcf(tmp_path, name: str, *diplotypes: str, drop: str | None = None) -> bytes:
    path = tmp_path / f"{name}.vcf"
    args = [sys.executable, str(REPO_ROOT / "test-data/generate_synthetic_vcf.py"),
            "--from-jar", str(JAR), "--sample", name.upper(), "-o", str(path)]
    for diplotype in diplotypes:
        args += ["--diplotype", diplotype]
    proc = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr[-500:]
    lines = path.read_text().splitlines()
    if drop:
        lines = [line for line in lines if line.startswith("#") or not line.startswith(drop)]
    return ("\n".join(lines) + "\n").encode()


def _warfarin(payload: bytes) -> tuple[dict, dict]:
    response = client.post("/analyze", files={"file": ("w.vcf", io.BytesIO(payload), "text/plain")},
                           data={"drugs": "warfarin"})
    if response.status_code == 503:  # pragma: no cover
        pytest.skip("PharmCAT unavailable")
    assert response.status_code == 200, response.text[:300]
    body = response.json()
    [result] = body["analyses"]
    return result, body


def _findings(result: dict) -> dict[str, dict]:
    return {f["gene"]: f for f in result["gene_findings"]}


# --------------------------------------------------------------------------- #
# AC1 — VKORC1 and CYP4F2 are parsed and gated
# --------------------------------------------------------------------------- #


def test_both_genes_are_parsed_as_genotype_only(jar) -> None:
    """PharmCAT ships no phenotype file for either, which is why they are genotype-only."""
    with zipfile.ZipFile(JAR) as zf:
        phenotypes = {n.rsplit("/", 1)[1] for n in zf.namelist()
                      if n.startswith("org/pharmgkb/pharmcat/phenotype/")}
    assert {"VKORC1.json", "CYP4F2.json"}.isdisjoint(phenotypes)
    assert {"VKORC1", "CYP4F2"} <= set(TARGET_GENES)
    assert GENOTYPE_ONLY_GENES == {"VKORC1", "CYP4F2"}


def test_their_positions_and_critical_positions_come_from_the_jar(jar) -> None:
    genes = REQUIREMENTS["genes"]
    assert genes["VKORC1"]["positions"] == [["chr16", 31096368]]
    assert len(genes["CYP4F2"]["positions"]) == 20
    assert genes["VKORC1"]["decision_critical_positions"] == [["chr16", 31096368]]
    # Recomputed here, independently: where CYP4F2*3 differs from *1.
    with zipfile.ZipFile(JAR) as zf:
        d = json.loads(zf.read("org/pharmgkb/pharmcat/definition/alleles/CYP4F2_translation.json"))
    alleles = {a["name"]: a["alleles"] for a in d["namedAlleles"]}
    star3 = [d["variants"][i]["position"] for i, (a, b) in enumerate(zip(alleles["*1"], alleles["*3"]))
             if b is not None and a != b]
    assert genes["CYP4F2"]["decision_critical_positions"] == [["chr19", p] for p in star3]
    for gene in ("VKORC1", "CYP4F2"):
        assert genes[gene]["min_coverage_percent"] == 100
        assert genes[gene]["threshold_measured"] is False


def test_warfarin_depends_on_cyp2c9_and_vkorc1_and_shows_cyp4f2() -> None:
    w = capabilities.capability_for("warfarin")
    assert w.evidence_dependencies == ("CYP2C9", "VKORC1")
    assert w.relevant_genes == ("CYP2C9", "VKORC1", "CYP4F2")
    assert w.guidance_capable is False


# --------------------------------------------------------------------------- #
# AC2' — Unknown, genes shown, CPIC quoted, no dose, limits stated
# --------------------------------------------------------------------------- #


def test_every_jar_row_carries_the_quoted_cpic_text(jar) -> None:
    texts = _jar_texts()
    assert len(texts) == 12
    assert set(texts) == {CPIC_TEXT}
    assert CPIC_TEXT in capabilities.capability_for("warfarin").limitation


@pytest.mark.parametrize(("name", "diplotypes", "cyp4f2"), [
    ("normal", ("CYP2C9=*1/*1", f"VKORC1={VKORC1_CC}"), None),
    ("pm_tt_cyp4f2", ("CYP2C9=*3/*3", f"VKORC1={VKORC1_TT}", "CYP4F2=*1/*3"), "*1/*3"),
    ("pm_tt_ref_cyp4f2", ("CYP2C9=*3/*3", f"VKORC1={VKORC1_TT}", "CYP4F2=*1/*1"), "*1/*1"),
])
def test_called_genes_are_shown_and_the_label_stays_unknown(jar, tmp_path, name, diplotypes, cyp4f2) -> None:
    result, _ = _warfarin(_vcf(tmp_path, name, *diplotypes))
    findings = _findings(result)

    assert result["risk_assessment"]["risk_label"] == "Unknown"
    assert findings["CYP2C9"]["assessed"] and findings["VKORC1"]["assessed"]
    assert findings["CYP2C9"]["call"] == diplotypes[0].split("=")[1]
    assert findings["VKORC1"]["call"] == diplotypes[1].split("=", 1)[1]
    assert findings["CYP4F2"]["role"] == "reference"
    assert findings["CYP4F2"]["assessed"] is (cyp4f2 is not None)
    assert findings["CYP4F2"]["call"] == (cyp4f2 or "")

    action = result["clinical_recommendation"]["action"]
    assert CPIC_TEXT in action
    assert "does not collect" in action and "ancestry" in action
    assert "rs12777823 is not assessed" in action
    assert not DOSE.search(json.dumps(result)), DOSE.search(json.dumps(result))


# --------------------------------------------------------------------------- #
# AC3 / AC5' — a missing required gene is named
# --------------------------------------------------------------------------- #


def test_a_missing_vkorc1_is_named_and_not_assessed(jar, tmp_path) -> None:
    result, body = _warfarin(_vcf(tmp_path, "no_vkorc1", "CYP2C9=*3/*3", f"VKORC1={VKORC1_TT}",
                                  drop="chr16"))
    findings = _findings(result)

    assert result["risk_assessment"]["risk_label"] == "Unknown"
    assert result["clinical_recommendation"]["action"].startswith(
        "Required genomic evidence is incomplete for VKORC1.")
    assert findings["VKORC1"]["assessed"] is False and findings["VKORC1"]["call"] == ""
    assert findings["CYP2C9"]["assessed"] is True
    assert any(w.startswith("VKORC1: only 0 of 1") and "no coverage sweep" in w
               for w in body["quality_metrics"]["warnings"])


def test_a_missing_cyp2c9_is_named_and_not_assessed(jar, tmp_path) -> None:
    result, _ = _warfarin(_vcf(tmp_path, "no_cyp2c9", "CYP2C9=*3/*3", f"VKORC1={VKORC1_TT}",
                               drop="chr10"))
    assert result["risk_assessment"]["risk_label"] == "Unknown"
    assert "Required genomic evidence is incomplete for CYP2C9" in result["clinical_recommendation"]["action"]
    assert _findings(result)["CYP2C9"]["assessed"] is False


# --------------------------------------------------------------------------- #
# Warnings name only genes the request depends on
# --------------------------------------------------------------------------- #


def test_a_clopidogrel_request_does_not_list_warfarin_gene_gaps(jar) -> None:
    demo = (REPO_ROOT / "test-data/demo/demo_confident.vcf").read_bytes()  # no chr16/chr19 rows
    body = client.post("/analyze", files={"file": ("d.vcf", io.BytesIO(demo), "text/plain")},
                       data={"drugs": "clopidogrel"}).json()
    assert not [w for w in body["quality_metrics"]["warnings"] if "VKORC1" in w or "CYP4F2" in w]
    # Still reported, as every gene is.
    assert body["quality_metrics"]["position_coverage"]["VKORC1"]["sufficient"] is False
    assert body["analyses"][0]["risk_assessment"]["risk_label"] == "Ineffective"
