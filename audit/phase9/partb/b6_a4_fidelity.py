#!/usr/bin/env python3
"""
B6 AC6: every input rebuilt by backend/tests/a4_inputs.py equals Part A's.

    backend/.venv/bin/python audit/phase9/partb/b6_a4_fidelity.py

Part A's inputs are local only (audit/phase9/a4/inputs/). Plain files are
compared byte for byte; compressed ones after decompression; the BCF by its
records (`bcftools view -H`), since the fixture was remade without the header
line that named a local path; the gzip bomb by its expanded bytes. A4-12c and
A4-15b are README.md, which has changed since Part A: they are compared with
README.md at Part A's commit (a932adc), which is what Part A copied.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "backend"))
from tests import a4_inputs  # noqa: E402

PART_A = REPO / "audit" / "phase9" / "a4" / "inputs"
PART_A_COMMIT = "a932adc"
PART_A_NAMES = {"A4-15a": "_base_copy.vcf", "A4-15b": "A4-12c_readme.vcf", "A4-11": None}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bcf_records(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".bcf") as handle:
        handle.write(data)
        handle.flush()
        proc = subprocess.run(["bcftools", "view", "--no-version", "-H", handle.name],
                              capture_output=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"bcftools exited {proc.returncode}: {proc.stderr.decode()[-300:]}")
    return sha(proc.stdout)


def main() -> int:
    rows, ok = [], True
    cases = a4_inputs.build()
    for case_id, case in cases.items():
        name = PART_A_NAMES.get(case_id, case.filename)
        if case_id == "A4-11":
            rows.append({"id": case_id, "verdict": "same file", "how": "test-data/demo/demo_variants_only.vcf itself"})
            continue
        if case_id == "A4-23":
            rows.append({"id": case_id, "verdict": "same input as A4-22", "how": "A4-22's file, four drugs"})
            continue
        part_a = (PART_A / name).read_bytes()
        if case_id in ("A4-04", "A4-05"):
            equal, how = gzip.decompress(case.data) == gzip.decompress(part_a), "after decompression"
        elif case_id == "A4-06":
            equal, how = bcf_records(case.data) == bcf_records(part_a), "records (bcftools view -H)"
        elif case_id in ("A4-12c", "A4-15b"):
            then = subprocess.run(["git", "show", f"{PART_A_COMMIT}:README.md"], cwd=REPO,
                                  capture_output=True, check=False)
            if then.returncode != 0:
                raise SystemExit(f"git show exited {then.returncode}")
            equal = then.stdout == part_a and case.data == (REPO / "README.md").read_bytes()
            how = f"Part A's file is README.md at {PART_A_COMMIT}; the rebuild is today's README.md"
        else:
            equal, how = case.data == part_a, "byte for byte"
        ok &= equal
        rows.append({"id": case_id, "verdict": "equal" if equal else "DIFFERS", "how": how,
                     "sha256": sha(case.data)})
    bomb_now = gzip.decompress(a4_inputs.bomb())
    bomb_then = gzip.decompress((PART_A / "A4-12f_bomb.vcf.gz").read_bytes())
    equal = bomb_now == bomb_then
    ok &= equal
    rows.append({"id": "A4-12f", "verdict": "equal" if equal else "DIFFERS",
                 "how": f"expanded bytes ({len(bomb_now):,})"})
    print(json.dumps({"all_equal": ok, "rows": rows}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
