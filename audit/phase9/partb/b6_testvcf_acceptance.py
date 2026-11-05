#!/usr/bin/env python3
"""
B6 zero-regression: does validation accept the same PharmCAT test VCFs as before?

    backend/.venv/bin/python audit/phase9/partb/b6_testvcf_acceptance.py <backend-dir> <out.json>

scripts/validate_testvcfs.py runs PharmCAT on the 74 files directly, so it never
meets validate_vcf, where B6's checks live. This runs validate_vcf from the given
backend directory (B5's exported from git, or the working tree) over every one
and records accepted, or the error code and message, plus the warnings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TESTVCF_DIR = REPO / "test-data" / "reference" / "pharmcat_testvcfs"


def main() -> int:
    backend, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
    sys.path.insert(0, str(backend))
    from app.vcf_validation import VcfValidationError, validate_vcf  # noqa: PLC0415

    results = {}
    files = sorted(TESTVCF_DIR.glob("*/*.vcf"))
    for vcf in files:
        key = str(vcf.relative_to(TESTVCF_DIR))
        try:
            meta = validate_vcf(vcf.read_bytes(), filename=vcf.name)
            results[key] = {"accepted": True, "warnings": meta.warnings}
        except VcfValidationError as exc:
            results[key] = {"accepted": False, "code": exc.code.value, "message": exc.message}
    out.write_text(json.dumps(results, indent=1, sort_keys=True))
    accepted = sum(r["accepted"] for r in results.values())
    print(f"{backend}: {len(results)} files, {accepted} accepted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
