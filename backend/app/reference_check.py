"""
PharmaGuard — REF identity at the required positions (Phase 9 B6, finding F-02).

A genotype is written relative to its REF allele. If a file's REF at a required
position is not GRCh38's base, the file was not made against the reference this
analysis reads, and its genotypes there mean something else. The adversarial
sweep built exactly that file — an hg19-style export sliced at GRCh38
coordinates — and got confident "No PGx-guided adjustment identified" for
fluorouracil and azathioprine: PharmCAT discards some such rows and reads others
as reference without a word, and the coverage gate keys evidence on
(chrom, pos) alone, so it counted every row as evidence.

This module only compares. The decision — decline the whole file — is
`vcf_validation.validate_vcf`'s, because a REF that contradicts GRCh38 says the
file came from somewhere else, and that cannot be confined to the rows where it
happens to show.

The bases come from `data/reference_alleles.json`, derived from PharmCAT's
positions VCF and cross-checked against its allele definitions by
`scripts/derive_reference_alleles.py`. The first base of a VCF REF is the
reference base at POS for SNVs and indels alike, so that is what is compared.
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass, field
from pathlib import Path

_DATA = Path(__file__).parent / "data" / "reference_alleles.json"


@dataclass(frozen=True)
class Mismatch:
    chrom: str
    pos: int
    gene: str
    rsid: str
    file_base: str
    grch38_base: str

    def describe(self) -> str:
        where = f"{self.chrom}:{self.pos}"
        named = f"{self.rsid}, {self.gene}" if self.rsid else self.gene
        return f"{where} ({named}): the file has {self.file_base or 'no base'}, GRCh38 has {self.grch38_base}"


@dataclass
class ReferenceCheck:
    #: Distinct required positions that had at least one row in the file.
    compared: int = 0
    #: One entry per required position whose REF disagreed, in file order.
    mismatches: list[Mismatch] = field(default_factory=list)


@functools.lru_cache(maxsize=1)
def reference_bases() -> dict[str, dict]:
    """`chrN:pos` -> {base, gene, rsid}."""
    return json.loads(_DATA.read_text())["alleles"]


def check(vcf_text: str) -> ReferenceCheck:
    """
    Compare REF with GRCh38 at every required position present in `vcf_text`.

    Expects contig names already normalised to `chrN` (validate_vcf does that
    first). A position with several rows counts once, and is a mismatch if any
    of its rows disagrees.
    """
    table = reference_bases()
    seen: set[str] = set()
    flagged: set[str] = set()
    result = ReferenceCheck()
    for line in vcf_text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t", 4)
        if len(parts) < 4:
            continue
        key = f"{parts[0]}:{parts[1]}"
        expected = table.get(key)
        if expected is None:
            continue
        seen.add(key)
        base = parts[3].strip()[:1].upper()
        if base != expected["base"] and key not in flagged:
            flagged.add(key)
            result.mismatches.append(Mismatch(
                chrom=parts[0], pos=int(parts[1]), gene=expected["gene"], rsid=expected["rsid"],
                file_base=base, grch38_base=expected["base"],
            ))
    result.compared = len(seen)
    return result
