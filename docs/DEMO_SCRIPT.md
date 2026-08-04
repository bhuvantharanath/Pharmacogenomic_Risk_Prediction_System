# Demo runbook — 5 minutes, one command

The demo is a script, not a list of commands to type. Three earlier walkthroughs
each died on a different environmental blocker — a CORS guard firing on an env
marker, a rate limit exhausted by rehearsal, shell quoting mangling file paths.
None was a product defect and all three would have happened live. Rehearsal and
presentation now run the identical code path, and `test_demo_script.py` covers it.

---

## Pre-flight

**1 · JDK 17.** Satisfies both PharmCAT (needs 17+) and the Android Gradle build
(rejects 25). One JDK for both.

```bash
java -version
```

If it is not 17, point at it for this shell — `infra/local-dev.env` records the path:

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@17 && export PATH="$JAVA_HOME/bin:$PATH"
```

**2 · Load local config.** This sets `CORS_ALLOWED_ORIGINS` for localhost.

```bash
set -a && source infra/local-dev.env && set +a
```

> **Why local config sets CORS at all.** The backend refuses to start when hosting
> markers are present (`PORT`, `K_SERVICE`, `SPACE_ID`, `RENDER`) and the allowlist
> is empty. That is a **deliberate hard failure**, not a bug: an unset allowlist
> passes every health check while blocking every real browser request, which is
> the Phase 4 defect the guard exists to catch. Configuring it locally means local
> startup exercises the same path as production. Do not work around the guard.
>
> Note also that the config lives in `infra/local-dev.env`, **not** `backend/.env`
> — a `.env` inside the backend makes `assert_no_baked_secrets` refuse to start,
> because a dotfile inside a deployed image is a credential-leak risk.

**3 · Start the backend** and note the URL it prints — do not assume it.

```bash
cd backend && uvicorn app.main:app --port 8000
```

```
[startup] pharmcat=jar via java -jar …/pharmcat-3.4.0-all.jar
[startup] listening on http://127.0.0.1:8000  (docs at /docs)
```

If that port differs, export it:

```bash
export PHARMAGUARD_API=http://127.0.0.1:<port>
```

**4 · Rehearse freely.** Loopback is exempt from rate limiting, so running the
demo repeatedly from this machine costs nothing. The deployed limit is unchanged.

**Checklist:** `java -version` is 17 · `infra/local-dev.env` sourced · backend up ·
URL noted · terminal font large.

---

## The demo

```bash
python scripts/run_demo.py
```

That runs pre-flight, a JVM warm-up, all six scenarios, and prints the S1/S2
contrast table. **~7 seconds** of compute; the rest is you talking.

For a paced walkthrough that waits for you between scenarios:

```bash
python scripts/run_demo.py --slow
```

---

## What to say

### 0 · Framing (30s)

> "This predicts drug risk from a patient's genome. The interesting part isn't
> that it answers — it's what it does when it shouldn't. Every defect we found
> building it erred the same way: sounding more confident than the evidence
> supported. So it's built to decline."

### 1 · It answers (45s) — S1

**Expect:** `CYP2C19 *2/*2` → PM → **Ineffective**, critical, 7/7 genes at 100%.

> "Poor metaboliser. Clopidogrel is a prodrug this patient never activates. The
> recommendation text is CPIC's own words — we don't write dosing guidance."

### 2 · THE CENTREPIECE (90s) — S2 and the contrast table

**Expect:** **Unknown**, confidence 0.00, CYP2C19 4/35 = 11.4%, variants-only alert.

> "Same patient. Same genotype — PharmCAT still calls \*2/\*2 from this file. The
> only difference is that it lists variants only, with no homozygous-reference
> rows. That's the shape most VCFs in the wild have.
>
> An absent position is indistinguishable from one never tested. So a variant
> whose defining position is missing is invisible, and the genotype reads as
> *normal*. Missing data here doesn't look like uncertainty — it looks like health.
>
> We measured it: up to 28.6% confidently-wrong calls at 60% coverage, and every
> single wrong call reported reduced function as normal. So the system refuses,
> and tells you what to upload instead."

**Pause on the contrast table.** This is the moment.

### 3 · Declining the unknowable (45s) — S3

> "Real 1000 Genomes sample, and it's in GeT-RM — which records its CYP2D6 as
> \*1/\*1. A right answer exists, and we still decline, because CYP2D6 depends on
> copy-number variation a VCF can't express. Not failing to find it. Refusing to
> guess it."

### 4 · A different guard (45s) — S4

**Expect:** **Unknown**, DPYD coverage 37.3% against a 20% minimum — **passing**.

> "Coverage is fine here, so this isn't the gate. PharmCAT called the genotype but
> said Indeterminate. Our lookup table would still have found a row and rendered
> **Safe**, on fluorouracil, where DPYD deficiency is fatal. Found at 400 samples.
> Fixing it generally rather than patching DPYD changed 294 results — 293 of them
> on other genes a targeted patch would have missed."

### 5 · It still answers (30s) — S5 and S6

> "Not a system that says Unknown to everything. Five drugs in one request, and an
> unsupported drug degrades to Unknown rather than erroring."

### 6 · The evidence (45s)

```bash
python scripts/validate_label_mapping.py
```

> "92 of 105 — exhaustive, every phenotype combination for all six drugs, not a
> sample. The 13 are documented divergences."

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
| S1 | 0:45 |
| **S2 + contrast** | **1:30** |
| S3 | 0:45 |
| S4 | 0:45 |
| S5 / S6 | 0:30 |
| Evidence | 0:45 |
| **Total** | **5:30** |

Cut S4 first if short, S3 second. **Never cut S2.**

---

## Fallbacks

| Failure | What to do |
| --- | --- |
| Pre-flight says UNREACHABLE | It prints the start command. Backend probably not running, or on another port — check the startup line and set `PHARMAGUARD_API`. |
| Backend refuses to start, CORS error | `infra/local-dev.env` was not sourced. The guard is correct; source it and restart. |
| Backend refuses to start, baked-secret error | A `backend/.env` exists. Delete it — config belongs in `infra/local-dev.env`. |
| A scenario returns 429 | Should not happen from loopback. If presenting from another machine, wait the `Retry-After` seconds. |
| Backend dies mid-demo | Every response is pre-captured in `test-data/demo/outputs/`. Say so plainly and read from those — they are real output, not mock-ups. |
| Anything else | `python scripts/run_demo.py --scenario 2` runs the centrepiece alone in ~1 second. |
