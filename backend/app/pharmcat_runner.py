"""
PharmaGuard — running PharmCAT and parsing its output.

Two responsibilities, kept in one module because they are two halves of the same
seam: invoke the `pharmcat_pipeline` executable, and turn its `-reporterJson`
output into the typed models in `pharmcat_models.py`.

The parser half is importable and testable **without PharmCAT installed** — that
is why `parse_report()` takes a dict. The backend's test suite runs against
checked-in fixtures captured from a real PharmCAT 3.4.0 run.

Verified command (see infra/PHARMCAT_NOTES.md for how it was discovered):

    pharmcat_pipeline <input.vcf> -o <outdir> -reporterJson

OPERATIONAL HAZARD, learned the hard way: the pipeline's preprocessor **rewrites
the input directory** — it bgzips `input.vcf` into `input.vcf.bgz` and deletes
the original. Never point it at a caller-owned path. We copy the upload into a
private temp directory, which is also why cleanup is unconditional.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .pharmcat_models import (
    CallStatus,
    CpicAnnotation,
    CpicDrugGuideline,
    PharmcatGeneCall,
    PharmcatReport,
    PharmcatVariant,
)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Overridable so the same code runs in the Docker image, in CI, and on a laptop.
PHARMCAT_PIPELINE = os.environ.get("PHARMCAT_PIPELINE", "pharmcat_pipeline")

# PharmCAT on a free-tier CPU takes a few seconds for a PGx-sized VCF; 120s is
# a generous ceiling that still stops a wedged JVM from pinning a worker.
PHARMCAT_TIMEOUT_SECONDS = float(os.environ.get("PHARMCAT_TIMEOUT_SECONDS", "120"))

# The key under `drugs` holding CPIC content. PharmCAT also emits DPWG and FDA
# sections; PharmaGuard is CPIC-only by design, so we read just this one.
CPIC_SECTION = "CPIC Guideline Annotation"

# Genes PharmaGuard reports on. CYP2D6 is included deliberately so we can say
# "not callable" rather than stay silent about it.
TARGET_GENES: tuple[str, ...] = (
    "CYP2C19",
    "CYP2C9",
    "SLCO1B1",
    "TPMT",
    "NUDT15",
    "DPYD",
    "CYP2D6",
)

# PharmCAT cannot resolve CYP2D6 from an unphased VCF: the gene's star alleles
# depend on structural/copy-number variation that a VCF does not express. It
# signals this with callSource == "NONE" even when every CYP2D6 position is
# present (verified — see infra/PHARMCAT_NOTES.md).
CYP2D6_WARNING = (
    "CYP2D6 structural/copy-number variation cannot be resolved from unphased "
    "VCF; outside diplotype input planned"
)

# TODO(phase5): accept an external CYP2D6 diplotype from a caller (e.g. from
# Stargazer, Cyrius or a lab report) and pass it to PharmCAT via its outside-call
# file: `pharmcat_pipeline ... -po outside_calls.tsv`. That flag is already
# available in 3.4.0; we simply have no trustworthy source for the call yet.
# Do NOT enable `-research cyp2d6` for this: PharmCAT documents research mode as
# unvalidated, and a research-grade call rendered in a clinical-looking UI would
# be worse than an honest "Unknown".


class PharmcatExecutionError(RuntimeError):
    """PharmCAT could not be run, timed out, or produced no report."""

    def __init__(self, message: str, *, detail: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


@dataclass
class PharmcatInvocation:
    """What actually ran, for the audit trail."""

    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def pharmcat_available() -> bool:
    """True if the pipeline executable is on PATH (used by /health)."""
    return shutil.which(PHARMCAT_PIPELINE) is not None


# --------------------------------------------------------------------------- #
# Running
# --------------------------------------------------------------------------- #


async def run_pharmcat(vcf_text: str, *, sample_hint: str = "sample") -> PharmcatReport:
    """
    Run PharmCAT over `vcf_text` and return the parsed report.

    Async and subprocess-based: the JVM work happens in a child process, so the
    event loop is never blocked. Everything is confined to a private temp dir
    that is removed in a `finally`, regardless of outcome.
    """
    workdir = Path(tempfile.mkdtemp(prefix="pharmaguard_pharmcat_"))
    try:
        # Nested `in/` because the preprocessor mutates the input directory.
        input_dir = workdir / "in"
        output_dir = workdir / "out"
        input_dir.mkdir()
        output_dir.mkdir()

        # Base filename drives the output names, so keep it predictable.
        base = "sample"
        vcf_path = input_dir / f"{base}.vcf"
        vcf_path.write_text(vcf_text, encoding="utf-8")

        command = [
            PHARMCAT_PIPELINE,
            str(vcf_path),
            "-o",
            str(output_dir),
            "-reporterJson",
        ]
        invocation = await _exec(command)

        report_path = output_dir / f"{base}.report.json"
        if not report_path.is_file():
            # A non-zero exit with no report is the normal failure mode; surface
            # PharmCAT's own stderr because it is usually specific and useful.
            raise PharmcatExecutionError(
                "PharmCAT did not produce a report for this file.",
                detail=(invocation.stderr or invocation.stdout or "")[-2000:],
            )

        try:
            raw = json.loads(report_path.read_text())
        except json.JSONDecodeError as exc:
            raise PharmcatExecutionError(
                "PharmCAT produced a report that could not be parsed as JSON.",
                detail=str(exc),
            ) from exc

        return parse_report(raw, sample_hint=sample_hint)
    finally:
        # Unconditional: temp dirs holding patient-derived data must not linger.
        shutil.rmtree(workdir, ignore_errors=True)


async def _exec(command: list[str]) -> PharmcatInvocation:
    """Run `command`, enforcing the timeout and killing the process group."""
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise PharmcatExecutionError(
            f"PharmCAT is not installed on this server (could not find "
            f"'{PHARMCAT_PIPELINE}'). The API is running without a working "
            "analysis pipeline.",
            detail=str(exc),
        ) from exc

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=PHARMCAT_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError as exc:
        process.kill()
        # Reap it so we do not leave a zombie behind.
        await process.wait()
        raise PharmcatExecutionError(
            f"PharmCAT did not finish within {PHARMCAT_TIMEOUT_SECONDS:.0f} seconds "
            "and was stopped. Try a VCF restricted to pharmacogenomic positions.",
        ) from exc

    return PharmcatInvocation(
        command=command,
        returncode=process.returncode if process.returncode is not None else -1,
        stdout=stdout.decode("utf-8", errors="replace"),
        stderr=stderr.decode("utf-8", errors="replace"),
    )


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #


def _as_float(value: object) -> float | None:
    """PharmCAT writes activity scores as numbers, but also as "No Result"."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _message_texts(messages: object) -> list[str]:
    """PharmCAT messages are dicts; pull the human-readable part."""
    out: list[str] = []
    if not isinstance(messages, list):
        return out
    for message in messages:
        if isinstance(message, str):
            out.append(message)
        elif isinstance(message, dict):
            text = message.get("message") or message.get("name")
            if isinstance(text, str) and text.strip():
                out.append(text.strip())
    return out


def _parse_gene(symbol: str, block: dict) -> PharmcatGeneCall:
    """
    Normalise one `genes.<SYMBOL>` block.

    The status decision is the important part, because it is what
    `confidence_score` and the Unknown fallbacks hang off:

      callSource == "NONE"          -> NOT_ATTEMPTED (CYP2D6)
      no diplotype / "No Result"    -> NO_CALL
      more than one candidate       -> AMBIGUOUS
      exactly one                   -> DEFINITE
    """
    warnings = _message_texts(block.get("messages"))
    diplotypes = block.get("recommendationDiplotypes") or []

    labels = [
        d.get("label")
        for d in diplotypes
        if isinstance(d, dict) and isinstance(d.get("label"), str)
    ]
    primary = diplotypes[0] if diplotypes and isinstance(diplotypes[0], dict) else {}

    phenotypes = primary.get("phenotypes") or []
    phenotype_raw = phenotypes[0] if phenotypes else None
    label = primary.get("label")

    call_source = block.get("callSource")
    # PharmCAT's sentinel for "nothing to report" appears in both fields.
    uncalled = (
        not labels
        or label in (None, "Unknown/Unknown")
        or phenotype_raw in (None, "No Result")
    )

    if call_source == "NONE":
        status = CallStatus.NOT_ATTEMPTED
    elif uncalled:
        status = CallStatus.NO_CALL
    elif len(labels) > 1:
        status = CallStatus.AMBIGUOUS
    else:
        status = CallStatus.DEFINITE

    if symbol == "CYP2D6" and status is CallStatus.NOT_ATTEMPTED:
        warnings.append(CYP2D6_WARNING)
    elif status is CallStatus.NO_CALL:
        missing = block.get("uncalledHaplotypes") or []
        warnings.append(
            f"{symbol}: no diplotype could be called"
            + (
                f" ({len(missing)} haplotype definitions could not be ruled out; "
                "the VCF is probably missing required positions)"
                if missing
                else ""
            )
        )
    elif status is CallStatus.AMBIGUOUS:
        warnings.append(
            f"{symbol}: PharmCAT reported {len(labels)} equally likely diplotypes "
            f"({', '.join(labels[:4])}). Results use the first; confidence is "
            "reduced accordingly."
        )

    allele_functions = [
        allele.get("function")
        for key in ("allele1", "allele2")
        if isinstance(allele := primary.get(key), dict)
        and isinstance(allele.get("function"), str)
    ]

    variants = [
        PharmcatVariant.model_validate(v)
        for v in (block.get("variants") or [])
        if isinstance(v, dict)
    ]

    lookup_keys = [k for k in (primary.get("lookupKey") or []) if isinstance(k, str)]

    return PharmcatGeneCall(
        gene=symbol,
        status=status,
        diplotype=None if uncalled else label,
        candidate_diplotypes=[lbl for lbl in labels if lbl],
        phenotype_raw=phenotype_raw,
        activity_score=_as_float(primary.get("activityScore")),
        lookup_keys=lookup_keys,
        allele_functions=[f for f in allele_functions if f],
        variants=variants,
        warnings=warnings,
    )


def _parse_annotation(block: dict) -> CpicAnnotation:
    """Copy one CPIC recommendation row verbatim. No rewriting."""
    lookup_key: list[dict[str, str]] = []
    for entry in block.get("lookupKey") or []:
        if isinstance(entry, dict):
            lookup_key.append(
                {str(k): str(v) for k, v in entry.items() if isinstance(v, str)}
            )

    return CpicAnnotation(
        drug_recommendation=block.get("drugRecommendation"),
        implications=[i for i in (block.get("implications") or []) if isinstance(i, str)],
        classification=block.get("classification"),
        population=block.get("population"),
        dosing_information=bool(block.get("dosingInformation")),
        alternate_drug_available=bool(block.get("alternateDrugAvailable")),
        other_prescribing_guidance=bool(block.get("otherPrescribingGuidance")),
        lookup_key=lookup_key,
    )


def _parse_drug(name: str, block: dict) -> CpicDrugGuideline:
    guidelines = block.get("guidelines") or []
    first = guidelines[0] if guidelines and isinstance(guidelines[0], dict) else {}

    annotations: list[CpicAnnotation] = []
    genes: set[str] = set()
    for guideline in guidelines:
        if not isinstance(guideline, dict):
            continue
        for annotation in guideline.get("annotations") or []:
            if not isinstance(annotation, dict):
                continue
            parsed = _parse_annotation(annotation)
            annotations.append(parsed)
            for entry in parsed.lookup_key:
                genes.update(entry.keys())

    return CpicDrugGuideline(
        drug=name,
        guideline_name=first.get("name"),
        guideline_url=first.get("url"),
        annotations=annotations,
        genes=sorted(genes),
    )


def parse_report(raw: dict, *, sample_hint: str = "sample") -> PharmcatReport:
    """
    Parse a PharmCAT `-reporterJson` document.

    Pure and dependency-free so it can be tested against a checked-in fixture.
    Unknown or missing sections degrade to empty rather than raising: a partial
    report is still worth showing, and a hard failure here would turn a usable
    result into a 500.
    """
    genes_raw = raw.get("genes")
    genes: dict[str, PharmcatGeneCall] = {}
    if isinstance(genes_raw, dict):
        for symbol in TARGET_GENES:
            block = genes_raw.get(symbol)
            if isinstance(block, dict):
                genes[symbol] = _parse_gene(symbol, block)

    drugs: dict[str, CpicDrugGuideline] = {}
    drugs_raw = raw.get("drugs")
    if isinstance(drugs_raw, dict):
        cpic = drugs_raw.get(CPIC_SECTION)
        if isinstance(cpic, dict):
            for name, block in cpic.items():
                if isinstance(block, dict):
                    drugs[name.strip().lower()] = _parse_drug(name, block)

    return PharmcatReport(
        pharmcat_version=str(raw.get("pharmcatVersion") or "unknown"),
        data_version=raw.get("dataVersion"),
        timestamp=raw.get("timestamp"),
        # PharmCAT titles the report with the sample id.
        sample_id=raw.get("title") or sample_hint,
        genes=genes,
        drugs=drugs,
        warnings=_message_texts(raw.get("messages")),
    )
