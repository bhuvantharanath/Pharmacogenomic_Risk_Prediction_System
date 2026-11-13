# PharmaGuard — presentation runbook

Everything below was measured on 2026-11-12 against the working tree. Timings
are from this laptop; re-time on the presentation machine before relying on
them.

## 0. Everything in this runbook is live

Deployed 2026-11-13 from commit `ac69e14`. Verified on the public URL after
the deploy, not assumed:

| | |
|---|---|
| `GET /health` reports commit | **`ac69e14`** |
| Codeine with a supplied DRAGEN call | **Ineffective** — `*4/*5`, Poor Metaboliser, activity score 0.0, `supplied_by: DRAGEN` |
| The four real sample files | served, byte counts matching local |
| The three old authored files | gone — those paths now return the site's fallback page, byte-identical to a nonsense filename |

The release gate ran in CI on this exact commit and passed, which is what let
Render and Cloudflare deploy. The `content review` workflow is red, as it is on
every push: it is named "red until adjudicated" and its four outstanding items
are the unapproved stored prose, which the release policy withholds rather than
serving. It does not block the deploy and it is not a regression.

A good habit anyway: run the health check in section 1 before you present, and
confirm it still says `ac69e14`.

## 1. Before the room

```bash
curl -sS -o /dev/null -w "%{http_code} %{time_total}s\n" https://pharmaguard-api-baml.onrender.com/health
```

Run it **twice**, about ten minutes apart, and again five minutes before you
start. The first wakes the instance; the second confirms it stayed awake.

If you want it reliably warm, run the `keepalive` workflow by hand from the
GitHub Actions tab (`workflow_dispatch`). Its schedule is commented out on
purpose — leaving it on burns Render's 750 instance-hours a month.

Measured today:

| | |
|---|---|
| Cold `/health` after idle | **32.4 s** |
| Warm `/analyze` | **62–63 s** |

**Say "about a minute", not "about thirty seconds".** The ~51 s in
`infra/DEPLOY_NOTES.md` is behind reality; I measured 62.2, 63.5 and 62.8 s,
and checked it is the instance rather than the file or the drug count (old
file, new file, one drug, six drugs — all 62–63 s). The client waits up to
180 s and shows elapsed seconds throughout, so a long wait looks like waiting,
not like a hang.

## 2. The click path

1. Open **https://pharmaguard-web.pages.dev**.
2. The banner may say the backend is waking, with a counter. Let it finish.
3. Scroll to **"No genome file? Use a sample"**. Five cards, each with **Try**
   and **Download**.
4. Press **Try** on the sample you want. It uploads and analyses in one step.
5. Results screen: one card per drug. Every card opens — CPIC recommendation,
   mechanism, patient-friendly text. **Input coverage** is below the cards.

The drug box defaults to the audited set. You do not need to type anything.

Real uploads still work: **Choose a VCF file**, list drugs, **Analyze**.

## 3. What each sample shows

All five bundled samples are **real, named public genomes** — 1000 Genomes
participants, transcribed from the Illumina/AWS DRAGEN v4.4.7 reanalysis.
Nothing is made up.

### HG02684 — the one to lead with (PJL, Punjabi in Lahore)

| Drug | Result | Why |
|---|---|---|
| **fluorouracil** | **Toxic** (critical) | DPYD `c.1905+1G>A (*2A)` on **both** copies, activity score 0.0, Poor Metaboliser |
| clopidogrel | Safe | CYP2C19 `*1/*38`, Normal |
| simvastatin | Safe | SLCO1B1 `*37/*37`, Normal |
| azathioprine | Safe | TPMT `*1/*1`, Normal |
| warfarin | Unknown | deliberate abstention — see §6 Q3 |

The line worth saying: *two independent callers and this person's family
pedigree agree on that genotype before our pipeline sees the file.* DRAGEN
calls it homozygous; the NYGC phased panel has the same sample `1|1` at
chr1:97450058, the mother `0|0` and the child `1|0` — which is what a
homozygous father requires. It is also the **only** DPYD poor metaboliser in
all 3,202 samples of the reanalysis.

### HG00525 — two findings, two unrelated drugs (CHS, Southern Han Chinese)

| Drug | Result | Why |
|---|---|---|
| **clopidogrel** | **Ineffective** (critical) | CYP2C19 `*2/*2`, Poor Metaboliser — a prodrug never activated |
| **simvastatin** | **Toxic** (critical) | SLCO1B1 `*45/*45`, Poor Function |
| azathioprine, fluorouracil | Safe | normal |

### HG02661 — the control (PJL)

Everything Safe. Use it to answer "does it ever say yes?" — it is not a system
that returns Unknown to everything.

### HG02684, variants only — **the centrepiece**

Same person as the first card, with the reference-matching rows removed.
**Every gene declined.** See section 4.

### A research VCF, as published (NA12273)

Every gene declined. This is what happens to most public research VCFs, and it
is why the other files had to be built from a different kind of source.

### Codeine, which needs a CYP2D6 diplotype supplied alongside

The web picker does not supply one, so codeine reads Unknown from a sample card
alone — correctly, because no VCF establishes CYP2D6. To show it answering you
need the optional second input, which the API takes as `cyp2d6_diplotype` and
`cyp2d6_caller`. The per-sample values are in
`demo/samples/<ID>.cyp2d6.json`.

| Sample | CYP2D6 supplied | codeine |
|---|---|---|
| NA20863 | `*4/*5`, copy number 3 | **Ineffective** — Poor Metaboliser, activity score 0.0 |
| HG01502 | `*2/*4` | Safe |
| HG00525 | `*10+*36x2/*49` | **Unknown** — PharmCAT returns Indeterminate |

NA20863 is the one to show, and it works on the live API:

```bash
curl -F "file=@demo/samples/NA20863.vcf" -F "drugs=codeine" \
     -F "cyp2d6_diplotype=*4/*5" -F "cyp2d6_caller=DRAGEN" \
     https://pharmaguard-api-baml.onrender.com/analyze
```

HG00525 is the honest one: a diplotype is in hand and the system still
declines, because PharmCAT assigns that tandem no phenotype. Every result that
rests on a supplied call is labelled *"CYP2D6 supplied by DRAGEN, not called by
PharmaGuard"* wherever it appears.

## 4. The contrast — what to say

Run **HG02684**, then **HG02684 again, variants only**.

> This is the same person. The same genome, the same pipeline, the same code.
> The only difference is the shape of the file: the second one lists only the
> positions where they differ from the reference, which is what most
> sequencing pipelines output by default.
>
> The DPYD variant is still in that second file. Nothing was hidden. What is
> gone is the evidence that anything *else* was measured — and in this field
> the reference allele is the low-risk state, so a missing position does not
> read as uncertainty. It reads as normal.
>
> So the system refuses. It would rather say "I don't know" than tell this
> person their fluorouracil is fine.

Then, if asked how much that matters: at 20% position coverage we measured
confidently-wrong calls in up to 47.8% of samples for CYP2C9 — and **every
single one** replaced a reduced-function result with a normal one. Never the
reverse.

Keep **Input coverage** on screen for the second run: 0 of 9 genes.

## 5. Offline fallback

If the venue network fails, everything runs locally. Measured **7.12 s and
7.15 s** for all six scenarios, twice, six for six.

```bash
set -a && source infra/local-dev.env && set +a
export PATH="$JAVA_HOME/bin:$PATH"
cd backend && python -m uvicorn app.main:app --port 8000 --workers 1
```

In a second terminal:

```bash
python scripts/run_demo.py
```

Six scenarios print with their labels and the S1/S2 contrast at the end. Three
of them are marked **`SYNTHETIC genotypes — authored to isolate one guard`** on
screen; say so if you use them. The real cohort is in `demo/samples/`.

To run the real samples locally instead:

```bash
curl -F "file=@demo/samples/HG02684.vcf" -F "drugs=clopidogrel,simvastatin,azathioprine,fluorouracil" http://127.0.0.1:8000/analyze
```

Verify this path on the presentation machine from a clean clone **before** the
day. It has been verified here, not there.

## 6. Three questions you will be asked

### Q1. "Has this been validated?"

No, and the distinction matters.

What exists: 400 real 1000 Genomes samples and PharmCAT's 74 adversarial test
VCFs, both re-run on 2026-11-12 with **0 mismatches** across 5,600 and 148
field comparisons. That is *fidelity* — it proves the application reports what
PharmCAT said, not that PharmCAT is right.

External truth is **n=1 in the sense that matters**. One showcase sample,
NA10847, has a GeT-RM multi-laboratory consensus, and the pipeline agrees on
all four genes it can call (CYP2C19 `*1/*1`, CYP2C9 `*1/*1`, SLCO1B1 `*5/*15`
= GeT-RM's `*15/*5`, TPMT `*1/*1`). Its DPYD it declines, and its CYP2D6 it
declines, against a known `*1/*41`.

Say plainly: *this is a research and educational prototype. It is not a medical
device and has not been clinically validated.*

### Q2. "Who reviewed the clinical content?"

**No qualified clinical expert has.** The project says so in the API response,
in the UI and in the About screen, and does not imply a review is pending.

What replaces it: the recommendation text is **verbatim CPIC**, quoted from
PharmCAT's own output and never model-authored. Explanatory wording is
pre-generated offline, checked against a provenance guard, and the response
states that automated checks verify provenance, not correctness. Adjudication
was done by the author and is recorded as such.

No patient genome ever reaches a language model.

### Q3. "Why does warfarin say Unknown? Isn't that a failure?"

No — it is the correct output, and it is declared in the registry as an
explicit abstention.

CPIC's warfarin guidance is a **dosing algorithm**, not a recommendation per
genotype, and it depends in part on ancestry and clinical factors this
application does not collect. Producing a warfarin dose from a gene call alone
would be inventing the part CPIC does not supply. The CYP2C9, VKORC1 and CYP4F2
calls are shown beside it for reference — for HG02684, CYP2C9 `*1/*3`.

The same reasoning covers **CYP2D6 from a VCF**: its star alleles depend on
copy number and hybrids with CYP2D7, which a VCF cannot express. The showcase
files carry only 2.5–9.6% of CYP2D6's required positions, so two independent
layers refuse it. A diplotype from a dedicated caller can be supplied
alongside, and every result that rests on one is labelled *"CYP2D6 supplied by
DRAGEN, not called by PharmaGuard."*

## 7. If something goes wrong

| Symptom | What it is | What to do |
|---|---|---|
| **Fewer than 6 drug cards, or a promised result missing** | **a cached build** — see below | Hard reload, or open a private window |
| Banner counts past 60 s | cold start | Let it run; the budget is 180 s |
| `SERVER_BUSY` (503) | one analysis slot, someone else is in it | Wait and retry; it is a queue, not a fault |
| Every gene Unknown on an uploaded file | almost always a variants-only or array file | That is the demo — show the coverage panel |
| codeine Unknown from a sample card | expected — no CYP2D6 call was supplied | Section 3, last subsection |
| `OUTSIDE_CALL_INVALID` (400) | the caller name is not one of the five accepted | Use `DRAGEN` exactly, with a diplotype like `*4/*5` |
| Live site unreachable | Pages or Render | Section 5, offline |

### The cached-build trap, which bit this project once already

The client is a Flutter web app with a **service worker**, so a browser that
visited the site before a deploy can keep serving the old build indefinitely —
including after a normal reload. On 2026-11-13 this made a freshly deployed fix
look like it had not shipped: the deployed `main.dart.js` provably contained
the new code, and the browser kept running the old one.

**Before presenting, on the machine you will present from**, open the site and
confirm a sample run shows **6 drug cards**. If it shows 3, you are on a cached
build. Either hard reload (Cmd+Shift+R / Ctrl+Shift+R), open a private window,
or run this in the browser console:

```js
(await navigator.serviceWorker.getRegistrations()).forEach(r => r.unregister());
(await caches.keys()).forEach(k => caches.delete(k));
location.reload();
```

A private window is the simplest insurance and costs nothing.

## 8. Do not claim

- That it is clinically validated, or a medical device.
- That a clinician reviewed the explanations.
- Any concordance figure beyond the n=1 GeT-RM corroboration in Q1.
- That the 400-sample cohort measures accuracy. It measures fidelity.
- That CYP2D6 is called from the VCF. It never is.
