#!/usr/bin/env python3
"""Fail when the checked scientific bundle differs from current artifacts."""

from __future__ import annotations

import argparse
import json

from compatible_bundle import verify_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = verify_manifest()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("compatible scientific bundle:", "PASS" if result["compatible"] else "FAIL")
        for problem in result["problems"]:
            print(" -", problem)
    return 0 if result["compatible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
