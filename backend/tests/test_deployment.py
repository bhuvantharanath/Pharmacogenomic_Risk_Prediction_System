"""
Phase 4 — the controls a public URL needs.

Everything here is about the deployed configuration rather than the analysis
pipeline: CORS, rate limiting, response headers, secret hygiene, readiness, and
the privacy claim that no genomic data survives a request.

The temp-file test is the one that backs a **claim made to users** in the
README, so it asserts the property directly rather than trusting the code.
"""

from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main, security
from app.pharmcat_models import PharmcatReport
from app.security import (
    BakedSecretError,
    CorsMisconfiguredError,
    InMemoryRateLimiter,
    assert_cors_configured,
    assert_no_baked_secrets,
    client_key,
    looks_hosted,
)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, cyp2c19_pm_report: PharmcatReport):
    async def fake_run_pharmcat(vcf_text: str, *, sample_hint: str = "sample"):
        return cyp2c19_pm_report

    monkeypatch.setattr(main, "run_pharmcat", fake_run_pharmcat)
    return TestClient(main.app)


def post(client: TestClient, content: bytes, drugs: str = "clopidogrel", **kwargs):
    return client.post(
        "/analyze",
        files={"file": ("test.vcf", io.BytesIO(content), "text/plain")},
        data={"drugs": drugs},
        **kwargs,
    )


class TestHealthAndReady:
    """/health must stay cheap; /ready must actually check things."""

    def test_health_is_dependency_free(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        The wake-up ping must not touch PharmCAT.

        If it did, the endpoint the client hammers during a cold start would be
        the expensive one — and a container that is still waking would report
        unhealthy.
        """

        def explode():
            raise AssertionError("/health invoked PharmCAT")

        monkeypatch.setattr(main, "pharmcat_available", explode)
        response = TestClient(main.app).get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_ready_reports_per_dependency_status(self) -> None:
        body = TestClient(main.app).get("/ready").json()
        assert set(body["checks"]) == {
            "pharmcat",
            "mechanism_corpus",
            "explanations",
            "label_mapping",
        }
        for name, check in body["checks"].items():
            assert isinstance(check["ok"], bool), name
            assert check["detail"], name

    def test_ready_is_503_when_pharmcat_is_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Patches `resolve_invoker`, which is the seam /ready actually consults
        # now that the jar is the primary path. `pharmcat_available` is derived
        # from the same resolver, so patching that alone would no longer make
        # this endpoint report a failure.
        monkeypatch.setattr(main, "resolve_invoker", lambda: None)
        response = TestClient(main.app).get("/ready")
        assert response.status_code == 503
        assert response.json()["status"] == "not_ready"
        assert response.json()["checks"]["pharmcat"]["ok"] is False
        # The message must say what to DO, not just what is missing — the whole
        # reason this path was reworked is that "not installed" pointed at the
        # wrapper while a usable jar sat on disk.
        detail = response.json()["checks"]["pharmcat"]["detail"]
        assert "PHARMCAT_JAR" in detail or "fetch_reference_data" in detail

    def test_missing_jar_message_leads_with_the_jar_not_the_wrapper(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        The Docker case: no jar, no wrapper, and the operator needs one command.

        This is the regression that motivated the rework. An earlier draft of
        `unavailable_reason()` returned "the optional 'pharmcat_pipeline' wrapper
        is also absent" whenever the jar happened to resolve — actionable for
        nobody, and pointing at the component that is explicitly optional.
        """
        from app import pharmcat_runner

        monkeypatch.setattr(pharmcat_runner, "find_jar", lambda: None)
        monkeypatch.setattr(pharmcat_runner.shutil, "which", lambda _: None)
        reason = pharmcat_runner.unavailable_reason()

        assert "fetch_reference_data" in reason, "must name the command that fixes it"
        assert "PHARMCAT_JAR" in reason, "must name the override env var"
        assert not reason.startswith("the optional"), (
            "the optional wrapper must never lead the diagnosis"
        )

    def test_unavailable_reason_never_blames_only_the_wrapper(self) -> None:
        """
        Holds on THIS machine, where the jar is present.

        Guards the branch that produced a nonsense message: jar found, JRE found,
        resolution still failed. The honest answer is 'this should have worked' —
        never a confident wrong cause.
        """
        from app import pharmcat_runner

        reason = pharmcat_runner.unavailable_reason()
        assert "pharmcat_pipeline" not in reason or "jar" in reason.lower()
        assert len(reason) > 40, "a bare phrase is not a remediation"

    def test_missing_explanations_does_not_fail_readiness(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        """Degraded (template fallback) is not the same as broken."""
        from app.explanation import static_store

        static_store.load_store.cache_clear()
        monkeypatch.setattr(
            static_store, "DEFAULT_STORE_PATH", tmp_path / "missing.json"
        )
        try:
            body = TestClient(main.app).get("/ready").json()
            assert body["checks"]["explanations"]["ok"] is True
        finally:
            static_store.load_store.cache_clear()


class TestSecurityHeaders:
    @pytest.mark.parametrize(
        "header,expected",
        [
            ("X-Content-Type-Options", "nosniff"),
            ("Referrer-Policy", "no-referrer"),
            ("X-Frame-Options", "DENY"),
        ],
    )
    def test_headers_present(self, header: str, expected: str) -> None:
        response = TestClient(main.app).get("/health")
        assert response.headers.get(header) == expected

    def test_headers_present_on_errors_too(self, client: TestClient) -> None:
        response = post(client, b"")
        assert response.status_code == 400
        assert response.headers.get("X-Content-Type-Options") == "nosniff"


class TestCors:
    """
    Phase 1-3 allowed any `*.pages.dev` origin. On a public URL that lets an
    attacker's Pages site call this API from a visitor's browser.
    """

    def _origin_allowed(self, monkeypatch, origin: str, **env: str) -> bool:
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        # CORS config is read when the middleware stack is built.
        from importlib import reload

        reload(main)
        response = TestClient(main.app).get("/health", headers={"Origin": origin})
        return response.headers.get("access-control-allow-origin") is not None

    def test_localhost_is_always_allowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assert self._origin_allowed(monkeypatch, "http://localhost:5000")

    def test_configured_origin_is_allowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assert self._origin_allowed(
            monkeypatch,
            "https://pharmaguard.pages.dev",
            CORS_ALLOWED_ORIGINS="https://pharmaguard.pages.dev",
        )

    def test_unlisted_origin_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Acceptance #4 — an unlisted origin gets no CORS header."""
        assert not self._origin_allowed(
            monkeypatch,
            "https://evil.example.com",
            CORS_ALLOWED_ORIGINS="https://pharmaguard.pages.dev",
        )

    def test_arbitrary_pages_dev_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The specific Phase 1-3 hole: any *.pages.dev used to pass."""
        assert not self._origin_allowed(
            monkeypatch,
            "https://attacker-site.pages.dev",
            CORS_ALLOWED_ORIGINS="https://pharmaguard.pages.dev",
        )

    def test_preview_subdomains_are_scoped_to_one_project(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert self._origin_allowed(
            monkeypatch,
            "https://abc123.pharmaguard.pages.dev",
            CORS_ALLOWED_ORIGINS="https://pharmaguard.pages.dev",
            CORS_ALLOW_PAGES_PREVIEWS="pharmaguard",
        )
        assert not self._origin_allowed(
            monkeypatch,
            "https://abc123.someone-else.pages.dev",
            CORS_ALLOWED_ORIGINS="https://pharmaguard.pages.dev",
            CORS_ALLOW_PAGES_PREVIEWS="pharmaguard",
        )

    def test_no_wildcard_is_ever_configured(self) -> None:
        assert "*" not in security.allowed_origins()
        assert security.cors_summary()["wildcard"] is False


class TestRateLimiter:
    def test_allows_up_to_the_limit(self) -> None:
        limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60)
        assert [limiter.check("ip").allowed for _ in range(3)] == [True] * 3

    def test_blocks_beyond_the_limit(self) -> None:
        limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
        limiter.check("ip")
        limiter.check("ip")
        decision = limiter.check("ip")
        assert not decision.allowed
        assert decision.retry_after > 0

    def test_window_slides(self) -> None:
        limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
        limiter.check("ip", now=0.0)
        limiter.check("ip", now=1.0)
        assert not limiter.check("ip", now=2.0).allowed
        # Once the first two hits age out, capacity returns.
        assert limiter.check("ip", now=62.0).allowed

    def test_clients_are_independent(self) -> None:
        limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60)
        assert limiter.check("a").allowed
        assert not limiter.check("a").allowed
        assert limiter.check("b").allowed

    def test_stale_buckets_are_evicted(self) -> None:
        """Without eviction, one request per IP would grow the dict forever."""
        limiter = InMemoryRateLimiter(max_requests=1, window_seconds=1)
        for i in range(5000):
            limiter.check(f"ip-{i}", now=0.0)
        limiter.check("trigger", now=10_000.0)
        assert len(limiter._hits) < 5000

    def test_analyze_returns_429_when_tripped(
        self, client: TestClient, valid_vcf_bytes: bytes, monkeypatch
    ) -> None:
        """Acceptance #4 — the limiter returns 429 with a clear message."""
        monkeypatch.setattr(security, "RATE_LIMIT_REQUESTS", 2)
        security.limiter.__init__(max_requests=2, window_seconds=300)

        assert post(client, valid_vcf_bytes).status_code == 200
        assert post(client, valid_vcf_bytes).status_code == 200

        response = post(client, valid_vcf_bytes)
        assert response.status_code == 429
        body = response.json()
        assert body["error_code"] == "RATE_LIMITED"
        assert "Rate limit" in body["detail"]
        assert int(response.headers["Retry-After"]) > 0

    def test_limit_is_per_client_ip(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        security.limiter.__init__(max_requests=1, window_seconds=300)

        first = post(client, valid_vcf_bytes, headers={"X-Forwarded-For": "1.1.1.1"})
        assert first.status_code == 200
        blocked = post(client, valid_vcf_bytes, headers={"X-Forwarded-For": "1.1.1.1"})
        assert blocked.status_code == 429
        # A different client is unaffected.
        other = post(client, valid_vcf_bytes, headers={"X-Forwarded-For": "2.2.2.2"})
        assert other.status_code == 200

    def test_forwarded_for_takes_the_leftmost_entry(self) -> None:
        """Every target platform terminates TLS at a proxy."""

        class _Request:
            headers = {"x-forwarded-for": "203.0.113.7, 70.41.3.18, 150.172.238.178"}
            client = None

        assert client_key(_Request()) == "203.0.113.7"


class TestNoDataRetention:
    """
    Acceptance #6, and a claim the README makes to users.

    Asserted as a property of the filesystem after a real request, not as a
    reading of the code — the point is that a future refactor that starts
    persisting uploads fails here.
    """

    def test_temp_dir_is_empty_after_a_request(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        temp_root = Path(tempfile.gettempdir())
        before = set(temp_root.glob("pharmaguard_*"))

        assert post(client, valid_vcf_bytes).status_code == 200

        leaked = set(temp_root.glob("pharmaguard_*")) - before
        assert not leaked, f"temp dirs survived the request: {leaked}"

    def test_temp_dir_is_cleaned_even_when_pharmcat_fails(
        self, monkeypatch: pytest.MonkeyPatch, valid_vcf_bytes: bytes
    ) -> None:
        """The `finally` must hold on the error path too — that is its job."""
        from app import pharmcat_runner

        temp_root = Path(tempfile.gettempdir())
        before = set(temp_root.glob("pharmaguard_*"))

        async def exploding_exec(command):
            raise RuntimeError("simulated PharmCAT crash")

        monkeypatch.setattr(pharmcat_runner, "_exec", exploding_exec)

        with pytest.raises(RuntimeError):
            import asyncio

            asyncio.run(pharmcat_runner.run_pharmcat("##fileformat=VCFv4.2\n"))

        leaked = set(temp_root.glob("pharmaguard_*")) - before
        assert not leaked, f"temp dirs survived a failure: {leaked}"

    def test_uploaded_content_is_not_echoed_in_the_response(
        self, client: TestClient, valid_vcf_bytes: bytes
    ) -> None:
        """A response containing raw genotype lines would be a leak vector."""
        body = post(client, valid_vcf_bytes).text
        assert "##fileformat" not in body
        assert "PharmaGuardSyntheticGenerator" not in body

    def test_root_advertises_no_retention(self) -> None:
        body = TestClient(main.app).get("/").json()
        assert "none" in body["data_retention"].lower()


class TestSecretHygiene:
    """Acceptance #3 — no key anywhere, and startup fails if one appears."""

    def test_passes_when_no_secrets_are_set(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "HF_TOKEN"):
            monkeypatch.delenv(name, raising=False)
        assert assert_no_baked_secrets(
            explanation_mode="static", dotenv_path=str(tmp_path / "absent.env")
        ) == []

    def test_dotenv_in_the_image_is_fatal(self, tmp_path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("GEMINI_API_KEY=leaked\n")
        with pytest.raises(BakedSecretError) as excinfo:
            assert_no_baked_secrets(
                explanation_mode="static", dotenv_path=str(env_file)
            )
        assert "never from a file inside the image" in str(excinfo.value)

    def test_unused_key_in_static_mode_warns(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        monkeypatch.setenv("GEMINI_API_KEY", "unused-but-present")
        warnings = assert_no_baked_secrets(
            explanation_mode="static", dotenv_path=str(tmp_path / "absent.env")
        )
        assert any("GEMINI_API_KEY" in w for w in warnings)

    def test_no_secret_literals_in_the_repo(self) -> None:
        """
        Grep the tracked source for anything shaped like a real key.

        Google API keys start `AIza`. This is a coarse check, but it is the one
        that would have caught the mistake we most care about.
        """
        import re

        repo = Path(__file__).resolve().parents[2]
        pattern = re.compile(r"AIza[0-9A-Za-z_\-]{20,}|hf_[0-9A-Za-z]{30,}")
        skip = {".venv", ".git", "build", ".dart_tool", "__pycache__", "node_modules"}

        offenders = []
        for path in repo.rglob("*"):
            if not path.is_file() or any(part in skip for part in path.parts):
                continue
            if path.suffix not in {
                ".py", ".dart", ".yaml", ".yml", ".json", ".md",
                ".txt", ".sh", ".example", ".gradle", ".properties",
            }:
                continue
            try:
                if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                    offenders.append(str(path.relative_to(repo)))
            except OSError:
                continue
        assert not offenders, f"possible secret literals: {offenders}"

    def test_env_example_has_no_populated_key(self) -> None:
        example = Path(__file__).resolve().parents[1] / ".env.example"
        for line in example.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY"):
                assert line.strip() == "GEMINI_API_KEY=", (
                    f".env.example must ship an empty key, got: {line!r}"
                )


class TestPortConfiguration:
    """
    One image, three hosts.

    HF Spaces expects 7860; Cloud Run and Render inject `$PORT`. The container
    command honours `$PORT` with a 7860 default so the same image runs on all
    three without a rebuild.
    """

    def test_dockerfile_honours_port_env(self) -> None:
        dockerfile = (
            Path(__file__).resolve().parents[2] / "infra" / "Dockerfile"
        ).read_text()
        assert "${PORT:-7860}" in dockerfile, (
            "Dockerfile must honour $PORT with a 7860 default"
        )

    def test_hf_space_readme_declares_docker_sdk(self) -> None:
        readme = (
            Path(__file__).resolve().parents[2] / "infra" / "hf-space" / "README.md"
        ).read_text()
        assert readme.startswith("---"), "HF Space README needs YAML front matter"
        assert "sdk: docker" in readme
        assert "app_port: 7860" in readme


class TestCorsFailsLoudWhenMisconfigured:
    """
    P1-3 regression.

    The original defect was not that CORS was *wrong* — the policy code was
    correct and well tested. It was that nothing set the value, and an unset
    value produced a service that passed every health check while blocking
    every real browser request. So the fix under test here is the *loudness*:
    a hosted instance with no origins must refuse to start.
    """

    @pytest.fixture(autouse=True)
    def _clean_env(self, monkeypatch: pytest.MonkeyPatch):
        for name in (
            "CORS_ALLOWED_ORIGINS",
            "PHARMAGUARD_ENV",
            "SPACE_ID",
            "K_SERVICE",
            "RENDER",
            "PORT",
        ):
            monkeypatch.delenv(name, raising=False)

    # -- environment sniffing ------------------------------------------------

    def test_bare_local_run_is_not_hosted(self) -> None:
        assert looks_hosted() is False

    @pytest.mark.parametrize(
        "marker,value",
        [
            ("SPACE_ID", "user/pharmaguard"),  # Hugging Face Spaces
            ("K_SERVICE", "pharmaguard-api"),  # Cloud Run
            ("RENDER", "true"),                # Render
            ("PORT", "8080"),                  # Cloud Run / Render
        ],
    )
    def test_platform_markers_are_detected(
        self, monkeypatch: pytest.MonkeyPatch, marker: str, value: str
    ) -> None:
        monkeypatch.setenv(marker, value)
        assert looks_hosted() is True

    def test_explicit_env_overrides_sniffing_both_ways(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PORT", "8080")
        monkeypatch.setenv("PHARMAGUARD_ENV", "development")
        assert looks_hosted() is False

        monkeypatch.delenv("PORT")
        monkeypatch.setenv("PHARMAGUARD_ENV", "production")
        assert looks_hosted() is True

    # -- the assertion itself ------------------------------------------------

    def test_hosted_with_empty_origins_refuses_to_start(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """This is the exact misconfiguration the audit found."""
        monkeypatch.setenv("K_SERVICE", "pharmaguard-api")
        with pytest.raises(CorsMisconfiguredError) as excinfo:
            assert_cors_configured()

        message = str(excinfo.value)
        # The message has to be actionable, not just a refusal.
        assert "CORS_ALLOWED_ORIGINS" in message
        assert "pages.dev" in message
        assert "Hugging Face" in message and "Cloud Run" in message
        assert "PHARMAGUARD_ENV=development" in message

    def test_hosted_with_origins_starts_fine(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("K_SERVICE", "pharmaguard-api")
        monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://pharmaguard.pages.dev")
        assert_cors_configured()  # must not raise

    def test_local_dev_with_empty_origins_starts_fine(self) -> None:
        """Localhost is always allowed, so this must never fire in dev."""
        assert_cors_configured()  # must not raise

    def test_local_container_opt_out_starts_fine(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PORT", "7860")
        monkeypatch.setenv("PHARMAGUARD_ENV", "development")
        assert_cors_configured()  # must not raise

    # -- end-to-end through the app ------------------------------------------

    def test_configured_origin_is_allowed_and_unlisted_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        The behavioural half: an allowed origin gets the CORS header back, an
        unlisted one does not. Asserted against the real middleware stack.
        """
        from importlib import reload

        monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://pharmaguard.pages.dev")
        reload(main)
        client = TestClient(main.app)

        allowed = client.get(
            "/health", headers={"Origin": "https://pharmaguard.pages.dev"}
        )
        assert allowed.headers.get("access-control-allow-origin") == (
            "https://pharmaguard.pages.dev"
        )

        for bad in (
            "https://evil.example.com",
            "https://attacker-site.pages.dev",  # the old wildcard hole
        ):
            rejected = client.get("/health", headers={"Origin": bad})
            assert rejected.headers.get("access-control-allow-origin") is None, bad


class TestRateLimitScoping:
    """
    Loopback is exempt; everything else is limited exactly as before.

    This is scoping, not loosening — the distinction matters because the obvious
    alternative (raise the limit) would weaken the deployed endpoint to fix a
    problem that only exists locally.
    """

    def _request(self, host: str):
        from unittest.mock import Mock

        request = Mock()
        request.client = Mock(host=host)
        request.headers = {}
        return request

    @pytest.mark.parametrize("host", ["127.0.0.1", "::1", "::ffff:127.0.0.1"])
    def test_loopback_is_exempt(self, host: str) -> None:
        from app import security

        assert security.is_loopback(self._request(host)) is True
        assert security.should_rate_limit(self._request(host)) is False

    @pytest.mark.parametrize("host", ["203.0.113.7", "10.0.0.4", "198.51.100.2"])
    def test_everything_else_is_still_limited(self, host: str) -> None:
        from app import security

        assert security.is_loopback(self._request(host)) is False
        assert security.should_rate_limit(self._request(host)) is True

    def test_a_spoofed_forwarded_header_cannot_buy_an_exemption(self) -> None:
        """
        X-Forwarded-For is caller-controlled. If the exemption trusted it, anyone
        could claim 127.0.0.1 and skip the limit — turning a local convenience
        into a hole in the deployed protection.
        """
        from unittest.mock import Mock

        from app import security

        request = Mock()
        request.client = Mock(host="203.0.113.7")
        request.headers = {"x-forwarded-for": "127.0.0.1"}
        assert security.is_loopback(request) is False
        assert security.should_rate_limit(request) is True

    def test_the_limit_itself_was_not_raised(self) -> None:
        from app import security

        assert security.RATE_LIMIT_REQUESTS == 10
        assert security.RATE_LIMIT_WINDOW_SECONDS == 300

    def test_429_carries_retry_after_and_says_it_is_a_rate_limit(self) -> None:
        from app import security

        response = security.rate_limit_response(
            security.RateLimitDecision(False, 0, 42)
        )
        assert response.status_code == 429
        assert response.headers["Retry-After"] == "42"
        body = response.body.decode()
        assert "RATE_LIMITED" in body
        assert "Rate limit reached" in body
        assert "42 seconds" in body


class TestCorsConvergence:
    """
    Local configuration must exercise the same path as deployed configuration.

    An earlier fix read the port out of argv specifically so PORT would stay unset
    and the hosted-instance guard would not fire. That made local startup take a
    different branch from production — in the one area where a misconfiguration is
    invisible until a real browser tries it.
    """

    def test_guard_still_fires_on_hosting_markers_with_empty_allowlist(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app import security

        monkeypatch.setenv("PORT", "8080")
        monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "")
        with pytest.raises(security.CorsMisconfiguredError):
            security.assert_cors_configured()

    def test_documented_local_config_starts_even_with_hosting_markers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app import security

        monkeypatch.setenv("PORT", "8000")
        monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:8080")
        security.assert_cors_configured()   # must not raise
        assert "http://localhost:8080" in security.allowed_origins()

    def test_local_dev_env_file_documents_the_origins(self) -> None:
        """
        The file the runbook tells you to copy must actually configure CORS.

        Asserts the **example**, not `infra/local-dev.env` itself. The real file
        matches `*.env` in .gitignore, so it exists on a developer's machine and
        never in CI — an earlier version of this test asserted the real file and
        so could only ever pass locally. It had been failing on `main` since the
        workflow was added, which is how a test that cannot pass survives: it
        goes red somewhere nobody is looking.

        The example is what a new contributor copies, so it is the thing whose
        contents actually have to be right.
        """
        from pathlib import Path

        infra = Path(__file__).resolve().parents[2] / "infra"
        example = infra / "local-dev.env.example"
        assert example.is_file(), "infra/local-dev.env.example is in the runbook"
        text = example.read_text()
        assert "CORS_ALLOWED_ORIGINS=" in text
        assert "localhost" in text

        # And if a developer has made the real file, it must agree.
        real = infra / "local-dev.env"
        if real.is_file():
            assert "CORS_ALLOWED_ORIGINS=" in real.read_text()

    def test_no_dotenv_is_committed_under_backend(self) -> None:
        """
        `assert_no_baked_secrets` refuses to start if backend/.env exists, so the
        local config deliberately lives elsewhere. Creating one breaks startup.
        """
        from pathlib import Path

        assert not (Path(__file__).resolve().parents[1] / ".env").is_file(), (
            "backend/.env exists — the secret guard will refuse to start"
        )
