"""
Shared plumbing for the PharmaGuard CLI scripts.

Everything in `scripts/` is build-time tooling: it may read the API key, call
Gemini, and write into `backend/app/data/`. None of it is imported by the served
application — `EXPLANATION_MODE=static` reads only the generated JSON, so the
deployed path stays key-free.

WHERE THE KEY LIVES
    Repo-root `.env`, gitignored. Deliberately NOT `backend/.env`: the backend's
    own startup guard (`app/security.py::assert_no_baked_secrets`) refuses to
    boot if it finds `backend/.env`, on the grounds that inside a deployed image
    such a file could only be a leaked credential. Putting build-time secrets
    one directory up keeps both invariants true at once.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
DATA_DIR = BACKEND / "app" / "data"
REPORTS_DIR = REPO_ROOT / "reports"
LOGS_DIR = REPO_ROOT / "logs"

CASE_MATRIX_PATH = DATA_DIR / "case_matrix.json"
EXPLANATIONS_PATH = DATA_DIR / "explanations.json"
GUARD_EVENTS_PATH = LOGS_DIR / "guard_events.jsonl"
DOTENV_PATH = REPO_ROOT / ".env"

# Make `app.*` importable from any script.
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


# --------------------------------------------------------------------------- #
# Model + rate limiting
# --------------------------------------------------------------------------- #

#: Default model. Overridable with GEMINI_MODEL, and by `--model` on the CLIs.
#:
#: `gemini-3.6-flash` was confirmed present in this project's own
#: `models.list()` output on 2026-07-23 (see scripts/README.md). It is not
#: hardcoded anywhere in application source — only here, as a default that the
#: environment can override, because model ids change often.
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

#: Seconds between requests.
#:
#: Google stopped publishing free-tier RPM/TPM/RPD publicly — the rate-limits
#: page now redirects to a per-project dashboard
#: (https://aistudio.google.com/rate-limit). Since the real ceiling is unknown
#: and unknowable from here, the default is deliberately conservative: 6s
#: between calls is 10 RPM, comfortably under every historical free tier.
#: Lower it with --delay once you have checked your own dashboard.
DEFAULT_DELAY_SECONDS = float(os.environ.get("GEMINI_DELAY_SECONDS", "6.0"))

#: Backoff schedule for HTTP 429. Multiplied by attempt number.
BACKOFF_BASE_SECONDS = 20.0
MAX_RETRIES_ON_RATE_LIMIT = 4


def load_env() -> None:
    """Load repo-root .env if present. Real env vars always win."""
    if not DOTENV_PATH.is_file():
        return
    for line in DOTENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def api_key() -> str | None:
    load_env()
    return os.environ.get("GEMINI_API_KEY") or None


def redact(secret: str | None) -> str:
    """Never print a key in full — these scripts are run with output captured."""
    if not secret:
        return "(unset)"
    return f"{secret[:6]}…{secret[-4:]} ({len(secret)} chars)"


def scrub(text: object) -> str:
    """
    Remove the API key from any string before it is printed or logged.

    Applied at every site that renders an exception, because those strings come
    from a third-party SDK whose behaviour we do not control. Verified on
    2026-07-23 that google-genai does NOT echo the key in error messages or
    tracebacks — but "verified once" is not the same as "guaranteed", and a
    leaked key in a captured terminal log is unrecoverable.

    Cheap insurance: one string replace on a path that only runs on failure.
    """
    rendered = str(text)
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        secret = os.environ.get(name)
        if secret and len(secret) > 8 and secret in rendered:
            rendered = rendered.replace(secret, "<<REDACTED_API_KEY>>")
    return rendered


class RateLimiter:
    """
    Minimum-interval throttle with exponential backoff on 429.

    Simple by design: pre-generation is a few dozen sequential calls, so a
    token bucket would be more machinery than the problem deserves.
    """

    def __init__(self, delay_seconds: float = DEFAULT_DELAY_SECONDS) -> None:
        self.delay = delay_seconds
        self._last_call: float | None = None

    def wait(self) -> None:
        if self._last_call is None:
            self._last_call = time.monotonic()
            return
        elapsed = time.monotonic() - self._last_call
        remaining = self.delay - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_call = time.monotonic()

    @staticmethod
    def is_rate_limit_error(exc: Exception) -> bool:
        # Not scrubbed: this string is only matched against, never printed or
        # stored. Scrubbing here would be harmless but misleading — it would
        # imply this value reaches output.
        text = f"{type(exc).__name__} {exc}".lower()  # noqa: not-rendered
        return any(
            marker in text
            for marker in ("429", "resource_exhausted", "rate limit", "quota")
        )

    @staticmethod
    def backoff_seconds(attempt: int) -> float:
        return BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))


# --------------------------------------------------------------------------- #
# Reproducibility
# --------------------------------------------------------------------------- #


def prompt_hash(system_instruction: str, user_prompt: str, model: str) -> str:
    """
    Stable fingerprint of exactly what produced an entry.

    Recorded per entry so a reviewer can tell whether two entries came from the
    same prompt, and so a prompt change is visible as a hash change rather than
    having to be remembered.
    """
    digest = hashlib.sha256()
    for part in (model, system_instruction, user_prompt):
        digest.update(part.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Terminal output
# --------------------------------------------------------------------------- #

_USE_COLOUR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOUR else text


def green(t: str) -> str:
    return _c("32", t)


def red(t: str) -> str:
    return _c("31", t)


def yellow(t: str) -> str:
    return _c("33", t)


def bold(t: str) -> str:
    return _c("1", t)


def dim(t: str) -> str:
    return _c("2", t)


def rule(title: str = "", width: int = 78) -> str:
    if not title:
        return "─" * width
    return f"── {title} " + "─" * max(0, width - len(title) - 4)


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    fatal: bool = True

    @property
    def marker(self) -> str:
        if self.passed:
            return green("PASS")
        return red("FAIL") if self.fatal else yellow("WARN")


def print_check_table(checks: list[CheckResult]) -> bool:
    """Render a PASS/FAIL/WARN table. Returns True if no fatal check failed."""
    width = max((len(c.name) for c in checks), default=10) + 2
    print(rule("preflight"))
    for check in checks:
        print(f"  {check.marker}  {check.name.ljust(width)} {dim(check.detail)}")
    print(rule())

    fatal_failures = [c for c in checks if not c.passed and c.fatal]
    warnings = [c for c in checks if not c.passed and not c.fatal]

    if fatal_failures:
        print(red(f"\n{len(fatal_failures)} check(s) FAILED:"))
        for check in fatal_failures:
            print(red(f"  · {check.name}: {check.detail}"))
    if warnings:
        print(yellow(f"\n{len(warnings)} warning(s):"))
        for check in warnings:
            print(yellow(f"  · {check.name}: {check.detail}"))
    if not fatal_failures:
        print(green("\nAll required checks passed."))
    return not fatal_failures


# --------------------------------------------------------------------------- #
# JSONL logging
# --------------------------------------------------------------------------- #


def append_jsonl(path: Path, record: dict) -> None:
    """Append one record. Never raises — logging must not fail a generation."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass


def read_jsonl(path: Path) -> Iterator[dict]:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def load_json(path: Path, default: dict | None = None) -> dict:
    if not path.is_file():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default if default is not None else {}


def write_json_atomic(path: Path, payload: dict) -> None:
    """
    Write via a temp file + rename.

    Pre-generation writes after every single case so a rate-limit stop never
    loses work; a non-atomic write interrupted mid-flush would corrupt the file
    it is trying to protect.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)
