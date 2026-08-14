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

import json
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import coverage as coverage_mod
from . import cpic_engine, security
from .explanation import ExplanationMode, generate_explanation
from .explanation import static_store as explanation_store
from .explanation.context import ExplanationContext
from .models import (
    AnalyzeResponse,
    ClinicalRecommendation,
    CoverageResponse,
    DetectedVariant,
    GeneReadiness,
    GuidelineProvenance,
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
    MAX_CONCURRENT_PHARMCAT,
    PHARMCAT_QUEUE_TIMEOUT_SECONDS,
    PINNED_VERSION,
    PharmcatBusyError,
    PharmcatExecutionError,
    pharmcat_available,
    resolve_invoker,
    run_pharmcat,
    unavailable_reason,
)
from .vcf_validation import (
    MAX_UPLOAD_BYTES,
    ReferenceBuild,
    VcfMetadata,
    VcfValidationError,
    validate_vcf,
)

MAX_DRUGS_PER_REQUEST = 25


def _resolved_base_url() -> str:
    """
    Where this process is reachable, for the startup banner.

    Reads PORT/HOST like a deployed instance does. An earlier version parsed
    `--port` out of argv specifically to avoid setting PORT, because PORT is one
    of the markers `assert_cors_configured` uses to detect a hosted instance —
    but that made local startup take a different code path from production,
    which is exactly where a CORS misconfiguration must be caught. The fix is to
    configure CORS locally (see .env.example), not to hide the marker.
    """
    port = os.environ.get("PORT") or os.environ.get("UVICORN_PORT") or "8000"
    host = os.environ.get("HOST") or os.environ.get("UVICORN_HOST") or "127.0.0.1"
    if host in {"0.0.0.0", "::", "*"}:
        host = "127.0.0.1"
    return f"http://{host}:{port}"


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

    # Raises CorsMisconfiguredError if this looks like a hosted instance with an
    # empty allowlist. Deliberately fatal: that misconfiguration passes every
    # health check while blocking every real browser request, so it would
    # otherwise be discovered by a visitor rather than by the deployer.
    security.assert_cors_configured()

    # PharmCAT reachability, checked at startup rather than at first request.
    #
    # Previously the only signal was a 503 PHARMCAT_UNAVAILABLE when a user
    # uploaded a VCF — so a deploy with a missing jar looked completely healthy
    # until someone tried to use it, and the error named the wrapper rather than
    # the fix. Whether this is fatal is a deployment decision, not ours to force:
    # STRICT_PHARMCAT=1 refuses to start, the default starts and says loudly what
    # is wrong. /ready already reports the same state for orchestrators.
    invoker = resolve_invoker()
    if invoker is None:
        reason = unavailable_reason()
        message = (
            f"PharmCAT cannot be invoked, so /analyze will return 503 for every "
            f"request. {reason}"
        )
        if os.environ.get("STRICT_PHARMCAT", "").strip().lower() in {"1", "true", "yes"}:
            raise RuntimeError(f"[startup] FATAL: {message}")
        print(f"[startup] WARNING: {message}", flush=True)
    else:
        print(
            f"[startup] pharmcat={invoker.kind} via {invoker.describe}",
            flush=True,
        )

    # The concurrency gate only works in ONE process.
    #
    # `asyncio.Semaphore` lives in a single interpreter's memory. Run uvicorn
    # with --workers 4 and you get four independent semaphores, each cheerfully
    # allowing one JVM, so the instance runs four — which is exactly the state
    # the gate exists to prevent, now with the added charm of looking correct in
    # the source. There is no shared-memory fallback here on purpose: the fix is
    # one worker, and a cross-process lock would invite someone to raise the
    # worker count and trust it.
    _assert_single_worker()

    # The resolved base URL, printed once. A presenter needs to know which port
    # actually bound — guessing wrong mid-demo looks like the backend is down.
    #
    # Read from the command line first, NOT from PORT. Setting PORT is one of the
    # markers `assert_cors_configured` uses to decide an instance looks hosted, so
    # exporting it to make this line accurate would refuse to start with an empty
    # CORS allowlist. Found that the hard way; the argv path avoids it entirely.
    print(f"[startup] listening on {_resolved_base_url()}  (docs at /docs)", flush=True)

    print(
        f"[startup] explanation_mode={ExplanationMode.from_env().value} "
        f"cors_origins={security.allowed_origins() or '(localhost only)'} "
        f"rate_limit={security.RATE_LIMIT_REQUESTS}/"
        f"{security.RATE_LIMIT_WINDOW_SECONDS}s",
        flush=True,
    )
    yield


def _app_metadata() -> dict[str, str]:
    """
    Title and blurb for the OpenAPI page.

    Kept in its own function because /docs is an API reference read by a
    developer, not the product's voice. The glossary audit excludes it by name
    (see `OPERATOR_ONLY` in scripts/glossary_lib.py) — the boundary is a real
    one, so it is drawn in the code rather than asserted in a comment.
    """
    return {
        "title": "PharmaGuard API",
        "description": (
            "Pharmacogenomic risk prediction. Genotypes from PharmCAT, clinical "
            "guidance from CPIC (verbatim), explanations pre-generated and "
            "guard-checked. Research/educational use only; not a medical device."
        ),
    }


app = FastAPI(
    **_app_metadata(),
    version="0.4.0",
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


#: How the running build identifies itself.
#:
#: `RENDER_GIT_COMMIT` is set automatically by Render at runtime (verified
#: against render.com/docs/environment-variables, 2026-08-13). `GIT_COMMIT` is
#: the generic fallback so the same code reports a real SHA under Docker
#: Compose or any other host that passes one.
#:
#: WHY THIS IS EXPOSED AT ALL. The frontend and backend deploy through
#: different systems — Pages via GitHub Actions, Render via an API call — and
#: for one release they drifted silently, because `autoDeploy` reports enabled
#: while doing nothing. A version the client can read is what turns "the site
#: behaves oddly" into "these two halves are three commits apart".
def build_commit() -> str:
    for var in ("RENDER_GIT_COMMIT", "GIT_COMMIT", "SOURCE_COMMIT"):
        value = os.environ.get(var, "").strip()
        if value:
            return value
    return "unknown"


def _configured_workers() -> int | None:
    """
    How many workers uvicorn was told to run, or None if it cannot be told.

    Read from argv and the environment rather than from uvicorn internals: the
    server object is not reachable from an app-level startup hook, and guessing
    at a private attribute would break silently on an upgrade — which for a
    safety check is worse than not checking.
    """
    for source, flag in ((sys.argv, "--workers"), (sys.argv, "-w")):
        if flag in source:
            index = source.index(flag)
            if index + 1 < len(source):
                try:
                    return int(source[index + 1])
                except ValueError:
                    return None
    for arg in sys.argv:
        if arg.startswith("--workers="):
            try:
                return int(arg.split("=", 1)[1])
            except ValueError:
                return None
    for var in ("WEB_CONCURRENCY", "UVICORN_WORKERS", "GUNICORN_WORKERS"):
        raw = os.environ.get(var, "").strip()
        if raw:
            try:
                return int(raw)
            except ValueError:
                return None
    return None


def _assert_single_worker() -> None:
    """
    Refuse to serve with a worker count that defeats the concurrency gate.

    Fatal rather than a warning. The failure it prevents is an OOM kill of the
    whole container under concurrent load — silent, total, and attributed to the
    host rather than to the configuration that caused it. A warning printed once
    at startup would scroll past and be discovered by whoever is presenting.
    """
    workers = _configured_workers()
    if workers is not None and workers > 1:
        raise RuntimeError(
            f"[startup] FATAL: {workers} workers requested, but the PharmCAT "
            f"concurrency gate (MAX_CONCURRENT_PHARMCAT="
            f"{MAX_CONCURRENT_PHARMCAT}) is an asyncio.Semaphore and is "
            f"PER PROCESS. {workers} workers would allow "
            f"{workers * MAX_CONCURRENT_PHARMCAT} concurrent JVMs; two "
            f"measured 594 MB against a 512 MB instance "
            f"(reports/memory_measurement.md). Run with --workers 1, or raise "
            f"the instance size and set MAX_CONCURRENT_PHARMCAT deliberately."
        )
    print(
        f"[startup] pharmcat_concurrency={MAX_CONCURRENT_PHARMCAT} "
        f"workers={workers if workers is not None else 1} "
        f"queue_timeout={PHARMCAT_QUEUE_TIMEOUT_SECONDS:.0f}s",
        flush=True,
    )


class ApiError(HTTPException):
    """
    An HTTPException that also carries a machine-readable code.

    `detail` stays a plain human-readable string so existing clients (including
    the Phase 1 Flutter app, which reads `detail`) keep showing a useful message;
    `error_code` is added alongside for clients that want to branch on it.
    """

    def __init__(self, status_code: int, code: str, message: str,
                 headers: dict[str, str] | None = None) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        #: `Retry-After` for the busy case. A client told to wait needs to know
        #: how long, and guessing produces either a stampede or a needless delay.
        self.extra_headers = headers or {}


@app.exception_handler(ApiError)
async def _api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.code},
        headers=exc.extra_headers or None,
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

    # Reports HOW PharmCAT will be invoked, not merely whether. The previous
    # message named only the wrapper, which is misleading now that the jar is the
    # primary path — and on failure it said what was missing without saying what
    # to do about it.
    invoker = resolve_invoker()
    checks["pharmcat"] = {
        "ok": invoker is not None,
        "detail": (
            f"{invoker.kind}: {invoker.describe}"
            if invoker is not None
            else f"{unavailable_reason()}; /analyze will return 503"
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
            f"{len(store)} pre-generated "
            f"({len(store) - store.unverified_count} provenance-verified)"
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
    commit = build_commit()
    return JSONResponse(
        status_code=200 if ready_now else 503,
        content={
            "status": "ready" if ready_now else "not_ready",
            "checks": checks,
            "explanation_mode": ExplanationMode.from_env().value,
            # NOT a check — an unknown or mismatched commit does not make the
            # service unready, and gating readiness on it would take a working
            # backend offline over a label. It is reported so the client can
            # say the two halves disagree, and let the user carry on.
            "build": {
                "commit": commit,
                "commit_short": commit[:7] if commit != "unknown" else "unknown",
            },
        },
    )


@app.get("/provenance", response_model=GuidelineProvenance, tags=["meta"])
async def provenance() -> GuidelineProvenance:
    """
    When the guidance this build ships was captured.

    A GET because the About screen must be able to state it without an analysis
    having been run — the version behind an answer is not a property of the
    upload. Reports the pinned PharmCAT release; the data-bundle stamp comes
    from a real run and so is only present on /analyze.
    """
    return guideline_provenance()


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
        "explanations_provenance_verified": len(store) - store.unverified_count,
        "clinical_expert_review": "NOT_OBTAINED",
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
    ambiguous = list(call.candidate_diplotypes or [])
    if len(ambiguous) < 2:
        ambiguous = []
    return PharmacogenomicProfile(
        primary_gene=call.gene,
        # An ambiguous call gets a marker, not one of the candidates. The
        # phenotype may still be asserted (every candidate agreed on function);
        # the exact star alleles are simply not determined, and saying otherwise
        # is the over-claiming this whole layer exists to prevent.
        diplotype=(
            f"Undetermined ({len(ambiguous)} equally likely)"
            if ambiguous
            else (call.diplotype or "Unknown")
        ),
        candidate_diplotypes=ambiguous,
        # Only surfaced when it actually differs — repeating the same string under
        # two names would invite exactly the conflation the field exists to expose.
        recommendation_diplotype=(
            call.recommendation_diplotype
            if call.recommendation_diplotype
            and call.recommendation_diplotype != call.diplotype
            else None
        ),
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
        candidate_diplotypes=list(call.candidate_diplotypes) if call else [],
    )


def build_result(
    drug: str,
    report: PharmcatReport,
    starved_genes: set[str] | None = None,
) -> tuple[PerDrugResult, list[str], str]:
    """
    Map one drug through the engine and assemble its contract object.

    Returns (result, warnings, explanation_provenance). The provenance travels
    with the result rather than being recomputed by the caller — regenerating it
    would mean a second LLM call per drug in live mode.
    """
    assessment, recommendation, call, warnings = cpic_engine.evaluate(drug, report)
    phenotype = cpic_engine.map_phenotype(call.phenotype_raw if call else None)

    # Coverage-starved gene: demote to Unknown. The per-gene reason is already in
    # quality_metrics.warnings; repeating it per drug would spam a 6-drug request.
    if starved_genes and call is not None and call.gene in starved_genes:
        phenotype = Phenotype.UNKNOWN
        assessment = RiskAssessment(
            risk_label=RiskLabel.UNKNOWN,
            confidence_score=0.0,
            severity=assessment.severity.__class__.NONE,
        )
        recommendation = cpic_engine.build_clinical_recommendation(
            None,
            report.drug(drug.strip().lower()),
            fallback_reason=(
                f"The uploaded VCF does not cover enough of {call.gene}'s required "
                f"positions to support a confident call, so no recommendation is "
                f"made for {drug}."
            ),
        )

    # Build the profile FIRST so it can be handed to the explanation layer.
    # This is the object the client renders in the card, and it is what every
    # value injected into the explanation gets cross-checked against — so the
    # sentence and the card above it cannot disagree.
    profile = _profile(call, phenotype)

    context = _build_context(drug, call, phenotype, assessment, recommendation)
    # Never raises: every mode degrades to the deterministic template.
    explained = generate_explanation(context, profile=profile)
    warnings.extend(explained.notes)

    return (
        PerDrugResult(
            drug=drug.strip().lower(),
            risk_assessment=assessment,
            pharmacogenomic_profile=profile,
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
    cov: "coverage_mod.CoverageReport | None" = None,
) -> AnalyzeResponse:
    """Assemble the full contract response from a parsed PharmCAT report."""
    analyses: list[PerDrugResult] = []
    warnings: list[str] = list(metadata.warnings)
    provenances: list[str] = []

    # THE COVERAGE GATE. Genes whose input coverage is below the measured minimum
    # cannot support a confident phenotype, so they are suppressed BEFORE the label
    # engine sees them. This is the only check that can catch a confidently-wrong
    # call, because the wrongness is in the input, not the output.
    starved: set[str] = set()
    if cov is not None:
        if cov.variants_only:
            warnings.append(coverage_mod.variants_only_warning())
        insufficient = cov.insufficient()
        # EVERY gene declined is one diagnosis, not seven. Repeating a generic
        # coverage message per gene buries the useful part — that this is a
        # property of the file, and which kinds of file behave this way. It is
        # also the most likely first experience for a visitor who downloads a
        # public research VCF or a consumer SNP export.
        all_gated = bool(cov.genes) and len(insufficient) == len(cov.genes)
        if all_gated:
            warnings.append(coverage_mod.all_genes_gated_warning(cov))

        for gene_cov in insufficient:
            starved.add(gene_cov.gene)
            # Two different refusals, two different sentences. A gene that met
            # its percentage but lacks the positions that could show a variant
            # needs the second one, or "37% was enough and you refused anyway"
            # reads as a bug rather than as the point.
            if (gene_cov.percent >= gene_cov.min_percent
                    and gene_cov.critical_enforced
                    and not gene_cov.critical_satisfied):
                # Kept even when everything is gated: this one says something
                # the summary does not, and it is the project's sharpest point.
                warnings.append(coverage_mod.critical_positions_warning(gene_cov))
            elif not all_gated:
                warnings.append(coverage_mod.insufficient_warning(gene_cov))

    for drug in drugs:
        result, drug_warnings, provenance = build_result(
            drug, report, starved_genes=starved
        )
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
    # The honest disclosure. This project has no qualified clinical reviewer,
    # so the warning states what was actually done -- provenance verification --
    # and names the gap directly rather than implying a review is pending.
    if store.entries:
        if store.unverified_count:
            warnings.append(
                f"{store.unverified_count} of {len(store)} pre-generated explanations "
                "have unverified clinical content. Treat their wording with caution."
            )
        warnings.append(
            "No qualified clinical expert has reviewed these explanations. This "
            "system writes no clinical content of its own: every clinical "
            "statement is machine-verified to trace to a CPIC recommendation "
            "issued by PharmCAT, or to a cited mechanism document. That checks "
            "provenance, not correctness."
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
            position_coverage=(
                cov.as_metrics() if cov is not None else {}
            ),
            guideline_provenance=guideline_provenance(report),
        ),
    )


# --------------------------------------------------------------------------- #
# Endpoint
# --------------------------------------------------------------------------- #


def _read_and_validate(contents: bytes, filename: str) -> VcfMetadata:
    """
    Upload gate shared by /analyze and /coverage.

    Extracted rather than copied: two endpoints applying subtly different size or
    build checks would be a silent divergence, and the coverage preview is only
    useful if it accepts exactly what the analysis would.
    """
    if len(contents) > MAX_UPLOAD_BYTES:
        raise ApiError(
            413,
            "FILE_TOO_LARGE",
            f"The file is {len(contents) / (1024 * 1024):.1f} MB, over the "
            f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
        )
    try:
        return validate_vcf(contents, filename=filename or "upload.vcf")
    except VcfValidationError as exc:
        raise ApiError(400, exc.code.value, exc.message) from exc


def guideline_provenance(report: PharmcatReport | None = None) -> GuidelineProvenance:
    """
    When the guidance behind a result was captured.

    Reads the explanation store's own generation stamp and, when a run is in
    hand, PharmCAT's self-reported versions — rather than constants, so it
    cannot claim a currency the shipped data does not have. `/coverage` has no
    run, so it names the pinned release and leaves the data-bundle stamp empty
    instead of guessing at one.

    Deliberately NOT a staleness check; see `GuidelineProvenance`.
    """
    generated = ""
    try:
        raw = json.loads(
            (Path(__file__).parent / "data" / "explanations.json").read_text()
        )
        generated = str(raw.get("generated_at") or "")
    except Exception:  # noqa: BLE001 — provenance must never break a response
        generated = ""
    return GuidelineProvenance(
        pharmcat_version=(report.pharmcat_version if report else PINNED_VERSION),
        cpic_data_version=((report.data_version or "") if report else ""),
        explanations_generated_at=generated,
    )


@app.post("/coverage", response_model=CoverageResponse, tags=["analysis"])
async def coverage_preview(
    file: UploadFile = File(..., description="VCF upload (.vcf or .vcf.gz, GRCh38)"),
) -> CoverageResponse:
    """
    What this file can answer — WITHOUT running PharmCAT.

    Exists so a user sees the shape of their result before committing to an
    analysis. Four Unknowns arriving unannounced read as failure; the same four
    announced in advance read as the system knowing its own limits.

    **No JVM is started here**, which is why it is not rate limited: it reads the
    upload, counts positions against the requirements table, and returns. It also
    writes no temp files at all — the coverage check works on the in-memory text —
    so the retention guarantee is satisfied by construction rather than by a
    cleanup block.
    """
    contents = await file.read()
    await file.close()
    metadata = _read_and_validate(contents, file.filename or "upload.vcf")

    cov = coverage_mod.assess(metadata.text)
    cfg = cpic_engine.load_mapping()
    data = coverage_mod.readiness(cov, cfg.get("drug_primary_gene", {}) or {})

    warnings = list(metadata.warnings)
    if cov.variants_only:
        warnings.append(coverage_mod.variants_only_warning())

    return CoverageResponse(
        genes=[GeneReadiness(**g) for g in data["genes"]],
        genes_passing=data["genes_passing"],
        genes_total=data["genes_total"],
        answerable_drugs=data["answerable_drugs"],
        unanswerable_drugs=data["unanswerable_drugs"],
        variants_only=data["variants_only"],
        warnings=warnings,
        guideline_provenance=guideline_provenance(),
    )


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
    # Loopback is exempt — see `security.should_rate_limit`. Checked before the
    # limiter so a local run does not even consume budget.
    decision = (
        security.limiter.check(security.client_key(request))
        if security.should_rate_limit(request)
        else security.RateLimitDecision(True, security.RATE_LIMIT_REQUESTS, 0)
    )
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

    # Size cap + format validation, shared with /coverage so the preview cannot
    # accept a file the analysis would reject.
    metadata = _read_and_validate(contents, file.filename or "upload.vcf")

    # A missing/ambiguous reference build is not fatal — validate_vcf has already
    # recorded a warning in metadata.warnings, which flows into quality_metrics.

    # THE FOURTH EDGE, and the only one facing the input. Computed before PharmCAT
    # because no output check can see it: missing positions do not make PharmCAT
    # decline, they make it confidently call the reference haplotype. See
    # `app/coverage.py` for the measured wrong-call rates.
    cov = coverage_mod.assess(metadata.text)

    try:
        report = await run_pharmcat(
            metadata.text,
            sample_hint=metadata.sample_ids[0] if metadata.sample_ids else "sample",
        )
    except PharmcatBusyError as exc:
        # ALSO 503, but a different error_code and a Retry-After, because this
        # is a queue and not a fault. Checked BEFORE PharmcatExecutionError:
        # PharmcatBusyError subclasses it, so the wider except would swallow it
        # and every busy response would read as "the analysis backend is down".
        raise ApiError(
            503, "SERVER_BUSY", exc.message,
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    except PharmcatExecutionError as exc:
        # 503, not 500: the request was fine, the server's analysis backend is not.
        raise ApiError(503, "PHARMCAT_UNAVAILABLE", exc.message) from exc

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return build_response(report, requested, metadata, elapsed_ms, cov=cov)
