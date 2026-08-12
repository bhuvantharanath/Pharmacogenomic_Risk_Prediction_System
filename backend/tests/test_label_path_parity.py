"""
The build-time enumeration and the runtime must derive labels identically.

WHY

They did not. The runtime gated on the phenotype before selecting an
annotation; `scripts/pregenerate_explanations.py` called `classify_annotation`
directly with no gate. On `fluorouracil` with an unasserted phenotype the
runtime refused and the enumeration derived `Safe`.

It went unnoticed because no fixture made that case reachable for the
build-time check. One real Indeterminate DPYD report made it reachable and the
invariant test went red immediately — the check was working; it had never been
given the input.

Both now call `cpic_engine.derive_label`. This file asserts they keep agreeing,
so a future divergence fails here rather than being discovered by whichever
fixture happens to arrive next.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from app import cpic_engine
from app.models import Phenotype, RiskLabel

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


@pytest.fixture(scope="module")
def pregen():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "pregenerate_explanations", SCRIPTS / "pregenerate_explanations.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["pregenerate_explanations"] = module
    spec.loader.exec_module(module)
    return module


def test_there_is_exactly_one_label_derivation(pregen) -> None:
    """
    Sabotage check. The enumeration must not grow its own copy again — two
    implementations of one rule is precisely how they drifted.
    """
    source = (SCRIPTS / "pregenerate_explanations.py").read_text()
    assert "derive_label(" in source
    assert "classify_annotation(" not in source, (
        "the enumeration is classifying annotations directly again, bypassing "
        "the phenotype invariant in cpic_engine.derive_label"
    )


def test_both_paths_agree_on_every_reachable_case(pregen) -> None:
    """
    The parity assertion. For every reachable (drug, gene, phenotype), the label
    the enumeration derives must equal the label the shared function derives
    from the same annotation.
    """
    disagreements: list[str] = []

    for case in pregen.load_reachable_cases():
        context, _ = pregen.build_context(case)
        phenotype = Phenotype(case.phenotype)
        annotation, _gene = pregen.find_annotation(case.drug, phenotype)

        expected, _rule, _hint = cpic_engine.derive_label(phenotype, annotation)
        if context.risk_label is not expected:
            disagreements.append(
                f"{case.drug}:{case.phenotype} enumeration={context.risk_label.value} "
                f"shared={expected.value}")

    assert not disagreements, (
        "the two label-derivation paths disagree:\n  " + "\n  ".join(disagreements))


def test_no_reachable_case_pairs_a_confident_label_with_an_unasserted_phenotype(
    pregen,
) -> None:
    """
    The property the disagreement was hiding, asserted directly. This is the
    test that went red when the DPYD fixture arrived; it stays as the check that
    the unification actually fixed the cause rather than the symptom.
    """
    violations = [
        f"{case.drug}:{case.phenotype}"
        for case in pregen.load_reachable_cases()
        if cpic_engine.check_phenotype_label(
            Phenotype(case.phenotype), pregen.build_context(case)[0].risk_label)
    ]
    assert not violations, (
        "reachable cases pair a confident label with an unasserted phenotype: "
        + ", ".join(violations))


def test_the_shared_function_refuses_an_unasserted_phenotype() -> None:
    """
    Unit-level. `derive_label` must refuse regardless of what the annotation
    says, and must name WHY so a caller can tell a refusal from an absence.
    """
    from app.pharmcat_models import CpicAnnotation

    confident = CpicAnnotation(
        drug_recommendation="Based on genotype, there is no indication to "
                            "change dose or therapy.",
        implications=["Normal metabolism"], classification="Strong",
        dosing_information=False, alternate_drug_available=False,
        other_prescribing_guidance=False,
    )
    baseline, rule, _ = cpic_engine.derive_label(Phenotype.NM, confident)
    assert baseline is not RiskLabel.UNKNOWN, "test premise: a confident row"

    label, rule, _ = cpic_engine.derive_label(Phenotype.UNKNOWN, confident)
    assert label is RiskLabel.UNKNOWN
    assert rule == "unasserted_phenotype", (
        f"the refusal is not distinguishable from 'no guidance': rule={rule!r}")


def test_a_missing_annotation_is_reported_as_such() -> None:
    label, rule, _ = cpic_engine.derive_label(Phenotype.NM, None)
    assert label is RiskLabel.UNKNOWN
    assert rule == "no_annotation"
