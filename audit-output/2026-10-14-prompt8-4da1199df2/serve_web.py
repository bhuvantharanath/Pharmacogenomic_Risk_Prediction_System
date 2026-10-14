"""Serve a task-owned Flutter release build on 127.0.0.1:3000 and record receipts.
Usage: serve_web.py <label> <build-dir>"""
import datetime, json, os, signal, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
label, build = sys.argv[1], Path(sys.argv[2]).resolve()
servers = HERE / "servers"; servers.mkdir(exist_ok=True)
argv = [sys.executable, "-m", "http.server", "3000", "--bind", "127.0.0.1", "--directory", str(build)]
def save(name, payload): (servers / f"{label}-web.{name}.json").write_text(json.dumps(payload, indent=1) + "\n")
save("command", {"argv": argv, "cwd": str(HERE), "started": datetime.datetime.now(datetime.timezone.utc).isoformat()})
with (servers / f"{label}-web.log").open("w") as log:
    p = subprocess.Popen(argv, cwd=HERE, stdout=log, stderr=subprocess.STDOUT)
    save("pid", {"pid": p.pid, "launcher_pid": os.getpid()})
    signal.signal(signal.SIGTERM, lambda *_: p.terminate()); signal.signal(signal.SIGINT, lambda *_: p.terminate())
    code = p.wait()
save("exit", {"exit_code": code, "at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
