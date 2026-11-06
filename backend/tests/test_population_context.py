"""
The South Asian context comes from the project's own measurement (Phase 9 B11,
audit/phase9/B11_PLAN.md, AC1).

The client shows these figures beside a result and never uses them for one.
They must still be right: the committed table is what the reports give, and
the generator's arithmetic reproduces the figures the report itself documents
(read from the report here, not typed into the test).
"""

from __future__ import annotations

import importlib.util
import re

from tests.conftest import REPO_ROOT

REPORT = REPO_ROOT / "reports/sas_cohort_expansion.md"


def _generator():
    spec = importlib.util.spec_from_file_location(
        "generate_population_context", REPO_ROOT / "scripts/generate_population_context.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _documented_cyp2c19() -> dict[str, tuple[str, str, str]]:
    """The report's CYP2C19 table: cohort -> (percent, low, high)."""
    rows = {}
    pattern = re.compile(
        r"^\| \**(\w+)\** \| \**\d+\** \| \d+ \| \d+ \| \**([\d.]+)%\** \| \**\[([\d.]+), ([\d.]+)\]\** \|",
        re.MULTILINE)
    section = REPORT.read_text().split("## CYP2C19 reduced function", 1)[1].split("\n## ", 1)[0]
    for cohort, percent, low, high in pattern.findall(section):
        rows[cohort] = (percent, low, high)
    return rows


def test_the_committed_table_is_what_the_reports_give() -> None:
    generator = _generator()
    assert generator.OUT.read_text() == generator.render(generator.build())


def test_cyp2c19_reproduces_the_reports_documented_figures() -> None:
    documented = _documented_cyp2c19()
    assert set(documented) == {"pooled", "STU", "ITU", "BEB", "PJL", "GIH"}, documented
    cyp2c19 = _generator().build()["genes"]["CYP2C19"]
    got = {"pooled": (cyp2c19["pooled"]["percent"], cyp2c19["pooled"]["low"], cyp2c19["pooled"]["high"])}
    got.update({c["cohort"]: (c["percent"], c["low"], c["high"]) for c in cyp2c19["cohorts"]})
    assert got == documented


def test_uncertain_calls_stay_in_the_total_and_are_never_reduced() -> None:
    genes = _generator().build()["genes"]
    assert genes["DPYD"]["uncertain"] == {"Indeterminate": 129}
    assert genes["DPYD"]["pooled"]["reduced"] == 13 and genes["DPYD"]["pooled"]["n"] == 601
    for gene, data in genes.items():
        assert data["pooled"]["n"] == 601, gene
        assert sum(c["n"] for c in data["cohorts"]) == 601, gene


def test_coverage_is_named_where_it_was_measured_and_unknown_where_not() -> None:
    genes = _generator().build()["genes"]
    assert (genes["CYP2C19"]["positions_present"], genes["CYP2C19"]["positions_required"]) == (16, 35)
    assert genes["DPYD"]["positions_present"] is None
