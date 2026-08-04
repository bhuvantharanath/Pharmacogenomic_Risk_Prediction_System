# Demo script — 5 minutes

The centrepiece is **one contrast**, not a feature tour: the same patient, two
file shapes, two different and both-correct answers.

## Pre-flight (do before the audience is watching)

**JDK 17.** PharmCAT needs a JRE 17+, and the Android Gradle build rejects JDK 25 —
so **JDK 17 satisfies both** and is the version to have installed. Check first:

```bash
java -version
```

Everything below is backend-only and works on any JRE 17+; only the APK build cares.

**Start the backend and note the URL it prints.**

```bash
cd backend && uvicorn app.main:app --port 8000
```

It prints its own resolved address — do not assume it:

```
[startup] listening on http://127.0.0.1:8000  (docs at /docs)
```

**Export that as `$API` so every command below follows it.** Nothing in this
runbook hardcodes a port.

```bash
export API=<paste the URL from the startup line above>
```

(On a default local run that is `http://127.0.0.1:8000`, but copy it rather than
assume it — the whole point of the printed line is that `--port` may differ.)

> Do **not** set `PORT` to make this line accurate. `PORT` is one of the markers
> the CORS guard reads as "this instance looks hosted", and the backend will refuse
> to start with an empty allowlist. Pass `--port` instead.

```bash
curl -s $API/ready | python3 -m json.tool
```

Confirm `"status": "ready"` and that the `pharmcat` check says `jar: java -jar …`.
Then send one throwaway request to warm the JVM — the first call pays class-loading
and runs ~2× slower, which looks like a stall on stage.

```bash
curl -s -X POST $API/analyze -F "file=@test-data/demo/demo_normal.vcf" -F "drugs=clopidogrel" -o /dev/null -w "warm-up %{time_total}s\n"
```

**Checklist:** `java -version` is 17 · backend up · **URL from the startup line
exported as `$API`** · `/ready` green · warm-up sent · terminal font large ·
`test-data/demo/` open in a second pane.

---

## 0 · Framing (30s)

> "This predicts drug risk from a patient's genome. But the interesting part isn't
> that it answers — it's what it does when it *shouldn't*. Every defect we found
> building it erred the same way: sounding more confident than the evidence
> supported. So the system is built to decline."

---

## 1 · It answers when it can (45s) — S1

```bash
curl -s -X POST $API/analyze -F "file=@test-data/demo/demo_confident.vcf" -F "drugs=clopidogrel" | python3 -m json.tool
```

**Expect:** `CYP2C19 *2/*2` → `PM` → **Ineffective**, severity `critical`,
confidence 0.95, coverage 7/7 genes. ~1.2 s.

> "Poor metaboliser. Clopidogrel is a prodrug — this patient never activates it.
> That's a real finding, and the recommendation text is CPIC's own words, not ours."

**If it fails:** show `test-data/demo/outputs/S1_confident.json`, captured earlier.

---

## 2 · THE CENTREPIECE — same patient, declined (90s) — S2

```bash
curl -s -X POST $API/analyze -F "file=@test-data/demo/demo_variants_only.vcf" -F "drugs=clopidogrel" | python3 -m json.tool
```

**Expect:** **Unknown**, confidence 0.00, `CYP2C19 4/35 positions = 11.4%`, and a
variants-only warning.

> "Same patient. Same genotype — PharmCAT still calls \*2/\*2 from this file. The
> only difference is that this VCF lists variants only, with no homozygous-reference
> rows. That's what most VCFs in the wild look like.
>
> And that's the problem: a position that's absent is indistinguishable from one
> never tested. A variant whose defining position is missing is invisible — so the
> genotype reads as *normal*. Missing data doesn't look like uncertainty here. It
> looks like health.
>
> We measured it: at 60% coverage up to 28.6% of calls were confidently wrong, and
> every single wrong call reported reduced function as normal. So the system
> refuses, and tells you exactly what to upload instead."

**This is the moment.** Pause here.

**If it fails:** `test-data/demo/outputs/S2_variants_only.json`.

---

## 3 · Declining what cannot be known (45s) — S3

```bash
curl -s -X POST $API/analyze -F "file=@test-data/demo/demo_na12273_1000g.vcf" -F "drugs=codeine" | python3 -m json.tool
```

**Expect:** codeine **Unknown**, CYP2D6 not called, structural-variation warning.

> "Real 1000 Genomes sample. This one is in GeT-RM, the reference panel — which
> records its CYP2D6 as \*1/\*1. So there *is* a right answer, and we still decline,
> because CYP2D6 depends on copy-number variation a VCF cannot express. We're not
> failing to find it. We're refusing to guess it."

---

## 4 · The invariant, isolated (45s) — S4

```bash
curl -s -X POST $API/analyze -F "file=@test-data/demo/demo_dpyd_indeterminate.vcf" -F "drugs=fluorouracil" | python3 -m json.tool
```

**Expect:** **Unknown**. DPYD coverage 31/83 = 37.3%, which **passes** its 20%
minimum — so this is not the coverage gate.

> "Coverage is fine here. This is a different guard. PharmCAT called the genotype
> but said `Indeterminate` — it declined to assign a phenotype. Our lookup table
> would still have found a row and rendered **Safe**, on fluorouracil, where DPYD
> deficiency is fatal. We found that at 400 samples. Fixing it generally rather
> than patching DPYD changed 294 results — and 293 of those were on other genes a
> targeted patch would have missed."

---

## 5 · It still answers (30s) — S5 + S6

```bash
curl -s -X POST $API/analyze -F "file=@test-data/demo/demo_confident.vcf" -F "drugs=clopidogrel,simvastatin,fluorouracil,codeine,ibuprofen" | python3 -m json.tool
```

**Expect:** Ineffective / Safe / Safe / Unknown (CYP2D6) / Unknown (ibuprofen —
no CPIC guideline). Five drugs, one request.

> "Not a system that says Unknown to everything. It answers where the evidence
> supports it, and an unsupported drug degrades to Unknown rather than erroring."

---

## 6 · The evidence (45s)

```bash
python scripts/validate_label_mapping.py
```

> "92 of 105 — and that's exhaustive, every phenotype combination for all six
> drugs, not a sample. The 13 are documented divergences, each justified."

```bash
python scripts/adjudication_status.py
```

> "Exits 1. Human review of the explanation prose isn't finished, so the release
> gate is red. It stays red until a person has read every claim."

---

## Timing

| Step | Time |
| --- | ---: |
| Framing | 0:30 |
| S1 confident | 0:45 |
| **S2 contrast** | **1:30** |
| S3 CYP2D6 | 0:45 |
| S4 invariant | 0:45 |
| S5/S6 breadth | 0:30 |
| Evidence | 0:45 |
| **Total** | **5:30** |

Cut S4 first if short; cut S3 second. **Never cut S2.**

## ⚠️ The rate limit will bite you if you rehearse and then present

`/analyze` allows **10 requests per 5 minutes per IP**, in-memory. The demo makes
**7** (warm-up plus six scenarios). Rehearsing and then presenting inside the same
five-minute window exhausts it, and every further call returns **429** in about a
millisecond — which on stage looks exactly like the backend crashing.

Measured: a full clean run is **7.6 s** for six scenarios, plus ~1.2 s warm-up.

**Before presenting, restart the backend.** The limiter is in-memory, so a restart
clears it instantly — faster and more certain than waiting out the window.

```bash
pkill -f "uvicorn app.main:app" && cd backend && uvicorn app.main:app --port 8000
```

Then re-export `$API` from the printed startup line and send one warm-up request.

## If the backend dies mid-demo

Every response is pre-captured in `test-data/demo/outputs/`. Say so plainly —
"the server's gone, here's the response I captured this morning" — and continue.
The files are real output, not mock-ups.
