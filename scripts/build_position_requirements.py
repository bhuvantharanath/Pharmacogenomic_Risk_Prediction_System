#!/usr/bin/env python3
"""
Regenerate the required positions in backend/app/data/position_requirements.json.

    python scripts/build_position_requirements.py --check   # exit 1 if they differ
    python scripts/build_position_requirements.py --write   # rewrite the positions

The position lists are extracted from PharmCAT's own positions VCF
(`pharmcat_positions_3.4.0.vcf.bgz`, INFO/PX names the gene), never transcribed
by hand. Everything else in the file is MEASURED or DERIVED elsewhere and is
carried over untouched: `min_coverage_percent` and `measured_wrong_rate_below`
come from the coverage-sensitivity sweep, and the decision-critical fields from
scripts/derive_decision_critical.py. This script never computes a threshold.

The data file has named this script as its generator since July; it did not
exist until Phase 9 B1 (audit finding F-18). `--check` reproduced the committed
lists exactly for all seven genes before `--write` was ever needed.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

from _common import REPO_ROOT

POSITIONS_VCF = REPO_ROOT / "test-data" / "reference" / "tools" / "pharmcat_positions_3.4.0.vcf.bgz"
REQUIREMENTS = REPO_ROOT / "backend" / "app" / "data" / "position_requirements.json"


def positions_by_gene(vcf: Path = POSITIONS_VCF) -> dict[str, list[list]]:
    """Every (chrom, pos) PharmCAT defines, per gene, in file order."""
    genes: dict[str, list[list]] = {}
    with gzip.open(vcf, "rt") as handle:  # BGZF is multi-member gzip
        for line in handle:
            if line.startswith("#"):
                continue
            chrom, pos, _id, _ref, _alt, _qual, _filter, info = line.split("\t")[:8]
            fields = dict(item.split("=", 1) for item in info.split(";") if "=" in item)
            for gene in fields.get("PX", "").split(","):
                if gene and gene != ".":
                    entry = [chrom, int(pos)]
                    if entry not in genes.setdefault(gene, []):
                        genes[gene].append(entry)
    return genes


def differences(requirements: Path = REQUIREMENTS, vcf: Path = POSITIONS_VCF) -> dict[str, dict]:
    """Per gene in the requirements file: positions added or removed by PharmCAT."""
    data = json.loads(requirements.read_text())
    derived = positions_by_gene(vcf)
    out = {}
    for gene, spec in data["genes"].items():
        committed = [list(p) for p in spec["positions"]]
        fresh = derived.get(gene, [])
        if committed != fresh:
            out[gene] = {
                "only_committed": [p for p in committed if p not in fresh],
                "only_pharmcat": [p for p in fresh if p not in committed],
                "same_set_different_order": sorted(map(tuple, committed)) == sorted(map(tuple, fresh)),
            }
    return out


def write(requirements: Path = REQUIREMENTS, vcf: Path = POSITIONS_VCF) -> None:
    data = json.loads(requirements.read_text())
    derived = positions_by_gene(vcf)
    for gene, spec in data["genes"].items():
        spec["positions"] = derived[gene]
        spec["required_positions"] = len(derived[gene])
    requirements.write_text(json.dumps(data, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    if args.write:
        write()
        print(f"rewrote positions in {REQUIREMENTS.relative_to(REPO_ROOT)}")
        return 0
    diff = differences()
    print(json.dumps(diff, indent=1) if diff else "required positions match PharmCAT's positions VCF")
    return 1 if diff else 0


if __name__ == "__main__":
    sys.exit(main())
