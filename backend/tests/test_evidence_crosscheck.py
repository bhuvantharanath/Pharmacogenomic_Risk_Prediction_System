"""
The coverage invariant checked twice: on our parser's evidence and on PharmCAT's
(Phase 9 B3, app/evidence_crosscheck.py).

Part A found files whose genotypes PharmCAT itself discarded — a REF base that
contradicts GRCh38, a contig name it does not recognise — while the coverage
gate counted them, and the API answered confidently from them. The adversarial
files here are rebuilt from the tracked demo VCF the way Part A built them
(audit/phase9/a4/build_inputs.py), so the tests do not depend on Part A's
untracked inputs.
"""

from __future__ import annotations

import ast
import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.evidence_crosscheck as crosscheck
import app.main as main
from app.capabilities import capability_for
from app.coverage import DrugEligibility
from app.pharmcat_models import CallStatus, PharmcatGeneCall, PharmcatReport, PharmcatVariant
from app.pharmcat_runner import find_jar
from tests.conftest import REPO_ROOT

DEMO = REPO_ROOT / "test-data/demo/demo_confident.vcf"
DRUGS = "clopidogrel,warfarin,codeine,simvastatin,azathioprine,fluorouracil"
CALLED = ("CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "NUDT15", "DPYD")
SWAP = {"A": "C", "C": "G", "G": "T", "T": "A"}
CONFIDENT = {"Ineffective", "Toxic", "Adjust Dosage", "No PGx-guided adjustment identified"}
REQUIREMENTS = json.loads((REPO_ROOT / "backend/app/data/position_requirements.json").read_text())

client = TestClient(main.app)


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


def _demo() -> tuple[list[str], list[list[str]]]:
    header, rows = [], []
    for line in DEMO.read_text().splitlines():
        (header if line.startswith("#") else rows).append(line if line.startswith("#") else line.split("\t"))
    return header, rows


def _vcf(header: list[str], rows: list[list[str]]) -> bytes:
    return ("\n".join(header + ["\t".join(r) for r in rows]) + "\n").encode()


def _wrong_ref(ref: str, alt: str) -> str:
    new = SWAP[ref]
    return SWAP[new] if new == alt else new


def ref_wrong_at_critical_row() -> bytes:
    """A4-09b: rs4244285 (G>A in GRCh38, GT 1/1) carries REF C."""
    header, rows = _demo()
    for r in rows:
        if r[2] == "rs4244285":
            r[3], r[4] = "C", "A"
    return _vcf(header, rows)


def ref_wrong_at_ten_cyp2c19_rows() -> bytes:
    """A4-09a: ten hom-ref CYP2C19 rows carry a REF GRCh38 does not have."""
    header, rows = _demo()
    changed = 0
    for r in rows:
        if "PX=CYP2C19" in r[7] and r[9] == "0/0" and changed < 10 and len(r[3]) == 1 and r[3] in SWAP:
            r[3] = _wrong_ref(r[3], r[4])
            changed += 1
    assert changed == 10
    return _vcf(header, rows)


def ref_wrong_at_every_snv_row() -> bytes:
    """A4-22's essential property: every SNV row's REF contradicts GRCh38."""
    header, rows = _demo()
    for r in rows:
        if len(r[3]) == 1 and r[3] in SWAP and all(len(a) == 1 for a in r[4].split(",")):
            r[3] = _wrong_ref(r[3], r[4])
    return _vcf(header, rows)


def unprefixed_contigs() -> bytes:
    """A4-03: `10` instead of `chr10`, in the rows and the contig lines."""
    header, rows = _demo()
    header = [h.replace("##contig=<ID=chr", "##contig=<ID=") for h in header]
    for r in rows:
        r[0] = r[0].removeprefix("chr")
    return _vcf(header, rows)


CASES = {
    "base": lambda: DEMO.read_bytes(),
    "ref_critical": ref_wrong_at_critical_row,
    "ref_ten": ref_wrong_at_ten_cyp2c19_rows,
    "ref_every_snv": ref_wrong_at_every_snv_row,
    "no_chr": unprefixed_contigs,
}


@pytest.fixture(scope="module")
def responses() -> dict[str, dict]:
    if find_jar() is None:  # pragma: no cover — no jar in this environment
        pytest.skip("PharmCAT jar not found")
    out = {}
    for name, build in CASES.items():
        response = client.post(
            "/analyze",
            files={"file": (f"{name}.vcf", io.BytesIO(build()), "text/plain")},
            data={"drugs": DRUGS},
        )
        assert response.status_code == 200, (name, response.text[:300])
        out[name] = response.json()
    return out


def _labels(body: dict) -> dict[str, str]:
    return {a["drug"]: a["risk_assessment"]["risk_label"] for a in body["analyses"]}


def _coverage(body: dict, gene: str) -> dict:
    return body["quality_metrics"]["position_coverage"][gene]


def _crosscheck_warnings(body: dict) -> list[str]:
    """The per-gene warnings; per-drug refusals repeat a shorter form of them."""
    return [w for w in body["quality_metrics"]["warnings"]
            if "the coverage check counted this file's genotypes as complete" in w]


# --------------------------------------------------------------------------- #
# The adversarial files: PharmCAT's own evidence now decides with ours
# --------------------------------------------------------------------------- #


def test_an_intact_file_agrees_everywhere(responses: dict) -> None:
    """Positive control: complete, GRCh38-consistent evidence is used in full."""
    body = responses["base"]
    for gene in CALLED:
        row = _coverage(body, gene)
        assert row["sufficient"] and row["pharmcat_sufficient"], gene
        assert row["pharmcat_positions_used"] == row["positions_present"] == row["positions_required"]
    assert _crosscheck_warnings(body) == []
    assert _labels(body)["clopidogrel"] == "Ineffective"


def test_a_wrong_ref_at_the_decision_critical_row_declines_clopidogrel(responses: dict) -> None:
    body = responses["ref_critical"]
    row = _coverage(body, "CYP2C19")

    assert row["sufficient"] is True            # our parser counted it
    assert row["pharmcat_positions_used"] == 34  # PharmCAT discarded it
    assert row["pharmcat_sufficient"] is False
    assert _labels(body)["clopidogrel"] == "Unknown"
    [warning] = _crosscheck_warnings(body)
    assert warning.startswith("CYP2C19: ")
    assert "rs4244285" in warning
    assert "does not match expected reference" in warning
    reason = next(a for a in body["analyses"] if a["drug"] == "clopidogrel")
    assert "PharmCAT did not use genotypes the coverage check counted for CYP2C19" in json.dumps(reason)


def test_wrong_refs_at_ten_cyp2c19_rows_decline_clopidogrel(responses: dict) -> None:
    body = responses["ref_ten"]
    assert _coverage(body, "CYP2C19")["pharmcat_positions_used"] == 25
    assert _labels(body)["clopidogrel"] == "Unknown"


def test_a_file_whose_refs_contradict_grch38_gets_no_confident_label(responses: dict) -> None:
    body = responses["ref_every_snv"]
    assert not CONFIDENT & set(_labels(body).values()), _labels(body)
    for gene in ("DPYD", "TPMT", "NUDT15"):
        assert _coverage(body, gene)["pharmcat_sufficient"] is False, gene


def test_unprefixed_contigs_are_declined_with_the_unused_positions_named(responses: dict) -> None:
    body = responses["no_chr"]
    assert set(_labels(body).values()) == {"Unknown"}
    named = {w.split(":", 1)[0] for w in _crosscheck_warnings(body)}
    assert named == set(CALLED), named
    for gene in CALLED:
        assert _coverage(body, gene)["pharmcat_positions_used"] == 0


def test_no_confident_label_when_either_view_is_insufficient(responses: dict) -> None:
    """The acceptance invariant, over every response here."""
    for name, body in responses.items():
        for analysis in body["analyses"]:
            if analysis["risk_assessment"]["risk_label"] not in CONFIDENT:
                continue
            for gene in capability_for(analysis["drug"]).evidence_dependencies:
                row = _coverage(body, gene)
                assert row["sufficient"] and row["pharmcat_sufficient"], (name, analysis["drug"], gene)


# --------------------------------------------------------------------------- #
# The rule itself, on constructed reports
# --------------------------------------------------------------------------- #


def _report(gene: str, uncalled: set[int] = frozenset()) -> PharmcatReport:
    spec = REQUIREMENTS["genes"][gene]
    variants = [
        PharmcatVariant(position=int(p), chromosome=c, call=None if int(p) in uncalled else "A/A")
        for c, p in spec["positions"]
    ]
    call = PharmcatGeneCall(gene=gene, status=CallStatus.DEFINITE, variants=variants)
    return PharmcatReport(pharmcat_version="3.4.0", genes={gene: call})


def test_a_null_call_is_not_evidence() -> None:
    first = int(REQUIREMENTS["genes"]["CYP2C19"]["positions"][0][1])
    evidence = crosscheck.assess(_report("CYP2C19", {first}))["CYP2C19"]

    assert (evidence.used, evidence.required) == (34, 35)
    assert not evidence.sufficient
    assert [u.position for u in evidence.unused] == [first]


def test_pharmcats_own_required_positions_name_only_nat2() -> None:
    """Pinned: a PharmCAT that adds requirements for our genes fails here first."""
    if find_jar() is None:  # pragma: no cover
        pytest.skip("PharmCAT jar not found")
    native = crosscheck.pharmcat_required_positions()
    assert {g: sorted(p) for g, p in native.items() if p} == {
        "NAT2": [18400194, 18400344, 18400593, 18400806, 18400860]
    }
    for gene in CALLED:
        assert not native.get(gene), gene


def test_a_pharmcat_required_position_is_honoured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Positive control for the native rule, on a gene our thresholds would pass."""
    spec = REQUIREMENTS["genes"]["DPYD"]
    critical = {int(p) for _, p in spec["decision_critical_positions"]}
    spare = next(int(p) for _, p in spec["positions"] if int(p) not in critical)
    report = _report("DPYD", {spare})
    assert crosscheck.assess(report)["DPYD"].sufficient  # 82/83, every critical one used

    monkeypatch.setattr(crosscheck, "pharmcat_required_positions", lambda: {"DPYD": frozenset({spare})})
    evidence = crosscheck.assess(report)["DPYD"]
    assert evidence.missing_required == (spare,)
    assert not evidence.sufficient


def test_a_pharmcat_required_position_fires_for_cyp2c19(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC1 as pre-committed: inject a CYP2C19 requirement; the native rule fires and declines.

    CYP2C19's own 100% threshold would decline this report anyway, so the DPYD
    control above is the one that isolates the rule's effect; this one shows the
    rule is read for the gene the plan names.
    """
    critical_row = 94781859  # rs4244285
    report = _report("CYP2C19", {critical_row})
    monkeypatch.setattr(crosscheck, "pharmcat_required_positions",
                        lambda: {"CYP2C19": frozenset({critical_row})})
    evidence = crosscheck.assess(report)["CYP2C19"]
    assert evidence.missing_required == (critical_row,)
    assert not evidence.sufficient
    assert "PharmCAT itself requires 1" in crosscheck.disagreement_warning(evidence)


def test_restrict_declines_and_names_the_finding() -> None:
    eligibility = DrugEligibility(
        drug="clopidogrel", required_genes=("CYP2C19",), failed_genes=(),
        guidance_capable=True, limitation="",
    )
    first = int(REQUIREMENTS["genes"]["CYP2C19"]["positions"][0][1])
    restricted = crosscheck.restrict(eligibility, crosscheck.assess(_report("CYP2C19", {first})))

    assert not restricted.eligible
    assert restricted.failed_genes == ("CYP2C19",)
    assert "PharmCAT did not use genotypes the coverage check counted for CYP2C19." in restricted.reason
    assert crosscheck.restrict(eligibility, crosscheck.assess(_report("CYP2C19"))) is eligibility


def test_the_second_view_does_not_read_the_vcf_or_reuse_the_first() -> None:
    """Independence: no runtime import of the coverage module, no VCF argument."""
    tree = ast.parse(Path(crosscheck.__file__).read_text())
    runtime_imports = [
        node for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module and "coverage" in node.module
    ]
    assert runtime_imports == []
    params = [a.arg for a in next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "assess"
    ).args.args]
    assert params == ["report", "requirements"]


def test_the_served_image_runs_the_jar_not_the_preprocessor() -> None:
    """Why bcftools 1.24 needed no adoption: the served path never preprocesses."""
    dockerfile = (REPO_ROOT / "infra/Dockerfile").read_text()
    assert "ENV PHARMCAT_JAR=/pharmcat/pharmcat.jar" in dockerfile
    assert "9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741" in dockerfile
