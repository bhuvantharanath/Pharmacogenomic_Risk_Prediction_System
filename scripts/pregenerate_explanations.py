#!/usr/bin/env python3
"""
Generate the explanation set with a real LLM, guard every output, and write
results incrementally so a rate-limit stop never loses work.

    python scripts/pregenerate_explanations.py --dry-run      # no API calls
    python scripts/pregenerate_explanations.py --resume       # the real run
    python scripts/pregenerate_explanations.py --only clopidogrel --limit 2

WHAT THIS REPLACES
    Every prior entry in explanations.json was deterministic template text, so
    the field named `llm_generated_explanation` was a misnomer and the
    faithfulness guard had never had the opportunity to catch anything — it had
    only ever validated strings our own code composed. This makes both honest.

DESIGN NOTES

  Reachability. Only cases marked reachable in `case_matrix.json` are
  generated. Authoring prose for a case the pipeline cannot produce would pad
  the coverage numbers with fiction.

  Slots stay intact. The model is instructed to write `{diplotype}` and
  `{detected_variants}` rather than concrete values, because one reviewed
  sentence is reused for every patient sharing a phenotype. Phase 4's runtime
  slot verifier then cross-checks the filled values against the response's own
  profile.

  Guard, then retry, then fall back. Every generation is checked. A failure is
  retried once with a stricter instruction naming the offending entities; a
  second failure falls back to the deterministic template with
  `"fallback": true` and the reason recorded. We never ship unguarded prose.

  Incremental writes. The output file is rewritten after every single case.
  Free-tier quota can stop a run at any point, and losing forty minutes of
  generated text to a 429 would be its own kind of failure.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from _common import (
    CASE_MATRIX_PATH,
    DEFAULT_PROVIDER,
    PROVIDER_KEY_ENV,
    DEFAULT_DELAY_SECONDS,
    DEFAULT_MODEL,
    EXPLANATIONS_PATH,
    GUARD_EVENTS_PATH,
    REPO_ROOT,
    RateLimiter,
    api_key,
    append_jsonl,
    bold,
    dim,
    green,
    load_json,
    prompt_hash,
    red,
    rel,
    rule,
    scrub,
    write_json_atomic,
    yellow,
)

from app.cpic_engine import derive_label, map_phenotype, select_annotation
from app.explanation import generator_template
from app.explanation.context import Explanation, ExplanationContext
from app.explanation.guard import check as guard_check
from app.models import Phenotype, RiskLabel
from app.pharmcat_models import CpicAnnotation
from app.pharmcat_runner import parse_report
from app.retrieval import retrieve_mechanism

FIXTURE_DIR = REPO_ROOT / "backend" / "tests" / "fixtures"

#: Appended to the system instruction on the retry after a guard failure.
STRICTER_SUFFIX = """

RETRY — YOUR PREVIOUS ANSWER WAS REJECTED.
A deterministic checker found entities in your output that do not appear in the
supplied context: {violations}

Those are fabrications. Rewrite the explanation using ONLY facts present in the
supplied JSON. In particular:
  - Do NOT state any number, dose, or unit that is not in the context verbatim.
  - Do NOT name any drug, gene, rsID or star allele that is not in the context.
  - If you cannot say something without inventing a detail, omit it entirely.
An explanation that says less is correct. An explanation that invents is not.
"""


@dataclass
class Case:
    drug: str
    gene: str
    phenotype: str

    @property
    def key(self) -> str:
        return f"{self.drug}:{self.phenotype}"


def load_reachable_cases() -> list[Case]:
    matrix = load_json(CASE_MATRIX_PATH)
    if not matrix:
        print(
            red(f"No case matrix at {CASE_MATRIX_PATH}."), file=sys.stderr
        )
        print("Run: python scripts/enumerate_cases.py", file=sys.stderr)
        raise SystemExit(2)
    return [
        Case(c["drug"], c["gene"], c["phenotype"])
        for c in matrix.get("cases", [])
        if c.get("reachable")
    ]


def find_annotation(drug: str, phenotype: Phenotype) -> tuple[CpicAnnotation | None, str | None]:
    """
    Locate the CPIC row the runtime would select for this case.

    Uses the production selector against the checked-in fixtures, so the text a
    generated explanation is grounded on is the same text a user would see.
    """
    for fixture in sorted(FIXTURE_DIR.glob("pharmcat_report_*.json")):
        report = parse_report(load_json(fixture))
        guideline = report.drug(drug)
        if guideline is None:
            continue
        for gene_symbol in guideline.genes or []:
            call = report.gene(gene_symbol)
            if call is None or not call.is_called:
                continue
            if map_phenotype(call.phenotype_raw) is not phenotype:
                continue
            annotation, _ = select_annotation(guideline, report)
            if annotation and (annotation.drug_recommendation or "").strip():
                return annotation, gene_symbol
    return None, None


def build_context(case: Case) -> tuple[ExplanationContext, CpicAnnotation | None]:
    """
    Assemble the closed set of facts the model may use.

    Patient-specific values are supplied as the placeholder strings themselves
    — not concrete values (which would get baked into reused prose) and not
    None (which makes generators take their "nothing was called" branch).
    """
    phenotype = Phenotype(case.phenotype)
    annotation, matched_gene = find_annotation(case.drug, phenotype)
    gene = matched_gene or case.gene

    # The SAME derivation the runtime uses — see `cpic_engine.derive_label`.
    # This used to call `classify_annotation` directly with no phenotype gate,
    # which is why the two paths disagreed on an unasserted phenotype.
    label, _rule, _hint = derive_label(phenotype, annotation)

    called = phenotype is not Phenotype.UNKNOWN
    context = ExplanationContext(
        drug=case.drug,
        risk_label=label,
        phenotype=phenotype,
        gene=gene,
        diplotype="{diplotype}" if called else None,
        activity_score=None,
        detected_variants=[],
        cpic_recommendation=(annotation.drug_recommendation or "") if annotation else "",
        cpic_implications=list(annotation.implications) if annotation else [],
        cpic_strength=(annotation.classification or "") if annotation else "",
        cpic_evidence_level="Unknown",
        mechanism=retrieve_mechanism(gene, case.drug),
        phenotype_label="" if not called else _pharmcat_wording(case.drug, phenotype),
    )
    return context, annotation


def _pharmcat_wording(drug: str, phenotype: Phenotype) -> str:
    """PharmCAT's own phrasing for this phenotype, for readable prose."""
    for fixture in sorted(FIXTURE_DIR.glob("pharmcat_report_*.json")):
        report = parse_report(load_json(fixture))
        guideline = report.drug(drug)
        if guideline is None:
            continue
        for gene_symbol in guideline.genes or []:
            call = report.gene(gene_symbol)
            if call and call.is_called and map_phenotype(call.phenotype_raw) is phenotype:
                return call.phenotype_raw or ""
    return ""


def log_guard_event(case: Case, report, attempt: int, action: str, model: str) -> None:
    """Every evaluation, pass or fail — this is the safety evidence."""
    append_jsonl(
        GUARD_EVENTS_PATH,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "pregenerate",
            "case": case.key,
            "drug": case.drug,
            "gene": case.gene,
            "phenotype": case.phenotype,
            "model": model,
            "attempt": attempt,
            "passed": report.passed,
            "violations": [
                {"kind": v.kind, "token": v.token, "field": v.field_name}
                for v in report.violations
            ],
            "action_taken": action,
        },
    )


def generate_one(
    case: Case,
    context: ExplanationContext,
    model: str,
    limiter: RateLimiter,
    verbose: bool,
) -> dict:
    """
    Generate, guard, retry once, then fall back. Returns the entry payload.

    Never raises for an API problem — a failed case degrades to the template
    and is recorded as such, so one bad case cannot abort a long run.
    """
    from app.explanation import generator_llm
    from app.explanation.providers import QuotaExhausted

    system_instruction = generator_llm.SYSTEM_INSTRUCTION
    user_prompt = generator_llm._build_prompt(context)
    phash = prompt_hash(system_instruction, user_prompt, model)

    last_violations: list[str] = []
    for attempt in (1, 2):
        limiter.wait()

        instruction = system_instruction
        if attempt == 2 and last_violations:
            instruction = system_instruction + STRICTER_SUFFIX.format(
                violations=", ".join(last_violations)
            )

        try:
            result = _call_with_backoff(
                context, model, instruction, limiter, verbose
            )
        except QuotaExhausted:
            # A hard wall fails every remaining case identically. Let it out so
            # the run stops cleanly rather than emitting 20 template fallbacks
            # that bury the real cause.
            raise
        except generator_llm.LlmUnavailableError as exc:
            if verbose:
                print(red(f"      API error: {scrub(exc)}"))
            return _fallback_entry(
                case, context, model, phash, f"API error: {scrub(exc)}", None
            )

        report = guard_check(result.explanation, context, generator=f"llm:{model}")
        report.attempts = attempt

        if report.passed:
            log_guard_event(case, report, attempt, "accepted", model)
            return {
                "drug": case.drug,
                "gene": context.gene or case.gene,
                "phenotype": case.phenotype,
                "derived_risk_label": context.risk_label.value,
                "explanation": result.explanation.fields(),
                # Template-as-provider is honestly labelled "template", not "llm:".
                "generator": "template" if result.provider == "template" else f"llm:{result.model}",
                "provider": result.provider,
                "model": result.model,
                "json_mode": result.json_mode,
                "usage": result.usage,
                "prompt_hash": phash,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "guard_report": report.to_dict(),
                "fallback": False,
                "fallback_reason": None,
                "attempts": attempt,
                "cpic_recommendation_used": context.cpic_recommendation,
                "mechanism_source": context.mechanism.citation_line if context.mechanism else "",
                "review": _fresh_review(),
            }

        last_violations = [f"{v.kind}:{v.token}" for v in report.violations]
        action = "retried with stricter instruction" if attempt == 1 else "fell back to template"
        report.action_taken = action
        log_guard_event(case, report, attempt, action, model)
        if verbose:
            print(yellow(f"      guard rejected (attempt {attempt}): {', '.join(last_violations[:4])}"))

    return _fallback_entry(
        case,
        context,
        model,
        phash,
        f"guard rejected both attempts: {', '.join(last_violations[:6])}",
        last_violations,
    )


def _call_with_backoff(context, model: str, instruction: str, limiter: RateLimiter, verbose: bool):
    """
    Call the selected provider, backing off exponentially on a transient limit.

    A hard quota/credit wall (`QuotaExhausted`) is re-raised immediately: backing
    off and retrying cannot recover credits, so waiting would only slow the
    inevitable fall back to the template. Only a `RateLimited`/429 is retried.
    """
    from app.explanation import generator_llm
    from app.explanation.providers import QuotaExhausted

    last_error: Exception | None = None
    for attempt in range(1, 5):
        try:
            return generator_llm.generate(
                context, model=model, system_instruction=instruction
            )
        except QuotaExhausted:
            raise  # a wall, not a speed bump — do not back off
        except generator_llm.LlmUnavailableError as exc:
            last_error = exc
            if not RateLimiter.is_rate_limit_error(exc) or attempt == 4:
                raise
            wait = RateLimiter.backoff_seconds(attempt)
            print(yellow(f"      rate limited; backing off {wait:.0f}s (attempt {attempt}/4)"))
            import time

            time.sleep(wait)
    raise last_error  # type: ignore[misc]


def _fresh_review() -> dict:
    """
    The review block for a newly generated entry.

    `provenance_verified` starts False on purpose: generation and verification
    are separate steps, and an entry that asserted its own verification would
    make the release gate self-certifying. `verify_provenance.py --write` is
    what sets it, after actually checking.
    """
    return {
        "provenance_verified": False,
        "verified_by": "",
        "verified_at": "",
        "read_by_author": None,
        "clinical_expert_review": None,
        "clinical_expert_review_status": "NOT_OBTAINED",
    }


def _fallback_entry(
    case: Case,
    context: ExplanationContext,
    model: str,
    phash: str,
    reason: str,
    violations: list[str] | None,
) -> dict:
    """Deterministic template, clearly marked as a fallback."""
    explanation = generator_template.generate(context)
    report = guard_check(explanation, context, generator="template")
    return {
        "drug": case.drug,
        "gene": context.gene or case.gene,
        "phenotype": case.phenotype,
        "derived_risk_label": context.risk_label.value,
        "explanation": explanation.fields(),
        "generator": "template",
        "provider": "template",
        "model": model,
        "json_mode": "none",
        "prompt_hash": phash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "guard_report": report.to_dict(),
        "fallback": True,
        "fallback_reason": reason,
        "rejected_violations": violations or [],
        "attempts": 2,
        "cpic_recommendation_used": context.cpic_recommendation,
        "mechanism_source": context.mechanism.citation_line if context.mechanism else "",
        "review": _fresh_review(),
    }


def print_dry_run(case: Case, context: ExplanationContext, model: str) -> None:
    """Print exactly what would be sent — and nothing is sent."""
    from app.explanation import generator_llm

    system_instruction = generator_llm.SYSTEM_INSTRUCTION
    user_prompt = generator_llm._build_prompt(context)
    phash = prompt_hash(system_instruction, user_prompt, model)

    print(rule(f"{case.drug} / {case.phenotype}"))
    print(f"  {bold('gene')}            {context.gene}")
    print(f"  {bold('risk_label')}      {context.risk_label.value}  {dim('(derived by the rule engine)')}")
    print(f"  {bold('model')}           {model}")
    print(f"  {bold('prompt_hash')}     {phash}")
    print(f"  {bold('mechanism')}       {context.mechanism.path.name if context.mechanism and context.mechanism.path else '(none)'}")
    print(f"\n  {bold('CPIC recommendation (grounding, verbatim)')}")
    text = context.cpic_recommendation or "(none — this is an Unknown case)"
    for line in _wrap(text, 72):
        print(f"    {line}")
    if context.cpic_implications:
        print(f"\n  {bold('CPIC implications')}")
        for implication in context.cpic_implications:
            for line in _wrap(implication, 72):
                print(f"    {line}")
    print(f"\n  {bold('user prompt')} {dim(f'({len(user_prompt)} chars)')}")
    for line in user_prompt.splitlines()[:14]:
        print(dim(f"    {line[:76]}"))
    if len(user_prompt.splitlines()) > 14:
        print(dim(f"    … {len(user_prompt.splitlines()) - 14} more lines"))
    print()


def _wrap(text: str, width: int) -> list[str]:
    import textwrap

    return textwrap.wrap(text, width) or [""]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Print payloads; make NO API call.")
    parser.add_argument("--only", action="append", default=[], metavar="DRUG", help="Limit to these drugs.")
    parser.add_argument("--only-phenotype", action="append", default=[], metavar="PH", help="Limit to these phenotypes.")
    parser.add_argument("--resume", action="store_true", help="Skip cases already present in the output.")
    parser.add_argument("--force", action="store_true", help="Regenerate even if already present.")
    parser.add_argument("--limit", type=int, default=0, metavar="N", help="Stop after N cases.")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER,
                        help=f"LLM provider: nvidia|gemini|ollama|template (default {DEFAULT_PROVIDER}).")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model id within the provider.")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS, help="Seconds between requests.")
    parser.add_argument("-o", "--output", type=Path, default=EXPLANATIONS_PATH)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    if args.resume and args.force:
        parser.error("--resume and --force are mutually exclusive")

    # The generator reads provider/model from the environment; setting them from
    # the CLI here keeps a single source of truth and lets every downstream call
    # (generate, backoff) agree without threading the values through.
    os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        os.environ["LLM_MODEL"] = args.model

    cases = load_reachable_cases()
    if args.only:
        wanted = {d.strip().lower() for d in args.only}
        cases = [c for c in cases if c.drug in wanted]
    if args.only_phenotype:
        wanted_ph = {p.strip() for p in args.only_phenotype}
        cases = [c for c in cases if c.phenotype in wanted_ph]
    if not cases:
        print(red("No cases match those filters."), file=sys.stderr)
        return 2

    existing = load_json(args.output, {"explanations": []})
    by_key = {f"{e['drug']}:{e['phenotype']}": e for e in existing.get("explanations", [])}

    todo = list(cases)
    if args.resume:
        todo = [c for c in cases if c.key not in by_key]
    if args.limit:
        todo = todo[: args.limit]

    print(bold("\nPharmaGuard explanation pre-generation"))
    print(
        dim(
            f"  provider={args.provider}  model={args.model or '(provider default)'}  "
            f"delay={args.delay}s ({60 / max(args.delay, 0.01):.0f} RPM)  "
            f"reachable={len(cases)}  to-do={len(todo)}  already={len(by_key)}"
        )
    )
    if args.dry_run:
        print(yellow("  DRY RUN — no API call will be made\n"))
    print()

    if not todo:
        print(green("Nothing to do — every reachable case is already generated."))
        print(dim("Use --force to regenerate."))
        return 0

    if args.dry_run:
        for case in todo:
            context, _ = build_context(case)
            print_dry_run(case, context, args.model)
        print(rule())
        target = f"{args.provider}:{args.model}" if args.model else args.provider
        print(f"\n{bold(str(len(todo)))} case(s) would be sent to {bold(target)}.")
        print(dim(f"Estimated wall time at {args.delay}s/request: ~{len(todo) * args.delay / 60:.1f} min"))
        print(dim("No API call was made. Re-run without --dry-run to generate."))
        return 0

    key_env = PROVIDER_KEY_ENV.get(args.provider, "")
    if key_env and not api_key(args.provider):
        print(red(f"{key_env} is not set — cannot generate with provider {args.provider!r}."), file=sys.stderr)
        print(dim("  Put it in repo-root .env, or switch --provider (ollama/template need no key)."), file=sys.stderr)
        return 2

    from app.explanation.providers import QuotaExhausted

    limiter = RateLimiter(args.delay)
    generated = fallbacks = 0

    for index, case in enumerate(todo, start=1):
        print(f"  [{index:>2}/{len(todo)}] {case.drug:<14} {case.phenotype:<8} ", end="", flush=True)
        context, _ = build_context(case)
        try:
            entry = generate_one(case, context, args.model, limiter, args.verbose)
        except QuotaExhausted as exc:
            # A depleted key fails every remaining case identically. Stop rather
            # than churn out 20 template fallbacks that hide the real cause, and
            # leave already-generated work saved.
            print(red("QUOTA EXHAUSTED"))
            print(red(f"\n  {scrub(exc)}"))
            print(yellow(f"  Stopped after {index - 1} case(s). Work so far is saved."))
            print(dim("  Switch --provider (e.g. nvidia/ollama) or top up, then --resume."))
            return 3

        by_key[case.key] = entry
        if entry["fallback"]:
            fallbacks += 1
            print(yellow("fallback") + dim(f"  {entry['fallback_reason'][:44]}"))
        else:
            generated += 1
            print(green("ok") + dim(f"  guard passed (attempt {entry['attempts']})"))

        # Write after EVERY case: a 429 three-quarters through a run must not
        # cost the work already done.
        write_json_atomic(
            args.output,
            {
                "version": 2,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "generator": "llm",
                "provider": args.provider,
                "model": args.model,
                "pharmaguard_note": (
                    "LLM-generated, guard-checked explanations. Slots are filled at "
                    "request time and cross-checked by the runtime slot verifier. "
                    "NOT YET PROVENANCE-VERIFIED: run scripts/verify_provenance.py "
                    "--write before shipping. No clinical expert has reviewed this "
                    "content and none is expected to; see reports/provenance_report.md."
                ),
                "explanations": sorted(
                    by_key.values(), key=lambda e: (e["drug"], e["phenotype"])
                ),
            },
        )

    print(rule())
    print(f"\n  generated {green(str(generated))}   fallback {yellow(str(fallbacks))}   total {len(by_key)}")
    print(dim(f"  wrote {rel(args.output)}"))
    print(dim(f"  guard events appended to {rel(GUARD_EVENTS_PATH)}"))
    print(dim("\nNext:  python scripts/generation_report.py"))
    print(dim("Then:  python scripts/verify_provenance.py --write"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
