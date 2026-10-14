#!/usr/bin/env python3
"""Frozen GeT-RM/1000 Genomes external analytical benchmark.

This script deliberately separates three questions:

1. What does the independent CDC GeT-RM table say?
2. What genomic evidence is present in the frozen 1000 Genomes release, and
   does it satisfy the application's declared input contract?
3. What did PharmCAT and the unchanged application assert from that evidence?

Run ``prepare`` before ``fetch`` or ``evaluate``.  ``prepare`` writes and hashes
the cohort and truth locks without reading any PharmCAT/application output.
Missing VCF positions are never synthesized as reference genotypes.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator


REPO = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = REPO / "test-data" / "benchmark" / "external"
PROTOCOL = BENCHMARK_DIR / "protocol.json"
MANIFEST = BENCHMARK_DIR / "benchmark_manifest.json"
WORKBOOK = BENCHMARK_DIR / "Consolidated_PGx-HLA_table_1-22-25-V4.xlsx"
PANEL = REPO / "test-data" / "reference" / "1000G_3202_populations.txt"
TOOLS = REPO / "test-data" / "reference" / "tools"
POSITIONS = TOOLS / "pharmcat_positions_3.4.0.vcf.bgz"
JAR = TOOLS / "pharmcat-3.4.0-all.jar"
COHORT_LOCK = BENCHMARK_DIR / "cohort_lock.json"
TRUTH_TABLE = BENCHMARK_DIR / "sample_gene_truth.tsv"
ELIGIBILITY_TABLE = BENCHMARK_DIR / "input_eligibility.tsv"
EXCLUSIONS = BENCHMARK_DIR / "exclusions.tsv"
DISCREPANCIES = BENCHMARK_DIR / "discrepancies.tsv"
RESULTS = BENCHMARK_DIR / "external_benchmark_results.json"
REPORT_MANIFEST = BENCHMARK_DIR / "pharmcat_report_manifest.json"
REPORT = REPO / "reports" / "external_analytical_benchmark.md"
SLICE_DIR = BENCHMARK_DIR / "genomic"
REPORT_DIR = BENCHMARK_DIR / "pharmcat_reports"

TRUTH_SHEET = "PGx HLA Genotypes"
GENE_COLUMNS = {
    "CYP2C9": (20, 21),
    "CYP2C19": (22, 23),
    "CYP2D6": (24, 25),
    "DPYD": (34, 35),
    "NUDT15": (49, 50),
    "SLCO1B1": (55, 56),
    "TPMT": (59, 60),
}
PRIMARY_GENES = ("CYP2C19", "CYP2C9", "DPYD", "NUDT15", "SLCO1B1", "TPMT")
ALL_GENES = (*PRIMARY_GENES, "CYP2D6")
GENE_TO_DRUG = {
    "CYP2C19": "clopidogrel",
    "CYP2C9": "warfarin",
    "DPYD": "fluorouracil",
    "NUDT15": "azathioprine",
    "SLCO1B1": "simvastatin",
    "TPMT": "azathioprine",
    "CYP2D6": "codeine",
}
BASE_URL = (
    "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/"
    "1000G_2504_high_coverage/working/20220422_3202_phased_SNV_INDEL_SV"
)
VCF_PATTERN = "1kGP_high_coverage_Illumina.{chrom}.filtered.SNV_INDEL_SV_phased_panel.vcf.gz"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n")


def write_tsv(path: Path, fieldnames: list[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


@dataclass(frozen=True)
class PanelSample:
    sample_id: str
    family_id: str
    father_id: str
    mother_id: str
    sex: str
    population: str
    superpopulation: str


def load_panel(path: Path = PANEL) -> dict[str, PanelSample]:
    with path.open() as handle:
        reader = csv.DictReader(handle, delimiter=" ", skipinitialspace=True)
        rows: dict[str, PanelSample] = {}
        for row in reader:
            sample_id = (row.get("SampleID") or "").strip()
            if not sample_id:
                continue
            rows[sample_id] = PanelSample(
                sample_id=sample_id,
                family_id=(row.get("FamilyID") or "").strip(),
                father_id=(row.get("FatherID") or "").strip(),
                mother_id=(row.get("MotherID") or "").strip(),
                sex=(row.get("Sex") or "").strip(),
                population=(row.get("Population") or "").strip(),
                superpopulation=(row.get("Superpopulation") or "").strip(),
            )
    return rows


_SIMPLE_STAR_DIPLOTYPE = re.compile(
    r"^\s*(\*[^/\s]+(?:\s*\+\s*\*[^/\s]+)*)\s*/\s*"
    r"(\*[^/\s]+(?:\s*\+\s*\*[^/\s]+)*)\s*$"
)


def normalize_diplotype(value: object) -> tuple[str, str]:
    """Return (status, order-only-normalized value) without inventing equivalence."""
    raw = "" if value is None else str(value).strip()
    if not raw:
        return "truth_blank", ""
    lowered = raw.lower()
    if " or " in lowered or "undefined" in lowered or "unknown" in lowered:
        return "truth_unresolved_or_discordant", ""
    match = _SIMPLE_STAR_DIPLOTYPE.fullmatch(raw)
    if not match:
        return "truth_nomenclature_not_safely_parseable", ""
    alleles = [re.sub(r"\s+", "", match.group(1)), re.sub(r"\s+", "", match.group(2))]
    return "evaluable", "/".join(sorted(alleles))


def same_diplotype(left: str, right: str) -> bool:
    left_status, left_norm = normalize_diplotype(left)
    right_status, right_norm = normalize_diplotype(right)
    return left_status == right_status == "evaluable" and left_norm == right_norm


def candidate_compatible(truth: str, candidates: Iterable[str]) -> bool:
    return any(same_diplotype(truth, candidate) for candidate in candidates)


def prepare() -> None:
    if not PROTOCOL.is_file() or not MANIFEST.is_file() or not WORKBOOK.is_file():
        raise SystemExit("protocol, manifest, and CDC workbook must exist before prepare")
    manifest = read_json(MANIFEST)
    if manifest["protocol_sha256"] != sha256(PROTOCOL):
        raise SystemExit("frozen protocol hash differs from benchmark_manifest.json")
    if COHORT_LOCK.is_file() and TRUTH_TABLE.is_file():
        lock = read_json(COHORT_LOCK)
        checks = {
            "protocol": (sha256(PROTOCOL), lock.get("protocol_sha256")),
            "truth workbook": (sha256(WORKBOOK), lock.get("truth_workbook_sha256")),
            "panel manifest": (sha256(PANEL), lock.get("panel_manifest_sha256")),
            "truth table": (sha256(TRUTH_TABLE), lock.get("sample_gene_truth_sha256")),
        }
        changed = [name for name, (observed, frozen) in checks.items() if observed != frozen]
        if changed:
            raise SystemExit(
                "refusing to replace frozen cohort after source/output change: "
                + ", ".join(changed)
            )
        print(
            f"reusing frozen cohort: {lock['sample_count']} samples × "
            f"{len(lock['genes'])} genes"
        )
        return

    # Lazy dependency: unit tests can exercise all comparison/statistics helpers
    # without requiring spreadsheet support.
    import openpyxl

    panel = load_panel()
    workbook = openpyxl.load_workbook(WORKBOOK, read_only=True, data_only=True)
    sheet = workbook[TRUTH_SHEET]
    raw_rows = [row for row in sheet.iter_rows(min_row=3, values_only=True) if row[1]]
    by_id = {str(row[1]).strip(): row for row in raw_rows}
    cohort_ids = sorted(set(panel).intersection(by_id))

    truth_rows: list[dict] = []
    exclusion_rows: list[dict] = []
    for sample_id in cohort_ids:
        source = by_id[sample_id]
        study_refs = "" if source[0] is None else str(source[0]).strip()
        for gene in ALL_GENES:
            value_col, ref_col = GENE_COLUMNS[gene]
            raw = "" if source[value_col - 1] is None else str(source[value_col - 1]).strip()
            refs = "" if source[ref_col - 1] is None else str(source[ref_col - 1]).strip()
            status, normalized = normalize_diplotype(raw)
            truth_rows.append({
                "sample_id": sample_id,
                "gene": gene,
                "drug_context": GENE_TO_DRUG[gene],
                "truth_raw": raw,
                "truth_normalized": normalized,
                "truth_status": status,
                "truth_source_references": refs,
                "sample_study_references": study_refs,
                "independent_phenotype_truth": "",
                "truth_actionability": "unavailable",
                "actionability_reason": (
                    "CDC consensus table supplies genotype but no independent phenotype/drug-context "
                    "truth; not derived from PharmCAT or the application"
                ),
            })
            if status != "evaluable":
                exclusion_rows.append({
                    "stage": "truth",
                    "sample_id": sample_id,
                    "gene": gene,
                    "reason": status,
                    "detail": raw or "blank CDC truth cell",
                })

    truth_fields = [
        "sample_id", "gene", "drug_context", "truth_raw", "truth_normalized",
        "truth_status", "truth_source_references", "sample_study_references",
        "independent_phenotype_truth", "truth_actionability", "actionability_reason",
    ]
    write_tsv(TRUTH_TABLE, truth_fields, truth_rows)
    write_tsv(EXCLUSIONS, ["stage", "sample_id", "gene", "reason", "detail"], exclusion_rows)

    counts = collections.Counter(row["truth_status"] for row in truth_rows)
    lock = {
        "benchmark_id": manifest["benchmark_id"],
        "locked_at": utc_now(),
        "selection_rule": "all identifiers in the CDC workbook and frozen 1000G 3,202-sample manifest",
        "sample_count": len(cohort_ids),
        "sample_ids": cohort_ids,
        "sample_metadata": [panel[sample_id].__dict__ for sample_id in cohort_ids],
        "genes": list(ALL_GENES),
        "truth_rows": len(truth_rows),
        "truth_status_counts": dict(sorted(counts.items())),
        "truth_actionability": (
            "FROZEN_UNAVAILABLE: no independent phenotype/drug-context truth in the selected CDC source"
        ),
        "protocol_sha256": sha256(PROTOCOL),
        "truth_workbook_sha256": sha256(WORKBOOK),
        "panel_manifest_sha256": sha256(PANEL),
        "sample_gene_truth_sha256": sha256(TRUTH_TABLE),
        "exclusions_sha256_at_lock": sha256(EXCLUSIONS),
        "performance_output_examined_before_lock": False,
    }
    write_json(COHORT_LOCK, lock)

    manifest["truth"].update({
        "sha256": sha256(WORKBOOK),
        "bytes": WORKBOOK.stat().st_size,
        "acquired_at": utc_now(),
        "sheet": TRUTH_SHEET,
        "declared_sample_count": len(by_id),
    })
    manifest["genomic"]["panel_sample_count_observed"] = len(panel)
    manifest["locks"].update({
        "cohort": "FROZEN",
        "truth_actionability": "FROZEN_UNAVAILABLE",
        "performance_evaluated": False,
    })
    manifest["cohort_lock_path"] = str(COHORT_LOCK.relative_to(REPO))
    manifest["cohort_lock_sha256"] = sha256(COHORT_LOCK)
    manifest["sample_gene_truth_sha256"] = sha256(TRUTH_TABLE)
    write_json(MANIFEST, manifest)
    print(f"locked {len(cohort_ids)} samples × {len(ALL_GENES)} genes ({len(truth_rows)} rows)")
    print(f"truth statuses: {dict(sorted(counts.items()))}")


@dataclass(frozen=True)
class GeneRegion:
    gene: str
    chrom: str
    start: int
    end: int
    positions: int

    @property
    def spec(self) -> str:
        return f"{self.chrom}:{self.start}-{self.end}"


def gene_regions() -> dict[str, GeneRegion]:
    if not POSITIONS.is_file():
        raise SystemExit(f"missing PharmCAT positions file: {POSITIONS}")
    proc = subprocess.run(
        ["bcftools", "query", "-f", "%CHROM\t%POS\t%INFO/PX\n", str(POSITIONS)],
        check=True, capture_output=True, text=True,
    )
    spans: dict[str, list] = {}
    for line in proc.stdout.splitlines():
        chrom, pos_text, px, *_ = line.split("\t")
        for gene in (token.strip() for token in px.split(",")):
            if gene not in ALL_GENES:
                continue
            pos = int(pos_text)
            span = spans.setdefault(gene, [chrom, pos, pos, 0])
            span[1] = min(span[1], pos)
            span[2] = max(span[2], pos)
            span[3] += 1
    return {gene: GeneRegion(gene, *values) for gene, values in spans.items()}


def fetch(*, resume: bool) -> None:
    if not COHORT_LOCK.is_file():
        raise SystemExit("run prepare before fetch")
    if shutil.which("bcftools") is None:
        raise SystemExit("bcftools is required")
    lock = read_json(COHORT_LOCK)
    sample_ids = lock["sample_ids"]
    SLICE_DIR.mkdir(parents=True, exist_ok=True)
    sample_file = SLICE_DIR / "locked_samples.txt"
    sample_file.write_text("\n".join(sample_ids) + "\n")

    regions = gene_regions()
    by_chrom: dict[str, list[GeneRegion]] = collections.defaultdict(list)
    for region in regions.values():
        by_chrom[region.chrom].append(region)

    parts: list[Path] = []
    source_records: list[dict] = []
    for chrom in sorted(by_chrom, key=lambda value: int(value.removeprefix("chr"))):
        target = SLICE_DIR / f"{chrom}.locked_cohort.vcf.gz"
        index = Path(str(target) + ".tbi")
        url = f"{BASE_URL}/{VCF_PATTERN.format(chrom=chrom)}"
        spec = ",".join(region.spec for region in by_chrom[chrom])
        started = time.monotonic()
        if not (resume and target.is_file() and index.is_file()):
            subprocess.run(
                ["bcftools", "view", "-r", spec, "-S", str(sample_file),
                 "--force-samples", "-Oz", "-o", str(target), url],
                check=True, timeout=1800,
            )
            subprocess.run(["bcftools", "index", "-f", "-t", str(target)], check=True)
        subprocess.run(["bcftools", "view", "-h", str(target)], check=True, capture_output=True)
        parts.append(target)
        source_records.append({
            "chromosome": chrom,
            "source_url": url,
            "regions": spec,
            "local_path": str(target.relative_to(REPO)),
            "sha256": sha256(target),
            "bytes": target.stat().st_size,
            "index_sha256": sha256(index),
            "elapsed_seconds": round(time.monotonic() - started, 2),
        })
        print(f"{chrom}: {target.stat().st_size / 1e6:.1f} MB")

    combined = SLICE_DIR / "locked_cohort.vcf.gz"
    if not (resume and combined.is_file()):
        subprocess.run(
            ["bcftools", "concat", "-Oz", "-o", str(combined), *map(str, parts)],
            check=True,
        )
        subprocess.run(["bcftools", "index", "-f", "-t", str(combined)], check=True)
    observed = subprocess.run(
        ["bcftools", "query", "-l", str(combined)], check=True, capture_output=True, text=True
    ).stdout.split()
    if observed != sample_ids:
        raise SystemExit("combined VCF sample list/order differs from frozen cohort")

    manifest = read_json(MANIFEST)
    manifest["genomic"].update({
        "slices": source_records,
        "combined_path": str(combined.relative_to(REPO)),
        "combined_sha256": sha256(combined),
        "combined_bytes": combined.stat().st_size,
        "combined_index_sha256": sha256(Path(str(combined) + ".tbi")),
        "sample_count": len(observed),
        "sample_extraction": "bcftools sample subset only; no genotype rewriting or reference filling",
    })
    manifest["locks"]["genomic_evidence"] = "ACQUIRED_AND_HASHED"
    write_json(MANIFEST, manifest)
    print(f"combined: {combined.stat().st_size / 1e6:.1f} MB; {len(observed)} samples")


def wilson(successes: int, total: int) -> dict | None:
    if total < 5:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return {
        "level": 0.95,
        "method": "Wilson",
        "lower": 0.0 if successes == 0 else max(0.0, centre - margin),
        "upper": 1.0 if successes == total else min(1.0, centre + margin),
    }


def proportion(successes: int, total: int) -> dict:
    return {
        "numerator": successes,
        "denominator": total,
        "proportion": successes / total if total else None,
        "confidence_interval": wilson(successes, total) if total else None,
    }


def _raw_pharmcat_calls(raw: dict) -> dict[str, dict]:
    genes = raw.get("genes") or {}
    section = genes.get("CPIC") if isinstance(genes, dict) and "CPIC" in genes else genes
    output: dict[str, dict] = {}
    for gene, block in (section or {}).items():
        if gene not in ALL_GENES or not isinstance(block, dict):
            continue
        labels: list[str] = []
        phenotypes: list[str] = []
        for item in block.get("sourceDiplotypes") or []:
            if not isinstance(item, dict):
                continue
            label = item.get("label")
            if not label:
                names = [
                    allele.get("name") for allele in (item.get("allele1"), item.get("allele2"))
                    if isinstance(allele, dict) and allele.get("name")
                ]
                label = "/".join(names)
            if label:
                labels.append(label)
            for phenotype in item.get("phenotypes") or []:
                if phenotype and phenotype not in phenotypes:
                    phenotypes.append(phenotype)
        no_call = str(block.get("callSource") or "").upper() == "NONE"
        labels = [
            label for label in labels
            if label.strip().lower() not in {"", "unknown/unknown", "unknown", "no result", "n/a"}
        ]
        if no_call:
            labels = []
        output[gene] = {
            "call_source": block.get("callSource"),
            "diplotypes": labels,
            "phenotypes": [] if no_call else phenotypes,
        }
    return output


def _sample_id_from_report(path: Path, cohort_ids: set[str]) -> str | None:
    matches = [sample_id for sample_id in cohort_ids if sample_id in path.name]
    return max(matches, key=len) if matches else None


def _run_pharmcat(combined: Path, *, resume: bool) -> None:
    if resume and len(list(REPORT_DIR.glob("*.report.json"))) >= read_json(COHORT_LOCK)["sample_count"]:
        return
    if not JAR.is_file():
        raise SystemExit(f"missing PharmCAT jar: {JAR}")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["java", "-jar", str(JAR), "-vcf", str(combined), "-o", str(REPORT_DIR), "-reporterJson"],
        check=True, timeout=7200,
    )


def _single_sample_vcf(combined: Path, sample_id: str, target: Path) -> None:
    """Project one sample to PharmCAT positions without changing any genotype.

    The regional source slice contains every polymorphic row in broad gene spans.
    That is analytically useful upstream, but it exceeds the application's upload
    shape after sample extraction.  This is the repository-documented
    ``bcftools view -R`` preprocessing: irrelevant coordinates are removed while
    absent required coordinates remain absent (never filled as reference).
    """
    subprocess.run(
        ["bcftools", "view", "-R", str(POSITIONS), "-s", sample_id,
         "-Ov", "-o", str(target), str(combined)],
        check=True, capture_output=True,
    )


def evaluate(*, resume: bool) -> None:
    if not COHORT_LOCK.is_file():
        raise SystemExit("run prepare before evaluate")
    manifest = read_json(MANIFEST)
    # Bind every rerun to the production artifacts it actually exercises. The
    # compatibility manifest itself is excluded from this core hash to avoid a
    # self-referential digest; it subsequently binds this benchmark manifest.
    from compatible_bundle import application_core_hash

    manifest["local_production_artifact_sha256"] = application_core_hash()
    write_json(MANIFEST, manifest)
    if manifest["locks"].get("cohort") != "FROZEN":
        raise SystemExit("cohort is not frozen")
    if manifest["locks"].get("truth_actionability") != "FROZEN_UNAVAILABLE":
        raise SystemExit("truth actionability is not frozen")
    combined = REPO / manifest["genomic"].get("combined_path", "")
    if not combined.is_file() or sha256(combined) != manifest["genomic"].get("combined_sha256"):
        raise SystemExit("hashed genomic cohort slice missing or changed; run fetch")
    if sha256(TRUTH_TABLE) != read_json(COHORT_LOCK)["sample_gene_truth_sha256"]:
        raise SystemExit("frozen truth table changed")

    _run_pharmcat(combined, resume=resume)
    lock = read_json(COHORT_LOCK)
    cohort_ids = set(lock["sample_ids"])
    reports: dict[str, Path] = {}
    for path in REPORT_DIR.glob("*.report.json"):
        sample_id = _sample_id_from_report(path, cohort_ids)
        if sample_id:
            reports[sample_id] = path

    report_manifest = {
        "pharmcat_version": read_json(MANIFEST)["pharmcat_version"],
        "source_vcf_sha256": sha256(combined),
        "report_count": len(reports),
        "reports": [
            {
                "sample_id": sample_id,
                "local_cache_path": str(path.relative_to(REPO)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for sample_id, path in sorted(reports.items())
        ],
        "cache_note": (
            "Raw reports are reproducible local benchmark cache files and are excluded from Git; "
            "their identities are frozen here."
        ),
    }
    write_json(REPORT_MANIFEST, report_manifest)

    sys.path.insert(0, str(REPO / "backend"))
    from app import coverage as coverage_mod
    from app.main import build_result
    from app.pharmcat_runner import parse_report
    from app.vcf_validation import validate_vcf

    truth_rows = read_tsv(TRUTH_TABLE)
    truth_lookup = {(row["sample_id"], row["gene"]): row for row in truth_rows}
    exclusion_rows = read_tsv(EXCLUSIONS)
    eligibility_rows: list[dict] = []
    comparison_rows: list[dict] = []
    discrepancy_rows: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="pgx-benchmark-") as temp_name:
        temp = Path(temp_name)
        for index, sample_id in enumerate(lock["sample_ids"], 1):
            sample_vcf = temp / f"{sample_id}.vcf"
            _single_sample_vcf(combined, sample_id, sample_vcf)
            payload = sample_vcf.read_bytes()
            metadata = validate_vcf(payload, sample_vcf.name)
            cov = coverage_mod.assess(metadata.text)
            report_path = reports.get(sample_id)
            parsed = None
            raw_calls: dict[str, dict] = {}
            if report_path:
                raw = read_json(report_path)
                raw_calls = _raw_pharmcat_calls(raw)
                parsed = parse_report(raw, sample_hint=sample_id)

            drug_cache: dict[str, object] = {}
            for gene in ALL_GENES:
                truth = truth_lookup[(sample_id, gene)]
                gene_cov = cov.genes[gene]
                drug = GENE_TO_DRUG[gene]
                eligibility = coverage_mod.drug_eligibility(cov, drug)
                eligibility_rows.append({
                    "sample_id": sample_id,
                    "gene": gene,
                    "drug_context": drug,
                    "vcf_sha256": sha256(sample_vcf),
                    "positions_present": gene_cov.present,
                    "positions_required": gene_cov.required,
                    "coverage_percent": f"{gene_cov.percent:.1f}",
                    "decision_critical_present": gene_cov.critical_present,
                    "decision_critical_required": gene_cov.critical_required,
                    "gene_evidence_sufficient": str(gene_cov.sufficient).lower(),
                    "drug_eligible": str(eligibility.eligible).lower(),
                    "valid_dependency_genes": ",".join(eligibility.valid_genes),
                    "missing_dependency_genes": ",".join(eligibility.failed_genes),
                    "eligibility_reason": eligibility.reason,
                    "variants_only": str(cov.variants_only).lower(),
                    "input_validation": "accepted_single_sample_grch38",
                })

                upstream = raw_calls.get(gene, {})
                upstream_candidates = upstream.get("diplotypes", [])
                upstream_exact_asserted = len(upstream_candidates) == 1
                upstream_candidate_asserted = bool(upstream_candidates)
                upstream_exact = (
                    upstream_exact_asserted
                    and same_diplotype(truth["truth_raw"], upstream_candidates[0])
                ) if truth["truth_status"] == "evaluable" else False
                upstream_compatible = (
                    candidate_compatible(truth["truth_raw"], upstream_candidates)
                    if truth["truth_status"] == "evaluable" else False
                )

                final_result = None
                if parsed is not None:
                    if drug not in drug_cache:
                        drug_cache[drug] = build_result(drug, parsed, eligibility)[0]
                    final_result = drug_cache[drug]
                final_profile = final_result.pharmacogenomic_profile if final_result else None
                final_candidates = list(final_profile.candidate_diplotypes) if final_profile else []
                final_diplotype = final_profile.diplotype if final_profile else ""
                final_exact_asserted = bool(
                    final_profile
                    and final_profile.primary_gene == gene
                    and final_diplotype not in {"", "Unknown"}
                    and not final_diplotype.startswith("Undetermined")
                )
                final_candidate_asserted = bool(
                    final_profile and final_profile.primary_gene == gene and final_candidates
                )
                final_exact = (
                    final_exact_asserted and same_diplotype(truth["truth_raw"], final_diplotype)
                    if truth["truth_status"] == "evaluable" else False
                )
                final_compatible = (
                    candidate_compatible(truth["truth_raw"], final_candidates)
                    if truth["truth_status"] == "evaluable" else False
                )
                risk_label = final_result.risk_assessment.risk_label.value if final_result else "Unknown"
                comparison_rows.append({
                    "sample_id": sample_id,
                    "gene": gene,
                    "drug_context": drug,
                    "truth_status": truth["truth_status"],
                    "truth_raw": truth["truth_raw"],
                    "upstream_diplotypes": " | ".join(upstream_candidates),
                    "upstream_exact_asserted": upstream_exact_asserted,
                    "upstream_candidate_asserted": upstream_candidate_asserted,
                    "upstream_exact": upstream_exact,
                    "upstream_candidate_compatible": upstream_compatible,
                    "upstream_phenotypes": " | ".join(upstream.get("phenotypes", [])),
                    "application_drug_eligible": eligibility.eligible,
                    "application_profile_gene": final_profile.primary_gene if final_profile else "",
                    "application_diplotype": final_diplotype,
                    "application_candidate_diplotypes": " | ".join(final_candidates),
                    "application_exact_asserted": final_exact_asserted,
                    "application_candidate_asserted": final_candidate_asserted,
                    "application_exact": final_exact,
                    "application_candidate_compatible": final_compatible,
                    "application_risk_label": risk_label,
                    "application_abstained": risk_label == "Unknown",
                    "independent_phenotype_truth": "",
                    "truth_actionability": "unavailable",
                })
                if truth["truth_status"] == "evaluable" and not upstream_exact:
                    if not report_path:
                        category = "execution_or_parse_failure"
                    elif not upstream_candidates:
                        category = "upstream_caller_abstention"
                    elif upstream_compatible:
                        category = "upstream_candidate_ambiguity"
                    elif gene == "DPYD":
                        category = "truth_output_nomenclature_mismatch"
                    elif gene == "SLCO1B1" and ("*1A" in truth["truth_raw"] or "*1B" in truth["truth_raw"]):
                        category = "truth_output_nomenclature_or_definition_mismatch"
                    else:
                        category = "upstream_caller_disagreement"
                    discrepancy_rows.append({
                        "sample_id": sample_id,
                        "gene": gene,
                        "layer": "A_upstream",
                        "classification": category,
                        "truth": truth["truth_raw"],
                        "observed": " | ".join(upstream_candidates) or "no assertion",
                        "detail": "independent truth compared using frozen order-only equivalence",
                    })
                if truth["truth_status"] == "evaluable" and risk_label == "Unknown":
                    discrepancy_rows.append({
                        "sample_id": sample_id,
                        "gene": gene,
                        "layer": "B_application",
                        "classification": (
                            "intentional_cyp2d6_abstention" if gene == "CYP2D6"
                            else "evidence_gate" if not eligibility.eligible
                            else "application_mapping_or_upstream_abstention"
                        ),
                        "truth": truth["truth_raw"],
                        "observed": "Unknown",
                        "detail": eligibility.reason,
                    })
            print(f"evaluated {index}/{len(lock['sample_ids'])}: {sample_id}")

    write_tsv(
        ELIGIBILITY_TABLE,
        ["sample_id", "gene", "drug_context", "vcf_sha256", "positions_present",
         "positions_required", "coverage_percent", "decision_critical_present",
         "decision_critical_required", "gene_evidence_sufficient", "drug_eligible",
         "valid_dependency_genes", "missing_dependency_genes", "eligibility_reason",
         "variants_only", "input_validation"],
        eligibility_rows,
    )
    write_tsv(
        DISCREPANCIES,
        ["sample_id", "gene", "layer", "classification", "truth", "observed", "detail"],
        discrepancy_rows,
    )
    for sample_id in sorted(cohort_ids - set(reports)):
        exclusion_rows.append({
            "stage": "upstream", "sample_id": sample_id, "gene": "ALL",
            "reason": "pharmcat_execution_failure", "detail": "no PharmCAT report produced",
        })
    write_tsv(EXCLUSIONS, ["stage", "sample_id", "gene", "reason", "detail"], exclusion_rows)

    result = summarize(
        comparison_rows, eligibility_rows, discrepancy_rows, len(reports), len(cohort_ids)
    )
    write_json(RESULTS, result)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(result, manifest))
    manifest = read_json(MANIFEST)
    manifest["locks"]["performance_evaluated"] = True
    manifest["evaluated_at"] = utc_now()
    manifest["outputs"] = {
        str(path.relative_to(REPO)): {"sha256": sha256(path), "bytes": path.stat().st_size}
        for path in (
            TRUTH_TABLE, ELIGIBILITY_TABLE, EXCLUSIONS, DISCREPANCIES,
            REPORT_MANIFEST, RESULTS, REPORT,
        )
    }
    write_json(MANIFEST, manifest)


def summarize(
    rows: list[dict], eligibility_rows: list[dict], discrepancy_rows: list[dict],
    reports: int, cohort: int,
) -> dict:
    truth_status_counts = collections.Counter(row["truth_status"] for row in rows)
    per_gene: dict[str, dict] = {}
    for gene in ALL_GENES:
        evaluable = [row for row in rows if row["gene"] == gene and row["truth_status"] == "evaluable"]
        upstream_exact_assertions = [row for row in evaluable if row["upstream_exact_asserted"]]
        upstream_candidate_assertions = [row for row in evaluable if row["upstream_candidate_asserted"]]
        app_exact_assertions = [row for row in evaluable if row["application_exact_asserted"]]
        app_candidate_assertions = [row for row in evaluable if row["application_candidate_asserted"]]
        app_abstentions = [row for row in evaluable if row["application_abstained"]]
        eligible = [row for row in eligibility_rows if row["gene"] == gene and row["drug_eligible"] == "true"]
        discrepancy_counts = collections.Counter(
            row["classification"] for row in discrepancy_rows if row["gene"] == gene
        )
        per_gene[gene] = {
            "truth_evaluable": len(evaluable),
            "layer_A_upstream": {
                "exact_diplotype_concordance": proportion(sum(row["upstream_exact"] for row in evaluable), len(evaluable)),
                "candidate_compatible_concordance": proportion(sum(row["upstream_candidate_compatible"] for row in evaluable), len(evaluable)),
                "exact_assertion_coverage": proportion(len(upstream_exact_assertions), len(evaluable)),
                "candidate_set_assertion_coverage": proportion(len(upstream_candidate_assertions), len(evaluable)),
                "abstention": proportion(len(evaluable) - len(upstream_candidate_assertions), len(evaluable)),
                "conditional_exact_accuracy": proportion(
                    sum(row["upstream_exact"] for row in upstream_exact_assertions),
                    len(upstream_exact_assertions),
                ),
            },
            "layer_B_application": {
                "input_eligible": proportion(len(eligible), len([r for r in eligibility_rows if r["gene"] == gene])),
                "exact_diplotype_concordance": proportion(sum(row["application_exact"] for row in evaluable), len(evaluable)),
                "candidate_compatible_concordance": proportion(sum(row["application_candidate_compatible"] for row in evaluable), len(evaluable)),
                "exact_assertion_coverage": proportion(len(app_exact_assertions), len(evaluable)),
                "candidate_set_assertion_coverage": proportion(len(app_candidate_assertions), len(evaluable)),
                "abstention": proportion(len(app_abstentions), len(evaluable)),
                "conditional_exact_accuracy": proportion(
                    sum(row["application_exact"] for row in app_exact_assertions),
                    len(app_exact_assertions),
                ),
            },
            "discrepancy_classification": dict(sorted(discrepancy_counts.items())),
            "phenotype_concordance": {"numerator": None, "denominator": 0, "proportion": None, "confidence_interval": None},
            "false_reassurance": {"numerator": None, "denominator": 0, "proportion": None, "confidence_interval": None},
            "false_warning": {"numerator": None, "denominator": 0, "proportion": None, "confidence_interval": None},
            "not_estimable_reason": "independent source has no phenotype or drug-context actionability truth",
        }
    return {
        "benchmark_id": "pharmaguard-external-analytical-benchmark-v1",
        "generated_at": utc_now(),
        "cohort_samples": cohort,
        "sample_gene_truth_rows": len(rows),
        "truth_status_counts": dict(sorted(truth_status_counts.items())),
        "pharmcat_reports": reports,
        "genes": per_gene,
        "pooled_accuracy": None,
        "pooled_accuracy_reason": "predeclared protocol forbids a pooled marketing-style accuracy number",
        "clinical_utility_claim": False,
    }


def _fmt(metric: dict) -> str:
    if not metric["denominator"]:
        return "not estimable (0 denominator)"
    pct = 100 * metric["proportion"]
    interval = metric.get("confidence_interval")
    suffix = ""
    if interval:
        suffix = f"; 95% Wilson CI {100*interval['lower']:.1f}–{100*interval['upper']:.1f}%"
    return f"{metric['numerator']}/{metric['denominator']} ({pct:.1f}%{suffix})"


def render_report(result: dict, manifest: dict) -> str:
    lines = [
        "# Independent external analytical benchmark",
        "",
        "> Research/educational analytical evaluation only. This is not clinical validation,",
        "> clinical utility evidence, a calibrated patient-risk estimate, or prescribing authority.",
        "",
        "## Frozen sources and cohort",
        "",
        f"- Frozen protocol: `{manifest['protocol_sha256']}`.",
        f"- CDC GeT-RM truth: [{manifest['truth']['version']}]({manifest['truth']['url']}) (`{manifest['truth']['sha256']}`).",
        f"- Genomic evidence: [{manifest['genomic']['version']}]({BASE_URL}) (GRCh38, polymorphic-filtered VCF).",
        f"- 1000 Genomes sample manifest: `{manifest['genomic']['sample_manifest_sha256']}` ({manifest['genomic']['panel_sample_count_observed']} samples).",
        f"- Deterministic intersection: {result['cohort_samples']} individuals.",
        f"- Frozen sample × gene rows: {result['sample_gene_truth_rows']} (`{json.dumps(result['truth_status_counts'], sort_keys=True)}`).",
        f"- PharmCAT reports produced: {result['pharmcat_reports']}/{result['cohort_samples']}.",
        "- Raw report hashes are retained in `pharmcat_report_manifest.json`; bulky raw reports are a local rerunnable cache.",
        "- Missing positions were retained as absent; no omitted genotype was synthesized as reference.",
        "",
        "## Results by gene",
        "",
        "No pooled accuracy is reported. Each denominator is the number of unique individuals for that gene.",
        "",
    ]
    for gene, row in result["genes"].items():
        a = row["layer_A_upstream"]
        b = row["layer_B_application"]
        lines.extend([
            f"### {gene}",
            "",
            f"- Independent evaluable diplotypes: {row['truth_evaluable']}.",
            f"- Layer A exact concordance: {_fmt(a['exact_diplotype_concordance'])}.",
            f"- Layer A candidate-compatible concordance: {_fmt(a['candidate_compatible_concordance'])}.",
            f"- Layer A exact-assertion coverage: {_fmt(a['exact_assertion_coverage'])}.",
            f"- Layer A candidate-set assertion coverage: {_fmt(a['candidate_set_assertion_coverage'])}; abstention: {_fmt(a['abstention'])}.",
            f"- Layer A conditional exact accuracy: {_fmt(a['conditional_exact_accuracy'])}.",
            f"- Application input eligibility: {_fmt(b['input_eligible'])}.",
            f"- Layer B exact concordance: {_fmt(b['exact_diplotype_concordance'])}.",
            f"- Layer B exact-assertion coverage: {_fmt(b['exact_assertion_coverage'])}.",
            f"- Layer B candidate-set assertion coverage: {_fmt(b['candidate_set_assertion_coverage'])}; abstention: {_fmt(b['abstention'])}.",
            f"- Layer B conditional exact accuracy: {_fmt(b['conditional_exact_accuracy'])}.",
            f"- Discrepancy classifications: `{json.dumps(row['discrepancy_classification'], sort_keys=True)}`.",
            "- Phenotype concordance, false reassurance, and false warning: not estimable; the independent",
            "  source does not supply phenotype/drug-context truth, and no label was derived from the systems under test.",
            "",
        ])
    lines.extend([
        "## Nomenclature boundary",
        "",
        "The comparator was frozen to allele-order normalization only. It does not equate CDC legacy star",
        "labels with PharmCAT's current variant-component labels (especially DPYD), or collapse revised",
        "SLCO1B1 definitions. Therefore an exact mismatch can be a nomenclature/definition mismatch rather",
        "than a demonstrated biological genotype disagreement. The raw pairs and classifications remain in",
        "`discrepancies.tsv`; no post-result equivalence was introduced.",
        "",
        "## Interpretation and limitations",
        "",
        "The 1000 Genomes source is a polymorphic-filtered research VCF. Under the application's frozen",
        "evidence contract, coordinate omission is unknown rather than homozygous reference. Consequently,",
        "Layer B may correctly abstain even where Layer A makes a call. This benchmark therefore supports only",
        "bounded statements about diplotype agreement, input eligibility, assertion coverage, and abstention for",
        "this exact source combination. It does not establish assay validity, clinical benefit, individualized drug",
        "safety, or performance on complete all-sites VCFs.",
        "",
        "All exclusions and discrepancies are retained in the companion TSV files; negative findings were not",
        "removed or used to tune the application.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare", help="freeze deterministic cohort and independent truth")
    for name in ("fetch", "evaluate", "all"):
        child = sub.add_parser(name)
        child.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        prepare()
    elif args.command == "fetch":
        fetch(resume=args.resume)
    elif args.command == "evaluate":
        evaluate(resume=args.resume)
    else:
        prepare()
        fetch(resume=args.resume)
        evaluate(resume=args.resume)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
