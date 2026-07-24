#!/usr/bin/env python3
"""
List the models a provider's key can actually see.

    python scripts/list_models.py                       # the configured provider
    python scripts/list_models.py --provider nvidia     # NVIDIA NIM catalogue
    python scripts/list_models.py --provider nvidia --grep instruct --json
    python scripts/list_models.py --provider nvidia --probe-json llama-3.3-70b-instruct

WHY THIS EXISTS
    Model ids change often, and any id written from memory is a guess with a
    shelf life. Nothing in this project hardcodes one in application source: the
    provider layer resolves `LLM_MODEL` from the environment, and every CLI takes
    `--model`. This script is how you discover what to put there — from the
    provider's own catalogue, not from anyone's recollection.

WHAT THE API DOES AND DOESN'T TELL YOU
    An id list is available live. **Credit-free vs credit-consuming is not** —
    neither NVIDIA's nor Google's model endpoint returns pricing, so this script
    refuses to guess it. It points you at the provider's own catalogue page for
    that, and (with --probe-json) will spend one tiny call to check whether a
    model honours JSON output, because that is checkable and worth knowing before
    a benchmark.

COST
    Listing is a metadata call — no token quota, though it counts as a request.
    `--probe-json` makes one minimal generation per named model (a few tokens).
"""

from __future__ import annotations

import argparse
import json
import sys

from _common import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    PROVIDER_KEY_ENV,
    api_key,
    bold,
    dim,
    green,
    red,
    rule,
    scrub,
    yellow,
)

#: The provider catalogue pages where credit/pricing actually lives. Printed, not
#: scraped — the page is JS-rendered and its shape is not a stable contract.
CATALOGUE_URLS = {
    "nvidia": "https://build.nvidia.com/models",
    "gemini": "https://ai.google.dev/gemini-api/docs/models",
}


def _nvidia_models(key: str) -> list[dict]:
    from openai import OpenAI

    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key)
    out = []
    for model in client.models.list():
        out.append({
            "id": model.id,
            "owned_by": getattr(model, "owned_by", "") or "",
            "created": getattr(model, "created", None),
        })
    return out


def _gemini_models(key: str, include_all: bool) -> list[dict]:
    from google import genai

    client = genai.Client(api_key=key)
    out = []
    for model in client.models.list():
        name = model.name.replace("models/", "")
        actions = list(getattr(model, "supported_actions", None) or [])
        if not include_all and actions and "generateContent" not in actions:
            continue
        out.append({
            "id": name,
            "owned_by": "google",
            "display_name": getattr(model, "display_name", "") or "",
            "supported_actions": actions,
        })
    return out


def _probe_json(provider: str, key: str, model: str) -> str:
    """
    One minimal call to see whether the model returns a JSON object.

    Returns "response_format" / "prompt_enforced" / "no" / "error: …". Kept tiny
    (a handful of tokens) so probing a shortlist costs almost nothing.
    """
    if provider != "nvidia":
        return "n/a"
    from openai import OpenAI

    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key)
    prompt = 'Return a JSON object: {"ok": "yes"}. Only the object.'
    # Native JSON mode first.
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=40,
            temperature=0,
        )
        text = (r.choices[0].message.content or "").strip()
        if _looks_like_json(text):
            return "response_format"
    except Exception as exc:  # noqa: BLE001
        low = scrub(exc).lower()
        if "response_format" not in low and "json" not in low:
            return f"error: {scrub(exc)[:40]}"
    # Prompt-enforced fallback.
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=40,
            temperature=0,
        )
        text = (r.choices[0].message.content or "").strip()
        return "prompt_enforced" if _looks_like_json(text) else "no"
    except Exception as exc:  # noqa: BLE001
        return f"error: {scrub(exc)[:40]}"


def _looks_like_json(text: str) -> bool:
    from app.explanation.providers.json_output import extract_json_text

    candidate = extract_json_text(text)
    if not candidate:
        return False
    try:
        json.loads(candidate)
        return True
    except json.JSONDecodeError:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, help=f"nvidia|gemini (default {DEFAULT_PROVIDER}).")
    parser.add_argument("--all", action="store_true", help="Gemini: include non-generateContent models.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    parser.add_argument("--grep", default="", help="Only ids containing this substring.")
    parser.add_argument("--probe-json", nargs="*", default=None, metavar="MODEL",
                        help="Probe these model ids for JSON support (one tiny call each). "
                             "No ids = probe all listed.")
    args = parser.parse_args(argv)

    provider = args.provider.strip().lower()
    if provider not in ("nvidia", "gemini"):
        print(red(f"list_models supports nvidia|gemini, not {provider!r}."), file=sys.stderr)
        return 2

    key = api_key(provider)
    key_env = PROVIDER_KEY_ENV.get(provider, "")
    if not key:
        print(red(f"{key_env} is not set."), file=sys.stderr)
        print("Put it in repo-root .env (gitignored) or export it.", file=sys.stderr)
        return 2

    try:
        models = _nvidia_models(key) if provider == "nvidia" else _gemini_models(key, args.all)
    except ImportError as exc:
        print(red(f"SDK missing: {scrub(exc)}. pip install -r backend/requirements-llm.txt"), file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(red(f"Could not list models: {type(exc).__name__}: {scrub(exc)}"), file=sys.stderr)
        return 1

    if args.grep:
        models = [m for m in models if args.grep.lower() in m["id"].lower()]
    models.sort(key=lambda m: m["id"])

    probes: dict[str, str] = {}
    if args.probe_json is not None:
        targets = args.probe_json or [m["id"] for m in models]
        for model_id in targets:
            probes[model_id] = _probe_json(provider, key, model_id)

    if args.json:
        print(json.dumps({
            "provider": provider,
            "count": len(models),
            "models": [{**m, "json_mode": probes.get(m["id"])} for m in models],
            "credit_free": "not available via API — see " + CATALOGUE_URLS.get(provider, ""),
        }, indent=1))
        return 0

    print(rule(f"{len(models)} model(s) visible to this {provider} key"))
    width = max((len(m["id"]) for m in models), default=20) + 2
    for m in models:
        marker = green(" *") if m["id"] == DEFAULT_MODEL else "  "
        extra = dim(f"  {m.get('owned_by', '')}")
        if m["id"] in probes:
            extra += "  " + _fmt_probe(probes[m["id"]])
        print(f"{marker} {bold(m['id'].ljust(width))}{extra}")
    print(rule())

    print(yellow("\nCredit-free vs credit-consuming is NOT returned by the API."))
    print(dim(f"  Check the provider catalogue: {CATALOGUE_URLS.get(provider, '')}"))
    print(dim("  Then benchmark a shortlist: python scripts/benchmark_models.py --models <a,b,c>"))
    return 0


def _fmt_probe(verdict: str) -> str:
    if verdict in ("response_format", "prompt_enforced"):
        return green(f"json:{verdict}")
    if verdict == "no":
        return red("json:no")
    return yellow(verdict)


if __name__ == "__main__":
    raise SystemExit(main())
