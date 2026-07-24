"""
PharmaGuard — the pre-generated explanation store.

Loads `app/data/explanations.json`: explanations generated offline, checked by
the faithfulness guard, and machine-verified sentence by sentence against their
cited sources. At runtime we do a dictionary lookup and deterministic slot
filling. No API call, no network, no key.

THERE IS NO CLINICAL REVIEWER
    An earlier design assumed a faculty guide would sign off on this prose. No
    such reviewer exists on this project, so the store records what is actually
    true — see `ReviewRecord` — and the API says so on every response.

WHY PRE-GENERATION IS THE DEPLOYED PATH
    The explanation space is enumerable — six drugs times a handful of
    phenotypes. That means every string a user can see is a string a human can
    read *before* it ships. An LLM in the request path makes the output
    unreviewable by construction: you can review a sample, never the thing the
    next user gets.

    It also removes the API key, the rate limit, the latency and the network
    failure mode from the deployed service. `EXPLANATION_MODE=live` exists for
    the demo video; `static` is what runs.

KEY
    (drug, phenotype) — lower-cased drug, contract phenotype code (PM/IM/NM/RM/
    URM/Unknown). The gene is implied by the drug, so it is stored for audit but
    not used for lookup.

MISSES DEGRADE
    An unknown key returns None and the caller falls back to the template
    generator. A missing or corrupt file is a warning, not a crash: a service
    that still explains, less elegantly, beats a 500.
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass, field
from pathlib import Path

from .context import Explanation

DEFAULT_STORE_PATH = Path(__file__).resolve().parents[1] / "data" / "explanations.json"


@dataclass(frozen=True)
class ReviewRecord:
    """
    What is actually known about this entry's scrutiny.

    Replaces a single `reviewed_by` string, which conflated three different
    things and implied the strongest of them. This project has **no qualified
    clinical reviewer**, so the fields are separate and the absent one is named
    explicitly rather than left to be inferred from a null.
    """

    #: Every clinical-claim sentence traces to a cited source. Machine-checked
    #: by scripts/verify_provenance.py.
    provenance_verified: bool = False
    verified_by: str = ""
    verified_at: str = ""

    #: The project author read this entry. Not clinical approval; the author is
    #: not qualified to give it. Recorded because "nobody has read this at all"
    #: and "a non-clinician read it" are different states.
    read_by_author: str | None = None

    #: Reserved. Stays None until a qualified clinician reviews the entry —
    #: which, for this project, is not expected to happen.
    clinical_expert_review: str | None = None
    clinical_expert_review_status: str = "NOT_OBTAINED"

    @property
    def has_clinical_expert_review(self) -> bool:
        return bool(self.clinical_expert_review)


@dataclass(frozen=True)
class StoredExplanation:
    """One entry, with the provenance needed to audit it."""

    explanation: Explanation
    drug: str
    phenotype: str
    gene: str | None = None
    model: str = ""
    generated_at: str = ""
    generator: str = ""
    guard_passed: bool = False
    review: ReviewRecord = field(default_factory=ReviewRecord)

    @property
    def is_provenance_verified(self) -> bool:
        return self.review.provenance_verified


@dataclass
class ExplanationStore:
    """Parsed `explanations.json`."""

    entries: dict[tuple[str, str], StoredExplanation]
    version: int = 0
    generated_at: str = ""
    model: str = ""
    load_error: str | None = None

    def get(self, drug: str, phenotype: str) -> StoredExplanation | None:
        return self.entries.get((drug.strip().lower(), phenotype.strip()))

    @property
    def unverified_count(self) -> int:
        """Entries whose clinical claims are not traced to a source."""
        return sum(1 for e in self.entries.values() if not e.is_provenance_verified)

    @property
    def unread_count(self) -> int:
        """Entries no human has read at all."""
        return sum(1 for e in self.entries.values() if not e.review.read_by_author)

    def __len__(self) -> int:
        return len(self.entries)


def _parse_review(raw: dict) -> ReviewRecord:
    """
    Read the review block.

    Tolerates the legacy `reviewed_by` field so an old store still loads, but
    deliberately does **not** map it onto anything implying clinical approval:
    a legacy name recorded who read the entry, nothing more.
    """
    block = raw.get("review")
    if isinstance(block, dict):
        return ReviewRecord(
            provenance_verified=bool(block.get("provenance_verified")),
            verified_by=str(block.get("verified_by") or ""),
            verified_at=str(block.get("verified_at") or ""),
            read_by_author=block.get("read_by_author"),
            clinical_expert_review=block.get("clinical_expert_review"),
            clinical_expert_review_status=str(
                block.get("clinical_expert_review_status") or "NOT_OBTAINED"
            ),
        )
    return ReviewRecord(read_by_author=raw.get("reviewed_by"))


def _key(drug: str, phenotype: str) -> tuple[str, str]:
    return drug.strip().lower(), phenotype.strip()


def _parse(payload: dict) -> ExplanationStore:
    entries: dict[tuple[str, str], StoredExplanation] = {}

    for raw in payload.get("explanations") or []:
        if not isinstance(raw, dict):
            continue
        drug = str(raw.get("drug") or "").strip()
        phenotype = str(raw.get("phenotype") or "").strip()
        fields = raw.get("explanation")
        if not drug or not phenotype or not isinstance(fields, dict):
            continue

        guard = raw.get("guard_report")
        entries[_key(drug, phenotype)] = StoredExplanation(
            explanation=Explanation(
                summary=str(fields.get("summary") or ""),
                mechanism=str(fields.get("mechanism") or ""),
                variant_rationale=str(fields.get("variant_rationale") or ""),
                patient_friendly=str(fields.get("patient_friendly") or ""),
            ),
            drug=drug.lower(),
            phenotype=phenotype,
            gene=raw.get("gene"),
            model=str(raw.get("model") or ""),
            generated_at=str(raw.get("generated_at") or ""),
            generator=str(raw.get("generator") or ""),
            guard_passed=bool(guard.get("passed")) if isinstance(guard, dict) else False,
            review=_parse_review(raw),
        )

    return ExplanationStore(
        entries=entries,
        version=int(payload.get("version") or 0),
        generated_at=str(payload.get("generated_at") or ""),
        model=str(payload.get("model") or ""),
    )


@functools.lru_cache(maxsize=1)
def load_store(path: Path | None = None) -> ExplanationStore:
    """Load the store once. Call `.cache_clear()` in tests."""
    target = path or DEFAULT_STORE_PATH

    if not target.is_file():
        return ExplanationStore(
            entries={},
            load_error=(
                f"No pre-generated explanations at {target.name}. Run "
                "scripts/pregenerate_explanations.py; until then every result "
                "uses the deterministic template."
            ),
        )

    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ExplanationStore(
            entries={},
            load_error=f"Could not read {target.name}: {exc}",
        )

    if not isinstance(payload, dict):
        return ExplanationStore(
            entries={}, load_error=f"{target.name} is not a JSON object."
        )

    return _parse(payload)


def lookup(drug: str, phenotype: str, path: Path | None = None) -> StoredExplanation | None:
    """Fetch one entry, or None."""
    return load_store(path).get(drug, phenotype)
