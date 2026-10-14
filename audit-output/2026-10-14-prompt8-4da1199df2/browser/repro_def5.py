"""DEF-5 reproduction: expanded result cards collapse after scrolling to the
export buttons and back. Fresh analysis of D01 through the real UI, then:
expand all six drug cards, record state, scroll to the bottom (Export JSON),
scroll back to the top, record state again, screenshot each step.
Usage: repro_def5.py <session-label>"""
import json, sys, time, urllib.request
from pathlib import Path
HERE = Path(__file__).resolve().parent; AUDIT = HERE.parent; REPO = AUDIT.parents[1]
label = sys.argv[1]; OUT = HERE / label / "def5"; OUT.mkdir(parents=True, exist_ok=True)
def cmd(p, t=90):
    r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:9444/", data=json.dumps(p).encode(), method="POST"), timeout=t)
    b = json.loads(r.read()); assert b["ok"], b; return b["result"]
EXP = """(() => [...document.querySelectorAll('flt-semantics[aria-expanded]')].map(e => { const r=e.getBoundingClientRect();
  return {t:(e.getAttribute('aria-label')||e.textContent||'').replace(/\\n/g,' ').slice(0,40), e:e.getAttribute('aria-expanded'), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)}; }))()"""
def state(): return cmd({"op": "eval", "expr": EXP})
def wheel(dy, n=1):
    for _ in range(n): cmd({"op": "wheel", "x": 640, "y": 400, "dy": dy}); time.sleep(0.25)
log = []
fixture = REPO / json.loads((AUDIT / "fixtures/EVIDENCE-TABLE.json").read_text())["fixtures"][0]["upload_copy"]
cmd({"op": "viewport", "w": 1280, "h": 720, "mobile": False}); cmd({"op": "navigate", "url": "http://127.0.0.1:3000/"}); time.sleep(5)
cmd({"op": "semantics"}); time.sleep(1.5)
cmd({"op": "set_upload", "path": str(fixture)}); cmd({"op": "click_text", "text": "No file selected"}); time.sleep(2.5)
for _ in range(20):  # bring the button into the viewport before clicking it
    hit = [n for n in cmd({"op": "nodes"}) if n["text"] == "Check all 6 medicines"]
    if hit and 100 <= hit[0]["y"] + hit[0]["h"] // 2 <= 700:
        cmd({"op": "click", "x": hit[0]["x"] + hit[0]["w"] // 2, "y": hit[0]["y"] + hit[0]["h"] // 2}); break
    cmd({"op": "wheel", "x": 640, "y": 400, "dy": 300}); time.sleep(0.4)
time.sleep(5)
drugs = ["azathioprine", "clopidogrel", "fluorouracil", "simvastatin", "codeine", "warfarin"]
wheel(-3000, 6); time.sleep(0.5)
for d in drugs:  # expand each drug card by its header, scrolling it into view
    for _ in range(12):
        hit = [n for n in state() if n["t"].startswith(d + ":")]
        if hit and 100 <= hit[0]["y"] + 22 <= 700:
            cmd({"op": "click", "x": hit[0]["x"] + 300, "y": hit[0]["y"] + 22}); time.sleep(0.6); break
        wheel(350); time.sleep(0.3)
wheel(-3000, 6); time.sleep(0.6)
s1 = state(); log.append({"step": "after expanding all six cards, at top", "expanded": [n["t"] for n in s1 if n["e"] == "true"]})
cmd({"op": "screenshot", "name": "../def5/01-expanded-top"})
wheel(3000, 8); time.sleep(0.8)
s2 = state(); log.append({"step": "scrolled to bottom (Export JSON visible)", "expanded": [n["t"] for n in s2 if n["e"] == "true"], "collapsed": [n["t"] for n in s2 if n["e"] == "false"]})
cmd({"op": "screenshot", "name": "../def5/02-bottom"})
wheel(-3000, 8); time.sleep(0.8)
s3 = state(); log.append({"step": "scrolled back to top", "expanded": [n["t"] for n in s3 if n["e"] == "true"], "collapsed": [n["t"] for n in s3 if n["e"] == "false"]})
cmd({"op": "screenshot", "name": "../def5/03-back-at-top"})
(OUT / "repro.json").write_text(json.dumps(log, indent=1) + "\n")
print(json.dumps(log, indent=1))
