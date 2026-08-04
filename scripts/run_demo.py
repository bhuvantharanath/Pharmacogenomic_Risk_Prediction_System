#!/usr/bin/env python3
"""
Run the demo. One command, same path for rehearsal and presentation.

WHY THIS IS A SCRIPT AND NOT A LIST OF CURL COMMANDS

Three attempts to walk the demo by hand each hit a different environmental
blocker — a CORS guard firing on an env marker, a rate limit exhausted by
rehearsal, and shell word-splitting mangling file paths into six 422s. None of
those were product defects, and all three would have happened on stage.

The demo path was the least-tested path in the system, so it is now tested like
everything else: `test_demo_script.py` runs this against the live API and asserts
each scenario's label class. A demo that can regress silently is not a demo.

USAGE

    python scripts/run_demo.py                 # all six, presentable output
    python scripts/run_demo.py --scenario 2    # just the centrepiece
    python scripts/run_demo.py --slow          # pause between scenarios
    python scripts/run_demo.py --json          # dump raw responses too
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Project convention: every rendered exception goes through scrub(), because
# third-party error text is outside our control and a captured terminal log — or
# a projector — is unrecoverable. Enforced by test_exception_sites_are_scrubbed.
from _common import scrub  # noqa: E402

DEMO_DIR = REPO_ROOT / "test-data" / "demo"
OUTPUT_DIR = DEMO_DIR / "outputs"

DEFAULT_BASE = os.environ.get("PHARMAGUARD_API", "http://127.0.0.1:8000")

BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"
RED, GREEN, AMBER, BLUE = "\033[31m", "\033[32m", "\033[33m", "\033[36m"


def colour_for(label: str) -> str:
    return {
        "Safe": GREEN,
        "Ineffective": RED,
        "Toxic": RED,
        "Adjust Dosage": AMBER,
        "Unknown": BLUE,
    }.get(label, "")


@dataclass(frozen=True)
class Scenario:
    number: int
    key: str
    vcf: str
    drugs: str
    headline: str
    #: One line the presenter says. Kept here so the runbook and the script
    #: cannot drift — there is one source for what this demonstrates.
    narration: str
    expect: str


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(1, "S1_confident", "demo_confident.vcf", "clopidogrel",
             "The system answers when the evidence supports it",
             "Complete-coverage VCF. CYP2C19 *2/*2 — a poor metaboliser. Clopidogrel "
             "is a prodrug this patient never activates, so it is Ineffective, and "
             "the recommendation text is CPIC's own words.",
             "Ineffective"),
    Scenario(2, "S2_variants_only", "demo_variants_only.vcf", "clopidogrel",
             "THE CENTREPIECE — same patient, and the system declines",
             "Same genotype. PharmCAT still calls *2/*2. The only difference is that "
             "this file lists variants only, with no homozygous-reference rows — the "
             "shape most VCFs in the wild have. An absent position is "
             "indistinguishable from one never tested, so missing data reads as "
             "normal, not as uncertainty. We measured up to 28.6% confidently-wrong "
             "calls at 60% coverage, every one reporting reduced function as normal.",
             "Unknown"),
    Scenario(3, "S3_cyp2d6", "demo_na12273_1000g.vcf", "codeine",
             "Declining what cannot be known from this data type",
             "Real 1000 Genomes sample, and it is in GeT-RM — which records its "
             "CYP2D6 as *1/*1. So a right answer exists, and we still decline, "
             "because CYP2D6 depends on copy-number variation a VCF cannot express.",
             "Unknown"),
    Scenario(4, "S4_dpyd", "demo_dpyd_indeterminate.vcf", "fluorouracil",
             "A different guard: the phenotype->label invariant",
             "Coverage passes here — 37.3% against DPYD's 20% minimum — so this is "
             "not the coverage gate. PharmCAT called the genotype but said "
             "Indeterminate. The lookup table would still have found a row and "
             "rendered Safe, on fluorouracil, where DPYD deficiency is fatal.",
             "Unknown"),
    Scenario(5, "S5_normal", "demo_normal.vcf", "simvastatin",
             "Not a system that says Unknown to everything",
             "All-reference control, complete coverage. SLCO1B1 *1/*1, normal "
             "transporter function, and a confident Safe.",
             "Safe"),
    Scenario(6, "S6_multidrug", "demo_confident.vcf",
             "clopidogrel,simvastatin,fluorouracil,codeine,ibuprofen",
             "Breadth, and graceful degradation",
             "Five drugs in one request. Ibuprofen has no CPIC guideline at all — it "
             "degrades to Unknown rather than erroring.",
             "mixed"),
)


@dataclass
class Result:
    scenario: Scenario
    status: int
    latency_ms: int
    body: dict = field(default_factory=dict)
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status == 200 and bool(self.body)

    def label_of(self, drug: str) -> str:
        for a in self.body.get("analyses", []):
            if a["drug"] == drug:
                return a["risk_assessment"]["risk_label"]
        return ""

    @property
    def primary(self) -> dict:
        analyses = self.body.get("analyses", [])
        return analyses[0] if analyses else {}


# --------------------------------------------------------------------------- #
# HTTP — stdlib only, so the demo has no dependency the backend does not
# --------------------------------------------------------------------------- #


def post_analyze(base: str, vcf: Path, drugs: str, timeout: int = 180) -> Result | None:
    boundary = f"----pharmaguard{uuid.uuid4().hex}"
    parts: list[bytes] = []
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="file"; filename="{vcf.name}"\r\n'
        f"Content-Type: text/plain\r\n\r\n".encode()
    )
    parts.append(vcf.read_bytes())
    parts.append(f"\r\n--{boundary}\r\n".encode())
    parts.append(b'Content-Disposition: form-data; name="drugs"\r\n\r\n')
    parts.append(drugs.encode())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    payload = b"".join(parts)

    request = urllib.request.Request(
        f"{base}/analyze",
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            elapsed = int((time.monotonic() - started) * 1000)
            return Result(SCENARIOS[0], response.status, elapsed,
                          json.loads(response.read()))
    except urllib.error.HTTPError as exc:
        elapsed = int((time.monotonic() - started) * 1000)
        raw = exc.read()
        try:
            body = json.loads(raw)
        except Exception:  # noqa: BLE001
            body = {"detail": raw.decode("utf-8", "replace")[:400]}
        return Result(SCENARIOS[0], exc.code, elapsed, {}, json.dumps(body))
    except Exception as exc:  # noqa: BLE001
        elapsed = int((time.monotonic() - started) * 1000)
        return Result(SCENARIOS[0], 0, elapsed, {}, f"{type(exc).__name__}: {scrub(exc)}")


def preflight(base: str) -> bool:
    """Fail early and specifically rather than mid-presentation."""
    print(f"{BOLD}── pre-flight ────────────────────────────────────────────────{RESET}")
    print(f"  base URL   {base}")
    try:
        with urllib.request.urlopen(f"{base}/ready", timeout=30) as response:
            ready = json.loads(response.read())
    except Exception as exc:  # noqa: BLE001
        print(f"{RED}  UNREACHABLE: {type(exc).__name__}: {scrub(exc)}{RESET}")
        print(f"{DIM}  Start it with:{RESET}")
        print(f"{DIM}    set -a && source backend/.env && set +a{RESET}")
        print(f"{DIM}    cd backend && uvicorn app.main:app --port 8000{RESET}")
        print(f"{DIM}  Then re-run, or set PHARMAGUARD_API to the printed URL.{RESET}")
        return False

    status = ready.get("status")
    print(f"  /ready     {GREEN if status == 'ready' else RED}{status}{RESET}")
    for name, check in ready.get("checks", {}).items():
        mark = f"{GREEN}ok{RESET}" if check.get("ok") else f"{RED}FAIL{RESET}"
        print(f"    {name:18} {mark}  {DIM}{str(check.get('detail'))[:56]}{RESET}")
    return status == "ready"


# --------------------------------------------------------------------------- #
# Presentation
# --------------------------------------------------------------------------- #


def coverage_line(result: Result, gene: str) -> str:
    cov = result.body.get("quality_metrics", {}).get("position_coverage", {})
    entry = cov.get(gene)
    if not entry:
        return "n/a"
    mark = f"{GREEN}pass{RESET}" if entry["sufficient"] else f"{AMBER}GATED{RESET}"
    return (f"{entry['positions_present']}/{entry['positions_required']} = "
            f"{entry['percent']:.1f}%  (min {entry['minimum_percent']}%)  {mark}")


def show(result: Result) -> None:
    s = result.scenario
    print()
    print(f"{BOLD}── S{s.number} · {s.headline} ──{RESET}")
    print(f"{DIM}  {s.vcf}  +  {s.drugs}{RESET}")
    if not result.ok:
        print(f"{RED}  FAILED  HTTP {result.status}  {result.error[:300]}{RESET}")
        return

    for a in result.body.get("analyses", []):
        p, r = a["pharmacogenomic_profile"], a["risk_assessment"]
        c = colour_for(r["risk_label"])
        print(f"  {a['drug']:14} {c}{BOLD}{r['risk_label']:14}{RESET}"
              f" severity={r['severity']:9} confidence={r['confidence_score']:.2f}")
        print(f"  {'':14} {DIM}{p['primary_gene']} {p['diplotype']} → "
              f"{p['phenotype']}{RESET}")
        if p.get("candidate_diplotypes"):
            print(f"  {'':14} {DIM}candidates: "
                  f"{', '.join(p['candidate_diplotypes'][:4])}{RESET}")

    gene = result.primary.get("pharmacogenomic_profile", {}).get("primary_gene", "")
    print(f"  {'coverage':14} {coverage_line(result, gene)}")

    warnings = result.body.get("quality_metrics", {}).get("warnings", [])
    # Show the warning that explains THIS scenario's result, not merely the first
    # interesting one. A multi-gene VCF carries coverage warnings for every gene,
    # and printing CYP2C9's while demonstrating DPYD buries the point.
    def rank(w: str) -> int:
        if gene and w.startswith(f"{gene}:"):
            return 0                                  # this gene, directly
        if "homozygous-reference" in w:
            return 1                                  # variants-only, always key
        if "Indeterminate" in w or "copy-number" in w:
            return 2                                  # the honesty guards
        if "required positions" in w:
            return 3                                  # another gene's coverage
        return 9
    key = sorted((w for w in warnings if rank(w) < 9), key=rank)
    print(f"  {'warnings':14} {len(warnings)} total")
    for w in key[:2]:
        for i, line in enumerate(textwrap.wrap(w, 74)[:2]):
            print(f"    {AMBER if i == 0 else DIM}{line}{RESET}")
    print(f"  {'latency':14} {result.latency_ms} ms")


def show_contrast(a: Result, b: Result) -> None:
    """
    S1 vs S2 side by side. This is the whole argument in one table: identical
    genotype, opposite outcomes, and the only difference is the file's shape.
    """
    if not (a.ok and b.ok):
        print(f"{RED}  contrast unavailable — one side failed{RESET}")
        return

    def field(r: Result, path: str) -> str:
        p = r.primary["pharmacogenomic_profile"]
        k = r.primary["risk_assessment"]
        cov = r.body["quality_metrics"]["position_coverage"].get(p["primary_gene"], {})
        return {
            "diplotype": p["diplotype"],
            "phenotype": p["phenotype"],
            "label": k["risk_label"],
            "severity": k["severity"],
            "confidence": f"{k['confidence_score']:.2f}",
            "coverage": f"{cov.get('positions_present')}/{cov.get('positions_required')}"
                        f" = {cov.get('percent', 0):.1f}%",
        }[path]

    print()
    print(f"{BOLD}══ THE CONTRAST — same patient, same genotype ══════════════════{RESET}")
    print(f"  {'':20} {BOLD}{'complete coverage':<26}{'variants-only':<26}{RESET}")
    print(f"  {DIM}{'-' * 72}{RESET}")
    for key, label in (("diplotype", "PharmCAT called"), ("phenotype", "phenotype"),
                       ("label", "RISK LABEL"), ("severity", "severity"),
                       ("confidence", "confidence"), ("coverage", "coverage")):
        left, right = field(a, key), field(b, key)
        same = left == right
        lc = "" if same else colour_for(left) or BOLD
        rc = "" if same else colour_for(right) or BOLD
        marker = f"{DIM}(identical){RESET}" if same else ""
        print(f"  {label:20} {lc}{left:<26}{RESET}{rc}{right:<26}{RESET}{marker}")
    print()
    print(f"  {DIM}The genotype is not lost — PharmCAT calls *2/*2 from both files.{RESET}")
    print(f"  {DIM}What changes is whether the system can verify the input supported{RESET}")
    print(f"  {DIM}it. Missing data does not read as uncertainty here; it reads as{RESET}")
    print(f"  {DIM}normal. So the system declines.{RESET}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--base", default=DEFAULT_BASE, help="API base URL.")
    parser.add_argument("--scenario", type=int, help="Run one scenario (1-6).")
    parser.add_argument("--slow", action="store_true",
                        help="Pause between scenarios for narration.")
    parser.add_argument("--json", action="store_true",
                        help="Also save raw responses to test-data/demo/outputs/.")
    parser.add_argument("--no-warmup", action="store_true",
                        help="Skip the JVM warm-up request.")
    parser.add_argument("--quiet-preflight", action="store_true")
    args = parser.parse_args(argv)

    if not preflight(args.base):
        return 2

    chosen = [s for s in SCENARIOS
              if args.scenario is None or s.number == args.scenario]
    if not chosen:
        print(f"{RED}no scenario {args.scenario}; valid: 1-6{RESET}")
        return 2

    if not args.no_warmup:
        warm = DEMO_DIR / "demo_normal.vcf"
        if warm.is_file():
            r = post_analyze(args.base, warm, "clopidogrel")
            print(f"  warm-up    {r.latency_ms if r else '?'} ms "
                  f"{DIM}(JVM class loading; not timed below){RESET}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Result] = {}
    started = time.monotonic()

    for s in chosen:
        vcf = DEMO_DIR / s.vcf
        if not vcf.is_file():
            print(f"{RED}missing demo file: {vcf}{RESET}")
            return 2
        result = post_analyze(args.base, vcf, s.drugs)
        result = Result(s, result.status, result.latency_ms, result.body, result.error)
        results[s.key] = result
        show(result)
        if args.json or True:
            (OUTPUT_DIR / f"{s.key}.json").write_text(
                json.dumps(result.body, indent=1) + "\n"
            )
        if args.slow and s is not chosen[-1]:
            try:
                input(f"{DIM}  [enter to continue]{RESET}")
            except EOFError:
                # Piped or redirected stdin: carry on rather than crashing
                # mid-sequence. --slow is a presentation aid, not a requirement.
                print(f"{DIM}  (no tty — continuing){RESET}")

    if "S1_confident" in results and "S2_variants_only" in results:
        show_contrast(results["S1_confident"], results["S2_variants_only"])

    elapsed = time.monotonic() - started
    failed = [k for k, r in results.items() if not r.ok]
    print()
    print(f"{BOLD}── summary ───────────────────────────────────────────────────{RESET}")
    for key, r in results.items():
        mark = f"{GREEN}ok{RESET}" if r.ok else f"{RED}FAIL ({r.status}){RESET}"
        print(f"  {key:20} {mark:20} {r.latency_ms:5} ms")
    print(f"  {'TOTAL':20} {'':20} {elapsed * 1000:5.0f} ms")
    if failed:
        print(f"{RED}  {len(failed)} scenario(s) failed: {failed}{RESET}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
