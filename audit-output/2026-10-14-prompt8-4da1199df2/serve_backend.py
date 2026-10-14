"""Start the task-owned local backend (capture wrapper over the unmodified app).

Usage: serve_backend.py <label>
Writes servers/<label>-backend.{command,pid,exit}.json and a log. Follows the
documented local procedure (docs/DEMO_SCRIPT.md: infra/local-dev.env values,
uvicorn on 127.0.0.1:8000, one worker) and pins the PharmCAT JAR, JDK 17 and
strict startup explicitly so the run cannot silently fall back.
"""
from __future__ import annotations

import datetime
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
label = sys.argv[1]
servers = HERE / "servers"
servers.mkdir(exist_ok=True)

local_dev = {}
for line in (REPO / "infra/local-dev.env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        local_dev[key] = value

overrides = {
    "CORS_ALLOWED_ORIGINS": local_dev["CORS_ALLOWED_ORIGINS"],
    "EXPLANATION_MODE": local_dev["EXPLANATION_MODE"],
    "JAVA_HOME": local_dev["JAVA_HOME"],
    "PHARMCAT_JAR": str(REPO / "test-data/reference/tools/pharmcat-3.4.0-all.jar"),
    "PHARMCAT_JAVA": local_dev["JAVA_HOME"] + "/bin/java",
    "STRICT_PHARMCAT": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "CAPTURE_DIR": str(HERE / f"api-captures-{label}"),
}
env = dict(os.environ, **overrides)
argv = [
    str(REPO / "backend/.venv/bin/python"), "-m", "uvicorn", "capture_api:app",
    "--app-dir", str(HERE), "--host", "127.0.0.1", "--port", "8000", "--workers", "1",
]


def save(name: str, payload: dict) -> None:
    (servers / f"{label}-backend.{name}.json").write_text(json.dumps(payload, indent=1) + "\n")


save("command", {"argv": argv, "cwd": str(REPO / "backend"), "environment_overrides": overrides,
                 "started": datetime.datetime.now(datetime.timezone.utc).isoformat()})
with (servers / f"{label}-backend.log").open("w") as log:
    process = subprocess.Popen(argv, cwd=REPO / "backend", env=env, stdout=log, stderr=subprocess.STDOUT)
    save("pid", {"pid": process.pid, "launcher_pid": os.getpid()})

    def stop(signum, _frame):
        process.send_signal(signal.SIGINT)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    code = process.wait()
save("exit", {"exit_code": code, "at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
