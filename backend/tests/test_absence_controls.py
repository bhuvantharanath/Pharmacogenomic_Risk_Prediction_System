"""
Positive controls for every check whose answer can be "it is not there".

WHY

Tally #17: a check asked "is rs1799853 present in the slice?", ran
`bcftools query -r` against an unindexed VCF, and got nothing back. bcftools
refused, said so on stderr, and **exited 255** — but the call passed no
`check=True`, never read `returncode`, and turned empty stdout into an empty
set. Every position then tested as absent. It was believed because only the
expected answer was inspected.

An absence check has a failure mode no presence check has: **when it breaks, it
breaks toward "absent"**, which is indistinguishable from working correctly on
data that genuinely lacks the thing. A presence check that breaks returns
nothing and is noticed immediately.

So each check below is paired with a POSITIVE CONTROL — something known to be
present, asserted to report present. If the control fails, the check is broken
and its absences mean nothing. The control is the part that distinguishes "I
looked and it was not there" from "I did not look".

SCOPE

Not all 210 absence-shaped expressions in the codebase — most are local guards
whose failure is immediately visible. These are the ones whose result becomes a
**reported finding or a gate decision**: where "nothing found" is the conclusion
rather than a step toward one.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
JAR = REPO / "test-data/reference/tools/pharmcat-3.4.0-all.jar"

from app import coverage as coverage_mod
from app import vcf_validation


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# 1. Coverage — "which required positions are missing"
# --------------------------------------------------------------------------- #

def test_coverage_control_a_complete_file_reports_positions_PRESENT() -> None:
    """
    THE CONTROL FOR THE WHOLE GATE. `assess` reports missing positions, and a
    broken parser would report every position missing — which looks exactly
    like a thin file, which is the thing the gate exists to detect. Without
    this, "0 of 35 present" is unfalsifiable.
    """
    complete = REPO / "test-data/demo/demo_confident.vcf"
    result = coverage_mod.assess(complete.read_text())

    assert result.genes, "no genes assessed at all — the parser found nothing"
    for gene, c in result.genes.items():
        assert c.required > 0, f"{gene} claims zero required positions"
    # This file is complete-coverage by construction; at least one gene must
    # reach 100%, or the position matching is broken rather than the input thin.
    assert any(c.present == c.required for c in result.genes.values()), (
        "not one gene reached full coverage on a file built to have it — the "
        "position matcher is finding nothing, not the file lacking anything")


def test_coverage_control_a_thin_file_still_reports_SOME_present() -> None:
    """
    The negative case, bounded. A variants-only file is thin, but not empty —
    if it reported literally zero positions everywhere, that would be the
    parser failing rather than the file being sparse.
    """
    thin = REPO / "test-data/demo/demo_variants_only.vcf"
    result = coverage_mod.assess(thin.read_text())
    assert any(c.present > 0 for c in result.genes.values()), (
        "every gene reported zero present positions — indistinguishable from "
        "a parser that read nothing")


def test_required_position_table_is_not_empty() -> None:
    """
    Everything downstream divides by these counts. An empty table would make
    every file look fully covered (0 of 0) or fully uncovered, depending on the
    arithmetic — and neither would raise.
    """
    path = REPO / "backend/app/data/position_requirements.json"
    data = json.loads(path.read_text())["genes"]
    genes = {k: v for k, v in data.items() if isinstance(v, dict)}
    assert len(genes) >= 7, f"only {len(genes)} genes have requirements"
    for gene, spec in genes.items():
        assert spec.get("positions"), f"{gene} has an empty position list"


def test_decision_critical_positions_are_not_empty_where_enforced() -> None:
    """`critical_required == 0` would make the identity requirement vacuous."""
    path = REPO / "backend/app/data/position_requirements.json"
    data = json.loads(path.read_text())["genes"]
    enforced = [g for g, v in data.items()
                if isinstance(v, dict) and v.get("decision_critical_enforced")]
    assert enforced, "no gene enforces decision-critical positions any more"
    for gene in enforced:
        assert data[gene]["decision_critical_count"] > 0, (
            f"{gene} enforces identity over an EMPTY critical set — every "
            f"input would satisfy it")


# --------------------------------------------------------------------------- #
# 2. VCF validation — "no species declared", "no build evidence"
# --------------------------------------------------------------------------- #

def test_species_control_a_declared_species_IS_detected() -> None:
    """
    `detect_species` returning None means "the file declares no species", which
    is treated as acceptable. A broken detector returns None for everything,
    silently accepting a mouse genome.
    """
    mouse = [
        "##fileformat=VCFv4.2",
        '##contig=<ID=chr10,assembly=GRCm39,species="Mus musculus">',
    ]
    assert vcf_validation.detect_species(mouse) == "Mus musculus", (
        "a file that plainly declares its species reports none — the detector "
        "is broken, and every absence it reports is meaningless")


def test_build_control_a_known_accession_IS_resolved() -> None:
    """`detect_build_from_accessions` returning None must mean no evidence."""
    header = ["##contig=<ID=chr1,length=248956422,assembly=GRCh38>",
              "##reference=GRCh38"]
    accession = ["##contig=<ID=NC_000001.11,length=248956422>"]
    resolved = vcf_validation.detect_build_from_accessions(accession)
    assert resolved is not None, (
        "NC_000001.11 is GRCh38 in PharmCAT's own mapping and resolved to "
        "nothing — the accession table is empty or unreadable")
    assert "38" in resolved


def test_build_evidence_table_is_populated() -> None:
    data = json.loads(
        (REPO / "backend/app/data/build_evidence.json").read_text())
    mapping = data.get("accession_to_build", {})
    assert len(mapping) > 50, (
        f"only {len(mapping)} accessions known — an empty-ish table makes "
        f"every file 'no build evidence'")


# --------------------------------------------------------------------------- #
# 3. PharmCAT resolution — "no jar found"
# --------------------------------------------------------------------------- #

def test_jar_control_the_jar_this_repo_ships_IS_found() -> None:
    """
    `find_jar()` returning None means "PharmCAT is not installed", which makes
    /analyze return 503 for everything. A broken search reports the same.
    """
    from app import pharmcat_runner
    if not JAR.is_file():
        pytest.skip("reference jar not fetched")
    import os
    old = os.environ.get("PHARMCAT_JAR")
    os.environ["PHARMCAT_JAR"] = str(JAR)
    try:
        assert pharmcat_runner.find_jar() is not None, (
            "the jar was pointed at explicitly and still not found")
    finally:
        if old is None:
            os.environ.pop("PHARMCAT_JAR", None)
        else:
            os.environ["PHARMCAT_JAR"] = old


# --------------------------------------------------------------------------- #
# 4. Definition lookups — "this allele has no defining positions"
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(not JAR.is_file(), reason="reference jar not fetched")
def test_defining_positions_control_a_known_allele_HAS_them() -> None:
    """
    The filter that classifies deviations as input artifacts asks "are this
    allele's defining positions present?". If the definition loader returned
    nothing, every allele would have zero required positions, zero missing, and
    would sail through the coverage filter as though fully observed.
    """
    module = _load("filter_frequency_deviations",
                   REPO / "scripts/filter_frequency_deviations.py")
    defs = module.defining_positions("CYP2C9")
    assert defs, "no alleles loaded for CYP2C9"
    star2 = defs.get("*2")
    assert star2, "*2 has no defining positions — the loader read nothing"
    rsids = {r for _, _, r in star2}
    assert "rs1799853" in rsids, (
        "CYP2C9 *2 is defined by rs1799853; the loader did not report it")


@pytest.mark.skipif(not (REPO / "test-data/reference/cohort/cohort_n601.vcf").is_file(),
                    reason="SAS slice not present (gitignored, regenerable)")
def test_sliced_positions_control_a_position_KNOWN_present_reports_present() -> None:
    """
    THE EXACT CHECK THAT FAILED. rs1799853 at chr10:94942290 is in the slice.
    Any reader that reports it absent is broken — that is tally #17, and this
    is the control that would have caught it in one line.
    """
    module = _load("filter_frequency_deviations",
                   REPO / "scripts/filter_frequency_deviations.py")
    present = module.sliced_positions()
    assert len(present) > 1000, (
        f"only {len(present)} positions parsed — an empty or tiny set makes "
        f"every allele an 'input artifact'")
    assert ("chr10", 94942290) in present, (
        "chr10:94942290 (rs1799853) IS in the slice and was reported absent — "
        "this is the failure recorded as tally #17")


@pytest.mark.skipif(not (REPO / "test-data/reference/cohort/cohort_n601.vcf").is_file(),
                    reason="SAS slice not present")
def test_sliced_positions_are_matched_per_chromosome() -> None:
    """
    A bare POS is not an identity. Pooling across contigs let a coordinate on
    one chromosome satisfy a lookup for another.
    """
    module = _load("filter_frequency_deviations",
                   REPO / "scripts/filter_frequency_deviations.py")
    present = module.sliced_positions()
    assert all(isinstance(k, tuple) and len(k) == 2 for k in list(present)[:20]), (
        "positions are not (chromosome, position) pairs")
    chroms = {c for c, _ in present}
    assert len(chroms) > 1, "only one chromosome parsed from a 7-gene slice"


# --------------------------------------------------------------------------- #
# 5. The subprocess hazard itself
# --------------------------------------------------------------------------- #

def test_bcftools_DOES_signal_refusal_through_its_exit_code() -> None:
    """
    THE SECOND CORRECTION. The write-up of #17 first claimed bcftools "exits 0
    while refusing". It does not — it exits **255**, and says why on stderr.

    That claim came from `bcftools ... | head -5; echo $?`, where `$?` reports
    HEAD's status, not bcftools'. Measuring the exit code through a pipe
    measured the wrong process.

    So #17 was not a tool lying. It was simpler: the call passed no
    `check=True`, never looked at `returncode`, and turned empty stdout into an
    empty set. The tool said no, at normal volume, and nobody was listening.

    Pinned here because the correct lesson — CHECK THE EXIT CODE — is different
    from, and easier than, the one first written down.
    """
    slice_path = REPO / "test-data/reference/cohort/cohort_n601.vcf"
    if not slice_path.is_file():
        pytest.skip("SAS slice not present")

    result = subprocess.run(
        ["bcftools", "query", "-f", "%POS\n", "-r", "chr10", str(slice_path)],
        capture_output=True, text=True)

    assert result.returncode != 0, (
        "bcftools accepted an unindexed region query, or now fails silently — "
        "either way the reasoning behind the linear-scan reader has changed")
    assert result.stdout.strip() == "", "refused but still returned rows"
    assert "bgzip" in result.stderr or "index" in result.stderr.lower(), (
        f"refusal message changed: {result.stderr[:200]}")


def test_no_absence_check_trusts_an_empty_subprocess_result() -> None:
    """
    Structural guard. `sliced_positions` raises rather than returning an empty
    set, because an empty set answers "no" to every membership question.
    """
    source = (REPO / "scripts/filter_frequency_deviations.py").read_text()
    assert "if not out:" in source and "refusing to" in source, (
        "sliced_positions no longer refuses an empty result — an empty "
        "position set silently classifies every allele as an input artifact")
