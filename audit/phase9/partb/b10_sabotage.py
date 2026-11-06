#!/usr/bin/env python3
"""
B10 sabotages (audit/phase9/B10_PLAN.md): break one rule, run the tests that should catch it, restore.

    backend/.venv/bin/python audit/phase9/partb/b10_sabotage.py

Each sabotage is an exact text replacement that must occur once. The file is restored after the run and its
sha256 compared with the original. A sabotage that turns nothing red is reported as such, and the script exits 1.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FLUTTER = shutil.which("flutter") or "flutter"
PY = str(REPO / "backend/.venv/bin/python")


def backend() -> tuple[list[str], int]:
    proc = subprocess.run([PY, "-m", "pytest", "--no-header", "-p", "no:cacheprovider", "-o", "addopts=", "-q",
                           "tests/test_outside_calls.py"], cwd=REPO / "backend",
                          capture_output=True, text=True, check=False)
    red = [line.split(" - ")[0] for line in proc.stdout.splitlines() if line.startswith(("FAILED", "ERROR"))]
    return red, proc.returncode


def flutter(*tests: str) -> tuple[list[str], int]:
    proc = subprocess.run([FLUTTER, "test", "--reporter", "expanded", *tests], cwd=REPO / "app",
                          capture_output=True, text=True, check=False)
    red = sorted({line.split(": ", 1)[-1].replace(" [E]", "").strip()
                  for line in proc.stdout.splitlines() if line.rstrip().endswith("[E]")})
    return red, proc.returncode


SABOTAGES = [
    ("SB10-a", "the diplotype grammar lets a newline through", "backend/app/outside_calls.py",
     "not DIPLOTYPE.fullmatch(diplotype):", "not DIPLOTYPE.match(diplotype):", backend),
    ("SB10-b", "codeine's gate opens for a CYP2D6 call that did not come OUTSIDE", "backend/app/cpic_engine.py",
     "        and outside.is_outside_call\n    )", "        and outside.is_called\n    )", backend),
    ("SB10-c", "supplied_by is not set for an outside call", "backend/app/main.py",
     "    supplier = supplied_by if call is not None and call.is_outside_call else None",
     "    supplier = None", backend),
    ("SB10-d", "the template says PharmCAT called a supplied diplotype",
     "backend/app/explanation/generator_template.py",
     '            "{gene} {diplotype} was supplied by "',
     '            "PharmCAT called {gene} as {diplotype}, supplied by "', backend),
    ("SB10-e", "the new phrase is removed from standard_dosing", "backend/app/data/label_mapping.yaml",
     '      - "label recommended age- or weight-specific dosing"\n', "", backend),
    ("SB10-f", "the caller list accepts any name", "backend/app/outside_calls.py",
     "    if caller not in CALLERS:", "    if not caller.strip():", backend),
    ("SB10-g", "-research cyp2d6 is added to the PharmCAT command", "backend/app/pharmcat_runner.py",
     '        extra = ["-po", str(outside_calls)] if outside_calls is not None else []',
     '        extra = (["-po", str(outside_calls), "-research", "cyp2d6"]\n'
     '                 if outside_calls is not None else [])', backend),
    ("SB10-h", "the results row drops the provenance line", "app/lib/widgets/summary_grid.dart",
     "      if (result.pharmacogenomicProfile.provenanceLine != null) ...<Widget>[\n"
     "        const SizedBox(height: 3),\n"
     "        Text(\n"
     "          result.pharmacogenomicProfile.provenanceLine!,\n"
     "          style: Tokens.monoSm.copyWith(color: Tokens.ink2),\n"
     "        ),\n"
     "      ],\n", "", lambda: flutter("test/outside_call_test.dart")),
    ("SB10-i", "the printable summary drops the provenance line", "app/lib/print/summary_document.dart",
     "      b.writeln('<p class=\"note\">${esc(provenance)}</p>');\n", "",
     lambda: flutter("test/outside_call_test.dart", "test/summary_pdf_test.dart")),
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
        for line in red[:10]:
            print(f"  {line[:150]}")
        if len(red) > 10:
            print(f"  ... {len(red) - 10} more")
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
