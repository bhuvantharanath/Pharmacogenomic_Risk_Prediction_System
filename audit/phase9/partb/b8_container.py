#!/usr/bin/env python3
"""
B8 AC7: the image rebuilt with the upgraded framework serves /ready and S1-S6.

    backend/.venv/bin/python audit/phase9/partb/b8_container.py

Builds infra/Dockerfile as pharmaguard-api:b8, reads the framework versions
installed in it, starts it as B4 did (same JAVA_TOOL_OPTIONS as production),
checks /ready, runs S1-S6 through measure_warm.py, and compares every S1-S6
body with the local B8 run apart from `timestamp` and `processing_time_ms`.
Writes audit/phase9/partb/B8/container.json. Exits 0 only when all of it holds.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "B8"
CFG = Path(__file__).resolve().parent / "B4" / ".dockercfg"
ENV = dict(os.environ, DOCKER_CONFIG=str(CFG), DOCKER_HOST=f"unix://{Path.home()}/.colima/default/docker.sock")
JAVA_OPTS = "-Xmx208m -XX:MaxMetaspaceSize=68m"
PY = str(REPO / "backend/.venv/bin/python")
IMAGE, NAME, PORT = "pharmaguard-api:b8", "pg-b8", 8033
VOLATILE = {"timestamp", "processing_time_ms"}


def docker(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(["docker", *args], env=ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise SystemExit(f"docker {' '.join(args[:3])} failed rc={proc.returncode}: {proc.stderr[-800:]}")
    return proc


def strip(obj):
    if isinstance(obj, dict):
        return {k: strip(v) for k, v in obj.items() if k not in VOLATILE}
    if isinstance(obj, list):
        return [strip(v) for v in obj]
    return obj


def main() -> int:
    CFG.mkdir(parents=True, exist_ok=True)
    built = time.monotonic()
    docker("build", "-f", "infra/Dockerfile", "-t", IMAGE, str(REPO))
    result: dict = {"image": IMAGE, "build_seconds": round(time.monotonic() - built, 1),
                    "image_size_bytes": int(docker("image", "inspect", "--format", "{{.Size}}", IMAGE).stdout)}
    docker("rm", "-f", NAME, check=False)
    docker("run", "-d", "--name", NAME, "-p", f"{PORT}:7860", "-e", "PHARMAGUARD_ENV=development",
           "-e", "CORS_ALLOWED_ORIGINS=http://localhost:8080", "-e", f"JAVA_TOOL_OPTIONS={JAVA_OPTS}", IMAGE)
    try:
        versions = docker("exec", NAME, "python3", "-c",
                          "import fastapi, starlette, multipart; "
                          "print(fastapi.__version__, starlette.__version__, multipart.__version__)").stdout.split()
        result["versions"] = dict(zip(("fastapi", "starlette", "python-multipart"), versions))
        for _ in range(240):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/ready", timeout=5) as resp:
                    result["ready"] = {"status": resp.status, "body": json.loads(resp.read())["status"]}
                    break
            except Exception:  # noqa: BLE001 — still starting
                time.sleep(0.5)
        else:
            raise SystemExit("/ready never answered")
        dest = OUT / "container-s1s6"
        run = subprocess.run([PY, str(REPO / "audit/phase9/live/measure_warm.py"), "--base",
                              f"http://127.0.0.1:{PORT}", "--out", str(dest), "--phase", "scenarios", "--no-pace"],
                             capture_output=True, text=True)
        if run.returncode != 0:
            raise SystemExit(f"S1-S6 failed: {run.stderr[-800:]}")
    finally:
        docker("rm", "-f", NAME, check=False)

    same, differ = [], []
    for path in sorted((OUT / "s1-s6" / "s1-s6").glob("S*.json")):
        local = strip(json.loads(path.read_text()))
        served = strip(json.loads((dest / "s1-s6" / path.name).read_text()))
        (same if local == served else differ).append(path.stem)
    result.update({"s1s6_equal_to_local": same, "s1s6_differ": differ})
    expected = {"fastapi": "0.162.0", "starlette": "1.10.0", "python-multipart": "0.0.33"}
    result["all_pass"] = (result["versions"] == expected and result["ready"] == {"status": 200, "body": "ready"}
                          and len(same) == 6 and not differ)
    (OUT / "container.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
