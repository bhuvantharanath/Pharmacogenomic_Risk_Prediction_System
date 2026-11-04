"""
Phase 9 B1: what the pinned engine knows, checked against CPIC itself.

The application's clinical text, the 105-row mapping validation and the
required positions all come from the pinned PharmCAT jar. These tests compare
that jar with a vendored snapshot of CPIC's public API and re-derive every
generated table from the jar, so a silent difference cannot accumulate between
what CPIC says, what PharmCAT embeds and what this repository commits.

Plan and pre-committed criteria: audit/phase9/B1_PLAN.md (AC1, AC2, AC5, AC6).
"""

from __future__ import annotations

import html
import json
import re
import sys

import pytest

from app.explanation import static_store
from tests.conftest import REPO_ROOT

SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_position_requirements  # noqa: E402
import cpic_snapshot  # noqa: E402

pytestmark = pytest.mark.skipif(
    not cpic_snapshot.JAR.is_file(),
    reason="pinned PharmCAT jar absent — run: python scripts/fetch_pinned_artifacts.py",
)


def test_the_vendored_snapshot_is_intact_and_dated() -> None:
    manifest = json.loads((cpic_snapshot.SNAPSHOT_DIR / "manifest.json").read_text())

    assert cpic_snapshot.verify_manifest() == []
    assert manifest["api"] == cpic_snapshot.API
    assert manifest["fetched_utc"].startswith("20")
    assert set(manifest["files"]) == set(cpic_snapshot.ENDPOINTS)


def test_the_jar_agrees_with_cpic_except_the_enumerated_rows() -> None:
    """AC1. Anything not in EXPECTED_DIFFERENCES is new and must be explained."""
    assert cpic_snapshot.diff() == cpic_snapshot.EXPECTED_DIFFERENCES


def test_no_recommendation_text_differs_for_an_implemented_drug() -> None:
    """The part of AC1 a user would read: every shown sentence is CPIC's today."""
    implemented = {"clopidogrel", "simvastatin", "azathioprine", "fluorouracil", "capecitabine"}
    result = cpic_snapshot.diff()

    assert not [row for row in result["text_differences"] if row["drug"] in implemented]
    assert not set(result["pharmcat_only_rows"]) & implemented
    assert not set(result["api_only_rows"]) & implemented


def test_the_expectation_table_regenerates_unchanged_from_the_jar() -> None:
    """AC2: the 105 rows are the jar's rows, not a hand-kept list."""
    import validate_label_mapping as vlm  # noqa: PLC0415

    fresh = vlm.build_table()
    committed = vlm.load_table()

    assert len(committed) == 105
    assert fresh == committed


def test_required_positions_regenerate_from_pharmcats_positions_vcf() -> None:
    """AC5 (part 1), and the missing generator named by the data file (F-18)."""
    assert build_position_requirements.differences() == {}


def test_decision_critical_positions_rederive_unchanged() -> None:
    """AC5 (part 2): the join of translation and phenotype files, recomputed."""
    import derive_decision_critical as ddc  # noqa: PLC0415

    requirements = json.loads(
        (REPO_ROOT / "backend/app/data/position_requirements.json").read_text()
    )
    for gene, spec in requirements["genes"].items():
        derived = ddc.derive(gene)
        fresh = [[p["chromosome"], p["position"]] for p in derived["critical_positions"]]
        committed = [list(p) for p in spec["decision_critical_positions"]]
        assert sorted(map(tuple, fresh)) == sorted(map(tuple, committed)), gene


def _clean(text: str) -> str:
    text = html.unescape(re.sub(r"</?[a-zA-Z][^>]*>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def test_no_stored_explanation_rests_on_a_superseded_cpic_row() -> None:
    """
    AC6: every stored entry's source text is still a current CPIC row.

    If a data update ever changes a row an entry was written from, this goes red
    and that entry's adjudication is no longer valid; it must be listed and
    re-reviewed, never silently regenerated.
    """
    _functions, rows = cpic_snapshot.jar_tables()
    current = {}
    for (drug, _lookup, _population), text in rows.items():
        current.setdefault(drug, set()).add(text)

    store = static_store.load_store()
    sourced = [e for e in store.entries.values() if e.cpic_recommendation_used]
    stale = [
        f"{entry.drug}/{entry.phenotype}"
        for entry in sourced
        if _clean(entry.cpic_recommendation_used) not in current.get(entry.drug, set())
    ]
    # Positive control: the six Unknown-phenotype entries carry no CPIC text, so
    # 14 of 20 are checked. A check over zero entries would pass vacuously.
    assert len(sourced) == 14
    assert stale == []
