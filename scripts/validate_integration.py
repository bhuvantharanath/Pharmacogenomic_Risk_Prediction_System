#!/usr/bin/env python3
"""
Integration fidelity and call-rate measurement over real 1000 Genomes samples.

WHAT THIS MEASURES, AND WHAT IT CANNOT

This script answers one question precisely: **does PharmaGuard report what
PharmCAT actually said?** It is self-referential by design, so it needs no truth
labels and makes no claim about biological correctness.

    PharmCAT report.json          our parse_report() + profile
    ─────────────────────         ────────────────────────────
    diplotype label          vs   gene_call.diplotype
    phenotype wording        vs   gene_call.phenotype_raw
    callSource / no-call     vs   gene_call.status

Any disagreement is a bug in OUR code — a parser that drops a field, a mapping
that silently rewrites a call, an assumption that holds for synthetic VCFs and
fails on real ones. The target is therefore 100%, and anything less is a defect
rather than a finding about pharmacogenomics.

What it does NOT establish: that PharmCAT's calls are right. A shared error
between PharmCAT and us is invisible here, by construction. Genotype accuracy
needs an external truth set (GeT-RM), which is reported separately and as n=1.

EFFICIENCY, because it changes what is feasible

Two measurements shaped this script:

  * Remote slicing cost is dominated by reading the region's compressed blocks,
    not by how many samples are requested — 1 sample took 3.87 s and 300 took
    3.83 s for the same region. So the whole cohort is sliced in ONE pass per
    chromosome, not once per sample.
  * PharmCAT accepts a multi-sample VCF and writes `<base>.<sample>.report.json`
    for each, so the entire cohort costs ONE JVM start rather than N.

Together those turn a run that would take hours into one that takes minutes.

USAGE

    python scripts/validate_integration.py --limit 400
    python scripts/validate_integration.py --limit 400 --resume
    python scripts/validate_integration.py --dry-run

Cohort selection is deterministic (seeded, stratified by superpopulation), so a
re-run with the same --limit examines the same samples.
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import random
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Project convention: every rendered exception goes through scrub(), because
# third-party error text is outside our control and a captured terminal log is
# unrecoverable. Enforced by test_exception_sites_are_scrubbed.
from _common import scrub  # noqa: E402

REFERENCE_DIR = REPO_ROOT / "test-data" / "reference"
COHORT_DIR = REFERENCE_DIR / "cohort"
POPULATIONS = REFERENCE_DIR / "1000G_3202_populations.txt"
ARTIFACT = REPO_ROOT / "reports" / "integration_fidelity.json"

#: Deterministic cohort selection. Changing this changes which samples are
#: examined, which would invalidate comparison against a previous run.
COHORT_SEED = 20260725

# Reuse the slicer's verified gene coordinates rather than restating them: they
# are derived from PharmCAT's own positions VCF, and a second copy would drift.
_spec = importlib.util.spec_from_file_location(
    "fetch_reference_data", Path(__file__).parent / "fetch_reference_data.py"
)
_frd = importlib.util.module_from_spec(_spec)
sys.modules["fetch_reference_data"] = _frd
_spec.loader.exec_module(_frd)

THOUSAND_GENOMES_BASE = _frd.THOUSAND_GENOMES_BASE
THOUSAND_GENOMES_PATTERN = _frd.THOUSAND_GENOMES_PATTERN
TARGET_GENES = _frd.TARGET_GENES

#: CYP2D6 is the negative control: not callable from an unphased VCF at all, so
#: it must come back uncalled for every single sample. If it ever produces a
#: diplotype here, something is fabricating one.
NEGATIVE_CONTROL = "CYP2D6"
CALLABLE_GENES = tuple(g for g in TARGET_GENES if g != NEGATIVE_CONTROL)


def dim(text: str) -> str:
    return f"\033[2m{text}\033[0m"


def red(text: str) -> str:
    return f"\033[31m{text}\033[0m"


def green(text: str) -> str:
    return f"\033[32m{text}\033[0m"


def bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


# --------------------------------------------------------------------------- #
# Cohort
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Sample:
    sample_id: str
    population: str
    superpopulation: str


def load_panel() -> list[Sample]:
    if not POPULATIONS.is_file():
        raise SystemExit(
            f"missing {POPULATIONS.relative_to(REPO_ROOT)} — fetch it with:\n"
            f"  curl -s -o {POPULATIONS.relative_to(REPO_ROOT)} \\\n"
            f"    https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/"
            f"1000G_2504_high_coverage/20130606_g1k_3202_samples_ped_population.txt"
        )
    lines = POPULATIONS.read_text().splitlines()
    header = lines[0].split()
    i_id = header.index("SampleID")
    i_pop = header.index("Population")
    i_sup = header.index("Superpopulation")
    out = []
    for line in lines[1:]:
        cols = line.split()
        if len(cols) > max(i_id, i_pop, i_sup):
            out.append(Sample(cols[i_id], cols[i_pop], cols[i_sup]))
    return out


def select_cohort(panel: list[Sample], limit: int) -> list[Sample]:
    """
    Stratified by superpopulation, proportional to panel composition.

    Proportional rather than equal-sized groups: the frequency comparison in §3
    is against published population-specific tables, so a group needs enough
    members to be worth quoting. Deterministic under COHORT_SEED so a re-run
    examines the same samples.
    """
    if limit <= 0 or limit >= len(panel):
        return sorted(panel, key=lambda s: s.sample_id)

    by_super: dict[str, list[Sample]] = collections.defaultdict(list)
    for sample in panel:
        by_super[sample.superpopulation].append(sample)

    rng = random.Random(COHORT_SEED)
    chosen: list[Sample] = []
    for group in sorted(by_super):
        members = sorted(by_super[group], key=lambda s: s.sample_id)
        take = round(limit * len(members) / len(panel))
        rng.shuffle(members)
        chosen.extend(members[:take])
    return sorted(chosen, key=lambda s: s.sample_id)


# --------------------------------------------------------------------------- #
# Slicing
# --------------------------------------------------------------------------- #


def slice_cohort(cohort: list[Sample], *, resume: bool) -> Path | None:
    """
    One remote pass per chromosome for the whole cohort, then concatenate.

    Cached per (chromosome, cohort size) so an interrupted run resumes instead of
    re-downloading. The sample list is written to disk and passed with -S because
    400 ids on a command line is fragile.
    """
    COHORT_DIR.mkdir(parents=True, exist_ok=True)
    tag = f"n{len(cohort)}"
    combined = COHORT_DIR / f"cohort_{tag}.vcf"
    if combined.is_file() and resume:
        print(dim(f"  reusing {combined.name}"))
        return combined

    sample_file = COHORT_DIR / f"samples_{tag}.txt"
    sample_file.write_text("\n".join(s.sample_id for s in cohort) + "\n")

    regions = _frd.gene_regions()
    by_chrom: dict[str, list] = collections.defaultdict(list)
    for region in regions.values():
        by_chrom[region.chrom].append(region)

    parts: list[Path] = []
    for chrom in sorted(by_chrom, key=lambda c: int(c.removeprefix("chr"))):
        part = COHORT_DIR / f"{chrom}_{tag}.vcf.gz"
        spec = ",".join(r.region for r in by_chrom[chrom])
        if part.is_file() and resume:
            print(dim(f"  {chrom}: cached"))
            parts.append(part)
            continue
        url = f"{THOUSAND_GENOMES_BASE}/{THOUSAND_GENOMES_PATTERN.format(chrom=chrom)}"
        started = time.monotonic()
        try:
            subprocess.run(
                ["bcftools", "view", "-r", spec, "-S", str(sample_file),
                 "--force-samples", "-Oz", "-o", str(part), url],
                check=True, capture_output=True, timeout=1800,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            detail = getattr(exc, "stderr", b"") or b""
            print(red(f"  {chrom}: slice FAILED — {detail.decode()[-300:]}"))
            part.unlink(missing_ok=True)
            return None
        subprocess.run(["bcftools", "index", "-f", "-t", str(part)],
                       check=True, capture_output=True)
        print(f"  {chrom}: {part.stat().st_size / 1e6:.1f} MB "
              f"in {time.monotonic() - started:.0f}s")
        parts.append(part)

    # Uncompressed, because that is the form verified against PharmCAT.
    subprocess.run(
        ["bcftools", "concat", "-Ov", "-o", str(combined), *[str(p) for p in parts]],
        check=True, capture_output=True,
    )
    print(f"  combined: {combined.stat().st_size / 1e6:.1f} MB")
    return combined


# --------------------------------------------------------------------------- #
# PharmCAT
# --------------------------------------------------------------------------- #


def run_pharmcat_cohort(vcf: Path, outdir: Path, *, resume: bool) -> bool:
    """One JVM start for the whole multi-sample VCF."""
    from app.pharmcat_runner import resolve_invoker, unavailable_reason

    existing = list(outdir.glob("*.report.json")) if outdir.is_dir() else []
    if existing and resume:
        print(dim(f"  reusing {len(existing)} existing report(s)"))
        return True

    invoker = resolve_invoker()
    if invoker is None:
        print(red(f"  PharmCAT unavailable: {unavailable_reason()}"))
        return False
    outdir.mkdir(parents=True, exist_ok=True)
    print(dim(f"  {invoker.kind}: {invoker.describe}"))
    started = time.monotonic()
    proc = subprocess.run(
        invoker.build(vcf, outdir), capture_output=True, text=True, timeout=7200
    )
    elapsed = time.monotonic() - started
    reports = list(outdir.glob("*.report.json"))
    print(f"  {len(reports)} report(s) in {elapsed:.0f}s "
          f"({elapsed / max(len(reports), 1):.2f}s per sample)")
    if not reports:
        print(red(f"  PharmCAT produced nothing (exit {proc.returncode})"))
        print(dim((proc.stderr or proc.stdout or "")[-1500:]))
        return False
    return True


# --------------------------------------------------------------------------- #
# Comparison
# --------------------------------------------------------------------------- #


def pharmcat_truth(raw: dict) -> dict[str, dict]:
    """
    Read gene calls straight out of report.json, independently of our parser.

    Deliberately does not import anything from `app`: if this reused the parser
    it would be comparing the parser to itself, which is exactly the circularity
    that made an earlier provenance metric meaningless.
    """
    genes = raw.get("genes") or {}
    section = genes.get("CPIC") if isinstance(genes, dict) and "CPIC" in genes else genes
    out: dict[str, dict] = {}
    for gene, block in (section or {}).items():
        if gene not in TARGET_GENES or not isinstance(block, dict):
            continue
        record: dict[str, object] = {"call_source": block.get("callSource")}
        # BOTH fields are read, because PharmCAT means different things by them
        # and conflating them hides the most interesting result in this run:
        #
        #   sourceDiplotypes          what was actually CALLED, compound alleles
        #                             intact, phenotype possibly "Indeterminate"
        #   recommendationDiplotypes  PharmCAT's own reduction for LOOKING UP a
        #                             CPIC recommendation — compound alleles split,
        #                             an activity score assigned
        #
        # For DPYD these genuinely differ. Measuring against `source` answers
        # "do we report what PharmCAT called?"; also recording `recommendation`
        # lets a mismatch be attributed to a deliberate field choice rather than
        # to a parsing bug, which are different defects with different fixes.
        for key, prefix in (("sourceDiplotypes", "source"),
                            ("recommendationDiplotypes", "recommendation")):
            labels: list[str] = []
            phenotypes: list[str] = []
            for dip in block.get(key) or []:
                if not isinstance(dip, dict):
                    continue
                label = dip.get("label")
                if not label:
                    alleles = [dip.get("allele1"), dip.get("allele2")]
                    names = [a.get("name") for a in alleles if isinstance(a, dict)]
                    label = "/".join(n for n in names if n) or None
                if label:
                    labels.append(label)
                for phenotype in dip.get("phenotypes") or []:
                    if phenotype not in phenotypes:
                        phenotypes.append(phenotype)
            record[f"{prefix}_diplotypes"] = labels
            record[f"{prefix}_phenotype"] = phenotypes[0] if phenotypes else None
        # Back-compat aliases: the comparison below reads these.
        record["diplotypes"] = record["source_diplotypes"]
        record["phenotype"] = record["source_phenotype"]
        out[gene] = record
    return out


#: PharmCAT's sentinels for "there is no call here". Our parser normalises all of
#: them to None, which `pharmcat_models.PharmcatGeneCall` documents as its
#: representation of an uncalled gene ("or None when uncalled"). Treating that as
#: a mismatch would report 26 defects for one deliberate, documented choice — so
#: the equivalence is declared here rather than silently ignored.
_NO_CALL_SENTINELS = frozenset({"", "unknown/unknown", "unknown", "no result", "n/a"})


def _equivalent_diplotype(pharmcat: object, ours: object) -> bool:
    left, right = _norm(pharmcat), _norm(ours)
    if left == right:
        return True
    return left in _NO_CALL_SENTINELS and right in _NO_CALL_SENTINELS


def _matches_reco(expected: dict, key: str, ours: object) -> bool:
    values = expected.get(key) or []
    return any(_norm(v) == _norm(ours) for v in values)


@dataclass
class Mismatch:
    sample: str
    gene: str
    field: str
    pharmcat: object
    ours: object
    #: True when our value equals PharmCAT's `recommendationDiplotypes` instead of
    #: its `sourceDiplotypes`. That distinguishes "the parser lost data" from "the
    #: parser read the other field on purpose" — different defects, different fixes.
    matches_recommendation: bool = False

    def line(self) -> str:
        note = "  [= recommendationDiplotypes]" if self.matches_recommendation else ""
        return (f"{self.sample} {self.gene} {self.field}: "
                f"PharmCAT={self.pharmcat!r} ours={self.ours!r}{note}")


@dataclass
class Outcome:
    compared: int = 0
    mismatches: list[Mismatch] = field(default_factory=list)
    # (sample, gene) -> reason a usable call was not produced
    failures: dict[tuple[str, str], str] = field(default_factory=dict)
    # gene -> Counter of diplotype / phenotype
    diplotype_freq: dict[str, collections.Counter] = field(default_factory=dict)
    phenotype_freq: dict[str, collections.Counter] = field(default_factory=dict)
    # (gene, population) -> Counter
    phenotype_by_pop: dict[tuple[str, str], collections.Counter] = field(
        default_factory=dict
    )
    samples_seen: set[str] = field(default_factory=set)
    sample_errors: dict[str, str] = field(default_factory=dict)


def classify_failure(truth: dict, status: str | None) -> str | None:
    """
    Why this gene produced no usable phenotype. None means it did produce one.

    Reason classes are kept coarse on purpose: a long tail of one-off strings is
    not a distribution anyone can act on.
    """
    phenotype = (truth.get("phenotype") or "").strip().lower()
    source = (truth.get("call_source") or "").upper()
    diplotypes = truth.get("diplotypes") or []

    if source == "NONE":
        return "not_attempted_structural"      # CYP2D6: needs copy-number data
    if len(diplotypes) > 1:
        return "ambiguous_multiple_diplotypes"
    if not diplotypes:
        return "no_call_missing_positions"
    if phenotype in {"", "no result"}:
        return "no_call_missing_positions"
    if phenotype == "indeterminate":
        return "called_but_unclassifiable"     # data present, CPIC cannot place it
    return None


def compare(reports: list[Path], cohort: dict[str, Sample]) -> Outcome:
    from app.pharmcat_runner import parse_report

    outcome = Outcome()
    for path in sorted(reports):
        # `<base>.<sample>.report.json`
        stem = path.name.removesuffix(".report.json")
        sample_id = stem.split(".", 1)[1] if "." in stem else stem
        outcome.samples_seen.add(sample_id)
        meta = cohort.get(sample_id)

        try:
            raw = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            outcome.sample_errors[sample_id] = f"report_json_unparseable: {scrub(exc)}"
            continue

        truth = pharmcat_truth(raw)
        try:
            parsed = parse_report(raw, sample_hint=sample_id)
        except Exception as exc:  # noqa: BLE001 — any parser failure is a finding
            outcome.sample_errors[sample_id] = (
                f"parse_failure: {type(exc).__name__}: {scrub(exc)}"
            )
            continue

        ours = dict(parsed.genes)

        for gene in TARGET_GENES:
            expected = truth.get(gene)
            call = ours.get(gene)
            if expected is None and call is None:
                continue
            if expected is None or call is None:
                outcome.mismatches.append(Mismatch(
                    sample_id, gene, "gene_present",
                    expected is not None, call is not None,
                ))
                continue

            outcome.compared += 1

            # -- diplotype ------------------------------------------------- #
            want = expected["diplotypes"][0] if expected["diplotypes"] else None
            if not _equivalent_diplotype(want, call.diplotype):
                outcome.mismatches.append(Mismatch(
                    sample_id, gene, "diplotype", want, call.diplotype,
                    matches_recommendation=_matches_reco(
                        expected, "recommendation_diplotypes", call.diplotype
                    ),
                ))

            # -- phenotype wording, compared RAW --------------------------- #
            # Raw, not our enum: the enum deliberately collapses states (see
            # limitation #21), so comparing enums would score an intentional
            # design decision as an integration bug.
            if _norm(expected["phenotype"]) != _norm(call.phenotype_raw):
                outcome.mismatches.append(Mismatch(
                    sample_id, gene, "phenotype_raw",
                    expected["phenotype"], call.phenotype_raw,
                    matches_recommendation=(
                        _norm(expected.get("recommendation_phenotype"))
                        == _norm(call.phenotype_raw)
                    ),
                ))

            # -- the negative control -------------------------------------- #
            if gene == NEGATIVE_CONTROL and expected["diplotypes"] not in ([], None):
                real = [d for d in expected["diplotypes"]
                        if "unknown" not in (d or "").lower()]
                if real:
                    outcome.mismatches.append(Mismatch(
                        sample_id, gene, "negative_control_called",
                        "expected no call", real,
                    ))

            # -- failure class / frequency --------------------------------- #
            reason = classify_failure(expected, call.status.value if call.status else None)
            if reason:
                outcome.failures[(sample_id, gene)] = reason
            else:
                outcome.diplotype_freq.setdefault(gene, collections.Counter())[want] += 1
                phenotype = expected["phenotype"]
                outcome.phenotype_freq.setdefault(gene, collections.Counter())[phenotype] += 1
                if meta:
                    for key in ((gene, meta.population), (gene, meta.superpopulation)):
                        outcome.phenotype_by_pop.setdefault(
                            key, collections.Counter()
                        )[phenotype] += 1
    return outcome


def _norm(value: object) -> str:
    """Compare on content, not incidental whitespace or case."""
    if value is None:
        return ""
    return " ".join(str(value).split()).strip().lower()


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def emit(outcome: Outcome, cohort: list[Sample], elapsed: float) -> dict:
    n_samples = len(outcome.samples_seen)
    total = outcome.compared
    bad = len(outcome.mismatches)
    rate = (total - bad) / total if total else 0.0

    print()
    print(bold("── integration fidelity ──────────────────────────────────────"))
    print(f"  samples with a report     {n_samples} / {len(cohort)} requested")
    print(f"  (sample, gene) compared   {total}")
    print(f"  field comparisons         {total * 2}  (diplotype + phenotype_raw)")
    colour = green if bad == 0 else red
    print(colour(f"  match rate                {rate * 100:.4f}%   mismatches: {bad}"))
    if outcome.sample_errors:
        print(red(f"  samples erroring          {len(outcome.sample_errors)}"))
        for sample, err in list(outcome.sample_errors.items())[:10]:
            print(red(f"    {sample}: {err}"))
    for mismatch in outcome.mismatches[:60]:
        print(red(f"    {mismatch.line()}"))
    if bad > 60:
        print(red(f"    … and {bad - 60} more (all in the JSON artifact)"))

    print()
    print(bold("── usable results ────────────────────────────────────────────"))
    reasons = collections.Counter(outcome.failures.values())
    callable_pairs = n_samples * len(CALLABLE_GENES)
    callable_failures = sum(
        1 for (_s, g), _r in outcome.failures.items() if g in CALLABLE_GENES
    )
    usable = callable_pairs - callable_failures
    print(f"  callable (sample, gene)   {callable_pairs}   "
          f"[{len(CALLABLE_GENES)} genes x {n_samples} samples, CYP2D6 excluded]")
    if callable_pairs:
        print(f"  usable phenotype          {usable}  "
              f"({usable / callable_pairs * 100:.2f}%)")
    print("  reason classes:")
    for reason, count in reasons.most_common():
        print(f"    {reason:34} {count}")

    print()
    print(bold("── per-gene call rate ────────────────────────────────────────"))
    for gene in TARGET_GENES:
        got = sum(outcome.phenotype_freq.get(gene, collections.Counter()).values())
        note = "  (negative control)" if gene == NEGATIVE_CONTROL else ""
        pct = f"{got / n_samples * 100:5.1f}%" if n_samples else "   n/a"
        print(f"  {gene:9} {got:5} / {n_samples}  {pct}{note}")

    artifact = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(elapsed, 1),
        "cohort_seed": COHORT_SEED,
        "requested_samples": len(cohort),
        "samples_with_report": n_samples,
        "integration_fidelity": {
            "pairs_compared": total,
            "field_comparisons": total * 2,
            "mismatches": bad,
            "match_rate": rate,
            "mismatch_detail": [
                {"sample": m.sample, "gene": m.gene, "field": m.field,
                 "pharmcat": m.pharmcat, "ours": m.ours,
                 "matches_recommendation_diplotypes": m.matches_recommendation}
                for m in outcome.mismatches
            ],
            "sample_errors": outcome.sample_errors,
        },
        "usable_results": {
            "callable_pairs": callable_pairs,
            "usable": usable,
            "rate": (usable / callable_pairs) if callable_pairs else None,
            "reason_classes": dict(reasons),
        },
        "frequencies": {
            "diplotype": {g: dict(c) for g, c in outcome.diplotype_freq.items()},
            "phenotype": {g: dict(c) for g, c in outcome.phenotype_freq.items()},
            "phenotype_by_population": {
                f"{g}|{p}": dict(c) for (g, p), c in outcome.phenotype_by_pop.items()
            },
        },
        "cohort": [
            {"sample": s.sample_id, "population": s.population,
             "superpopulation": s.superpopulation} for s in cohort
        ],
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(artifact, indent=1) + "\n")
    print()
    print(dim(f"  artifact: {ARTIFACT.relative_to(REPO_ROOT)}"))
    return artifact


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--limit", type=int, default=400,
                        help="Cohort size (default 400; 0 = all 3202).")
    parser.add_argument("--resume", action="store_true",
                        help="Reuse cached slices and PharmCAT reports.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show the plan and exit without touching the network.")
    parser.add_argument("--keep", action="store_true",
                        help="Keep the per-sample PharmCAT output directory.")
    args = parser.parse_args(argv)

    for tool in ("bcftools",):
        if shutil.which(tool) is None:
            print(red(f"{tool} is required and not on PATH."))
            return 2

    panel = load_panel()
    cohort = select_cohort(panel, args.limit)
    by_super = collections.Counter(s.superpopulation for s in cohort)
    by_pop = collections.Counter(s.population for s in cohort)

    print(bold("── cohort ────────────────────────────────────────────────────"))
    print(f"  panel {len(panel)} samples -> selected {len(cohort)} "
          f"(seed {COHORT_SEED}, stratified)")
    print(f"  superpopulations: {dict(sorted(by_super.items()))}")
    sas = {p: c for p, c in sorted(by_pop.items())
           if p in {"PJL", "BEB", "STU", "ITU", "GIH"}}
    print(f"  SAS breakdown:    {sas}  (n={sum(sas.values())})")

    if args.dry_run:
        print(dim("\n  --dry-run: nothing fetched, nothing run."))
        return 0

    started = time.monotonic()
    print(bold("\n── slicing (one remote pass per chromosome) ───────────────────"))
    vcf = slice_cohort(cohort, resume=args.resume)
    if vcf is None:
        return 1

    print(bold("\n── PharmCAT (one JVM for the whole cohort) ───────────────────"))
    outdir = COHORT_DIR / f"pharmcat_n{len(cohort)}"
    if not run_pharmcat_cohort(vcf, outdir, resume=args.resume):
        return 1

    reports = sorted(outdir.glob("*.report.json"))
    print(bold("\n── comparing our parse against PharmCAT's own output ─────────"))
    outcome = compare(reports, {s.sample_id: s for s in cohort})
    artifact = emit(outcome, cohort, time.monotonic() - started)

    if not args.keep:
        # Reports are large and fully re-derivable; the artifact keeps the numbers.
        pass

    return 0 if artifact["integration_fidelity"]["mismatches"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
