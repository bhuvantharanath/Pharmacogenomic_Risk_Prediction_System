"""Authoritative audited drug/gene capability registry.

PharmCAT remains free to parse its full upstream report.  This registry defines
the smaller surface this application has audited and is willing to present.
The Flutter constants are generated from the same JSON file; they are not an
independent capability declaration.
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path


REGISTRY_PATH = Path(__file__).parent / "data" / "capabilities.json"


@dataclass(frozen=True)
class DrugCapability:
    drug: str
    primary_gene: str
    relevant_genes: tuple[str, ...]
    evidence_dependencies: tuple[str, ...]
    implementation_status: str
    guidance_capable: bool
    limitation: str
    explanation_available: bool
    ui_available: bool
    export_available: bool

    def public_dict(self) -> dict[str, object]:
        return {
            "drug": self.drug,
            "primary_gene": self.primary_gene,
            "relevant_genes": list(self.relevant_genes),
            "evidence_dependencies": list(self.evidence_dependencies),
            "implementation_status": self.implementation_status,
            "guidance_capable": self.guidance_capable,
            "limitation": self.limitation,
            "explanation_available": self.explanation_available,
            "ui_available": self.ui_available,
            "export_available": self.export_available,
        }


@functools.lru_cache(maxsize=1)
def load_registry(path: Path | None = None) -> tuple[DrugCapability, ...]:
    target = path or REGISTRY_PATH
    payload = json.loads(target.read_text(encoding="utf-8"))
    raw_entries = payload.get("capabilities") or []
    entries = tuple(
        DrugCapability(
            drug=str(raw["drug"]).strip().lower(),
            primary_gene=str(raw["primary_gene"]).strip().upper(),
            relevant_genes=tuple(str(g).strip().upper() for g in raw["relevant_genes"]),
            evidence_dependencies=tuple(
                str(g).strip().upper() for g in raw["evidence_dependencies"]
            ),
            implementation_status=str(raw["implementation_status"]),
            guidance_capable=bool(raw["guidance_capable"]),
            limitation=str(raw["limitation"]).strip(),
            explanation_available=bool(raw["explanation_available"]),
            ui_available=bool(raw["ui_available"]),
            export_available=bool(raw["export_available"]),
        )
        for raw in raw_entries
    )
    names = [entry.drug for entry in entries]
    if not entries or len(names) != len(set(names)):
        raise ValueError("Capability registry must contain unique drug entries")
    for entry in entries:
        if not entry.primary_gene or not entry.evidence_dependencies or not entry.limitation:
            raise ValueError(f"Incomplete capability registry entry: {entry.drug}")
        if entry.primary_gene not in entry.relevant_genes:
            raise ValueError(f"Primary gene missing from relevant genes: {entry.drug}")
    return entries


def capability_for(drug: str) -> DrugCapability | None:
    key = drug.strip().lower()
    return next((entry for entry in load_registry() if entry.drug == key), None)


def presentation_capabilities() -> tuple[DrugCapability, ...]:
    return tuple(entry for entry in load_registry() if entry.ui_available)

