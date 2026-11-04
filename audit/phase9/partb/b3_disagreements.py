#!/usr/bin/env python3
"""
B3 measurement: where the coverage gate and PharmCAT's own evidence disagree.

    python audit/phase9/partb/b3_disagreements.py <tag>

For every gene of every input, two verdicts on the same thresholds:

  ours      app/coverage.assess on the VCF text (what the gate counted)
  PharmCAT  app/evidence_crosscheck.assess on the parsed report (what PharmCAT used)

Inputs: the 400-sample cohort (cached PharmCAT 3.4.0 reports, the same per-sample
VCF text the regression harness builds), every Part A A4 input that passes
validation, and the S1-S6 demo files (both run through the real runner).

Each disagreement is given a position-level cause; anything that cannot be
named is counted as `unexplained` (pre-committed to be 0, B3_PLAN.md AC4). The
invariant of AC3 is checked on the same responses: no confident label when
either verdict is insufficient for a gene the drug depends on.

Writes audit/phase9/partb/<tag>/b3_disagreements.json and .md.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "backend"))
os.environ.setdefault("EXPLANATION_MODE", "static")

from app import coverage, evidence_crosscheck, main  # noqa: E402
from app.capabilities import capability_for  # noqa: E402
from app.pharmcat_runner import parse_report, run_pharmcat  # noqa: E402

COHORT_VCF = REPO / "test-data/reference/cohort/cohort_n400.vcf"
COHORT_REPORTS = REPO / "test-data/reference/cohort/pharmcat_n400"
DRUGS = ["clopidogrel", "warfarin", "codeine", "simvastatin", "azathioprine", "fluorouracil"]
CONFIDENT = {"Ineffective", "Toxic", "Adjust Dosage", "No PGx-guided adjustment identified"}
USABLE = {coverage.EvidenceStatus.VALID, coverage.EvidenceStatus.QUALITY_NOT_ESTABLISHED}
REQ = coverage.load_requirements()["genes"]


def our_evidence(text: str) -> tuple[dict, dict]:
    """Per (contig, position): the gate's status, and the contig as written."""
    status, written = {}, {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 10:
            continue
        try:
            pos = int(parts[1])
        except ValueError:
            continue
        key = (coverage._norm_chrom(parts[0]), pos)
        st, _ = coverage._sample_evidence(parts)
        prev = status.get(key)
        if prev is None or coverage._STATUS_PRIORITY[st] > coverage._STATUS_PRIORITY[prev]:
            status[key] = st
        written.setdefault(key, parts[0])
    return status, written


def cause_of(gene: str, ours_ok: bool, theirs_ok: bool, text: str, report) -> list[str]:
    """Position-level reasons the two views differ for one gene."""
    status, written = our_evidence(text)
    call = report.gene(gene)
    variants = {v.position: v for v in call.variants} if call else {}
    used = {p for p, v in variants.items() if v.call}
    causes = []
    for chrom, pos in REQ[gene]["positions"]:
        key = (coverage._norm_chrom(chrom), int(pos))
        ours = status.get(key) in USABLE
        theirs = int(pos) in used
        if ours and not theirs:
            warns = " ".join(variants[int(pos)].warnings) if int(pos) in variants else ""
            if "does not match expected reference" in warns:
                causes.append("pharmcat_discarded_ref_mismatch")
            elif warns:
                causes.append("pharmcat_discarded_other")
            elif written.get(key) != chrom:
                causes.append("contig_name_not_recognised_by_pharmcat")
            else:
                causes.append("unexplained_pharmcat_unused")
        elif theirs and not ours:
            causes.append(f"gate_rejected_{status.get(key, coverage.EvidenceStatus.ABSENT).value}")
    if not causes and ours_ok != theirs_ok:
        causes.append("unexplained_same_positions_different_verdict")
    return causes


def run_case(source, case, metadata, report, drugs, table, rows, violations):
    cov = coverage.assess(metadata.text)
    theirs = evidence_crosscheck.assess(report)
    response = main.build_response(report, drugs, metadata, 0, cov=cov)
    for gene, ev in theirs.items():
        if gene not in cov.genes:
            continue
        ours_ok = cov.genes[gene].sufficient
        cell = f"{'S' if ours_ok else 'I'}{'S' if ev.sufficient else 'I'}"
        table[source][gene][cell] += 1
        if ours_ok != ev.sufficient:
            causes = cause_of(gene, ours_ok, ev.sufficient, metadata.text, report)
            rows.append({"source": source, "case": case, "gene": gene, "cell": cell,
                         "ours": f"{cov.genes[gene].present}/{cov.genes[gene].required}",
                         "pharmcat": f"{ev.used}/{ev.required}",
                         "causes": dict(Counter(causes))})
    labels = {}
    for a in response.analyses:
        label = a.risk_assessment.risk_label.value
        labels[a.drug] = label
        if label not in CONFIDENT:
            continue
        cap = capability_for(a.drug)
        for gene in (cap.evidence_dependencies if cap else ()):
            ours_ok = gene in cov.genes and cov.genes[gene].sufficient
            theirs_ok = gene in theirs and theirs[gene].sufficient
            if not (ours_ok and theirs_ok):
                violations.append({"source": source, "case": case, "drug": a.drug,
                                   "label": label, "gene": gene,
                                   "ours": ours_ok, "pharmcat": theirs_ok})
    return labels


def cohort(table, rows, violations) -> dict:
    from app.vcf_validation import validate_vcf
    meta, chrom, body = [], None, []
    with COHORT_VCF.open() as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("##"):
                meta.append(line)
            elif line.startswith("#CHROM"):
                chrom = line.split("\t")
            elif line:
                body.append(line.split("\t"))
    labels = {}
    for index, sample in enumerate(chrom[9:]):
        column = 9 + index
        text = "\n".join(meta + ["\t".join(chrom[:9] + [sample])]
                         + ["\t".join(r[:7] + ["."] + [r[8], r[column]]) for r in body]) + "\n"
        metadata = validate_vcf(text.encode(), filename=f"{sample}.vcf")
        raw = json.loads((COHORT_REPORTS / f"cohort_n400.{sample}.report.json").read_text())
        report = parse_report(raw, sample_hint=sample)
        labels[sample] = run_case("cohort", sample, metadata, report, DRUGS, table, rows, violations)
    return labels


def live(source, cases: dict[str, tuple[Path, list[str]]], table, rows, violations) -> dict:
    labels = {}
    for case, (path, drugs) in sorted(cases.items()):
        try:
            metadata = main._read_and_validate(path.read_bytes(), path.name)
        except Exception as exc:  # noqa: BLE001 — a 4xx input has no verdicts
            labels[case] = {"declined_at_upload": type(exc).__name__}
            continue
        report = asyncio.run(run_pharmcat(metadata.text, sample_hint=case))
        labels[case] = run_case(source, case, metadata, report, drugs, table, rows, violations)
    return labels


def main_() -> int:
    tag = sys.argv[1]
    dest = OUT / tag
    dest.mkdir(parents=True, exist_ok=True)
    table: dict = defaultdict(lambda: defaultdict(Counter))
    rows: list = []
    violations: list = []

    sys.path.insert(0, str(REPO / "audit/phase9/partb"))
    import a4_labels  # noqa: PLC0415
    a4 = {case: (path, DRUGS) for case, path in a4_labels.cases().items()}
    demo = REPO / "test-data/demo"
    s1s6 = {
        "S1_confident": (demo / "demo_confident.vcf", ["clopidogrel"]),
        "S2_variants_only": (demo / "demo_variants_only.vcf", ["clopidogrel"]),
        "S3_cyp2d6": (demo / "demo_na12273_1000g.vcf", ["codeine"]),
        "S4_dpyd": (demo / "demo_dpyd_indeterminate.vcf", ["fluorouracil"]),
        "S5_normal": (demo / "demo_normal.vcf", ["simvastatin"]),
        "S6_multidrug": (demo / "demo_confident.vcf",
                         ["clopidogrel", "simvastatin", "fluorouracil", "codeine", "ibuprofen"]),
    }
    labels = {
        "s1_s6": live("s1_s6", s1s6, table, rows, violations),
        "a4": live("a4", a4, table, rows, violations),
        "cohort": cohort(table, rows, violations),
    }
    causes = Counter()
    for row in rows:
        causes.update(row["causes"])
    unexplained = sum(n for c, n in causes.items() if c.startswith("unexplained"))
    result = {
        "tag": tag,
        "table": {src: {g: dict(c) for g, c in genes.items()} for src, genes in table.items()},
        "disagreements": len(rows),
        "disagreements_by_cell": dict(Counter(r["cell"] for r in rows)),
        "cause_counts": dict(causes),
        "unexplained": unexplained,
        "invariant_violations": violations,
        "rows": rows,
        "labels": labels,
    }
    (dest / "b3_disagreements.json").write_text(json.dumps(result, indent=1, sort_keys=True))
    lines = ["| source | gene | ours S / PharmCAT S | S / I | I / S | I / I |", "|---|---|---|---|---|---|"]
    for src in ("s1_s6", "a4", "cohort"):
        for gene, c in sorted(result["table"].get(src, {}).items()):
            lines.append(f"| {src} | {gene} | {c.get('SS', 0)} | {c.get('SI', 0)} | {c.get('IS', 0)} | {c.get('II', 0)} |")
    lines += ["", f"Disagreements: {len(rows)} {result['disagreements_by_cell']}",
              f"Causes (position-level): {dict(causes)}",
              f"Unexplained: {unexplained}",
              f"Invariant violations (confident with either verdict insufficient): {len(violations)}"]
    (dest / "b3_disagreements.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[-4:]))
    return 0


if __name__ == "__main__":
    sys.exit(main_())
