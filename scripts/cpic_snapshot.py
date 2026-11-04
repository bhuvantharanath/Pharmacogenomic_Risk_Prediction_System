#!/usr/bin/env python3
"""
A pinned snapshot of CPIC's API, and the diff against what PharmCAT embeds.

    python scripts/cpic_snapshot.py --fetch     # refresh the vendored snapshot
    python scripts/cpic_snapshot.py --diff      # vendored snapshot vs the pinned jar
    python scripts/cpic_snapshot.py --check-live --report-dir out/   # the weekly watch
    python scripts/cpic_snapshot.py --compare-to DIR [--pharmcat-tag vX.Y.Z]  # same, offline

WHY A SNAPSHOT AT ALL

Every CPIC string this application shows comes from PharmCAT's report, and the
105-row mapping validation reads the same jar, so the jar is the only knowledge
source the build uses. Nothing recorded what CPIC itself said when that jar was
validated, so nothing could notice when CPIC moved on. The snapshot is that
record: CPIC's own allele-function and recommendation rows for our genes and
drugs, fetched from the public PostgREST API with the date and per-file SHA-256.

`--diff` shows exactly where the jar and CPIC disagree. The disagreements that
are expected — rows PharmCAT synthesises itself, alleles PharmCAT cannot define —
are enumerated in `EXPECTED_DIFFERENCES`; anything else is new and must be
explained before it is accepted (tests/test_cpic_snapshot.py).

THE WATCH

`--check-live` fetches CPIC's current tables and PharmCAT's latest release and
compares them with what this build pins: the vendored snapshot, row by row on
every fetched field, and the pinned PharmCAT version. It never edits the
snapshot. Exit 0 means nothing changed, 1 means something did (the report names
each row), 2 means the check could not be completed — which is not "no change".
`.github/workflows/knowledge-watch.yml` runs it weekly and opens one issue.
`--compare-to` runs the same comparison against a directory instead of the
network, which is how the tests exercise it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from _common import REPO_ROOT, scrub

API = "https://api.cpicpgx.org/v1"
SNAPSHOT_DIR = REPO_ROOT / "test-data" / "reference" / "cpic_snapshot"
JAR = REPO_ROOT / "test-data" / "reference" / "tools" / "pharmcat-3.4.0-all.jar"
BUNDLE = REPO_ROOT / "backend" / "app" / "data" / "compatible_bundle.json"
PHARMCAT_LATEST = "https://api.github.com/repos/PharmGKB/PharmCAT/releases/latest"
USER_AGENT = "PharmaGuard-cpic-snapshot/1 (research; github.com/bhuvantharanath)"

#: The genes PharmaGuard calls from a VCF (CYP2D6 is never called here).
GENES = ("CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "NUDT15", "DPYD")
#: The drugs whose CPIC rows the application or its validation reads.
DRUGS = ("azathioprine", "capecitabine", "clopidogrel", "codeine", "fluorouracil",
         "simvastatin", "warfarin")

ENDPOINTS = {
    "allele.json": (
        "/allele?genesymbol=in.(" + ",".join(GENES) + ")"
        "&select=genesymbol,name,clinicalfunctionalstatus,activityvalue&order=genesymbol,name"
    ),
    "recommendation.json": (
        "/recommendation_view?drugname=in.(" + ",".join(DRUGS) + ")"
        "&select=drugname,guidelinename,lookupkey,population,classification,"
        "drugrecommendation,implications&order=drugname,population"
    ),
}

#: Known, explained disagreements between the pinned jar and CPIC's API. Any
#: difference not listed here fails tests/test_cpic_snapshot.py.
EXPECTED_DIFFERENCES = {
    # PharmCAT 3.4.0's NUDT15 definitions have no *2; CPIC assigns it No
    # function. *2 shares rs116855232 (R139C) with *3, also No function.
    "allele_function": [["NUDT15", "*2", None, "No function"]],
    # Rows PharmCAT synthesises that are not CPIC recommendations: an
    # instructional row for CYP2D6 duplications, and warfarin's twelve
    # "use a pharmacogenetic dosing algorithm" pointers (CPIC's warfarin
    # guidance is an algorithm, not per-genotype text).
    "pharmcat_only_rows": {"codeine": 1, "warfarin": 12},
    "api_only_rows": {},
    "text_differences": [],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _get(path: str) -> bytes:
    # The API refuses Python's default "Python-urllib" agent with 403, so the
    # request names itself.
    request = urllib.request.Request(
        f"{API}{path}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise RuntimeError(f"{path}: HTTP {response.status}")
        return response.read()


def fetch(dest: Path = SNAPSHOT_DIR) -> dict:
    """Fetch every endpoint and write files plus a manifest of their hashes."""
    dest.mkdir(parents=True, exist_ok=True)
    fetched = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    files = {}
    for name, path in ENDPOINTS.items():
        raw = _get(path)
        rows = json.loads(raw)
        if not isinstance(rows, list) or not rows:
            raise RuntimeError(f"{name}: expected a non-empty JSON list")
        body = (json.dumps(rows, indent=1, sort_keys=True) + "\n").encode()
        (dest / name).write_bytes(body)
        files[name] = {"url": API + path, "rows": len(rows), "sha256": sha256_bytes(body)}
    manifest = {"source": "CPIC public API (PostgREST)", "api": API,
                "fetched_utc": fetched, "files": files}
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


def _population(value: str | None) -> str:
    """PharmCAT leaves the general population blank; the API names it."""
    value = (value or "").strip().lower()
    return "general" if value in ("", "n/a", "general") else value


def _text(value: str | None) -> str:
    # Strip real tags before unescaping, so "&lt;20mg/day" survives as text.
    value = html.unescape(re.sub(r"</?[a-zA-Z][^>]*>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def jar_tables(jar: Path = JAR) -> tuple[dict, dict]:
    """(allele functions by gene, recommendation text by key) from the jar."""
    with zipfile.ZipFile(jar) as zf:
        functions = {}
        for gene in GENES:
            data = json.loads(zf.read(f"org/pharmgkb/pharmcat/phenotype/{gene}.json"))
            functions[gene] = {a["name"]: a.get("functionValue")
                               for a in data.get("namedAlleles", [])}
        guidance = json.loads(zf.read("org/pharmgkb/pharmcat/reporter/prescribing_guidance.json"))
    rows = {}
    for guideline in guidance["guidelines"]:
        if guideline["guideline"]["source"] != "CPIC":
            continue
        for rec in guideline.get("recommendations", []):
            for chem in rec.get("relatedChemicals", []):
                if chem["name"] in DRUGS:
                    lookup = rec["lookupKey"][0] if rec["lookupKey"] else {}
                    key = (chem["name"], json.dumps(lookup, sort_keys=True),
                           _population(rec.get("population")))
                    rows[key] = _text(rec["text"]["html"])
    return functions, rows


def snapshot_tables(snapshot: Path = SNAPSHOT_DIR) -> tuple[dict, dict]:
    alleles = json.loads((snapshot / "allele.json").read_text())
    functions: dict = {gene: {} for gene in GENES}
    for row in alleles:
        functions[row["genesymbol"]][row["name"]] = row.get("clinicalfunctionalstatus")
    recs = json.loads((snapshot / "recommendation.json").read_text())
    rows = {}
    for row in recs:
        key = (row["drugname"], json.dumps(row.get("lookupkey") or {}, sort_keys=True),
               _population(row.get("population")))
        rows[key] = _text(row.get("drugrecommendation"))
    return functions, rows


def diff(snapshot: Path = SNAPSHOT_DIR, jar: Path = JAR) -> dict:
    """Every disagreement between the jar and the snapshot, as plain data."""
    jar_f, jar_r = jar_tables(jar)
    api_f, api_r = snapshot_tables(snapshot)
    function_rows = []
    for gene in GENES:
        for name in sorted(set(jar_f[gene]) | set(api_f[gene])):
            a, b = jar_f[gene].get(name), api_f[gene].get(name)
            if (a or None) != (b or None):
                function_rows.append([gene, name, a, b])
    pharmcat_only: dict = {}
    api_only: dict = {}
    text_rows = []
    for key in sorted(set(jar_r) | set(api_r)):
        if key not in api_r:
            pharmcat_only[key[0]] = pharmcat_only.get(key[0], 0) + 1
        elif key not in jar_r:
            api_only[key[0]] = api_only.get(key[0], 0) + 1
        elif jar_r[key] != api_r[key]:
            text_rows.append({"drug": key[0], "lookup": json.loads(key[1]),
                              "population": key[2], "pharmcat": jar_r[key], "cpic": api_r[key]})
    return {"allele_function": function_rows, "pharmcat_only_rows": pharmcat_only,
            "api_only_rows": api_only, "text_differences": text_rows}


def verify_manifest(snapshot: Path = SNAPSHOT_DIR) -> list[str]:
    """Problems with the vendored files' recorded hashes; empty when intact."""
    manifest = json.loads((snapshot / "manifest.json").read_text())
    problems = []
    for name, entry in manifest["files"].items():
        path = snapshot / name
        if not path.is_file():
            problems.append(f"missing {name}")
        elif sha256_bytes(path.read_bytes()) != entry["sha256"]:
            problems.append(f"{name}: sha256 differs from manifest")
    return problems


# --------------------------------------------------------------------------- #
# The watch: the pinned snapshot and PharmCAT release vs what exists now
# --------------------------------------------------------------------------- #

#: How a row is identified, so an edited row reads as "changed" rather than as
#: a removal plus an addition. The comparison itself covers every field.
ROW_KEYS = {
    "allele.json": ("genesymbol", "name"),
    "recommendation.json": ("drugname", "guidelinename", "lookupkey", "population"),
}
#: Enough of each changed row for the issue to be read without the artifact.
REPORT_ROW_LIMIT = 40
REPORT_TEXT_LIMIT = 600


def _rows_by_key(path: Path, key_fields: tuple[str, ...]) -> dict[str, list[str]]:
    rows = json.loads(path.read_text())
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path}: expected a non-empty JSON list")
    grouped: dict[str, list[str]] = {}
    for row in rows:
        key = json.dumps([row.get(field) for field in key_fields], sort_keys=True)
        grouped.setdefault(key, []).append(json.dumps(row, sort_keys=True))
    return {key: sorted(group) for key, group in grouped.items()}


def compare_tables(pinned: Path, current: Path) -> list[dict]:
    """Every row that was added, removed or changed between two snapshots."""
    changes = []
    for name, key_fields in ROW_KEYS.items():
        before = _rows_by_key(pinned / name, key_fields)
        after = _rows_by_key(current / name, key_fields)
        for key in sorted(set(before) | set(after)):
            old, new = before.get(key), after.get(key)
            if old == new:
                continue
            kind = "added" if old is None else "removed" if new is None else "changed"
            changes.append({
                "table": name, "kind": kind,
                "key": dict(zip(key_fields, json.loads(key))),
                "before": [json.loads(r) for r in old or []],
                "after": [json.loads(r) for r in new or []],
            })
    return changes


def _version(tag: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", tag.strip())
    if not match:
        raise ValueError(f"unrecognised PharmCAT release tag {tag!r}")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def pinned_pharmcat_version() -> str:
    return json.loads(BUNDLE.read_text())["pharmcat"]["engine_version"]


def release_change(latest_tag: str, pinned: str) -> dict | None:
    """The newer release, or None when the pinned one is the latest."""
    if _version(latest_tag) > _version(pinned):
        return {"pinned": pinned, "latest": latest_tag}
    return None


def latest_pharmcat_tag() -> str:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    # Unauthenticated calls share a 60-an-hour budget per runner IP; the
    # workflow's own token avoids failing on someone else's usage.
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    request = urllib.request.Request(PHARMCAT_LATEST, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"PharmCAT releases: HTTP {response.status}")
        tag = json.loads(response.read()).get("tag_name")
    if not tag:
        raise RuntimeError("PharmCAT releases: no tag_name in the latest release")
    return tag


def _clip(value) -> str:
    text = json.dumps(value, sort_keys=True)
    return text if len(text) <= REPORT_TEXT_LIMIT else text[:REPORT_TEXT_LIMIT] + " …"


def render_report(result: dict) -> str:
    """The issue body and job summary: what was compared, and what differs."""
    manifest = result.get("pinned_manifest") or {}
    lines = [
        f"## Knowledge watch — {result['status']}",
        "",
        f"- Checked: {result['checked_utc']}",
        f"- Pinned CPIC snapshot: fetched {manifest.get('fetched_utc', 'unknown')} "
        f"(`test-data/reference/cpic_snapshot/`)",
        f"- Compared with: {result['compared_with']}",
        f"- Pinned PharmCAT: {result.get('pinned_pharmcat') or 'unknown'}; latest release: "
        f"{result.get('latest_pharmcat') or 'not checked'}",
        "",
    ]
    if result["status"] == "error":
        lines += ["The check could not be completed, so nothing is known about whether "
                  "CPIC or PharmCAT changed.", "", f"    {result['error']}", ""]
        return "\n".join(lines)
    changes = result["changes"]
    release = result["release"]
    if not changes and not release:
        lines += ["No difference: CPIC's tables match the pinned snapshot on every "
                  "fetched field, and no newer PharmCAT release exists.", ""]
        return "\n".join(lines)
    if release:
        lines += [f"**PharmCAT {release['latest']} is newer than the pinned {release['pinned']}.**", ""]
    if changes:
        counts: dict[str, int] = {}
        for change in changes:
            label = f"{change['table']} {change['kind']}"
            counts[label] = counts.get(label, 0) + 1
        lines += ["**CPIC rows that differ from the pinned snapshot:** "
                  + ", ".join(f"{n} {label}" for label, n in sorted(counts.items())), ""]
        for change in changes[:REPORT_ROW_LIMIT]:
            lines.append(f"- `{change['table']}` {change['kind']}: `{_clip(change['key'])}`")
            if change["before"]:
                lines.append(f"  - before: `{_clip(change['before'])}`")
            if change["after"]:
                lines.append(f"  - after: `{_clip(change['after'])}`")
        if len(changes) > REPORT_ROW_LIMIT:
            lines.append(f"- … and {len(changes) - REPORT_ROW_LIMIT} more; run the command "
                         "below for the full list.")
        lines.append("")
    lines += [
        "### What to do",
        "",
        "Nothing is changed automatically. A person decides whether the change matters:",
        "",
        "1. `python scripts/cpic_snapshot.py --check-live --report-dir out/` reproduces this.",
        "2. If CPIC changed: `--fetch` refreshes the snapshot and `--diff` shows where the "
        "pinned jar now disagrees with CPIC. `tests/test_cpic_snapshot.py` fails until "
        "each new difference is explained in `EXPECTED_DIFFERENCES` or the jar is updated.",
        "3. If PharmCAT released: upgrading the jar is a scientific-core change and needs "
        "the full re-validation (label mapping, cohort, adversarial VCFs, evaluation re-bind).",
        "",
    ]
    return "\n".join(lines)


def run_watch(compare_to: Path | None, pharmcat_tag: str | None, report_dir: Path | None,
              save_live: Path | None = None) -> int:
    """
    Compare what is pinned with what exists. Returns 0 (no change), 1 (change)
    or 2 (could not check). Live when `compare_to` is None.
    """
    result: dict = {
        "status": "error",
        "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "compared_with": str(compare_to) if compare_to else f"CPIC API {API} (live)",
        "pinned_manifest": None, "pinned_pharmcat": None, "latest_pharmcat": None,
        "changes": [], "release": None, "error": None,
    }
    try:
        problems = verify_manifest()
        if problems:
            raise RuntimeError(f"the pinned snapshot is not intact: {problems}")
        result["pinned_manifest"] = json.loads((SNAPSHOT_DIR / "manifest.json").read_text())
        result["pinned_pharmcat"] = pinned_pharmcat_version()
        with tempfile.TemporaryDirectory() as scratch:
            if compare_to is None:
                current = save_live or Path(scratch)
                fetch(current)
                pharmcat_tag = latest_pharmcat_tag()
            else:
                current = compare_to
            result["changes"] = compare_tables(SNAPSHOT_DIR, current)
        if pharmcat_tag:
            result["latest_pharmcat"] = pharmcat_tag
            result["release"] = release_change(pharmcat_tag, result["pinned_pharmcat"])
        result["status"] = "changed" if result["changes"] or result["release"] else "unchanged"
    except Exception as exc:  # noqa: BLE001 — any failure means "not checked", never "no change"
        result["error"] = scrub(f"{type(exc).__name__}: {exc}")
    report = render_report(result)
    print(report)
    if report_dir is not None:
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "knowledge-watch.md").write_text(report + "\n")
        (report_dir / "knowledge-watch.json").write_text(json.dumps(result, indent=1) + "\n")
    return {"unchanged": 0, "changed": 1}.get(result["status"], 2)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fetch", action="store_true", help="refresh the vendored snapshot")
    ap.add_argument("--diff", action="store_true", help="snapshot vs the pinned jar")
    ap.add_argument("--check-live", action="store_true",
                    help="compare the pinned snapshot and PharmCAT version with what exists now")
    ap.add_argument("--compare-to", type=Path, metavar="DIR",
                    help="offline watch: compare the pinned snapshot with the tables in DIR")
    ap.add_argument("--pharmcat-tag", metavar="TAG",
                    help="with --compare-to: treat TAG as PharmCAT's latest release")
    ap.add_argument("--report-dir", type=Path, metavar="DIR",
                    help="write knowledge-watch.md and knowledge-watch.json here")
    ap.add_argument("--save-live", type=Path, metavar="DIR",
                    help="with --check-live: keep the fetched tables in DIR")
    args = ap.parse_args(argv)
    if args.check_live or args.compare_to:
        if args.check_live and args.compare_to:
            ap.error("--check-live and --compare-to are alternatives")
        if args.pharmcat_tag and not args.compare_to:
            ap.error("--pharmcat-tag only applies to --compare-to; --check-live asks GitHub")
        return run_watch(args.compare_to, args.pharmcat_tag, args.report_dir, args.save_live)
    if args.fetch:
        manifest = fetch()
        print(json.dumps(manifest, indent=1))
    if args.diff:
        problems = verify_manifest()
        result = diff()
        print(json.dumps({"manifest_problems": problems, **result}, indent=1))
        return 0 if not problems and result == EXPECTED_DIFFERENCES else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
