#!/usr/bin/env python3
"""
B6 sabotages (audit/phase9/B6_PLAN.md): break one rule, run the B6 tests, restore.

    backend/.venv/bin/python audit/phase9/partb/b6_sabotage.py [SB6-g,SB6-h]

Each sabotage is an exact text replacement that must occur once. After every
run the file is restored and its sha256 compared with the original; any
difference stops the script. A sabotage that turns no test red exits 1.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PYTEST = [str(REPO / "backend/.venv/bin/python"), "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider",
          "tests/test_a4_inputs.py", "tests/test_input_robustness.py", "tests/test_evidence_crosscheck.py"]


def _drop_grch37_lengths(text: str) -> str:
    data = json.loads(text)
    del data["contig_lengths"]["GRCh37"]
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


SABOTAGES = [
    ("SB6-a", "the REF check reports no mismatches", "backend/app/reference_check.py",
     'if base != expected["base"] and key not in flagged:',
     'if False and base != expected["base"] and key not in flagged:'),
    ("SB6-b", "GRCh37 lengths removed from build_evidence.json", "backend/app/data/build_evidence.json",
     None, _drop_grch37_lengths),
    ("SB6-c", "contig rewrite disabled", "backend/app/vcf_validation.py",
     "    text, renamed = normalize_contigs(text)\n",
     "    renamed: dict[str, str] = {}\n"),
    ("SB6-d", "gVCF block detection disabled", "backend/app/coverage.py",
     "    if not any(marker in parts[4] for marker in _GVCF_ALT):\n        return 0",
     "    if True:\n        return 0"),
    ("SB6-e", "one base in reference_alleles.json flipped (rs4244285 G -> A)", "backend/app/data/reference_alleles.json",
     '"chr10:94781859": {\n      "base": "G",',
     '"chr10:94781859": {\n      "base": "A",'),
    ("SB6-f", "BCF magic check removed", "backend/app/vcf_validation.py",
     'if data[:3] == b"BCF":',
     'if False and data[:3] == b"BCF":'),
    # The re-bind chain (added after the owner's amendment; the evaluation tests
    # are excluded because they wait for the re-bind itself).
    ("SB6-g", "bundle rule ignores the difference from the previous evaluation", "scripts/compatible_bundle.py",
     '        and comparison.get("differing_eligibility_fields_vs_previous_evaluation") == against_previous\n',
     "        and True\n", ["tests/test_compatible_bundle.py", "-k", "rebind or chain or previous or inherited"]),
    ("SB6-h", "bundle rule stops requiring declarations to be in the chain", "scripts/compatible_bundle.py",
     "        and chained\n", "        and True\n",
     ["tests/test_compatible_bundle.py", "-k", "rebind or chain or previous or inherited"]),
]


def main() -> int:
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    caught_all = True
    for sid, what, rel, old, new, *tests in SABOTAGES:
        if only and sid not in only:
            continue
        argv = PYTEST[:7] + (tests[0] if tests else PYTEST[7:])
        path = REPO / rel
        original = path.read_bytes()
        before = hashlib.sha256(original).hexdigest()
        text = original.decode()
        if old is None:
            sabotaged = new(text)
        else:
            if text.count(old) != 1:
                raise SystemExit(f"{sid}: expected text found {text.count(old)} times in {rel}")
            sabotaged = text.replace(old, new)
        try:
            path.write_text(sabotaged)
            proc = subprocess.run(argv, cwd=REPO / "backend", capture_output=True, text=True, check=False)
        finally:
            path.write_bytes(original)
        restored = hashlib.sha256(path.read_bytes()).hexdigest() == before
        failed = [line for line in proc.stdout.splitlines() if line.startswith(("FAILED", "ERROR"))]
        summary = f"{len(failed)} red"
        print(f"== {sid}: {what} ({rel}) ==")
        for line in failed:
            print(line.split(" - ")[0])
        print(f"pytest exit {proc.returncode}; {summary}")
        print(f"restored identical: {'yes' if restored else 'NO'}")
        if not restored:
            raise SystemExit(f"{sid}: {rel} was not restored")
        if proc.returncode == 0 or not failed:
            caught_all = False
            print(f"{sid} NOT CAUGHT")
    return 0 if caught_all else 1


if __name__ == "__main__":
    sys.exit(main())
