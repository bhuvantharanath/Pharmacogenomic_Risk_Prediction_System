"""Measure the already-built release image under its real Docker cgroup limit."""
import asyncio
import datetime
import hashlib
import json
import sys
from pathlib import Path
import subprocess
import threading
import time

import httpx

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REAL_INCOMPLETE = ROOT / "audit-output/2026-09-26/derived/NA18526.1000G2022.vcf.gz"
NORMAL_CONTROL = ROOT / "test-data/normal_metabolizer_control.vcf"
REAL_COMPLETE = ROOT / "audit-output/2026-09-30-f4/NA18526.observed.vcf"


def command(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip()


def inspect(name):
    return json.loads(command("docker", "inspect", name))[0]


def cgroup(name):
    result = command("docker", "exec", name, "sh", "-c",
                     "cat /sys/fs/cgroup/memory.current; cat /sys/fs/cgroup/memory.peak; cat /sys/fs/cgroup/memory.events; cat /sys/fs/cgroup/memory.stat")
    lines = result.splitlines()
    return {"current_bytes": int(lines[0]), "peak_bytes": int(lines[1]),
            "events": {k: int(v) for k, v in (line.split() for line in lines[2:8])},
            "stat": {k: int(v) for k, v in (line.split() for line in lines[8:])}}


class Sampler:
    def __init__(self, name):
        self.name = name
        self.samples = []
        self.stop = threading.Event()

    def __enter__(self):
        def poll():
            while not self.stop.is_set():
                try:
                    value = cgroup(self.name)
                    top = command("docker", "top", self.name, "-eo", "pid,comm,rss")
                    processes = []
                    for line in top.splitlines()[1:]:
                        parts = line.split()
                        if len(parts) >= 3 and parts[-1].isdigit():
                            processes.append({"pid": int(parts[0]), "command": parts[1], "rss_kib": int(parts[-1])})
                    self.samples.append({"time": time.monotonic(), "memory_current_bytes": value["current_bytes"],
                                         "processes": processes})
                except Exception as exc:
                    self.samples.append({"time": time.monotonic(), "error": str(exc)})
                self.stop.wait(0.15)
        self.thread = threading.Thread(target=poll, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join(timeout=5)


def post(port, endpoint, path, case, drugs="clopidogrel,simvastatin,fluorouracil,azathioprine,warfarin,codeine"):
    start = time.monotonic()
    with httpx.Client(timeout=180) as client, path.open("rb") as f:
        r = client.post(f"http://127.0.0.1:{port}/{endpoint}", files={"file": (path.name, f)},
                        data={"drugs": drugs} if endpoint == "analyze" else {})
    duration = time.monotonic() - start
    try:
        payload = r.json()
    except ValueError:
        payload = {"non_json_response": r.text[:1000]}
    (OUT / f"{case}.json").write_text(json.dumps(payload, indent=2) + "\n")
    result = {"case": case, "endpoint": endpoint, "input": str(path.relative_to(ROOT)),
              "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "status": r.status_code, "seconds": round(duration, 3)}
    if endpoint == "coverage":
        result["answerable_drugs"] = payload.get("answerable_drugs")
        result["genes_passing"] = payload.get("genes_passing")
    else:
        result["labels"] = {a["drug"]: a["risk_assessment"]["risk_label"] for a in payload.get("analyses", [])}
        result["error_code"] = payload.get("error_code")
    return result


def envelope(name, label, task):
    before = cgroup(name)
    with Sampler(name) as sampler:
        try:
            results = task()
        except Exception as exc:
            results = {"exception": repr(exc)}
    try:
        after = cgroup(name)
    except Exception as exc:
        after = {"error": repr(exc)}
    state = inspect(name)["State"]
    return {"label": label, "before": before, "after": after,
            "sample_count": len(sampler.samples),
            "sampled_peak_bytes": max((s.get("memory_current_bytes", 0) for s in sampler.samples), default=0),
            "sampled_jvm_rss_kib_peak": max((sum(p["rss_kib"] for p in s.get("processes", []) if p["command"] == "java") for s in sampler.samples), default=0),
            "sampled_python_rss_kib_peak": max((sum(p["rss_kib"] for p in s.get("processes", []) if p["command"] in ("uvicorn", "python3", "python")) for s in sampler.samples), default=0),
            "sampled_jvm_count_peak": max((sum(p["command"] == "java" for p in s.get("processes", [])) for s in sampler.samples), default=0),
            "samples": sampler.samples, "container_state": state, "results": results}


def main():
    for path in (REAL_INCOMPLETE, NORMAL_CONTROL, REAL_COMPLETE):
        assert path.exists(), path
    if len(sys.argv) == 1:
        name, port, heap_flags, run_id = "pgx-f5-main", 8767, "-Xmx256m -XX:MaxMetaspaceSize=80m", "before"
    elif len(sys.argv) == 5:
        name, port, heap_flags, run_id = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    else:
        raise SystemExit("Usage: measure.py [container_name port java_tool_options run_id]")
    config = inspect(name)
    assert config["HostConfig"]["Memory"] == 512 * 1024 * 1024
    assert config["HostConfig"]["MemorySwap"] == 512 * 1024 * 1024
    env = dict(x.split("=", 1) for x in config["Config"]["Env"])
    for key, expected in {"JAVA_TOOL_OPTIONS": heap_flags,
                          "MAX_CONCURRENT_PHARMCAT": "1", "PHARMCAT_QUEUE_TIMEOUT_SECONDS": "90",
                          "PHARMCAT_TIMEOUT_SECONDS": "120", "EXPLANATION_MODE": "static", "STRICT_PHARMCAT": "1"}.items():
        assert env[key] == expected, key
    data = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "container_name": name, "image_id": config["Image"], "container_id": config["Id"],
            "linux_platform": command("docker", "info", "--format", "{{.OSType}}/{{.Architecture}}"),
            "memory_limit_bytes": config["HostConfig"]["Memory"],
            "memory_swap_limit_bytes": config["HostConfig"]["MemorySwap"],
            "configured_environment": {k: env[k] for k in ("JAVA_TOOL_OPTIONS", "MAX_CONCURRENT_PHARMCAT", "PHARMCAT_QUEUE_TIMEOUT_SECONDS", "PHARMCAT_TIMEOUT_SECONDS", "EXPLANATION_MODE", "STRICT_PHARMCAT")},
            "cases": []}
    def keep(record):
        data["cases"].append(record)
        (OUT / f"measurements-{run_id}.json").write_text(json.dumps(data, indent=2) + "\n")

    with httpx.Client(timeout=20) as client:
        for endpoint in ("health", "ready"):
            start = time.monotonic()
            r = client.get(f"http://127.0.0.1:{port}/{endpoint}")
            assert r.status_code == 200
            keep({"label": endpoint, "status": r.status_code, "seconds": round(time.monotonic() - start, 3), "cgroup": cgroup(name)})
    keep(envelope(name, "coverage_incomplete_real", lambda: post(port, "coverage", REAL_INCOMPLETE, f"{run_id}-coverage-incomplete-real")))
    keep(envelope(name, "analysis_incomplete_real", lambda: post(port, "analyze", REAL_INCOMPLETE, f"{run_id}-analysis-incomplete-real")))
    keep(envelope(name, "analysis_complete_synthetic", lambda: post(port, "analyze", NORMAL_CONTROL, f"{run_id}-analysis-complete-synthetic")))
    keep(envelope(name, "analysis_complete_real", lambda: post(port, "analyze", REAL_COMPLETE, f"{run_id}-analysis-complete-real")))
    keep(envelope(name, "sequential_repeat", lambda: [post(port, "analyze", NORMAL_CONTROL, f"{run_id}-sequential-{i}") for i in range(2)]))

    def triple():
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=3) as pool:
            return list(pool.map(lambda i: post(port, "analyze", REAL_INCOMPLETE, f"{run_id}-concurrent-{i}"), range(3)))
    keep(envelope(name, "three_concurrent_large_real", triple))
    print(json.dumps({"cases": len(data["cases"]), "cgroup_peak_mib": round(cgroup(name)["peak_bytes"] / 1048576, 2),
                      "events": cgroup(name)["events"], "status": [r["status"] for item in data["cases"][-6:] for r in (item["results"] if isinstance(item["results"], list) else [item["results"]])]}, indent=2))


if __name__ == "__main__":
    main()
