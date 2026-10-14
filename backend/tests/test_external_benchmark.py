"""Regression tests for the frozen independent external benchmark."""

from __future__ import annotations

import importlib.util
import csv
import hashlib
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "benchmark_external", REPO / "scripts" / "benchmark_external.py"
)
assert SPEC and SPEC.loader
benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark
SPEC.loader.exec_module(benchmark)


def test_equivalence_is_allele_order_only() -> None:
    assert benchmark.same_diplotype("*1/*2", "*2/*1")
    assert not benchmark.same_diplotype("*1A/*1B", "*1/*1")
    assert not benchmark.same_diplotype("*1/(*4)", "*1/*4")


def test_ambiguous_and_non_diplotype_truth_are_not_forced() -> None:
    assert benchmark.normalize_diplotype("")[0] == "truth_blank"
    assert benchmark.normalize_diplotype("*8/*33 or *1/*46")[0] == "truth_unresolved_or_discordant"
    assert benchmark.normalize_diplotype("c.85T>C het")[0] == "truth_nomenclature_not_safely_parseable"


def test_candidate_compatibility_does_not_become_exact() -> None:
    candidates = ["*1/*2", "*1/*3"]
    assert benchmark.candidate_compatible("*2/*1", candidates)
    assert len(candidates) != 1


def test_pharmcat_none_unknown_pair_is_an_abstention() -> None:
    raw = {
        "genes": {
            "CYP2D6": {
                "callSource": "NONE",
                "sourceDiplotypes": [
                    {"label": "Unknown/Unknown", "phenotypes": ["No Result"]}
                ],
            }
        }
    }
    call = benchmark._raw_pharmcat_calls(raw)["CYP2D6"]
    assert call["diplotypes"] == []
    assert call["phenotypes"] == []


def test_wilson_interval_requires_five_independent_people() -> None:
    assert benchmark.wilson(4, 4) is None
    interval = benchmark.wilson(4, 5)
    assert interval is not None
    assert 0 < interval["lower"] < interval["upper"] < 1
    assert benchmark.wilson(0, 100)["lower"] == 0.0


def test_zero_denominator_is_not_reported_as_zero_percent() -> None:
    metric = benchmark.proportion(0, 0)
    assert metric["proportion"] is None
    assert metric["confidence_interval"] is None


def test_summary_has_no_pooled_accuracy_and_no_inferred_actionability() -> None:
    result = benchmark.summarize([], [], [], reports=0, cohort=0)
    assert result["pooled_accuracy"] is None
    for gene in result["genes"].values():
        assert gene["false_reassurance"]["denominator"] == 0
        assert gene["false_warning"]["denominator"] == 0
        assert gene["phenotype_concordance"]["denominator"] == 0


def test_frozen_cohort_and_truth_table_have_not_drifted() -> None:
    base = REPO / "test-data" / "benchmark" / "external"
    lock = json.loads((base / "cohort_lock.json").read_text())
    truth_bytes = (base / "sample_gene_truth.tsv").read_bytes()
    truth_rows = list(csv.DictReader(truth_bytes.decode().splitlines(), delimiter="\t"))
    assert lock["sample_count"] == 208
    assert len(truth_rows) == 208 * 7
    assert len({(row["sample_id"], row["gene"]) for row in truth_rows}) == len(truth_rows)
    assert hashlib.sha256(truth_bytes).hexdigest() == lock["sample_gene_truth_sha256"]
    assert lock["performance_output_examined_before_lock"] is False


def test_negative_full_pipeline_finding_is_preserved() -> None:
    path = REPO / "test-data" / "benchmark" / "external" / "external_benchmark_results.json"
    result = json.loads(path.read_text())
    assert result["pooled_accuracy"] is None
    for gene in result["genes"].values():
        layer = gene["layer_B_application"]
        assert layer["input_eligible"]["numerator"] == 0
        assert layer["exact_assertion_coverage"]["numerator"] == 0
        assert layer["abstention"]["numerator"] == gene["truth_evaluable"]
