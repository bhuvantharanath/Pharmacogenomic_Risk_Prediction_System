#!/usr/bin/env python3
"""
Validate PharmaGuard's FHIR export with the official HL7 FHIR validator.

    python scripts/validate_fhir_exports.py
    python scripts/validate_fhir_exports.py --responses DIR --report OUT.json

The release gate runs this as a required check, and so does CI
(audit/phase9/B9_PLAN.md, AC1 and AC7). It exits 0 only when every real
bundle has no error and the positive control has at least one.

THE STEPS, AND WHY EACH IS THERE

1. The validator is a pinned file (scripts/fhir_validator.json: version, URL,
   size, SHA-256), fetched and checked by fetch_pinned_artifacts.ensure. A jar
   on disk that does not match is refused, never replaced. A download must
   match before it is used.
2. `flutter test test/export_fixtures_test.dart` writes one bundle per
   /analyze response: the fixtures in app/test/fixtures/responses, or the
   responses in --responses, such as a live run's.
3. Positive control: a copy of one bundle with DiagnosticReport.code removed.
   The Genomic Report profile requires that code. A validator that finds
   nothing wrong with the copy is not validating, so the run fails.
4. One validator run covers every bundle, with the pinned IG and the
   terminology server off (-tx n/a), so the result does not depend on a
   remote server. Any error or fatal in a real bundle fails the run, as does
   a bundle the validator never reports on.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _common import REPO_ROOT, scrub
from fetch_pinned_artifacts import Pin, PinError, ensure

PIN_FILE = REPO_ROOT / "scripts" / "fhir_validator.json"
APP = REPO_ROOT / "app"
CONTROL = "positive-control.fhir.json"


def load_pin() -> tuple[Pin, dict]:
    config = json.loads(PIN_FILE.read_text())
    v = config["validator"]
    return Pin(v["path"], v["sha256"], v["bytes"], v["url"]), config


def write_bundles(out: Path, responses: Path | None) -> list[Path]:
    env = dict(os.environ, PHARMAGUARD_EXPORT_DIR=str(out))
    if responses is not None:
        env["PHARMAGUARD_EXPORT_RESPONSES"] = str(responses.resolve())
    flutter = shutil.which("flutter")
    if flutter is None:
        raise SystemExit("fhir validation: flutter is not on PATH")
    proc = subprocess.run([flutter, "test", "test/export_fixtures_test.dart"], cwd=APP, env=env,
                          capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        print(proc.stdout[-3000:], proc.stderr[-2000:], sep="\n", file=sys.stderr)
        raise SystemExit(f"fhir validation: writing the bundles failed (flutter test exit {proc.returncode})")
    bundles = sorted(out.glob("*.fhir.json"))
    if not bundles:
        raise SystemExit("fhir validation: no bundle was written")
    return bundles


def write_control(source: Path, out: Path) -> Path:
    bundle = json.loads(source.read_text())
    report = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "DiagnosticReport")
    # pop, not del: if the real bundles already lack the code, the run must
    # reach the validator and report that, not stop here.
    report.pop("code", None)
    control = out / CONTROL
    control.write_text(json.dumps(bundle, indent=1))
    return control


def validate(jar: Path, files: list[Path], config: dict, out: Path) -> dict[str, list[dict]]:
    java = shutil.which("java")
    if java is None:
        raise SystemExit("fhir validation: java is not on PATH")
    report = out / "validator-output.json"
    proc = subprocess.run(
        [java, "-jar", str(jar), *map(str, files), "-version", config["fhir_version"], "-ig", config["ig"],
         "-tx", config["terminology_server"], "-output", str(report)],
        capture_output=True, text=True, check=False)
    if not report.is_file():
        print(proc.stdout[-3000:], proc.stderr[-2000:], sep="\n", file=sys.stderr)
        raise SystemExit(f"fhir validation: the validator wrote no output (exit {proc.returncode})")
    data = json.loads(report.read_text())
    outcomes = [e["resource"] for e in data["entry"]] if data.get("resourceType") == "Bundle" else [data]
    issues: dict[str, list[dict]] = {}
    for oo in outcomes:
        source = next((x.get("valueString") for x in oo.get("extension", [])
                       if x.get("url", "").endswith("operationoutcome-file")), None)
        if source is None:
            raise SystemExit("fhir validation: an outcome does not name the file it is about")
        issues[Path(source).name] = oo.get("issue", [])
    return issues


def summarise(issues: dict[str, list[dict]], expected: list[str]) -> dict:
    files = {}
    warnings: collections.Counter = collections.Counter()
    for name in expected:
        found = issues.get(name)
        counts = collections.Counter(i["severity"] for i in found or [])
        files[name] = {"reported": found is not None, **{s: counts.get(s, 0) for s in
                                                          ("fatal", "error", "warning", "information")}}
        if name != CONTROL:
            files[name]["errors"] = [f"{(i.get('expression') or ['?'])[0]}: {i.get('details', {}).get('text', '')}"
                                     for i in found or [] if i["severity"] in ("error", "fatal")]
            for i in found or []:
                if i["severity"] == "warning":
                    warnings[i.get("details", {}).get("text", "")] += 1
    real = [n for n in expected if n != CONTROL]
    control = files[CONTROL]
    passed = (all(files[n]["reported"] and files[n]["error"] == 0 and files[n]["fatal"] == 0 for n in real)
              and control["reported"] and control["error"] + control["fatal"] >= 1)
    return {"files": files, "warnings": dict(warnings.most_common()), "passed": passed,
            "bundles": len(real), "control_errors": control["error"] + control["fatal"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--responses", type=Path, help="export these /analyze responses instead of the fixtures")
    parser.add_argument("--report", type=Path, help="write the summary here as JSON")
    args = parser.parse_args(argv)

    pin, config = load_pin()
    try:
        state = ensure(pin)
    except PinError as exc:
        print(f"fhir validation: {scrub(exc)}", file=sys.stderr)
        return 2
    print(f"validator {config['validator']['version']}: {state}, size and SHA-256 match the pin")

    with tempfile.TemporaryDirectory(prefix="pharmaguard-fhir-") as tmp:
        out = Path(tmp)
        bundles = write_bundles(out, args.responses)
        control = write_control(bundles[0], out)
        issues = validate(REPO_ROOT / pin.path, [*bundles, control], config, out)
        summary = summarise(issues, [b.name for b in bundles] + [CONTROL])

    for name, f in summary["files"].items():
        print(f"  {name}: {f['error']} errors, {f['fatal']} fatal, {f['warning']} warnings"
              + ("" if f["reported"] else "  NOT REPORTED BY THE VALIDATOR"))
        for line in f.get("errors", []):
            print(f"    error {line}")
    for text, n in summary["warnings"].items():
        print(f"  warning x{n}: {text}")
    if args.report:
        args.report.write_text(json.dumps({"validator": config["validator"]["version"], "ig": config["ig"],
                                           "fhir_version": config["fhir_version"],
                                           "terminology_server": config["terminology_server"], **summary},
                                          indent=1) + "\n")
    verdict = "PASS" if summary["passed"] else "FAIL"
    print(f"FHIR validation: {verdict} ({summary['bundles']} bundles; "
          f"positive control rejected with {summary['control_errors']} errors)")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
