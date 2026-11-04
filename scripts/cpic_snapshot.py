#!/usr/bin/env python3
"""
A pinned snapshot of CPIC's API, and the diff against what PharmCAT embeds.

    python scripts/cpic_snapshot.py --fetch     # refresh the vendored snapshot
    python scripts/cpic_snapshot.py --diff      # vendored snapshot vs the pinned jar

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
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

from _common import REPO_ROOT

API = "https://api.cpicpgx.org/v1"
SNAPSHOT_DIR = REPO_ROOT / "test-data" / "reference" / "cpic_snapshot"
JAR = REPO_ROOT / "test-data" / "reference" / "tools" / "pharmcat-3.4.0-all.jar"

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
        headers={"User-Agent": "PharmaGuard-cpic-snapshot/1 (research; github.com/bhuvantharanath)",
                 "Accept": "application/json"},
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fetch", action="store_true", help="refresh the vendored snapshot")
    ap.add_argument("--diff", action="store_true", help="snapshot vs the pinned jar")
    args = ap.parse_args(argv)
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
