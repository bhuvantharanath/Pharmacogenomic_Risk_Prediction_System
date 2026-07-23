"""
Table-driven tests for the CPIC -> risk label mapping.

Two layers:

1. `TestRealCpicText` pins the outcome for CPIC wording **copied verbatim from
   real PharmCAT 3.4.0 output**. These are the regression tests that matter: the
   rule ORDER in label_mapping.yaml is load-bearing, and reordering it silently
   changes clinical labels. Each row records the genotype it came from.

2. `TestSyntheticText` probes the rules with constructed strings, to document
   intent at the boundaries.

If you add a rule to label_mapping.yaml, add a row here.
"""

from __future__ import annotations

import pytest

from app.cpic_engine import (
    classify_annotation,
    derive_confidence,
    derive_severity,
    load_mapping,
    map_phenotype,
)
from app.models import Phenotype, RiskLabel, Severity
from app.pharmcat_models import CallStatus, CpicAnnotation


def annotation(
    recommendation: str = "",
    implications: str = "",
    *,
    dosing: bool = False,
    alternate: bool = False,
    classification: str = "Strong",
) -> CpicAnnotation:
    return CpicAnnotation(
        drug_recommendation=recommendation,
        implications=[implications] if implications else [],
        classification=classification,
        dosing_information=dosing,
        alternate_drug_available=alternate,
    )


# --------------------------------------------------------------------------- #
# (label, rule_id, recommendation, implications, flags) captured from real runs
# --------------------------------------------------------------------------- #

REAL_CPIC_ROWS = [
    pytest.param(
        "clopidogrel / CYP2C19 *2/*2 (Poor Metabolizer)",
        "Avoid clopidogrel if possible. Use prasugrel or ticagrelor at standard "
        "dose if no contraindication.",
        "CYP2C19: Significantly reduced clopidogrel active metabolite formation; "
        "increased on-treatment platelet reactivity; increased risk for adverse "
        "cardiac and cerebrovascular events",
        {"alternate": True},
        RiskLabel.INEFFECTIVE,
        "avoid_for_lack_of_efficacy",
        id="clopidogrel-PM-ineffective",
    ),
    pytest.param(
        "clopidogrel / CYP2C19 *38/*38 (Normal Metabolizer)",
        "If considering clopidogrel, use at standard dose (75 mg/day)",
        "CYP2C19: Normal clopidogrel active metabolite formation; normal "
        "on-treatment platelet reactivity",
        {},
        RiskLabel.SAFE,
        "standard_dosing",
        id="clopidogrel-NM-safe",
    ),
    pytest.param(
        # The dangerous near-miss: efficacy vocabulary in a REASSURING sentence.
        "clopidogrel / CYP2C19 *17/*17 (Ultrarapid Metabolizer)",
        "If considering clopidogrel, use at standard dose (75 mg/day)",
        "CYP2C19: Increased clopidogrel active metabolite formation; lower "
        "on-treatment platelet reactivity; no association with higher bleeding risk",
        {},
        RiskLabel.SAFE,
        "standard_dosing",
        id="clopidogrel-URM-safe-despite-efficacy-words",
    ),
    pytest.param(
        "fluorouracil / DPYD Reference/Reference (Normal Metabolizer)",
        "Based on genotype, there is no indication to change dose or therapy. "
        "Use label-recommended dosage and administration.",
        'DPYD: Normal DPD activity and "normal" risk for fluoropyrimidine toxicity',
        {},
        RiskLabel.SAFE,
        "standard_dosing",
        id="fluorouracil-NM-safe-despite-toxicity-word",
    ),
    pytest.param(
        "fluorouracil / DPYD c.1905+1G>A het (Intermediate Metabolizer)",
        "Reduce starting dose by 50% followed by titration of dose based on "
        "toxicity or therapeutic drug monitoring (if available).",
        "DPYD: Decreased DPD activity (leukocyte DPD activity at 30% to 70% that "
        "of the normal population) and increased risk for severe or even fatal "
        "drug toxicity when treated with fluoropyrimidine drugs",
        {"dosing": True},
        RiskLabel.ADJUST_DOSAGE,
        "dose_change_or_monitoring",
        id="fluorouracil-IM-adjust",
    ),
    pytest.param(
        "fluorouracil / DPYD homozygous c.1905+1G>A (Poor Metabolizer)",
        "Avoid use of 5-fluorouracil or 5-fluorouracil prodrug-based regimens.",
        "DPYD: Complete DPD deficiency and increased risk for severe or even "
        "fatal drug toxicity when treated with fluoropyrimidine drugs.",
        {"alternate": True},
        RiskLabel.TOXIC,
        "avoid_for_toxicity",
        id="fluorouracil-PM-toxic",
    ),
    pytest.param(
        "azathioprine / TPMT *3A/*3A (Poor Metabolizer)",
        "Consider alternative nonthiopurine immunosuppressant therapy.",
        "Greatly increased risk of thiopurine-related leukopenia, neutropenia and "
        "myelosuppression. Fatal toxicity possible without dose decrease.",
        {"alternate": True},
        RiskLabel.TOXIC,
        "avoid_for_toxicity",
        id="azathioprine-TPMT-PM-toxic",
    ),
    pytest.param(
        "azathioprine / TPMT *1/*1 (Normal Metabolizer)",
        "Initiate therapy with standard starting dose (e.g., 2 mg/kg/day for "
        "autoimmune diseases). During therapy, adjust doses of azathioprine "
        "based on disease-specific guidelines.",
        "Normal risk of thiopurine-related leukopenia, neutropenia and "
        "myelosuppression.",
        {},
        RiskLabel.SAFE,
        "standard_dosing",
        id="azathioprine-NM-safe-despite-adjust-word",
    ),
    pytest.param(
        "simvastatin / SLCO1B1 *1/*1 (Normal Function)",
        "Prescribe desired starting dose and adjust doses based on "
        "disease-specific guidelines.",
        "SLCO1B1: Typical myopathy risk and statin exposure",
        {},
        RiskLabel.SAFE,
        "standard_dosing",
        id="simvastatin-normal-function-safe",
    ),
]


class TestRealCpicText:
    """Verbatim CPIC wording from PharmCAT 3.4.0 -> expected label."""

    @pytest.mark.parametrize(
        "provenance,recommendation,implications,flags,expected_label,expected_rule",
        REAL_CPIC_ROWS,
    )
    def test_label(
        self,
        provenance: str,
        recommendation: str,
        implications: str,
        flags: dict,
        expected_label: RiskLabel,
        expected_rule: str,
    ) -> None:
        label, rule_id, _ = classify_annotation(
            annotation(recommendation, implications, **flags)
        )
        assert label is expected_label, f"{provenance}: matched rule {rule_id!r}"
        assert rule_id == expected_rule, provenance


class TestSyntheticText:
    """Boundary probes that document rule intent."""

    @pytest.mark.parametrize(
        "recommendation,implications,expected",
        [
            ("This drug is contraindicated.", "", RiskLabel.TOXIC),
            ("Codeine should not be used.", "", RiskLabel.TOXIC),
            # Avoid with no stated reason falls to the conservative default.
            ("Avoid this drug.", "", RiskLabel.TOXIC),
            ("Use standard dosing.", "", RiskLabel.SAFE),
            ("Monitor closely and titrate.", "", RiskLabel.ADJUST_DOSAGE),
            # Nothing recognisable -> visible Unknown, never a guessed Safe.
            ("Consult a specialist.", "", RiskLabel.UNKNOWN),
        ],
    )
    def test_synthetic(
        self, recommendation: str, implications: str, expected: RiskLabel
    ) -> None:
        label, _, _ = classify_annotation(annotation(recommendation, implications))
        assert label is expected

    def test_html_entities_are_unescaped_before_matching(self) -> None:
        """PharmCAT emits entities such as `c.2846A&gt;T`."""
        label, rule_id, _ = classify_annotation(
            annotation("Reduce dose for c.2846A&gt;T carriers.", "")
        )
        assert label is RiskLabel.ADJUST_DOSAGE
        assert rule_id == "dose_change_or_monitoring"

    def test_flag_only_annotation_uses_dosing_flag(self) -> None:
        label, rule_id, _ = classify_annotation(
            annotation("Refer to the product label.", "", dosing=True)
        )
        assert label is RiskLabel.ADJUST_DOSAGE
        assert rule_id == "dosing_information_flag"

    def test_last_rule_is_the_catch_all(self) -> None:
        """The Unknown fallback must stay last or it would shadow everything."""
        rules = load_mapping()["risk_label_rules"]
        last = rules[-1]
        assert last["id"] == "fallback_unmatched"
        assert last["label"] == "Unknown"
        assert not any(k in last for k in ("any_text", "require_any_text", "all_flags"))


class TestPhenotypeMap:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("Poor Metabolizer", Phenotype.PM),
            ("poor metabolizer", Phenotype.PM),
            ("Intermediate Metabolizer", Phenotype.IM),
            ("Normal Metabolizer", Phenotype.NM),
            ("Ultrarapid Metabolizer", Phenotype.URM),
            ("Rapid Metabolizer", Phenotype.RM),
            # Transporters use function wording, not metaboliser wording.
            ("Normal Function", Phenotype.NM),
            ("Decreased Function", Phenotype.IM),
            ("Poor Function", Phenotype.PM),
            # PharmCAT's sentinels and anything unrecognised.
            ("No Result", Phenotype.UNKNOWN),
            ("Indeterminate", Phenotype.UNKNOWN),
            ("something new", Phenotype.UNKNOWN),
            (None, Phenotype.UNKNOWN),
        ],
    )
    def test_map(self, raw: str | None, expected: Phenotype) -> None:
        assert map_phenotype(raw) is expected


class TestSeverity:
    @pytest.mark.parametrize(
        "label,phenotype,hint,expected",
        [
            # Base severities.
            (RiskLabel.SAFE, Phenotype.NM, "none", Severity.NONE),
            (RiskLabel.ADJUST_DOSAGE, Phenotype.IM, "moderate", Severity.MODERATE),
            (RiskLabel.TOXIC, Phenotype.IM, "high", Severity.HIGH),
            # Extreme phenotypes escalate one step.
            (RiskLabel.TOXIC, Phenotype.PM, "high", Severity.CRITICAL),
            (RiskLabel.INEFFECTIVE, Phenotype.PM, "high", Severity.CRITICAL),
            (RiskLabel.ADJUST_DOSAGE, Phenotype.URM, "moderate", Severity.HIGH),
            # ...but Safe and Unknown never escalate.
            (RiskLabel.SAFE, Phenotype.PM, "none", Severity.NONE),
            (RiskLabel.SAFE, Phenotype.URM, "none", Severity.NONE),
            (RiskLabel.UNKNOWN, Phenotype.PM, "none", Severity.NONE),
            # Escalation saturates at the top of the scale.
            (RiskLabel.TOXIC, Phenotype.PM, "critical", Severity.CRITICAL),
        ],
    )
    def test_severity(
        self, label: RiskLabel, phenotype: Phenotype, hint: str, expected: Severity
    ) -> None:
        assert derive_severity(label, phenotype, hint) is expected


class TestConfidence:
    @pytest.mark.parametrize(
        "status,expected",
        [
            (CallStatus.DEFINITE, 0.95),
            (CallStatus.AMBIGUOUS, 0.60),
            (CallStatus.NO_CALL, 0.20),
            (CallStatus.NOT_ATTEMPTED, 0.10),
        ],
    )
    def test_by_call_status(self, status: CallStatus, expected: float) -> None:
        assert derive_confidence(status, has_guidance=True, known_drug=True) == expected

    def test_unknown_drug_is_zero(self) -> None:
        assert (
            derive_confidence(
                CallStatus.DEFINITE, has_guidance=False, known_drug=False
            )
            == 0.0
        )

    def test_no_guidance_is_low_even_for_a_definite_call(self) -> None:
        """A perfect genotype call is worthless if no CPIC row applies."""
        assert (
            derive_confidence(CallStatus.DEFINITE, has_guidance=False, known_drug=True)
            == 0.10
        )

    def test_all_values_are_valid_contract_scores(self) -> None:
        mapping = load_mapping()["confidence"]
        values = [
            *mapping["by_call_status"].values(),
            mapping["no_guidance"],
            mapping["unknown_drug"],
        ]
        assert all(0.0 <= float(v) <= 1.0 for v in values)


class TestMappingFileIntegrity:
    def test_declares_faculty_review_requirement(self) -> None:
        """The sign-off flag is part of the contract with the faculty guide."""
        assert load_mapping()["requires_faculty_review"] is True

    def test_every_rule_has_an_id_and_a_valid_label(self) -> None:
        seen: set[str] = set()
        for rule in load_mapping()["risk_label_rules"]:
            assert rule["id"] not in seen, f"duplicate rule id {rule['id']}"
            seen.add(rule["id"])
            # Raises ValueError if the YAML drifts from the contract enum.
            RiskLabel(rule["label"])
            Severity(rule.get("severity_hint", "none"))

    def test_every_phenotype_value_is_a_contract_enum_member(self) -> None:
        for value in load_mapping()["phenotype_map"].values():
            Phenotype(value)
