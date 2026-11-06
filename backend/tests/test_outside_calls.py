"""
CYP2D6 from a dedicated caller (Phase 9 B10, audit/phase9/B10_PLAN.md).

PharmaGuard still never calls CYP2D6 from a VCF. A user may supply a diplotype
that Cyrius, BCyrius, Aldy or StellarPGx called from the reads; PharmCAT takes
it as an outside call, and codeine is then answered from CPIC's text for that
phenotype. Every view names the call as supplied, not called.

The input is the dangerous part: the diplotype is written into a file PharmCAT
reads line by line, so the grammar is tested on the attacks (a newline that
adds a second gene) as much as on the notation.
"""

from __future__ import annotations

import io
import json
import sys
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app import outside_calls, pharmcat_runner, security
from app.pharmcat_runner import Invoker, run_pharmcat
from tests.conftest import REPO_ROOT

NA12273 = REPO_ROOT / "test-data/demo/demo_na12273_1000g.vcf"
CONFIDENT = REPO_ROOT / "test-data/demo/demo_confident.vcf"
HAS_JAR = pharmcat_runner.find_jar() is not None

# PharmCAT 3.4.0's CPIC text for codeine by CYP2D6 phenotype (measured with the
# pinned jar, audit/phase9/B10.log).
PM_TEXT = ("Avoid codeine use because of possibility of diminished analgesia. If "
           "opioid use is warranted, consider a non-tramadol opioid.")
UM_TEXT = ("Avoid codeine use because of potential for serious toxicity. If opioid "
           "use is warranted, consider a non-tramadol opioid.")
NM_TEXT = "Use codeine label recommended age- or weight-specific dosing."
IM_TEXT = ("Use codeine label recommended age- or weight-specific dosing. If no "
           "response and opioid use is warranted, consider a non-tramadol opioid.")


def _post(vcf: Path, drugs: str, diplotype: str | None = None, caller: str | None = None):
    security.limiter.reset()
    data = {"drugs": drugs}
    if diplotype is not None:
        data["cyp2d6_diplotype"] = diplotype
    if caller is not None:
        data["cyp2d6_caller"] = caller
    return TestClient(main.app).post(
        "/analyze", files={"file": (vcf.name, io.BytesIO(vcf.read_bytes()), "text/plain")}, data=data)


def _analysis(response, drug: str) -> dict:
    return next(a for a in response.json()["analyses"] if a["drug"] == drug)


# --------------------------------------------------------------------------- #
# AC4 — input safety
# --------------------------------------------------------------------------- #

ACCEPTED = ["*1/*4", "*4/*4", "*1x2/*1", "*1/*1x2", "*2x2/*4", "*1xN/*4", "*68+*4/*10",
            "*1/[*6 + *8]", "*1≥3/*4", "*1.001/*2", "*4/*10", "*999/*1"]

REFUSED = {
    "a newline adding a second gene": "*1/*4\nCYP2C19\t*1/*1",
    "a trailing newline": "*1/*4\n",
    "a tab": "*1/*4\t",
    "a leading space": " *1/*4",
    "a gene prefix": "CYP2D6*1/*4",
    "a lowercase prefix": "cyp2d6*1/*4",
    "a bare allele": "1/4",
    "one haplotype": "*1",
    "three haplotypes": "*1/*4/*2",
    "a space before the slash": "*1 /*4",
    "a letter allele": "*a/*4",
    "a shell suffix": "*1/*4;rm",
    "a combination without spaces": "[*6+*8]/*1",
    "a copy number of one": "*1x1/*4",
    "more than 80 characters": "*1+" * 26 + "*1/*4",
}


@pytest.mark.parametrize("diplotype", ACCEPTED)
def test_the_notation_is_accepted(diplotype: str) -> None:
    call = outside_calls.parse(diplotype, "Cyrius")
    assert call is not None and call.gene == "CYP2D6" and call.diplotype == diplotype
    assert call.file_line() == f"CYP2D6\t{diplotype}\n"


@pytest.mark.parametrize("case", sorted(REFUSED))
def test_anything_else_is_refused(case: str) -> None:
    with pytest.raises(outside_calls.OutsideCallError) as exc:
        outside_calls.parse(REFUSED[case], "Cyrius")
    assert exc.value.code == "OUTSIDE_CALL_INVALID"


@pytest.mark.parametrize("caller", ["cyrius", "Stargazer", "Aldy 4", "", " Cyrius"])
def test_only_the_named_callers_are_accepted(caller: str) -> None:
    with pytest.raises(outside_calls.OutsideCallError):
        outside_calls.parse("*1/*4", caller)
    for name in outside_calls.CALLERS:
        assert outside_calls.parse("*1/*4", name).caller == name


def test_both_or_neither() -> None:
    assert outside_calls.parse(None, None) is None
    assert outside_calls.parse("", "") is None
    for diplotype, caller in (("*1/*4", None), (None, "Cyrius")):
        with pytest.raises(outside_calls.OutsideCallError) as exc:
            outside_calls.parse(diplotype, caller)
        assert exc.value.code == "OUTSIDE_CALL_INCOMPLETE"


@pytest.mark.parametrize(("diplotype", "caller", "code"), [
    (REFUSED["a newline adding a second gene"], "Cyrius", "OUTSIDE_CALL_INVALID"),
    (REFUSED["a tab"], "Cyrius", "OUTSIDE_CALL_INVALID"),
    (REFUSED["more than 80 characters"], "Cyrius", "OUTSIDE_CALL_INVALID"),
    ("*1/*4", "Stargazer", "OUTSIDE_CALL_INVALID"),
    ("*1/*4", None, "OUTSIDE_CALL_INCOMPLETE"),
    (None, "Cyrius", "OUTSIDE_CALL_INCOMPLETE"),
])
def test_the_api_refuses_before_pharmcat_runs(monkeypatch, diplotype, caller, code) -> None:
    ran = []

    async def recording(*args, **kwargs):  # pragma: no cover - must not run
        ran.append((args, kwargs))
        raise AssertionError("PharmCAT ran")

    monkeypatch.setattr(main, "run_pharmcat", recording)
    response = _post(CONFIDENT, "codeine", diplotype, caller)
    assert response.status_code == 400
    assert response.json()["error_code"] == code
    assert ran == []


def test_the_command_carries_the_file_and_never_research_mode(tmp_path: Path) -> None:
    vcf, out, outside = tmp_path / "s.vcf", tmp_path / "out", tmp_path / "outside_calls.tsv"
    for kind in ("jar", "wrapper"):
        invoker = Invoker(kind=kind, command_prefix=["pharmcat"], version_args=[], describe=kind)
        without = invoker.build(vcf, out)
        with_call = invoker.build(vcf, out, outside)
        assert "-po" not in without
        assert with_call == [*without, "-po", str(outside)]
        assert not any(arg.startswith("-research") for arg in with_call)


def test_the_runner_writes_one_cyp2d6_line_and_removes_it(tmp_path: Path, monkeypatch) -> None:
    seen = tmp_path / "seen.tsv"
    script = tmp_path / "fake_pharmcat.py"
    script.write_text(textwrap.dedent(f"""
        import json, shutil, sys
        from pathlib import Path
        argv = sys.argv
        out = Path(argv[argv.index("-o") + 1])
        shutil.copyfile(argv[argv.index("-po") + 1], {str(seen)!r})
        out.joinpath("sample.report.json").write_text(json.dumps({{"genes": {{}}}}))
    """))
    monkeypatch.setattr(pharmcat_runner, "resolve_invoker", lambda: Invoker(
        kind="wrapper", command_prefix=[sys.executable, str(script)], version_args=[],
        describe="fake"))
    root = tmp_path / "tmproot"
    root.mkdir()
    monkeypatch.setattr(pharmcat_runner.tempfile, "tempdir", str(root))
    import asyncio
    asyncio.run(run_pharmcat(CONFIDENT.read_text(),
                             outside_call=outside_calls.parse("*1/*4", "Aldy")))
    assert seen.read_text(encoding="utf-8") == "CYP2D6\t*1/*4\n"
    assert list(root.glob("pharmaguard_pharmcat_*")) == []


# --------------------------------------------------------------------------- #
# AC1-AC3, AC5 — the real PharmCAT
# --------------------------------------------------------------------------- #

pytestmark_jar = pytest.mark.skipif(not HAS_JAR, reason="PharmCAT jar not found")


@pytestmark_jar
def test_without_a_supplied_call_codeine_stays_unknown() -> None:
    for vcf in (NA12273, CONFIDENT):
        codeine = _analysis(_post(vcf, "codeine"), "codeine")
        assert codeine["risk_assessment"]["risk_label"] == "Unknown"
        assert codeine["pharmacogenomic_profile"]["supplied_by"] is None


@pytestmark_jar
@pytest.mark.parametrize(("diplotype", "caller", "label", "phenotype", "text"), [
    ("*4/*4", "Cyrius", "Ineffective", "PM", PM_TEXT),
    ("*4/*10", "Aldy", "No PGx-guided adjustment identified", "IM", IM_TEXT),
    ("*1/*2", "StellarPGx", "No PGx-guided adjustment identified", "NM", NM_TEXT),
    ("*1/*1x2", "BCyrius", "Toxic", "URM", UM_TEXT),
    ("*1xN/*4", "Cyrius", "Unknown", "Unknown", None),
    ("*999/*1", "Cyrius", "Unknown", "Unknown", None),
])
def test_a_supplied_call_answers_codeine_from_cpic(diplotype, caller, label, phenotype, text) -> None:
    response = _post(NA12273, "codeine", diplotype, caller)
    assert response.status_code == 200
    codeine = _analysis(response, "codeine")
    profile = codeine["pharmacogenomic_profile"]
    assert codeine["risk_assessment"]["risk_label"] == label
    assert profile["phenotype"] == phenotype
    assert profile["supplied_by"] == caller
    if text is not None:
        assert codeine["clinical_recommendation"]["action"] == text

    # AC3: named as supplied, never as called. The warning quotes the call as
    # it was supplied; PharmCAT may reorder it in the profile (*999/*1 -> *1/*999).
    assert (f"CYP2D6 {diplotype} supplied by {caller}, not called by PharmaGuard."
            in response.json()["quality_metrics"]["warnings"])
    rationale = codeine["llm_generated_explanation"]["variant_rationale"]
    if label != "Unknown":
        assert f"supplied by {caller}, not called by PharmaGuard" in rationale
    assert "PharmCAT called" not in rationale
    assert "PharmaGuard called" not in rationale
    assert "non-reference positions supporting" not in rationale


@pytestmark_jar
@pytest.mark.parametrize(("vcf", "drugs"), [
    (CONFIDENT, "clopidogrel"),
    (CONFIDENT, "clopidogrel,simvastatin,fluorouracil,codeine,ibuprofen"),
])
def test_a_supplied_call_changes_only_cyp2d6_drugs(vcf: Path, drugs: str) -> None:
    def analyses(response) -> dict:
        body = response.json()
        return {a["drug"]: json.dumps(a, sort_keys=True) for a in body["analyses"]}

    without = analyses(_post(vcf, drugs))
    supplied = analyses(_post(vcf, drugs, "*1/*2", "Cyrius"))
    assert without.keys() == supplied.keys()
    for drug in without:
        if drug == "codeine":
            assert without[drug] != supplied[drug]
        else:
            assert without[drug] == supplied[drug], drug


# --------------------------------------------------------------------------- #
# The gates themselves: a CYP2D6 call opens codeine only if it came OUTSIDE,
# and only for the request that supplied it.
# --------------------------------------------------------------------------- #


@pytestmark_jar
def test_only_an_outside_call_opens_codeine() -> None:
    """
    Without a supplied call PharmCAT makes no CYP2D6 call, so codeine is Unknown
    whatever the gates do; that is why the negative control alone cannot test
    them. This takes a real report with a supplied PM call and relabels the call
    as one from the VCF (as PharmCAT's research mode would make): the engine
    must still abstain.
    """
    import asyncio

    from app import cpic_engine

    report = asyncio.run(run_pharmcat(
        NA12273.read_text(), outside_call=outside_calls.parse("*4/*4", "Cyrius")))
    outside = report.gene("CYP2D6")
    assert outside is not None and outside.is_outside_call and outside.is_called

    supplied, _, _, _ = cpic_engine.evaluate("codeine", report)
    assert supplied.risk_label.value == "Ineffective"

    from_vcf = report.model_copy(update={"genes": {
        **report.genes, "CYP2D6": outside.model_copy(update={"call_source": "MATCHER"})}})
    abstained, _, _, _ = cpic_engine.evaluate("codeine", from_vcf)
    assert abstained.risk_label.value == "Unknown"


@pytestmark_jar
def test_the_supplied_gene_is_named_only_for_the_request_that_supplied_it() -> None:
    """build_response names a call supplied, and lifts the coverage gate, only
    with this request's own outside call in hand."""
    import asyncio

    from app import coverage as coverage_mod
    from app.vcf_validation import validate_vcf

    text = NA12273.read_text()
    report = asyncio.run(run_pharmcat(
        text, outside_call=outside_calls.parse("*4/*4", "Cyrius")))
    metadata = validate_vcf(text.encode(), "na12273.vcf")
    cov = coverage_mod.assess(metadata.text)

    with_call = main.build_response(report, ["codeine"], metadata, 0, cov=cov,
                                    outside_call=outside_calls.parse("*4/*4", "Cyrius"))
    without = main.build_response(report, ["codeine"], metadata, 0, cov=cov)
    assert with_call.analyses[0].pharmacogenomic_profile.supplied_by == "Cyrius"
    assert with_call.analyses[0].risk_assessment.risk_label.value == "Ineffective"
    assert without.analyses[0].pharmacogenomic_profile.supplied_by is None
    assert without.analyses[0].risk_assessment.risk_label.value == "Unknown"
