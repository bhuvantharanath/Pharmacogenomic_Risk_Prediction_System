"""
GRCh38's base at a required position, for the VCFs tests write (Phase 9 B6).

Since B6 a REF allele that contradicts GRCh38 at a required position declines
the whole file. Test files used to write REF `A` everywhere, which no real
GRCh38 file does; their rows now carry the real base, as a real file's would.
Positions outside the required set are not checked, so they keep `A`.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path

_DATA = Path(__file__).resolve().parents[1] / "app" / "data" / "reference_alleles.json"


@functools.lru_cache(maxsize=1)
def _bases() -> dict[str, str]:
    return {key: entry["base"] for key, entry in json.loads(_DATA.read_text())["alleles"].items()}


def ref(chrom: str, pos: int) -> str:
    """GRCh38's base at (chrom, pos) if it is a required position, else `A`."""
    return _bases().get(f"chr{chrom.removeprefix('chr')}:{pos}", "A")


def alt(chrom: str, pos: int) -> str:
    """Any base other than REF, for the ALT column."""
    return "G" if ref(chrom, pos) != "G" else "A"
