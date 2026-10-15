# Pharmacogenomic Risk Prediction System (PharmaGuard)

Analyses a patient's genetic data (VCF) against a prescribed drug and returns a pharmacogenomic risk assessment, a CPIC-aligned clinical recommendation, and a plain-language explanation.

> **⚠️ Research and educational use only. This is not a medical device and is not for clinical use.** No output from this system should be used to make a prescribing decision. Consult a qualified clinician or genetic counsellor.

---

## Table of contents

- [What this project is](#what-this-project-is)
- [Key results](#key-results)
- [Architecture](#architecture)
- [Field authorship](#field-authorship)
- [The verification model](#the-verification-model)
- [Tech stack](#tech-stack)
- [Method](#method)
- [Validation results](#validation-results)
- [Input requirements](#input-requirements)
- [Quickstart](#quickstart)
- [Running the demo](#running-the-demo)
- [Repository map](#repository-map)
- [Testing and release gates](#testing-and-release-gates)
- [Current status](#current-status)
- [Limitations](#limitations)
- [Team](#team)

---

## What this project is

Adverse drug reactions are a major cause of preventable harm, and a significant fraction are attributable to genetic variation in drug-metabolising enzymes. Pharmacogenomics maps that variation to prescribing guidance. The Clinical Pharmacogenetics Implementation Consortium (CPIC) publishes the guidelines; the problem is getting from a patient's raw genomic file to a recommendation a person can act on.

This system does that end to end for **7 pharmacogenes** and **6 drugs**:

| Gene | Drug |
|---|---|
| CYP2C19 | clopidogrel |
| CYP2C9 | warfarin |
| CYP2D6 | codeine |
| SLCO1B1 | simvastatin |
| TPMT (+ NUDT15) | azathioprine |
| DPYD | fluorouracil |

This six-drug list is the audited application boundary. Four pathways can return
non-Unknown PGx guidance when their evidence requirements are met: clopidogrel,
simvastatin, azathioprine and fluorouracil. Codeine remains an explicit CYP2D6
abstention, and this project does not implement validated automated warfarin
dosing. PharmCAT may contain other annotations internally; the application does
not present them as supported guidance.

Conclusion labels: `No PGx-guided adjustment identified` · `Adjust Dosage` ·
`Toxic` · `Ineffective` · `Unknown`. The first label is bounded to the assessed
PGx evidence; it is not a statement that a drug is broadly safe.

### What makes it different

The project became two things. The first is the system above. The second — and the stronger contribution — is what happened when we measured it.

We built the system, then validated it exhaustively, and found **eight distinct ways that a pharmacogenomic pipeline silently produces false reassurance**: telling a user they are safe when the system does not actually know. Every defect found ran in the same direction. None ran the other way.

There is a structural reason, and it is the project's central claim:

> **In variant-based genomics, the reference allele is the low-risk state. Missing data is therefore not neutral — it reads as normal. Incomplete input produces false *confidence*, not uncertainty.**

The system's design is a response to that finding. It is built to decline rather than guess, and the verification architecture exists to enforce that.

---

## Key results

| Result | Value |
|---|---|
| CPIC label-mapping validation | **92/105** combinations, exhaustive (not sampled); 13 documented divergences, all erring toward caution |
| Historical integration fidelity (self-consistency, **not** accuracy) | **100.0000%** — 400 samples, 2,800 gene-pairs, 5,600 field comparisons, 0 mismatches against the same PharmCAT caller. Version-specific and blind to input adequacy |
| Independent external benchmark | **208 individuals**, 1,456 sample×gene rows, **596 evaluable truth diplotypes** across seven genes. Results are reported per gene with denominators; no pooled “accuracy” is claimed |
| PharmCAT adversarial test VCFs | **0 mismatches** across all 74 files |
| CYP2D6 negative control | **400/400** declined — never fabricated |
| Application assertions on benchmark input | **0/1,456 sample×gene rows**: polymorphic-only 1000 Genomes evidence did not meet the application contract, so the application abstained rather than infer omitted positions as reference |
| Historical complete-coverage synthetic sweep | **100% asserted, 0% discordant with its constructed truth**. This is a test-fixture result, not independent biological accuracy |
| South Asian frequency analysis, **n=601** | Historical descriptive analysis of 1000 Genomes diaspora/regional samples; not representative population prevalence and not a performance metric |
| Compatible scientific record | PharmCAT 3.4.0 and its data, rules, corpus, explanations, review state, sources, benchmark, and runtime are hash-bound in `compatible_bundle.json` |
| Backend tests | See the current phase report/test run; counts change as regressions are added |
| Client tests | 198 passing |

### The eight findings

1. **Lexical provenance checking is unsound *and* incomplete.** A term-overlap matcher passed a polarity-*reversed* claim ("Do NOT consider dose reduction" against a source saying "Consider dose reduction") while rejecting 15 of 16 faithful paraphrases.
2. **Assertion-marker rules are structurally blind to fabricated mechanisms.** A planted fabrication ("inhibited by grapefruit juice") contains no number, duration, or polarity marker, so no rule fires.
3. **Closed-vocabulary checking penalises plain language.** Applied to explanation text it produced a 57% false-positive rate (30% after POS narrowing) — flagging *genetic*, *properly*, *effectively*.
4. **Label/prose divergence.** Explanation→CPIC and label→CPIC were both verified, yet the two artifacts contradicted each other — because they trace to *different parts* of the same source. Pairwise verification against a common source does not guarantee mutual consistency.
5. **A category error between two PharmCAT structures.** `recommendationDiplotypes` is a lossy reduction for CPIC table lookup; `sourceDiplotypes` is what was actually called. Reading the former for both displayed "Normal Metabolizer" where PharmCAT said "Indeterminate" — manufacturing certainty the source explicitly withheld.
6. **A missing phenotype→label edge.** A phenotype PharmCAT declined to assert still found a CPIC table row, rendering a green *Safe* badge on fluorouracil. Fixing it as a general invariant changed **294 of 2,400** results, every one removing an unsupported confident label. A DPYD-specific patch would have left **293 of the 294** live.
7. **No-data vs indeterminate conflation, in three separate layers.** One instance silently collapsed `{Normal Function, Indeterminate}` to `{NM}`, asserted Safe, and *measured as a fix* while leaving 195 samples broken. Framing adopted: **n/a is silence; Indeterminate is testimony.**
8. **Reduced position coverage produces confident wrong calls, not declines.** A variant whose defining position is absent is invisible, and every observed position reads reference. Measured confidently-wrong rates at 20% coverage: CYP2C9 47.8%, SLCO1B1 42.9%, NUDT15 37.5%, CYP2C19 30.0%, TPMT 20.8%, DPYD 0%. Every wrong call replaced a reduced-function phenotype with a normal one, at status `DEFINITE`, with nothing signalling doubt.

A ninth, methodological: **validation tooling is itself unvalidated code.** Four separate checks in this project produced false results before being corrected. In a verification-heavy architecture, every check needs its own validation before its output carries weight.

Full write-ups: `reports/provenance_finding.md`, `reports/validation_report.md`, `reports/guard_experiment.md`, `reports/detector_sensitivity.md`.

---

## Architecture

```mermaid
flowchart TD
    A[VCF upload + drug names] --> B[Validation<br/>format, size, build]
    B --> C{Position coverage gate}
    C -->|below threshold| Z[Unknown<br/>+ coverage warning]
    C -->|passes| D[PharmCAT 3.4.0<br/>direct JAR invocation]
    D --> E[Diplotype + phenotype<br/>sourceDiplotypes]
    E --> F{Phenotype asserted?}
    F -->|no| Z
    F -->|yes| G[Deterministic CPIC<br/>label mapping]
    G --> H[Bounded PGx conclusion<br/>+ verbatim CPIC recommendation]
    H --> I[Pre-generated explanation<br/>keyed by drug + phenotype]
    I --> J[Runtime slot verification<br/>+ label/prose cross-check]
    J --> K[JSON response]
    K --> L[Flutter client<br/>web + Android/iOS]
```

**Design principles**

- **Decline over guess.** `Unknown` is a first-class, correct output — not a failure.
- **No clinical content originates in the system.** Every dosing statement is verbatim CPIC, obtained via PharmCAT.
- **No patient data reaches a third-party LLM.** Explanation candidates are generated offline. Only exact approved content/source/context identities may be served; all other cases use deterministic templates. This is an architectural guarantee, not a policy promise.
- **No application persistence.** Uploaded VCFs are bounded in memory and written only to an owned temporary directory; the child process is reaped and that directory is removed before the analysis slot is released. This does not claim control over reverse-proxy access logs, crash dumps, backups, or hosting-platform retention.

---

## Field authorship

Which layer authors which field is the core of the safety design:

| Field | Authored by | Guarantee |
|---|---|---|
| `clinical_recommendation.*` | **Verbatim CPIC**, via PharmCAT | Never model-authored. Exact-match verified. |
| `variant_rationale` | **Code**, composed at request time from the PharmCAT profile | Correct by construction — cannot disagree with the reported genotype |
| `summary`, `mechanism`, `patient_friendly` | Approved stored prose or **code-authored deterministic template** | Current stored candidates remain withheld: 19 sentences are unresolved and 36 decisions are automated rather than human |
| `recommendation_diplotype` | PharmCAT's `recommendationDiplotypes` | Provenance only — deliberately not rendered to the user |

The LLM never decides anything. It rephrases sourced text.

---

## The verification model

Five checked edges. **Each was added after a defect proved it necessary** — none was designed up front.

| Edge | Catches | Added after |
|---|---|---|
| `input → required positions` | Incomplete VCFs that would produce confident reference calls | Finding 8 |
| `explanation → CPIC` | Fabricated clinical claims in generated prose | Faithfulness guard design |
| `label → CPIC` | Mapping rules that disagree with the guideline | Finding of the substring collision |
| `explanation → label` | Prose and badge contradicting each other | Finding 4 |
| `phenotype → label` | Confident labels derived from unasserted phenotypes | Finding 6 |

Plus a **contradiction guard**: the mapping reads CPIC recommendation *text*, and is cross-checked against CPIC's *structured* booleans. Different inputs, so agreement is evidence rather than tautology.

**Automated checks are triage.** Human adjudication is a required prerequisite. `scripts/release_status.py` is the sole final decision and also requires tests plus matching approval and candidate hashes.

---

## Tech stack

**Backend**
- Python 3.11 · FastAPI · Uvicorn · Pydantic v2
- PharmCAT 3.4.0, invoked **directly via JAR** (not the `pharmcat_pipeline` wrapper, which can be silently absent)
- JDK 17 (satisfies both PharmCAT and the Android Gradle build)
- `bcftools` / `tabix` for remote region slicing of reference genomes
- spaCy — build-time only, POS tagging for the (retired) vocabulary check

**LLM layer**
- NVIDIA NIM (`integrate.api.nvidia.com/v1`), OpenAI-compatible
- Model: `meta/llama-3.1-8b-instruct`, selected by measured benchmark
- Provider abstraction supports NVIDIA / Gemini / Ollama / deterministic template
- **API key is build-time only.** The deployed path serves pre-generated explanations and requires no key.

**Client**
- Flutter (Dart) — single codebase → web + Android + iOS
- Android release APK builds under JDK 17 (49 MB). Installation on a physical device is untested

**Testing / CI**
- pytest (backend) · flutter test (client) · GitHub Actions

**Deployment (live)**
- **Web app — <https://pharmaguard-web.pages.dev>** (Cloudflare Pages)
- **API — <https://pharmaguard-api-baml.onrender.com>** (Render free, Docker)

### Performance on the free tier

Measured against the deployed service, not estimated:

| | deployed | local | why |
| --- | ---: | ---: | --- |
| **Coverage check** (`/coverage`) | **0.35 s** | ~0.3 s | Pure Python over the VCF header and positions. No JVM. |
| **Full analysis** (`/analyze`) | **~52 s** — p50 51.27 s, p95 53.56 s (n=20) | ~2.6 s | PharmCAT is a Java program on a shared free-tier CPU, ~20× slower than a laptop core |
| **Cold start** | **12.85 s** | n/a | The instance sleeps after ~15 min idle |

**The ~20× gap is the hosting, not the pipeline** — the same image, the same
commit, the same inputs produce byte-identical results in 2.6 s locally. The
client states the cost while you wait rather than hiding it behind a spinner,
and the coverage census gives real computed feedback in under a second before
the long call starts.

One analysis runs at a time (two concurrent PharmCAT invocations measured 594 MB
against a 512 MB instance), so a second visitor is queued and a third gets an
honest `503`. Detail in
[`reports/deployment_verification.md`](reports/deployment_verification.md).

---

## Method

### Building

Built in phases, each closed by a report-back and review before the next began. Explanations were pre-generated offline rather than at request time, because the case space is enumerable — 28 `(drug, phenotype)` combinations, of which **20 are reachable**. The 8 unreachable ones were *not* authored, because authoring them would mean inventing coverage the system cannot produce.

### Validating

Where the space is enumerable, validation is **exhaustive rather than sampled**. The label mapping is a pure function of `(gene, phenotype, drug)`, so all 105 CPIC combinations were checked — complete coverage, no sampling error.

Methodological practices that materially changed outcomes:

- **Pre-committed acceptance thresholds.** Written down *before* tuning. This retired the vocabulary check at 30% false positives rather than letting it be tuned to pass, and its zero-regression condition caught two over-broad fixes before they shipped.
- **Sabotage tests.** Every safety check has a test that fails if the check is disabled or weakened.
- **Independent expectation tables.** The mapping reads CPIC recommendation *text*; the expectation table derives from CPIC *structured booleans*. Different inputs keep the validation non-tautological.
- **Directive vs descriptive.** A documented principle after three defects shared one shape — matching text that *describes* dosing rather than *directs* it. It immediately predicted its own next instance.

### Adjudicating

Clinical claims in the stored explanation candidates are compared with their sources and recorded as accept / edit / reject with a rationale. This is under way, not finished: 19 sentences remain unresolved and 36 decisions are automated. Consequently none of the 20 stored entries is approved for serving; the deterministic fallback is used. This process verifies **provenance**, not clinical approval. No qualified clinical reviewer was available, and that remains an explicit limitation.

---

## Validation results

### Label mapping — exhaustive

105 combinations. Three defects found and fixed, taking agreement from 60 → 92 with **zero regressions**:

1. A substring collision returned `Safe` for 16 azathioprine rows where CPIC requires a 30–80% dose reduction.
2. Two clopidogrel rows were labelled where CPIC says "No recommendation" — a provenance violation.
3. Three simvastatin rows returned `Unknown` where CPIC says prescribe an alternative — losing a warning.

13 remaining divergences are documented and accepted, all erring toward caution.

**Toxic vs Ineffective policy:** *Toxic* = harm from drug **exposure**; *Ineffective* = therapeutic **failure**. The test is whether harm comes from the drug acting or from it failing to act.

### Integration fidelity

Comparing our pipeline's output against PharmCAT's direct output is self-referential, so it needs no truth labels and can run at scale.

- 400 samples · 2,800 gene-pairs · 5,600 field comparisons · **0 mismatches**
- PharmCAT's own 74 adversarial test VCFs · **0 mismatches**

This demonstrates *integration fidelity* — that the pipeline does not corrupt PharmCAT's calls. It is not independent validation of PharmCAT's science, which is established in its own literature.

**And it is blind to input adequacy by construction.** Two systems reading the same input can agree perfectly on an answer neither was in a position to give. Across these 400 samples the slice carried 8 of DPYD's 28 decision-critical positions; PharmCAT read those 8 and returned Normal Metabolizer, and so did we. Agreement measures whether the second system reproduces the first — it says nothing about whether the first had enough evidence to be asked.

The original Phase 6 exercise had only one overlapping sample and remains preserved as a version-specific historical report. The current independent benchmark uses the later CDC consolidated GeT-RM/PGx consensus workbook and a deterministic 1000 Genomes overlap: **208 individuals**, 1,456 sample×gene rows, and 596 evaluable truth diplotypes across seven genes. See [`reports/external_analytical_benchmark.md`](reports/external_analytical_benchmark.md). Results are reported per gene because gene observations repeat within individuals and sparse genes must not be hidden in one pooled number.

### Coverage sensitivity

Confidently-wrong rate (asserted a phenotype disagreeing with complete-coverage truth), 120 samples, 12 subsets per level:

| Gene | 100% | 80% | 60% | 40% | 20% |
|---|---|---|---|---|---|
| CYP2C9 | 0.0% | 17.4% | 28.6% | 33.3% | 47.8% |
| NUDT15 | 0.0% | 0.0% | 25.0% | 29.2% | 37.5% |
| SLCO1B1 | 0.0% | 0.0% | 15.0% | 19.0% | 42.9% |
| TPMT | 0.0% | 0.0% | 8.3% | 20.8% | 20.8% |
| CYP2C19 | 0.0% | 0.0% | 4.3% | 12.5% | 30.0% |
| DPYD | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |

These are an **upper bound**: the sweep dropped positions at random, whereas real filtering (e.g. 1000 Genomes) drops *monomorphic* positions, where reference is the correct call.

**A monomorphic-aware relaxation of the gate was considered and rejected.** It would assert "this position is usually reference, therefore this patient is reference" — the exact bias the gate exists to prevent, with a probability attached. It fails worst for rare severe variants: DPYD deficiency alleles are rare (hence monomorphic in a panel), and missing one causes fatal fluorouracil toxicity.

### Independent external benchmark

The frozen current benchmark intersects the CDC consolidated consensus workbook with 1000 Genomes high-coverage data and contains **208 individuals**. Across seven genes it has **596 evaluable independent truth diplotypes**; exact and candidate-compatible concordance, abstention, assertion coverage, conditional accuracy, and Wilson intervals are reported separately by gene with explicit denominators.

Layer A measures the pinned PharmCAT call against consensus truth. Layer B measures the application after its evidence gate. All 1,456 benchmark sample×gene inputs are polymorphic-only slices and therefore ineligible under the application contract; Layer B abstains throughout. This is an analytically useful negative result, not evidence of clinical utility and not a reason to weaken the evidence gate.

The original n=1 result is retained in `reports/validation_report.md` as historical evidence only; it is superseded for current external-benchmark claims. In that historical case, the CYP2C9 divergence was conservative: consensus asserted `*1/*2` while the application declined an ambiguous call.

---

## Input requirements

**This section is the most important operational content in this README.**

A conforming VCF must contain **all 306 defining positions with explicit genotypes, including homozygous-reference calls.**

A **variants-only VCF** — which most pipelines emit by default — is indistinguishable from one where those positions were never assayed. This is the single most likely way a user gets a wrong answer, and the system detects and warns about it specifically.

Minimum coverage per gene, derived from the sensitivity measurement:

| Gene | Minimum coverage |
|---|---|
| CYP2C19 | 100% |
| CYP2C9 | 100% |
| SLCO1B1 | 100% |
| TPMT | 80% |
| NUDT15 | 80% |
| DPYD | 20% |

Below threshold, the system returns `Unknown` with the coverage achieved versus required — it does not guess.

**File size:** a conforming PGx VCF is around 25 KB (463 rows, all seven genes). A real 1000 Genomes slice restricted to the same positions is larger — roughly 194 KB for 169 rows — because research-format records carry long INFO fields. Either way the 5 MB upload cap leaves ample headroom, and only rejects whole-region research files (~28 MB raw slices).

Full detail: `docs/input_requirements.md`.

---

## Quickstart

**Prerequisites:** Python 3.11, JDK 17, Flutter SDK, `bcftools`, PharmCAT 3.4.0 JAR.

> JDK 17 is required. Gradle rejects JDK 25, and JDK 17 also runs PharmCAT — one version serves both.

```bash
# Backend
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# PharmCAT is a Java app, not a pip package — fetch the pinned 3.4.0 JAR:
python ../scripts/fetch_reference_data.py --fetch-tools
# ...or point at your own copy: export PHARMCAT_JAR=/path/to/pharmcat-3.4.0-all.jar
# The identity checks also need the locked cohort VCF. This fetches every pinned
# binary and refuses any whose SHA-256 differs from the manifests. CI runs it too:
python ../scripts/fetch_pinned_artifacts.py

cp ../infra/local-dev.env.example ../infra/local-dev.env   # then edit
set -a && source ../infra/local-dev.env && set +a          # the app reads env, not the file
uvicorn app.main:app --reload --port 8000
```

The backend prints the URL it actually bound, plus which PharmCAT strategy resolved:

```
[startup] pharmcat=jar via java -jar .../pharmcat-3.4.0-all.jar
[startup] listening on http://127.0.0.1:8000  (docs at /docs)
```

> Local config lives in `infra/local-dev.env`, **not** `backend/.env` — a dotfile inside the deployable directory is a leak risk and startup refuses it.
>
> `CORS_ALLOWED_ORIGINS` must be set. An empty allowlist with hosting markers present is a deliberate hard failure.

```bash
# Client
cd app
flutter pub get
flutter run -d chrome        # web
flutter build apk --release  # Android
```

**No API key is required to run the system.** Explanations are pre-generated and shipped. A key is only needed to *regenerate* them.

---

## Running the demo

```bash
python scripts/run_demo.py            # all scenarios
python scripts/run_demo.py --slow     # pause between scenarios for narration
python scripts/run_demo.py --scenario 1
```

Six scenarios, ~7 seconds of compute. The centrepiece is **S1 vs S2**:

```
                       complete coverage         variants-only
  PharmCAT called      *2/*2                     *2/*2            (identical)
  phenotype            PM                        Unknown
  PGx CONCLUSION       Ineffective               Unknown
  coverage             35/35 = 100.0%            4/35 = 11.4%
```

The API still carries the historical `confidence_score` and `severity` fields
for compatibility. They are deprecated: the score is a deterministic pipeline
status lookup, not a calibrated probability, and the severity value is not a
validated clinical severity assessment. Neither is shown or included in the
user export.

Same patient. Same genotype call from PharmCAT. Different file *shape*.

The system declines an answer that happens to be **correct** — because the file cannot demonstrate that it is correct. Accepting it would mean also accepting the 47.8% of CYP2C9 cases at low coverage where the same reference-fill produces a confidently *wrong* normal-metaboliser call. At the input, the two are indistinguishable.

Presenter runbook: `docs/DEMO_SCRIPT.md`.

---

## Repository map

| Path | Contents |
|---|---|
| `backend/` | FastAPI service, CPIC mapping, coverage gate, explanation serving |
| `backend/app/data/` | `label_mapping.yaml`, `explanations.json`, `case_matrix.json` |
| `app/` | Flutter client (web + mobile) |
| `rag-corpus/` | Mechanism corpus — biological background, cited and dated |
| `scripts/` | CLI tooling: demo, validation, generation, adjudication, gates |
| `reports/` | **Primary results.** Validation, provenance findings, guard experiment, benchmarks |
| `docs/` | Input requirements, demo script, onboarding |
| `test-data/` | Synthetic and reference VCFs, demo files |
| `infra/` | Dockerfile, deploy notes, PharmCAT notes, local config |
| `PROJECT_STATUS.md` | Live status, open items, limitations register |

**Start with `reports/` if you want the findings, `docs/ONBOARDING.md` if you want to contribute.**

---

## Testing and release gates

```bash
cd backend && pytest          # backend suite
cd app && flutter test        # client suite
```

Counts are in [Key results](#key-results); they are a snapshot of the last run,
not a target.

Release prerequisites, each exiting non-zero on failure and combined only by
`scripts/release_status.py`:

| Gate | Checks |
|---|---|
| Mapping validation | All 105 CPIC combinations |
| Label/prose cross-check | Every shipped entry |
| Detector sensitivity | Planted violations still caught |
| Coverage gate tests | 31 tests incl. sabotage cases |
| Provenance verification | Clinical sentences traceable |
| Human adjudication | Every stored sentence decided by a named person — **red** |
| Approval identity | Exact content, source, drug/gene/phenotype/risk context, and store hashes |
| Authoritative release status | All required tests plus the exact tested candidate hash |

**Invariants contributors must not break:**

1. Never assert a phenotype the caller withheld.
2. Never emit clinical text not traceable to CPIC.
3. Never tune a check until it stops firing — pre-commit the threshold instead.

---

## Current status

| Phase | State |
|---|---|
| 1 — Backend/client seam | ✅ Complete |
| 2 — PharmCAT + CPIC mapping | ✅ Complete |
| 3 — Grounded explanations + guard | ✅ Complete |
| 4 — Deployment code | ✅ Complete |
| 5A — Real LLM generation | ⚠️ Generated; **19 sentences escalated to a human and not decided** |
| 5B — Warfarin regressor + SHAP | ⏳ Optional |
| 6 — Validation | ✅ Complete |
| 7 — Adjudication, docs, demo | ⚠️ Docs and demo complete; adjudication deliberately left open |
| 8 — Deployment | ✅ **Live** — backend on Render, web on Cloudflare Pages; S1–S6 verified against the deployed URLs |

### The adjudication prerequisite is incomplete, and that is the honest state

179 claim sentences. **160 adjudicated** — 124 by a person, 36 by automation
against a quoted source passage. **19 escalated to a human and left undecided.**
The authoritative content gate exits non-zero. Unapproved stored prose is not
served; requests receive the deterministic fallback instead.

**This is a decision, not an unfinished task.** The 19 are clinical assertions —
whether a rapid metaboliser carries a higher bleeding risk, whether a normal
SLCO1B1 result leaves the usual muscle-toxicity risk. `auto_adjudicate.py` looked
at each and declined, because each asserts something its aligned passage does not
plainly support. Deciding them requires clinical judgement, and this project
records, in `scripts/adjudication_status.py`'s own output:

```
clinical expert      NOT_OBTAINED   (no qualified reviewer on this project)
```

Clearing the prerequisite without that reviewer would mean signing a clinical review that
did not happen. A green gate would then mean less than the red one does — it
would assert review, where red asserts only that unreviewed prose exists and is
withheld. The 19 sentences are listed in
[`reports/escalation_list.md`](reports/escalation_list.md), each with its source
passage and the specific tension.

Everything adjudication can decide without a clinician, it has decided. What remains
is what a clinician is for.

```bash
python scripts/adjudicate.py --escalated-only --adjudicator "<your real name>"
```

---

## Limitations

Stated plainly, because declared limitations cost less than concealed ones.

- **36 of 179 clinical sentences were adjudicated by automated alignment, not by a person.** Each was matched to a quoted passage in the mechanism corpus and accepted only where it added no causal step, quantity, timeline, comparative or scope claim. A further 19 were escalated for human review and remain outstanding; 124 were previously decided by a person. Full human adjudication of the remainder is outstanding. Automation is triage, not a substitute for human review: the detail report marks this state `provisional`, the sole authoritative release status remains not ready, and all 20 stored entries currently fall back rather than serve as approved prose.
- **No clinical expert review.** No qualified clinical reviewer was available. The system compensates by generating no clinical content of its own; every clinical statement is provenance-verified to a CPIC source. This is a declared limitation, not a solved problem.
- **The current independent benchmark has 208 individuals but no application-eligible inputs.** Its 596 evaluable truth diplotypes support gene-specific upstream-caller comparisons. They do not establish application accuracy on inputs satisfying the evidence contract, because Layer B correctly abstained on every polymorphic-only slice.
- **CYP2D6 is not called from VCF.** Copy-number and structural variation cannot be resolved from an unphased VCF. The system returns `Unknown` with an explicit warning and never fabricates a call.
- **Historical usability and complete-coverage numbers are synthetic/self-consistency results.** They characterize particular frozen fixtures, not clinical accuracy or population performance. The current independent benchmark and its explicit denominators are the authoritative analytical report.
- **A coverage percentage is a proxy, and DPYD is no longer exempt from identity.** Position *identity* matters, not count: DPYD used to clear a 20% threshold at 37.3% coverage with 0% measured error while CYP2C9 failed at 19.3%. That 0% came from a sweep over a cohort where DPYD's reduced-function variants are rare, so it could not detect the failure the threshold exists to exclude — absence of observed error is not absence of possible error. Every gene now additionally requires each **decision-critical position**, derived mechanically from PharmCAT's own function assignments; DPYD carries 8 of 28 and is **gated**. Percentages remain in place as a second, weaker condition; replacing them entirely with function-weighted coverage is still future work.
- **`Indeterminate` and `No Result` share an enum value.** The falsehood was removed from user-facing prose and the distinction is preserved in `quality_metrics.warnings`, but a client cannot machine-check it. Deferred deliberately: clinical action is identical in both states.
- **No application result history.** The application does not store results and they vanish on reload. Static/default explanation mode makes no outbound explanation call. Host access logs, crash handling, backups, and platform-level retention remain deployment responsibilities rather than a universal zero-retention promise.
- **Deployed on free tiers, with the costs that implies.** An analysis takes
  ~52 s on Render's free CPU (~20× the local 2.6 s), and the instance sleeps
  after ~15 minutes idle so the first visitor pays a cold start. Neither is a
  property of the pipeline; both are what the hosting costs nothing.
- **One analysis runs at a time.** Two concurrent PharmCAT invocations measured
  594 MB against a 512 MB instance, so a second visitor is queued and a third
  is refused with an honest `503 SERVER_BUSY` rather than the container being
  OOM-killed for everyone.
- **iOS App Store distribution out of scope** — requires the paid Apple Developer Program. Simulator and local device only.

---

## Team

Final-year project, Department of Computer Science & Engineering (Data Science)
Sai Vidya Institute of Technology, Bengaluru · Visvesvaraya Technological University

- Bhuvan T
- Anupam M Hegde
- Gangadhar V
- Niteesh Seetaram Naik

---

## Acknowledgements and licensing

- **PharmCAT** (MPL-2.0) — diplotype calling and CPIC recommendation retrieval
- **CPIC / ClinPGx** — clinical guidelines; all clinical content originates here
- **PharmVar** — star allele definitions
- **1000 Genomes Project** and **CDC GeT-RM** — reference genomic data
- **NVIDIA NIM** — LLM inference
- **Flutter**, **FastAPI**, and the wider open-source ecosystem

See `LICENSE` for this project's terms and third-party attributions.

---

*Built as a final-year engineering project. It is a working system and a study of how such systems fail. Both halves matter — but the second one more.*
