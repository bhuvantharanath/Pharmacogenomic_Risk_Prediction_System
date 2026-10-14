"""Check each saved print PDF against the same run's API response.

Usage (Python with pdfplumber): verify_print.py <browser-session-dir> <out.json>

Reports which intended summary fields are present, which API fields the
summary policy omits (listed explicitly, never called parity), the repeated
research header per page, and renders each page to PNG with pdftoppm for
visual clipping inspection. Wording of interest (source-checking disclaimer,
Unknown reasons, census note) is extracted verbatim for before/after review.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pdfplumber

session, out = Path(sys.argv[1]), Path(sys.argv[2])
PDFTOPPM = "/Users/bhuvant/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm"
HEADER = "RESEARCH AND EDUCATIONAL USE ONLY"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


def present(value: str, text: str) -> bool:
    # Only extra normalisation: PDF text extraction splits words hyphenated at
    # a line break ("label-\nrecommended"); a hyphen-joined copy is also tried.
    joined = re.sub(r"-\s+", "-", text)
    return bool(value) and (norm(value) in text or norm(value) in joined)


results = []
for case_dir in sorted((session / "cases").iterdir()):
    pdf = case_dir / "print.pdf"
    if not pdf.is_file():
        continue
    rec = json.loads((case_dir / "case.json").read_text())
    api = json.loads((session / rec["analyze"]["body_file"]).read_bytes())
    with pdfplumber.open(pdf) as doc:
        pages = [p.extract_text() or "" for p in doc.pages]
        sizes = [(round(p.width), round(p.height)) for p in doc.pages]
    (case_dir / "print-extracted.txt").write_text("\n\f\n".join(pages))
    text = norm(" ".join(pages))
    checks = []

    def check(field, value):
        checks.append({"field": field, "expected": value, "present": present(value, text)})

    check("patient_id", api["patient_id"])
    for a in api["analyses"]:
        d = a["drug"]
        check(f"{d}.risk_label", a["risk_assessment"]["risk_label"])
        for k in ("primary_gene", "diplotype", "phenotype"):
            check(f"{d}.{k}", a["pharmacogenomic_profile"][k])
        for k in ("action", "cpic_recommendation", "source"):
            check(f"{d}.{k}", a["clinical_recommendation"][k])
        check(f"{d}.summary", a["llm_generated_explanation"]["summary"])
    prov = api["quality_metrics"].get("guideline_provenance") or {}
    for k in ("pharmcat_version", "cpic_data_version", "cpic_source", "note"):
        if prov.get(k):
            check(f"provenance.{k}", prov[k])
    warnings = api["quality_metrics"].get("warnings", [])
    omitted = {
        "pipeline_warnings_total": len(warnings),
        "pipeline_warnings_present_verbatim": sum(present(w, text) for w in warnings),
        "explanation.mechanism_present": sum(present(a["llm_generated_explanation"]["mechanism"][:120], text) for a in api["analyses"]),
        "explanation.variant_rationale_present": sum(present(a["llm_generated_explanation"]["variant_rationale"][:120], text) for a in api["analyses"]),
        "explanation.patient_friendly_present": sum(present(a["llm_generated_explanation"]["patient_friendly"][:120], text) for a in api["analyses"]),
        "explanation.disclaimer_present": sum(present(a["llm_generated_explanation"]["disclaimer"], text) for a in api["analyses"]),
        "detected_variants_rsids_present": sorted({v["rsid"] for a in api["analyses"] for v in a["pharmacogenomic_profile"]["detected_variants"] if v["rsid"] and v["rsid"] in text}),
        "detected_variants_rsids_total": sorted({v["rsid"] for a in api["analyses"] for v in a["pharmacogenomic_profile"]["detected_variants"] if v["rsid"]}),
    }
    quote = {}
    for label, pattern in (
        ("source_checking_disclaimer", r"This is not a clinical report\..*?qualified healthcare professional\."),
        ("census_note", r"How many of the positions.*?(?:passed\.|Unknown\.)"),
        ("unknown_section", r"Unknown results \(\d+\).*?(?:Input coverage)"),
    ):
        m = re.search(pattern, text)
        quote[label] = m.group(0) if m else None
    render_prefix = case_dir / "print-page"
    subprocess.run([PDFTOPPM, "-r", "80", "-png", str(pdf), str(render_prefix)], check=True)
    results.append({
        "id": rec["id"],
        "pdf": str(pdf.relative_to(session)),
        "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "api_body": rec["analyze"]["body_file"],
        "api_sha256": rec["analyze"]["body_sha256"],
        "pages": len(pages),
        "page_sizes_pt": sizes,
        "research_header_on_page": [HEADER in norm(p) for p in pages],
        "checks": checks,
        "missing_intended_fields": [c for c in checks if not c["present"]],
        "omitted_by_summary_policy": omitted,
        "verbatim": quote,
        "renders": sorted(p.name for p in case_dir.glob("print-page-*.png")),
    })
out.write_text(json.dumps(results, indent=1) + "\n")
for r in results:
    print(r["id"], "pages", r["pages"], "header-all-pages", all(r["research_header_on_page"]),
          "missing", [c["field"] for c in r["missing_intended_fields"]],
          "warnings-in-print", r["omitted_by_summary_policy"]["pipeline_warnings_present_verbatim"], "/", r["omitted_by_summary_policy"]["pipeline_warnings_total"])
