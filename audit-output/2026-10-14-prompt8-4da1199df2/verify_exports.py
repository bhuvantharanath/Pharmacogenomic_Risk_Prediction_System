"""Bind every browser case to its fixture, its API bytes, and its exports.

Usage: verify_exports.py <browser-session-dir> <api-capture-dir> <out.json>

For each case:
  * upload: the multipart file part the server received == fixture SHA-256;
  * API -> browser: bytes the browser received == bytes the server sent;
  * export: downloaded JSON and clipboard JSON (pbpaste) parsed and compared
    with the API response after ONLY the documented export transform:
      - drop risk_assessment.confidence_score / severity (deprecated);
      - add risk_assessment.assessment_scope (fixed text);
      - add application_capability, which must equal the registry entry
        (backend/app/data/capabilities.json) for registered drugs.
    Every other difference is reported, not normalised away.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

session, captures, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
REPO = Path(__file__).resolve().parents[2]
registry = {c["drug"]: c for c in json.loads((REPO / "backend/app/data/capabilities.json").read_text())["capabilities"]}
SCOPE = "PGx interpretation only; not a clinical safety, probability, or severity assessment"
CAP_KEYS = ("drug", "primary_gene", "relevant_genes", "evidence_dependencies", "implementation_status",
            "guidance_capable", "limitation", "explanation_available", "ui_available", "export_available")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def diff(a, b, path="$"):
    if isinstance(a, bool) or isinstance(b, bool):
        return [] if a is b else [f"{path}: {a!r} != {b!r}"]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return [] if float(a) == float(b) else [f"{path}: {a!r} != {b!r}"]
    if type(a) is not type(b):
        return [f"{path}: type {type(a).__name__} != {type(b).__name__} ({a!r} vs {b!r})"]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append(f"{path}.{k}: only in export")
            elif k not in b:
                out.append(f"{path}.{k}: only in API")
            else:
                out += diff(a[k], b[k], f"{path}.{k}")
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} != {len(b)}"]
        return [x for i, (p, q) in enumerate(zip(a, b)) for x in diff(p, q, f"{path}[{i}]")]
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def documented_transform(api: dict) -> tuple[dict, list[str]]:
    notes = []
    expected = json.loads(json.dumps(api))
    for a in expected["analyses"]:
        ra = a["risk_assessment"]
        for k in ("confidence_score", "severity"):
            if k in ra:
                ra.pop(k)
        ra["assessment_scope"] = SCOPE
        cap = registry.get(a["drug"].strip().lower())
        if cap:
            a["application_capability"] = {k: cap[k] for k in CAP_KEYS}
        else:
            a["application_capability"] = {"drug": a["drug"], "guidance_capable": False,
                                           "export_available": False,
                                           "limitation": "Outside the audited application scope."}
            notes.append(f"{a['drug']}: not in registry; export uses the documented client fallback")
    return expected, notes


server = {}
for receipt in captures.glob("*.receipt.json"):
    r = json.loads(receipt.read_text())
    server.setdefault(r["response_sha256"], []).append(r)

results = []
for case_dir in sorted((session / "cases").iterdir()):
    if not (case_dir / "case.json").is_file():
        continue  # case still running or aborted; reported by the runner
    rec = json.loads((case_dir / "case.json").read_text())
    row = {"id": rec["id"], "fixture_sha256": rec["fixture_sha256"]}
    for stage in ("coverage", "analyze", "recovery_analyze"):
        s = rec.get(stage)
        if not s or not s.get("body_sha256"):
            continue
        matches = server.get(s["body_sha256"], [])
        files = [p for m in matches for p in m["multipart_parts"] if p.get("filename")]
        row[stage] = {
            "status": s.get("status"),
            "browser_received_sha256": s["body_sha256"],
            "server_sent_match": bool(matches),
            "server_receipts": [m["n"] for m in matches],
            "uploaded_file_sha256": sorted({f["sha256"] for f in files}),
            "upload_bound_to_fixture": stage == "recovery_analyze" or any(f["sha256"] == rec["fixture_sha256"] for f in files),
            "drugs_field": sorted({p.get("value") for m in matches for p in m["multipart_parts"] if p.get("name") == "drugs"} - {None}),
        }
    if rec.get("download") and rec["analyze"].get("status") == 200:
        api_raw = (session / rec["analyze"]["body_file"]).read_bytes()
        api = json.loads(api_raw)
        expected, notes = documented_transform(api)
        dl_raw = (case_dir / rec["download"]["file"]).read_bytes()
        clip_path = case_dir / "clipboard.json"
        clip_raw = clip_path.read_bytes() if clip_path.is_file() else dl_raw  # headless runs skip the OS clipboard
        dl, clip = json.loads(dl_raw), json.loads(clip_raw)
        row["export"] = {
            "download_bytes": len(dl_raw), "download_sha256": sha(dl_raw),
            "clipboard_checked": clip_path.is_file(),
            "clipboard_bytes": len(clip_raw), "clipboard_sha256": sha(clip_raw),
            "clipboard_equals_download_bytes": dl_raw == clip_raw,
            "download_vs_api_after_documented_transform": diff(expected, dl),
            "clipboard_vs_api_after_documented_transform": diff(expected, clip),
            "transform_notes": notes,
            "api_fields_removed": ["analyses[].risk_assessment.confidence_score", "analyses[].risk_assessment.severity"],
            "fields_added": ["analyses[].risk_assessment.assessment_scope", "analyses[].application_capability"],
        }
    results.append(row)

summary = {
    "cases": len(results),
    "all_uploads_bound": all(r.get("analyze", {}).get("upload_bound_to_fixture", True) for r in results),
    "all_api_bytes_match_browser": all(r[s]["server_sent_match"] for r in results for s in ("coverage", "analyze", "recovery_analyze") if s in r),
    "export_parity_failures": {r["id"]: r["export"]["download_vs_api_after_documented_transform"][:10]
                               for r in results if r.get("export") and r["export"]["download_vs_api_after_documented_transform"]},
    "clipboard_parity_failures": {r["id"]: r["export"]["clipboard_vs_api_after_documented_transform"][:10]
                                  for r in results if r.get("export") and r["export"]["clipboard_vs_api_after_documented_transform"]},
}
out.write_text(json.dumps({"summary": summary, "cases": results}, indent=1) + "\n")
print(json.dumps(summary, indent=1))
