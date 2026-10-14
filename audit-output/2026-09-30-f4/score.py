"""Run frozen read-derived inputs through real local HTTP and PharmCAT paths."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import httpx
from prepare import OUT, ROOT, digest, save


def main():
    frozen = OUT / "frozen-protocol.json"
    assert digest(frozen) == (OUT / "frozen-protocol.sha256").read_text().strip()
    protocol = json.loads(frozen.read_text())
    for name, expected in protocol["hashes"].items():
        assert digest(ROOT / name) == expected, name
    jar = ROOT / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
    java = "/opt/homebrew/opt/openjdk/bin/java"
    if sys.argv[1:] == ["direct-only"]:
        direct(protocol, jar, java, json.loads((OUT / "scoring.json").read_text()))
        return
    env = dict(os.environ, PHARMCAT_JAR=str(jar), PHARMCAT_JAVA=java, EXPLANATION_MODE="static", STRICT_PHARMCAT="1")
    command = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8766"]
    summary = {"started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "frozen_protocol_sha256": digest(frozen), "server_command": command,
               "explanation_mode": "static", "samples": {}}
    with (OUT / "api-server.log").open("w") as log:
        server = subprocess.Popen(command, cwd=ROOT / "backend", env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            with httpx.Client(base_url="http://127.0.0.1:8766", timeout=180) as client:
                for attempt in range(60):
                    if server.poll() is not None:
                        raise RuntimeError("Local API failed to start; inspect api-server.log")
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.ConnectError:
                        pass
                    time.sleep(0.5)
                else:
                    raise RuntimeError("API readiness timeout")
                for sample in protocol["samples"]:
                    path = OUT / f"{sample}.observed.vcf"
                    evidence = json.loads((OUT / f"{sample}.evidence.json").read_text())
                    assert digest(path) == evidence["observed_vcf_sha256"]
                    record = {"input_sha256": digest(path)}
                    for endpoint in ("coverage", "analyze"):
                        with path.open("rb") as f:
                            response = client.post("/" + endpoint, files={"file": (path.name, f, "text/plain")},
                                data={"drugs": "clopidogrel,simvastatin,fluorouracil,azathioprine,warfarin,codeine"} if endpoint == "analyze" else {})
                        payload = response.json()
                        save(f"{sample}.{endpoint}.json", payload)
                        record[endpoint + "_http_status"] = response.status_code
                        if endpoint == "coverage":
                            record["answerable_drugs"] = payload.get("answerable_drugs")
                        else:
                            record["labels"] = {a["drug"]: a["risk_assessment"]["risk_label"] for a in payload.get("analyses", [])}
                    summary["samples"][sample] = record
                    save("scoring.json", summary)
                    print(sample, record, flush=True)
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    direct(protocol, jar, java, summary)


def direct(protocol, jar, java, summary):
    sys.path.insert(0, str(ROOT / "backend"))
    from app.pharmcat_runner import parse_report
    for sample in protocol["samples"]:
        directory = OUT / (sample + ".pharmcat")
        directory.mkdir(exist_ok=True)
        cmd = [java, "-jar", str(jar), "-vcf", str(OUT / f"{sample}.observed.vcf"), "-o", str(directory), "-reporterJson"]
        with (directory / "execution.log").open("w") as log:
            result = subprocess.run(cmd, cwd=directory, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        summary["samples"][sample]["direct_pharmcat"] = {"command": cmd, "exit_code": result.returncode}
        reports = list(directory.glob("*.report.json"))
        if result.returncode == 0 and len(reports) == 1:
            parsed = parse_report(json.loads(reports[0].read_text()), sample_hint=sample)
            save(f"{sample}.parsed.json", parsed.model_dump(mode="json"))
        else:
            summary["samples"][sample]["direct_report_files"] = [p.name for p in directory.iterdir()]
        save("scoring.json", summary)
    summary["completed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save("scoring.json", summary)


if __name__ == "__main__":
    main()
