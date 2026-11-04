#!/usr/bin/env python3
"""
B4 measurement: the old and slim images, side by side, on this machine.

    python audit/phase9/partb/b4_containers.py <old-image> <slim-image>

For each image, with the production JAVA_TOOL_OPTIONS:
  1. start the container, wait for /health, run S1-S6 through its /analyze
     (audit/phase9/live/measure_warm.py, the harness every other S1-S6 run uses),
     then read the container's cgroup v2 memory.peak;
  2. run the 74 PharmCAT test VCFs with the jar inside the image, exactly as the
     runner invokes it (-vcf … -o … -reporterJson), and keep each report.json.
Then compare: S1-S6 JSON apart from `timestamp` and `processing_time_ms`, and the
`genes` section of every report.json.

Writes audit/phase9/partb/B4/{old,slim}/ and B4/containers.json. Docker is driven
with an empty client config (the user's config names a credential helper that is
not installed) against colima's socket.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "B4"
TESTVCFS = REPO / "test-data/reference/pharmcat_testvcfs"
JAVA_OPTS = "-Xmx208m -XX:MaxMetaspaceSize=68m"   # production, set 2026-11-04
PY = str(REPO / "backend/.venv/bin/python")
CFG = Path(__file__).resolve().parent / "B4" / ".dockercfg"
ENV = dict(os.environ, DOCKER_CONFIG=str(CFG),
           DOCKER_HOST=f"unix://{Path.home()}/.colima/default/docker.sock")
VOLATILE = {"timestamp", "processing_time_ms"}


def docker(*args: str, check: bool = True, **kw) -> subprocess.CompletedProcess:
    proc = subprocess.run(["docker", *args], env=ENV, capture_output=True, **kw)
    if check and proc.returncode != 0:
        raise SystemExit(f"docker {' '.join(args[:3])} failed rc={proc.returncode}: "
                         f"{proc.stderr.decode(errors='replace')[-800:]}")
    return proc


def scenarios(image: str, kind: str, port: int) -> dict:
    name = f"pg-b4-{kind}"
    docker("rm", "-f", name, check=False)
    docker("run", "-d", "--name", name, "-p", f"{port}:7860",
           "-e", "PHARMAGUARD_ENV=development",
           "-e", "CORS_ALLOWED_ORIGINS=http://localhost:8080",
           "-e", f"JAVA_TOOL_OPTIONS={JAVA_OPTS}", image)
    try:
        started = time.monotonic()
        for _ in range(240):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
                    health = json.loads(r.read())
                    break
            except Exception:  # noqa: BLE001 — still starting
                time.sleep(0.5)
        else:
            raise SystemExit(f"{kind}: /health never answered")
        ready_s = round(time.monotonic() - started, 1)
        dest = OUT / kind / "s1-s6"
        run = subprocess.run([PY, str(REPO / "audit/phase9/live/measure_warm.py"),
                              "--base", f"http://127.0.0.1:{port}", "--out", str(dest),
                              "--phase", "scenarios", "--no-pace"],
                             capture_output=True, text=True)
        if run.returncode != 0:
            raise SystemExit(f"{kind}: S1-S6 failed: {run.stderr[-800:]}")
        peak = docker("exec", name, "cat", "/sys/fs/cgroup/memory.peak").stdout.decode().strip()
        pid1 = docker("exec", name, "sh", "-c", "tr '\\0' ' ' < /proc/1/cmdline").stdout.decode().strip()
        uid = docker("exec", name, "id", "-u").stdout.decode().strip()
        wrapper = docker("exec", name, "sh", "-c", "command -v pharmcat_pipeline || echo absent",
                         check=False).stdout.decode().strip()
        jar = docker("exec", name, "sha256sum", "/pharmcat/pharmcat.jar").stdout.decode().split()[0]
        java = docker("exec", name, "sh", "-c", "java -version 2>&1 | head -1").stdout.decode().strip()
        python = docker("exec", name, "python3", "--version").stdout.decode().strip()
    finally:
        docker("logs", name, check=False)
        docker("rm", "-f", name, check=False)
    return {"ready_seconds": ready_s, "health": health, "memory_peak_bytes": int(peak),
            "pid1": pid1, "uid": uid, "pharmcat_pipeline": wrapper, "jar_sha256": jar,
            "java": java, "python": python}


def testvcfs(image: str, kind: str) -> dict:
    """Each test VCF through the jar inside the image; report.json kept per file."""
    script = (
        "set -eu; mkdir -p /tmp/out; "
        "for f in $(cd /vcfs && find . -name '*.vcf' | sort); do "
        "  d=/tmp/out/$(echo $f | tr '/.' '__'); mkdir -p $d/in; cp /vcfs/$f $d/in/in.vcf; "
        "  java -jar /pharmcat/pharmcat.jar -vcf $d/in/in.vcf -o $d -reporterJson > $d/run.log 2>&1 "
        "    || echo FAILED $f; "
        "done; tar -C /tmp/out -cf - ."
    )
    proc = docker("run", "--rm", "--entrypoint", "sh", "-e", f"JAVA_TOOL_OPTIONS={JAVA_OPTS}",
                  "-v", f"{TESTVCFS}:/vcfs:ro", image, "-c", script)
    reports = {}
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as tar:
        for member in tar.getmembers():
            if member.name.endswith("in.report.json"):
                key = member.name.split("/")[1]
                reports[key] = json.loads(tar.extractfile(member).read())
    (OUT / kind / "testvcf_genes.json").write_text(
        json.dumps({k: v["genes"] for k, v in sorted(reports.items())}, sort_keys=True))
    return reports


def strip(obj):
    if isinstance(obj, dict):
        return {k: strip(v) for k, v in obj.items() if k not in VOLATILE}
    if isinstance(obj, list):
        return [strip(v) for v in obj]
    return obj


def main() -> int:
    old_image, slim_image = sys.argv[1], sys.argv[2]
    CFG.mkdir(parents=True, exist_ok=True)
    result = {"java_tool_options": JAVA_OPTS}
    for kind, image, port in (("old", old_image, 8031), ("slim", slim_image, 8032)):
        (OUT / kind).mkdir(parents=True, exist_ok=True)
        size = docker("image", "inspect", "--format", "{{.Size}}", image).stdout.decode().strip()
        result[kind] = {"image": image, "image_size_bytes": int(size),
                        "served": scenarios(image, kind, port)}
        result[kind]["testvcf_reports"] = len(testvcfs(image, kind))
        print(kind, json.dumps(result[kind]["served"]["memory_peak_bytes"]), flush=True)
    s_old = OUT / "old" / "s1-s6" / "s1-s6"
    s_new = OUT / "slim" / "s1-s6" / "s1-s6"
    same, differ = [], []
    for path in sorted(s_old.glob("*.json")):
        a = strip(json.loads(path.read_text()))
        b = strip(json.loads((s_new / path.name).read_text()))
        (same if a == b else differ).append(path.stem)
    g_old = json.loads((OUT / "old" / "testvcf_genes.json").read_text())
    g_new = json.loads((OUT / "slim" / "testvcf_genes.json").read_text())
    vcf_differ = sorted(k for k in set(g_old) | set(g_new) if g_old.get(k) != g_new.get(k))
    result["comparison"] = {
        "s1_s6_identical": f"{len(same)}/{len(same) + len(differ)}", "s1_s6_differing": differ,
        "testvcf_identical": f"{len(set(g_old) & set(g_new)) - len(vcf_differ)}/{len(set(g_old) | set(g_new))}",
        "testvcf_differing": vcf_differ,
    }
    (OUT / "containers.json").write_text(json.dumps(result, indent=1, sort_keys=True))
    print(json.dumps(result["comparison"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
