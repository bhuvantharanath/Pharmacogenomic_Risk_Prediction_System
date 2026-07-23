"""
PharmaGuard — faithfulness guard.

A deterministic, free, always-on check that generated text asserts nothing the
supplied context did not contain. It is not a filter of last resort bolted on
for tidiness: it is the mechanism that makes an LLM acceptable in this project
at all.

WHAT IT CHECKS
    Every entity extracted from the generated text must appear in the context:

      dose        a number adjacent to a unit (mg, mcg, %, mg/kg, units, ...)
      number      any other bare numeric token
      rsid        rs\\d+
      star_allele \\*\\d+\\w*
      gene        a symbol from our known gene list
      drug        a drug name from the mechanism corpus

    Anything present in the text but absent from the context is a violation.

WHAT IT DOES NOT CHECK
    Semantics. The guard cannot tell that "reduced CYP2C19 function causes the
    drug to accumulate" is backwards — every token in that sentence is present
    in the context. It catches *fabricated entities*, which is the failure mode
    with the sharpest clinical edge (an invented dose), not *wrong reasoning*.
    Reasoning errors are what the corpus review and faculty sign-off are for.
    Do not mistake a passing guard report for a correctness guarantee.

DIRECTION OF FAILURE
    The guard is intentionally strict. A false positive costs a retry and then
    a fall back to deterministic template text, which is always safe. A false
    negative puts an invented clinical number in front of a reader. When tuning,
    err toward strict.
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..pharmcat_runner import TARGET_GENES
from ..retrieval import all_documents, known_genes
from .context import ExplanationContext, Explanation

# --------------------------------------------------------------------------- #
# Extraction patterns
# --------------------------------------------------------------------------- #

# Units that make a number a clinical quantity. Order matters: longer units are
# listed first so "mg/kg" is not truncated to "mg".
_UNITS = (
    r"mg/kg/day|mg/kg|mg/m2|mg/day|mcg/kg|units?/kg|"
    r"mg|mcg|µg|ug|kg|ml|mL|g|%|units?|iu|IU|fold|x"
)
# Trailing guard is a lookahead, not `\b`. `\b` requires a word/non-word
# transition, so "30%." never matched — the `%` and the `.` are both non-word
# characters. That silently demoted every percentage from `dose` to `number`,
# which still failed the check but misreported the reason. Percentages are
# explicitly in scope for the dose check.
_DOSE = re.compile(rf"(\d+(?:\.\d+)?)\s*(?:{_UNITS})(?![A-Za-z0-9])", re.IGNORECASE)
_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_RSID = re.compile(r"\brs\d+\b", re.IGNORECASE)
_STAR_ALLELE = re.compile(r"\*\d+[A-Za-z]*")

# Bare integers that carry no clinical meaning in ordinary prose ("one of two
# copies", "the first step"). Excluding them stops the guard failing on grammar
# while leaving every dose-shaped and identifier-shaped number checked.
_BENIGN_NUMBERS = frozenset({"1", "2"})


@dataclass(frozen=True)
class Violation:
    """One unfaithful entity."""

    kind: str  # dose | number | rsid | star_allele | gene | drug | slot
    token: str
    field_name: str

    def __str__(self) -> str:
        return f"{self.kind}:{self.token!r} in {self.field_name}"


@dataclass
class GuardReport:
    """Structured verdict. Returned to callers and written to the JSONL log."""

    passed: bool
    violations: list[Violation] = field(default_factory=list)
    action_taken: str = "accepted"
    generator: str = ""
    attempts: int = 1

    @property
    def summary(self) -> str:
        if self.passed:
            return f"guard passed ({self.generator})"
        kinds = sorted({v.kind for v in self.violations})
        return (
            f"guard failed ({self.generator}): "
            f"{len(self.violations)} violation(s) [{', '.join(kinds)}] "
            f"-> {self.action_taken}"
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "generator": self.generator,
            "attempts": self.attempts,
            "action_taken": self.action_taken,
            "violations": [
                {"kind": v.kind, "token": v.token, "field": v.field_name}
                for v in self.violations
            ],
        }


# --------------------------------------------------------------------------- #
# Normalisation
# --------------------------------------------------------------------------- #


def _normalise(text: str) -> str:
    """
    Lower-case and collapse whitespace for containment checks.

    Punctuation is preserved: `*2` and `rs4244285` must stay matchable as
    written, and stripping `*` would let a fabricated `*17` match the digits of
    an unrelated number.
    """
    return re.sub(r"\s+", " ", text.lower())


def _contains(haystack: str, needle: str, kind: str) -> bool:
    """
    Is `needle` present in `haystack` as a whole token?

    **Boundary-aware on purpose.** Naive substring matching silently defeats the
    guard: an invented "50 mg" was accepted because the mechanism text contains
    "cytochrome P450", and "P450" contains the substring "50". A fabricated
    clinical dose passing the dose check is the single worst failure this module
    can have, so numeric and identifier tokens are matched with explicit
    boundaries.

    Regression-tested in `test_guard.py::TestSubstringFalseNegatives`.
    """
    token = _normalise(needle)
    if not token:
        return False

    if kind in ("dose", "number"):
        # No adjacent digit, decimal point, or comma — so 50 does not match
        # "P450", "1.50", "450", or "1,500".
        pattern = rf"(?<![\d.,]){re.escape(token)}(?![\d.,])"
    elif kind == "star_allele":
        # *2 must not match *22. A leading letter would make it part of a word.
        pattern = rf"(?<![\w]){re.escape(token)}(?![\d\w])"
    elif kind in ("rsid", "gene", "drug"):
        pattern = rf"\b{re.escape(token)}\b"
    else:
        return token in haystack

    return re.search(pattern, haystack) is not None


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #


def _known_drug_names() -> set[str]:
    """Drug names and aliases the corpus knows, for the drug-name check."""
    names: set[str] = set()
    for document in all_documents():
        names.add(document.drug.lower())
        names.update(alias.lower() for alias in document.aliases)
    return names


def _all_known_genes() -> set[str]:
    """Corpus genes plus PharmCAT's target genes."""
    return {g.upper() for g in known_genes()} | {g.upper() for g in TARGET_GENES}


def extract_entities(text: str) -> dict[str, set[str]]:
    """
    Pull checkable entities out of one piece of generated text.

    Exposed separately from `check()` so tests can assert on extraction alone.
    """
    doses = set(_DOSE.findall(text))
    # A number already counted as a dose is not re-reported as a bare number.
    numbers = {
        n
        for n in _NUMBER.findall(text)
        if n not in doses and n not in _BENIGN_NUMBERS
    }
    lowered = text.lower()

    return {
        "dose": doses,
        "number": numbers,
        "rsid": {r.lower() for r in _RSID.findall(text)},
        "star_allele": set(_STAR_ALLELE.findall(text)),
        "gene": {g for g in _all_known_genes() if re.search(rf"\b{g}\b", text, re.I)},
        "drug": {d for d in _known_drug_names() if re.search(rf"\b{re.escape(d)}\b", lowered)},
    }


# --------------------------------------------------------------------------- #
# The check
# --------------------------------------------------------------------------- #


def check(
    explanation: Explanation,
    context: ExplanationContext,
    *,
    generator: str = "unknown",
) -> GuardReport:
    """
    Verify that `explanation` asserts nothing absent from `context`.

    Runs against the **unfilled** explanation (placeholders intact). Slot values
    come straight from PharmCAT, so checking after substitution would just be
    re-validating our own data — and would fail spuriously when a diplotype
    contains a star allele the reviewed prose never mentioned.
    """
    grounding = _normalise(context.grounding_text())
    violations: list[Violation] = []

    for field_name, text in explanation.fields().items():
        if not text:
            continue

        entities = extract_entities(text)
        for kind, tokens in entities.items():
            for token in sorted(tokens):
                if not _contains(grounding, token, kind):
                    violations.append(Violation(kind, token, field_name))

        # A placeholder we cannot fill would reach the user as literal "{foo}".
        from .context import unknown_slots

        for slot in sorted(unknown_slots(text)):
            violations.append(Violation("slot", f"{{{slot}}}", field_name))

    return GuardReport(
        passed=not violations,
        violations=violations,
        action_taken="accepted" if not violations else "rejected",
        generator=generator,
    )


# --------------------------------------------------------------------------- #
# Violation log
#
# Every failure is appended to a JSONL file so the project report can quote real
# hallucination rates instead of estimating them.
# --------------------------------------------------------------------------- #

DEFAULT_LOG_PATH = Path(
    os.environ.get(
        "GUARD_LOG_PATH",
        str(Path(__file__).resolve().parents[2] / "logs" / "guard_violations.jsonl"),
    )
)

# Appends happen from request handlers; a lock keeps concurrent lines intact.
_LOG_LOCK = threading.Lock()


def log_violation(
    report: GuardReport,
    context: ExplanationContext,
    explanation: Explanation | None = None,
    *,
    path: Path | None = None,
) -> None:
    """
    Append one guard event to the JSONL log. Never raises.

    Logging must not be able to fail a request: an unwritable log directory is
    an ops problem, not a reason to deny the user their (already safe) result.
    """
    target = path or DEFAULT_LOG_PATH
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "drug": context.drug,
        "gene": context.gene,
        "phenotype": context.phenotype.value,
        "risk_label": context.risk_label.value,
        **report.to_dict(),
    }
    if explanation is not None:
        # The offending text, so a reviewer can see what was actually said.
        record["rejected_text"] = explanation.fields()

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_LOCK, target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def read_violation_log(path: Path | None = None) -> list[dict]:
    """Read the JSONL log back. Used by tests and by reporting."""
    target = path or DEFAULT_LOG_PATH
    if not target.is_file():
        return []
    records: list[dict] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records
