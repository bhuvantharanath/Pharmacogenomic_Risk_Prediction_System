"""
No borrowed CPIC row (Phase 9 F-20, audit/phase9/F20_PLAN.md).

When no CPIC row matches the called phenotypes, `select_annotation` used to fall
back to "the strongest available row" of any phenotype. Strength ranks how
well-evidenced a recommendation is, not how cautious, so the stand-in was in
effect the first row in the list, and the label was derived from text written
for somebody else. In the exemplar a CYP2C19 Poor Metabolizer was told to use
clopidogrel at standard dose.

No real input was measured reaching that branch at runtime: an earlier gate
turned every unasserted phenotype into Unknown first. These tests build the
case that does reach it, using CPIC's own wording rather than invented text, so
the branch cannot quietly come back.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest

from app import cpic_engine
from app.models import Phenotype, RiskLabel
from app.pharmcat_models import CpicAnnotation
from app.pharmcat_runner import parse_report
from tests.conftest import REPO_ROOT

FIXTURES = REPO_ROOT / "backend" / "tests" / "fixtures"
SCRIPTS = REPO_ROOT / "scripts"
EXPECTATIONS = REPO_ROOT / "test-data" / "reference" / "cpic_expectations.json"

#: The new warning: what tells a reader the branch was taken.
NO_MATCH = "matches the called phenotypes, so none is shown"
#: evaluate()'s existing reason on its Unknown branch.
NO_MATCH_REASON = "PharmCAT returned no CPIC recommendation matching the called phenotype"
#: Measured before the fix (F20.log): the construction below reaches the branch
#: this many times. Fewer would mean the test had stopped testing the branch.
MEASURED_CASES = 63


def _report(name: str):
    return parse_report(json.loads((FIXTURES / f"pharmcat_report_{name}.json").read_text()))


def _row(row: dict) -> CpicAnnotation:
    """One CPIC expectation row, as the annotation PharmCAT would have given."""
    return CpicAnnotation(
        drug_recommendation=row["recommendation"],
        implications=row.get("implications") or [],
        classification=row.get("classification"),
        population=row.get("population"),
        dosing_information=bool(row.get("dosingInformation")),
        alternate_drug_available=bool(row.get("alternateDrugAvailable")),
        lookup_key=[row["lookup"]],
    )


def _cpic_rows() -> dict[str, list[CpicAnnotation]]:
    rows = json.loads(EXPECTATIONS.read_text())["rows"]
    by_drug: dict[str, list[CpicAnnotation]] = defaultdict(list)
    for row in rows:
        if (row.get("recommendation") or "").strip():
            by_drug[row["drug"]].append(_row(row))
    return by_drug


def _with_only(report, drug: str, annotations: list[CpicAnnotation]):
    guideline = report.drugs[drug].model_copy(update={"annotations": annotations})
    return report.model_copy(update={"drugs": {**report.drugs, drug: guideline}})


def _script(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    # A dataclass looks its own module up in sys.modules while it is defined.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --- AC1: the exemplar --------------------------------------------------------


def test_the_fixture_is_the_poor_metabolizer_it_claims_to_be() -> None:
    """The control: untouched, this report is the Ineffective case."""
    assessment, recommendation, _call, _w = cpic_engine.evaluate("clopidogrel", _report("cyp2c19_pm"))
    assert assessment.risk_label is RiskLabel.INEFFECTIVE
    assert "Avoid clopidogrel" in recommendation.action


def test_a_poor_metabolizer_is_not_given_the_normal_metabolizer_row() -> None:
    rows = json.loads(EXPECTATIONS.read_text())["rows"]
    normal = next(
        r for r in rows
        if r["drug"] == "clopidogrel"
        and r["lookup"] == {"CYP2C19": "Normal Metabolizer"}
        and r.get("classification") == "Strong"
    )
    probe = _with_only(_report("cyp2c19_pm"), "clopidogrel", [_row(normal)])

    assessment, recommendation, _call, warnings = cpic_engine.evaluate("clopidogrel", probe)

    assert assessment.risk_label is RiskLabel.UNKNOWN
    assert "use at standard dose" not in recommendation.action
    assert NO_MATCH_REASON in recommendation.action
    assert any(NO_MATCH in w for w in warnings), warnings


# --- AC2: every fixture, every real CPIC row ----------------------------------


def test_no_fixture_borrows_a_label_from_another_phenotypes_row() -> None:
    """
    Each fixture's guideline is given every real CPIC row for its drug EXCEPT the
    rows that match the called phenotypes, which is the only way to reach the
    no-match branch. Nothing may come back confident, and no borrowed row's text
    may reach the recommendation.
    """
    cpic = _cpic_rows()
    reached, failures = 0, []
    for fixture in sorted(FIXTURES.glob("pharmcat_report_*.json")):
        report = parse_report(json.loads(fixture.read_text()))
        for drug in report.drugs:
            others = [a for a in cpic.get(drug, []) if not cpic_engine._annotation_matches_calls(a, report)]
            if not others:
                continue
            assessment, recommendation, _call, warnings = cpic_engine.evaluate(
                drug, _with_only(report, drug, others))
            if not any(NO_MATCH in w for w in warnings):
                continue  # an earlier gate decided first; not this branch
            reached += 1
            case = f"{fixture.stem.removeprefix('pharmcat_report_')}/{drug}"
            if assessment.risk_label is not RiskLabel.UNKNOWN:
                failures.append(f"{case}: {assessment.risk_label.value}")
            borrowed = [a.drug_recommendation for a in others
                        if a.drug_recommendation and a.drug_recommendation in recommendation.action]
            if borrowed:
                failures.append(f"{case}: action carries {borrowed[0][:60]!r}")

    # The positive control. An absence check that never reached the branch would
    # pass with nothing tested.
    assert reached >= MEASURED_CASES, (
        f"only {reached} cases reached the no-match branch; {MEASURED_CASES} were measured")
    assert not failures, "\n".join(failures)


# --- AC3: build time agrees with the runtime ----------------------------------


@pytest.mark.parametrize("drug", ["fluorouracil", "capecitabine"])
def test_the_explanation_builder_does_not_ground_on_a_borrowed_row(drug: str) -> None:
    """
    `find_annotation` is "the CPIC row the runtime would select". For an
    Indeterminate DPYD call the runtime selects none, but the fallback used to
    hand the builder CPIC's activity score 2.0 row: standard dosing.
    """
    assert cpic_engine.evaluate(drug, _report("dpyd_compound_het"))[0].risk_label is RiskLabel.UNKNOWN

    annotation, _gene = _script("pregenerate_explanations").find_annotation(drug, Phenotype.UNKNOWN)
    assert annotation is None or annotation.lookup_key != [{"DPYD": "2.0"}], annotation
    found, text = _script("enumerate_cases").cpic_text_for(drug, Phenotype.UNKNOWN)
    assert "no indication to change dose" not in text, (found, text)
