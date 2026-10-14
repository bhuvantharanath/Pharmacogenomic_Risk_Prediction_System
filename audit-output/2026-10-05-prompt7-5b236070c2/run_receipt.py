"""Execute a Prompt 7 command and preserve exact arguments, output, and exit code."""

import datetime
import json
from pathlib import Path
import subprocess
import sys

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parents[1]
name, *argv = sys.argv[1:]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
result = subprocess.run(argv, cwd=ROOT, capture_output=True)
(AUDIT / f"{name}.stdout").write_bytes(result.stdout)
(AUDIT / f"{name}.stderr").write_bytes(result.stderr)
ledger = AUDIT / "commands.json"
entries = json.loads(ledger.read_text()) if ledger.exists() else []
entries.append({
    "name": name, "argv": argv, "cwd": str(ROOT), "started_at": started,
    "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "exit_code": result.returncode, "stdout": f"{name}.stdout",
    "stderr": f"{name}.stderr",
})
ledger.write_text(json.dumps(entries, indent=2) + "\n")
print(json.dumps({"name": name, "exit_code": result.returncode,
                  "stdout_bytes": len(result.stdout), "stderr_bytes": len(result.stderr)}))
print(result.stdout.decode(errors="replace")[:2000])
print(result.stderr.decode(errors="replace")[:1000])
sys.exit(result.returncode)
