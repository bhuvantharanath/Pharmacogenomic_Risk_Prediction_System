"""Authoritative approval and semantic-identity checks for stored prose.

The pre-generated store is an input artifact, not its own approval.  A stored
entry may be served only when the separately generated approval manifest binds
the exact text and source to the exact semantic context being requested.
"""

from __future__ import annotations

import functools
import hashlib
import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Mapping

from ..capabilities import capability_for
from ..retrieval import retrieve_mechanism
from .context import Explanation, ExplanationContext

if TYPE_CHECKING:
    from .static_store import StoredExplanation


DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "explanation_approvals.json"
)
DEFAULT_STORE_PATH = Path(__file__).resolve().parents[1] / "data" / "explanations.json"

APPROVED = "approved"
UNRESOLVED = "unresolved"
REJECTED = "rejected"
AUTHOR_REVIEW = "author_provenance_adjudication"
NO_EXPERT_REVIEW = "NOT_OBTAINED"


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalise_text(value: str) -> str:
    return " ".join(html.unescape(value or "").split())


def _normalise_label(value: str) -> str:
    if value == "Safe":
        return "No PGx-guided adjustment identified"
    return value


def content_hash(explanation: Explanation | Mapping[str, object]) -> str:
    fields = (
        explanation.fields()
        if isinstance(explanation, Explanation)
        else {
            name: str(explanation.get(name) or "")
            for name in (
                "summary",
                "mechanism",
                "variant_rationale",
                "patient_friendly",
            )
        }
    )
    return _digest(fields)


def source_hash(
    cpic_recommendation: str,
    mechanism_source: str,
    mechanism_content: str = "",
    mechanism_url: str = "",
) -> str:
    return _digest(
        {
            "cpic_recommendation": _normalise_text(cpic_recommendation),
            "mechanism_source": _normalise_text(mechanism_source),
            "mechanism_content": _normalise_text(mechanism_content),
            "mechanism_url": mechanism_url.strip(),
        }
    )


def semantic_context_hash(
    *,
    drug: str,
    gene: str | None,
    phenotype: str,
    risk_label: str,
) -> str:
    capability = capability_for(drug)
    relevant_genes = list(capability.relevant_genes) if capability else []
    return _digest(
        {
            "drug": drug.strip().lower(),
            "gene": (gene or "").strip().upper(),
            "relevant_genes": relevant_genes,
            "phenotype": phenotype.strip(),
            "risk_label": _normalise_label(risk_label.strip()),
        }
    )


def stored_source_hash(stored: "StoredExplanation") -> str:
    mechanism = retrieve_mechanism(stored.gene, stored.drug)
    return source_hash(
        stored.cpic_recommendation_used,
        stored.mechanism_source,
        mechanism.snippet() if mechanism else "",
        mechanism.source_url if mechanism else "",
    )


def context_source_hash(context: ExplanationContext) -> str:
    citation = context.mechanism.citation_line if context.mechanism else ""
    return source_hash(
        context.cpic_recommendation,
        citation,
        context.mechanism.snippet() if context.mechanism else "",
        context.mechanism.source_url if context.mechanism else "",
    )


def stored_context_hash(stored: "StoredExplanation") -> str:
    return semantic_context_hash(
        drug=stored.drug,
        gene=stored.gene,
        phenotype=stored.phenotype,
        risk_label=stored.derived_risk_label,
    )


def runtime_context_hash(context: ExplanationContext) -> str:
    return semantic_context_hash(
        drug=context.drug,
        gene=context.gene,
        phenotype=context.phenotype.value,
        risk_label=context.risk_label.value,
    )


@dataclass(frozen=True)
class ApprovalRecord:
    drug: str
    gene: str
    phenotype: str
    status: str
    content_hash: str
    source_hash: str
    context_hash: str
    review_kind: str
    adjudicated_by: tuple[str, ...]
    clinical_expert_review_status: str
    reason: str

    @property
    def key(self) -> tuple[str, str, str]:
        return self.drug, self.gene, self.phenotype


@dataclass
class ApprovalManifest:
    records: dict[tuple[str, str, str], ApprovalRecord]
    store_sha256: str = ""
    actual_store_sha256: str = ""
    version: int = 0
    load_error: str | None = None

    @property
    def store_compatible(self) -> bool:
        return bool(
            self.store_sha256
            and self.actual_store_sha256
            and self.store_sha256 == self.actual_store_sha256
        )

    def get(self, drug: str, gene: str | None, phenotype: str) -> ApprovalRecord | None:
        return self.records.get(
            (
                drug.strip().lower(),
                (gene or "").strip().upper(),
                phenotype.strip(),
            )
        )


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    reason: str
    record: ApprovalRecord | None = None


def _parse_record(raw: Mapping[str, object]) -> ApprovalRecord:
    return ApprovalRecord(
        drug=str(raw.get("drug") or "").strip().lower(),
        gene=str(raw.get("gene") or "").strip().upper(),
        phenotype=str(raw.get("phenotype") or "").strip(),
        status=str(raw.get("status") or UNRESOLVED),
        content_hash=str(raw.get("content_hash") or ""),
        source_hash=str(raw.get("source_hash") or ""),
        context_hash=str(raw.get("context_hash") or ""),
        review_kind=str(raw.get("review_kind") or ""),
        adjudicated_by=tuple(str(name) for name in raw.get("adjudicated_by") or []),
        clinical_expert_review_status=str(
            raw.get("clinical_expert_review_status") or NO_EXPERT_REVIEW
        ),
        reason=str(raw.get("reason") or ""),
    )


@functools.lru_cache(maxsize=1)
def load_manifest(
    path: Path | None = None,
    store_path: Path | None = None,
) -> ApprovalManifest:
    target = path or DEFAULT_MANIFEST_PATH
    source = store_path or DEFAULT_STORE_PATH
    if not target.is_file():
        return ApprovalManifest(
            records={},
            load_error=f"No explanation approval manifest at {target.name}.",
        )
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        actual_hash = file_sha256(source)
    except (OSError, json.JSONDecodeError) as exc:
        return ApprovalManifest(records={}, load_error=str(exc))

    if not isinstance(payload, dict):
        return ApprovalManifest(records={}, load_error="Approval manifest is not an object.")

    records: dict[tuple[str, str, str], ApprovalRecord] = {}
    for raw in payload.get("entries") or []:
        if not isinstance(raw, dict):
            continue
        record = _parse_record(raw)
        if not all(record.key) or record.key in records:
            return ApprovalManifest(
                records={},
                load_error="Approval manifest contains an incomplete or duplicate identity.",
            )
        records[record.key] = record

    return ApprovalManifest(
        records=records,
        store_sha256=str(payload.get("store_sha256") or ""),
        actual_store_sha256=actual_hash,
        version=int(payload.get("version") or 0),
    )


def evaluate(
    stored: "StoredExplanation",
    context: ExplanationContext,
    manifest: ApprovalManifest | None = None,
) -> ApprovalDecision:
    approvals = manifest or load_manifest()
    if approvals.load_error:
        return ApprovalDecision(False, approvals.load_error)
    if not approvals.store_compatible:
        return ApprovalDecision(
            False,
            "The explanation store hash does not match the reviewed approval manifest.",
        )

    record = approvals.get(context.drug, context.gene, context.phenotype.value)
    if record is None:
        return ApprovalDecision(
            False,
            "No approval exists for this drug, gene, and phenotype context.",
        )
    if record.status != APPROVED:
        return ApprovalDecision(
            False,
            f"Explanation approval status is {record.status}: {record.reason}",
            record,
        )
    if record.review_kind != AUTHOR_REVIEW or not record.adjudicated_by:
        return ApprovalDecision(
            False,
            "The approval is not bound to a named human provenance adjudication.",
            record,
        )
    if "automated" in {name.strip().lower() for name in record.adjudicated_by}:
        return ApprovalDecision(
            False,
            "An automated adjudication cannot be represented as human approval.",
            record,
        )
    if record.clinical_expert_review_status != NO_EXPERT_REVIEW:
        return ApprovalDecision(
            False,
            "The manifest makes an unsupported clinical-expert review claim.",
            record,
        )
    if content_hash(stored.explanation) != record.content_hash:
        return ApprovalDecision(False, "Approved content hash does not match.", record)
    if stored_source_hash(stored) != record.source_hash:
        return ApprovalDecision(False, "Stored source binding has changed.", record)
    if context_source_hash(context) != record.source_hash:
        return ApprovalDecision(
            False,
            "Runtime source context is incompatible with the approved source.",
            record,
        )
    if stored_context_hash(stored) != record.context_hash:
        return ApprovalDecision(False, "Stored semantic identity has changed.", record)
    if runtime_context_hash(context) != record.context_hash:
        return ApprovalDecision(
            False,
            "Runtime semantic context is incompatible with the approved context.",
            record,
        )
    return ApprovalDecision(True, "Approved content and context match.", record)
