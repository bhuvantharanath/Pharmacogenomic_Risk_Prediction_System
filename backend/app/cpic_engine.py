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
        raise MappingConfigError(
            f"The label mapping file could not be read: {exc}") from exc

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


@dataclass(frozen=True)
class ResolvedPhenotype:
    """
    The phenotype we are willing to assert, and whether we assert it at all.

    THE INVARIANT THIS EXISTS TO ENFORCE

        A phenotype the caller declined to assert can never produce a
        confident risk label.

    Stated generally, over every gene and drug — not as a DPYD special case. Two
    measured defects motivated it, and they fail in opposite directions:

      OVER-CLAIMING (DPYD, 4/302 samples). PharmCAT called `Indeterminate`; the
      pipeline rendered `Safe` on fluorouracil, where deficiency is fatal. The
      label came from `lookup_keys`, which are derived from
      `recommendationDiplotypes` — and that structure exists to FIND A TABLE ROW,
      not to assert what the patient has. Using it to derive a risk label repeats
      the sourceDiplotypes category error one layer up.

      OVER-CLAIMING (SLCO1B1, 195/400 samples). Several equally-likely candidate
      diplotypes disagreed about function — one said `Normal Function`, another
      `Indeterminate` — and reading only candidate[0] rendered a confident `Safe`
      for 49% of the cohort.

    So assertion is decided from ALL candidates, not the first:

      * one candidate, phenotype maps        -> asserted
      * several candidates, all informative ones map to the SAME class
                                             -> asserted (function is known even
                                                though the exact diplotype is not)
      * several candidates that disagree     -> NOT asserted
      * nothing informative                  -> NOT asserted

    The middle case is why this keys on PHENOTYPE and never on diplotype
    ambiguity: 30 SLCO1B1 calls have every informative candidate reading
    `Decreased Function` or `Possible Decreased Function`. Both mean decreased
    transporter function, so the myopathy risk is known and must still produce a
    label. Suppressing those would trade one direction of dishonesty for the other.
    """

    phenotype: Phenotype
    asserted: bool
    #: Lookup keys safe to match a CPIC row with. Empty when nothing is asserted,
    #: so an unasserted phenotype cannot reach the lookup at all.
    lookup_keys: tuple[str, ...]
    reason: str = ""


def resolve_phenotype(
    call: PharmcatGeneCall | None, mapping: dict | None = None
) -> ResolvedPhenotype:
    """Decide what phenotype, if any, this gene call supports. See `ResolvedPhenotype`."""
    cfg = mapping or load_mapping()
    if call is None:
        return ResolvedPhenotype(
            Phenotype.UNKNOWN, False, (), "no gene call for this drug"
        )

    candidates = [p for p in (call.candidate_phenotypes or []) if p and p.strip()]
    if not candidates and call.phenotype_raw:
        # Older fixtures predate `candidate_phenotypes`; fall back so they still
        # resolve rather than silently becoming unasserted.
        candidates = [call.phenotype_raw]

    if not candidates:
        return ResolvedPhenotype(
            Phenotype.UNKNOWN, False, (),
            f"{call.gene}: PharmCAT assigned no phenotype to any candidate diplotype",
        )

    # `Indeterminate` is a CLAIM, not an absence of one.
    #
    # Subtle and load-bearing: `n/a` was already dropped by the parser because it
    # marks a candidate PharmCAT never assigned a phenotype to. `Indeterminate` is
    # different — it is PharmCAT positively stating that this genotype HAS no
    # phenotype assignment. So a candidate reading `Indeterminate` genuinely
    # DISAGREES with one reading `Normal Function`, and both must count.
    #
    # A first version of this function filtered every candidate mapping to UNKNOWN
    # out of the comparison, which collapsed {Normal Function, Indeterminate} to
    # {NM} and asserted `Safe` — leaving all 195 affected samples exactly as
    # broken as before. Classes are therefore compared WITHOUT dropping UNKNOWN.
    classes = {map_phenotype(p, cfg) for p in candidates}

    if len(classes) > 1:
        return ResolvedPhenotype(
            Phenotype.UNKNOWN, False, (),
            f"{call.gene}: candidate diplotypes disagree about function "
            f"({', '.join(sorted(candidates))}), so no phenotype can be asserted",
        )

    resolved = next(iter(classes))
    if resolved is Phenotype.UNKNOWN:
        return ResolvedPhenotype(
            Phenotype.UNKNOWN, False, (),
            f"{call.gene}: PharmCAT returned {candidates[0]!r}, which is not a "
            f"phenotype this build can act on",
        )
    keys = tuple(call.candidate_lookup_keys or call.lookup_keys or ())
    return ResolvedPhenotype(resolved, True, keys)


def check_phenotype_label(
    phenotype: Phenotype, label: RiskLabel
) -> str | None:
    """
    THE MISSING VERIFICATION EDGE. Returns a message on violation, else None.

    Three edges were already checked — explanation->CPIC (the provenance guard),
    label->CPIC (the mapping validation) and explanation->label (the consistency
    check). **phenotype->label was not**, and that is precisely where a green
    `Safe` badge sat above an `Unknown` phenotype on a drug that can kill.

    Deliberately one-directional. An `Unknown` phenotype must not carry a
    confident label; a *known* phenotype carrying `Unknown` is legitimate — CPIC
    may simply have no guidance for that pair, which is a gap in the table rather
    than a contradiction about what we know.
    """
    if phenotype is Phenotype.UNKNOWN and label is not RiskLabel.UNKNOWN:
        return (
            f"phenotype is Unknown but the label is {label.value!r}: a result the "
            f"genotyping step declined to assert cannot support a confident label"
        )
    return None


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
            if call is None:
                continue
            # An unasserted phenotype must never reach the lookup. Its
            # `lookup_keys` come from `recommendationDiplotypes`, which exists to
            # find a table row — not to state what the patient has. Matching on it
            # is what let an `Indeterminate` DPYD call select the Normal
            # Metabolizer row and render `Safe` on fluorouracil.
            resolved = resolve_phenotype(call)
            if not resolved.asserted or not resolved.lookup_keys:
                continue
            compared += 1
            called = {k.strip().lower() for k in resolved.lookup_keys}
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
                f"CPIC has guidance for {guideline.drug}, but none of it applies to "
                "this particular result (this drug's guidance may be based on a "
                "dose calculation rather than on gene function)."
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
            f"{guideline.drug} ({', '.join(sorted(populations))}). The strongest one "
            f"is shown ({chosen.population or 'unspecified'}); review the "
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
            source="PharmCAT (no matching CPIC entry)",
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

    source = "Entry in the CPIC Guideline, via PharmCAT"
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

    # --- THE INVARIANT: no asserted phenotype -> no confident label ----------
    # Checked BEFORE annotation selection so an unasserted phenotype never
    # reaches `lookup_keys`. See `ResolvedPhenotype` for the two measured defects
    # this prevents, one of which rendered `Safe` for 195 of 400 real samples.
    resolved = resolve_phenotype(gene_call, cfg)
    if gene_call is not None and not resolved.asserted:
        warnings.extend(gene_call.warnings)
        if resolved.reason:
            warnings.append(
                f"{resolved.reason}. Reported as Unknown rather than assuming one "
                f"of the possibilities."
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
            build_clinical_recommendation(
                None, guideline,
                fallback_reason=(
                    f"{resolved.reason}, so no pharmacogenomic recommendation can "
                    f"be made for {drug}."
                ),
            ),
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
    # Re-resolve: `select_reporting_gene` may have changed which gene we report.
    resolved = resolve_phenotype(gene_call, cfg)
    phenotype = resolved.phenotype
    if resolved.asserted:
        _, phenotype_note = map_phenotype_noted(
            gene_call.phenotype_raw if gene_call else None, cfg
        )
        if phenotype_note:
            warnings.append(phenotype_note)
        if gene_call is not None and len(gene_call.candidate_phenotypes or []) > 1:
            # Function known, exact diplotype not. Say so rather than letting the
            # single reported diplotype imply more precision than we have.
            warnings.append(
                f"{gene_call.gene}: PharmCAT could not narrow the diplotype "
                f"({len(gene_call.candidate_diplotypes)} equally likely: "
                f"{', '.join(gene_call.candidate_diplotypes[:4])}"
                f"{'…' if len(gene_call.candidate_diplotypes) > 4 else ''}), but "
                f"every candidate with a phenotype indicates "
                f"{phenotype.value}, so the functional result is reported with "
                f"confidence while the exact diplotype remains undetermined."
            )
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
            f"No rule in this build matched CPIC's wording for {drug}, so it is "
            "reported as Unknown. That is a gap in how this system reads the "
            "guideline, not a finding about the genotype."
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

    # Request-time verification edge. Degrade rather than serve a contradiction:
    # a confident badge above an Unknown phenotype is worse than a plain Unknown.
    violation = check_phenotype_label(phenotype, risk_label)
    if violation:
        warnings.append(
            f"{violation}. Degraded to Unknown. This is a bug in the label path, "
            f"not a genotype finding."
        )
        risk_label, severity = RiskLabel.UNKNOWN, Severity.NONE

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
            f"label {label.value!r} asserts unchanged prescribing, but CPIC records "
            "a dose change or monitoring requirement for this recommendation"
        )
    if annotation.alternate_drug_available:
        return (
            f"label {label.value!r} asserts no action needed, but CPIC records that "
            "another drug should be considered instead"
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
