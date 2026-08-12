"""
Two layers stop a confident label on a phenotype nobody asserted. Both are here.

WHAT AUDIT A FOUND

Deleting the enforcement gate in `cpic_engine.evaluate` failed no test, and the
output did not change. It did not change because of a SECOND mechanism nobody
had written down: `resolve_phenotype` returns `Phenotype.UNKNOWN`, and
`label_mapping.yaml` happens to contain no rule keyed on an unasserted
phenotype, so the lookup falls through to Unknown anyway.

Safety by coincidence. Either layer could be removed by someone who had no idea
the other existed, and nothing would go red.

This file turns the coincidence into a rule. Two independent tests:

  LAYER 1  the gate refuses, and says why          test_the_gate_*
  LAYER 2  no mapping rule may key on an           test_no_mapping_rule_*
           unasserted phenotype

They are deliberately redundant AT THE OUTPUT and independent IN THE MECHANISM,
which is what defence in depth means. Redundancy that shares a failure mode is
not defence in depth; it is one layer with two names.

WHAT THE GATE IS TESTED THROUGH — AND A CORRECTION TO AUDIT A

Audit A reported that deleting the gate "does not change the output". That was
measured on the risk label alone, and it was wrong. Measured on the whole
result, deleting the gate turns a refusal into CPIC's no-change-needed
directive at 95% confidence, attributed to a real guideline row, on a DPYD
Indeterminate for fluorouracil. The label stays Unknown; the text a user reads
does not.

So the gate is tested on confidence, on the recommendation text and on the
attribution — the observables that actually move.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app import cpic_engine
from app.models import Phenotype, RiskLabel
from app.pharmcat_models import PharmcatGeneCall, PharmcatReport

#: Phenotype strings that mean "nothing was asserted". A mapping rule keyed on
#: any of these would let a confident label out over an unasserted phenotype.
UNASSERTED = ("unknown", "indeterminate", "no result", "n/a", "not called",
              "undetermined")


def _discordant_report() -> PharmcatReport:
    """
    A synthetic discordant call, for the resolver-level assertions.

    NOT used for the gate tests: with no guideline attached, `evaluate` exits at
    the "drug not covered by any CPIC guideline" branch BEFORE the gate is
    reached, so it cannot show anything about the gate. That mistake is what
    made the first version of this file assert the wrong observable.
    """
    call = PharmcatGeneCall(
        gene="SLCO1B1", diplotype="*37/*37", phenotype="Normal Function",
        candidate_diplotypes=["*37/*37", "*37/*42"],
        candidate_phenotypes=["Normal Function", "Indeterminate"],
        status="definite", warnings=[],
    )
    return PharmcatReport(pharmcat_version="3.4.0",
                          genes={"SLCO1B1": call}, drugs={})


def _real_indeterminate_report():
    """
    A REAL PharmCAT report with a real CPIC guideline attached, so `evaluate`
    actually reaches the gate. Captured from `demo_dpyd_indeterminate.vcf`.
    """
    import json
    from app.pharmcat_runner import parse_report

    path = (Path(__file__).parent / "fixtures"
            / "pharmcat_report_dpyd_compound_het.json")
    if not path.exists():  # pragma: no cover
        pytest.skip("compound-het fixture not captured")
    return parse_report(json.loads(path.read_text()), sample_hint="dpyd")


# --------------------------------------------------------------------------- #
# LAYER 1 — the enforcement gate
# --------------------------------------------------------------------------- #

def test_the_gate_refuses_a_confident_label() -> None:
    risk, _rec, _call, _warnings = cpic_engine.evaluate(
        "fluorouracil", _real_indeterminate_report())
    assert risk.risk_label is RiskLabel.UNKNOWN
    assert risk.confidence_score < 0.5


def test_deleting_the_gate_changes_the_recommendation_and_this_catches_it() -> None:
    """
    SABOTAGE TEST for layer 1, on the observable that actually moves.

    Audit A reported "the output does not change" when the gate is deleted.
    That was measured on the RISK LABEL alone and was wrong. Measured on the
    whole result, deleting the gate produces:

        confidence   0.1  ->  0.95
        action       "DPYD: PharmCAT returned 'Indeterminate' ... no
                      pharmacogenomic recommendation can be made"
                     ->
                     "Based on genotype, there is no indication to change dose
                      or therapy. Use label-recommended dosage"
        source       "PharmCAT (no matching CPIC entry)"
                     -> "Annotation of CPIC Guideline for fluorouracil and DPYD"

    The label stays Unknown because layer 2 holds, but the text the user reads
    becomes CPIC's no-change-needed directive, at 95% confidence, attributed to
    a real guideline — on a DPYD Indeterminate for fluorouracil. That is worse
    than a missing explanation, and it is what this test pins.
    """
    risk, rec, _call, warnings = cpic_engine.evaluate(
        "fluorouracil", _real_indeterminate_report())

    assert risk.confidence_score < 0.5, (
        f"confidence {risk.confidence_score} on an unasserted phenotype — the "
        f"enforcement gate has been removed or bypassed"
    )
    action = rec.action.lower()
    assert "no indication to change dose" not in action, (
        "CPIC's no-change directive is being shown for a phenotype PharmCAT "
        "never asserted"
    )
    assert "annotation of cpic guideline" not in rec.source.lower(), (
        f"the refusal is attributed to a CPIC row it did not come from: "
        f"{rec.source!r}"
    )
    assert any("rather than assuming" in w for w in warnings), (
        f"the gate's explanation is missing from {warnings!r}"
    )


def test_the_resolver_still_declines_to_assert() -> None:
    """Layer 1's input. If this flips, the gate never fires and layer 2 is alone."""
    resolved = cpic_engine.resolve_phenotype(_discordant_report().gene("SLCO1B1"))
    assert resolved.asserted is False
    assert resolved.phenotype is not Phenotype.NM


# --------------------------------------------------------------------------- #
# LAYER 2 — the mapping may not key on an unasserted phenotype
# --------------------------------------------------------------------------- #

def _mapping() -> dict:
    return yaml.safe_load(
        (cpic_engine.MAPPING_PATH).read_text())


def test_no_mapping_rule_keys_on_an_unasserted_phenotype() -> None:
    """
    THE RULE THAT WAS ONLY EVER AN ACCIDENT.

    Nothing prevented someone adding a rule matching an Unknown or
    Indeterminate phenotype. Such a rule would let a confident label out the
    moment layer 1 was touched — and layer 1 was demonstrably deletable without
    a single test failing.

    Now it is asserted. If a rule like that is ever added, this fails and the
    author has to justify it rather than discover the consequence later.
    """
    mapping = _mapping()
    offenders: list[str] = []

    for rule in mapping.get("risk_label_rules", []) or []:
        rule_id = rule.get("id", "<unnamed>")
        label = str(rule.get("label", "")).strip().lower()
        if label in ("unknown", ""):
            continue  # a rule that yields Unknown is the safe direction

        for key in ("phenotype", "phenotypes", "phenotype_in", "match_phenotype"):
            value = rule.get(key)
            if value is None:
                continue
            values = value if isinstance(value, (list, tuple)) else [value]
            for entry in values:
                if str(entry).strip().lower() in UNASSERTED:
                    offenders.append(
                        f"{rule_id}: {key}={entry!r} -> label={rule.get('label')!r}")

    assert not offenders, (
        "a mapping rule keys a CONFIDENT label on an unasserted phenotype:\n  "
        + "\n  ".join(offenders)
        + "\nThis is the second layer of the unasserted-phenotype defence. "
          "See the header of label_mapping.yaml."
    )


def test_the_phenotype_table_has_no_confident_entry_for_an_unasserted_state() -> None:
    """
    The same property one level down: the phenotype->label table itself must not
    map an unasserted state onto anything but Unknown.
    """
    for phenotype in (Phenotype.UNKNOWN,):
        for label in (RiskLabel.SAFE, RiskLabel.TOXIC, RiskLabel.INEFFECTIVE,
                      RiskLabel.ADJUST_DOSAGE):
            assert cpic_engine.check_phenotype_label(phenotype, label) is not None, (
                f"{phenotype.value} paired with {label.value} is not flagged as a "
                f"violation — the invariant check has been weakened"
            )


@pytest.mark.parametrize("state", UNASSERTED)
def test_every_unasserted_spelling_maps_to_unknown(state: str) -> None:
    """
    PharmCAT's wording varies by gene and release: `Indeterminate`,
    `No Result`, `n/a`. A rule that handles only one spelling leaves the others
    to fall through, which is how a phenotype nobody asserted becomes a lookup
    key.
    """
    assert cpic_engine.map_phenotype(state) is Phenotype.UNKNOWN, (
        f"{state!r} does not map to Unknown — it could be used as a lookup key"
    )
