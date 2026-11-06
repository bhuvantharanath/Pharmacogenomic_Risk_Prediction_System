#!/usr/bin/env python3
"""
B10 after deploy: criteria L4 and L5 of audit/phase9/B10.log ("Push and live check").

    b10_live_checks.py codeine VERDICT.json      L4: NA12273 with codeine, without and with a supplied CYP2D6 call
    b10_live_checks.py bundle SHA VERDICT.json   L5: the deployed web bundle carries the commit and the new strings

The codeine check makes two uploads, one after another. Exits 0 only when every check passes.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BASE = "https://pharmaguard-api-baml.onrender.com"
WEB = "https://pharmaguard-web.pages.dev"
# Cloudflare refuses Python-urllib's default User-Agent (B5.log); name the client plainly.
AGENT = "curl/8.7.1 (phase9-audit)"
VCF = REPO / "test-data/demo/demo_na12273_1000g.vcf"
PM_TEXT = ("Avoid codeine use because of possibility of diminished analgesia. If opioid use is warranted, "
           "consider a non-tramadol opioid.")
WARNING = "CYP2D6 *4/*4 supplied by Cyrius, not called by PharmaGuard."
CLIENT_TEXT = ("CYP2D6 from a dedicated caller", "not called by PharmaGuard")


def analyze(fields: dict[str, str]) -> tuple[int, dict]:
    boundary = f"----phase9{uuid.uuid4().hex}"
    parts = [f"--{boundary}\r\n".encode(),
             f'Content-Disposition: form-data; name="file"; filename="{VCF.name}"\r\n'
             "Content-Type: text/plain\r\n\r\n".encode(), VCF.read_bytes(), b"\r\n"]
    for name, value in fields.items():
        parts += [f"--{boundary}\r\n".encode(),
                  f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(), value.encode(), b"\r\n"]
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(f"{BASE}/analyze", data=b"".join(parts), method="POST", headers={
        "User-Agent": AGENT, "Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=400) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


def codeine(verdict: Path) -> int:
    runs = {}
    for name, fields in (("without", {"drugs": "codeine"}),
                         ("with", {"drugs": "codeine", "cyp2d6_diplotype": "*4/*4", "cyp2d6_caller": "Cyrius"})):
        status, body = analyze(fields)
        a = (body.get("analyses") or [{}])[0]
        profile = a.get("pharmacogenomic_profile") or {}
        runs[name] = {"status": status, "label": (a.get("risk_assessment") or {}).get("risk_label"),
                      "supplied_by": profile.get("supplied_by"), "diplotype": profile.get("diplotype"),
                      "action": (a.get("clinical_recommendation") or {}).get("action"),
                      "warning_present": WARNING in ((body.get("quality_metrics") or {}).get("warnings") or []),
                      "rationale": (a.get("llm_generated_explanation") or {}).get("variant_rationale")}
        print(json.dumps({name: {k: v for k, v in runs[name].items() if k != "rationale"}}), flush=True)
    w, s = runs["without"], runs["with"]
    checks = {
        "without a call: 200, codeine Unknown, supplied_by null, no supplied warning":
            w["status"] == 200 and w["label"] == "Unknown" and w["supplied_by"] is None and not w["warning_present"],
        "with *4/*4 from Cyrius: 200, codeine Ineffective with the CPIC PM text":
            s["status"] == 200 and s["label"] == "Ineffective" and s["action"] == PM_TEXT,
        "with the call: supplied_by Cyrius and the provenance warning":
            s["supplied_by"] == "Cyrius" and s["warning_present"],
        "with the call: the explanation says supplied, not called":
            "supplied by Cyrius, not called by PharmaGuard" in (s["rationale"] or "")
            and "PharmCAT called" not in (s["rationale"] or ""),
    }
    ok = all(checks.values())
    verdict.write_text(json.dumps({"checks": checks, "all_pass": ok, "runs": runs}, indent=1) + "\n")
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
    return 0 if ok else 1


def bundle(sha: str, verdict: Path) -> int:
    req = urllib.request.Request(f"{WEB}/main.dart.js?b10={sha[:7]}",
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
    if sys.argv[1] == "codeine":
        return codeine(Path(sys.argv[2]))
    if sys.argv[1] == "bundle":
        return bundle(sys.argv[2], Path(sys.argv[3]))
    raise SystemExit(f"unknown command {sys.argv[1]}")


if __name__ == "__main__":
    sys.exit(main())
