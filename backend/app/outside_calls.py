"""
CYP2D6 from a dedicated caller, passed to PharmCAT as an outside call (Phase 9 B10).

PharmaGuard does not call CYP2D6 from a VCF, and still will not: the gene's
star alleles depend on structural and copy-number variation a VCF does not
express, and PharmCAT itself advises against it. A caller that reads the
sequencing reads (Cyrius, BCyrius, Aldy, StellarPGx, DRAGEN) can call it, and
PharmCAT accepts such a call as an "outside call" (`-po`). This module is the
one door for that call.

WHY THE GRAMMAR IS STRICT

The diplotype is written into PharmCAT's outside-call file, which PharmCAT reads
line by line: one gene per line, tab-separated. A newline in a supplied value
would add a call for another gene, and PharmCAT accepts a made-up allele without
complaint (it returns Indeterminate). So nothing reaches the file that is not a
CYP2D6 diplotype in PharmCAT's documented notation: star alleles, copy numbers
(`x2`, `xN`, the binned `≥3`), tandems (`+`) and bracketed combinations. The
gene is never taken from the user.

WHAT IT CLAIMS

The call is used as given and always labelled as supplied: "CYP2D6 supplied by
<caller>, not called by PharmaGuard." The caller is the uploader's statement;
this application cannot see the reads it came from.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: The callers the brief names, as offered to the user. Aldy is version 4.
#:
#: DRAGEN was added in Phase 10 §4. It belongs here on the same ground as the
#: other four and on no weaker one: DRAGEN v4.x ships a targeted CYP2D6 caller
#: that works from the reads and reports a total copy number alongside the
#: diplotype, which is exactly the capability a VCF cannot supply and the
#: reason this door exists. The alternative considered and rejected was to pass
#: a DRAGEN call under one of the existing names, which would put a false
#: statement in the provenance line every view of the result carries.
#:
#: Adding a name here widens nothing else. The grammar, the pinned gene, and
#: the refusal to call CYP2D6 from a VCF are untouched, and a supplied call is
#: still labelled as supplied wherever it appears.
CALLERS: tuple[str, ...] = ("Cyrius", "BCyrius", "Aldy", "StellarPGx", "DRAGEN")

#: The only gene an outside call may supply.
GENE = "CYP2D6"

MAX_LENGTH = 80

_ALLELE = r"\*\d{1,3}(?:\.\d{3})?"
_COPIES = rf"{_ALLELE}(?:x(?:[2-9]|1\d|N)|≥3)?"
_TANDEM = rf"{_COPIES}(?:\+{_COPIES})*"
_COMBINATION = rf"\[{_COPIES}(?: \+ {_COPIES})+\]"
_HAPLOTYPE = rf"(?:{_COMBINATION}|{_TANDEM})"
DIPLOTYPE = re.compile(rf"{_HAPLOTYPE}/{_HAPLOTYPE}")


class OutsideCallError(ValueError):
    """A supplied call that is refused before PharmCAT runs."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class OutsideCall:
    gene: str
    diplotype: str
    caller: str

    def file_line(self) -> str:
        """The line PharmCAT reads: gene, tab, diplotype."""
        return f"{self.gene}\t{self.diplotype}\n"

    @property
    def provenance(self) -> str:
        """What every view of a supplied result says."""
        return f"{self.gene} supplied by {self.caller}, not called by PharmaGuard."

    @property
    def warning(self) -> str:
        return f"{self.gene} {self.diplotype} supplied by {self.caller}, not called by PharmaGuard."


def parse(diplotype: str | None, caller: str | None) -> OutsideCall | None:
    """
    The supplied call, or None when none was supplied. Raises OutsideCallError
    for anything else. Nothing is trimmed or rewritten: a value is accepted as
    it was sent, or refused.
    """
    if not diplotype and not caller:
        return None
    if not diplotype or not caller:
        raise OutsideCallError(
            "OUTSIDE_CALL_INCOMPLETE",
            "A CYP2D6 call needs both the diplotype and the caller that produced it.",
        )
    if caller not in CALLERS:
        raise OutsideCallError(
            "OUTSIDE_CALL_INVALID",
            "The CYP2D6 caller must be one of: " + ", ".join(CALLERS) + ".",
        )
    if len(diplotype) > MAX_LENGTH or not DIPLOTYPE.fullmatch(diplotype):
        raise OutsideCallError(
            "OUTSIDE_CALL_INVALID",
            "The CYP2D6 diplotype is not in star-allele notation, for example "
            "*1/*4, *1x2/*4 or *1/[*6 + *8].",
        )
    return OutsideCall(GENE, diplotype, caller)
