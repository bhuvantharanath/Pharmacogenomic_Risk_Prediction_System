"""
PharmaGuard — deployment hardening.

Phase 4 puts the API on a public URL, which changes the threat model: Phases 1-3
assumed a caller on localhost. This module adds the three controls that matter
for a public, unauthenticated, free-tier service:

  * an explicit CORS allowlist (no wildcard in production)
  * a per-IP rate limit on the expensive endpoint
  * conservative security headers

It also holds the startup assertion that fails loudly if an API key was baked
into the image — the deployed path is supposed to need no secrets at all, and a
leaked key in a public Space would be the worst outcome of this phase.
"""

from __future__ import annotations

import os
import re
import threading
import time
from collections import deque
from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #

# Always allowed: local development. `flutter run -d chrome` binds a random
# port, so localhost needs a regex rather than a fixed list.
_LOCALHOST_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"


def allowed_origins() -> list[str]:
    """
    Exact origins from `CORS_ALLOWED_ORIGINS` (comma-separated).

    Phase 1-3 allowed `*.pages.dev` by regex, which is far too broad for a
    public deployment: it lets *any* Cloudflare Pages site — including one an
    attacker deploys in seconds — call this API from a user's browser. Phase 4
    names the deployment explicitly.
    """
    raw = os.environ.get("CORS_ALLOWED_ORIGINS", "")
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


def allowed_origin_regex() -> str | None:
    """
    Regex for origins that cannot be enumerated.

    Localhost always. Cloudflare Pages *preview* deployments get one
    per-branch subdomain of the project, so they are opt-in via
    `CORS_ALLOW_PAGES_PREVIEWS` with the project name — still scoped to one
    project, unlike a bare `*.pages.dev`.
    """
    patterns = [_LOCALHOST_REGEX]

    project = os.environ.get("CORS_ALLOW_PAGES_PREVIEWS", "").strip()
    if project:
        safe = re.escape(project)
        patterns.append(rf"^https://[a-z0-9-]+\.{safe}\.pages\.dev$")

    return "|".join(patterns)


#: Env vars that only exist on a real host. Their presence is how we tell
#: "someone deployed this" from "someone is running uvicorn on their laptop",
#: without needing an explicit ENVIRONMENT flag that a deployer could forget to
#: set — forgetting to set things is the exact failure we are guarding against.
#:   PORT           injected by Cloud Run and Render
#:   SPACE_ID       injected by Hugging Face Spaces
#:   K_SERVICE      injected by Cloud Run (Knative)
#:   RENDER         injected by Render
_HOSTED_ENV_MARKERS = ("SPACE_ID", "K_SERVICE", "RENDER", "PORT")


def looks_hosted() -> bool:
    """
    True when we appear to be running on a deployment platform.

    `PHARMAGUARD_ENV` overrides the sniffing in both directions, for anyone
    running a container locally (`=development`) or on a host we do not
    recognise (`=production`).
    """
    declared = os.environ.get("PHARMAGUARD_ENV", "").strip().lower()
    if declared in ("production", "prod", "hosted"):
        return True
    if declared in ("development", "dev", "local", "test"):
        return False
    return any(os.environ.get(marker) for marker in _HOSTED_ENV_MARKERS)


class CorsMisconfiguredError(RuntimeError):
    """Deployed with no allowed origins. Fails startup rather than 'working'."""


def assert_cors_configured() -> None:
    """
    Refuse to start a hosted instance with an empty origin allowlist.

    Why fatal rather than a warning: with no origins configured the service
    passes every health check, serves `/docs`, and answers `curl` perfectly —
    while every browser request from the real frontend is blocked. The failure
    surfaces only when a person opens the site, which in practice means during
    the demo. A container that refuses to start is discovered in the deploy log,
    minutes after the mistake, by the person who made it.

    Localhost is always permitted, so this never fires in development.
    """
    if not looks_hosted() or allowed_origins():
        return

    raise CorsMisconfiguredError(
        "CORS_ALLOWED_ORIGINS is empty but this instance looks hosted "
        f"(markers: {[m for m in _HOSTED_ENV_MARKERS if os.environ.get(m)]}).\n"
        "\n"
        "Only localhost would be allowed, so the deployed web app could not "
        "call this API from a browser — every analysis would fail CORS while "
        "health checks kept passing.\n"
        "\n"
        "Set it to your frontend's exact origin, for example:\n"
        "    CORS_ALLOWED_ORIGINS=https://pharmaguard.pages.dev\n"
        "\n"
        "  Hugging Face Spaces : Settings -> Variables and secrets -> New variable\n"
        "  Cloud Run           : --set-env-vars CORS_ALLOWED_ORIGINS=...\n"
        "  Render              : Environment -> Add Environment Variable\n"
        "  docker compose      : already set in infra/docker-compose.yml\n"
        "\n"
        "If this really is a local container, set PHARMAGUARD_ENV=development."
    )


def cors_summary() -> dict[str, object]:
    """What the CORS policy actually is, for `/` and for DEPLOY_NOTES."""
    return {
        "explicit_origins": allowed_origins(),
        "localhost_allowed": True,
        "pages_preview_project": os.environ.get("CORS_ALLOW_PAGES_PREVIEWS") or None,
        "wildcard": False,
    }


# --------------------------------------------------------------------------- #
# Rate limiting
# --------------------------------------------------------------------------- #

# Deliberately generous for a demo, but low enough that a public URL cannot be
# used to burn a free tier's compute budget. /analyze spawns a JVM per call.
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "300"))


@dataclass
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after: int


class InMemoryRateLimiter:
    """
    Sliding-window per-IP limiter.

    In-memory on purpose. The app is stateless and single-instance on every free
    tier considered (HF Spaces, Cloud Run min-instances=0, Render free), so a
    shared store would add a dependency for no benefit. The trade-off is
    explicit: **the limit resets when the container restarts**, which on a
    scale-to-zero host is often. This is abuse dampening, not a security
    boundary — it exists so a casual scraper cannot burn the free-tier budget.

    A real deployment behind multiple instances needs Redis; that is out of
    scope for a student project with no budget.
    """

    def __init__(
        self,
        max_requests: int = RATE_LIMIT_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, *, now: float | None = None) -> RateLimitDecision:
        """Record a hit for `key` and decide whether it is allowed."""
        current = now if now is not None else time.monotonic()
        cutoff = current - self.window_seconds

        with self._lock:
            bucket = self._hits.setdefault(key, deque())
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                retry_after = max(1, int(bucket[0] + self.window_seconds - current) + 1)
                return RateLimitDecision(False, 0, retry_after)

            bucket.append(current)
            # Opportunistic cleanup: without this, one request per IP from a
            # botnet would grow the dict forever.
            if len(self._hits) > 4096:
                self._evict_stale(cutoff)
            return RateLimitDecision(True, self.max_requests - len(bucket), 0)

    def _evict_stale(self, cutoff: float) -> None:
        """Drop buckets whose most recent hit is outside the window."""
        stale = [k for k, v in self._hits.items() if not v or v[-1] <= cutoff]
        for key in stale:
            self._hits.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = InMemoryRateLimiter()


#: Loopback addresses. A request from one of these came from this machine, so the
#: only possible caller is the operator.
_LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost", "::ffff:127.0.0.1"})


def is_loopback(request: Request) -> bool:
    """
    True when the caller is this machine, using the DIRECT peer address only.

    Deliberately ignores `X-Forwarded-For`: that header is caller-controlled, so
    trusting it here would let anyone claim `127.0.0.1` and skip the limit
    entirely. `request.client.host` is the actual TCP peer, which a remote caller
    cannot forge. A proxy on the same host is the one false positive, and that is
    a deployment shape this project does not use.
    """
    client = request.client
    host = (client.host if client else "").strip().lower()
    return host in _LOOPBACK


def client_key(request: Request) -> str:
    """
    Identify the caller for rate-limiting purposes.

    Every target platform (HF Spaces, Cloud Run, Render, Cloudflare) terminates
    TLS at a proxy, so `request.client.host` is the proxy, not the user. The
    left-most `X-Forwarded-For` entry is the original client.

    That header is caller-controlled and trivially spoofed. We use it anyway
    because the alternative — limiting every user to a shared proxy IP — would
    rate-limit all legitimate traffic as one caller. Stated plainly: this
    dampens casual abuse; it does not stop a determined attacker.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    client = request.client
    return client.host if client else "unknown"


# --------------------------------------------------------------------------- #
# Security headers
# --------------------------------------------------------------------------- #


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Conservative response headers.

    This service returns JSON only and renders no HTML, so the interesting
    header is `X-Content-Type-Options: nosniff` — it stops a browser
    reinterpreting a JSON response as something executable.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # Do not leak the full API URL (or query) to third parties.
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        # No HTML is served, so no frame should ever embed a response.
        response.headers.setdefault("X-Frame-Options", "DENY")
        # Belt and braces: a JSON API needs none of these capabilities.
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        return response


def should_rate_limit(request: Request) -> bool:
    """
    Whether this request is subject to the per-IP limit.

    LOOPBACK IS EXEMPT, and this is scoping rather than loosening. Per-IP limiting
    exists to stop a public endpoint being hammered by strangers. On 127.0.0.1
    there are no strangers — the only client is the operator running the service,
    so the limit protects nothing while reliably breaking rehearsal: the demo
    makes 7 requests against a 10-per-5-minutes budget, so running it twice in a
    window returns 429 in about a millisecond, which looks exactly like a crash.
    The deployed limit for every non-loopback caller is unchanged.
    """
    if is_loopback(request):
        return False
    return True


def rate_limit_response(decision: RateLimitDecision) -> JSONResponse:
    """The 429 body. Explains the limit rather than just refusing."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                f"Rate limit reached: {RATE_LIMIT_REQUESTS} analyses per "
                f"{RATE_LIMIT_WINDOW_SECONDS // 60} minutes per client. "
                f"Please wait {decision.retry_after} seconds and try again. "
                "This is a free-tier academic demo, not a production service."
            ),
            "error_code": "RATE_LIMITED",
        },
        headers={"Retry-After": str(decision.retry_after)},
    )


# --------------------------------------------------------------------------- #
# Secret-leak assertion
# --------------------------------------------------------------------------- #

# Env vars that must never be present in the deployed image. The runtime reads
# these only in `live` explanation mode, which is not the production default.
_SECRET_ENV_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "HF_TOKEN")


class BakedSecretError(RuntimeError):
    """A secret was found where one should never be. Fails startup."""


def assert_no_baked_secrets(
    *, explanation_mode: str, dotenv_path: str | None = None
) -> list[str]:
    """
    Fail startup if a credential appears to be baked into the image.

    Two checks:

      1. A committed `.env` file inside the image. `.env` is gitignored, so its
         presence means someone forced it in or COPY'd the whole build context.
      2. A populated `GEMINI_API_KEY` while running in `static` mode. Static
         mode makes no API call, so a key being there is either a mistake or a
         leak — and on a public Space, anything in the image is public.

    Returns warnings for non-fatal observations. Raises `BakedSecretError` for
    the fatal ones, deliberately taking the service down rather than serving
    from an image with a secret in it.
    """
    from pathlib import Path

    warnings: list[str] = []

    env_file = Path(dotenv_path or Path(__file__).resolve().parent.parent / ".env")
    if env_file.is_file():
        raise BakedSecretError(
            f"A .env file is present at {env_file}. Secrets must come from the "
            "platform's secret store (HF Space Secrets / Cloud Run secrets), "
            "never from a file inside the image. Refusing to start."
        )

    if explanation_mode == "static":
        present = [name for name in _SECRET_ENV_VARS if os.environ.get(name, "").strip()]
        if present:
            # Not fatal: on a correctly-configured Space this means the operator
            # set a secret they do not need. Loud, because on a *public* Space a
            # key in the image layer would be readable by anyone.
            warnings.append(
                f"{', '.join(present)} is set but EXPLANATION_MODE=static makes no "
                "API call. Remove it unless you intend to switch to live mode — "
                "an unused credential is pure risk."
            )

    return warnings
