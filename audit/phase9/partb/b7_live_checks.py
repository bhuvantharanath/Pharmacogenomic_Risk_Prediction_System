#!/usr/bin/env python3
"""
B7 after deploy: criteria L4 (a-c) and L5 of audit/phase9/B7.log ("Push and live check").

    b7_live_checks.py cors SHA VERDICT.json
    b7_live_checks.py bundle SHA VERDICT.json

No uploads: /health, /provenance and preflights only, so the rate limit is not
touched. Exits 0 only when every check passes.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://pharmaguard-api-baml.onrender.com"
WEB = "https://pharmaguard-web.pages.dev"
PRODUCTION = "https://pharmaguard-web.pages.dev"
PREVIEW = "https://6bc16810.pharmaguard-web.pages.dev"
EVIL = "https://evil.example"
# Cloudflare refuses Python-urllib's default User-Agent (B5.log); name the client plainly.
AGENT = "curl/8.7.1 (phase9-audit)"
CLIENT_TEXT = ("This page cannot use the analysis server", "This file was not analysed")


def _request(method: str, path: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(f"{BASE}{path}", method=method, headers={"User-Agent": AGENT, **headers})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in (exc.headers or {}).items()}, exc.read()


def cors(sha: str, verdict: Path) -> int:
    checks, seen = {}, {}
    status, headers, body = _request("GET", "/health", {"Origin": PRODUCTION})
    health = json.loads(body)
    _, _, prov_body = _request("GET", "/provenance", {})
    provenance = json.loads(prov_body)
    seen["health_production"] = {"status": status, "acao": headers.get("access-control-allow-origin"), "body": health}
    checks["a production origin reads /health"] = status == 200 and headers.get("access-control-allow-origin") == "*"
    checks["a origin_allowed true for production"] = health.get("origin_allowed") is True
    checks["a commit is the pushed one"] = health.get("commit") == sha
    keys = ("cpic_guidance_sha256", "allele_definitions_sha256", "allele_definitions_version")
    checks["a data identity equals /provenance"] = all(
        health.get("data", {}).get(k) and health["data"][k] == provenance.get(k) for k in keys)

    status, headers, _ = _request("OPTIONS", "/analyze", {
        "Origin": PREVIEW, "Access-Control-Request-Method": "POST"})
    seen["preflight_preview"] = {"status": status, "acao": headers.get("access-control-allow-origin")}
    checks["b the F-11 preview origin may call /analyze"] = (
        status == 200 and headers.get("access-control-allow-origin") == PREVIEW)

    status, headers, body = _request("GET", "/health", {"Origin": EVIL})
    seen["health_evil"] = {"status": status, "acao": headers.get("access-control-allow-origin"),
                           "origin_allowed": json.loads(body).get("origin_allowed")}
    checks["c a refused origin still reads /health"] = status == 200 and headers.get("access-control-allow-origin") == "*"
    checks["c and is told it is refused"] = json.loads(body).get("origin_allowed") is False
    status, headers, _ = _request("OPTIONS", "/analyze", {"Origin": EVIL, "Access-Control-Request-Method": "POST"})
    seen["preflight_evil"] = {"status": status, "acao": headers.get("access-control-allow-origin")}
    checks["c its /analyze preflight is refused"] = status == 400 and "access-control-allow-origin" not in headers

    ok = all(checks.values())
    verdict.write_text(json.dumps({"checks": checks, "all_pass": ok, "seen": seen}, indent=1) + "\n")
    print(f"cors live checks: {sum(checks.values())}/{len(checks)} pass")
    return 0 if ok else 1


def bundle(sha: str, verdict: Path) -> int:
    req = urllib.request.Request(f"{WEB}/main.dart.js?b7={sha[:7]}",
                                 headers={"Cache-Control": "no-cache", "User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        js = resp.read().decode("utf-8", "replace")
    checks = {"bundle contains EXPECTED_BACKEND_SHA": sha in js}
    for text in CLIENT_TEXT:
        checks[f"bundle contains {text!r}"] = text in js
    ok = all(checks.values())
    verdict.write_text(json.dumps({"checks": checks, "all_pass": ok, "bundle_bytes": len(js)}, indent=1) + "\n")
    print(f"bundle live checks: {sum(checks.values())}/{len(checks)} pass")
    return 0 if ok else 1


def main() -> int:
    command, sha, verdict = sys.argv[1:4]
    if command == "cors":
        return cors(sha, Path(verdict))
    if command == "bundle":
        return bundle(sha, Path(verdict))
    raise SystemExit(f"unknown command {command}")


if __name__ == "__main__":
    sys.exit(main())
