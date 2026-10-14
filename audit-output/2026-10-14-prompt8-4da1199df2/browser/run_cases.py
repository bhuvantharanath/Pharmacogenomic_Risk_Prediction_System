"""Drive the task-owned Chrome through each evidence-table browser case.

Usage: run_cases.py <session-label> <case-id>[,<case-id>...] [--print=D05,...] [--small=D05,...]

Real UI route only: the file card opens the browser's file chooser (fulfilled
via CDP with the fixture path), drugs are typed into the field, Analyze is
clicked, every disclosure is expanded and the whole list is scrolled and
photographed. Export JSON / Copy JSON / Printable summary are pressed through
the UI; the downloaded file, the system clipboard (pbpaste) and the saved PDF
are collected as produced. A guard fails the case if the backend saw more
analyze requests than this script issued (an external actor clicked once).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
REPO = AUDIT.parents[1]
label = sys.argv[1]
case_ids = sys.argv[2].split(",")
opts = {a.split("=")[0]: a.split("=")[1].split(",") for a in sys.argv[3:] if "=" in a}
PRINT_CASES = set(opts.get("--print", []))
SKIP_CLIPBOARD = '--no-clipboard' in sys.argv  # headless Chrome does not write the system pasteboard
SMALL_CASES = set(opts.get("--small", []))
SESSION = HERE / label
CASES = SESSION / "cases"
CASES.mkdir(parents=True, exist_ok=True)
table = {f["id"]: f for f in json.loads((AUDIT / "fixtures/EVIDENCE-TABLE.json").read_text())["fixtures"]}
RECOVERY = "D01"
HOME = "http://127.0.0.1:3000/"


def cmd(payload: dict, timeout: float = 90):
    req = urllib.request.Request("http://127.0.0.1:9444/", data=json.dumps(payload).encode(), method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read())
    if not body.get("ok"):
        raise RuntimeError(f"{payload.get('op')}: {body.get('error')}")
    return body["result"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


NODES = """(() => [...document.querySelectorAll('flt-semantics, flt-semantics input, flt-semantics textarea')].map(el => {
  const r = el.getBoundingClientRect();
  const label = (el.getAttribute('aria-label') || '').trim();
  const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').trim();
  const role = el.getAttribute('role') || (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' ? 'textbox' : '');
  return { text: label || own, role, expanded: el.getAttribute('aria-expanded'),
           disabled: el.getAttribute('aria-disabled') === 'true', x: Math.round(r.x), y: Math.round(r.y),
           w: Math.round(r.width), h: Math.round(r.height) };
}).filter(n => n.w > 0 && n.h > 0 && (n.text || n.role)))()"""


def nodes():
    return cmd({"op": "eval", "expr": NODES})


def net():
    return cmd({"op": "state"})["network"]


def posts(path: str):
    return [v for v in net().values() if v["method"] == "POST" and v["url"].endswith(path)]


def wait_post(path: str, before: int, timeout: float = 120):
    end = time.time() + timeout
    while time.time() < end:
        done = [p for p in posts(path) if p.get("finished") or p.get("failed") or p.get("status")]
        if len(done) > before and (done[-1].get("finished") or done[-1].get("failed")):
            return done[-1]
        time.sleep(0.25)
    raise TimeoutError(path)


def click_node(predicate, describe: str, scroll_tries: int = 70):
    for attempt in range(scroll_tries):
        if attempt == 4:
            # Not found while moving down: the target may be above the
            # viewport (Flutter only keeps nearby nodes), so restart at the top.
            scroll_top()
        hits = [n for n in nodes() if predicate(n)]
        visible = [n for n in hits if 92 <= n["y"] + n["h"] // 2 <= VIEW_H - 8]
        if visible:
            n = visible[0]
            cmd({"op": "click", "x": n["x"] + n["w"] // 2, "y": n["y"] + n["h"] // 2})
            return n
        if hits:
            target = hits[0]["y"] + hits[0]["h"] // 2
            cmd({"op": "wheel", "x": VIEW_W // 2, "y": VIEW_H // 2, "dy": max(-600, min(600, target - VIEW_H // 2))})
        else:
            # Opened rows now stay open (DEF-5 fix), so the list can be long.
            cmd({"op": "wheel", "x": VIEW_W // 2, "y": VIEW_H // 2, "dy": 600})
        time.sleep(0.4)
    raise LookupError(describe)


def scroll_top():
    for _ in range(12):
        cmd({"op": "wheel", "x": VIEW_W // 2, "y": VIEW_H // 2, "dy": -3000})
        time.sleep(0.15)


def sweep(case_dir: Path, prefix: str, expand: bool):
    """Expand every collapsed disclosure while moving down, photographing each
    step as it is expanded (the expanded state does not survive scrolling far
    away and back — a separately reproduced defect — so a second pass from the
    top would photograph collapsed cards)."""
    texts: list[str] = []
    if expand:
        scroll_top()
        stuck: set[str] = set()
        shots = []
        for _ in range(200):
            pending = [n for n in nodes() if n["expanded"] == "false" and n["text"][:60] not in stuck
                       and 92 <= n["y"] + min(n["h"], 44) // 2 <= VIEW_H - 8]
            if pending:
                n = pending[0]
                # A disclosure's tap target is not always at the node's top
                # (the summary card toggles on its warnings row), so try a few
                # offsets and stop as soon as the node reports expanded.
                offsets = sorted({min(n["h"] // 2, 22), int(n["h"] * 0.62), int(n["h"] * 0.78), max(n["h"] - 14, 1)})
                toggled = False
                for dy in offsets:
                    y = n["y"] + dy
                    if not 92 <= y <= VIEW_H - 8:
                        continue
                    cmd({"op": "click", "x": n["x"] + min(n["w"] // 2, 300), "y": y})
                    time.sleep(0.45)
                    if any(m["text"][:60] == n["text"][:60] and abs(m["y"] - n["y"]) <= 6
                           and m["expanded"] == "true" for m in nodes()):
                        toggled = True
                        break
                if not toggled:
                    stuck.add(n["text"][:60])
                continue
            name = f"{prefix}-{len(shots):02d}"
            cmd({"op": "screenshot", "name": f"{case_dir.name}/{name}"})
            shots.append(name)
            for m in nodes():
                if m["text"] and m["text"] not in texts:
                    texts.append(m["text"])
            before = json.dumps([(m["text"][:40], m["y"]) for m in nodes()])
            cmd({"op": "wheel", "x": VIEW_W // 2, "y": VIEW_H // 2, "dy": 450})
            time.sleep(0.45)
            if json.dumps([(m["text"][:40], m["y"]) for m in nodes()]) == before:
                break
        return shots, texts, sorted(stuck)
    scroll_top()
    time.sleep(0.4)
    shots = []
    for i in range(60):
        name = f"{prefix}-{i:02d}"
        cmd({"op": "screenshot", "name": f"{case_dir.name}/{name}"})
        shots.append(name)
        for n in nodes():
            if n["text"] and n["text"] not in texts:
                texts.append(n["text"])
        before = json.dumps([(n["text"][:40], n["y"]) for n in nodes()])
        cmd({"op": "wheel", "x": VIEW_W // 2, "y": VIEW_H // 2, "dy": VIEW_H - 160})
        time.sleep(0.45)
        if json.dumps([(n["text"][:40], n["y"]) for n in nodes()]) == before:
            break
    return shots, texts


def upload(path: Path, card_text: str):
    before = len(posts("/coverage"))
    cmd({"op": "set_upload", "path": str(path)})
    click_node(lambda n: n["role"] == "button" and n["text"].startswith(card_text), "file card")
    return wait_post("/coverage", before)


def set_drugs_and_analyze(drugs: str, case_dir: Path):
    click_node(lambda n: n["text"] == "Drugs (comma-separated)", "drugs field")
    time.sleep(0.4)
    cmd({"op": "key", "key": "a", "code": "KeyA", "vk": 65, "modifiers": 4, "commands": ["selectAll"]})
    cmd({"op": "type", "text": drugs})
    time.sleep(0.3)
    typed = cmd({"op": "eval", "expr": "(() => { const i = document.querySelector('input, textarea'); return i ? i.value : null; })()"})
    before = len(posts("/analyze"))
    click_node(lambda n: n["role"] == "button" and n["text"] == "Analyze", "Analyze")
    time.sleep(0.2)
    cmd({"op": "screenshot", "name": f"{case_dir.name}/loading"})
    loading = [n for n in nodes() if n["role"] in ("button", "checkbox") or "Analys" in n["text"]]
    resp = wait_post("/analyze", before)
    time.sleep(1.6)
    return typed, loading, resp


def collect_download(case_dir: Path, known: set[str]):
    end = time.time() + 30
    while time.time() < end:
        for d in cmd({"op": "state"})["downloads"]:
            if d["guid"] not in known and d.get("state") == "completed":
                known.add(d["guid"])
                src = SESSION / "downloads" / d["suggestedFilename"]
                dest = case_dir / f"download-{d['suggestedFilename']}"
                shutil.move(str(src), dest)
                raw = dest.read_bytes()
                return {"file": dest.name, "bytes": len(raw), "sha256": sha(raw), "event": d}
        time.sleep(0.3)
    return {"error": "no completed download within 30 s", "downloads": cmd({"op": "state"})["downloads"]}


def collect_print(case_dir: Path):
    pdir = SESSION / "print"
    end = time.time() + 45
    while time.time() < end:
        pdfs = sorted(p for p in pdir.glob("*.pdf"))
        if pdfs:
            time.sleep(1.5)
            src = pdfs[0]
            dest = case_dir / "print.pdf"
            shutil.move(str(src), dest)
            raw = dest.read_bytes()
            return {"file": dest.name, "original_name": src.name, "bytes": len(raw), "sha256": sha(raw)}
        time.sleep(0.5)
    return {"error": "no PDF within 45 s"}


VIEW_W, VIEW_H = 1280, 720
known_downloads: set[str] = {d["guid"] for d in cmd({"op": "state"})["downloads"]}
summary = []
for cid in case_ids:
    f = table[cid]
    case_dir = CASES / cid
    case_dir.mkdir(exist_ok=True)
    rec = {"id": cid, "label": f["label"], "fixture": f["upload_copy"], "fixture_sha256": f["source_sha256"],
           "drugs": f["drugs"], "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    analyze_clicks = 0
    analyze_before = len(posts("/analyze"))
    VIEW_W, VIEW_H = 1280, 720
    cmd({"op": "viewport", "w": VIEW_W, "h": VIEW_H, "mobile": False})
    cmd({"op": "navigate", "url": HOME})
    time.sleep(5)
    cmd({"op": "semantics"})
    time.sleep(1.5)
    cov = upload(REPO / f["upload_copy"], "No file selected")
    rec["coverage"] = {k: cov.get(k) for k in ("status", "body_sha256", "body_file", "failed")}
    time.sleep(1.2)
    cmd({"op": "wheel", "x": 640, "y": 500, "dy": 700})
    time.sleep(0.6)
    cmd({"op": "screenshot", "name": f"{cid}/readiness"})
    rec["readiness_text"] = [n["text"] for n in nodes() if n["text"]]
    typed, loading, ana = set_drugs_and_analyze(f["drugs"], case_dir)
    analyze_clicks += 1
    rec["typed_drugs"] = typed
    rec["loading_controls"] = [{k: n[k] for k in ("text", "role", "disabled")} for n in loading]
    rec["analyze"] = {k: ana.get(k) for k in ("status", "body_sha256", "body_file", "failed")}
    if ana.get("status") != 200:
        cmd({"op": "screenshot", "name": f"{cid}/error"})
        rec["error_view_text"] = [n["text"] for n in nodes() if n["text"]]
        rec["controls_after_error"] = [{k: n[k] for k in ("text", "role", "disabled")} for n in nodes() if n["role"] in ("button", "checkbox")]
        if cid in SMALL_CASES:
            VIEW_W, VIEW_H = 360, 640
            cmd({"op": "viewport", "w": 360, "h": 640, "mobile": True})
            time.sleep(1)
            rec["small_shots"], _ = sweep(case_dir, "small-error", expand=False)
            VIEW_W, VIEW_H = 1280, 720
            cmd({"op": "viewport", "w": 1280, "h": 720, "mobile": False})
            time.sleep(1)
        rf = table[RECOVERY]
        name = Path(f["upload_copy"]).name
        rcov = upload(REPO / rf["upload_copy"], name)
        rec["recovery_coverage"] = {k: rcov.get(k) for k in ("status", "body_sha256")}
        time.sleep(1)
        _, _, rana = set_drugs_and_analyze(rf["drugs"], case_dir)
        analyze_clicks += 1
        rec["recovery_analyze"] = {k: rana.get(k) for k in ("status", "body_sha256", "body_file")}
        cmd({"op": "screenshot", "name": f"{cid}/recovery-results"})
        rec["recovery_results_text"] = [n["text"] for n in nodes() if n["text"]][:40]
    else:
        rec["results_shots"], rec["results_text"], rec["disclosures_not_toggled"] = sweep(case_dir, "results", expand=True)
        scroll_top()
        click_node(lambda n: n["role"] == "button" and n["text"] == "Export JSON" and n["y"] > 90, "Export JSON (body)")
        rec["download"] = collect_download(case_dir, known_downloads)
        scroll_top()
        if SKIP_CLIPBOARD:
            rec["clipboard"] = {"skipped": "headless session; system clipboard not reachable"}
        else:
            click_node(lambda n: n["role"] == "button" and n["text"] == "Copy JSON" and n["y"] > 90, "Copy JSON (body)")
            time.sleep(1.2)
            clip = subprocess.run(["pbpaste"], capture_output=True).stdout
            (case_dir / "clipboard.json").write_bytes(clip)
            rec["clipboard"] = {"bytes": len(clip), "sha256": sha(clip)}
        if cid in PRINT_CASES:
            scroll_top()
            click_node(lambda n: n["role"] == "button" and n["text"] == "Printable summary", "Printable summary")
            rec["print"] = collect_print(case_dir)
        if cid in SMALL_CASES:
            VIEW_W, VIEW_H = 360, 640
            cmd({"op": "viewport", "w": 360, "h": 640, "mobile": True})
            time.sleep(1.2)
            rec["small_shots"], rec["small_text"] = sweep(case_dir, "small", expand=False)
            VIEW_W, VIEW_H = 1280, 720
            cmd({"op": "viewport", "w": 1280, "h": 720, "mobile": False})
            time.sleep(1)
    rec["analyze_requests_seen"] = len(posts("/analyze")) - analyze_before
    rec["analyze_clicks_issued"] = analyze_clicks
    rec["external_interference"] = rec["analyze_requests_seen"] != analyze_clicks
    rec["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    (case_dir / "case.json").write_text(json.dumps(rec, indent=1) + "\n")
    summary.append({k: rec.get(k) for k in ("id", "coverage", "analyze", "external_interference")})
    print(cid, rec["coverage"]["status"], rec["analyze"]["status"], "interference" if rec["external_interference"] else "clean", flush=True)

(SESSION / f"run-{int(time.time())}.json").write_text(json.dumps(summary, indent=1) + "\n")
