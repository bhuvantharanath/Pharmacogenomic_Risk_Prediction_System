"""
Label/prose consistency — the check that was missing.

WHY THIS LAYER EXISTS

Three separate divergences were found in Phase 6, and they trace to one gap:

    provenance guard      verifies  explanation -> CPIC
    mapping validation    verifies  label       -> CPIC
    (nothing)             verifies  explanation -> label

Two artifacts can each be faithfully traceable to the same source and still
contradict each other, because they trace to *different parts* of it — the label
is derived from CPIC's recommendation text, the prose is grounded in CPIC's
implications and the mechanism corpus. Neither check can see the contradiction,
because from each one's vantage point nothing is wrong.

The three real cases, all now fixtures:

  1. WRONG LABEL, CORRECT PROSE   azathioprine:IM carried a green `Safe` badge
     over prose reading "your doctor may need to start you on a lower dose". The
     substring-collision bug produced the label; the model's text was right.

  2. CORRECT LABEL, WRONG PROSE   SLCO1B1 "Possible Decreased Function" derives
     `Toxic`/high, but collapses to `Phenotype.UNKNOWN`, so the served
     explanation says "your genetic result was not available for this gene" —
     under a red Toxic badge. The result *was* available; it is tentative.

  3. STALE PROSE AFTER A LABEL CHANGE   fixing the mapping moved three entries'
     labels while their text stayed as generated.

WHAT IT CHECKS

Deterministic rules over three inputs: the derived label, the derived phenotype
state, and the explanation text. **No LLM judges anything here** — using a model
to check a model is circular, and this project has already documented what
happens when a checker shares an input with the thing it checks.

Two independent tests:

  DECLARED PARAPHRASE   if the prose contains a sentence declared in
                        `label_paraphrases.yaml`, that sentence's label/phenotype
                        must equal the derived one. Exact, no interpretation.

  ACTION CLASS          free prose is classified by the action it describes
                        (no-data / standard use / active intervention) and
                        checked against the action the label implies.

WHERE IT RUNS

Build time over the whole store, and request time over each response. A
request-time failure degrades to the deterministic template and warns — a
contradicting pair is never served, because a confident-looking contradiction is
more dangerous than plainer text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..models import Phenotype, RiskLabel

# --------------------------------------------------------------------------- #
# Action classes
# --------------------------------------------------------------------------- #

#: Fields whose prose DIRECTS the reader. Only these are action-checked.
_DIRECTIVE_FIELDS = frozenset({"summary", "patient_friendly"})

NO_DATA = "no_data"
STANDARD = "standard_use"
INTERVENTION = "intervention"

#: Prose asserting that no usable result exists.
_NO_DATA_PROSE = re.compile(
    r"\bnot available\b|\bcould not (?:be )?(?:determine|reach|call|assign)"
    r"|\bno (?:result|genotype|conclusion|recommendation)\b"
    r"|\bunknown because\b|\bwas not called\b|\bcannot be (?:determined|assigned)\b"
    r"|\bunable to (?:determine|call)\b",
    re.IGNORECASE,
)

#: Prose asserting that nothing about prescribing changes.
#:
#: "standard dose" alone is NOT such an assertion, and assuming it was produced
#: four false positives on real prose. In this corpus the phrase most often
#: appears as the OBJECT of an avoidance ("avoid the standard dose of
#: clopidogrel") or attached to a DIFFERENT drug ("prasugrel or ticagrelor at
#: the standard dose"). Both mean the opposite of standard use. So only explicit
#: no-change assertions count, and the bare phrase is excluded entirely.
_STANDARD_PROSE = re.compile(
    r"\bdo(?:es)? not suggest a change\b|\bno change to how\b"
    r"|\bas (?:it is )?usually prescribed\b"
    r"|\bno adjustment (?:is )?(?:needed|required)\b"
    r"|\btake it as prescribed\b|\bcan take (?:the|this) (?:drug|medicine)\b",
    re.IGNORECASE,
)

#: Prose directing an active change.
#:
#: Deliberately NARROW. Broad intervention vocabulary is unreliable over free
#: prose because the same words describe biology: "turn codeine into a different
#: medicine" is metabolism, not a substitution; "monitor" and "increased risk"
#: appear inside mechanism explanations and inside NEGATED statements ("not at
#: increased risk"). Every one of those produced a false positive.
#:
#: What survives is imperative-shaped: an explicit dose reduction, or an explicit
#: direction to use something else. Narrowing costs sensitivity on prose that
#: hints at intervention obliquely — accepted, because a check that cries wolf on
#: faithful text gets switched off, which is the failure this project has already
#: documented twice.
_INTERVENTION_PROSE = re.compile(
    r"\blower dose\b|\blower(?:ed)? (?:the )?dose\b"
    r"|\breduc\w*\s+(?:the\s+)?(?:\w+\s+){0,2}?dos"
    r"|\bsmaller dose\b|\bdose reduction\b"
    r"|\b(?:may|might|should|will)\s+(?:need|want|choose|recommend|prescribe|consider)\b"
    r"|\bavoid\b|\bmay not work\b",
    re.IGNORECASE,
)

#: What each label licenses the prose to describe.
#:
#: `Unknown` deliberately permits only NO_DATA: prose recommending an action under
#: an Unknown label would assert guidance the pipeline cannot support, which is
#: the same over-claiming the CYP2D6 negative control exists to prevent.
_ALLOWED: dict[RiskLabel, frozenset[str]] = {
    RiskLabel.SAFE: frozenset({STANDARD}),
    RiskLabel.ADJUST_DOSAGE: frozenset({INTERVENTION}),
    RiskLabel.TOXIC: frozenset({INTERVENTION}),
    RiskLabel.INEFFECTIVE: frozenset({INTERVENTION}),
    RiskLabel.UNKNOWN: frozenset({NO_DATA}),
}


def classify_action(text: str) -> set[str]:
    """
    Which action classes this prose describes. May be several, or none.

    An empty result means the prose asserts no action at all — pure framing —
    which is consistent with any label and is not a divergence.
    """
    found: set[str] = set()
    if _NO_DATA_PROSE.search(text):
        found.add(NO_DATA)
    if _INTERVENTION_PROSE.search(text):
        found.add(INTERVENTION)
    if _STANDARD_PROSE.search(text):
        found.add(STANDARD)
    return found


# --------------------------------------------------------------------------- #
# Verdict
# --------------------------------------------------------------------------- #


@dataclass
class ConsistencyIssue:
    kind: str          # label_action | declared_label | declared_phenotype | phenotype_framing
    detail: str
    field_name: str = ""

    def __str__(self) -> str:
        where = f" [{self.field_name}]" if self.field_name else ""
        return f"{self.kind}{where}: {self.detail}"


@dataclass
class ConsistencyReport:
    label: RiskLabel
    phenotype: Phenotype
    issues: list[ConsistencyIssue] = field(default_factory=list)

    @property
    def consistent(self) -> bool:
        return not self.issues

    @property
    def summary(self) -> str:
        if self.consistent:
            return "explanation is consistent with its label"
        return "; ".join(str(i) for i in self.issues)


def check_consistency(
    *,
    label: RiskLabel,
    phenotype: Phenotype,
    fields: dict[str, str],
    label_paraphrases: dict[str, str] | None = None,
    phenotype_paraphrases: dict[str, str] | None = None,
) -> ConsistencyReport:
    """
    Assert that the explanation text agrees with the label rendered beside it.

    `fields` is the explanation's four narrative fields. `label_paraphrases` and
    `phenotype_paraphrases` map a normalised sentence to the label/phenotype it
    was declared for (see `label_paraphrases.yaml`).
    """
    report = ConsistencyReport(label=label, phenotype=phenotype)
    allowed = _ALLOWED.get(label, frozenset())

    for field_name, text in fields.items():
        if not (text or "").strip():
            continue
        directive_field = field_name in _DIRECTIVE_FIELDS

        # -- declared paraphrases: exact, no interpretation ------------------ #
        for sentence in _sentences(text):
            key = _normalise(sentence)
            if label_paraphrases and key in label_paraphrases:
                declared = label_paraphrases[key]
                if declared != label.value:
                    report.issues.append(ConsistencyIssue(
                        "declared_label",
                        f"prose uses the declared paraphrase for {declared!r} but "
                        f"the derived label is {label.value!r}",
                        field_name,
                    ))
            if phenotype_paraphrases and key in phenotype_paraphrases:
                declared = phenotype_paraphrases[key]
                if declared != phenotype.value:
                    report.issues.append(ConsistencyIssue(
                        "declared_phenotype",
                        f"prose uses the declared paraphrase for phenotype "
                        f"{declared!r} but the derived phenotype is {phenotype.value!r}",
                        field_name,
                    ))

        # -- action class ---------------------------------------------------- #
        # Only fields that DIRECT are checked. `mechanism` describes biology and
        # legitimately says "increased risk" or names a metabolite as "a different
        # medicine"; `variant_rationale` is code-composed and states the call.
        # Checking either against an action class is a category error — and it
        # produced false positives on real prose before this restriction.
        if not directive_field:
            continue
        described = classify_action(text)
        if not described:
            continue
        forbidden = described - allowed
        # NO_DATA prose under a real-call label, and vice versa, are the two
        # divergences actually observed; both are covered by set difference.
        if forbidden:
            report.issues.append(ConsistencyIssue(
                "label_action",
                f"prose describes {sorted(forbidden)} but label {label.value!r} "
                f"licenses only {sorted(allowed)}",
                field_name,
            ))

    return report


_SENT = re.compile(r"(?<=[.!?])\s+")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.split(text.strip()) if s.strip()]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())
