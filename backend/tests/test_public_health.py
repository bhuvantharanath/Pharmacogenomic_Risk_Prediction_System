"""
`/health` answers every origin; everything else keeps the allowlist (Phase 9 B7).

Audit finding F-11: a page on an origin the CORS policy refused got no readable
response at all, so the client could not tell it from a server still asleep, and
after 180 s told the user the server had "responded but did not report healthy".
`/health` is now readable from any origin and reports whether the asking origin
is allowed; preview deployments of the configured Pages project are allowed by a
strict regex. These tests pin both halves: what opened, and that nothing else did.
"""

from __future__ import annotations

import io

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app import main, security

EVIL = "https://evil.example"
LOCAL = "http://localhost:5000"  # allowed in every environment, by regex
PRODUCTION = "https://pharmaguard-web.pages.dev"
PREVIEW = "https://6bc16810.pharmaguard-web.pages.dev"  # the F-11 origin
LOOK_ALIKES = (
    "https://pharmaguard-web.pages.dev.evil.com",
    "https://evil-pharmaguard-web.pages.dev",
    "https://a.b.pharmaguard-web.pages.dev",
    "http://abc.pharmaguard-web.pages.dev",
    "https://abc.pharmaguard-web.pages.dev.",
    "https://abcpharmaguard-web.pages.dev",
    "https://abc.other-project.pages.dev",
    "https://abc.pharmaguard-web.pages.dev:8443",
    "https://ABC.pharmaguard-web.pages.dev",
    "https://abc.pharmaguard-web.pages.dev/path",
    "https://abc.pharmaguard-webxpages.dev",
)


def _client() -> TestClient:
    # A client per call: test_deployment.py reloads app.main.
    return TestClient(main.app)


def _acao(response) -> str | None:
    return response.headers.get("access-control-allow-origin")


# --------------------------------------------------------------------------- #
# AC1 — /health
# --------------------------------------------------------------------------- #


def test_health_reports_build_data_and_no_origin_without_one() -> None:
    response = _client().get("/health")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"
    assert set(body) == {"status", "commit", "commit_short", "data", "origin_allowed"}
    assert body["origin_allowed"] is None
    assert body["commit_short"] == (body["commit"][:7] if body["commit"] != "unknown" else "unknown")
    if main.knowledge_identity():  # the jar is present
        assert set(body["data"]) == {"cpic_guidance_sha256", "allele_definitions_sha256",
                                     "allele_definitions_version"}


@pytest.mark.parametrize(("origin", "allowed"), [(LOCAL, True), (EVIL, False)])
def test_every_origin_can_read_health_and_learns_whether_it_is_allowed(origin: str, allowed: bool) -> None:
    response = _client().get("/health", headers={"Origin": origin})
    assert _acao(response) == "*"
    assert response.json()["origin_allowed"] is allowed


def test_the_health_preflight_is_answered_for_any_origin() -> None:
    response = _client().options("/health", headers={
        "Origin": EVIL, "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type"})
    assert response.status_code == 204
    assert _acao(response) == "*"
    assert "GET" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-headers"] == "content-type"


def test_nothing_else_opened_for_a_refused_origin() -> None:
    client = _client()
    assert _acao(client.get("/ready", headers={"Origin": EVIL})) is None
    assert _acao(client.get("/", headers={"Origin": EVIL})) is None
    upload = {"file": ("x.vcf", io.BytesIO(b"not a vcf"), "text/plain")}
    assert _acao(client.post("/coverage", files=upload, headers={"Origin": EVIL})) is None
    assert _acao(client.post("/analyze", files=upload, data={"drugs": "clopidogrel"},
                             headers={"Origin": EVIL})) is None
    preflight = client.options("/analyze", headers={"Origin": EVIL, "Access-Control-Request-Method": "POST"})
    assert preflight.status_code == 400 and _acao(preflight) is None


@pytest.mark.parametrize("origin", [LOCAL, "http://127.0.0.1:8080", EVIL, PRODUCTION, PREVIEW, *LOOK_ALIKES[:3]])
def test_origin_allowed_is_the_cors_middlewares_own_decision(origin: str) -> None:
    """What /health reports equals what CORSMiddleware does on a real endpoint."""
    client = _client()
    reported = client.get("/health", headers={"Origin": origin}).json()["origin_allowed"]
    granted = _acao(client.get("/ready", headers={"Origin": origin})) == origin
    assert reported is granted, (origin, reported, granted)


# --------------------------------------------------------------------------- #
# AC2 — preview origins of the configured Pages project
# --------------------------------------------------------------------------- #


@pytest.fixture
def production_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", PRODUCTION)
    monkeypatch.delenv("CORS_ALLOW_PAGES_PREVIEWS", raising=False)


def _real_cors_app() -> TestClient:
    """A bare app behind CORSMiddleware configured exactly as main configures it."""
    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=security.allowed_origins(),
                       allow_origin_regex=security.allowed_origin_regex(), allow_credentials=False,
                       allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])

    @app.get("/x")
    def x() -> dict:
        return {}

    return TestClient(app)


def test_the_configured_projects_previews_are_allowed(production_origin) -> None:
    assert security.pages_preview_projects() == ["pharmaguard-web"]
    client = _real_cors_app()
    for origin in (PRODUCTION, PREVIEW, "https://main.pharmaguard-web.pages.dev"):
        assert security.is_allowed_origin(origin), origin
        assert _acao(client.get("/x", headers={"Origin": origin})) == origin, origin


@pytest.mark.parametrize("origin", LOOK_ALIKES)
def test_a_look_alike_is_rejected(production_origin, origin: str) -> None:
    assert not security.is_allowed_origin(origin)
    assert _acao(_real_cors_app().get("/x", headers={"Origin": origin})) is None


def test_no_pages_origin_means_no_previews(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never a bare *.pages.dev: with no Pages project configured, no preview passes."""
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://example.org")
    monkeypatch.delenv("CORS_ALLOW_PAGES_PREVIEWS", raising=False)
    assert security.pages_preview_projects() == []
    assert not security.is_allowed_origin(PREVIEW)
    assert security.cors_summary()["wildcard"] is False
