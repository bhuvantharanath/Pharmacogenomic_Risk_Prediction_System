"""
PharmaGuard — CPIC recommendation -> contract fields.

This is the interpretation layer, and the only place in the backend where a
clinical judgement is made. It is deliberately thin and deliberately boring:

  * All clinical *text* (dosing guidance, recommendation, implications) is
    copied verbatim from PharmCAT's CPIC output. This module never composes
    clinical prose.
  * The one derived value is `risk_label`, produced by ordered rules declared in
    `data/label_mapping.yaml` — data, not code. Adding a rule means editing YAML
    and adding a test row, not editing an if-chain here.
  * `severity` and `confidence_score` are pure functions of already-derived
    values, with their tables in the same YAML file.

Read the header of `data/label_mapping.yaml` before changing anything: the rule
ORDER is load-bearing and was validated against real PharmCAT output.

EVIDENCE LEVEL — an honest gap
    Our JSON contract has `cpic_evidence_level: A|B|C|D|Unknown`, meaning CPIC's
    *level of evidence* for a gene-drug pair. PharmCAT's report JSON does not
    carry that field (verified against 3.4.0 output — grep found no
    levelOfEvidence/evidenceLevel key anywhere). What it does carry is
    `classification`: the CPIC *strength of recommendation*, one of
    Strong/Moderate/Optional/Unspecified. Those are different scales.

    So `cpic_evidence_level` is reported as "Unknown" and the strength is
    surfaced verbatim inside `cpic_recommendation` instead. Inventing an A-D
    grade from the strength would be fabricating a clinical claim.
    TODO(phase4): pull real CPIC levels from the CPIC API and populate properly.
"""

from __future__ import annotations

import functools
import html
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .models import (
    ClinicalRecommendation,
    CpicEvidenceLevel,
    PerDrugResult,
    Phenotype,
    RiskAssessment,
    RiskLabel,
    Severity,
)
from .pharmcat_models import (
    CallStatus,
    CpicAnnotation,
    CpicDrugGuideline,
    PharmcatGeneCall,
    PharmcatReport,
)

MAPPING_PATH = Path(__file__).parent / "data" / "label_mapping.yaml"


@dataclass(frozen=True)
class LabelDecision:
    """The outcome of the mapping, including *why* — for the audit trail."""

    risk_label: RiskLabel
    severity: Severity
    confidence: float
    # Which YAML rule fired. Surfaced in the response so a reviewer can trace
    # any label back to the rule that produced it.
    rule_id: str
    rationale: str


class MappingConfigError(RuntimeError):
    """The YAML is missing or malformed — a deploy-time bug, not a user error."""


@functools.lru_cache(maxsize=1)
def load_mapping(path: Path | None = None) -> dict:
    """Load and lightly validate the mapping file. Cached; call cache_clear in tests."""
    target = path or MAPPING_PATH
    try:
        data = yaml.safe_load(target.read_text())
    except FileNotFoundError as exc:
        raise MappingConfigError(f"Label mapping file not found: {target}") from exc
    except yaml.YAMLError as exc:
        raise MappingConfigError(f"Label mapping file is not valid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise MappingConfigError(f"{target} did not parse to a mapping.")
    for key in ("phenotype_map", "risk_label_rules", "severity", "confidence"):
        if key not in data:
            raise MappingConfigError(f"{target} is missing required section '{key}'.")
    if not data["risk_label_rules"]:
        raise MappingConfigError(f"{target} declares no risk_label_rules.")
    return data


# --------------------------------------------------------------------------- #
# Phenotype
# --------------------------------------------------------------------------- #


def map_phenotype(raw: str | None, mapping: dict | None = None) -> Phenotype:
    """
    PharmCAT's phenotype wording -> our contract enum.

    Unrecognised wording becomes Unknown rather than guessing: a phenotype we
    cannot place is exactly the case where a wrong guess would be invisible.
    """
    cfg = mapping or load_mapping()
    if not raw:
        return Phenotype.UNKNOWN
    value = cfg["phenotype_map"].get(raw.strip().lower())
    if value is None:
        return Phenotype.UNKNOWN
    try:
        return Phenotype(value)
    except ValueError:
        return Phenotype.UNKNOWN


def map_phenotype_noted(
    raw: str | None, mapping: dict | None = None
) -> tuple[Phenotype, str | None]:
    """
    `map_phenotype`, plus a warning when the enum loses information.

    WHY THIS EXISTS

    `Phenotype.UNKNOWN` conflates two clinically different states:

        NO RESULT      the gene was not called — coverage, no data, a failed run
        INDETERMINATE  the gene WAS called, but the diplotype has no CPIC
                       phenotype assignment

    In the first, we know nothing. In the second, we ran the assay and got an
    answer that CPIC's table cannot classify. Collapsing them makes the served
    prose assert the stronger claim — "no result" — for a case where a result
    exists. That is a falsehood the pipeline generates about its own inputs.

    The honest fix is a distinct enum value, which is a schema change across
    Pydantic, the response contract, and the Dart client. Deferred deliberately;
    see PROJECT_STATUS. Until then the distinction is carried here, where it costs
    nothing and hides nothing: the raw string PharmCAT returned is surfaced
    verbatim, so a reader of the response can always tell which state produced
    the Unknown. A warning is strictly weaker than a typed field — it is not
    machine-checkable by the client — and that limitation is the reason this is
    a deferral rather than a solution.
    """
    cfg = mapping or load_mapping()
    phenotype = map_phenotype(raw, cfg)
    if phenotype is not Phenotype.UNKNOWN:
        return phenotype, None
    text = (raw or "").strip()
    if not text:
        # Genuinely no result. The enum says exactly what happened.
        return phenotype, None
    return phenotype, (
        f"PharmCAT returned the phenotype {text!r}, which this build reports as "
        f"Unknown. A result WAS obtained for this gene — 'Unknown' here means the "
        f"call could not be placed in a CPIC phenotype class, not that data was "
        f"missing. The response contract has no separate value for that state yet."
    )


# --------------------------------------------------------------------------- #
# Rule matching
# --------------------------------------------------------------------------- #


def _annotation_text(annotation: CpicAnnotation) -> str:
    """
    The haystack the rules match against: recommendation + implications.

    HTML-unescaped because PharmCAT emits entities such as `c.2846A&gt;T`, and
    left lower-cased because all rule phrases are lower-case.
    """
    parts = [annotation.drug_recommendation or "", *annotation.implications]
    return html.unescape(" ".join(parts)).lower()


def _rule_matches(rule: dict, text: str, annotation: CpicAnnotation) -> bool:
    """
    A rule matches when every condition it declares is satisfied.

    A rule declaring no conditions matches everything — that is how the
    `fallback_unmatched` catch-all works, and why it must stay last.
    """
    any_text = rule.get("any_text")
    if any_text and not any(phrase.lower() in text for phrase in any_text):
        return False

    require_any = rule.get("require_any_text")
    if require_any and not any(phrase.lower() in text for phrase in require_any):
        return False

    # Regex conditions exist because some distinctions are structural, not
    # lexical. The substring collision found by the Phase 6 validation is the
    # motivating case: "30-80% of standard starting dose" contains the phrase
    # "standard starting dose", so no list of substrings can tell a MODIFIED
    # dose instruction from an unmodified one. That needs to see the modifier
    # governing the phrase, which needs a pattern.
    # `match_field: recommendation` narrows a rule to the directive alone.
    # Implications describe biology and may mention dose or risk even where CPIC
    # gives no directive, so a rule establishing whether a directive EXISTS must
    # not read them. See the `no_cpic_guidance` rationale.
    scoped = text
    if rule.get("match_field") == "recommendation":
        scoped = html.unescape(annotation.drug_recommendation or "").lower()

    any_regex = rule.get("any_text_regex")
    if any_regex and not any(re.search(p, scoped, re.IGNORECASE) for p in any_regex):
        return False

    none_regex = rule.get("none_text_regex")
    if none_regex and any(re.search(p, text, re.IGNORECASE) for p in none_regex):
        return False

    for flag, expected in (rule.get("all_flags") or {}).items():
        if getattr(annotation, flag, None) != expected:
            return False

    return True


def classify_annotation(
    annotation: CpicAnnotation, mapping: dict | None = None
) -> tuple[RiskLabel, str, str]:
    """
    Apply the ordered rules to one CPIC annotation.

    Returns (risk_label, rule_id, matched_severity_hint).
    """
    cfg = mapping or load_mapping()
    text = _annotation_text(annotation)

    for rule in cfg["risk_label_rules"]:
        if _rule_matches(rule, text, annotation):
            return (
                RiskLabel(rule["label"]),
                str(rule["id"]),
                str(rule.get("severity_hint", "none")),
            )

    # Unreachable while the YAML keeps its catch-all, but never guess.
    return RiskLabel.UNKNOWN, "no_rule_matched", "none"


# --------------------------------------------------------------------------- #
# Severity and confidence
# --------------------------------------------------------------------------- #


def derive_severity(
    risk_label: RiskLabel,
    phenotype: Phenotype,
    severity_hint: str,
    mapping: dict | None = None,
) -> Severity:
    """
    severity = f(risk_label, phenotype extremity).

    The matched rule's `severity_hint` sets the base; an extreme phenotype
    (PM/URM) escalates one step, because the same recommendation carries more
    consequence at the ends of the activity range.
    """
    cfg = mapping or load_mapping()
    section = cfg["severity"]
    scale: list[str] = section["scale"]

    base = severity_hint or section["base_by_label"].get(risk_label.value, "none")
    if base not in scale:
        base = section["base_by_label"].get(risk_label.value, "none")

    if risk_label.value not in section.get("never_escalate_labels", []):
        if phenotype.value in section.get("escalate_one_step_for_phenotypes", []):
            index = min(scale.index(base) + 1, len(scale) - 1)
            base = scale[index]

    return Severity(base)


def derive_confidence(
    status: CallStatus,
    *,
    has_guidance: bool,
    known_drug: bool,
    mapping: dict | None = None,
) -> float:
    """
    Deterministic call-quality score.

    NOT an ML confidence and NOT a probability. It expresses how sure PharmCAT
    was that it read the genotype, nothing about whether the recommendation is
    right. Numbers live in the YAML so they can be tuned without code changes.
    """
    cfg = mapping or load_mapping()
    section = cfg["confidence"]

    if not known_drug:
        return float(section["unknown_drug"])
    if not has_guidance:
        return float(section["no_guidance"])
    return float(section["by_call_status"].get(status.value, section["no_guidance"]))


# --------------------------------------------------------------------------- #
# Annotation selection
# --------------------------------------------------------------------------- #

_STRENGTH_ORDER = {"strong": 3, "moderate": 2, "optional": 1}


def _annotation_matches_calls(
    annotation: CpicAnnotation, report: PharmcatReport
) -> bool:
    """
    Does this CPIC row apply to the phenotypes we actually called?

    A lookup key is a gene -> phenotype map, and for multi-gene guidelines it
    names every gene at once, e.g.
        {"TPMT": "Poor Metabolizer", "NUDT15": "Normal Metabolizer"}
    Every gene in the key that we have a call for must agree; genes we could not
    call are ignored rather than treated as mismatches.
    """
    for entry in annotation.lookup_key:
        compared = 0
        for gene_symbol, phenotype in entry.items():
            call = report.gene(gene_symbol)
            if call is None or not call.lookup_keys:
                continue
            compared += 1
            called = {k.strip().lower() for k in call.lookup_keys}
            if phenotype.strip().lower() not in called:
                break
        else:
            if compared:
                return True
    return False


def select_annotation(
    guideline: CpicDrugGuideline, report: PharmcatReport
) -> tuple[CpicAnnotation | None, list[str]]:
    """
    Pick which CPIC row applies, and say so.

    PharmCAT often returns several rows for one drug — the same phenotype across
    different patient populations (clopidogrel has three: "CVI ACS PCI",
    "CVI non-ACS non-PCI", "NVI"). We cannot know the patient's indication, so:

      1. keep only rows whose full lookup key matches the called phenotypes;
      2. among those, take the strongest classification (most cautious);
      3. warn that other populations exist, naming them.

    Returns (annotation, warnings).
    """
    warnings: list[str] = []
    usable = [a for a in guideline.annotations if (a.drug_recommendation or "").strip()]
    if not usable:
        if guideline.annotations:
            # e.g. warfarin, whose CPIC guidance is a dosing algorithm rather
            # than per-phenotype text.
            warnings.append(
                f"PharmCAT returned CPIC annotations for {guideline.drug} but none "
                "carry a phenotype-specific recommendation (this drug's guideline "
                "may be algorithm-based rather than phenotype-based)."
            )
        return None, warnings

    matched = [a for a in usable if _annotation_matches_calls(a, report)]
    candidates = matched or usable
    if not matched:
        warnings.append(
            f"No CPIC row for {guideline.drug} matched the called phenotypes exactly; "
            "showing the strongest available row. Treat with extra caution."
        )

    chosen = max(
        candidates,
        key=lambda a: _STRENGTH_ORDER.get((a.classification or "").lower(), 0),
    )

    populations = {a.population for a in candidates if a.population}
    if len(candidates) > 1 and len(populations) > 1:
        warnings.append(
            f"CPIC gives {len(candidates)} population-specific recommendations for "
            f"{guideline.drug} ({', '.join(sorted(populations))}). PharmaGuard shows "
            f"the strongest one ({chosen.population or 'unspecified'}); review the "
            "population that matches the patient."
        )
    return chosen, warnings


def select_reporting_gene(
    annotation: CpicAnnotation | None,
    guideline: CpicDrugGuideline | None,
    report: PharmcatReport,
    fallback_gene: str | None,
    mapping: dict,
) -> PharmcatGeneCall | None:
    """
    Which gene call to show for this drug.

    Multi-gene guidelines (azathioprine keys off both TPMT and NUDT15) would
    otherwise attach the wrong phenotype: picking the first gene alphabetically
    reports NUDT15 Normal for a TPMT Poor Metaboliser, hiding the actual finding
    and under-stating severity.

    So we report the *most abnormal* called gene named by the matched
    annotation — that is the one driving the recommendation.
    """
    ranks: dict[str, int] = mapping.get("phenotype_abnormality_rank", {})

    candidates: list[str] = []
    if annotation:
        candidates = [g for entry in annotation.lookup_key for g in entry]
    if not candidates and guideline:
        candidates = list(guideline.genes)
    if not candidates and fallback_gene:
        candidates = [fallback_gene]

    calls = [call for g in candidates if (call := report.gene(g)) is not None]
    if not calls:
        return report.gene(fallback_gene) if fallback_gene else None

    def rank(call: PharmcatGeneCall) -> tuple[int, int]:
        phenotype = map_phenotype(call.phenotype_raw, mapping)
        # Tie-break toward the YAML's declared primary gene for the drug.
        preferred = 1 if fallback_gene and call.gene == fallback_gene else 0
        return (ranks.get(phenotype.value, 0), preferred)

    return max(calls, key=rank)


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #


def _alternatives_from(annotation: CpicAnnotation) -> list[str]:
    """
    Alternatives, only when CPIC actually offers them.

    We do NOT parse drug names out of the recommendation prose — that would be
    inventing a clinical list. When PharmCAT's `alternateDrugAvailable` flag is
    set we say so and point at the recommendation text, which names them.
    """
    if not annotation.alternate_drug_available:
        return []
    return [
        "CPIC indicates an alternative drug is available — see the recommendation "
        "text above for the specific agents."
    ]


def build_clinical_recommendation(
    annotation: CpicAnnotation | None,
    guideline: CpicDrugGuideline | None,
    *,
    fallback_reason: str,
) -> ClinicalRecommendation:
    """Assemble the contract's clinical block. All text is PharmCAT's."""
    if annotation is None:
        return ClinicalRecommendation(
            action=fallback_reason,
            dosing_guidance="No CPIC dosing guidance is available for this "
            "gene-drug-phenotype combination.",
            cpic_recommendation=(
                guideline.guideline_name
                if guideline and guideline.guideline_name
                else "No CPIC recommendation was returned by PharmCAT."
            ),
            cpic_evidence_level=CpicEvidenceLevel.UNKNOWN,
            alternatives=[],
            source="PharmCAT (no matching CPIC annotation)",
        )

    recommendation = html.unescape(annotation.drug_recommendation or "").strip()
    implications = " ".join(html.unescape(i).strip() for i in annotation.implications)

    # The recommendation strength lives here because our contract's
    # `cpic_evidence_level` enum cannot express it (see module docstring).
    strength = annotation.classification or "Unspecified"
    cpic_text = f"CPIC strength of recommendation: {strength}."
    if annotation.population and annotation.population.lower() not in ("n/a", ""):
        cpic_text += f" Population: {annotation.population}."
    if implications:
        cpic_text += f" Implications: {implications}"

    source = "PharmCAT CPIC Guideline Annotation"
    if guideline and guideline.guideline_name:
        source = f"{guideline.guideline_name} (via PharmCAT)"

    return ClinicalRecommendation(
        # `action` is CPIC's recommendation verbatim — the most important string
        # in the response, so it is passed through untouched.
        action=recommendation,
        dosing_guidance=recommendation,
        cpic_recommendation=cpic_text,
        cpic_evidence_level=CpicEvidenceLevel.UNKNOWN,
        alternatives=_alternatives_from(annotation),
        source=source,
    )


def evaluate(
    drug: str,
    report: PharmcatReport,
    mapping: dict | None = None,
) -> tuple[RiskAssessment, ClinicalRecommendation, PharmcatGeneCall | None, list[str]]:
    """
    Full mapping for one drug.

    Returns (risk_assessment, clinical_recommendation, gene_call, warnings).
    Never raises for unknown drugs or unsupported gene-drug pairs — those are
    normal, well-typed Unknown results.
    """
    cfg = mapping or load_mapping()
    warnings: list[str] = []
    key = drug.strip().lower()

    guideline = report.drug(key)

    # Which gene does this drug hang off? The YAML table is only a hint used for
    # fallback and tie-breaking; the matched CPIC annotation is authoritative,
    # so the final choice happens after annotation selection below.
    fallback_gene: str | None = cfg.get("drug_primary_gene", {}).get(key)
    if fallback_gene is None and guideline and guideline.genes:
        fallback_gene = next((g for g in guideline.genes if report.gene(g)), None)
    gene_call = report.gene(fallback_gene) if fallback_gene else None

    # --- drug PharmCAT has no CPIC guideline for at all ---------------------
    if guideline is None:
        return (
            RiskAssessment(
                risk_label=RiskLabel.UNKNOWN,
                confidence_score=derive_confidence(
                    CallStatus.NO_CALL,
                    has_guidance=False,
                    known_drug=False,
                    mapping=cfg,
                ),
                severity=Severity.NONE,
            ),
            build_clinical_recommendation(
                None,
                None,
                fallback_reason=(
                    f"'{drug}' is not covered by any CPIC guideline in PharmCAT "
                    f"{report.pharmcat_version}. This is not a safety finding — the "
                    "tool simply has no pharmacogenomic guidance for it."
                ),
            ),
            None,
            warnings,
        )

    # --- gene could not be called -------------------------------------------
    if gene_call is not None and not gene_call.is_called:
        warnings.extend(gene_call.warnings)
        reason = (
            f"{gene_call.gene} could not be called from this VCF, so no "
            f"pharmacogenomic recommendation can be made for {drug}."
        )
        return (
            RiskAssessment(
                risk_label=RiskLabel.UNKNOWN,
                confidence_score=derive_confidence(
                    gene_call.status,
                    has_guidance=False,
                    known_drug=True,
                    mapping=cfg,
                ),
                severity=Severity.NONE,
            ),
            build_clinical_recommendation(None, guideline, fallback_reason=reason),
            gene_call,
            warnings,
        )

    annotation, selection_warnings = select_annotation(guideline, report)
    warnings.extend(selection_warnings)
    # Re-resolve the gene now that we know which CPIC row matched: for
    # multi-gene guidelines this is what stops a TPMT Poor Metaboliser being
    # reported under NUDT15 Normal.
    gene_call = (
        select_reporting_gene(annotation, guideline, report, fallback_gene, cfg)
        or gene_call
    )
    if gene_call:
        warnings.extend(gene_call.warnings)

    # --- no annotation matched the phenotype --------------------------------
    if annotation is None:
        phenotype, phenotype_note = map_phenotype_noted(
            gene_call.phenotype_raw if gene_call else None, cfg
        )
        if phenotype_note:
            warnings.append(phenotype_note)
        return (
            RiskAssessment(
                risk_label=RiskLabel.UNKNOWN,
                confidence_score=derive_confidence(
                    gene_call.status if gene_call else CallStatus.NO_CALL,
                    has_guidance=False,
                    known_drug=True,
                    mapping=cfg,
                ),
                severity=Severity.NONE,
            ),
            build_clinical_recommendation(
                None,
                guideline,
                fallback_reason=(
                    f"PharmCAT returned no CPIC recommendation matching the called "
                    f"phenotype ({phenotype.value}) for {drug}."
                ),
            ),
            gene_call,
            warnings,
        )

    # --- the normal path ----------------------------------------------------
    phenotype, phenotype_note = map_phenotype_noted(
        gene_call.phenotype_raw if gene_call else None, cfg
    )
    if phenotype_note:
        warnings.append(phenotype_note)
    risk_label, rule_id, severity_hint = classify_annotation(annotation, cfg)
    severity = derive_severity(risk_label, phenotype, severity_hint, cfg)
    confidence = derive_confidence(
        gene_call.status if gene_call else CallStatus.NO_CALL,
        has_guidance=True,
        known_drug=True,
        mapping=cfg,
    )

    if risk_label is RiskLabel.UNKNOWN and rule_id == "fallback_unmatched":
        # A visible gap in the table rather than a silent wrong answer.
        warnings.append(
            f"No label-mapping rule matched CPIC's wording for {drug}; reported as "
            "Unknown. This is a gap in label_mapping.yaml, not a genotype finding."
        )

    recommendation = build_clinical_recommendation(
        annotation, guideline, fallback_reason=""
    )
    # Append the rule id so any label can be traced to the rule that made it.
    recommendation = recommendation.model_copy(
        update={
            "source": f"{recommendation.source} [label rule: {rule_id}]",
        }
    )

    return (
        RiskAssessment(
            risk_label=risk_label,
            confidence_score=confidence,
            severity=severity,
        ),
        recommendation,
        gene_call,
        warnings,
    )

class LabelContradiction(RuntimeError):
    """
    The text-derived label contradicts CPIC's own structured fields.

    Raised loudly rather than logged. A contradiction here means the mapping read
    CPIC's prose one way while CPIC's machine-readable flags say the opposite, and
    silently serving either answer would be worse than failing.
    """


#: Labels asserting that nothing about prescribing needs to change.
_NO_ACTION_LABELS = frozenset({RiskLabel.SAFE})


def check_label_contradiction(annotation: CpicAnnotation, label: RiskLabel) -> str | None:
    """
    Cross-check a text-derived label against CPIC's structured booleans.

    WHY THIS IS A CROSS-CHECK AND NOT AN INPUT

    The mapping deliberately keeps reading recommendation TEXT. The exhaustive
    validation in `scripts/validate_label_mapping.py` derives its expectations
    from these same structured booleans, so if the mapping consumed them the two
    sides would share an input and the validation would become tautological —
    it would agree by construction and stop catching anything.

    Used as an assertion instead, the booleans add a genuinely independent
    signal: they cannot make the mapping right, but they can prove it wrong.

    THIS WOULD HAVE CAUGHT THE PHASE 6 BUG ON ITS OWN

    The 16 azathioprine rows labelled `Safe` by a substring collision all carry
    `dosingInformation = true`. A label of "nothing needs to change" against a
    flag saying "the dose must change" is exactly this contradiction, so the guard
    would have failed on them without anyone writing an expectation table.

    Returns a description, or None when consistent.
    """
    if label not in _NO_ACTION_LABELS:
        return None

    if annotation.dosing_information:
        return (
            f"label {label.value!r} asserts unchanged prescribing, but CPIC sets "
            "dosingInformation=true for this recommendation (a dose change or "
            "monitoring requirement applies)"
        )
    if annotation.alternate_drug_available:
        return (
            f"label {label.value!r} asserts no action needed, but CPIC sets "
            "alternateDrugAvailable=true for this recommendation (another drug "
            "should be considered instead)"
        )
    return None


def classify_annotation_checked(
    annotation: CpicAnnotation, mapping: dict | None = None
) -> tuple[RiskLabel, str, str]:
    """
    `classify_annotation`, with the contradiction guard enforced.

    Raises `LabelContradiction`. Callers that must degrade rather than fail
    should catch it — but they must not ignore it, because the failure it
    reports is a mislabelled clinical recommendation.
    """
    label, rule_id, hint = classify_annotation(annotation, mapping)
    problem = check_label_contradiction(annotation, label)
    if problem is not None:
        raise LabelContradiction(f"{problem} (rule: {rule_id})")
    return label, rule_id, hint
