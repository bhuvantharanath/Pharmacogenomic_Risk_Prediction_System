#!/usr/bin/env python3
"""
AC8 of audit/phase9/GATE_AMENDMENT_PLAN.md — after the Deploy workflow.

  1. live /ready reports the expected commit;
  2. live S1–S6 serve no stored prose (`source=template` on every response)
     and carry HEAD's disclaimer;
  3. live S1–S6 labels equal the local HEAD run's labels (zero regression).

Reads the S1–S6 bodies written by measure_warm.py --phase scenarios.

    python verify_postdeploy.py EXPECTED_SHA LIVE_DIR LOCAL_DIR
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

BASE = "https://pharmaguard-api-baml.onrender.com"


def labels(body: dict) -> dict:
    return {a["drug"]: a["risk_assessment"]["risk_label"] for a in body.get("analyses", [])}


def main() -> int:
    expected, live_dir, local_dir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    with urllib.request.urlopen(f"{BASE}/ready", timeout=120) as resp:
        ready = json.loads(resp.read())
    commit = ready.get("build", {}).get("commit", "")
    results = {"ready_commit": commit, "commit_matches": commit == expected, "scenarios": {}}
    ok = results["commit_matches"]
    for path in sorted(live_dir.glob("S*.json")):
        live = json.loads(path.read_text())
        local = json.loads((local_dir / path.name).read_text())
        warnings = live.get("quality_metrics", {}).get("warnings", [])
        sources = sorted({w.split("source=")[1].split(",")[0]
                          for w in warnings if "source=" in w})
        live_disclaimers = {a["llm_generated_explanation"]["disclaimer"] for a in live.get("analyses", [])}
        local_disclaimers = {a["llm_generated_explanation"]["disclaimer"] for a in local.get("analyses", [])}
        row = {
            "labels_live": labels(live),
            "labels_local_head": labels(local),
            "labels_equal": labels(live) == labels(local),
            "explanation_sources": sources,
            "no_stored_prose_served": sources == ["template"],
            "disclaimer_equals_head": live_disclaimers == local_disclaimers,
        }
        row["pass"] = row["labels_equal"] and row["no_stored_prose_served"] and row["disclaimer_equals_head"]
        ok = ok and row["pass"]
        results["scenarios"][path.stem] = row
    results["all_pass"] = ok and len(results["scenarios"]) == 6
    print(json.dumps(results, indent=1))
    return 0 if results["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
