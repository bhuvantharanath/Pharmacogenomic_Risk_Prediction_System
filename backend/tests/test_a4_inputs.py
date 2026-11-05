"""
Every A4 row, kept as a permanent test (Phase 9 B6, AC6 and the A4 rows of
AC1-AC5 and AC7).

Part A ran 35 adversarial inputs once, against a local server, with every
expectation written before anything ran (audit/phase9/A4_PRECOMMIT.md) and a
verdict computed by a judge, not by reading the output
(audit/phase9/a4/run_a4.py). Both are kept here: the inputs are rebuilt from the
demo files by tests/a4_inputs.py, and `judge` is Part A's, unchanged except
that it now also covers the addendum rows Part A judged by hand (A4-22 to
A4-26), with the rules the addenda wrote down.

The second half pins what B6 chose where A4 allowed a choice
(audit/phase9/B6_PLAN.md): `10` and `Chr10` are read as `chr10`, a GRCh37 length
names the build, a wrong REF declines the whole file, a gVCF is named as one,
and a BCF is named as one.
"""

from __future__ import annotations

import functools
import io

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.pharmcat_runner import find_jar
from tests import a4_inputs

CASES = a4_inputs.build()
DRUG = "clopidogrel"
BASE_LABEL = "Ineffective"
CONFIDENT = {"Ineffective", "Toxic", "Adjust Dosage", "Safe", "No PGx-guided adjustment identified"}
RENAMED = "Chromosome names were read in GRCh38's 'chr' form"

#: Part A's expectations (run_a4.py EXPECT), plus the addenda's rows.
EXPECT = {
    "BASE": ("same", None),
    "A4-01": ("4xx", "UNSUPPORTED_REFERENCE_BUILD"),
    "A4-02": ("build_decline", None),
    "A4-03": ("same_or_decline_preview_agrees", None),
    "A4-04": ("same", None),
    "A4-05": ("same", None),
    "A4-06": ("4xx_any", None),
    "A4-07": ("4xx", "UNSUPPORTED_MULTISAMPLE"),
    "A4-08a": ("same_or_decline", None),
    "A4-08b": ("same_or_decline", None),
    "A4-09a": ("decline", None),
    "A4-09b": ("decline", None),
    "A4-10": ("same", None),
    "A4-11": ("variants_only", None),
    "A4-12a": ("4xx", "EMPTY_FILE"),
    "A4-12b": ("4xx", "NO_VARIANTS"),
    "A4-12c": ("4xx", "NOT_VCF"),
    "A4-12d": ("4xx", "NOT_VCF"),
    "A4-12e": ("4xx", "FILE_TOO_LARGE"),
    "A4-12f": ("4xx", "DECOMPRESSED_TOO_LARGE"),
    "A4-13a": ("decline", None),
    "A4-13b": ("same_or_decline", None),
    "A4-14a": ("decline", None),
    "A4-14b": ("decline", None),
    "A4-15a": ("same", None),
    "A4-15b": ("4xx", "NOT_VCF"),
    "A4-16": ("decline", None),
    "A4-17": ("decline", None),
    "A4-18": ("same_or_decline", None),
    "A4-19": ("same_or_decline", None),
    "A4-20": ("same_or_decline_preview_agrees", None),
    "A4-21": ("same", None),
    # Addendum: "decline for every drug. FAIL on any confident label".
    "A4-22": ("decline_every_drug", None),
    "A4-23": ("decline_every_drug", None),
    # Addendum 2, azathioprine.
    "A4-24": ("one_of", {"Toxic", "Unknown"}),
    "A4-25": ("one_of", {"Adjust Dosage", "Unknown"}),
    "A4-26": ("declined_or_disclosed", None),
}
PREVIEW = {"A4-03", "A4-20"}
NEEDS_PHARMCAT = {case for case, (kind, _) in EXPECT.items() if not kind.startswith("4xx")}


def _upload(path: str, case_id: str):
    case = CASES[case_id] if case_id != "A4-12f" else a4_inputs.Case("A4-12f", "A4-12f_bomb.vcf.gz", _bomb())
    data = {"drugs": case.drugs} if path == "/analyze" else None
    # A client per call: test_deployment.py reloads app.main, and a client built
    # earlier would serve the old app, whose error handler drops `error_code`.
    response = TestClient(main.app).post(
        path, files={"file": (case.filename, io.BytesIO(case.data), "text/plain")}, data=data)
    return response.status_code, response.json()


@functools.lru_cache(maxsize=1)
def _bomb() -> bytes:
    return a4_inputs.bomb()


@functools.lru_cache(maxsize=None)
def analyze(case_id: str) -> tuple[int, dict]:
    return _upload("/analyze", case_id)


@functools.lru_cache(maxsize=None)
def preview(case_id: str) -> tuple[int, dict]:
    return _upload("/coverage", case_id)


def _label(body: dict, drug: str = DRUG) -> str | None:
    return next((a["risk_assessment"]["risk_label"] for a in body.get("analyses", []) if a["drug"] == drug), None)


def judge(case_id: str, status: int, body: dict, answerable: list[str] | None) -> tuple[str, str]:
    """Part A's judge (audit/phase9/a4/run_a4.py), with the addenda's rows added."""
    kind, extra = EXPECT[case_id]
    lab = _label(body) if status == 200 else None
    code = body.get("error_code")
    warnings = body.get("quality_metrics", {}).get("warnings", []) if status == 200 else []
    if status == 0 or status >= 500:
        return "FAIL", f"status {status} {code or ''}"
    confident = lab in CONFIDENT
    named = any(DRUG in w or "CYP2C19" in w for w in warnings)
    if kind == "4xx":
        ok = 400 <= status < 500 and code == extra
        return ("PASS" if ok else "FAIL"), f"status {status} code {code} label {lab}"
    if kind == "4xx_any":
        ok = 400 <= status < 500 and bool(code) and "vcf" in str(body.get("detail", "")).lower()
        return ("PASS" if ok else "FAIL"), f"status {status} code {code}"
    if kind == "same":
        return ("PASS" if lab == BASE_LABEL else "FAIL"), f"label {lab} (base {BASE_LABEL})"
    if kind == "decline":
        if 400 <= status < 500 and code:
            return "PASS", f"4xx {code}"
        if lab == "Unknown":
            return ("PASS" if named else "PARTIAL"), f"Unknown; reason named={named}"
        return "FAIL", f"confident label {lab} on inadequate evidence"
    if kind.startswith("same_or_decline"):
        if confident and lab != BASE_LABEL:
            return "FAIL", f"different confident label {lab} (base {BASE_LABEL})"
        why = f"label {lab}" if status == 200 else f"4xx {code}"
        if kind.endswith("preview_agrees") and answerable is not None and status == 200:
            if DRUG in answerable and lab == "Unknown":
                return "FAIL", f"preview says {DRUG} answerable but /analyze returned Unknown"
        if lab == "Unknown" and not named:
            return "PARTIAL", why + "; Unknown without a named reason"
        return "PASS", why
    if kind == "build_decline":
        if 400 <= status < 500 and code == "UNSUPPORTED_REFERENCE_BUILD":
            return "PASS", "4xx UNSUPPORTED_REFERENCE_BUILD"
        if confident:
            return "FAIL", f"confident label {lab}"
        specific = [w for w in warnings if "GRCh37" in w and "assuming GRCh38" not in w]
        return ("PASS" if specific else "PARTIAL"), f"Unknown; build-specific warning={bool(specific)}"
    if kind == "variants_only":
        ok = lab == "Unknown" and any("homozygous-reference" in w for w in warnings)
        return ("PASS" if ok else "FAIL"), f"label {lab}"
    if kind == "decline_every_drug":
        if 400 <= status < 500 and code:
            return "PASS", f"4xx {code}"
        labels = {a["drug"]: a["risk_assessment"]["risk_label"] for a in body.get("analyses", [])}
        return ("FAIL" if CONFIDENT & set(labels.values()) else "PASS"), f"labels {labels}"
    if kind == "one_of":
        lab = _label(body, "azathioprine") if status == 200 else None
        return ("PASS" if lab in extra else "FAIL"), f"azathioprine {lab}"
    if kind == "declined_or_disclosed":
        analysis = next(a for a in body.get("analyses", []) if a["drug"] == "azathioprine")
        lab = analysis["risk_assessment"]["risk_label"]
        disclosed = (any("3B" in w or "3C" in w or "phase" in w.lower() for w in warnings)
                     or any("3B" in c for c in analysis["pharmacogenomic_profile"].get("candidate_diplotypes", [])))
        return ("PASS" if lab == "Unknown" or disclosed else "FAIL"), f"azathioprine {lab}, disclosed={disclosed}"
    return "FAIL", "unjudged"


@pytest.fixture
def pharmcat(request) -> None:
    if find_jar() is None:  # pragma: no cover — no jar in this environment
        pytest.skip("PharmCAT jar not found")


# --------------------------------------------------------------------------- #
# AC6 — every row meets its pre-committed expectation
# --------------------------------------------------------------------------- #


def test_every_a4_row_has_a_case_and_an_expectation() -> None:
    assert set(EXPECT) == set(CASES) | {"A4-12f"}
    assert len(EXPECT) == 37  # BASE, A4-01 ... A4-26 with their letters


@pytest.mark.parametrize("case_id", sorted(EXPECT))
def test_a4_row_meets_its_precommitted_expectation(case_id: str, request) -> None:
    if case_id in NEEDS_PHARMCAT:
        request.getfixturevalue("pharmcat")
    status, body = analyze(case_id)
    answerable = preview(case_id)[1].get("answerable_drugs") if case_id in PREVIEW else None
    verdict, why = judge(case_id, status, body, answerable)
    assert verdict == "PASS", f"{case_id}: {verdict}: {why}"


def test_the_judge_still_fails_what_part_a_failed() -> None:
    """Positive control: Part A's recorded FAIL bodies, reduced to what the judge reads."""
    confident_from_wrong_ref = {"analyses": [{"drug": DRUG, "risk_assessment": {"risk_label": "Ineffective"}}]}
    assert judge("A4-09a", 200, confident_from_wrong_ref, None)[0] == "FAIL"
    preview_disagrees = {"analyses": [{"drug": DRUG, "risk_assessment": {"risk_label": "Unknown"}}],
                         "quality_metrics": {"warnings": ["CYP2C19: no diplotype could be called"]}}
    assert judge("A4-03", 200, preview_disagrees, [DRUG])[0] == "FAIL"
    wrong_build_answered = {"analyses": [{"drug": "fluorouracil",
                                          "risk_assessment": {"risk_label": "No PGx-guided adjustment identified"}}]}
    assert judge("A4-23", 200, wrong_build_answered, None)[0] == "FAIL"


# --------------------------------------------------------------------------- #
# What B6 chose where A4 allowed a choice
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("case_id", ["A4-03", "A4-20"])
def test_unprefixed_and_capitalised_contigs_are_read_as_chr(case_id: str, pharmcat) -> None:
    """AC1: the base file's answer, the rename said out loud, and a preview that agrees."""
    status, body = analyze(case_id)
    assert status == 200
    [analysis] = body["analyses"]
    assert analysis["risk_assessment"]["risk_label"] == BASE_LABEL
    assert analysis["pharmacogenomic_profile"]["diplotype"] == "*2/*2"
    assert any(w.startswith(RENAMED) for w in body["quality_metrics"]["warnings"])
    assert DRUG in preview(case_id)[1]["answerable_drugs"]


def test_a_grch37_length_names_the_build_and_the_contig() -> None:
    """AC2: A4-02 carries only `##contig=<ID=1,length=249250621>`-style lines."""
    status, body = analyze("A4-02")
    assert (status, body["error_code"]) == (400, "UNSUPPORTED_REFERENCE_BUILD")
    assert "GRCh37's chr1" in body["detail"] and "249,250,621" in body["detail"]


@pytest.mark.parametrize(("case_id", "code", "says"), [
    ("A4-09a", "REFERENCE_ALLELE_MISMATCH", ("At 10 of the 463 required positions",)),
    ("A4-09b", "REFERENCE_ALLELE_MISMATCH", ("chr10:94781859", "rs4244285", "GRCh38 has G")),
    ("A4-22", "UNSUPPORTED_REFERENCE_BUILD", ("GRCh37",)),
    ("A4-23", "UNSUPPORTED_REFERENCE_BUILD", ("GRCh37",)),
])
def test_a_ref_that_contradicts_grch38_declines_the_whole_file(case_id: str, code: str, says: tuple) -> None:
    """AC3: a 400 for every drug, and the preview refuses the same file the same way."""
    status, body = analyze(case_id)
    assert (status, body["error_code"]) == (400, code)
    for text in says:
        assert text in body["detail"], (text, body["detail"][:300])
    assert (preview(case_id)[0], preview(case_id)[1]["error_code"]) == (400, code)


def test_a_gvcf_is_named_as_one(pharmcat) -> None:
    """AC4: blocks counted and named; neither the array diagnosis nor the variants-only one."""
    status, body = analyze("A4-08b")
    assert status == 200 and _label(body) == "Unknown"
    warnings = body["quality_metrics"]["warnings"]
    [gvcf] = [w for w in warnings if w.startswith("This file is a gVCF:")]
    assert "required positions lie inside reference blocks" in gvcf
    assert not any("SNP-array" in w or "homozygous-reference genotypes at any" in w for w in warnings)
    assert _label(analyze("A4-08a")[1]) == BASE_LABEL


def test_a_bcf_is_named_as_one() -> None:
    """AC5."""
    status, body = analyze("A4-06")
    assert (status, body["error_code"]) == (400, "NOT_VCF")
    assert "is a BCF file" in body["detail"] and "Convert it to a .vcf" in body["detail"]


def test_two_samples_are_refused() -> None:
    """AC7: one sample per upload, as before, now under test."""
    status, body = analyze("A4-07")
    assert (status, body["error_code"]) == (400, "UNSUPPORTED_MULTISAMPLE")
    assert "one sample at a time" in body["detail"]
