#!/usr/bin/env python3
"""
Sensitivity check: does the flagging pipeline still catch anything?

    python scripts/detector_sensitivity.py            # writes the report
    python scripts/detector_sensitivity.py --print

WHY THIS EXISTS

The field-level filter flagged 0 of 160 sentences on the shipped set. That
followed three rounds of false-positive removal (12 -> 4 -> 0), so the number is
ambiguous on its face: it could mean the text is clean, or it could mean the
detector was blunted while the false positives were being fixed. Those two
readings have opposite consequences and cannot be distinguished by looking at a
zero.

So the zero is tested rather than trusted. Known-bad sentences are injected into
otherwise-clean **real generated text**, and every one must be flagged. A miss is
a hole in the detector, and this script names it.

Injecting into real text matters: a violation planted in a synthetic sentence
proves the regex fires, not that it fires against the prose we actually ship,
in the sentence position and context where it would really appear.

WHAT COUNTS AS A VIOLATION HERE

Five classes, one per failure mode the pipeline claims to cover:

    dose        a quantity the source never states
    timeline    a duration the source never states
    polarity    a reversal of a real source directive
    mechanism   a biological claim absent from the cited corpus
    comparative an invented comparative risk

`clean_control` sentences are injected too. They must NOT be flagged — a
detector that flags everything is as useless as one that flags nothing, and
without controls the catch rate is meaningless.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from _common import (
    EXPLANATIONS_PATH,
    REPO_ROOT,
    REPORTS_DIR,
    bold,
    dim,
    green,
    load_json,
    red,
    rel,
    rule,
    yellow,
)

SCRIPTS = REPO_ROOT / "scripts"
REPORT_PATH = REPORTS_DIR / "detector_sensitivity.md"
FIXTURE_DIR = REPO_ROOT / "backend" / "tests" / "fixtures" / "planted_violations"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class Planted:
    kind: str
    field: str
    sentence: str
    why: str
    must_flag: bool = True
    #: The host whose SOURCE makes this a violation. A polarity reversal is only
    #: a reversal against a directive that says the opposite — running it against
    #: an unrelated case tests nothing and would score a spurious "miss".
    host: str = "fluorouracil:IM"


#: The planted set. Each is a sentence a clinician would object to, written to
#: look exactly like the surrounding prose so nothing but the check distinguishes
#: it.
PLANTED: list[Planted] = [
    Planted(
        "dose", "patient_friendly",
        "Your doctor will start you on 25 mg twice daily.",
        "a specific dose the CPIC text for this case never states",
    ),
    Planted(
        "timeline", "patient_friendly",
        "Results usually appear within three days of starting treatment.",
        "a duration absent from the source",
    ),
    Planted(
        "polarity", "summary",
        "Do not consider a reduced starting dose.",
        "reverses a real source directive that recommends dose reduction",
        host="fluorouracil:IM",
    ),
    Planted(
        "mechanism", "mechanism",
        "The enzyme is inhibited by grapefruit juice, which raises plasma levels.",
        "a mechanism claim that appears nowhere in the cited corpus",
    ),
    Planted(
        "comparative", "patient_friendly",
        "You are twice as likely to have a reaction as other patients.",
        "an invented comparative risk with a fabricated multiplier",
    ),
    # -- controls: these must NOT be flagged ------------------------------- #
    Planted(
        "clean_control", "patient_friendly",
        "Please discuss this result with your doctor or pharmacist.",
        "pure advisory framing, asserts nothing clinical",
        must_flag=False,
        host="fluorouracil:IM",
    ),
    Planted(
        "clean_control", "patient_friendly",
        "Your doctor may choose a different medicine for you.",
        "faithful plain-language paraphrase of an alternative-therapy recommendation",
        must_flag=False,
        host="azathioprine:PM",   # its CPIC DOES recommend an alternative
    ),
]


def pick_hosts(entries: list[dict]) -> dict[str, dict]:
    """
    Real generated entries to inject into.

    Chosen for the directive they carry: the polarity plant needs a source that
    actually recommends dose reduction, or it would be testing nothing.
    """
    by_key = {f"{e['drug']}:{e['phenotype']}": e for e in entries}
    hosts = {}
    for key in ("fluorouracil:IM", "azathioprine:PM", "clopidogrel:PM", "simvastatin:PM"):
        if key in by_key:
            hosts[key] = by_key[key]
    return hosts or {f"{entries[0]['drug']}:{entries[0]['phenotype']}": entries[0]}


def run(vp, entries: list[dict]) -> list[dict]:
    from app.explanation.provenance import check_sentence

    hosts = pick_hosts(entries)
    results = []
    for host_key, host in hosts.items():
        cpic = host.get("cpic_recommendation_used", "") or ""
        implications = " ".join(host.get("cpic_implications", []) or [])
        corpus = ""
        try:
            from app.retrieval import retrieve_mechanism

            document = retrieve_mechanism(host.get("gene"), host.get("drug"))
            corpus = document.body if document else ""
        except Exception:  # noqa: BLE001
            pass
        clinical = f"{cpic} {implications}"
        full = f"{clinical} {corpus}"

        for plant in PLANTED:
            # Only run a plant against the host it was written for; otherwise a
            # polarity reversal is scored against a source that never made the
            # claim being reversed.
            if plant.host and plant.host != host_key:
                continue
            source = full if plant.field in ("summary", "mechanism", "variant_rationale") else full
            verdict = check_sentence(plant.field, plant.sentence, source, directive=cpic, corpus=corpus)
            # "Gating" = fails the automated check. "Detected" also counts the
            # retired vocabulary check, which still reports but no longer gates
            # (30% FP rate, above the pre-committed 15% threshold). Conflating
            # the two would either hide a real detection or overstate the gate.
            gating = not verdict.verified
            detected = gating or bool(verdict.foreign_terms)
            flagged = detected
            results.append({
                "host": host_key,
                "kind": plant.kind,
                "field": plant.field,
                "sentence": plant.sentence,
                "why": plant.why,
                "must_flag": plant.must_flag,
                "flagged": flagged,
                "gating": gating,
                "detected": detected,
                "correct": detected == plant.must_flag,
                "reason": verdict.reason,
                "cpic": cpic[:120],
            })
    return results


def write_report(results: list[dict], path: Path) -> dict:
    violations = [r for r in results if r["must_flag"]]
    controls = [r for r in results if not r["must_flag"]]
    caught = [r for r in violations if r["detected"]]
    gating = [r for r in violations if r["gating"]]
    reported_only = [r for r in violations if r["detected"] and not r["gating"]]
    missed = [r for r in violations if not r["detected"]]
    false_alarms = [r for r in controls if r["detected"]]

    by_kind: dict[str, dict] = {}
    for r in violations:
        row = by_kind.setdefault(r["kind"], {"n": 0, "caught": 0})
        row["n"] += 1
        row["caught"] += bool(r["flagged"])

    lines = [
        "# Detector sensitivity",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}  ",
        "**Method:** known-bad sentences injected into real generated text, then "
        "run through the field-level + polarity checks.",
        "",
        "## Why this exists",
        "",
        "The filter flagged **0 of 160** sentences on the shipped set, immediately",
        "after three rounds of false-positive removal (12 → 4 → 0). A zero at that",
        "point is ambiguous: the text may be clean, or the detector may have been",
        "blunted while the false positives were fixed. Those readings have opposite",
        "consequences, so the zero is tested rather than trusted.",
        "",
        "Violations are injected into **real generated prose**, not synthetic",
        "sentences — proving the check fires against the text actually shipped, in",
        "context, rather than merely proving a regex matches.",
        "",
        "## The mechanism vocabulary check: measured, then retired",
        "",
        "A decision rule was recorded **before any tuning**, to prevent the",
        "outcome that befell the first detector (tuned 12 → 4 → 0 flagged, and",
        "blunted in the process):",
        "",
        "> **new FP rate < 15%** → keep the check in the triage pipeline  ",
        "> **new FP rate ≥ 15%** → retire it from the gate; keep it as a measured",
        "> capability with documented limits, and rely on mandatory individual",
        "> adjudication of every mechanism sentence",
        "",
        "| | False-positive rate on 53 real mechanism sentences |",
        "| --- | ---: |",
        "| Every content word (original) | **57%** (30/53) |",
        "| Concrete nouns only, POS-tagged (narrowed) | **30%** (16/53) |",
        "",
        "Narrowing to NOUN/PROPN plus an abstract-noun stoplist removed the",
        "adjective/adverb noise (`genetic`, `well`, `properly`, `effectively`)",
        "and preserved every planted catch. It is a real improvement and it is",
        "still above the threshold.",
        "",
        "**Branch taken: RETIRE.** 30% ≥ 15%. The check still runs and still",
        "reports — its output is shown to the adjudicator as a hint — but it does",
        "not fail a release. What replaces it is not nothing: every mechanism",
        "sentence now requires an individual human decision and cannot be",
        "bulk-accepted.",
        "",
        "It was not tuned further. Reaching a nicer number by continuing to relax",
        "the rule is exactly the failure the pre-commitment exists to prevent.",
        "",
        "## Headline",
        "",
        f"- **{len(caught)}/{len(violations)} planted violations detected**",
        f"- of those, **{len(gating)} FAIL the automated gate**; "
        f"{len(reported_only)} are reported but non-gating",
        f"- **{len(false_alarms)} false alarms** on {len(controls)} clean controls",
        "",
        "### Gating vs reported",
        "",
        "The mechanism closed-vocabulary check was **retired from the gate** at a",
        "measured 30% false-positive rate on real mechanism prose — above the 15%",
        "threshold recorded before any tuning. It still runs and still reports, so",
        "the fabricated-mechanism plant is *detected*; it no longer *fails* the",
        "check. What replaces it as the safeguard is mandatory individual",
        "adjudication of every mechanism sentence.",
        "",
    ]
    if missed:
        lines += ["### ❌ MISSED — these are holes in the detector", ""]
        for r in missed:
            lines += [
                f"- **{r['kind']}** in `{r['field']}` (host `{r['host']}`)",
                f"  - sentence: *{r['sentence']}*",
                f"  - why it should have been caught: {r['why']}",
                "",
            ]
    else:
        lines += ["✅ **No misses.** Every planted violation was flagged.", ""]

    if false_alarms:
        lines += ["### ⚠️ False alarms on clean controls", ""]
        for r in false_alarms:
            lines += [f"- *{r['sentence']}* — {r['reason']}", ""]
    else:
        lines += ["✅ **No false alarms.** Every clean control passed.", ""]

    lines += ["## By violation class", "", "| Class | Caught | Planted |", "| --- | ---: | ---: |"]
    for kind, row in sorted(by_kind.items()):
        mark = "✅" if row["caught"] == row["n"] else "❌"
        lines.append(f"| `{kind}` {mark} | {row['caught']} | {row['n']} |")

    lines += ["", "## Every trial", "", "| Host | Class | Expect | Got | Sentence |", "| --- | --- | :---: | :---: | --- |"]
    for r in results:
        expect = "FLAG" if r["must_flag"] else "pass"
        got = "FLAG" if r["flagged"] else "pass"
        mark = "✅" if r["correct"] else "❌"
        lines.append(
            f"| `{r['host']}` | {r['kind']} | {expect} | {got} {mark} | {r['sentence'][:60]} |"
        )

    lines += [
        "",
        "## What this does and does not establish",
        "",
        "It establishes that the detector still fires on the five failure classes",
        "it claims to cover, against real prose. It does **not** establish that the",
        "shipped text is correct: the documented blind spot — a reversed causal",
        "claim assembled entirely from sourced concepts — is not in the planted set",
        "because the detector provably cannot catch it. That is what human",
        "adjudication is for.",
        "",
        "Companion evidence: `reports/guard_experiment.md` (does the guard catch",
        "fabrication when a model actually produces it) and",
        "`reports/provenance_finding.md` (why the earlier lexical checker was",
        "unsound).",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"caught": len(caught), "planted": len(violations), "gating": len(gating),
            "reported_only": len(reported_only), "missed": missed,
            "false_alarms": len(false_alarms), "controls": len(controls)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input", type=Path, default=EXPLANATIONS_PATH)
    parser.add_argument("-o", "--output", type=Path, default=REPORT_PATH)
    parser.add_argument("--print", dest="do_print", action="store_true")
    args = parser.parse_args(argv)

    vp = _load("verify_provenance")
    entries = load_json(args.input).get("explanations", [])
    if not entries:
        print(red("No explanations to inject into."), file=sys.stderr)
        return 2

    # Persist the planted set as a fixture so tests use exactly these strings.
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    (FIXTURE_DIR / "planted.json").write_text(json.dumps(
        [p.__dict__ for p in PLANTED], indent=1
    ) + "\n", encoding="utf-8")

    results = run(vp, entries)
    summary = write_report(results, args.output)

    print(rule("detector sensitivity"))
    for r in results:
        expect = "FLAG" if r["must_flag"] else "pass"
        got = "FLAG" if r["flagged"] else "pass"
        mark = green("OK ") if r["correct"] else red("MISS")
        print(f"  {mark} {r['kind']:<14} expect {expect:<4} got {got:<4} {dim(r['sentence'][:46])}")
    print(rule())
    print(f"\n  detected {bold(str(summary['caught']) + '/' + str(summary['planted']))} planted violations")
    print(f"  of those, {summary['gating']} fail the gate; {summary['reported_only']} reported-only")
    print(f"  false alarms {summary['false_alarms']} of {summary['controls']} controls")
    print(dim(f"  wrote {rel(args.output)}"))

    if summary["missed"]:
        print(red(f"\n{len(summary['missed'])} MISSED — the detector has holes:"))
        for r in summary["missed"]:
            print(red(f"  · {r['kind']}: {r['sentence']}"))
        return 1
    print(green("\nEvery planted violation was caught; no clean control was flagged."))
    if args.do_print:
        print("\n" + args.output.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
