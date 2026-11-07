#!/usr/bin/env python3
"""
F-20 sabotages (audit/phase9/F20_PLAN.md): break one rule, run the tests that should catch it, restore.

    backend/.venv/bin/python audit/phase9/partb/f20_sabotage.py

Each sabotage is an exact text replacement that must occur once. The file is restored after the run and its
sha256 compared with the original. A sabotage that turns nothing red is reported as such, and the script exits 1.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PY = str(REPO / "backend/.venv/bin/python")
ENGINE = "backend/app/cpic_engine.py"


def backend() -> tuple[list[str], int]:
    proc = subprocess.run([PY, "-m", "pytest", "--no-header", "-p", "no:cacheprovider", "-o", "addopts=", "-q",
                           "tests/test_no_borrowed_row.py"], cwd=REPO / "backend",
                          capture_output=True, text=True, check=False)
    red = [line.split(" - ")[0] for line in proc.stdout.splitlines() if line.startswith(("FAILED", "ERROR"))]
    return red, proc.returncode


WARNING = (
    '        warnings.append(\n'
    '            f"No CPIC row for {guideline.drug} matches the called phenotypes, so "\n'
    '            "none is shown: a row written for a different result could give the "\n'
    '            "opposite advice. Reported as Unknown."\n'
    '        )\n'
)

SABOTAGES = [
    ("SBF20-a", "the fallback is restored: candidates = matched or usable", ENGINE,
     "        return None, warnings\n    candidates = matched\n",
     "    candidates = matched or usable\n", backend),
    ("SBF20-b", "a different borrowing: the first usable row when none matches", ENGINE,
     "        return None, warnings\n    candidates = matched\n",
     "        return usable[0], warnings\n    candidates = matched\n", backend),
    ("SBF20-c", "no row is returned, but the warning is dropped", ENGINE, WARNING, "", backend),
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
