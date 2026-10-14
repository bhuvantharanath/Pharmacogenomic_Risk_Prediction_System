#!/usr/bin/env python3
"""Inspect demo fixtures before any expectation is assigned.

Usage: inspect_fixtures.py <repo> <fixtures.json> <out.json>

Reads raw VCF bytes only. Compares each file against the documented position
contract (backend/app/data/position_requirements.json, read as data) without
importing application code, so the census is independent of the parser under
test. It never edits, fills or normalises a fixture.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

repo, spec_path, out_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
spec = json.loads(spec_path.read_text())
contract = json.loads((repo / "backend/app/data/position_requirements.json").read_text())
MAX_UPLOAD = 5 * 1024 * 1024  # documented in docs/input_requirements.md and vcf_validation.py


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def lines(path: Path):
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        try:
            text = gzip.decompress(raw).decode("utf-8", "replace")
        except (OSError, EOFError) as exc:  # truncated/corrupt gzip is itself a finding
            return None, f"gzip decode failed: {type(exc).__name__}: {exc}"
    else:
        text = raw.decode("utf-8", "replace")
    return text.splitlines(), None


def gt_class(gt: str) -> str:
    if gt in (".", "./.", ".|."):
        return "no-call"
    alleles = gt.replace("|", "/").split("/")
    if len(alleles) != 2:
        return f"non-diploid({gt})"
    if "." in alleles:
        return "partial"
    if alleles == ["0", "0"]:
        return "hom-ref"
    if alleles[0] == alleles[1]:
        return "hom-alt"
    return "het"


def inspect(entry: dict) -> dict:
    path = repo / entry["path"]
    rec = {k: v for k, v in entry.items()}
    rec["exists"] = path.is_file()
    if not rec["exists"]:
        return rec
    rec["bytes"] = path.stat().st_size
    rec["sha256"] = sha256(path)
    rec["gzip"] = path.read_bytes()[:2] == b"\x1f\x8b"
    rec["over_upload_limit"] = rec["bytes"] > MAX_UPLOAD
    body, error = lines(path)
    if error:
        rec["decode_error"] = error
        return rec
    header = [l for l in body if l.startswith("##")]
    chrom = [l for l in body if l.startswith("#CHROM")]
    data = [l for l in body if l and not l.startswith("#")]
    rec["fileformat"] = next((l for l in header if l.startswith("##fileformat")), None)
    rec["build_declarations"] = sorted({
        part for l in header for part in ("GRCh38", "GRCh37", "hg19", "hg38", "b37")
        if part in l and (l.startswith("##contig") or l.startswith("##reference") or l.startswith("##assembly"))
    })
    rec["synthetic_annotations"] = [l for l in header if "pharmaguard_synthetic" in l or l.startswith("##source=")][:12]
    rec["chrom_header_present"] = bool(chrom)
    rec["samples"] = chrom[0].split("\t")[9:] if chrom else []
    rec["records"] = len(data)
    filters, classes, malformed = Counter(), Counter(), 0
    by_pos: dict[tuple[str, int], list[dict]] = {}
    for line in data:
        c = line.split("\t")
        if len(c) < 10:
            malformed += 1
            continue
        filters[c[6]] += 1
        fmt = c[8].split(":")
        values = c[9].split(":")
        gt = values[fmt.index("GT")] if "GT" in fmt and fmt.index("GT") < len(values) else None
        cls = gt_class(gt) if gt is not None else "missing-GT"
        classes[cls] += 1
        try:
            pos = int(c[1])
        except ValueError:
            malformed += 1
            continue
        by_pos.setdefault((c[0], pos), []).append({"filter": c[6], "gt": gt, "class": cls})
    rec["malformed_data_lines"] = malformed
    rec["filter_counts"] = dict(filters)
    rec["genotype_classes"] = dict(classes)
    genes = {}
    for gene, req in contract["genes"].items():
        positions = [(p[0], int(p[1])) for p in req["positions"]]
        critical = {(p[0], int(p[1])) for p in req.get("decision_critical_positions", [])}
        present = [p for p in positions if p in by_pos]
        usable = [
            p for p in present
            if all(r["filter"] in ("PASS", ".") and r["class"] in ("hom-ref", "het", "hom-alt") for r in by_pos[p])
        ]
        nonref = sorted(f"{p[0]}:{p[1]}={by_pos[p][0]['gt']}" for p in present
                        if any(r["class"] in ("het", "hom-alt") for r in by_pos[p]))
        problems = sorted(f"{p[0]}:{p[1]} filter={by_pos[p][0]['filter']} gt={by_pos[p][0]['gt']}"
                          for p in present if p not in usable)
        genes[gene] = {
            "required": len(positions),
            "present": len(present),
            "usable_full_diploid_pass_or_dot": len(usable),
            "critical_required": len(critical),
            "critical_usable": len(critical & set(usable)),
            "nonref_required_positions": nonref,
            "problem_positions": problems,
        }
    rec["required_position_census"] = genes
    return rec


results = [inspect(e) for e in spec["fixtures"]]
out = {
    "inspector": "inspect_fixtures.py (raw-text census; no application code imported)",
    "position_contract": "backend/app/data/position_requirements.json",
    "position_contract_sha256": sha256(repo / "backend/app/data/position_requirements.json"),
    "upload_limit_bytes": MAX_UPLOAD,
    "fixtures": results,
}
out_path.write_text(json.dumps(out, indent=1) + "\n")
for r in results:
    census = r.get("required_position_census", {})
    short = {g: f"{v['usable_full_diploid_pass_or_dot']}/{v['required']}" for g, v in census.items()}
    print(r["id"], r.get("bytes"), (r.get("sha256") or "")[:12], r.get("samples"), r.get("records"),
          r.get("filter_counts"), r.get("genotype_classes"), short, r.get("decode_error", ""))
