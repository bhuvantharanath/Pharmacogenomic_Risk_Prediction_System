#!/usr/bin/env python3
"""
B9 AC5, the independent check: read the PDFs back with pypdf, not with the code that wrote them.

    <venv with pypdf 6.21.1>/bin/python audit/phase9/partb/b9_pdf_text.py EXPORT_DIR VERDICT.json

EXPORT_DIR is what app/test/export_fixtures_test.dart writes with PHARMAGUARD_EXPORT_DIR set: per fixture,
NAME.summary.pdf and NAME.summary.html. For every PDF, page by page:
  * the running header (the disclaimer line) is on every page;
  * every text node of the HTML summary's body is in the PDF's extracted text, whitespace-normalised. This covers
    the plan's list (every label, CPIC quote, Unknown reason and the disclaimer) and everything else on the page.
pypdf is not a project dependency; it runs from a scratch virtualenv. Exits 0 only when every check holds.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import pypdf

HEADER = "RESEARCH AND EDUCATIONAL USE ONLY — NOT A MEDICAL DEVICE"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def html_nodes(document: str) -> list[str]:
    body = document[document.index("<body>"):document.index("</body>")]
    return [n for n in (norm(html.unescape(part)) for part in re.split(r"<[^>]*>", body)) if n]


def main() -> int:
    export_dir, verdict_path = Path(sys.argv[1]), Path(sys.argv[2])
    results = {}
    for pdf_path in sorted(export_dir.glob("*.summary.pdf")):
        name = pdf_path.name.removesuffix(".summary.pdf")
        pages = [norm(page.extract_text() or "") for page in pypdf.PdfReader(pdf_path).pages]
        text = " ".join(pages)
        nodes = html_nodes((export_dir / f"{name}.summary.html").read_text())
        missing = [n for n in nodes if n not in text]
        results[name] = {
            "pages": len(pages),
            "header_on_every_page": all(HEADER in p for p in pages),
            "html_nodes": len(nodes),
            "html_nodes_missing_from_pdf": missing,
            "pass": all(HEADER in p for p in pages) and not missing,
        }
        print(f"{name}: {len(pages)} pages, header on every page {results[name]['header_on_every_page']}, "
              f"{len(nodes) - len(missing)}/{len(nodes)} HTML text nodes found")
        for n in missing:
            print(f"   missing: {n[:110]}")
    verdict = {"pypdf": pypdf.__version__, "files": results, "all_pass": bool(results) and all(
        r["pass"] for r in results.values())}
    verdict_path.write_text(json.dumps(verdict, indent=1, ensure_ascii=False) + "\n")
    print("all_pass:", verdict["all_pass"])
    return 0 if verdict["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
