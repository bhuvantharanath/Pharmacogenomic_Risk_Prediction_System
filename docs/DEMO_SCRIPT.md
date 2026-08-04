# Demo script — 5 minutes

The centrepiece is **one contrast**, not a feature tour: the same patient, two
file shapes, two different and both-correct answers.

## Pre-flight (do before the audience is watching)

```bash
cd backend && uvicorn app.main:app --port 8000
```

```bash
curl -s localhost:8000/ready | python3 -m json.tool
```

Confirm `"status": "ready"` and that the `pharmcat` check says `jar: java -jar …`.
Then send one throwaway request to warm the JVM — the first call pays class-loading
and runs ~2× slower, which looks like a stall on stage.

**Checklist:** backend up · `/ready` green · one warm-up request sent · terminal
font large · `test-data/demo/` open in a second pane.

---

## 0 · Framing (30s)

> "This predicts drug risk from a patient's genome. But the interesting part isn't
> that it answers — it's what it does when it *shouldn't*. Every defect we found
> building it erred the same way: sounding more confident than the evidence
> supported. So the system is built to decline."

---

## 1 · It answers when it can (45s) — S1

```bash
curl -s -X POST localhost:8000/analyze -F "file=@test-data/demo/demo_confident.vcf" -F "drugs=clopidogrel" | python3 -m json.tool
```

**Expect:** `CYP2C19 *2/*2` → `PM` → **Ineffective**, severity `critical`,
confidence 0.95, coverage 7/7 genes. ~1.2 s.

> "Poor metaboliser. Clopidogrel is a prodrug — this patient never activates it.
> That's a real finding, and the recommendation text is CPIC's own words, not ours."

**If it fails:** show `test-data/demo/outputs/S1_confident.json`, captured earlier.

---

## 2 · THE CENTREPIECE — same patient, declined (90s) — S2

```bash
curl -s -X POST localhost:8000/analyze -F "file=@test-data/demo/demo_variants_only.vcf" -F "drugs=clopidogrel" | python3 -m json.tool
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
curl -s -X POST localhost:8000/analyze -F "file=@test-data/demo/demo_na12273_1000g.vcf" -F "drugs=codeine" | python3 -m json.tool
```

**Expect:** codeine **Unknown**, CYP2D6 not called, structural-variation warning.

> "Real 1000 Genomes sample. This one is in GeT-RM, the reference panel — which
> records its CYP2D6 as \*1/\*1. So there *is* a right answer, and we still decline,
> because CYP2D6 depends on copy-number variation a VCF cannot express. We're not
> failing to find it. We're refusing to guess it."

---

## 4 · The invariant, isolated (45s) — S4

```bash
curl -s -X POST localhost:8000/analyze -F "file=@test-data/demo/demo_dpyd_indeterminate.vcf" -F "drugs=fluorouracil" | python3 -m json.tool
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
curl -s -X POST localhost:8000/analyze -F "file=@test-data/demo/demo_confident.vcf" -F "drugs=clopidogrel,simvastatin,fluorouracil,codeine,ibuprofen" | python3 -m json.tool
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

## If the backend dies mid-demo

Every response is pre-captured in `test-data/demo/outputs/`. Say so plainly —
"the server's gone, here's the response I captured this morning" — and continue.
The files are real output, not mock-ups.
