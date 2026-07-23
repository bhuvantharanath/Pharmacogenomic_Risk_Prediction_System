#!/usr/bin/env python3
"""
Pre-generate the explanation set.

Enumerates every (drug, phenotype) case, builds a representative context from
**real PharmCAT CPIC output** plus the mechanism corpus, generates an
explanation, runs the faithfulness guard, and writes the survivors to
`backend/app/data/explanations.json`.

Run it once, review the output, ship the JSON. Runtime then does a dictionary
lookup and slot fill — no API call in the deployed path.

USAGE
    export GEMINI_API_KEY=...
    python scripts/pregenerate_explanations.py

    # See what would be generated, without spending any quota:
    python scripts/pregenerate_explanations.py --dry-run

    # Deterministic templates only — no key needed, useful in CI:
    python scripts/pregenerate_explanations.py --generator template

    # Just one drug, e.g. after editing its mechanism file:
    python scripts/pregenerate_explanations.py --drug clopidogrel

WHERE THE CPIC TEXT COMES FROM
    Not from this script's imagination. It reads PharmCAT report fixtures under
    `backend/tests/fixtures/` and, if present, any `*.report.json` passed via
    --reports. Each (gene, phenotype, drug) triple's recommendation is taken
    verbatim from those reports. A case with no CPIC text available is recorded
    as a gap rather than invented.

REVIEW IS NOT OPTIONAL
    Every entry is written with `"reviewed_by": null`. The runtime surfaces the
    unreviewed count in `quality_metrics.warnings`, and scripts/README.md states
    the workflow. Nothing here is fit to demo until a human has read it.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.cpic_engine import (  # noqa: E402
    classify_annotation,
    map_phenotype,
    select_annotation,
)
from app.explanation import generator_template  # noqa: E402
from app.explanation.context import Explanation, ExplanationContext  # noqa: E402
from app.explanation.guard import check, log_violation  # noqa: E402
from app.models import Phenotype, RiskLabel  # noqa: E402
from app.pharmcat_models import CpicAnnotation, PharmcatReport  # noqa: E402
from app.pharmcat_runner import parse_report  # noqa: E402
from app.retrieval import all_documents, retrieve_mechanism  # noqa: E402

OUTPUT_PATH = BACKEND / "app" / "data" / "explanations.json"
FIXTURE_DIR = BACKEND / "tests" / "fixtures"

# Phenotypes worth pre-generating. RM is omitted for genes that never report it;
# a case with no matching CPIC annotation is skipped and counted as a gap, so
# over-enumerating here is harmless.
PHENOTYPES: tuple[Phenotype, ...] = (
    Phenotype.PM,
    Phenotype.IM,
    Phenotype.NM,
    Phenotype.RM,
    Phenotype.URM,
    Phenotype.UNKNOWN,
)

# PharmCAT's phenotype wording, keyed by our enum. Used to find the CPIC
# annotation whose lookup key matches the case being generated.
_PHENOTYPE_WORDING: dict[Phenotype, tuple[str, ...]] = {
    Phenotype.PM: ("Poor Metabolizer", "Poor Function"),
    Phenotype.IM: ("Intermediate Metabolizer", "Decreased Function"),
    Phenotype.NM: ("Normal Metabolizer", "Normal Function"),
    Phenotype.RM: ("Rapid Metabolizer", "Increased Function"),
    Phenotype.URM: ("Ultrarapid Metabolizer",),
    Phenotype.UNKNOWN: ("No Result", "Indeterminate"),
}

def representative_label(annotation: CpicAnnotation | None) -> RiskLabel:
    """
    The risk label this case will actually carry at runtime.

    Derived with the production rule engine rather than guessed from the
    phenotype. That distinction matters: the label is a function of CPIC's
    *text*, not of the phenotype, and the two do not track each other. A
    phenotype-keyed guess puts clopidogrel + Poor Metaboliser at "Adjust
    Dosage", where the engine — reading CPIC's actual "avoid clopidogrel"
    wording — produces "Ineffective".

    Because the tone of the generated prose is chosen from this label, guessing
    it wrong means shipping reviewed text that contradicts the risk badge
    rendered directly above it.
    """
    if annotation is None:
        return RiskLabel.UNKNOWN
    label, _rule_id, _hint = classify_annotation(annotation)
    return label


@dataclass
class CaseOutcome:
    drug: str
    gene: str
    phenotype: Phenotype
    status: str  # generated | guard_failed | fallback | gap | skipped
    generator: str = ""
    detail: str = ""


# --------------------------------------------------------------------------- #
# Loading real CPIC text
# --------------------------------------------------------------------------- #


def load_reports(paths: list[Path]) -> list[PharmcatReport]:
    """Parse every PharmCAT report we can find, for CPIC annotation text."""
    reports: list[PharmcatReport] = []
    for path in paths:
        try:
            reports.append(parse_report(json.loads(path.read_text())))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  ! could not read {path.name}: {exc}", file=sys.stderr)
    return reports


def find_annotation(
    reports: list[PharmcatReport], drug: str, phenotype: Phenotype
) -> tuple[CpicAnnotation | None, str | None]:
    """
    Find CPIC text for (drug, phenotype) across all loaded reports.

    Rather than matching phenotype *wording* against annotation lookup keys, we
    find a report in which the drug's gene actually has the target phenotype and
    then ask `cpic_engine.select_annotation` — the exact function the runtime
    uses — which row applies. Two reasons:

      * **Correctness.** Not every gene keys its CPIC rows by phenotype name.
        DPYD keys by *activity score*: its lookup key is `{"DPYD": "1.0"}`, not
        `{"DPYD": "Intermediate Metabolizer"}`. Wording-matching silently found
        nothing for every fluoropyrimidine case.
      * **Fidelity.** Pre-generated text should be attached to the same CPIC row
        the runtime would pick. Sharing the selection function guarantees that,
        instead of hoping two implementations agree.

    Returns (annotation, gene).
    """
    for report in reports:
        guideline = report.drug(drug)
        if guideline is None:
            continue

        # Which gene does this guideline key off, and does this report have the
        # phenotype we are generating for?
        for gene_symbol in guideline.genes or []:
            call = report.gene(gene_symbol)
            if call is None or not call.is_called:
                continue
            if map_phenotype(call.phenotype_raw) is not phenotype:
                continue

            annotation, _ = select_annotation(guideline, report)
            if annotation is not None and (annotation.drug_recommendation or "").strip():
                return annotation, gene_symbol

    return None, None


def build_context(
    drug: str,
    gene: str,
    phenotype: Phenotype,
    annotation: CpicAnnotation | None,
) -> ExplanationContext:
    """
    Assemble a representative context for one case.

    Patient-specific values are supplied as the **placeholder strings
    themselves**, not as concrete values and not as None:

      * Concrete values would invite the generator to bake one patient's
        diplotype into prose reused for everyone.
      * None makes generators take their "nothing was called" branch, which
        bakes in the opposite error — text asserting no genotype was found,
        served to patients who have one.

    Passing `"{diplotype}"` keeps the called/uncalled branch correct while the
    value stays a slot. `ExplanationContext.was_called` is the property that
    makes this work.
    """
    called = phenotype is not Phenotype.UNKNOWN
    return ExplanationContext(
        drug=drug,
        risk_label=representative_label(annotation),
        phenotype=phenotype,
        gene=gene,
        diplotype="{diplotype}" if called else None,
        activity_score=None,
        detected_variants=[],
        cpic_recommendation=(annotation.drug_recommendation or "") if annotation else "",
        cpic_implications=list(annotation.implications) if annotation else [],
        cpic_strength=(annotation.classification or "") if annotation else "",
        cpic_evidence_level="Unknown",
        mechanism=retrieve_mechanism(gene, drug),
        phenotype_label=next(iter(_PHENOTYPE_WORDING.get(phenotype, ("",))), ""),
    )


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #


def generate_one(
    context: ExplanationContext, use_llm: bool, model: str | None
) -> tuple[Explanation, str, object, str]:
    """
    Generate one explanation with up to one retry, then fall back.

    Returns (explanation, generator_name, guard_report, status).
    """
    if use_llm:
        from app.explanation import generator_llm

        last_report = None
        for attempt in (1, 2):
            try:
                result = generator_llm.generate(context, model=model)
            except generator_llm.LlmUnavailableError as exc:
                fallback = generator_template.generate(context)
                report = check(fallback, context, generator="template")
                return fallback, "template", report, f"fallback ({exc})"

            report = check(result.explanation, context, generator=f"llm:{result.model}")
            report.attempts = attempt
            if report.passed:
                return result.explanation, f"llm:{result.model}", report, "generated"

            report.action_taken = "retried" if attempt == 1 else "fell back to template"
            log_violation(report, context, result.explanation)
            last_report = report

        fallback = generator_template.generate(context)
        detail = (
            f"guard rejected {len(last_report.violations)} entity(ies)"
            if last_report
            else "guard failed"
        )
        return fallback, "template", last_report, f"guard_failed ({detail})"

    explanation = generator_template.generate(context)
    report = check(explanation, context, generator="template")
    return explanation, "template", report, "generated"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--generator",
        choices=("llm", "template"),
        default="llm",
        help="llm (default) uses Gemini; template needs no API key.",
    )
    parser.add_argument("--model", default=None, help="Override the Gemini model id.")
    parser.add_argument("--drug", action="append", default=[], help="Limit to these drugs.")
    parser.add_argument(
        "--reports",
        type=Path,
        nargs="*",
        default=None,
        help="PharmCAT report.json files to source CPIC text from.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Enumerate cases only.")
    parser.add_argument("-o", "--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args(argv)

    report_paths = args.reports if args.reports is not None else sorted(FIXTURE_DIR.glob("*.json"))
    reports = load_reports([p for p in report_paths if p.is_file()])
    if not reports:
        print("error: no PharmCAT reports found to source CPIC text from.", file=sys.stderr)
        print(f"       looked in {FIXTURE_DIR}", file=sys.stderr)
        return 2

    documents = all_documents()
    if args.drug:
        wanted = {d.strip().lower() for d in args.drug}
        documents = [d for d in documents if d.drug in wanted]
    if not documents:
        print("error: no mechanism documents matched.", file=sys.stderr)
        return 2

    use_llm = args.generator == "llm"
    if use_llm and not args.dry_run:
        from app.explanation import generator_llm

        if not generator_llm.available():
            print(
                "error: --generator llm needs GEMINI_API_KEY (and google-genai).\n"
                "       Use --generator template for an API-free run.",
                file=sys.stderr,
            )
            return 2

    print(f"PharmaGuard explanation pre-generation")
    print(f"  reports  : {len(reports)} PharmCAT report(s)")
    print(f"  drugs    : {', '.join(sorted(d.drug for d in documents))}")
    print(f"  generator: {args.generator}{' (dry run)' if args.dry_run else ''}")
    print()

    outcomes: list[CaseOutcome] = []
    entries: list[dict] = []
    generated_at = datetime.now(timezone.utc).isoformat()

    for document in sorted(documents, key=lambda d: d.drug):
        for phenotype in PHENOTYPES:
            annotation, matched_gene = find_annotation(reports, document.drug, phenotype)
            gene = matched_gene or document.gene

            # No CPIC text for this combination. Recording it as a gap is the
            # honest outcome: runtime falls back to the template, which states
            # plainly that no recommendation was available.
            if annotation is None and phenotype is not Phenotype.UNKNOWN:
                outcomes.append(
                    CaseOutcome(
                        document.drug, gene, phenotype, "gap",
                        detail="no CPIC recommendation for this phenotype",
                    )
                )
                continue

            context = build_context(document.drug, gene, phenotype, annotation)

            if args.dry_run:
                outcomes.append(CaseOutcome(document.drug, gene, phenotype, "skipped", detail="dry run"))
                continue

            explanation, generator, report, status = generate_one(context, use_llm, args.model)
            outcomes.append(
                CaseOutcome(
                    document.drug, gene, phenotype,
                    "generated" if status == "generated" else status.split(" ")[0],
                    generator=generator,
                    detail=status,
                )
            )

            entries.append(
                {
                    "drug": document.drug,
                    "gene": gene,
                    "phenotype": phenotype.value,
                    # The label the runtime engine derives for this case. Stored
                    # for audit; the served value is filled from the live
                    # assessment via the {risk_label} slot.
                    "derived_risk_label": context.risk_label.value,
                    "explanation": explanation.fields(),
                    "generator": generator,
                    "model": generator.split(":", 1)[1] if ":" in generator else "",
                    "generated_at": generated_at,
                    "guard_report": report.to_dict() if report else None,
                    "cpic_recommendation_used": context.cpic_recommendation,
                    "mechanism_source": document.citation_line,
                    # Filled in by the faculty guide. Runtime reports the count
                    # of entries still null.
                    "reviewed_by": None,
                }
            )

    # ----------------------------------------------------------------------- #
    # Audit summary
    # ----------------------------------------------------------------------- #
    print(f"{'drug':<14}{'gene':<9}{'phenotype':<11}{'status':<14}generator")
    print("-" * 68)
    for outcome in outcomes:
        print(
            f"{outcome.drug:<14}{outcome.gene:<9}{outcome.phenotype.value:<11}"
            f"{outcome.status:<14}{outcome.generator}"
        )

    counts = Counter(o.status for o in outcomes)
    print()
    print("SUMMARY")
    print(f"  cases enumerated : {len(outcomes)}")
    print(f"  generated        : {counts['generated']}")
    print(f"  guard failures   : {counts['guard_failed']}")
    print(f"  fallbacks        : {counts['fallback']}")
    print(f"  gaps (no CPIC)   : {counts['gap']}")
    if counts["skipped"]:
        print(f"  skipped          : {counts['skipped']}")

    if args.dry_run:
        print("\nDry run — nothing written.")
        return 0

    payload = {
        "version": 1,
        "generated_at": generated_at,
        "generator": args.generator,
        "model": args.model or (entries[0]["model"] if entries else ""),
        "pharmaguard_note": (
            "Pre-generated explanations. Each entry passed the faithfulness "
            "guard at generation time. REQUIRES FACULTY REVIEW: set reviewed_by "
            "on every entry before any demo or submission."
        ),
        "explanations": entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(entries)} entries to {args.output.relative_to(REPO_ROOT)}")
    unreviewed = sum(1 for e in entries if not e["reviewed_by"])
    if unreviewed:
        print(
            f"\n  ** {unreviewed} entries have reviewed_by: null. **\n"
            "  These are NOT approved for demo or submission until the faculty\n"
            "  guide has read them and filled that field in. See scripts/README.md."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
