#!/usr/bin/env python3
"""
B8 sabotages (audit/phase9/B8_PLAN.md): break one rule, run the B8 tests, restore.

    backend/.venv/bin/python audit/phase9/partb/b8_sabotage.py

Each sabotage is an exact text replacement that must occur once; the file is
restored after the run and its sha256 compared with the original. A sabotage
that turns nothing red is reported as such, and the script exits 1.

SB8-g is not in the plan: it was added with the log test's stdout/stderr check,
to show that check sees output written during a real request.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PYTEST = [str(REPO / "backend/.venv/bin/python"), "-m", "pytest", "--no-header", "-p", "no:cacheprovider",
          "-o", "addopts=", "-q", "tests/test_abuse_privacy.py"]

SABOTAGES = [
    ("SB8-a", "client_key trusts the header from any peer", "backend/app/security.py",
     "    if not _peer_is_trusted_proxy(peer):\n        return peer\n\n"
     "    if client_ip_header():\n        return _header_client(request) or peer\n",
     "    if client_ip_header():\n        return _header_client(request) or peer\n"
     "    if not _peer_is_trusted_proxy(peer):\n        return peer\n\n"),
    ("SB8-b", "the in-flight check is removed", "backend/app/security.py",
     "if key is not None and key in self._clients.values():", "if False:"),
    ("SB8-c", "the queue cap is removed", "backend/app/security.py",
     "elif (self._busy or self._waiters) and len(self._waiters) >= self.max_waiting:", "elif False:"),
    ("SB8-d", "the exit status is ignored again", "backend/app/pharmcat_runner.py",
     "if invocation.returncode != 0:", "if False:"),
    ("SB8-e", "the delete swallows errors again and skips the retry", "backend/app/pharmcat_runner.py",
     "    for attempt in (1, 2):\n        try:\n            shutil.rmtree(workdir)\n",
     "    shutil.rmtree(workdir, ignore_errors=True)\n    return True\n"
     "    for attempt in (1, 2):\n        try:\n            shutil.rmtree(workdir)\n"),
    ("SB8-f", "a log line carries the uploaded filename", "backend/app/main.py",
     "    contents = await _read_upload_limited(file)\n\n    # Size cap + format validation, shared",
     "    contents = await _read_upload_limited(file)\n"
     "    __import__(\"logging\").getLogger(\"pharmaguard.api\").warning(\"upload %s\", file.filename)\n\n"
     "    # Size cap + format validation, shared"),
    ("SB8-g", "a print carries the uploaded filename (beyond the plan)", "backend/app/main.py",
     "    contents = await _read_upload_limited(file)\n\n    # Size cap + format validation, shared",
     "    contents = await _read_upload_limited(file)\n    print(\"upload\", file.filename, flush=True)\n\n"
     "    # Size cap + format validation, shared"),
]


def main() -> int:
    caught_all = True
    for sid, what, rel, old, new in SABOTAGES:
        path = REPO / rel
        original = path.read_bytes()
        before = hashlib.sha256(original).hexdigest()
        text = original.decode()
        if text.count(old) != 1:
            raise SystemExit(f"{sid}: expected text found {text.count(old)} times in {rel}")
        try:
            path.write_text(text.replace(old, new))
            proc = subprocess.run(PYTEST, cwd=REPO / "backend", capture_output=True, text=True, check=False)
        finally:
            path.write_bytes(original)
        restored = hashlib.sha256(path.read_bytes()).hexdigest() == before
        failed = [line.split(" - ")[0] for line in proc.stdout.splitlines() if line.startswith(("FAILED", "ERROR"))]
        print(f"== {sid}: {what} ({rel}) ==")
        for line in failed:
            print(line)
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
