#!/usr/bin/env python3
"""
Second fidelity check: PharmCAT's OWN test VCFs, which are adversarial by design.

WHY THIS EXISTS ALONGSIDE THE 1000 GENOMES RUN

The 1000 Genomes cohort measures fidelity on *common* variation — the easy case,
where most samples are reference at most positions. PharmCAT's unit-test VCFs are
the opposite: each one is hand-built to exercise a specific edge in the matcher —
rare alleles, missing positions, compound heterozygotes, hom/het boundaries. If
our parsing makes an assumption that only holds for ordinary genotypes, these are
where it breaks.

74 VCFs across the five callable star-allele genes we report, taken from
`src/test/resources/org/pharmgkb/pharmcat/haplotype/` at tag v3.4.0.

WHAT IS MEASURED, AND THE ONE THING THAT IS NOT

  1. INTEGRATION FIDELITY (rigorous). Run PharmCAT, parse with our code, compare
     diplotype and phenotype field-by-field. Any difference is our bug. This is
     the same self-referential test as the cohort run, on harder input.

  2. FILENAME-ENCODED EXPECTATION (partial, and clearly labelled). PharmCAT names
     these files after the genotype they encode — `s1s2.vcf` is *1/*2. Where that
     convention is unambiguous it is decoded and compared against PharmCAT's call.

     That second comparison tests PharmCAT plus my decoding, NOT our integration,
     and it is reported separately for exactly that reason. Files whose names do
     not follow the simple `sNsM` pattern are counted as "not decoded" rather
     than guessed at — inventing an expected value to raise a denominator would
     produce a number that means nothing.
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import scrub  # noqa: E402

TESTVCF_DIR = REPO_ROOT / "test-data" / "reference" / "pharmcat_testvcfs"
ARTIFACT = REPO_ROOT / "reports" / "testvcf_fidelity.json"

_spec = importlib.util.spec_from_file_location(
    "validate_integration", Path(__file__).parent / "validate_integration.py"
)
_vi = importlib.util.module_from_spec(_spec)
sys.modules["validate_integration"] = _vi
_spec.loader.exec_module(_vi)

pharmcat_truth = _vi.pharmcat_truth
Mismatch = _vi.Mismatch
_norm = _vi._norm
_equivalent_diplotype = _vi._equivalent_diplotype
bold, dim, red, green = _vi.bold, _vi.dim, _vi.red, _vi.green

#: Directory name -> the gene symbol PharmCAT reports.
GENE_DIRS = {
    "cyp2c19": "CYP2C19",
    "cyp2c9": "CYP2C9",
    "SLCO1B1": "SLCO1B1",
    "TPMT": "TPMT",
    "DPYD": "DPYD",
    "NUDT15": "NUDT15",
}

#: `s1s2` -> *1/*2. Deliberately strict: two star numbers, optional letter
#: suffix, nothing else. Anything more elaborate (`c1129-5923c2846`,
#: `s1s1s1` for a triplication, `novariant`) is left undecoded on purpose.
_STAR_PAIR = re.compile(r"^s(\d+[a-z]?)s(\d+[a-z]?)$", re.IGNORECASE)


def decode_expected(stem: str) -> str | None:
    """The diplotype the filename encodes, or None when the name is not simple."""
    match = _STAR_PAIR.match(stem)
    if not match:
        return None
    return f"*{match.group(1).upper()}/*{match.group(2).upper()}"


def run_one(vcf: Path, invoker, outdir: Path) -> dict | None:
    """PharmCAT over one test VCF; returns the parsed report.json."""
    proc = subprocess.run(
        invoker.build(vcf, outdir), capture_output=True, text=True, timeout=300
    )
    reports = sorted(outdir.glob("*.report.json"))
    if not reports:
        print(red(f"    {vcf.name}: no report (exit {proc.returncode})"))
        return None
    try:
        return json.loads(reports[0].read_text())
    except json.JSONDecodeError as exc:
        print(red(f"    {vcf.name}: unparseable report: {scrub(exc)}"))
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=0, help="Cap files examined.")
    args = parser.parse_args(argv)

    from app.pharmcat_runner import parse_report, resolve_invoker, unavailable_reason

    invoker = resolve_invoker()
    if invoker is None:
        print(red(f"PharmCAT unavailable: {unavailable_reason()}"))
        return 2

    files = sorted(
        (gene_dir, vcf)
        for name, gene_dir in GENE_DIRS.items()
        for vcf in (TESTVCF_DIR / name).glob("*.vcf")
    )
    if not files:
        print(red(f"no test VCFs under {TESTVCF_DIR.relative_to(REPO_ROOT)}"))
        return 2
    if args.limit:
        files = files[: args.limit]

    print(bold(f"── PharmCAT test VCFs ({len(files)} files) ───────────────────"))
    print(dim(f"  {invoker.kind}: {invoker.describe}"))

    mismatches: list[Mismatch] = []
    compared = 0
    errors: dict[str, str] = {}
    decoded_agree = decoded_differ = 0
    decoded_detail: list[dict] = []
    undecoded: list[str] = []
    per_gene = collections.Counter()
    started = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="pharmaguard_testvcf_") as tmp:
        for index, (gene, vcf) in enumerate(files, start=1):
            outdir = Path(tmp) / f"out{index}"
            outdir.mkdir()
            raw = run_one(vcf, invoker, outdir)
            if raw is None:
                errors[vcf.name] = "no_report"
                continue
            truth = pharmcat_truth(raw)
            try:
                parsed = parse_report(raw, sample_hint=vcf.stem)
            except Exception as exc:  # noqa: BLE001
                errors[vcf.name] = f"parse_failure: {type(exc).__name__}: {scrub(exc)}"
                continue
            ours = dict(parsed.genes)

            expected = truth.get(gene)
            call = ours.get(gene)
            if expected is None or call is None:
                errors[vcf.name] = f"gene {gene} absent (pharmcat={expected is not None})"
                continue

            compared += 1
            per_gene[gene] += 1
            want = expected["diplotypes"][0] if expected["diplotypes"] else None
            if not _equivalent_diplotype(want, call.diplotype):
                mismatches.append(Mismatch(
                    vcf.name, gene, "diplotype", want, call.diplotype,
                    matches_recommendation=_vi._matches_reco(
                        expected, "recommendation_diplotypes", call.diplotype
                    ),
                ))
            if _norm(expected["phenotype"]) != _norm(call.phenotype_raw):
                mismatches.append(Mismatch(
                    vcf.name, gene, "phenotype_raw",
                    expected["phenotype"], call.phenotype_raw,
                    matches_recommendation=(
                        _norm(expected.get("recommendation_phenotype"))
                        == _norm(call.phenotype_raw)
                    ),
                ))

            # -- filename expectation, where the name is simple --------------- #
            wanted = decode_expected(vcf.stem)
            if wanted is None:
                undecoded.append(vcf.name)
            else:
                actual = want or ""
                if _norm(wanted) == _norm(actual):
                    decoded_agree += 1
                else:
                    decoded_differ += 1
                    decoded_detail.append({
                        "file": vcf.name, "gene": gene,
                        "filename_encodes": wanted, "pharmcat_called": actual,
                    })

    elapsed = time.monotonic() - started
    total_fields = compared * 2
    bad = len(mismatches)
    rate = (total_fields - bad) / total_fields if total_fields else 0.0

    print()
    print(bold("── integration fidelity (ours vs PharmCAT) ───────────────────"))
    print(f"  files compared        {compared} / {len(files)}   in {elapsed:.0f}s")
    print(f"  field comparisons     {total_fields}")
    colour = green if bad == 0 else red
    print(colour(f"  match rate            {rate * 100:.4f}%   mismatches: {bad}"))
    for mismatch in mismatches[:40]:
        print(red(f"    {mismatch.line()}"))
    if errors:
        print(red(f"  files erroring        {len(errors)}"))
        for name, err in list(errors.items())[:10]:
            print(red(f"    {name}: {err}"))
    print(f"  per gene: {dict(per_gene)}")

    print()
    print(bold("── filename-encoded expectation (tests PharmCAT, not us) ─────"))
    decoded_total = decoded_agree + decoded_differ
    print(f"  decodable names       {decoded_total} / {compared}"
          f"   (not decoded: {len(undecoded)})")
    if decoded_total:
        print(f"  agree with PharmCAT   {decoded_agree} / {decoded_total}"
              f"  ({decoded_agree / decoded_total * 100:.1f}%)")
    for row in decoded_detail[:20]:
        print(dim(f"    {row['file']}: name={row['filename_encodes']} "
                  f"called={row['pharmcat_called']!r}"))
    print(dim("  Undecoded names are NOT counted as failures — the convention is"))
    print(dim("  only unambiguous for simple star pairs, and guessing the rest"))
    print(dim("  would manufacture a denominator rather than measure anything."))

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "PharmGKB/PharmCAT @ v3.4.0 src/test/resources/.../haplotype",
        "files_available": len(files),
        "files_compared": compared,
        "per_gene": dict(per_gene),
        "integration_fidelity": {
            "field_comparisons": total_fields,
            "mismatches": bad,
            "match_rate": rate,
            "mismatch_detail": [
                {"file": m.sample, "gene": m.gene, "field": m.field,
                 "pharmcat": m.pharmcat, "ours": m.ours,
                 "matches_recommendation_diplotypes": m.matches_recommendation}
                for m in mismatches
            ],
            "errors": errors,
        },
        "filename_expectation": {
            "note": "tests PharmCAT + the filename decoder, NOT our integration",
            "decodable": decoded_total,
            "agree": decoded_agree,
            "differ": decoded_differ,
            "differ_detail": decoded_detail,
            "not_decoded": undecoded,
        },
    }, indent=1) + "\n")
    print()
    print(dim(f"  artifact: {ARTIFACT.relative_to(REPO_ROOT)}"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
