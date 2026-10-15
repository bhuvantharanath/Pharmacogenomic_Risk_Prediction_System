#!/usr/bin/env python3
"""
Fetch the pinned binaries that git does not carry, and refuse any that do not match.

    python scripts/fetch_pinned_artifacts.py           # fetch what is missing, verify all
    python scripts/fetch_pinned_artifacts.py --check   # verify only; fetch nothing

WHY THIS EXISTS

The scientific identity checks hash four gitignored files: the PharmCAT 3.4.0
jar, its positions VCF and that VCF's index, and the locked 208-sample cohort
VCF. A clean CI checkout has none of them. On 2026-10-14 the six identity tests
failed in CI for that reason, and the release gate failed closed before it
could judge the human prerequisites.

NOTHING IS PINNED IN THIS FILE

Path, size and SHA-256 come from the hash-bound manifests:

  * The PharmCAT files come from backend/app/data/compatible_bundle.json.
  * The cohort comes from the current evaluation manifest. That manifest is
    used only after it matches the hash the bundle records for it.

This file only says where each file can be downloaded:

  * The PharmCAT files come from PharmGKB's own GitHub release for the pinned
    engine version.
  * The cohort comes from a release asset of this repository. It is a
    bcftools subset of public 1000 Genomes data, but its header records the
    local command lines it was built with, so a rebuild could never reproduce
    the pinned hash.

A file already on disk is verified and never replaced. A mismatch is an error
to investigate, not something to overwrite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from _common import REPO_ROOT, scrub

BUNDLE_RELATIVE = "backend/app/data/compatible_bundle.json"
PHARMCAT_RELEASE = "https://github.com/PharmGKB/PharmCAT/releases/download/v{version}/{name}"
COHORT_RELEASE = (
    "https://github.com/bhuvantharanath/Pharmacogenomic_Risk_Prediction_System/"
    "releases/download/evidence-locked-cohort-v1/{name}"
)
ATTEMPTS = 3


@dataclass(frozen=True)
class Pin:
    path: str
    sha256: str
    bytes: int
    url: str


class PinError(Exception):
    """A pinned file is missing, unreachable, or does not match its pin."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pins(root: Path = REPO_ROOT) -> list[Pin]:
    bundle = json.loads((root / BUNDLE_RELATIVE).read_text())
    pharmcat = bundle["pharmcat"]
    pins = [
        Pin(ref["path"], ref["sha256"], ref["bytes"],
            PHARMCAT_RELEASE.format(version=pharmcat["engine_version"], name=Path(ref["path"]).name))
        for ref in (pharmcat["jar"], pharmcat["positions"], pharmcat["positions_index"])
    ]
    manifest_ref = bundle["evaluation_current"]["manifest"]
    manifest_path = root / manifest_ref["path"]
    if sha256(manifest_path) != manifest_ref["sha256"]:
        raise PinError(f"{manifest_ref['path']} does not match the hash the bundle records for it")
    cohort = json.loads(manifest_path.read_text())["frozen_combined_vcf"]
    pins.append(Pin(cohort["path"], cohort["sha256"], cohort["bytes"],
                    COHORT_RELEASE.format(name=Path(cohort["path"]).name)))
    return pins


def _download(pin: Pin, target: Path) -> None:
    """Stream to a temporary file beside the target; move it into place only if it matches."""
    digest = hashlib.sha256()
    size = 0
    fd, partial = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".part", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as out, urllib.request.urlopen(pin.url, timeout=120) as response:
            for chunk in iter(lambda: response.read(1 << 20), b""):
                size += len(chunk)
                if size > pin.bytes:
                    raise PinError(f"{pin.path}: download is larger than the pinned {pin.bytes} bytes")
                digest.update(chunk)
                out.write(chunk)
        if size != pin.bytes or digest.hexdigest() != pin.sha256:
            raise PinError(
                f"{pin.path}: downloaded {size} bytes with SHA-256 {digest.hexdigest()}; "
                f"pinned {pin.bytes} bytes with SHA-256 {pin.sha256}")
        os.replace(partial, target)
    finally:
        if os.path.exists(partial):
            os.unlink(partial)


def ensure(pin: Pin, root: Path = REPO_ROOT, fetch: bool = True) -> str:
    """Return "present" or "fetched"; raise PinError for anything else."""
    target = root / pin.path
    if target.is_symlink():
        raise PinError(f"{pin.path} is a symlink; the identity checks require a regular file")
    if target.is_file():
        if target.stat().st_size == pin.bytes and sha256(target) == pin.sha256:
            return "present"
        raise PinError(f"{pin.path} is on disk but does not match its pin; remove it and fetch again")
    if not fetch:
        raise PinError(f"{pin.path} is missing")
    target.parent.mkdir(parents=True, exist_ok=True)
    last: Exception | None = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            _download(pin, target)
            return "fetched"
        except urllib.error.HTTPError as exc:
            if exc.code < 500:
                raise PinError(f"{pin.path}: HTTP {exc.code} from {pin.url}") from exc
            last = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
        if attempt < ATTEMPTS:
            time.sleep(5 * attempt)
    raise PinError(f"{pin.path}: download failed after {ATTEMPTS} attempts: {scrub(last)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="Verify only; fetch nothing.")
    args = parser.parse_args(argv)

    try:
        pins = load_pins()
    except (PinError, OSError, KeyError, ValueError) as exc:
        print(f"pinned artifacts: cannot read the pins: {scrub(exc)}", file=sys.stderr)
        return 1
    failed = 0
    for pin in pins:
        try:
            status = ensure(pin, fetch=not args.check)
        except PinError as exc:
            failed += 1
            print(f"  FAILED   {scrub(exc)}", file=sys.stderr)
            continue
        print(f"  {status:<8} {pin.path}  sha256 {pin.sha256[:16]}…")
    print(f"pinned artifacts: {len(pins) - failed} of {len(pins)} verified")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
