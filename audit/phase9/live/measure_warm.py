#!/usr/bin/env python3
"""
Phase 9 A3 — warm measurements against an API base URL.

Paced to the deployed rate limit (10 uploads / 300 s per client key), so a
429 here is a finding, not self-inflicted noise. Every request is logged with
its UTC start, status and wall time to <out>/requests.jsonl; S1-S6 bodies are
saved for the field-by-field diff against a local run.

    python audit/phase9/live/measure_warm.py --base https://... --out DIR --phase all
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
import run_demo  # noqa: E402  (SCENARIOS is the single source of S1-S6)

DEMO = REPO / "test-data" / "demo"


def _multipart(vcf: Path, drugs: str | None) -> tuple[bytes, str]:
    boundary = f"----phase9{uuid.uuid4().hex}"
    parts = [
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{vcf.name}"\r\n'
        "Content-Type: text/plain\r\n\r\n".encode(),
        vcf.read_bytes(),
        b"\r\n",
    ]
    if drugs is not None:
        parts += [
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="drugs"\r\n\r\n',
            drugs.encode(),
            b"\r\n",
        ]
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), boundary


def post(base: str, path: str, vcf: Path, drugs: str | None, log: Path,
         label: str, timeout: float = 300) -> dict:
    body, boundary = _multipart(vcf, drugs)
    req = urllib.request.Request(
        f"{base}{path}", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    started_utc = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    t0 = time.monotonic()
    status, payload, err, headers = 0, None, "", {}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            headers = dict(resp.headers)
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        status = exc.code
        headers = dict(exc.headers or {})
        raw = exc.read()
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {"raw": raw.decode("utf-8", "replace")[:500]}
    except Exception as exc:  # noqa: BLE001 — a timeout is a result to record
        err = f"{type(exc).__name__}: {exc}"
    elapsed = time.monotonic() - t0
    record = {
        "label": label, "path": path, "vcf": vcf.name, "drugs": drugs,
        "started_utc": started_utc, "status": status,
        "seconds": round(elapsed, 3), "error": err,
        "retry_after": headers.get("Retry-After") or headers.get("retry-after"),
        "error_code": (payload or {}).get("error_code") if isinstance(payload, dict) else None,
        "server_processing_ms": ((payload or {}).get("quality_metrics") or {}).get(
            "processing_time_ms") if isinstance(payload, dict) else None,
    }
    with log.open("a") as fh:
        fh.write(json.dumps(record) + "\n")
    print(json.dumps(record), flush=True)
    return {"record": record, "body": payload}


def pct(values: list[float], q: float) -> float:
    """Nearest-rank percentile; with n=5, p95 is the maximum."""
    ordered = sorted(values)
    rank = max(1, int(-(-q * len(ordered) // 1)))  # ceil(q*n)
    return ordered[min(rank, len(ordered)) - 1]


def wait_for_budget(first_hit: float, window: float = 305) -> None:
    remaining = first_hit + window - time.monotonic()
    if remaining > 0:
        print(f"[pace] sleeping {remaining:.0f}s for the rate-limit window", flush=True)
        time.sleep(remaining)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--phase", choices=["latency", "scenarios", "queue", "all"],
                    default="all")
    ap.add_argument("--no-pace", action="store_true",
                    help="local runs: loopback is exempt from the rate limit")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    log = out / "requests.jsonl"
    summary: dict = {"base": args.base}
    confident = DEMO / "demo_confident.vcf"

    if args.phase in ("latency", "all"):
        first = time.monotonic()
        cov = [post(args.base, "/coverage", confident, None, log, f"coverage-{i}")
               for i in range(1, 6)]
        ana = [post(args.base, "/analyze", confident, "clopidogrel", log, f"analyze-{i}")
               for i in range(1, 6)]
        cov_s = [r["record"]["seconds"] for r in cov if r["record"]["status"] == 200]
        ana_s = [r["record"]["seconds"] for r in ana if r["record"]["status"] == 200]
        summary["coverage"] = {
            "n_ok": len(cov_s), "n": len(cov), "seconds": cov_s,
            "p50": statistics.median(cov_s) if cov_s else None,
        }
        summary["analyze"] = {
            "n_ok": len(ana_s), "n": len(ana), "seconds": ana_s,
            "p50": statistics.median(ana_s) if ana_s else None,
            "p95_nearest_rank": pct(ana_s, 0.95) if ana_s else None,
            "note": "n=5: nearest-rank p95 equals the maximum",
        }
        if not args.no_pace:
            wait_for_budget(first)

    if args.phase in ("scenarios", "all"):
        first = time.monotonic()
        sdir = out / "s1-s6"
        sdir.mkdir(exist_ok=True)
        results = {}
        for sc in run_demo.SCENARIOS:
            r = post(args.base, "/analyze", DEMO / sc.vcf, sc.drugs, log, sc.key)
            (sdir / f"{sc.key}.json").write_text(json.dumps(r["body"], indent=2, sort_keys=True))
            labels = {a["drug"]: a["risk_assessment"]["risk_label"]
                      for a in (r["body"] or {}).get("analyses", [])} if isinstance(r["body"], dict) else {}
            results[sc.key] = {"status": r["record"]["status"], "labels": labels,
                               "expect": sc.expect}
        summary["scenarios"] = results
        if not args.no_pace:
            wait_for_budget(first)

    if args.phase in ("queue", "all"):
        # Two at once: the second must wait for the single PharmCAT slot.
        with cf.ThreadPoolExecutor(max_workers=2) as pool:
            futs = [pool.submit(post, args.base, "/analyze", confident, "clopidogrel",
                                log, f"queue-{i}") for i in (1, 2)]
            q = [f.result()["record"] for f in futs]
        summary["queue"] = q

    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
