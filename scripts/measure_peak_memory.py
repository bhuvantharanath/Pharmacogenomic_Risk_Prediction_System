"""
Peak resident memory of the backend while it serves one /analyze request.

Measures the WHOLE process tree (uvicorn + the JVM PharmCAT spawns per request),
because that sum is what a container memory limit counts. Sampled with `ps`
rather than psutil so it needs nothing installed.

Native, not containerised: no Docker runtime is present on this host. The
container adds its own small overhead on top of these numbers — see the note in
the report. The JVM heap is the dominant term either way, which is what the
JAVA_TOOL_OPTIONS sweep below is for.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Hardcoded: this script lives in a scratchpad outside the repo, so walking up
# from __file__ never finds `backend/` and spins at the filesystem root.
REPO = Path(__file__).resolve().parents[1]
assert (REPO / "backend").is_dir(), REPO

BACKEND = REPO / "backend"
VENV_PY = BACKEND / ".venv/bin/python"
_v = os.environ.get("MEM_VCF", "test-data/demo/demo_confident.vcf")
VCF = Path(_v) if Path(_v).is_absolute() else REPO / _v
JAR = REPO / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
JAVA_HOME = "/opt/homebrew/opt/openjdk@17"
PORT = 8971


def tree_rss_kb(root_pid: int) -> tuple[int, dict[str, int]]:
    """Total RSS in KB across root_pid and every descendant, plus a breakdown."""
    out = subprocess.run(["ps", "-Ao", "pid,ppid,rss,comm"],
                         capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines()[1:]:
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        try:
            rows.append((int(parts[0]), int(parts[1]), int(parts[2]), parts[3]))
        except ValueError:
            continue

    children: dict[int, list] = {}
    for pid, ppid, rss, comm in rows:
        children.setdefault(ppid, []).append((pid, rss, comm))

    total, breakdown, stack = 0, {}, [root_pid]
    by_pid = {pid: (rss, comm) for pid, _, rss, comm in rows}
    seen = set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        if pid in by_pid:
            rss, comm = by_pid[pid]
            total += rss
            key = "java" if "java" in comm.lower() else Path(comm).name
            breakdown[key] = breakdown.get(key, 0) + rss
        for child_pid, _, _ in children.get(pid, []):
            stack.append(child_pid)
    return total, breakdown


def wait_health(timeout: float = 90.0) -> float:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                if r.status == 200:
                    return time.time() - start
        except Exception:
            time.sleep(0.25)
    raise TimeoutError("backend never became healthy")


def post_vcf() -> tuple[int, float]:
    body, boundary = b"", "----pgmem"
    body += f"--{boundary}\r\n".encode()
    body += (b'Content-Disposition: form-data; name="file"; '
             b'filename="input.vcf"\r\n')
    body += b"Content-Type: text/plain\r\n\r\n"
    body += VCF.read_bytes() + b"\r\n"
    for drug in ("clopidogrel", "simvastatin", "azathioprine"):
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="drugs"\r\n\r\n{drug}\r\n'.encode()
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/analyze", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, time.time() - t0


def run(label: str, java_opts: str) -> dict:
    env = dict(os.environ)
    env.update({
        "PHARMCAT_JAR": str(JAR),
        "PHARMCAT_JAVA": f"{JAVA_HOME}/bin/java",
        "JAVA_HOME": JAVA_HOME,
        "EXPLANATION_MODE": "static",
        "CORS_ALLOWED_ORIGINS": "http://localhost:8080",
        "PHARMAGUARD_ENV": "development",
        "PYTHONUNBUFFERED": "1",
    })
    if java_opts:
        env["JAVA_TOOL_OPTIONS"] = java_opts
    else:
        env.pop("JAVA_TOOL_OPTIONS", None)

    log = open(f"/tmp/pgmem_{label}.log", "wb")
    proc = subprocess.Popen(
        [str(VENV_PY), "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(PORT), "--workers", "1"],
        cwd=BACKEND, env=env, stdout=log, stderr=subprocess.STDOUT,
        start_new_session=True)

    result = {"label": label, "java_tool_options": java_opts or "(unset)"}
    try:
        cold = wait_health()
        idle_kb, _ = tree_rss_kb(proc.pid)
        result["startup_seconds"] = round(cold, 2)
        result["idle_mb"] = round(idle_kb / 1024, 1)

        peak_kb, peak_break = idle_kb, {}
        done = {}

        import threading
        def sampler():
            nonlocal peak_kb, peak_break
            while not done:
                total, brk = tree_rss_kb(proc.pid)
                if total > peak_kb:
                    peak_kb, peak_break = total, brk
                time.sleep(0.05)

        t = threading.Thread(target=sampler, daemon=True)
        t.start()

        # MEM_CONCURRENCY>1 fires simultaneous /analyze calls. Each spawns its
        # own JVM: the runner uses asyncio.create_subprocess_exec with no
        # semaphore, so nothing serialises them and peak scales with in-flight
        # requests, not with worker count.
        n = int(os.environ.get("MEM_CONCURRENCY", "1"))
        if n == 1:
            status, elapsed = post_vcf()
            statuses = [status]
        else:
            import concurrent.futures as cf
            t0 = time.time()
            with cf.ThreadPoolExecutor(max_workers=n) as pool:
                out = list(pool.map(lambda _: post_vcf(), range(n)))
            elapsed = time.time() - t0
            statuses = [s for s, _ in out]
            status = statuses[0]
        done["x"] = True
        t.join(timeout=2)

        result["concurrency"] = n
        result["http_status"] = status
        result["all_statuses"] = statuses
        result["analyze_seconds"] = round(elapsed, 2)
        result["peak_mb"] = round(peak_kb / 1024, 1)
        result["peak_breakdown_mb"] = {
            k: round(v / 1024, 1) for k, v in sorted(
                peak_break.items(), key=lambda kv: -kv[1])}
    finally:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=15)
        except Exception:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass
        log.close()
    return result


if __name__ == "__main__":
    configs = [
        ("baseline", ""),
        ("xmx224", "-Xmx224m -XX:MaxMetaspaceSize=72m"),
        ("xmx192_serial", "-Xmx192m -XX:MaxMetaspaceSize=64m -XX:+UseSerialGC "
                          "-XX:TieredStopAtLevel=1 -Xss512k"),
        ("xmx320", "-Xmx320m -XX:MaxMetaspaceSize=96m"),
        ("xmx256", "-Xmx256m -XX:MaxMetaspaceSize=80m"),
        ("xmx192", "-Xmx192m -XX:MaxMetaspaceSize=64m"),
        ("xmx160_serial", "-Xmx160m -XX:MaxMetaspaceSize=64m -XX:+UseSerialGC "
                          "-XX:TieredStopAtLevel=1 -Xss512k"),
        ("xmx256_serial", "-Xmx256m -XX:MaxMetaspaceSize=80m -XX:+UseSerialGC "
                          "-XX:TieredStopAtLevel=1 -Xss512k"),
    ]
    only = sys.argv[1:] or None
    import json
    results = []
    for label, opts in configs:
        if only and label not in only:
            continue
        print(f"--- {label}: {opts or '(unset)'}", flush=True)
        try:
            r = run(label, opts)
        except Exception as exc:
            r = {"label": label, "java_tool_options": opts, "error": repr(exc)}
        results.append(r)
        print(json.dumps(r, indent=2), flush=True)
        for extra in range(int(os.environ.get("MEM_REPEATS", "1")) - 1):
            r2 = run(label, opts)
            results.append(r2)
            print(f"  repeat {extra+2}: status={r2.get('http_status')} "
                  f"peak={r2.get('peak_mb')}MB t={r2.get('analyze_seconds')}s",
                  flush=True)
    Path(os.environ.get("MEM_OUT", "/tmp/pgmem_results.json")).write_text(json.dumps(results, indent=2))
