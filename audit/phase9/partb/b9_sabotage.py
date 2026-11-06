#!/usr/bin/env python3
"""
B9 sabotages (audit/phase9/B9_PLAN.md): break one rule, run the check that should catch it, restore.

    backend/.venv/bin/python audit/phase9/partb/b9_sabotage.py

Each sabotage is an exact text replacement that must occur once. The file is restored after the run and its
sha256 compared with the original. A sabotage that turns nothing red is reported as such, and the script exits 1.
SB9-c is the validator's to catch, so its check is scripts/validate_fhir_exports.py, not a Flutter test.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FLUTTER = shutil.which("flutter") or "flutter"
FHIR = "app/lib/export/fhir_report.dart"
PDF = "app/lib/print/summary_pdf.dart"
SCREEN = "app/lib/screens/results_screen.dart"


def flutter_test(*tests: str) -> tuple[list[str], int]:
    proc = subprocess.run([FLUTTER, "test", "--reporter", "expanded", *tests], cwd=REPO / "app",
                          capture_output=True, text=True, check=False)
    red = sorted({line.split(": ", 1)[-1].replace(" [E]", "").strip()
                  for line in proc.stdout.splitlines() if line.rstrip().endswith("[E]")})
    return red, proc.returncode


def validator() -> tuple[list[str], int]:
    proc = subprocess.run([sys.executable, "scripts/validate_fhir_exports.py"], cwd=REPO,
                          capture_output=True, text=True, check=False)
    red = [line.strip() for line in proc.stdout.splitlines() if line.strip().startswith("error ")]
    return red, proc.returncode


SABOTAGES = [
    ("SB9-a", "the FHIR builder skips Unknown results", FHIR,
     "    for (int i = 0; i < ordered.length; i++)\n      _implication(",
     "    for (int i = 0; i < ordered.length; i++)\n"
     "      if (ordered[i].riskAssessment.riskLabel != RiskLabel.unknown)\n      _implication(",
     lambda: flutter_test("test/fhir_report_test.dart")),
    ("SB9-b", "the conclusion-string drops the last character of the CPIC text", FHIR,
     "      ? unknownExplanation(result, reason)\n      : c.action;",
     "      ? unknownExplanation(result, reason)\n      : c.action.substring(0, c.action.length - 1);",
     lambda: flutter_test("test/fhir_report_test.dart")),
    ("SB9-c", "the Genomic Report loses its LOINC code", FHIR,
     "    'code': _code(_loinc, '51969-4'),\n", "",
     validator),
    ("SB9-d", "the related artifact is left off a matched CPIC entry", FHIR,
     "    if (c.hasMatchedCpicEntry)\n      'extension': <Object?>[",
     "    if (!c.hasMatchedCpicEntry)\n      'extension': <Object?>[",
     lambda: flutter_test("test/fhir_report_test.dart")),
    ("SB9-e", "the report status becomes final", FHIR,
     "    'status': 'partial',", "    'status': 'final',",
     lambda: flutter_test("test/fhir_report_test.dart")),
    ("SB9-f", "the PDF builder leaves out the Unknown section", PDF,
     "        ..._unknownSection(p, unknowns, m),\n", "",
     lambda: flutter_test("test/summary_pdf_test.dart")),
    ("SB9-g", "the PDF's running header is left off pages after the first", PDF,
     "      header: (pw.Context context) => p.runningHeader(context.pageNumber),",
     "      header: (pw.Context context) => context.pageNumber > 1\n"
     "          ? pw.SizedBox()\n          : p.runningHeader(context.pageNumber),",
     lambda: flutter_test("test/summary_pdf_test.dart")),
    ("SB9-h", "the download control loses the FHIR item", SCREEN,
     "                    MenuItemButton(\n"
     "                      leadingIcon: const Icon(Icons.data_object),\n"
     "                      onPressed: () => _downloadFhir(context),\n"
     "                      child: const Text('FHIR Genomics Report (.json)'),\n"
     "                    ),\n", "",
     lambda: flutter_test("test/download_report_test.dart")),
]


def main() -> int:
    caught_all = True
    for sid, what, rel, old, new, check in SABOTAGES:
        path = REPO / rel
        original = path.read_bytes()
        before = hashlib.sha256(original).hexdigest()
        text = original.decode()
        if text.count(old) != 1:
            raise SystemExit(f"{sid}: expected text found {text.count(old)} times in {rel}")
        try:
            path.write_text(text.replace(old, new))
            red, rc = check()
        finally:
            path.write_bytes(original)
        restored = hashlib.sha256(path.read_bytes()).hexdigest() == before
        print(f"== {sid}: {what} ({rel}) ==")
        for line in red[:12]:
            print(f"  {line[:150]}")
        if len(red) > 12:
            print(f"  ... {len(red) - 12} more")
        print(f"exit {rc}; {len(red)} red")
        print(f"restored identical: {'yes' if restored else 'NO'}")
        if not restored:
            raise SystemExit(f"{sid}: {rel} was not restored")
        if rc == 0 or not red:
            caught_all = False
            print(f"{sid} NOT CAUGHT")
    return 0 if caught_all else 1


if __name__ == "__main__":
    sys.exit(main())
