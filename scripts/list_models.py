#!/usr/bin/env python3
"""
List the Gemini models this API key can actually see.

WHY THIS EXISTS
    Model ids change often, and any id written from memory is a guess with a
    shelf life. Nothing in this project hardcodes one in application source:
    `_common.DEFAULT_MODEL` reads `GEMINI_MODEL` from the environment, and every
    CLI accepts `--model`. This script is how you discover what to put there.

USAGE
    python scripts/list_models.py                 # generateContent models
    python scripts/list_models.py --all           # everything, incl. embed/TTS
    python scripts/list_models.py --json          # machine-readable
    python scripts/list_models.py --grep flash    # filter by substring

COST
    `models.list()` is a metadata call. It consumes no token quota, though it
    does count as an API request.
"""

from __future__ import annotations

import argparse
import json
import sys

from _common import (
    DEFAULT_MODEL,
    api_key,
    bold,
    dim,
    green,
    red,
    rule,
    scrub,
    yellow,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true", help="Include non-generateContent models.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    parser.add_argument("--grep", default="", help="Only models whose id contains this.")
    args = parser.parse_args(argv)

    key = api_key()
    if not key:
        print(red("GEMINI_API_KEY is not set."), file=sys.stderr)
        print("Put it in the repo-root .env (gitignored) or export it.", file=sys.stderr)
        return 2

    try:
        from google import genai
    except ImportError:
        print(red("google-genai is not installed."), file=sys.stderr)
        print("  pip install -r backend/requirements-llm.txt", file=sys.stderr)
        return 2

    try:
        client = genai.Client(api_key=key)
        models = list(client.models.list())
    except Exception as exc:  # noqa: BLE001 — SDK raises a wide range
        print(red(f"Could not list models: {type(exc).__name__}: {scrub(exc)}"), file=sys.stderr)
        return 1

    rows = []
    for model in models:
        name = model.name.replace("models/", "")
        actions = list(getattr(model, "supported_actions", None) or [])
        if not args.all and actions and "generateContent" not in actions:
            continue
        if args.grep and args.grep.lower() not in name.lower():
            continue
        rows.append(
            {
                "id": name,
                "display_name": getattr(model, "display_name", "") or "",
                "supported_actions": actions,
                "input_token_limit": getattr(model, "input_token_limit", None),
                "output_token_limit": getattr(model, "output_token_limit", None),
            }
        )
    rows.sort(key=lambda r: r["id"])

    if args.json:
        print(json.dumps({"count": len(rows), "models": rows}, indent=1))
        return 0

    print(rule(f"{len(rows)} model(s) visible to this key"))
    width = max((len(r["id"]) for r in rows), default=20) + 2
    for row in rows:
        marker = green(" *") if row["id"] == DEFAULT_MODEL else "  "
        limits = ""
        if row["input_token_limit"]:
            limits = dim(f"  in≤{row['input_token_limit']:,} out≤{row['output_token_limit'] or 0:,}")
        print(f"{marker} {bold(row['id'].ljust(width))}{row['display_name'][:34]}{limits}")
    print(rule())

    configured_ok = any(r["id"] == DEFAULT_MODEL for r in rows)
    print(f"\nConfigured model (GEMINI_MODEL, default): {bold(DEFAULT_MODEL)}")
    if configured_ok:
        print(green("  ✓ present in this key's model list"))
    else:
        print(yellow("  ! NOT in this key's list — set GEMINI_MODEL or pass --model"))

    # Free-tier status is per-project and not exposed by the API, so say so
    # rather than inventing a column for it.
    print(
        dim(
            "\nFree-tier eligibility and RPM/TPM/RPD are not returned by this API.\n"
            "Google publishes them per-project at https://aistudio.google.com/rate-limit\n"
            "— check there before a large run. The generation CLI throttles\n"
            "conservatively by default (see --delay)."
        )
    )
    return 0 if configured_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
