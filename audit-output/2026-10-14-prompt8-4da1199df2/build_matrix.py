"""Assemble the case-by-case matrix from recorded artifacts only (no new runs).

A label row passes only when every expected drug is present with exactly the
expected label, the expected diplotype/phenotype where the expectation names
one, and the CVI ACS PCI population qualifier where the expectation requires
it. An upload-error row passes only when /coverage carries the expected typed
error code and /analyze returns the same status. Browser columns are read from
the real-Chrome run and must match the API status.
"""
import json
import re
from pathlib import Path

A = Path(__file__).resolve().parent
LABELS = ("No PGx-guided adjustment identified", "Adjust Dosage", "Ineffective", "Unknown")
UPLOAD_CODES = {"D08": (413, "FILE_TOO_LARGE"), "D09": (400, "CORRUPT_GZIP")}
table = {f["id"]: f for f in json.loads((A / "fixtures/EVIDENCE-TABLE.json").read_text())["fixtures"]}
api = {r["id"]: r for r in json.loads((A / "api-harness-final2/results.json").read_text())["fixtures"]}
base_api = {r["id"]: r for r in json.loads((A / "api-harness-baseline/results.json").read_text())["fixtures"]}
exports = {r["id"]: r for r in json.loads((A / "verification/exports-final.json").read_text())["cases"]}
prints = {r["id"]: r for r in json.loads((A / "verification/print-final.json").read_text())}


def want_label(expectation: str) -> str:
    for label in LABELS:
        if expectation.startswith(label):
            return label
    raise ValueError(expectation)


def label_failures(expected: dict, drugs: dict) -> list:
    failures = []
    if set(expected) != set(drugs):
        failures.append(f"drug set {sorted(drugs)} != {sorted(expected)}")
    for drug, exp in expected.items():
        got = drugs.get(drug) or {}
        if got.get("risk_label") != want_label(exp):
            failures.append(f"{drug}: {got.get('risk_label')} != {want_label(exp)}")
        m = re.search(r"\(([A-Z0-9]+) (\*\S+), ([A-Z]{2})\)", exp)
        if m and (got.get("diplotype"), got.get("phenotype")) != (m.group(2), m.group(3)):
            failures.append(f"{drug}: {got.get('diplotype')} {got.get('phenotype')} != {m.group(2)} {m.group(3)}")
        m = re.search(r"\(([A-Z0-9]+) ([A-Z]{2}),", exp)
        if m and got.get("phenotype") != m.group(2):
            failures.append(f"{drug}: phenotype {got.get('phenotype')} != {m.group(2)}")
        if "ACS/PCI" in exp and "CVI ACS PCI" not in (got.get("cpic_recommendation") or ""):
            failures.append(f"{drug}: ACS/PCI qualifier missing")
    return failures


rows = []
for fid, f in table.items():
    a, b = api[fid], base_api[fid]
    drugs = a["analyze"]["drugs"] or {}
    base_drugs = b["analyze"]["drugs"] or {}
    pc = (a.get("pharmcat_direct") or {}).get("raw_gene_calls", {})
    caller = pc.get("CYP2C19", {}).get("source_diplotypes") if pc else None
    failures = []
    if fid in UPLOAD_CODES:
        status, code = UPLOAD_CODES[fid]
        if (a["coverage"]["status"], a["coverage"].get("error_code"), a["analyze"]["status"]) != (status, code, status):
            failures.append(f"upload: {a['coverage']['status']} {a['coverage'].get('error_code')} {a['analyze']['status']}")
    else:
        failures += label_failures(f["expected"], drugs)
    browser = None
    case_file = A / "browser/run-final/cases" / fid / "case.json"
    if case_file.is_file():
        c = json.loads(case_file.read_text())
        statuses = (c["coverage"]["status"], c["analyze"]["status"])
        if statuses != (a["coverage"]["status"], a["analyze"]["status"]):
            failures.append(f"browser statuses {statuses}")
        recovery = c.get("recovery_analyze", {}).get("status")
        if fid in UPLOAD_CODES and recovery != 200:
            failures.append(f"browser recovery {recovery}")
        browser = f"{statuses[0]}/{statuses[1]}" + (" +recovery 200" if recovery == 200 else "")
    e = exports.get(fid, {}).get("export")
    if e and (e["download_vs_api_after_documented_transform"] or e["clipboard_vs_api_after_documented_transform"]):
        failures.append("export differs from API after documented transform")
    p = prints.get(fid)
    if p and p["missing_intended_fields"]:
        failures.append("print missing fields")
    same_labels = drugs.keys() == base_drugs.keys() and all(
        drugs[d]["risk_label"] == base_drugs[d]["risk_label"] for d in drugs)
    rows.append(dict(
        id=fid, label=f["label"], synthetic=f["synthetic"], fixture=f["upload_copy"].split("/")[-1],
        sha=f["source_sha256"][:12], caller_cyp2c19=", ".join(caller) if caller else "—",
        api=f"{a['coverage']['status']}/{a['analyze']['status']}",
        labels="; ".join(f"{d}: {v['risk_label']}" for d, v in drugs.items())
        or f"{a['coverage'].get('error_code')}: {(a['analyze']['error'] or '')[:70]}…",
        labels_same_as_baseline=same_labels, browser=browser or "API only",
        export="parity" if e else "n/a",
        print=f"{p['pages']} pp, fields complete" if p else "—",
        failures=failures, verdict="PASS" if not failures else "FAIL",
    ))
(A / "verification/case-matrix.json").write_text(json.dumps(rows, indent=1) + "\n")
lines = ["| Case | Fixture (SHA-256 prefix) | Kind | Caller CYP2C19 | API cov/analyze | Drug results | Same as baseline | Browser | Export | Print | Verdict |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    lines.append(f"| {r['id']} {r['label']} | `{r['fixture']}` (`{r['sha']}`) | {'synthetic' if r['synthetic'] else 'real/derived'} | {r['caller_cyp2c19']} | {r['api']} | {r['labels']} | {'yes' if r['labels_same_as_baseline'] else 'NO'} | {r['browser']} | {r['export']} | {r['print']} | {r['verdict']}{' — ' + '; '.join(r['failures']) if r['failures'] else ''} |")
(A / "verification/case-matrix.md").write_text("\n".join(lines) + "\n")
print(json.dumps({"rows": len(rows), "pass": sum(r["verdict"] == "PASS" for r in rows),
                  "fail": [r["id"] for r in rows if r["failures"]],
                  "labels_changed_vs_baseline": [r["id"] for r in rows if not r["labels_same_as_baseline"]]}))
