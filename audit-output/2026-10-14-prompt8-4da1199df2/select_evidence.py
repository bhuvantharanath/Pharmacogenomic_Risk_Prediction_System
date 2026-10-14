"""List the curated subset of this audit directory that is committed.

Usage: select_evidence.py  (writes COMMITTED-EVIDENCE.txt next to this file)
Large or regenerable outputs stay local: web builds, upload copies, raw caller
outputs, raw capture bodies, full screenshot sets and checkpoints.
"""
from pathlib import Path

A = Path(__file__).resolve().parent
R = A.parents[1]
pick: list[Path] = []


def add(*patterns: str) -> None:
    for pattern in patterns:
        hits = sorted(p for p in A.glob(pattern) if p.is_file())
        assert hits, pattern
        pick.extend(hits)


add("PROMPT-8-REPORT.md", "DEFECTS.md", "DEMO-GUIDE.md", "HANDOFF.md", "started-utc.txt", "*.py",
    "api-harness-*.stdout", "env/environment.txt")
add("start/START-STATE.json", "start/head.txt", "start/branch.txt", "start/git-diff-stat.txt",
    "start/git-status-porcelain-v1.txt", "start/git-status-porcelain-v2.txt",
    "start/git-status-uall-delta-vs-prompt7.diff", "start/freeze-comparison-vs-prompt7.json")
add("fixtures/EVIDENCE-TABLE.json", "fixtures/EVIDENCE-TABLE.sha256", "fixtures/candidates.json",
    "fixtures/evidence_table_spec.py", "fixtures/inspection.json")
for run in ("api-harness-baseline", "api-harness-final2"):
    add(f"{run}/results.json", f"{run}/D*.coverage.json", f"{run}/D*.analyze.json")
add("verification/*", "regression/*", "tests/*", "diff/*", "sources/*", "servers/*",
    "failed-attempts/**/*", "prefix-snapshot/**/*", "builds/*.json", "builds/*.stdout", "builds/*.stderr")
add("refresh/*", "refresh/prefix-snapshot/**/*")
add("browser/cdp_agent.mjs", "browser/run_cases.py", "browser/repro_def5.py")
for run in ("run-baseline", "run-final", "run-final3", "run-final4-print"):
    add(f"browser/{run}/chrome-command.json", f"browser/{run}/chrome-exit.json",
        f"browser/{run}/matrix*.std*", f"browser/{run}/run-*.json", f"browser/{run}/cases/*/case.json")
add("browser/run-baseline/final-state.json", "browser/run-baseline/def5/*", "browser/run-final3/def5/*",
    "browser/run-final3/def5.stdout")
# Before-state screens and prints cited in DEFECTS.md.
add("browser/run-baseline/screens/D01/readiness.png", "browser/run-baseline/screens/D06/results-00.png",
    "browser/run-baseline/screens/D08/error.png", "browser/run-baseline/screens/D10/*.png",
    "browser/run-baseline/screens/D11/results-03.png", "browser/run-baseline/screens/about/about-bottom-baseline.png",
    "browser/run-baseline/superseded/probe-offscreen-render-2.png",
    "browser/run-baseline/cases/D10/print-page-4.png", "browser/run-baseline/cases/D15/print-page-3.png",
    "browser/run-baseline/cases/D05/download-*.json", "browser/run-baseline/cases/D05/clipboard.json")
# After-state screens cited in DEFECTS.md and DEMO-GUIDE.md.
add("browser/run-final/screens/D01/readiness.png", "browser/run-final/screens/D02/results-00.png",
    "browser/run-final/screens/D04/results-00.png", "browser/run-final/screens/D05/results-00.png",
    "browser/run-final/screens/D06/results-00.png", "browser/run-final/screens/D10/results-03.png",
    "browser/run-final/screens/D10/results-04.png", "browser/run-final/screens/D12/results-03.png",
    "browser/run-final/screens/D15/results-00.png", "browser/run-final/screens/D08/error.png",
    "browser/run-final/screens/D08/recovery-results.png", "browser/run-final/screens/D09/error.png",
    "browser/run-final/screens/D09/recovery-results.png")
# Final-build native PDFs and the pages cited.
add("browser/run-final4-print/cases/*/print.pdf", "browser/run-final4-print/cases/*/print-extracted.txt",
    "browser/run-final4-print/cases/D10/print-page-4.png", "browser/run-final4-print/cases/D15/print-page-3.png")

seen, lines = set(), []
for p in pick:
    rel = p.relative_to(R).as_posix()
    if rel not in seen and "__pycache__" not in rel:
        seen.add(rel); lines.append(rel)
lines.append((A / "COMMITTED-EVIDENCE.txt").relative_to(R).as_posix())
(A / "COMMITTED-EVIDENCE.txt").write_text("\n".join(sorted(lines)) + "\n")
total = sum((R / l).stat().st_size for l in lines if (R / l).exists())
print(len(lines), "files,", f"{total:,}", "bytes")
