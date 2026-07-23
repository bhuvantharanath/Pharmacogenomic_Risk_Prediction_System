#!/usr/bin/env python3
"""
Preflight checks — run this before any generation.

Verifies every dependency the pre-generation pipeline needs, and fails loudly
rather than half-way through a paid run. Exits non-zero if any required check
fails, so it can gate a CI job or a shell `&&` chain.

    python scripts/preflight.py
    python scripts/preflight.py --skip-auth     # no API call at all
    python scripts/preflight.py --json

WHAT IS FATAL vs A WARNING
    Fatal:   anything that would make generation fail or produce junk — no key,
             a key that does not authenticate, an unparseable label mapping, a
             missing corpus.
    Warning: things that matter for reproducibility but do not block a run —
             a dirty git tree, PharmCAT absent (only needed to regenerate the
             CPIC fixtures, not to generate prose from existing ones).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from _common import (
    CASE_MATRIX_PATH,
    DEFAULT_DELAY_SECONDS,
    DEFAULT_MODEL,
    DOTENV_PATH,
    EXPLANATIONS_PATH,
    REPO_ROOT,
    CheckResult,
    api_key,
    bold,
    dim,
    print_check_table,
    redact,
)


def check_dotenv_gitignored() -> CheckResult:
    """
    A committed .env is the single worst outcome of this phase.

    Checked with `git check-ignore` rather than by reading .gitignore, because
    only git can tell you what git will actually do.
    """
    if not DOTENV_PATH.is_file():
        return CheckResult(
            ".env gitignored",
            True,
            "no .env file (key must come from the environment)",
            fatal=False,
        )
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(DOTENV_PATH)],
            cwd=REPO_ROOT,
            capture_output=True,
        )
        ignored = result.returncode == 0
    except (OSError, subprocess.SubprocessError) as exc:
        return CheckResult(".env gitignored", False, f"could not ask git: {exc}")

    if not ignored:
        return CheckResult(
            ".env gitignored",
            False,
            "*** .env EXISTS AND IS NOT IGNORED — DO NOT COMMIT. Add '.env' to .gitignore ***",
        )

    # Also make sure it was never committed in the past.
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(DOTENV_PATH)],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    if tracked.returncode == 0:
        return CheckResult(
            ".env gitignored",
            False,
            "*** .env is TRACKED by git despite being ignored — it is already in history ***",
        )
    return CheckResult(".env gitignored", True, "present, ignored, and untracked")


def check_key_present() -> CheckResult:
    key = api_key()
    if not key:
        return CheckResult(
            "GEMINI_API_KEY",
            False,
            "not set — put it in repo-root .env or export it",
        )
    return CheckResult("GEMINI_API_KEY", True, f"present {redact(key)}")


def check_backend_env_absent() -> CheckResult:
    """
    backend/.env would break the server, not just leak.

    `app/security.py::assert_no_baked_secrets` refuses to start if it finds one,
    on the grounds that inside a deployed image it could only be a leaked
    credential. Build-time secrets therefore live at the repo root.
    """
    backend_env = REPO_ROOT / "backend" / ".env"
    if backend_env.is_file():
        return CheckResult(
            "backend/.env absent",
            False,
            "backend/.env exists — the API refuses to start with it. Move it to the repo root",
        )
    return CheckResult("backend/.env absent", True, "correct (secrets live at repo root)")


def check_auth(model: str) -> CheckResult:
    """Cheapest possible live call: list models. No token quota consumed."""
    key = api_key()
    if not key:
        return CheckResult("API authenticates", False, "no key to test")
    try:
        from google import genai
    except ImportError:
        return CheckResult(
            "API authenticates",
            False,
            "google-genai not installed — pip install -r backend/requirements-llm.txt",
        )
    try:
        client = genai.Client(api_key=key)
        available = [m.name.replace("models/", "") for m in client.models.list()]
    except Exception as exc:  # noqa: BLE001
        return CheckResult("API authenticates", False, f"{type(exc).__name__}: {str(exc)[:120]}")

    if model not in available:
        return CheckResult(
            "API authenticates",
            False,
            f"authenticated ({len(available)} models) but {model!r} is NOT among them",
        )
    return CheckResult(
        "API authenticates", True, f"{len(available)} models visible; {model} present"
    )


def check_pharmcat() -> CheckResult:
    """
    Only needed to regenerate CPIC fixtures, so a warning rather than fatal.

    Generation itself reads CPIC text from the checked-in report fixtures.
    """
    executable = os.environ.get("PHARMCAT_PIPELINE", "pharmcat_pipeline")
    path = shutil.which(executable)
    if path:
        return CheckResult("PharmCAT invokable", True, path)
    return CheckResult(
        "PharmCAT invokable",
        False,
        f"{executable!r} not on PATH — fine for generation (fixtures are checked in), "
        "needed only to regenerate them",
        fatal=False,
    )


def check_corpus() -> CheckResult:
    try:
        from app.retrieval import all_documents

        documents = all_documents()
    except Exception as exc:  # noqa: BLE001
        return CheckResult("Mechanism corpus", False, f"{type(exc).__name__}: {exc}")

    if not documents:
        return CheckResult("Mechanism corpus", False, "no documents parsed from rag-corpus/mechanisms")
    missing = [d.drug for d in documents if not d.source_guideline]
    if missing:
        return CheckResult("Mechanism corpus", False, f"missing provenance: {missing}")
    return CheckResult(
        "Mechanism corpus", True, f"{len(documents)} documents, all with provenance"
    )


def check_label_mapping() -> CheckResult:
    try:
        from app.cpic_engine import load_mapping

        mapping = load_mapping()
    except Exception as exc:  # noqa: BLE001
        return CheckResult("label_mapping.yaml", False, f"{type(exc).__name__}: {exc}")
    rules = mapping.get("risk_label_rules") or []
    if not rules:
        return CheckResult("label_mapping.yaml", False, "parsed but declares no rules")
    return CheckResult("label_mapping.yaml", True, f"{len(rules)} rules parsed")


def check_fixtures() -> CheckResult:
    fixtures = sorted((REPO_ROOT / "backend" / "tests" / "fixtures").glob("pharmcat_report_*.json"))
    if not fixtures:
        return CheckResult(
            "PharmCAT fixtures", False, "no report fixtures — generation has no CPIC text to ground on"
        )
    return CheckResult(
        "PharmCAT fixtures", True, f"{len(fixtures)}: {', '.join(f.stem for f in fixtures)}"
    )


def check_git_clean() -> CheckResult:
    """Warning only — you may legitimately be mid-edit."""
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True
        )
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return CheckResult("git tree clean", False, f"could not run git: {exc}", fatal=False)

    dirty = [ln for ln in status.stdout.splitlines() if ln.strip()]
    if dirty:
        return CheckResult(
            "git tree clean",
            False,
            f"on {branch!r} with {len(dirty)} uncommitted change(s) — generation output "
            "will be hard to attribute",
            fatal=False,
        )
    return CheckResult("git tree clean", True, f"clean on {branch!r}")


def check_case_matrix() -> CheckResult:
    """Warning — enumerate_cases.py produces it, and runs before generation."""
    if not CASE_MATRIX_PATH.is_file():
        return CheckResult(
            "case_matrix.json",
            False,
            "not generated yet — run scripts/enumerate_cases.py",
            fatal=False,
        )
    try:
        payload = json.loads(CASE_MATRIX_PATH.read_text())
        cases = payload.get("cases") or []
        reachable = [c for c in cases if c.get("reachable")]
    except (json.JSONDecodeError, OSError) as exc:
        return CheckResult("case_matrix.json", False, f"unreadable: {exc}", fatal=False)
    return CheckResult(
        "case_matrix.json", True, f"{len(reachable)} reachable of {len(cases)} enumerated"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model to verify (default {DEFAULT_MODEL}).")
    parser.add_argument("--skip-auth", action="store_true", help="Do not make any API call.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    args = parser.parse_args(argv)

    checks: list[CheckResult] = [
        check_key_present(),
        check_dotenv_gitignored(),
        check_backend_env_absent(),
    ]
    if args.skip_auth:
        checks.append(CheckResult("API authenticates", True, "skipped (--skip-auth)", fatal=False))
    else:
        checks.append(check_auth(args.model))
    checks += [
        check_pharmcat(),
        check_corpus(),
        check_label_mapping(),
        check_fixtures(),
        check_case_matrix(),
        check_git_clean(),
    ]

    if args.json:
        print(
            json.dumps(
                {
                    "passed": all(c.passed for c in checks if c.fatal),
                    "model": args.model,
                    "checks": [
                        {"name": c.name, "passed": c.passed, "detail": c.detail, "fatal": c.fatal}
                        for c in checks
                    ],
                },
                indent=1,
            )
        )
        return 0 if all(c.passed for c in checks if c.fatal) else 1

    print(bold("\nPharmaGuard preflight"))
    print(dim(f"model={args.model}  throttle={DEFAULT_DELAY_SECONDS}s ({60 / DEFAULT_DELAY_SECONDS:.0f} RPM)\n"))
    ok = print_check_table(checks)

    if ok:
        print(dim("\nNext:  python scripts/enumerate_cases.py"))
        print(dim("Then:  python scripts/pregenerate_explanations.py --dry-run"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
