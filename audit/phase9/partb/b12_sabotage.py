#!/usr/bin/env python3
"""
B12 sabotages (audit/phase9/B12_PLAN.md): break one rule, run the tests that should catch it, restore.

    backend/.venv/bin/python audit/phase9/partb/b12_sabotage.py

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


def flutter(*tests: str) -> tuple[list[str], int]:
    proc = subprocess.run([FLUTTER, "test", "--reporter", "expanded", *tests], cwd=REPO / "app",
                          capture_output=True, text=True, check=False)
    red = sorted({line.split(": ", 1)[-1].replace(" [E]", "").strip()
                  for line in proc.stdout.splitlines() if line.rstrip().endswith("[E]")})
    return red, proc.returncode


def access() -> tuple[list[str], int]:
    return flutter("test/accessibility_test.dart")


SABOTAGES = [
    ("SB12-a", "ink3 is put back to the value that fails AA as text", "app/lib/theme/tokens.dart",
     "  static const Color ink3 = Color(0xFF646E67);",
     "  static const Color ink3 = Color(0xFF7D8A81);", access),
    ("SB12-b", "a control's edge goes back to the decorative hairline", "app/lib/widgets/view_toggle.dart",
     "        border: Border.all(color: Tokens.controlEdge, width: Tokens.hairline),",
     "        border: Border.all(color: Tokens.rule2, width: Tokens.hairline),", access),
    ("SB12-c", "a sample's button loses the name that distinguishes it", "app/lib/widgets/sample_files.dart",
     "                  semanticsLabel: 'Try this sample: ${sample.title}',\n", "", access),
    ("SB12-d", "a status message goes back to a bare textbox", "app/lib/screens/home_screen.dart",
     "                MessageText(\n                  message,\n                  kind: 'Server busy',\n",
     "                SelectableText(\n                  message,\n", access),
    ("SB12-e", "Ineffective is given Toxic's icon, leaving colour and word only",
     "app/lib/theme/risk_style.dart",
     "  RiskLabel.ineffective => Icons.block,",
     "  RiskLabel.ineffective => Icons.warning_amber_rounded,", access),
    ("SB12-f", "a Flexible is removed, restoring the 200% overflow", "app/lib/screens/results_screen.dart",
     "        Flexible(child: Text(label, style: theme.textTheme.labelMedium)),",
     "        Text(label, style: theme.textTheme.labelMedium),", access),
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
