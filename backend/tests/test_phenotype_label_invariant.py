"""
The phenotype -> label invariant: the third missing edge in the verification graph.

    provenance guard      explanation -> CPIC     checked
    mapping validation    label       -> CPIC     checked
    consistency check     explanation -> label    checked
    THIS                  phenotype   -> label    was NOT checked

All three previously-missing edges produced the same directional failure: the
pipeline sounded more certain than its evidence. This one is the most dangerous
instance, because the label is the badge a user actually reads.

    A phenotype the caller declined to assert can never produce a confident label.

Measured effect on 400 real 1000 Genomes samples: 294 (drug, sample) labels moved
to Unknown, every single one removing a confident label — simvastatin 195,
fluorouracil 98, azathioprine 1.
"""

from __future__ import annotations

import pytest

from app.cpic_engine import (
    check_phenotype_label,
    resolve_phenotype,
)
from app.models import Phenotype, RiskLabel
from app.pharmcat_runner import _parse_gene


def _gene(symbol: str, candidates: list[tuple[str, str, list[str]]]):
    """Build a gene block from (label, phenotype, lookupKey) triples."""
    entries = [
        {"label": lbl, "phenotypes": [phen], "lookupKey": keys}
        for lbl, phen, keys in candidates
    ]
    return _parse_gene(symbol, {
        "callSource": "MATCHER",
        "sourceDiplotypes": entries,
        "recommendationDiplotypes": entries,
    })


# --------------------------------------------------------------------------- #
# The fatal case
# --------------------------------------------------------------------------- #


def test_dpyd_indeterminate_cannot_produce_a_confident_label() -> None:
    """
    The fixture that motivated the invariant.

    PharmCAT called `Indeterminate`. Its `recommendationDiplotypes` still carry
    activity score 2.0, so the CPIC lookup finds the Normal Metabolizer row and
    the label engine renders `Safe` — green, on fluorouracil, where DPYD
    deficiency is fatal.

    The lookup key is not a claim about the patient. It exists to FIND A TABLE
    ROW. Deriving a risk label from it repeats the sourceDiplotypes category
    error one layer up.
    """
    call = _parse_gene("DPYD", {
        "callSource": "MATCHER",
        "sourceDiplotypes": [{
            "label": "c.85T>C (*9A)/[c.85T>C (*9A) + c.1371C>T]",
            "phenotypes": ["Indeterminate"],
            "lookupKey": ["n/a"],
        }],
        "recommendationDiplotypes": [{
            "label": "c.85T>C (*9A)/c.85T>C (*9A)",
            "phenotypes": ["Normal Metabolizer"],
            "activityScore": 2.0,
            "lookupKey": ["2.0"],
        }],
    })
    resolved = resolve_phenotype(call)

    assert resolved.asserted is False
    assert resolved.phenotype is Phenotype.UNKNOWN
    # The gate must starve the lookup, not merely correct it afterwards.
    assert resolved.lookup_keys == (), (
        "an unasserted phenotype must not reach the CPIC lookup at all"
    )


@pytest.mark.parametrize("label", [
    RiskLabel.SAFE, RiskLabel.TOXIC, RiskLabel.INEFFECTIVE, RiskLabel.ADJUST_DOSAGE,
])
def test_unknown_phenotype_with_any_confident_label_is_a_violation(label) -> None:
    assert check_phenotype_label(Phenotype.UNKNOWN, label) is not None


def test_known_phenotype_with_unknown_label_is_allowed() -> None:
    """
    One-directional on purpose.

    CPIC may have no guidance for a (gene, drug) pair — warfarin's is an algorithm,
    not per-phenotype text. That is a gap in the table, not a contradiction about
    what we know, so it must not be flagged.
    """
    for phenotype in (Phenotype.PM, Phenotype.NM, Phenotype.URM):
        assert check_phenotype_label(phenotype, RiskLabel.UNKNOWN) is None


# --------------------------------------------------------------------------- #
# Ambiguity: keyed on PHENOTYPE, never on diplotype
# --------------------------------------------------------------------------- #


def test_discordant_candidates_assert_nothing() -> None:
    """
    195 of 400 real samples. `Normal Function` against `Indeterminate` — one green,
    one no-call — and reading candidate[0] rendered `Safe` for 49% of the cohort.

    `Indeterminate` is a CLAIM (this genotype has no phenotype assignment), not an
    absence of one. It must count as disagreement. An earlier version of the
    resolver dropped every UNKNOWN-mapping candidate before comparing, which
    collapsed {Normal Function, Indeterminate} to {NM} and left all 195 samples
    exactly as broken as before.
    """
    call = _gene("SLCO1B1", [
        ("*37/*37", "Normal Function", ["Normal Function"]),
        ("*37/*42", "Indeterminate", ["Indeterminate"]),
        ("*37/*52", "n/a", ["n/a"]),
    ])
    resolved = resolve_phenotype(call)
    assert resolved.asserted is False, (
        "candidates disagreeing about function must not yield a confident phenotype"
    )
    assert resolved.phenotype is Phenotype.UNKNOWN


def test_concordant_candidates_still_produce_a_confident_phenotype() -> None:
    """
    The other 30 samples, and the reason this keys on phenotype rather than on
    diplotype ambiguity.

    Every informative candidate reads `Decreased Function` or `Possible Decreased
    Function`. Both mean decreased transporter function, so the simvastatin
    myopathy risk IS known even though the exact star alleles are not. Suppressing
    these would trade over-claiming for under-claiming — the same error mirrored.
    """
    call = _gene("SLCO1B1", [
        ("*5/*37", "Decreased Function", ["Decreased Function"]),
        ("*5/*42", "Possible Decreased Function", ["Possible Decreased Function"]),
        ("*5/*52", "n/a", ["n/a"]),
        ("*5/*56", "n/a", ["n/a"]),
    ])
    resolved = resolve_phenotype(call)

    assert resolved.asserted is True
    assert resolved.phenotype is Phenotype.IM
    # Keys from every informative candidate, so a CPIC row can still be matched.
    assert "Decreased Function" in resolved.lookup_keys
    assert len(call.candidate_diplotypes) == 4, "the ambiguity itself is preserved"


def test_all_candidates_indeterminate_asserts_nothing() -> None:
    """Ten samples. Unanimity about having no assignment is still no assignment."""
    call = _gene("SLCO1B1", [
        ("*42/*42", "Indeterminate", ["Indeterminate"]),
        ("*42/*52", "Indeterminate", ["Indeterminate"]),
    ])
    assert resolve_phenotype(call).asserted is False


def test_unambiguous_call_is_unaffected() -> None:
    call = _gene("CYP2C19", [("*1/*2", "Intermediate Metabolizer",
                             ["Intermediate Metabolizer"])])
    resolved = resolve_phenotype(call)
    assert resolved.asserted is True
    assert resolved.phenotype is Phenotype.IM


# --------------------------------------------------------------------------- #
# Sabotage
# --------------------------------------------------------------------------- #


def test_reverting_the_invariant_is_detected() -> None:
    """
    Fails if someone restores the pre-fix behaviour of asserting candidate[0].

    Written as an explicit simulation rather than a mock so the thing being
    forbidden is visible in the test source.
    """
    from app.cpic_engine import map_phenotype

    call = _gene("SLCO1B1", [
        ("*37/*37", "Normal Function", ["Normal Function"]),
        ("*37/*42", "Indeterminate", ["Indeterminate"]),
    ])
    naive = map_phenotype(call.candidate_phenotypes[0])
    assert naive is Phenotype.NM, "test premise: candidate[0] alone looks confident"

    resolved = resolve_phenotype(call)
    assert resolved.phenotype is not naive, (
        "resolver agrees with the naive candidate[0] reading — the invariant has "
        "been reverted and 195 samples would render a false Safe again"
    )


def test_build_time_no_reachable_case_violates_the_invariant() -> None:
    """
    BUILD-TIME EDGE: every reachable (drug, phenotype) case, checked at once.

    The request-time check degrades a violation to Unknown, which protects the
    user but hides the bug. This one fails the build instead, so a mapping change
    that reintroduces a confident label over an unasserted phenotype cannot ship.
    """
    import importlib.util
    import sys
    from pathlib import Path

    scripts = Path(__file__).resolve().parents[2] / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(
        "pregenerate_explanations", scripts / "pregenerate_explanations.py"
    )
    pg = importlib.util.module_from_spec(spec)
    sys.modules["pregenerate_explanations"] = pg
    spec.loader.exec_module(pg)

    violations = []
    for case in pg.load_reachable_cases():
        context, _ = pg.build_context(case)
        problem = check_phenotype_label(context.phenotype, context.risk_label)
        if problem:
            violations.append(f"{case.key}: {problem}")
    assert not violations, (
        "reachable cases pair a confident label with an unasserted phenotype:\n  "
        + "\n  ".join(violations)
    )
