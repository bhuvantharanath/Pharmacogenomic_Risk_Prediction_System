#!/usr/bin/env python3
"""
Benchmark candidate models on the real task, and pick one on evidence.

    python scripts/benchmark_models.py --auto --dry-run          # plan, no calls
    python scripts/benchmark_models.py --models a,b,c            # explicit shortlist
    python scripts/benchmark_models.py --auto --limit 4         # discover + cap

WHAT THIS DECIDES
    Which model generates the shipped explanations. That choice should not come
    from a vendor's leaderboard or anyone's recollection — it should come from
    running the actual PharmaGuard task and measuring what matters here:

      1. faithfulness-guard pass rate   — does it invent clinical entities?
      2. provenance pass rate           — does every clinical claim trace?
      3. JSON reliability               — does it return parseable structured output?

    Ranked in that order. Latency and token usage are tiebreakers only: a fast
    model that fabricates is worse than useless, because fabrication is the one
    failure this whole project exists to prevent.

METHOD
    Every candidate runs the SAME three representative cases — one Safe, one
    Adjust Dosage, one Toxic — so the comparison is like-for-like. Each
    (model, case) records JSON success and mode, the guard verdict with any
    violations, the provenance result, latency, token usage, and the raw output.
    All of it lands in reports/model_benchmark.md, raw outputs included, so the
    pick is auditable and the table can go straight into the project report.

COST
    Tiny by construction: |candidates| x 3 short generations. `--limit` caps the
    candidate count; `--dry-run` makes no call at all.

CANDIDATE SELECTION
    `--models a,b,c` is explicit and preferred. `--auto` discovers the provider
    catalogue live and filters to general instruction-following models by a
    name heuristic (excludes coder/reasoning/vision/embedding/guard/rerank ids
    and obvious sub-8B sizes). The heuristic is transparent and fallible — it
    reads ids, it cannot read parameter counts — so the selected list is printed
    for you to sanity-check, and `--models` overrides it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from _common import (
    DEFAULT_DELAY_SECONDS,
    DEFAULT_PROVIDER,
    PROVIDER_KEY_ENV,
    REPO_ROOT,
    REPORTS_DIR,
    RateLimiter,
    api_key,
    bold,
    dim,
    green,
    load_json,
    red,
    rel,
    rule,
    scrub,
    yellow,
)

REPORT_PATH = REPORTS_DIR / "model_benchmark.md"
SCRIPTS = REPO_ROOT / "scripts"

#: The three representative labels, in report order.
TARGET_LABELS = ("Safe", "Adjust Dosage", "Toxic")

#: Substrings that mark a NIM id as NOT a general instruction model. Heuristic,
#: name-only — documented as such because the API does not report capability.
_EXCLUDE = (
    "code", "coder", "reason", "think", "-r1", "qwq", "vision", "-vl", "vlm",
    "embed", "embedding", "rerank", "ranking", "guard", "safety", "nemoguard",
    "ocr", "speech", "audio", "tts", "asr", "image", "diffusion", "riva",
)
#: Obvious sub-8B markers.
_TOO_SMALL = ("1b", "2b", "3b", "4b", "mini", "small", "tiny", "0.5b", "1.5b")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class Candidate:
    model: str


@dataclass
class Trial:
    model: str
    case_key: str
    label: str
    json_ok: bool
    json_mode: str
    guard_passed: bool | None
    guard_violations: list[dict]
    provenance_ok: bool | None
    provenance_failures: list[str]
    latency_s: float
    usage: dict
    text: dict | None
    error: str = ""


@dataclass
class Summary:
    model: str
    trials: list[Trial] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.trials)

    @property
    def json_rate(self) -> float:
        return _rate(t.json_ok for t in self.trials)

    @property
    def guard_rate(self) -> float:
        scored = [t for t in self.trials if t.guard_passed is not None]
        return _rate((t.guard_passed for t in scored), len(scored))

    @property
    def provenance_rate(self) -> float:
        scored = [t for t in self.trials if t.provenance_ok is not None]
        return _rate((t.provenance_ok for t in scored), len(scored))

    @property
    def mean_latency(self) -> float:
        oks = [t.latency_s for t in self.trials if t.latency_s > 0]
        return sum(oks) / len(oks) if oks else 0.0

    @property
    def total_tokens(self) -> int:
        return sum((t.usage or {}).get("total_tokens") or 0 for t in self.trials)

    @property
    def rank_key(self) -> tuple:
        # Higher is better for the first three; lower latency breaks ties.
        return (self.guard_rate, self.provenance_rate, self.json_rate, -self.mean_latency)


def _rate(bools, total: int | None = None) -> float:
    items = list(bools)
    denom = total if total is not None else len(items)
    return (sum(1 for b in items if b) / denom) if denom else 0.0


# --------------------------------------------------------------------------- #
# Case selection
# --------------------------------------------------------------------------- #


def pick_cases(pg) -> list:
    """One reachable case per target label, deterministic."""
    from app.explanation.context import ExplanationContext  # noqa: F401

    by_label: dict[str, object] = {}
    for case in pg.load_reachable_cases():
        context, _ = pg.build_context(case)
        label = context.risk_label.value
        if label in TARGET_LABELS and label not in by_label:
            by_label[label] = (case, context)
    missing = [lbl for lbl in TARGET_LABELS if lbl not in by_label]
    if missing:
        raise SystemExit(f"no reachable case for label(s): {missing}")
    return [by_label[lbl] for lbl in TARGET_LABELS]


# --------------------------------------------------------------------------- #
# Candidate discovery
# --------------------------------------------------------------------------- #


def discover_candidates(provider: str, key: str, limit: int) -> list[str]:
    lm = _load("list_models")
    models = lm._nvidia_models(key) if provider == "nvidia" else lm._gemini_models(key, False)
    ids = [m["id"] for m in models]

    def is_general(mid: str) -> bool:
        low = mid.lower()
        if any(x in low for x in _EXCLUDE):
            return False
        if any(x in low for x in _TOO_SMALL):
            return False
        return "instruct" in low or "chat" in low or "nemotron" in low

    general = sorted({m for m in ids if is_general(m)})
    return general[:limit] if limit else general



# --------------------------------------------------------------------------- #
# Availability probing
# --------------------------------------------------------------------------- #


def probe_availability(provider: str, model: str) -> tuple[bool, str, float]:
    """
    One minimal call to find out whether a model is actually served.

    NVIDIA's catalogue lists far more models than the integrate endpoint will
    serve: in the first benchmark, 3 of 5 candidates returned 404 or 500 and
    each burned a full trial slot (and, for the 500, a 120s timeout) before that
    became visible. Probing with a 1-token request costs almost nothing and
    keeps the benchmark table about models that can actually be used.

    Returns (served, reason, latency_seconds).
    """
    from app.explanation.providers import get_provider
    from app.explanation.providers.errors import ProviderError

    impl = get_provider(provider)
    started = time.monotonic()
    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=impl.base_url, api_key=impl.api_key() or "unused",
            timeout=30.0, max_retries=0,
        )
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ok"}],
            max_tokens=1, temperature=0,
        )
        return True, "served", time.monotonic() - started
    except Exception as exc:  # noqa: BLE001
        status = getattr(exc, "status_code", None)
        return False, f"HTTP {status}" if status else type(exc).__name__, time.monotonic() - started


def rescore_captured(vp, pg) -> list[dict]:
    """
    Re-score the stored benchmark outputs under the current policy.

    No API calls: the point is to re-measure text already captured, so a change
    to the metric can be evaluated against the same evidence rather than against
    a fresh (and differently-sampled) generation.
    """
    diag = _load("diagnose_provenance")
    captured = diag.load_captured()
    cases = {c.key: c for c in pg.load_reachable_cases()}
    labels, phenos = vp.load_paraphrases()
    rows = []
    for item in captured:
        key = item["case"]
        ctx, _ = pg.build_context(cases[key])
        entry = {
            "drug": cases[key].drug, "gene": ctx.gene, "phenotype": cases[key].phenotype,
            "derived_risk_label": ctx.risk_label.value,
            "cpic_recommendation_used": ctx.cpic_recommendation,
            "cpic_implications": list(ctx.cpic_implications),
            "explanation": item["explanation"],
        }
        result = vp.verify_entry(entry, labels, phenos)
        rows.append({
            "case": key, "label": item["label"],
            "sentences": len(result.sentences),
            "flagged": len(result.failures),
            "passed": result.clinical_ok,
            "detail": [f"{s.field_name}: {s.text[:70]}" for s in result.failures],
        })
    return rows


# --------------------------------------------------------------------------- #
# Running one trial
# --------------------------------------------------------------------------- #


def run_trial(pg, vp, paraphrases, provider: str, model: str, case, context) -> Trial:
    from app.explanation import generator_llm
    from app.explanation.guard import check as guard_check

    case_obj, ctx = case, context
    started = time.monotonic()
    try:
        result = generator_llm.generate(ctx, provider=provider, model=model)
    except generator_llm.LlmUnavailableError as exc:
        return Trial(
            model=model, case_key=case_obj.key, label=ctx.risk_label.value,
            json_ok=False, json_mode="", guard_passed=None, guard_violations=[],
            provenance_ok=None, provenance_failures=[], latency_s=time.monotonic() - started,
            usage={}, text=None, error=scrub(exc)[:200],
        )
    latency = time.monotonic() - started

    report = guard_check(result.explanation, ctx, generator=f"benchmark:{model}")

    # Provenance: synthesize the entry the verifier expects and check it.
    entry = {
        "drug": case_obj.drug,
        "gene": ctx.gene or case_obj.gene,
        "phenotype": case_obj.phenotype,
        "derived_risk_label": ctx.risk_label.value,
        "cpic_recommendation_used": ctx.cpic_recommendation,
        "cpic_implications": list(ctx.cpic_implications),
        "explanation": result.explanation.fields(),
    }
    entry_result = vp.verify_entry(entry, *paraphrases)
    prov_failures = [f"{s.kind}:{s.text[:40]}" for s in entry_result.failures]

    return Trial(
        model=model, case_key=case_obj.key, label=ctx.risk_label.value,
        json_ok=True, json_mode=result.json_mode,
        guard_passed=report.passed,
        guard_violations=[{"kind": v.kind, "token": v.token, "field": v.field_name} for v in report.violations],
        provenance_ok=entry_result.clinical_ok,
        provenance_failures=prov_failures,
        latency_s=latency, usage=result.usage, text=result.explanation.fields(),
    )


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


def write_report(summaries: list[Summary], provider: str, path: Path) -> None:
    ranked = sorted(summaries, key=lambda s: s.rank_key, reverse=True)
    winner = ranked[0] if ranked else None

    lines = [
        "# Model selection benchmark",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}  ",
        f"**Provider:** `{provider}`  ",
        f"**Candidates:** {len(summaries)}  ",
        f"**Cases per model:** {len(TARGET_LABELS)} (one each: {', '.join(TARGET_LABELS)})",
        "",
        "Ranked by guard pass rate, then provenance pass rate, then JSON",
        "reliability. Latency and tokens are tiebreakers only — a fast model that",
        "fabricates a dose is worse than a slow one that does not, because",
        "fabrication is the failure this project exists to prevent.",
        "",
        "## Result",
        "",
    ]
    if winner:
        lines += [
            f"**Recommended: `{winner.model}`** — "
            f"guard {_pct(winner.guard_rate)}, provenance {_pct(winner.provenance_rate)}, "
            f"JSON {_pct(winner.json_rate)}, {winner.mean_latency:.1f}s/case.",
            "",
        ]

    lines += [
        "| Rank | Model | JSON ok | Guard pass | Provenance pass | Latency | Tokens |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for i, s in enumerate(ranked, start=1):
        star = " ⭐" if s is winner else ""
        lines.append(
            f"| {i} | `{s.model}`{star} | {_pct(s.json_rate)} | {_pct(s.guard_rate)} | "
            f"{_pct(s.provenance_rate)} | {s.mean_latency:.1f}s | {s.total_tokens or '—'} |"
        )
    lines.append("")

    # Per-model detail with violations and raw outputs.
    lines += ["## Detail", ""]
    for s in ranked:
        lines += [f"### `{s.model}`", ""]
        for t in s.trials:
            head = f"**{t.label}** ({t.case_key}) — "
            if t.error:
                lines.append(head + f"❌ error: {t.error}")
                continue
            marks = [
                f"JSON {'✅' if t.json_ok else '❌'} ({t.json_mode or 'n/a'})",
                f"guard {'✅' if t.guard_passed else '❌'}",
                f"provenance {'✅' if t.provenance_ok else '❌'}",
                f"{t.latency_s:.1f}s",
            ]
            lines.append(head + " · ".join(marks))
            if t.guard_violations:
                v = ", ".join(f"{x['kind']}:{x['token']}" for x in t.guard_violations)
                lines.append(f"  - guard caught: {v}")
            if t.provenance_failures:
                lines.append(f"  - provenance unverified: {', '.join(t.provenance_failures[:4])}")
            if t.text:
                lines.append("")
                lines.append("  ```")
                for fname, val in t.text.items():
                    lines.append(f"  {fname}: {val}")
                lines.append("  ```")
            lines.append("")

    lines += [
        "## How to read this",
        "",
        "- **Guard pass** — the faithfulness guard found no fabricated dose,",
        "  number, rsID, allele, gene or drug. This is the primary criterion.",
        "- **Provenance pass** — every clinical-claim sentence traces to the CPIC",
        "  source or a declared paraphrase. Stricter than the guard.",
        "- **JSON ok** — the output parsed into the four-field schema, after",
        "  stripping any reasoning block and unwrapping any code fence.",
        "",
        "Raw outputs above are captured verbatim. They are candidate generations,",
        "not shipped content — the chosen model is re-run through the full",
        "pregeneration pipeline (guard, retry, provenance) before anything ships.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pct(rate: float) -> str:
    return f"{rate * 100:.0f}%"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER if DEFAULT_PROVIDER != "template" else "nvidia")
    parser.add_argument("--models", default="", help="Comma-separated model ids (preferred).")
    parser.add_argument("--auto", action="store_true", help="Discover candidates from the catalogue.")
    parser.add_argument("--limit", type=int, default=4, help="Max candidates in --auto mode (default 4).")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--dry-run", action="store_true", help="Plan only; make NO API call.")
    parser.add_argument("-o", "--output", type=Path, default=REPORT_PATH)
    parser.add_argument("--json", action="store_true", help="Also print machine-readable summary.")
    parser.add_argument("--rescore", action="store_true",
                        help="Re-score already-captured outputs under the current policy. No API calls.")
    parser.add_argument("--no-probe", action="store_true",
                        help="Skip the 1-token availability probe (not recommended).")
    args = parser.parse_args(argv)

    provider = args.provider.strip().lower()
    os.environ["LLM_PROVIDER"] = provider

    pg = _load("pregenerate_explanations")
    vp = _load("verify_provenance")

    if args.rescore:
        rows = rescore_captured(vp, pg)
        print(bold("\nRe-scored captured outputs under the CURRENT field-level policy"))
        print(dim("  (no API calls — same text, corrected metric)\n"))
        total = sum(r["sentences"] for r in rows)
        flagged = sum(r["flagged"] for r in rows)
        for r in rows:
            mark = green("PASS") if r["passed"] else yellow(f"{r['flagged']} flagged")
            print(f"  {r['case']:22} {r['label']:15} {r['sentences']:>2} sentences   {mark}")
            for d in r["detail"]:
                print(dim(f"       flagged: {d}"))
        print(rule())
        print(f"\n  {total - flagged}/{total} sentences pass   ({flagged} flagged for adjudication)")
        return 0

    try:
        cases = pick_cases(pg)
    except SystemExit as exc:
        print(red(str(exc)), file=sys.stderr)
        return 2

    key_env = PROVIDER_KEY_ENV.get(provider, "")
    key = api_key(provider)

    # Resolve candidates.
    if args.models:
        candidates = [m.strip() for m in args.models.split(",") if m.strip()]
    elif args.auto:
        if key_env and not key:
            print(red(f"{key_env} is not set — cannot discover candidates."), file=sys.stderr)
            return 2
        candidates = discover_candidates(provider, key, args.limit)
    else:
        print(red("Give --models a,b,c (preferred) or --auto to discover."), file=sys.stderr)
        print(dim("Discover ids first:  python scripts/list_models.py --provider nvidia"), file=sys.stderr)
        return 2

    if not candidates:
        print(red("No candidate models resolved."), file=sys.stderr)
        return 2

    if not args.no_probe and key_env:
        print(bold("\nAvailability probe") + dim("  (1 token each — skips models the endpoint will not serve)"))
        served, unavailable = [], []
        for model in candidates:
            ok, reason, latency = probe_availability(provider, model)
            if ok:
                served.append(model)
                print(f"  {green('served')}      {model:<44} {latency:.1f}s")
            else:
                unavailable.append((model, reason))
                print(f"  {red('unavailable')} {model:<44} {reason}")
        if unavailable:
            print(dim(f"\n  skipping {len(unavailable)} unavailable model(s) — they would waste a trial each"))
        candidates = served
        if not candidates:
            print(red("\nNo candidate model is actually served."), file=sys.stderr)
            return 2

    print(bold("\nPharmaGuard model benchmark"))
    print(dim(f"  provider={provider}  candidates={len(candidates)}  cases={len(cases)} ({', '.join(TARGET_LABELS)})"))
    print(dim(f"  models: {', '.join(candidates)}"))
    total_calls = len(candidates) * len(cases)
    print(dim(f"  total generations: {total_calls}  (~{total_calls * args.delay / 60:.1f} min at {args.delay}s)\n"))

    if args.dry_run:
        for case, ctx in cases:
            print(f"  case {case.key:<22} label={ctx.risk_label.value}")
        print(yellow(f"\nDRY RUN — {total_calls} generations would be made. No API call issued."))
        return 0

    if key_env and not key:
        print(red(f"{key_env} is not set — cannot benchmark."), file=sys.stderr)
        return 2

    paraphrases = vp.load_paraphrases()
    limiter = RateLimiter(args.delay)
    summaries: list[Summary] = []

    for model in candidates:
        print(bold(f"  {model}"))
        summary = Summary(model=model)
        for case, ctx in cases:
            limiter.wait()
            print(f"    {ctx.risk_label.value:<14} {case.key:<20} ", end="", flush=True)
            trial = run_trial(pg, vp, paraphrases, provider, model, case, ctx)
            summary.trials.append(trial)
            if trial.error:
                print(red(f"error: {trial.error[:44]}"))
            else:
                print(
                    ("json " + ("✓" if trial.json_ok else "✗"))
                    + ("  guard " + (green("✓") if trial.guard_passed else red("✗")))
                    + ("  prov " + (green("✓") if trial.provenance_ok else red("✗")))
                    + dim(f"  {trial.latency_s:.1f}s")
                )
        summaries.append(summary)

    write_report(summaries, provider, args.output)
    ranked = sorted(summaries, key=lambda s: s.rank_key, reverse=True)

    print(rule())
    print(bold("\n  Ranking (guard > provenance > JSON, latency tiebreak):"))
    for i, s in enumerate(ranked, start=1):
        print(
            f"    {i}. {s.model:<34} guard {_pct(s.guard_rate):>4}  "
            f"prov {_pct(s.provenance_rate):>4}  json {_pct(s.json_rate):>4}  {s.mean_latency:.1f}s"
        )
    if ranked:
        print(green(f"\n  Recommended: {bold(ranked[0].model)}"))
    print(dim(f"  wrote {rel(args.output)}"))

    if args.json:
        print(json.dumps({
            "provider": provider,
            "ranking": [
                {"model": s.model, "guard": s.guard_rate, "provenance": s.provenance_rate,
                 "json": s.json_rate, "latency_s": round(s.mean_latency, 2), "tokens": s.total_tokens}
                for s in ranked
            ],
            "recommended": ranked[0].model if ranked else None,
        }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
