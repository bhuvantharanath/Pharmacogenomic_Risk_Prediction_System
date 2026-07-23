"""
PharmaGuard — the pre-generated explanation store.

Loads `app/data/explanations.json`: explanations generated offline, checked by
the guard, and (eventually) reviewed by the faculty guide. At runtime we do a
dictionary lookup and deterministic slot filling. No API call, no network, no
key.

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
from dataclasses import dataclass
from pathlib import Path

from .context import Explanation

DEFAULT_STORE_PATH = Path(__file__).resolve().parents[1] / "data" / "explanations.json"


@dataclass(frozen=True)
class StoredExplanation:
    """One reviewed entry, with the provenance needed to audit it."""

    explanation: Explanation
    drug: str
    phenotype: str
    gene: str | None = None
    model: str = ""
    generated_at: str = ""
    generator: str = ""
    guard_passed: bool = False
    reviewed_by: str | None = None

    @property
    def is_reviewed(self) -> bool:
        return bool(self.reviewed_by)


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
    def unreviewed_count(self) -> int:
        return sum(1 for e in self.entries.values() if not e.is_reviewed)

    def __len__(self) -> int:
        return len(self.entries)


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
            reviewed_by=raw.get("reviewed_by"),
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
