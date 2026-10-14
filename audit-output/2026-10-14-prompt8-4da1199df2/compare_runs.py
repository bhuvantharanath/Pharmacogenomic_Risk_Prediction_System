"""Field-by-field comparison of baseline and final API responses for every fixture.
Usage: compare_runs.py <baseline-dir> <final-dir> <out.json>"""
import json, sys
from pathlib import Path
base, fin, out = map(Path, sys.argv[1:4])
VOLATILE = {"timestamp", "processing_time_ms"}
def walk(a, b, path, diffs):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in VOLATILE: continue
            if k not in a or k not in b: diffs.append({"path": f"{path}.{k}", "only_in": "final" if k not in a else "baseline"}); continue
            walk(a[k], b[k], f"{path}.{k}", diffs)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            # warnings list: report set difference instead of positional noise
            sa, sb = set(map(json.dumps, a)), set(map(json.dumps, b))
            diffs.append({"path": path, "removed": [json.loads(x) for x in sorted(sa - sb)], "added": [json.loads(x) for x in sorted(sb - sa)]}); return
        if path.endswith("warnings"):
            sa, sb = set(map(json.dumps, a)), set(map(json.dumps, b))
            if sa != sb: diffs.append({"path": path, "removed": [json.loads(x) for x in sorted(sa - sb)], "added": [json.loads(x) for x in sorted(sb - sa)]})
            return
        for i, (x, y) in enumerate(zip(a, b)): walk(x, y, f"{path}[{i}]", diffs)
    elif a != b:
        diffs.append({"path": path, "baseline": a, "final": b})
report = {}
for f in sorted(base.glob("D*.json")):
    g = fin / f.name
    a, b = json.loads(f.read_text()), json.loads(g.read_text())
    diffs = []; walk(a, b, "$", diffs)
    report[f.name] = diffs
paths = sorted({d["path"].split("[")[0] if "warnings" not in d["path"] else d["path"] for v in report.values() for d in v})
summary = {"files": len(report), "files_with_differences": sum(1 for v in report.values() if v),
           "distinct_changed_paths": sorted({__import__('re').sub(r"\[\d+\]", "[]", d["path"]) for v in report.values() for d in v})}
out.write_text(json.dumps({"summary": summary, "per_file": report}, indent=1) + "\n")
print(json.dumps(summary, indent=1))
