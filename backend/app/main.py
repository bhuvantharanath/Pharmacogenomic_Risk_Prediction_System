"""
PharmaGuard — FastAPI entrypoint.

Run locally:
    uvicorn app.main:app --reload --port 8000

Pipeline:
    upload -> vcf_validation -> PharmCAT -> cpic_engine -> explanation
           -> AnalyzeResponse

The response schema has been byte-for-byte stable since Phase 1, so the Flutter
client has never needed a change to consume new capability.

Phase 4 added the controls a public URL needs: an explicit CORS allowlist, a
per-IP rate limit on /analyze, security headers, a startup assertion against
baked-in secrets, and a /ready endpoint separate from the cheap /health ping.

DATA RETENTION: none. An uploaded VCF lives in memory and in a per-request temp
directory that `pharmcat_runner` removes in a `finally` block. Nothing genomic
is written to durable storage, logged, or returned to any third party.
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import cpic_engine, security
from .explanation import ExplanationMode, generate_explanation
from .explanation import static_store as explanation_store
from .explanation.context import ExplanationContext
from .models import (
    AnalyzeResponse,
    ClinicalRecommendation,
    DetectedVariant,
    HealthResponse,
    PerDrugResult,
    PharmacogenomicProfile,
    Phenotype,
    QualityMetrics,
    RiskAssessment,
    RiskLabel,
)
from .retrieval import all_documents, retrieve_mechanism
from .pharmcat_models import PharmcatGeneCall, PharmcatReport
from .pharmcat_runner import (
    CYP2D6_WARNING,
    PharmcatExecutionError,
    pharmcat_available,
    run_pharmcat,
)
from .vcf_validation import (
    MAX_UPLOAD_BYTES,
    ReferenceBuild,
    VcfMetadata,
    VcfValidationError,
    validate_vcf,
)

MAX_DRUGS_PER_REQUEST = 25

@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Startup checks. Fails loudly if a credential was baked into the image.

    Runs before the first request. The deployed configuration needs no secrets
    at all, so anything found here is either a mistake or a leak — and on a
    public Space, whatever is in the image is public.
    """
    warnings = security.assert_no_baked_secrets(
        explanation_mode=ExplanationMode.from_env().value
    )
    for warning in warnings:
        print(f"[startup] WARNING: {warning}", flush=True)
    print(
        f"[startup] explanation_mode={ExplanationMode.from_env().value} "
        f"cors_origins={security.allowed_origins() or '(localhost only)'} "
        f"rate_limit={security.RATE_LIMIT_REQUESTS}/"
        f"{security.RATE_LIMIT_WINDOW_SECONDS}s",
        flush=True,
    )
    yield


app = FastAPI(
    title="PharmaGuard API",
    version="0.4.0",
    description=(
        "Pharmacogenomic risk prediction. Genotypes from PharmCAT, clinical "
        "guidance from CPIC (verbatim), explanations pre-generated and "
        "guard-checked. Research/educational use only; not a medical device."
    ),
    lifespan=lifespan,
)


# --------------------------------------------------------------------------- #
# CORS
#
# Phase 4 replaces the Phase 1-3 policy. That one allowed `*.pages.dev` by
# regex, which is fine on localhost and wrong on a public URL: it lets any
# Cloudflare Pages site — including one an attacker deploys in seconds — call
# this API from a visitor's browser. Production origins are now named
# explicitly via CORS_ALLOWED_ORIGINS.
# --------------------------------------------------------------------------- #
app.add_middleware(
    CORSMiddleware,
    allow_origins=security.allowed_origins(),
    allow_origin_regex=security.allowed_origin_regex(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(security.SecurityHeadersMiddleware)


class ApiError(HTTPException):
    """
    An HTTPException that also carries a machine-readable code.

    `detail` stays a plain human-readable string so existing clients (including
    the Phase 1 Flutter app, which reads `detail`) keep showing a useful message;
    `error_code` is added alongside for clients that want to branch on it.
    """

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.code = code


@app.exception_handler(ApiError)
async def _api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.code},
    )


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    """
    Liveness. Deliberately trivial — no PharmCAT, no disk, no subprocess.

    This is the wake-up ping. On a scale-to-zero free tier the first request
    after idle pays the whole container cold start, so this endpoint exists to
    absorb that cost cheaply: the Flutter client fires it on load, and the
    keepalive workflow polls it. Adding a dependency check here would make the
    cheap ping expensive and could make a waking container look unhealthy.

    Use `/ready` when you need to know whether an analysis would actually work.
    """
    return HealthResponse(status="ok")


@app.get("/ready", tags=["meta"])
async def ready() -> JSONResponse:
    """
    Readiness. Verifies the things `/analyze` actually depends on.

    Returns 200 when an analysis could succeed now, 503 otherwise, with a
    per-check breakdown so a failure says *which* dependency is missing rather
    than just "not ready".
    """
    checks: dict[str, object] = {}

    pharmcat_ok = pharmcat_available()
    checks["pharmcat"] = {
        "ok": pharmcat_ok,
        "detail": (
            f"'{os.environ.get('PHARMCAT_PIPELINE', 'pharmcat_pipeline')}' on PATH"
            if pharmcat_ok
            else "pipeline executable not found; /analyze will return 503"
        ),
    }

    corpus = len(all_documents())
    checks["mechanism_corpus"] = {
        "ok": corpus > 0,
        "detail": f"{corpus} mechanism document(s) loaded",
    }

    store = explanation_store.load_store()
    # A missing store is degraded, not broken: the template generator still
    # produces a complete explanation, so this must not fail readiness.
    checks["explanations"] = {
        "ok": True,
        "detail": (
            f"{len(store)} pre-generated ({len(store) - store.unreviewed_count} "
            f"reviewed)"
            if store.entries
            else f"none loaded — falling back to templates ({store.load_error})"
        ),
    }

    try:
        cpic_engine.load_mapping()
        checks["label_mapping"] = {"ok": True, "detail": "label_mapping.yaml parsed"}
    except Exception as exc:  # noqa: BLE001 — readiness must not raise
        checks["label_mapping"] = {"ok": False, "detail": str(exc)}

    ready_now = all(check["ok"] for check in checks.values())  # type: ignore[index]
    return JSONResponse(
        status_code=200 if ready_now else 503,
        content={
            "status": "ready" if ready_now else "not_ready",
            "checks": checks,
            "explanation_mode": ExplanationMode.from_env().value,
        },
    )


@app.get("/", tags=["meta"])
async def root() -> dict[str, object]:
    available = pharmcat_available()
    mode = ExplanationMode.from_env()
    store = explanation_store.load_store()
    return {
        "service": "PharmaGuard API",
        "phase": "3 (PharmCAT + CPIC label mapping + grounded explanations)",
        "docs": "/docs",
        "pharmcat_available": available,
        "explanation_mode": mode.value,
        "explanations_available": len(store),
        "explanations_reviewed": len(store) - store.unreviewed_count,
        "cors": security.cors_summary(),
        "rate_limit": {
            "requests": security.RATE_LIMIT_REQUESTS,
            "window_seconds": security.RATE_LIMIT_WINDOW_SECONDS,
        },
        "data_retention": "none — uploaded VCFs are deleted before the response",
        # Deployed default is API-free; say so plainly so a reviewer can check.
        "requires_api_key": mode is ExplanationMode.LIVE,
        # Deployment mistakes here are silent and catastrophic, so say it loudly.
        "pharmcat_note": (
            None
            if available
            else "PharmCAT is NOT installed; /analyze will return 503."
        ),
        "disclaimer": (
            "Research/educational decision support only. Not a medical device. "
            "Not for clinical use."
        ),
    }


def _parse_drugs(raw: str) -> list[str]:
    """Split the comma-separated `drugs` field into a clean, ordered, unique list."""
    seen: set[str] = set()
    drugs: list[str] = []
    for token in raw.split(","):
        name = token.strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        drugs.append(name)
    return drugs


# --------------------------------------------------------------------------- #
# Response assembly
# --------------------------------------------------------------------------- #


def _detected_variants(call: PharmcatGeneCall | None) -> list[DetectedVariant]:
    """
    The non-reference calls PharmCAT read for this gene.

    Only non-reference positions are reported: a called gene has every one of its
    definition positions present (300+ across our gene set), and listing them all
    would bury the handful that actually matter.

    `star_allele` is deliberately null. PharmCAT does not attribute a position to
    a single star allele — a position typically participates in several allele
    definitions — so naming one here would be an invention. The called diplotype
    is reported at the profile level instead.
    """
    if call is None:
        return []

    variants: list[DetectedVariant] = []
    for variant in call.variants:
        if not variant.call or not variant.referenceAllele:
            continue
        alleles = [a.strip() for a in variant.call.replace("|", "/").split("/")]
        if all(a == variant.referenceAllele for a in alleles):
            continue  # homozygous reference: nothing detected

        defines = ", ".join(variant.alleles) if variant.alleles else ""
        variants.append(
            DetectedVariant(
                rsid=variant.dbSnpId,
                gene=call.gene,
                genotype=variant.call,
                star_allele=None,
                function=(
                    f"Contributes to named allele(s): {defines}"
                    if defines
                    else "Position of interest; not part of a named allele definition"
                ),
            )
        )
    return variants


def _profile(call: PharmcatGeneCall | None, phenotype: Phenotype) -> PharmacogenomicProfile:
    if call is None:
        return PharmacogenomicProfile(
            primary_gene="Unknown",
            diplotype="Unknown",
            phenotype=Phenotype.UNKNOWN,
            activity_score=None,
            detected_variants=[],
        )
    return PharmacogenomicProfile(
        primary_gene=call.gene,
        diplotype=call.diplotype or "Unknown",
        phenotype=phenotype,
        activity_score=call.activity_score,
        detected_variants=_detected_variants(call),
    )


def _build_context(
    drug: str,
    call: PharmcatGeneCall | None,
    phenotype: Phenotype,
    assessment: RiskAssessment,
    recommendation: ClinicalRecommendation,
) -> ExplanationContext:
    """
    Assemble the closed set of facts the explanation layer may use.

    Whatever is not in here cannot legitimately appear in generated text — the
    faithfulness guard validates against exactly this object.
    """
    gene = call.gene if call else None

    # PharmCAT's implications text is folded into `cpic_recommendation` by the
    # CPIC engine; pass it through so the guard can ground quotes from it.
    implications = [recommendation.cpic_recommendation] if recommendation.cpic_recommendation else []

    return ExplanationContext(
        drug=drug.strip().lower(),
        risk_label=assessment.risk_label,
        phenotype=phenotype,
        gene=gene,
        diplotype=call.diplotype if call else None,
        activity_score=call.activity_score if call else None,
        detected_variants=_detected_variants(call),
        cpic_recommendation=recommendation.action,
        cpic_implications=implications,
        cpic_strength="",
        cpic_evidence_level=recommendation.cpic_evidence_level.value,
        mechanism=retrieve_mechanism(gene, drug),
        phenotype_label=(call.phenotype_raw or "") if call else "",
    )


def build_result(
    drug: str, report: PharmcatReport
) -> tuple[PerDrugResult, list[str], str]:
    """
    Map one drug through the engine and assemble its contract object.

    Returns (result, warnings, explanation_provenance). The provenance travels
    with the result rather than being recomputed by the caller — regenerating it
    would mean a second LLM call per drug in live mode.
    """
    assessment, recommendation, call, warnings = cpic_engine.evaluate(drug, report)
    phenotype = cpic_engine.map_phenotype(call.phenotype_raw if call else None)

    context = _build_context(drug, call, phenotype, assessment, recommendation)
    # Never raises: every mode degrades to the deterministic template.
    explained = generate_explanation(context)
    warnings.extend(explained.notes)

    return (
        PerDrugResult(
            drug=drug.strip().lower(),
            risk_assessment=assessment,
            pharmacogenomic_profile=_profile(call, phenotype),
            clinical_recommendation=recommendation,
            # to_contract() supplies the disclaimer, so it is populated on every
            # response regardless of which generator ran.
            llm_generated_explanation=explained.explanation.to_contract(),
        ),
        warnings,
        explained.provenance,
    )


def build_response(
    report: PharmcatReport,
    drugs: list[str],
    metadata: VcfMetadata,
    elapsed_ms: int,
) -> AnalyzeResponse:
    """Assemble the full contract response from a parsed PharmCAT report."""
    analyses: list[PerDrugResult] = []
    warnings: list[str] = list(metadata.warnings)
    provenances: list[str] = []

    for drug in drugs:
        result, drug_warnings, provenance = build_result(drug, report)
        analyses.append(result)
        warnings.extend(drug_warnings)
        provenances.append(provenance)

    # The CYP2D6 caveat is worth stating once even when no CYP2D6 drug was asked
    # about, because its absence from the results is otherwise invisible.
    cyp2d6 = report.gene("CYP2D6")
    if cyp2d6 and CYP2D6_WARNING not in warnings:
        warnings.extend(w for w in cyp2d6.warnings if w == CYP2D6_WARNING)

    # Make the explanation pipeline visible in the output: which mode ran, and
    # whether the faithfulness guard passed. Collapsed to the distinct values so
    # a 5-drug request does not emit 5 identical lines.
    for provenance in dict.fromkeys(provenances):
        warnings.append(provenance)

    store = explanation_store.load_store()
    if store.entries and store.unreviewed_count:
        warnings.append(
            f"{store.unreviewed_count} of {len(store)} pre-generated explanations "
            "have not yet been reviewed by the faculty guide. Clinical "
            "recommendations come from CPIC via PharmCAT and are unaffected."
        )

    unknown = [
        r.drug for r in analyses if r.risk_assessment.risk_label is RiskLabel.UNKNOWN
    ]
    if unknown:
        warnings.append(
            "No usable pharmacogenomic result for: " + ", ".join(unknown) + "."
        )

    detected = sum(
        len(r.pharmacogenomic_profile.detected_variants) for r in analyses
    )

    # Deduplicate while preserving order; the same gene warning is reachable
    # through several drugs.
    seen: set[str] = set()
    deduped = [w for w in warnings if not (w in seen or seen.add(w))]

    # The VCF's own sample column wins: PharmCAT titles its report after the
    # input *filename*, which is a temp name we chose, not the patient id.
    patient_id = (
        metadata.sample_ids[0]
        if metadata.sample_ids
        else (report.sample_id or "UNKNOWN")
    )

    return AnalyzeResponse(
        patient_id=patient_id,
        analyses=analyses,
        quality_metrics=QualityMetrics(
            vcf_parsing_success=True,
            variants_detected_count=detected,
            processing_time_ms=elapsed_ms,
            warnings=deduped,
        ),
    )


# --------------------------------------------------------------------------- #
# Endpoint
# --------------------------------------------------------------------------- #


@app.post("/analyze", response_model=AnalyzeResponse, tags=["analysis"])
async def analyze(
    request: Request,
    file: UploadFile = File(..., description="VCF upload (.vcf or .vcf.gz, GRCh38)"),
    drugs: str = Form(..., description='Comma-separated, e.g. "codeine,warfarin"'),
) -> AnalyzeResponse:
    """
    Analyse one VCF against a list of drugs.

    Validation failures return 400 with `detail` (human) and `error_code`
    (machine). An unrecognised *drug* is never an error — it comes back as a
    well-formed `Unknown` result.

    **No genomic data is retained.** The upload is held in memory, written to a
    per-request temp directory for PharmCAT, and that directory is removed in a
    `finally` block before this function returns. See `pharmcat_runner`.
    """
    started = time.perf_counter()

    # Rate limit before doing any work: /analyze spawns a JVM, so an unlimited
    # public endpoint would burn a free tier's whole compute budget.
    decision = security.limiter.check(security.client_key(request))
    if not decision.allowed:
        return security.rate_limit_response(decision)

    requested = _parse_drugs(drugs)
    if not requested:
        raise ApiError(
            422,
            "NO_DRUGS",
            "No drugs supplied. Provide a comma-separated list, e.g. 'codeine,warfarin'.",
        )
    if len(requested) > MAX_DRUGS_PER_REQUEST:
        raise ApiError(
            422,
            "TOO_MANY_DRUGS",
            f"Too many drugs ({len(requested)}); the limit is "
            f"{MAX_DRUGS_PER_REQUEST} per request.",
        )

    contents = await file.read()
    await file.close()

    # Cheap guard before the (more expensive) full validation.
    if len(contents) > MAX_UPLOAD_BYTES:
        raise ApiError(
            413,
            "FILE_TOO_LARGE",
            f"The file is {len(contents) / (1024 * 1024):.1f} MB, over the "
            f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
        )

    try:
        metadata = validate_vcf(contents, filename=file.filename or "upload.vcf")
    except VcfValidationError as exc:
        raise ApiError(400, exc.code.value, exc.message) from exc

    # A missing/ambiguous reference build is not fatal — validate_vcf has already
    # recorded a warning in metadata.warnings, which flows into quality_metrics.

    try:
        report = await run_pharmcat(
            metadata.text,
            sample_hint=metadata.sample_ids[0] if metadata.sample_ids else "sample",
        )
    except PharmcatExecutionError as exc:
        # 503, not 500: the request was fine, the server's analysis backend is not.
        raise ApiError(503, "PHARMCAT_UNAVAILABLE", exc.message) from exc

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return build_response(report, requested, metadata, elapsed_ms)
