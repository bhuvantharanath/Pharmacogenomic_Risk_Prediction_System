#!/usr/bin/env python3
"""
B7 sabotages (audit/phase9/B7_PLAN.md): break one rule, run its tests, restore.

    backend/.venv/bin/python audit/phase9/partb/b7_sabotage.py

Each sabotage is an exact text replacement that must occur once; the file is
restored after the run and its sha256 compared with the original. A sabotage
that turns nothing red is reported as such, and the script exits 1.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PYTEST = ([str(REPO / "backend/.venv/bin/python"), "-m", "pytest", "--no-header", "-p", "no:cacheprovider",
           "tests/test_public_health.py", "tests/test_deployment.py"], REPO / "backend")
FLUTTER = (["flutter", "test", "test/connectivity_states_test.dart", "test/backend_status_test.dart"], REPO / "app")

SABOTAGES = [
    ("SB7-a", "the /health middleware stops adding *", "backend/app/security.py",
     '                MutableHeaders(scope=message)["Access-Control-Allow-Origin"] = "*"\n',
     "                pass\n", PYTEST),
    ("SB7-b", "the preview regex loses its anchors (as planned)", "backend/app/security.py",
     'patterns.append(rf"^https://[a-z0-9-]+\\.{safe}\\.pages\\.dev$")',
     'patterns.append(rf"https://[a-z0-9-]+\\.{safe}\\.pages\\.dev")', PYTEST),
    ("SB7-b2", "the preview label may contain dots (a real loosening)", "backend/app/security.py",
     'patterns.append(rf"^https://[a-z0-9-]+\\.{safe}\\.pages\\.dev$")',
     'patterns.append(rf"^https://[a-z0-9.-]+\\.{safe}\\.pages\\.dev$")', PYTEST),
    ("SB7-c", "the * header is applied to every path", "backend/app/security.py",
     '        if scope["type"] != "http" or scope["path"] != self.PATH:\n',
     '        if scope["type"] != "http":\n', PYTEST),
    ("SB7-d", "the client treats origin_allowed false as ready", "app/lib/api/pharmaguard_api.dart",
     "      report.originAllowed == false\n          ? HealthOutcome.blocked\n          : HealthOutcome.ready,\n",
     "      HealthOutcome.ready,\n", FLUTTER),
    ("SB7-e", "the wake bar divides by 90 s again", "app/lib/api/backend_status.dart",
     "elapsed.inMilliseconds / budget.inMilliseconds",
     "elapsed.inMilliseconds / 90000", FLUTTER),
    ("SB7-f", "a declined 400 maps to the server-error heading", "app/lib/api/pharmaguard_api.dart",
     "if (status >= 400 && errorCode != null) return ApiErrorKind.declined;",
     "if (status >= 400 && errorCode != null) return ApiErrorKind.serverError;", FLUTTER),
]


def main() -> int:
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    caught_all = True
    for sid, what, rel, old, new, (argv, cwd) in SABOTAGES:
        if only and sid not in only:
            continue
        path = REPO / rel
        original = path.read_bytes()
        before = hashlib.sha256(original).hexdigest()
        text = original.decode()
        if text.count(old) != 1:
            raise SystemExit(f"{sid}: expected text found {text.count(old)} times in {rel}")
        try:
            path.write_text(text.replace(old, new))
            proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
        finally:
            path.write_bytes(original)
        restored = hashlib.sha256(path.read_bytes()).hexdigest() == before
        out = proc.stdout.replace("\r", "\n")
        failed = sorted({line.split(" - ")[0].strip() for line in out.splitlines()
                         if line.startswith(("FAILED", "ERROR")) or line.rstrip().endswith("[E]")})
        print(f"== {sid}: {what} ({rel}) ==")
        for line in failed:
            print(line[-160:])
        print(f"exit {proc.returncode}; {len(failed)} red")
        print(f"restored identical: {'yes' if restored else 'NO'}")
        if not restored:
            raise SystemExit(f"{sid}: {rel} was not restored")
        if proc.returncode == 0 or not failed:
            caught_all = False
            print(f"{sid} NOT CAUGHT")
    return 0 if caught_all else 1


if __name__ == "__main__":
    sys.exit(main())
