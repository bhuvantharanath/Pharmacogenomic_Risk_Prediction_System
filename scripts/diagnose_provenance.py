#!/usr/bin/env python3
"""
Diagnose what the provenance verifier actually measures.

    python scripts/diagnose_provenance.py            # writes the report
    python scripts/diagnose_provenance.py --print    # also dump to stdout

WHY THIS EXISTS

`verify_provenance.py` scored real LLM output at 0% and the template at 100%,
and that result was reported as "LLM prose cannot meet the integrity bar". That
conclusion was wrong, and this script is the audit that establishes why.

The question it answers is narrow and decisive: **does the checker measure
faithfulness, or does it measure copying?** If a sentence that faithfully
restates a sourced claim in different words fails, then the metric rewards
verbatim reuse — and the template's 100% is true by construction rather than by
merit, because the template is assembled from source words.

Three minimal probes settle it (see PARAPHRASE PROBES below), and the 15 real
failures from the captured NVIDIA benchmark outputs are then classified by hand
into true and false positives. No LLM is used as a judge anywhere: that would be
circular, and it would burn quota to answer a question that a handful of
deterministic probes answers better.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import REPO_ROOT, REPORTS_DIR, bold, dim, green, red, rel, rule

REPORT_PATH = REPORTS_DIR / "provenance_diagnosis.md"
SCRIPTS = REPO_ROOT / "scripts"
BENCHMARK_MD = REPORTS_DIR / "model_benchmark.md"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Probes: what does the matcher actually reward?
# --------------------------------------------------------------------------- #

#: (description, source, candidate, what a FAITHFULNESS metric should say)
PROBES = [
    (
        "Faithful paraphrase — different words, same claim",
        "Consider dose reduction.",
        "Your doctor may lower your dose.",
        "PASS",
    ),
    (
        "Verbatim copy of the source claim",
        "Consider dose reduction.",
        "Consider dose reduction.",
        "PASS",
    ),
    (
        "CONTRADICTION that reuses the source's vocabulary",
        "Consider dose reduction.",
        "Do not consider dose reduction.",
        "FAIL",
    ),
    (
        "Unsourced addition using only common words",
        "Consider dose reduction.",
        "Consider dose reduction every day.",
        "FAIL",
    ),
]


def run_probes(vp) -> list[dict]:
    out = []
    for description, source, candidate, expected in PROBES:
        verified, untraced = vp.traces_to(candidate, source)
        actual = "PASS" if verified else "FAIL"
        out.append({
            "description": description,
            "source": source,
            "candidate": candidate,
            "expected_if_faithfulness": expected,
            "actual": actual,
            "agrees": actual == expected,
            "untraced": sorted(untraced),
        })
    return out


# --------------------------------------------------------------------------- #
# The 15 real failures, classified by hand
# --------------------------------------------------------------------------- #

#: Manual adjudication of every failing sentence from the three captured
#: NVIDIA outputs. Keyed by a distinctive prefix of the sentence.
#:
#: TRUE POSITIVE  — genuinely asserts something the source does not support.
#: FALSE POSITIVE — faithful paraphrase, correct restatement of the input, or
#:                  pure procedural framing carrying no clinical claim.
#:
#: Each carries the reason, so the count can be argued with rather than trusted.
HAND_CLASSIFICATION: dict[str, tuple[str, str, str]] = {
    # (verdict, cause-category, reasoning)
    "Reduced or absent function in these enzymes removes a brake": (
        "FALSE POSITIVE", "connective word",
        "Only 'leading' is untraced. The causal claim (reduced function -> "
        "marrow suppression) is in the mechanism corpus; the sentence fails on a "
        "conjunction.",
    ),
    "The patient has an intermediate metabolizer phenotype, which means they have moderate": (
        "FALSE POSITIVE", "phenotype descriptor",
        "Untraced words are 'intermediate/metabolizer/phenotype' — the case's own "
        "input phenotype. The biochemical detail (TGN, MeMPN concentrations) DID "
        "trace. It fails for naming the phenotype it was given.",
    ),
    "If you're taking {drug} and your doctor is considering a standard dose": (
        "FALSE POSITIVE", "plain-language rendering",
        "A faithful restatement of 'Initiate therapy with reduced starting doses "
        "if standard starting dose is >=2 mg/kg/day'. The dose threshold traced; "
        "'doctor/lower/need' are the plain words a patient needs.",
    ),
    "Your doctor will adjust the dose based on how your body is responding": (
        "FALSE POSITIVE", "plain-language rendering",
        "'adjust', 'dose', 'disease-specific', 'guidelines' all traced — the "
        "claim is sourced. Fails on 'body/doctor/medicine/responding'.",
    ),
    "It may take a few weeks to reach the right dose": (
        "BORDERLINE", "wording drift",
        "'weeks' traced: CPIC states a steady-state interval after dose "
        "adjustment, so the timeline is sourced, not invented. But 'reach the "
        "right dose' is not the same claim as 'reach steady state' — a mild "
        "drift worth a human look, not an invention.",
    ),
    "The patient has an intermediate metabolizer phenotype for the DPYD gene": (
        "FALSE POSITIVE", "phenotype descriptor",
        "Untraced: 'associated/intermediate/metabolizer/phenotype'. Restates the "
        "supplied phenotype and its known enzyme effect.",
    ),
    "This may increase the risk of severe or fatal toxicity when treated with fluorouracil": (
        "FALSE POSITIVE", "drug's own name",
        "The ONLY untraced word is 'fluorouracil' — the name of the drug the "
        "explanation is about. 'severe or fatal toxicity' traced verbatim.",
    ),
    "Reduced DPD activity slows inactivation": (
        "FALSE POSITIVE", "mechanism paraphrase",
        "Standard DPD mechanism, reworded. The corpus states the same causal "
        "chain in different words.",
    ),
    "The patient's intermediate metabolizer phenotype is associated with decreased DPD": (
        "FALSE POSITIVE", "phenotype descriptor",
        "Same descriptors plus the drug name; the toxicity claim traced.",
    ),
    "This means you may be at higher risk for serious side effects": (
        "FALSE POSITIVE", "plain-language rendering",
        "'serious side effects' is the lay rendering of 'severe toxicity', which "
        "is in the source. Fails only because laypeople and guidelines use "
        "different vocabulary.",
    ),
    "Your doctor or pharmacist can help you understand what this means": (
        "FALSE POSITIVE", "procedural framing",
        "Makes NO clinical claim at all. Advisory framing, misclassified as "
        "CLINICAL because it contains the word 'treatment'.",
    ),
    "The patient has a Poor Metabolizer phenotype for azathioprine": (
        "FALSE POSITIVE", "phenotype descriptor",
        "Untraced: phenotype descriptors and the drug name. The substantive claim "
        "(leukopenia, neutropenia, myelosuppression) traced verbatim.",
    ),
    "Reduced or absent TPMT function removes this brake": (
        "FALSE POSITIVE", "connective word",
        "Fails on 'allowing' and 'leading'. Two conjunctions.",
    ),
    "The patient's {phenotype} phenotype for azathioprine is due to {diplotype}": (
        "FALSE POSITIVE", "connective word",
        "Fails on 'due' and 'phenotype'. The sentence is almost entirely slots.",
    ),
    "This means you're at higher risk for serious side effects like low white blood cell": (
        "FALSE POSITIVE", "plain-language rendering",
        "'low white blood cell count' is the lay rendering of 'leukopenia', which "
        "IS in the source. Translating a term of art is the point of the field.",
    ),
    "Your doctor or pharmacist can help you choose a different medicine": (
        "FALSE POSITIVE", "procedural framing + paraphrase",
        "Restates 'Consider alternative nonthiopurine immunosuppressant therapy' "
        "in plain words, plus advisory framing.",
    ),
}


def classify(sentence: str) -> tuple[str, str, str]:
    for prefix, verdict in HAND_CLASSIFICATION.items():
        if sentence.startswith(prefix[:60]) or prefix[:60] in sentence:
            return verdict
    return ("UNCLASSIFIED", "", "not in the hand-adjudicated set")


# --------------------------------------------------------------------------- #
# Captured outputs
# --------------------------------------------------------------------------- #


def load_captured() -> list[dict]:
    """Extract the three llama-3.1-8b outputs from the benchmark report."""
    if not BENCHMARK_MD.is_file():
        raise SystemExit(f"no benchmark report at {rel(BENCHMARK_MD)} — run benchmark_models.py")
    md = BENCHMARK_MD.read_text()
    if "### `meta/llama-3.1-8b-instruct`" not in md:
        raise SystemExit("benchmark report has no llama-3.1-8b section")
    section = md.split("### `meta/llama-3.1-8b-instruct`")[1].split("### `")[0]
    blocks = re.findall(r"\*\*(.+?)\*\* \((.+?)\).*?\n\n  ```\n(.*?)\n  ```", section, re.S)
    out = []
    for label, case, body in blocks:
        fields = {}
        for line in body.split("\n"):
            m = re.match(r"\s*(summary|mechanism|variant_rationale|patient_friendly):\s*(.*)", line)
            if m:
                fields[m.group(1)] = m.group(2).strip()
        if len(fields) == 4:
            out.append({"label": label, "case": case, "explanation": fields})
    return out


def analyse(vp, pg, captured: list[dict]) -> list[dict]:
    cases = {c.key: c for c in pg.load_reachable_cases()}
    labels, phenos = vp.load_paraphrases()
    results = []
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
        report = vp.verify_entry(entry, labels, phenos)
        results.append({
            "case": key, "label": item["label"],
            "cpic": ctx.cpic_recommendation,
            "sentences": [
                {
                    "field": s.field_name, "kind": s.kind, "verified": s.verified,
                    "text": s.text, "untraced": sorted(s.untraced),
                    "hand": classify(s.text) if not s.verified else None,
                }
                for s in report.sentences
            ],
        })
    return results


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #

MATCHER_SOURCE = '''def traces_to(sentence: str, *sources: str) -> tuple[bool, set[str]]:
    """Does every content word of `sentence` appear in some source?"""
    haystack = " ".join(s or "" for s in sources).lower()
    present = set(re.findall(r"[a-z][a-z0-9\\-]*|\\d+(?:\\.\\d+)?", haystack))
    for word in list(present):
        present |= _normalise(word)
    untraced = {
        word for word in content_words(sentence) if not (_normalise(word) & present)
    }
    return (not untraced), untraced'''


def write_report(probes: list[dict], results: list[dict], path: Path) -> dict:
    failures = [
        (r["case"], s) for r in results for s in r["sentences"] if not s["verified"]
    ]
    counts: dict[str, int] = {}
    causes: dict[str, int] = {}
    for _case, s in failures:
        verdict = (s["hand"] or ("UNCLASSIFIED", "", ""))[0]
        counts[verdict] = counts.get(verdict, 0) + 1
        cause = (s["hand"] or ("", "", ""))[1]
        if cause:
            causes[cause] = causes.get(cause, 0) + 1

    total_sentences = sum(len(r["sentences"]) for r in results)
    lines = [
        "# Provenance verifier — diagnosis",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}  ",
        "**Inputs:** the three captured `meta/llama-3.1-8b-instruct` outputs from "
        "the NVIDIA benchmark (Safe / Adjust Dosage / Toxic)  ",
        f"**Sentences analysed:** {total_sentences} · **failing:** {len(failures)}",
        "",
        "## Verdict up front",
        "",
        "**The matcher is lexical term-overlap. It measures copying, not**",
        "**faithfulness.** The 0% score on LLM output and the 100% score on the",
        "template are both artifacts of that: the template is assembled from",
        "source words, so it passes by construction, and any paraphrase fails",
        "however faithful it is.",
        "",
        "## 1. What kind of matcher is it?",
        "",
        "**(a) lexical / term-overlap.** Not entity-level, not claim-level. The",
        "whole decision is a set-difference over content words:",
        "",
        "```python",
        MATCHER_SOURCE,
        "```",
        "",
        "There is no notion of a claim, a predicate, negation, or entailment",
        "anywhere in it. A word is either present in the source string or it is",
        "not.",
        "",
        "## 2. The decisive probes",
        "",
        "| Probe | Source | Candidate | A faithfulness metric should say | It actually says |",
        "| --- | --- | --- | :---: | :---: |",
    ]
    for p in probes:
        agree = "✅" if p["agrees"] else "❌"
        lines.append(
            f"| {p['description']} | `{p['source']}` | `{p['candidate']}` | "
            f"{p['expected_if_faithfulness']} | **{p['actual']}** {agree} |"
        )
    lines += [
        "",
        "**Read the third row.** A sentence that says the *opposite* of the source",
        "passes, because it reuses the source's vocabulary. And the fourth adds an",
        "unsourced frequency (\"every day\") using only words already present, and",
        "also passes. So the checker has false positives *and* false negatives:",
        "it rejects faithful rewording and accepts contradictions.",
        "",
        "That is the answer to the critical question: **a faithful restatement in",
        "different words FAILS.** The metric measures copying.",
        "",
        "## 3. The 15 real failures, classified by hand",
        "",
        "| Verdict | Count |",
        "| --- | ---: |",
    ]
    for verdict in ("TRUE POSITIVE", "BORDERLINE", "FALSE POSITIVE", "UNCLASSIFIED"):
        if counts.get(verdict):
            lines.append(f"| {verdict} | {counts[verdict]} |")
    lines += [
        "",
        "### Why they failed",
        "",
        "| Cause | Count |",
        "| --- | ---: |",
    ]
    for cause, n in sorted(causes.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {cause} | {n} |")

    lines += [
        "",
        "**Not one failure is a fabricated clinical claim.** The categories are:",
        "",
        "- **connective words** — `leading`, `allowing`, `due`. A correct causal",
        "  sentence fails on its conjunction.",
        "- **phenotype descriptors** — `intermediate`, `metabolizer`, `phenotype`.",
        "  The sentence fails for naming the phenotype it was handed as input,",
        "  because those words are not in the CPIC *recommendation* string.",
        "- **the drug's own name** — one sentence's only untraced word is",
        "  `fluorouracil`.",
        "- **plain-language rendering** — `doctor`, `body`, `lower`, `side effects`,",
        "  `low white blood cell count`. Translating `leukopenia` into words a",
        "  patient understands is the entire purpose of `patient_friendly`, and the",
        "  metric penalises exactly that.",
        "- **procedural framing** — \"your doctor or pharmacist can help you\"",
        "  asserts nothing clinical and should never have been scored.",
        "",
        "### Every failing sentence",
        "",
    ]
    for result in results:
        lines += [f"#### `{result['case']}` ({result['label']})", "",
                  f"> **CPIC source:** {result['cpic'][:400]}", ""]
        for s in result["sentences"]:
            if s["verified"]:
                continue
            verdict, cause, why = s["hand"]
            badge = {"TRUE POSITIVE": "🔴", "BORDERLINE": "🟡"}.get(verdict, "🟢")
            lines += [
                f"{badge} **{verdict}** ({cause}) — *{s['field']}*, classified `{s['kind']}`",
                "",
                f"> {s['text']}",
                "",
                f"- untraced tokens: {', '.join('`'+w+'`' for w in s['untraced'])}",
                f"- adjudication: {why}",
                "",
            ]

    lines += [
        "## 4. What follows",
        "",
        "The earlier conclusion — *\"real LLMs fail the integrity bar\"* — does not",
        "hold. It was a measurement artifact. What the data actually shows is that",
        "`llama-3.1-8b` produced clinically faithful text whose wording differs",
        "from the source, which is what a plain-language explainer is supposed to",
        "do.",
        "",
        "It does **not** follow that the output is safe to ship unexamined. The",
        "contradiction probe shows lexical overlap cannot certify anything, in",
        "either direction. So the replacement is two-part:",
        "",
        "1. **Field-level policy** — verbatim where verbatim matters (the CPIC",
        "   recommendation), claim-level checks where wording may legitimately",
        "   vary, and paraphrase explicitly permitted in `patient_friendly` under",
        "   a no-new-claims rule.",
        "2. **Human adjudication** — the automated layer flags candidates; a person",
        "   decides. With 20 entries that is tractable, and it is the payoff of",
        "   pre-generating rather than generating per request.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"counts": counts, "causes": causes, "failures": len(failures),
            "total": total_sentences, "probes": probes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output", type=Path, default=REPORT_PATH)
    parser.add_argument("--print", dest="do_print", action="store_true")
    args = parser.parse_args(argv)

    vp = _load("vp", SCRIPTS / "verify_provenance.py")
    pg = _load("pg", SCRIPTS / "pregenerate_explanations.py")

    probes = run_probes(vp)
    captured = load_captured()
    results = analyse(vp, pg, captured)
    summary = write_report(probes, results, args.output)

    print(rule("provenance diagnosis"))
    print(f"  matcher type      : {bold('lexical / term-overlap')} (not entity, not claim-level)")
    for p in probes:
        mark = green("as expected") if p["agrees"] else red("DISAGREES with faithfulness")
        print(f"  probe: {p['description'][:46]:<48} {p['actual']:<5} {mark}")
    print(f"\n  sentences analysed: {summary['total']}   failing: {summary['failures']}")
    for verdict, n in summary["counts"].items():
        colour = red if verdict == "TRUE POSITIVE" else (green if verdict == "FALSE POSITIVE" else dim)
        print(f"    {colour(verdict.ljust(16))} {n}")
    print(dim(f"\n  wrote {rel(args.output)}"))
    if args.do_print:
        print("\n" + args.output.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
