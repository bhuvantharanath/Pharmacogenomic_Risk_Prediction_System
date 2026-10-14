"""Capture final local evidence inventory; never modify production artifacts."""
import datetime
import json
import subprocess
from prepare import ROOT, OUT, digest, save

protocol = json.loads((OUT / "frozen-protocol.json").read_text())
assert digest(OUT / "frozen-protocol.json") == (OUT / "frozen-protocol.sha256").read_text().strip()
for name, expected in protocol["hashes"].items():
    assert digest(ROOT / name) == expected, name
gate = json.loads((OUT / "release-status.json").read_text())
assert all(c["passed"] for c in gate["required_checks"]) and len(gate["required_checks"]) == 6
assert not gate["release_ready"] and gate["clinical_expert_review"] == "NOT_OBTAINED"
assert gate["candidate_artifact_hash"] == "de4434adc05db07271e6fc34175098cde0163283495466b395ed2d2fd415db44"
status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
(OUT / "git-status.txt").write_text(status)
subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
save("final-verification.json", {
    "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "frozen_artifacts_unchanged": True, "release_artifact_unchanged": True,
    "release_ready": gate["release_ready"], "required_checks": [c["name"] for c in gate["required_checks"]],
    "modified_tracked_files": sum(l[:2] == " M" for l in status.splitlines()),
    "untracked_status_entries": sum(l.startswith("??") for l in status.splitlines()),
    "staged_changes": sum(l[0] not in " ?" for l in status.splitlines()),
    "scope": "F4 audit-output additions only; preexisting changes preserved"})
paths = sorted(p for p in OUT.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "artifact-checksums.json")
save("artifact-checksums.json", {"algorithm": "SHA-256 raw bytes", "files": [
    {"path": str(p.relative_to(OUT)), "bytes": p.stat().st_size, "sha256": digest(p)} for p in paths]})
print("Frozen inputs unchanged; six required checks pass; gate remains NOT READY;", len(paths), "artifact checksums recorded")
