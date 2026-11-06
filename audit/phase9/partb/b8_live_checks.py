#!/usr/bin/env python3
"""
B8 after deploy: criteria L4-i to iii and L5 of audit/phase9/B8.log ("Push and live check").

    b8_live_checks.py limit VERDICT.json          L4: eleven /coverage uploads, then a forged
                                                  CF-Connecting-IP, then a forged X-Forwarded-For
    b8_live_checks.py one-at-a-time VERDICT.json  L5: a /coverage while one /analyze of S1 runs

Records statuses, error codes, Retry-After and timings only, never an address.
Exits 0 only when every check passes.
"""

from __future__ import annotations

import json
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BASE = "https://pharmaguard-api-baml.onrender.com"
# Cloudflare refuses Python-urllib's default User-Agent (B5.log); name the client plainly.
AGENT = "curl/8.7.1 (phase9-audit)"
VCF = REPO / "test-data/demo/demo_confident.vcf"
FORGED_EDGE = {"CF-Connecting-IP": "192.0.2.77"}  # TEST-NET-1
FORGED_XFF = {"X-Forwarded-For": "192.0.2.78"}


def _multipart(drugs: str | None) -> tuple[bytes, str]:
    boundary = f"----phase9{uuid.uuid4().hex}"
    parts = [f"--{boundary}\r\n".encode(),
             f'Content-Disposition: form-data; name="file"; filename="{VCF.name}"\r\n'
             "Content-Type: text/plain\r\n\r\n".encode(), VCF.read_bytes(), b"\r\n"]
    if drugs is not None:
        parts += [f"--{boundary}\r\n".encode(), b'Content-Disposition: form-data; name="drugs"\r\n\r\n',
                  drugs.encode(), b"\r\n"]
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), boundary


def upload(path: str, drugs: str | None = None, extra: dict[str, str] | None = None,
           timeout: float = 400) -> dict:
    body, boundary = _multipart(drugs)
    req = urllib.request.Request(f"{BASE}{path}", data=body, method="POST", headers={
        "User-Agent": AGENT, "Content-Type": f"multipart/form-data; boundary={boundary}", **(extra or {})})
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, headers, raw = resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as exc:
        status, headers, raw = exc.code, exc.headers, exc.read()
    try:
        payload = json.loads(raw)
    except ValueError:
        payload = None
    return {"path": path, "forged": sorted(extra or {}), "status": status,
            "error_code": payload.get("error_code") if isinstance(payload, dict) else None,
            "retry_after": headers.get("Retry-After") if headers else None,
            "json": isinstance(payload, dict), "seconds": round(time.monotonic() - started, 2)}


def limit() -> tuple[dict, dict]:
    origin = time.monotonic()
    rows = []
    for extra in [None] * 11 + [FORGED_EDGE, FORGED_XFF]:
        at = round(time.monotonic() - origin, 2)
        rows.append({"n": len(rows) + 1, "at": at, **upload("/coverage", extra=extra)})
        print(json.dumps(rows[-1]), flush=True)
    eleventh_done = rows[10]["at"] + rows[10]["seconds"]
    checks = {
        "L4-i the eleventh gets 429, within 300 s": rows[10]["status"] == 429 and eleventh_done < 300,
        "L4-i (expected) the first ten answer 200": [r["status"] for r in rows[:10]] == [200] * 10,
        "L4-ii forged CF-Connecting-IP: still 429": rows[11]["status"] == 429,
        "L4-iii forged X-Forwarded-For: still 429": rows[12]["status"] == 429,
    }
    return checks, {"requests": rows, "eleventh_done_seconds": round(eleventh_done, 2)}


def one_at_a_time() -> tuple[dict, dict]:
    first: dict = {}
    analysis = threading.Thread(target=lambda: first.update(upload("/analyze", drugs="clopidogrel")))
    analysis.start()
    time.sleep(8)  # the S1 upload has arrived; on Render an analysis takes about a minute
    second = upload("/coverage")
    print(json.dumps({"second": second}), flush=True)
    analysis.join()
    print(json.dumps({"first": first}), flush=True)
    checks = {
        "L5 /coverage during the analysis: 429 ONE_AT_A_TIME with Retry-After":
            second["status"] == 429 and second["error_code"] == "ONE_AT_A_TIME" and bool(second["retry_after"]),
        "L5 (recorded) the analysis itself answers 200": first.get("status") == 200,
    }
    return checks, {"first_analyze": first, "second_coverage": second}


def main() -> int:
    kind, verdict = sys.argv[1], Path(sys.argv[2])
    run = {"limit": limit, "one-at-a-time": one_at_a_time}[kind]
    started_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    checks, evidence = run()
    verdict.write_text(json.dumps({"check": kind, "base": BASE, "started_utc": started_utc,
                                   "checks": checks, "all_pass": all(checks.values()), **evidence}, indent=1) + "\n")
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
