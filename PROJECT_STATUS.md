# PharmaGuard — Project Status Audit

**Audit date:** 2026-07-23
**Fix pass:** 2026-07-23 (same day, after `git init` — baseline commit `6d758cc`)
**Phase 5A:** 2026-07-23 — LLM generation *tooling* delivered. **The generation
run itself has not been executed**, so `explanations.json` is still template
text. See "Phase 5A" below for exactly what is and is not done.
**Mode:** the audit itself was read-only. A subsequent fix pass has since
resolved the six defects listed under "Fixed" below; everything else in this
document still describes the current state.
**Method:** every claim below is backed by a command run against the working
tree or a cited file path. Anything not directly verified is marked
**UNVERIFIED**.

---

## Executive summary

The backend is in genuinely good shape: the clinical pipeline is real and
traceable, and the deployed path needs no secrets. The audit found **three
defects that would each break a demo**, all in the Phase 4 deployment layer,
none covered by the then-existing 249 tests. All three have since been fixed
(**333 tests now pass**, 20 skipped — see A2):

| # | Defect | Impact | Status |
| --- | --- | --- | --- |
| 🔴 **P0** | Android `MainActivity` package mismatch — the built APK's launcher target does not exist in its own dex | **The release APK installs and crashes instantly** | ✅ **FIXED** |
| 🟠 **P1** | `docker-compose.yml` mounts `/opt/pharmaguard/*` but the Dockerfile's WORKDIR is `/home/user/app` | `docker compose up` silently runs baked-in code | ✅ **FIXED** |
| 🟠 **P1** | `CORS_ALLOWED_ORIGINS` documented but set nowhere; default empty | Deployed site loads, then **every analysis fails CORS** | ✅ **FIXED** |

The repo **is now a git repository** (baseline `6d758cc`). Nothing is deployed
yet, so no workflow has run.

---

## ✅ Fixed in the 2026-07-23 fix pass

Six defects resolved, each with a regression test that was **verified to fail
against the original bug** before being accepted. Backend suite: **249 → 305
passing**.

| ID | Defect | Fix | Regression test |
| --- | --- | --- | --- |
| **P0-1** | APK launcher target absent from its own dex | Canonical id `com.pharmaguard.pharmaguard` across `namespace`, `applicationId`, Kotlin package. Chosen over `com.pharmaguard.app` because it needed 2 line edits instead of a cross-directory file move, **and** it aligns Android with iOS's existing `PRODUCT_BUNDLE_IDENTIFIER` for free | `test_android_identity.py` (5) — sabotage-verified: reverting the namespace fails 2 tests |
| **P0-2** | Dead `stub_analyzer.py` with fabricated clinical values | Deleted (417 lines). Stale docstrings in `models.py` and `main.dart` rewritten to state real provenance | Repo-wide sweep clean; every dose string in tests traced to a PharmCAT fixture |
| **P1-3** | CORS unset in every deploy path | Set in compose, documented in Dockerfile, plus `assert_cors_configured()` which **refuses to start** a hosted instance with an empty allowlist | `test_deployment.py::TestCorsFailsLoudWhenMisconfigured` (11), `test_infra_config.py` (9) |
| **P1-4** | compose mounts missed the WORKDIR | Realigned to `/home/user/app/*` | `test_infra_config.py::TestComposeMountsMatchWorkdir` |
| **P1-5** | `sample1/2.vcf` broke the demo | Deleted; three demo-worthy samples retained | `test_sample_vcfs.py` (22) — sabotage-verified |
| **P1-6** | Runtime slot values unguarded | `slot_verifier.py` cross-checks injected values against the response's own profile; mismatch demotes to template | `test_slot_verifier.py` (12) |

### What the fix pass found that the audit missed

1. **`sample1/2.vcf` were worse than reported.** The audit said "all-Unknown".
   In fact PharmCAT writes *no report at all* for a file that sparse, so
   `/analyze` returns **503 PHARMCAT_UNAVAILABLE** — a server error, not a
   degraded result. A demo user picking the first file in the list got a 500-class
   failure.
2. **iOS already used `com.pharmaguard.pharmaguard`** in 6 places in
   `project.pbxproj`. The audit only examined the Android side, so it did not
   see that choosing `com.pharmaguard.app` would have left the two platforms
   permanently disagreeing.
3. **`test-data/README.md` had dangling references** to the deleted samples,
   caught by the new doc-reference test rather than by eye.

---

## Phase 5B — provider abstraction + NVIDIA (2026-07-24)

### Status: abstraction complete; benchmark run; **template ships (LLM prose fails the provenance gate)**

The Gemini key hit its daily free-tier wall (`RESOURCE_EXHAUSTED`) during the
5A run. Rather than wait for a reset, the LLM layer was made **provider-agnostic**
so a quota wall on one vendor no longer strands the project.

| Delivered | Detail |
| --- | --- |
| **Provider package** | `backend/app/explanation/providers/`: one interface, four implementations — `nvidia` (NIM, OpenAI-compatible), `gemini` (google-genai), `ollama` (local, zero-quota), `template` (deterministic). Selected by `LLM_PROVIDER` / `LLM_MODEL` |
| **Typed errors** | `QuotaExhausted` / `RateLimited` / `ModelUnavailable` / `InvalidResponse`, normalised across vendors. **NVIDIA 402 → QuotaExhausted** with a distinct message; all subclass `LlmUnavailableError` so existing catches still work |
| **JSON negotiation** | tries `response_format` then prompt-enforced; strips `<think>…</think>`, unwraps fences; records `json_mode` per entry |
| **Model discovery** | `list_models.py --provider nvidia` queries `/v1/models` and probes JSON support. Credit-free status is **not** in the API — the script says so and points at the catalogue rather than guessing |
| **Model benchmark** | `benchmark_models.py` runs candidates on the same 3 cases (Safe/Adjust/Toxic), ranks by guard > provenance > JSON. This *is* the model-selection experiment for the report |
| **Privacy property** | pinned by `test_privacy.py`: no patient genome reaches any provider at build or run time (see below) |
| **Tests** | +30: `test_providers.py` (24 — selection, error mapping, JSON recovery, quota→template) and `test_privacy.py` (6). Deployed path verified to import cleanly with **no SDK installed** |

### Benchmark result (2026-07-24) — the decisive finding

The NVIDIA key was added and discovery + benchmark **did run**. The result
settled the generation question on evidence, and it is the most important
outcome of the whole LLM effort.

| Model | JSON | Guard | **Provenance** | Latency | Served |
| --- | ---: | ---: | ---: | ---: | :---: |
| `meta/llama-3.1-8b-instruct` | 100% | 100% | **0%** | 2.4s | yes |
| `meta/llama-4-maverick-17b-128e` | 100% | 67% | **0%** | 2.5s | yes |
| `microsoft/phi-3.5-moe-instruct` | — | — | — | — | no (404) |
| `ibm/granite-3.0-8b-instruct` | — | — | — | — | no (404) |
| `mistralai/mixtral-8x7b-instruct` | — | — | — | — | no (500) |

**Every served model passes the entity guard and fails sentence-level
provenance.** The models write fluent, plausible clinical prose that elaborates
beyond the CPIC source — timeframes ("may take a few weeks"), generic advice
("your doctor will adjust the dose"), reworded mechanism. The guard misses this
(no fabricated dose/gene/allele *entity*); provenance catches it (the *claim*
does not trace). A second run with an aggressive "reuse the source's words, add
nothing" instruction still scored **guard 3/3, provenance 0/3** — the untraced
words were unavoidable plain-language terms (`doctor`, `body`, `lower`, `blood`,
`count`) that patient communication needs but clinical guidelines do not
contain.

**Conclusion — the template store ships; no LLM generation was run.** This is
not a fallback, it is the evidence-backed answer:

- A "every clinical word must trace" gate is fundamentally incompatible with
  free-form generative paraphrasing. No prompt or model tuning closes it.
- The template passes provenance 100% precisely because it is assembled from the
  declared CPIC→label paraphrases (`label_paraphrases.yaml`) — pre-approved
  plain-language mappings, which is exactly what provenance verification
  requires.
- So the LLM experiment **validates the pre-generation / template / declared-
  paraphrase architecture**: real models were tested against the integrity gate
  under two prompt regimes and it rejected fluent-but-ungrounded prose every
  time.

Raw outputs and per-sentence failures: `reports/model_benchmark.md`.

**Still not run:** the full 20-case generation and the guard-experiment rerun on
NVIDIA — deliberately, because the benchmark showed LLM prose cannot clear the
release gate, so generating it would only produce a red `verify_provenance`.
`explanations.json` remains the 5A template store (provenance-verified, 34/34).
Suite: 398 passed, 10 skipped.

### No patient genome reaches any LLM provider

A real architectural property, now that a model is genuinely in the loop:

- **Build time** — pregeneration sends a generic `(gene, phenotype, drug)` triple
  plus published CPIC text; patient fields are placeholders. There is no patient.
- **Run time** — the deployed service is static: it looks up by `(drug, phenotype)`
  and fills slots locally, importing no provider and opening no socket.

`test_privacy.py` checks every case's actual model payload carries no diplotype,
rsID, variant or activity score, and that the static path reaches no provider
even with all providers poisoned to raise on contact.

---

## Phase 5A — real LLM generation (2026-07-23)

### Status: tooling complete, **run not executed**

Phase 5A set out to replace template explanations with real model output and to
enforce the faithfulness guard against text this codebase did not write. The
**tooling to do that is finished and tested. The generation run has not been
performed**, and no API quota has been spent on generation.

This distinction is the whole point of the phase, so it is stated plainly rather
than buried:

| Claim | Status |
| --- | --- |
| Generation tooling exists, is tested, and is documented | ✅ **Yes** |
| A real model has produced explanation prose for this project | ⛔ **No** |
| The guard has been run against real model output | ⛔ **No** |
| `explanations.json` contains LLM text | ⛔ **No** — 20/20 entries are `generator: "template"`, `model: ""` |

**Verified, not assumed:** `git diff --quiet HEAD -- backend/app/data/explanations.json`
passes; the file is byte-identical to commit `7c69e85`. Its `generated_at` is
`2026-07-23T04:10:28Z` — the Phase 3 template run. No entry carries a
`prompt_hash` or a `fallback` key. `logs/guard_events.jsonl`,
`reports/guard_experiment.md` and `reports/guard_experiment_raw.json` do not
exist.

### The real numbers

| Metric | Value |
| --- | --- |
| Guard pass rate on real model output | **Not measured — no generations exist** |
| Fallback count | **Not measured — no generations exist** |
| Guard evaluations logged | **0** (`logs/guard_events.jsonl` absent) |
| API requests spent on generation | **0** |
| Cases enumerated / reachable / unreachable | **28 / 20 / 8** |
| Explanation entries authored | 20 — exactly the reachable set, no more |
| Entries human-reviewed | **0** |

A guard pass rate could be computed and stated here in one line. It would be
fabricated. In a project whose central claim is that it does not invent clinical
content, inventing its own validation statistics would be the most damaging
possible failure — so the cells above say "not measured" and will keep saying so
until a run produces the artifacts.

### What was delivered

| Area | Detail |
| --- | --- |
| **Reachability** | `enumerate_cases.py` derives producible cases from PharmCAT's own `org/pharmgkb/pharmcat/phenotype/<GENE>.json`. **28 enumerated, 20 reachable, 8 not** — the naive 6×6=36 product is fiction |
| **Generation** | `pregenerate_explanations.py`: guard → retry-once-stricter → template fallback, atomic write after every case, `--resume` keyed on `drug:phenotype` |
| **Adversarial validation** | `guard_experiment.py`: 4 arms (grounded / stripped / corrupted / coaxed), with a hard assertion that its output path is nowhere near `explanations.json` |
| **Review workflow** | `author_read.py` (records a read, never an approval), `review_status.py` (provenance and reading reported separately), `export_for_reading.py` (all 20 in one document) |
| **Safety plumbing** | `preflight.py` (10 checks, gates a run on exit code), `scrub()` applied at every exception-render site, `list_models.py` so no model id is ever written from memory |
| **Documentation** | `scripts/README.md` rewritten — clean-checkout→reviewed sequence, key hygiene and rotation, throttle rationale, resume semantics, reachability table |
| **Tests** | +44: `test_phase5a_tooling.py` (28, all run today) and `test_guard_real_outputs.py` (16, skip until a run exists) |

### Corrections to earlier claims in this document

Phase 5A's reachability analysis **falsifies two figures** stated in the original
audit and in the paste-back summary below:

1. **"16 of 36 explanation cases fall back to template text" is wrong.** 36 was
   the naive drug × phenotype product. The real enumeration is 28, of which 20
   are reachable — and **all 20 are authored**. No reachable case falls back.
2. **"Author the 16 missing explanations" (decision D3) is not a real choice.**
   The 8 unreachable cases cannot be authored without fabrication: CYP2D6 is not
   callable from an unphased VCF (4 cases), CPIC's warfarin guidance is a dosing
   algorithm with no per-phenotype text (3), and SLCO1B1 has no increased-function
   row (1). D3 is resolved by the evidence, not by a judgement call.

### `test_guard_real_outputs.py` — why 16 tests currently skip

These are the tests that consume real captured output. Each skips with the exact
command that produces its input rather than passing vacuously — a green test that
has never seen data would report the guard as validated against real output when
it has never seen any.

They were verified to work: run against synthetic artifacts of the correct shape,
11 execute and pass, and a mutation that makes the guard accept every fabrication
correctly **fails** `test_the_adversarial_arms_were_caught`. The five
store-dependent tests were separately exercised against all 20 existing entries
(context reconstruction → guard re-check: 20/20 pass), so they will run rather
than error the moment real entries land.

### To finish Phase 5A

Needs the user's approval to spend quota, per the standing instruction to ask
first. Expected cost at the default 10 RPM throttle:

```bash
python scripts/preflight.py                                   # free, gates the rest
python scripts/pregenerate_explanations.py --dry-run          # free
python scripts/pregenerate_explanations.py --resume           # 20-40 requests, 2-4 min
python scripts/guard_experiment.py                            # 12 requests, ~1.5 min
python scripts/generation_report.py                           # free — produces the real numbers
```

Then this section's "not measured" cells become measurements, the 16 skipped
tests run, and `verify_provenance.py` gates the result.

---

## Accepted limitation: no clinical reviewer

**Declared 2026-07-23. This is a condition of the project, not an open action.**

There is no qualified clinical expert on this project and there will not be one.
The planned faculty sign-off — assumed throughout Phases 1–4 and listed as
pending work in the original audit — is not going to happen.

Recording it as permanently pending would have been the dishonest option: it
reads as "not done yet" when the truth is "not obtainable". Every artifact that
implied a review was outstanding has been changed to say what is actually true.

### What replaces it

Not a weaker review. A narrower claim, and a checkable one:

> **The system asserts no clinical content of its own.** Every sentence making a
> clinical claim traces, word for word, to a CPIC recommendation as PharmCAT
> emitted it, or to a mechanism document carrying a citation and a retrieval date.

`scripts/verify_provenance.py` enforces this and exits non-zero on any failure.
CI runs it on every push. Current state: **34 of 34 clinical-claim sentences
verified (100%)**, 37 of 37 mechanism sentences traced.

| Class | Verified | Traces to | Gates release |
| --- | ---: | --- | :---: |
| `CLINICAL` | **0/0** | CPIC recommendation text, verbatim from PharmCAT | ✅ |
| `LABEL_PARAPHRASE` | 20/20 | `label_paraphrases.yaml` → the label a named `label_mapping.yaml` rule derived from CPIC text | ✅ |
| `PHENOTYPE_PARAPHRASE` | 14/14 | `label_paraphrases.yaml` → the PharmCAT phenotype call | ✅ |
| `MECHANISM` | 37/37 | the cited, dated corpus file for that gene-drug pair | ➖ reported |
| `PROCESS` | 40 | describes this analysis, not a clinical claim | ➖ exempt |
| `FRAMING` | 58 | carries no clinical claim | ➖ exempt, listed in the report |

**`CLINICAL` is 0/0, and that is the intended design rather than a coverage
gap.** The explanation fields never restate a CPIC recommendation in their own
words — CPIC's text is served verbatim in its own response field, where it needs
no paraphrase and can be read directly. What the prose does instead is restate
the *derived label* and the *phenotype*, which is why every clinical claim in
the shipped store falls into the two paraphrase classes.

The consequence worth stating: the strict CPIC-tracing path is currently
exercised only by tests, not by shipped text. Those tests plant unsourced
clinical sentences — an invented `25 mg` dose, an invented risk claim — and
confirm the gate rejects them (`test_captured_outputs.py`). If a future
generation run produces prose that does quote CPIC directly, that path
activates with no further work.

### The bound, stated precisely

| | |
| --- | --- |
| ✅ **Verified means** | every clinical word in the sentence appears in a cited source |
| ❌ **Verified does NOT mean** | a clinician has agreed the sentence is correct |

Lexical tracing cannot detect a sentence assembled from source words that is
still wrong — reversed causality, a dropped hedge, a recommendation attached to
the wrong phenotype. *"Reduced CYP2C19 activity makes the drug accumulate"* is
backwards for a prodrug, and every word of it traces. Catching that needs a
clinician. **Nothing in this project catches it.**

The strongest remaining check is the author reading all 20 entries
(`export_for_reading.py`, then `author_read.py`). That is recorded as a read,
never as an approval — the CLI has no action that records clinical approval, and
`clinical_expert_review` is not writable from any script here.

### How the gap is disclosed

| Where | What it says |
| --- | --- |
| Every API response | `disclaimer` names the absence and the guarantee that replaces it |
| Every API response | `quality_metrics.warnings` states it in full |
| Client UI | persistent banner, text pinned identical to the API's by a test |
| `README.md` | limitations table |
| `reports/provenance_report.md` | the percentage cannot be quoted without the caveat — they share a paragraph |
| CI | the `honesty` job fails if any entry claims a clinical review, or any doc implies one is pending |

### Structural changes made

| Before | After |
| --- | --- |
| `reviewed_by` / `reviewed_at` | a `review` block distinguishing what a machine checked, what the author read, and the clinical review that was **never obtained** |
| `review.py` — approve / reject | `author_read.py` — read / flag concern. No approve action exists |
| `export_for_review.py` — signature block per entry | `export_for_reading.py` — no signature line. A blank approval box reads as awaiting a signature, not as awaiting a reviewer who is never coming |
| `review_status.py` — one "reviewed" number | provenance and author-read reported separately. Collapsing them made the weak signal look like the strong one |
| API warning: *"not yet been reviewed by the faculty guide"* | names the absence outright, plus what was done instead |

---

## Phase 5A — status: **NOT COMPLETE** (one gate outstanding)

Everything except the final human adjudication pass is done. The release gate is
red, and the phase is not closed while it is.

### Final numbers

| | |
| --- | ---: |
| Reachable cases generated | **20 / 20** |
| Model | `meta/llama-3.1-8b-instruct` (NVIDIA NIM) |
| Guard pass rate | **20 / 20** |
| Generation retries / fallbacks | **0 / 0** |
| JSON mode | `response_format`, 20/20 |
| Claim-bearing sentences | 179 |
| Adjudicated | **126** (all `accepted`, bulk, by Bhuvan T) |
| **Outstanding** | **53** — every one a `mechanism` sentence |
| Edited / rejected | **0 / 0** |
| Backend tests | 436 passed, 4 skipped, 0 failed |
| Planted-violation detection | 5/5 detected (4 gating, 1 reported-only) |

### The one thing left

The 53 outstanding sentences are mechanism prose, and they are outstanding *by
design*. The closed-vocabulary check that would have screened them automatically
was retired at a measured 30% false-positive rate under a threshold committed
before tuning (see `reports/provenance_finding.md`, methods note). Mandatory
individual reading is what replaced it, so bulk-accepting them would convert a
deliberate trade into a silent downgrade.

```bash
python scripts/adjudicate.py --adjudicator "Bhuvan T"     # --only <drug> to split it up
```

What to look for is **direction of effect**: for a prodrug, less enzyme means
*less* active drug. A sentence stating the reverse would be fluent, fully
sourced, and wrong — the one error class no check in this project can catch.

### Field authorship (settled)

| Field | Author |
| --- | --- |
| `clinical_recommendation` | PharmCAT / CPIC, verbatim |
| `variant_rationale` | composed by code from the request's own profile |
| `summary`, `mechanism`, `patient_friendly` | LLM, genotype-agnostic |

### Open items beyond 5A

| Phase | Item |
| --- | --- |
| **5A** | 53 mechanism sentences to adjudicate — the only blocker |
| **5B** | Provider abstraction is done; Gemini quota still exhausted, Ollama path untested against a real local model |
| **6** | Deployment: nothing is deployed, Docker image never built, README links are placeholders |
| **6** | APK is fixed and verified at artifact level but has never been launched on a physical device |
| **7** | No clinical validation against GeT-RM / 1000 Genomes consensus genotypes |
| **7** | CYP2D6 remains uncallable from VCF (4 cases documented unreachable, never authored) |
| **8** | No qualified clinical reviewer — permanent, declared, disclosed on every response |

## Field authorship and the limits of automated checking

### Field authorship — who writes what

Not everything in an explanation has the same author, and conflating them was a
real defect: a prose model asked to emit `{diplotype}` templating complied 4
times in 14, leaving ten entries unable to show the patient's genotype.

| Field | Author | Guarantee |
| --- | --- | --- |
| `clinical_recommendation` | **PharmCAT / CPIC, verbatim** | Byte-identical to the guideline text. Never model-authored. |
| `variant_rationale` | **Composed by code** at request time from that response's own PharmCAT profile | Always present, always agrees with the reported genotype — structurally, not by instruction |
| `summary`, `mechanism`, `patient_friendly` | LLM (`meta/llama-3.1-8b-instruct`), genotype-agnostic | May not name a diplotype or emit placeholders; every clinical assertion must trace to a cited source |

### What the automated checks can and cannot do

Measured, not asserted — see `reports/provenance_finding.md`:

- Entity guard catches fabricated doses, genes, rsIDs, star alleles.
- Assertion checking catches invented quantities and timelines, but is
  **structurally blind to a fabricated mechanism** ("inhibited by grapefruit
  juice" contains no number and no unknown concept).
- Polarity checking catches negation reversal in both directions.
- Closed-vocabulary checking on mechanism text detects foreign entities but had a
  **57% false-positive rate** on real prose (30% after narrowing to concrete
  nouns), so it is **retired from the gate** and reports only.

**No combination of these certifies that a sentence is clinically correct.** They
are triage. The release gate is human adjudication of every shipped sentence, and
every mechanism sentence requires an individual decision. Adjudication is the
project author checking prose against its cited source — **not clinical expert
review**, which this project has never had and does not claim.

---

## A. What actually exists

### A1. Phase completion

| Phase | Status | Evidence |
| --- | --- | --- |
| **1 — monorepo seam** | ✅ Complete | `backend/app/main.py`, `app/lib/` present and working. ✅ *Fixed:* the dead `stub_analyzer.py` (417 lines of fabricated clinical text) has been deleted and the stale docstrings that referenced it rewritten |
| **2 — PharmCAT + CPIC mapping** | ✅ Complete | `backend/app/pharmcat_runner.py`, `backend/app/cpic_engine.py`, `backend/app/data/label_mapping.yaml` (314 lines, 9 rules). 24 parser tests + 51 mapping tests pass |
| **3 — grounded explanations** | ✅ Complete, ⚠️ content unreviewed and **still template-generated** | `backend/app/explanation/` (6 modules), `rag-corpus/mechanisms/` (6 files), `backend/app/data/explanations.json` (20 entries). **All 20 entries have `reviewed_by: null`; `generator: "template"`, `model: ""` — no LLM has ever been run against this project** |
| **4 — deployment** | ⚠️ **Partial — written, still largely unverified** | Workflows, Dockerfile, HF Space README and DEPLOY_NOTES all exist. ✅ *Fixed:* APK, compose mounts and CORS. ⛔ *Still open:* nothing is deployed, and the Docker image has never been built |
| **5A — real LLM generation** | ⚠️ **Tooling complete, run NOT executed** | 11 CLIs in `scripts/` + `scripts/README.md`; 44 new tests. Reachability derived (28 enumerated / 20 reachable / 8 not). ⛔ **Zero API calls have been spent on generation** — `explanations.json` is byte-identical to the Phase 3 template output, so there is no guard pass rate and no fallback count to report |

### A2. Test suite

**Backend — `cd backend && .venv/bin/python -m pytest`**

```
333 passed, 20 skipped in 1.16s     (249/1 at audit -> 305/4 after fixes
                                     -> 333/20 after Phase 5A)

Of the 20 skips: 1 live-LLM, 3 real-PharmCAT, and 16 in
test_guard_real_outputs.py that require a generation run that has not happened.
```

| File | Tests | |
| --- | --- | --- |
| `test_label_mapping.py` | 51 | |
| `test_explanation.py` | 51 | |
| `test_phase5a_tooling.py` | 28 | **new** (Phase 5A) — all run today |
| `test_deployment.py` | 44 | +11 (CORS fail-loud) |
| `test_guard.py` | 30 | |
| `test_analyze_api.py` | 29 | |
| `test_vcf_validation.py` | 27 | |
| `test_pharmcat_parser.py` | 24 | |
| `test_sample_vcfs.py` | 22 | **new** |
| `test_slot_verifier.py` | 12 | **new** |
| `test_infra_config.py` | 9 | **new** |
| `test_corpus.py` | 5 | |
| `test_android_identity.py` | 5 | **new** |
| `test_guard_real_outputs.py` | 16 | **new** (Phase 5A) — **all skip**: need a generation run |

- **Failures: 0**
- **Skipped: 4** — 1 live-LLM test (`GEMINI_API_KEY not set; live mode is
  optional by design`) plus 3 in `test_sample_vcfs.py::TestAgainstRealPharmcat`,
  which run the real pipeline when one is on `PATH`. **These 3 were executed
  manually against real PharmCAT during the fix pass and passed**, confirming
  each shipped sample produces its intended non-`Unknown` label.
- The live-LLM path still **has never executed against the real Gemini API.**

**Flutter — `cd app && flutter test`** → `+21: All tests passed!`
(`app/test/contract_test.dart` 7, `app/test/backend_status_test.dart` 14)

**`flutter analyze`** → `No issues found!`

**Coverage gaps.** ✅ *Closed:* Android manifest/package consistency, compose
mount correctness, sample-VCF usability, runtime slot values.
⛔ *Still open:* Docker image build, `generator_llm.py` against the real SDK,
`retrieval.py` container-path fallback, `scripts/pregenerate_explanations.py`.

### A3. Build outcomes

| Artifact | Result | Evidence |
| --- | --- | --- |
| Backend import | ✅ | `from app.main import app` succeeds; routes `['/', '/analyze', '/docs', '/health', '/ready', '/redoc']` |
| Backend serves | ✅ | Verified in this session in prior runs; `/health`, `/ready`, `/analyze` all return correct payloads |
| **Docker image** | ⛔ **UNVERIFIED — cannot build** | `which docker` → not found. **The image has never been built, in this session or any prior one.** |
| `flutter build web` | ✅ | Built previously for both `--base-href "/"` and `"/pharmaguard/"`; output ~30 MB incl. source maps |
| `flutter build apk --release` | ✅ **Fixed and re-verified** | Rebuilt 51.4 MB APK; `aapt dump badging` now reports `launchable-activity: com.pharmaguard.pharmaguard.MainActivity`, and that class **is present** in `classes.dex`. Still requires `JAVA_HOME=/opt/homebrew/opt/openjdk@17` — Gradle 8.14 rejects JDK 25 with a bare `25.0.1` as the whole error. ⛔ **Still not installed on a physical device** |
| `flutter build ios` | ⛔ Fails — environment | `xcrun simctl list runtimes` returns an **empty list**. Error: *"iOS 26.5 is not installed. Please download and install the platform from Xcode > Settings > Components."* Not a code fault |

#### 🔴 P0 — the release APK crashes on launch — ✅ **FIXED**

> **Resolved 2026-07-23.** Canonical id is now `com.pharmaguard.pharmaguard`
> across `namespace`, `applicationId` and the Kotlin package. A rebuilt APK
> reports `launchable-activity: com.pharmaguard.pharmaguard.MainActivity`, and
> that class is present in `classes.dex`. Guarded by
> `backend/tests/test_android_identity.py`.
>
> The original defect, for the record:

```
APK manifest launchable-activity : com.pharmaguard.app.MainActivity
Classes present in classes.dex   : Lcom/pharmaguard/app/R;
                                   Lcom/pharmaguard/pharmaguard/MainActivity;
```

`app/android/app/build.gradle.kts:35,51` set `namespace` and `applicationId` to
`com.pharmaguard.app`, so the manifest's `android:name=".MainActivity"`
(`app/android/app/src/main/AndroidManifest.xml:32`) resolves to
`com.pharmaguard.app.MainActivity`. But the only `MainActivity` compiled into the
APK is at `app/android/app/src/main/kotlin/com/pharmaguard/pharmaguard/MainActivity.kt`
(`package com.pharmaguard.pharmaguard`). The launcher target does not exist →
`ClassNotFoundException` at startup.

Phase 4 verified APK *metadata* (package name, permissions, `--dart-define`
string in `libapp.so`) but **never launched it**, so this passed unnoticed.

### A4. TODO / FIXME / STUB inventory

| File | Marker | Phase | Note |
| --- | --- | --- | --- |
| `backend/app/stub_analyzer.py` | 9× `TODO(pharmcat)` / `TODO(llm)`, 34× `STUB` | 1 | **Dead file.** Contains fabricated diplotypes, phenotypes and clinical text superseded in Phase 2 |
| `backend/app/models.py:9` | prose: *"served today comes from `stub_analyzer.py`"* | 1 | **Stale and now false** — misleads a reader about where clinical values originate |
| `backend/app/models.py:91,130,147,188` | `TODO(pharmcat)` ×3, `TODO(llm)` ×1 | 1→2/3 | **Stale** — the work described was completed in Phases 2 and 3 |
| `backend/app/cpic_engine.py:30` | `TODO(phase4)` | 4 | **Live** — pull real CPIC A–D evidence levels from the CPIC API |
| `backend/app/pharmcat_runner.py:77` | `TODO(phase5)` | 5 | **Live** — accept an external CYP2D6 diplotype via `-po` |
| `app/lib/utils/json_export_io.dart:6` | `TODO(phase2)` | 2 | **Live** — mobile export writes to a temp dir; wants `share_plus` |
| `infra/PHARMCAT_NOTES.md:148,184` | `TODO(phase4)`, `TODO(phase5)` | 4/5 | Documentation mirrors of the above |
| `app/lib/models/analysis.dart:149,161` | `'STUB'` | 1 | Harmless — a fallback default and a comment |

**Genuinely outstanding: 3** (phase4 CPIC levels, phase5 CYP2D6, phase2 mobile
share). **The other ~19 are stale markers on completed work**, concentrated in a
dead file.

---

## B. Correctness & integrity checks

### B1. Schema drift — ✅ **no drift**

Field names compared programmatically (Pydantic `model_fields` vs Dart `toJson`
keys) across all 8 contract classes:

| Class | Backend | Dart | Match |
| --- | --- | --- | --- |
| `AnalyzeResponse` | patient_id, timestamp, analyses, quality_metrics | identical | ✅ |
| `PerDrugResult` | drug, risk_assessment, pharmacogenomic_profile, clinical_recommendation, llm_generated_explanation | identical | ✅ |
| `RiskAssessment` | risk_label, confidence_score, severity | identical | ✅ |
| `PharmacogenomicProfile` | primary_gene, diplotype, phenotype, activity_score, detected_variants | identical | ✅ |
| `ClinicalRecommendation` | action, dosing_guidance, cpic_recommendation, cpic_evidence_level, alternatives, source | identical | ✅ |
| `LlmGeneratedExplanation` | summary, mechanism, variant_rationale, patient_friendly, disclaimer | identical | ✅ |
| `QualityMetrics` | vcf_parsing_success, variants_detected_count, processing_time_ms, warnings | identical | ✅ |
| `DetectedVariant` | rsid, gene, genotype, star_allele, function | identical | ✅ |

**Enums identical on both sides:** `RiskLabel` `[Safe, Adjust Dosage, Toxic,
Ineffective, Unknown]`, `Severity` `[none, low, moderate, high, critical]`,
`Phenotype` `[PM, IM, NM, RM, URM, Unknown]`, `CpicEvidenceLevel` `[A, B, C, D,
Unknown]`.

Nullability matches: `activity_score` and `rsid`/`star_allele` are optional in
both. One **intentional, documented** representation difference: `timestamp` is
`datetime` in Pydantic and `String` in Dart (with a `timestampUtc` parsing
getter) so the raw ISO string round-trips byte-for-byte — this is not drift, and
`contract_test.dart` asserts the round-trip.

### B2. Clinical provenance — ✅ **clean**

- **Zero** dose-like strings in any of the 4 explanation fields actually served
  to users (checked all 20 entries of `backend/app/data/explanations.json` against
  `\d+\s*(mg|mcg|µg|mg/kg|units?)`).
- 7 entries carry dose text in `cpic_recommendation_used`, which is **audit
  metadata capturing PharmCAT's verbatim CPIC output** at pre-generation time —
  e.g. *"Avoid standard dose (75 mg) clopidogrel if possible"*. Correct provenance.
- All 6 `rag-corpus/mechanisms/*.md` declare `contains_dosing: false`, and
  `backend/tests/test_corpus.py` enforces it as a build gate (5 tests pass).
- The only `mg`/`mcg` literals in backend source are the **unit-matching regex**
  in `backend/app/explanation/guard.py:57-58` — a detector, not a claim.
- ✅ **Resolved:** `backend/app/stub_analyzer.py` — which contained hand-written
  clinical strings and invented diplotypes (`*1/*2xN`, `*3A/*3A`, activity
  scores) — has been deleted. A follow-up repo-wide sweep found no other
  hardcoded clinical content, and every dose-bearing string asserted in the test
  suite was traced back to a real PharmCAT fixture.

### B3. Label mapping — ✅ **data-driven, fully documented**

`backend/app/data/label_mapping.yaml`, 314 lines, 9 ordered rules:
`contraindicated`, `avoid_for_lack_of_efficacy`, `avoid_for_toxicity`,
`avoid_unqualified`, `standard_dosing`, `dose_change_or_monitoring`,
`dosing_information_flag`, `alternate_drug_flag`, `fallback_unmatched`.

- **Every rule carries a `# Rationale:` comment** — verified programmatically;
  zero rules missing one.
- `clinical_review_status: NOT_OBTAINED` is set in the file and asserted by a
  test, alongside a note stating what *is* guaranteed. It replaced
  `requires_faculty_review: true`, which described a review as outstanding
  when no reviewer existed or was coming.
- No hardcoded label if/else in `backend/app/cpic_engine.py` — grep for
  `if ... RiskLabel.TOXIC/SAFE/INEFFECTIVE` returns nothing beyond an `UNKNOWN`
  guard clause.
- Rule **order is load-bearing** and pinned by 9 table-driven tests using verbatim
  real CPIC text.

### B4. CYP2D6 honesty — ✅ **verified, never fabricated**

```python
# backend/app/pharmcat_runner.py:72
CYP2D6_WARNING = (
    "CYP2D6 structural/copy-number variation cannot be resolved from unphased "
    "VCF; outside diplotype input planned"
)

# backend/app/pharmcat_runner.py:273
    if call_source == "NONE":
        status = CallStatus.NOT_ATTEMPTED

# backend/app/pharmcat_runner.py:282
    if symbol == "CYP2D6" and status is CallStatus.NOT_ATTEMPTED:
        warnings.append(CYP2D6_WARNING)
```

Live check: codeine returns `risk_label=Unknown`, `diplotype=Unknown`,
`phenotype=Unknown`, and the warning string appears in
`quality_metrics.warnings`. PharmCAT's unvalidated `-research cyp2d6` mode is
deliberately **not** enabled.

### B5. Faithfulness guard — ✅ exists and is tested; ⚠️ **not re-run per request in the deployed path**

- Defined: `backend/app/explanation/guard.py`.
- **Invoked per request in `live` mode only** —
  `backend/app/explanation/__init__.py:146` calls `check(...)`, with one retry
  then fallback to template.
- **In `static` mode (the deployed default) `check()` is NOT called per
  request.** `_static_result()` replays the guard verdict stored at generation
  time (`__init__.py:116`), with the in-code rationale *"Re-running the guard here
  would be theatre: the text has not changed since it passed."*
- The guard **does** run at pre-generation: `scripts/pregenerate_explanations.py:243,246,264`.

This is a defensible design (the served prose is fixed and was checked before
shipping), but the accurate statement is: **the guard is a build-time gate in
production, not a runtime one.**

✅ **Addressed 2026-07-23.** Two changes:
1. `backend/app/explanation/slot_verifier.py` now cross-checks every value
   injected at request time against the response's own `pharmacogenomic_profile`
   — the object the client renders in the card above the explanation. A mismatch
   demotes the result to the deterministic template and records a warning; a
   mismatched explanation is never served. Every response now reports
   `slots=verified` (or `slots=MISMATCH`) alongside `guard=passed`.
2. The README now states the split explicitly: **build-time guarded plus runtime
   slot-verified**, with an explicit note that neither check speaks to clinical
   correctness.

Tests proving rejection (all passing): invented `50 mg`, `300 mg`, `2.5 mg/kg`,
`30%`, `75 mcg`; invented `rs9999999`; plus a regression class
`TestSubstringFalseNegatives` pinning a fixed bug where `"50 mg"` was accepted
because the corpus contains `"cytochrome P450"`.

### B6. Static mode with no key — ✅ **verified**

Run with `GEMINI_API_KEY` and `GOOGLE_API_KEY` removed from the environment:

```
HTTP 200, analyses=3
  clopidogrel  label=Ineffective  empty_fields=[] unfilled_slots=[] disclaimer=OK
  codeine      label=Unknown      empty_fields=[] unfilled_slots=[] disclaimer=OK
  aspirin      label=Unknown      empty_fields=[] unfilled_slots=[] disclaimer=OK
  provenance: ['explanation mode=static, source=static, guard=passed, reviewed=NO', ...]
```

`backend/tests/test_analyze_api.py::TestStaticModeIsApiFree` additionally
monkeypatches `generator_llm.generate` to raise, so a regression reintroducing a
network call fails the build.

### B7. Data retention — ✅ **verified**

```python
# backend/app/pharmcat_runner.py:163
    finally:
        # Unconditional: temp dirs holding patient-derived data must not linger.
        shutil.rmtree(workdir, ignore_errors=True)
```

Four passing tests in `backend/tests/test_deployment.py::TestNoDataRetention`
assert the temp dir is empty after a real request, **after a simulated PharmCAT
crash**, that upload content is not echoed in the response, and that `/`
advertises the policy.

### B8. Secret leakage — ✅ **clean tree**, ⛔ **no history to audit**

- Grep for `AIza…`, `hf_…`, `sk-…`, PEM private-key headers, populated
  `CLOUDFLARE_API_TOKEN=` across the tree (excluding `.venv`, `build`, `Pods`):
  **no matches**.
- `backend/.env` — absent. `app/android/key.properties` — absent. No `*.jks` or
  `*.keystore` anywhere.
- `.gitignore` covers `.env`, `*.jks`, `key.properties`, `*.keystore` — all four
  confirmed present as exact lines.
- A test (`test_deployment.py::TestSecretHygiene::test_no_secret_literals_in_the_repo`)
  enforces this on every run.
- ⛔ **`git rev-parse` → "not a git repository".** There is no history, so the
  history-scan half of this check is **UNVERIFIED and currently unnecessary** —
  but it also means nothing has ever been committed, pushed, or CI-run.

### B9. CORS + rate limiting — ⚠️ **correct code, unset in deploy config**

Actual values with no environment configured:

```
allowed_origins()          : []          <-- EMPTY
allowed_origin_regex()     : ^https?://(localhost|127\.0\.0\.1)(:\d+)?$
RATE_LIMIT_REQUESTS        : 10
RATE_LIMIT_WINDOW_SECONDS  : 300
cors_summary()['wildcard'] : False
```

The policy is genuinely non-wildcard, and a prior session verified at raw-header
level that `attacker-site.pages.dev` and `evil.example.com` are rejected while a
configured origin is allowed.

**The problem (now fixed):** `CORS_ALLOWED_ORIGINS` appeared only as prose in
`infra/DEPLOY_NOTES.md` and `infra/hf-space/README.md`, and was set in neither
`infra/Dockerfile` nor `infra/docker-compose.yml`. Deployed as-is the site would
load while **every analysis failed**.

✅ **Fixed 2026-07-23.** `docker-compose.yml` now sets it (plus
`PHARMAGUARD_ENV=development`), the Dockerfile documents it, and
`security.assert_cors_configured()` makes a hosted instance with an empty
allowlist **refuse to start**, with a message naming the exact dashboard field
per platform. Detection uses the env markers each host injects (`SPACE_ID`,
`K_SERVICE`, `RENDER`, `PORT`), overridable via `PHARMAGUARD_ENV`. Local
development is unaffected — localhost is always allowed.

Rate limiter caveats already documented in `backend/app/security.py`: in-memory
(resets on scale-to-zero restart), keyed on the spoofable `X-Forwarded-For`.
Correctly described in-code as *"abuse dampening, not a security boundary."*

### B10. Licensing — ✅ **adequate**, minor gap

- `LICENSE:37` — PharmCAT attributed with URL, noted as invoked as a separate
  process and redistributed via the container.
- `LICENSE:42` — CPIC attributed, with a redistribution caveat.
- `LICENSE` carries an explicit **NOT A MEDICAL DEVICE** notice.
- `README.md:441` — repeats PharmCAT MPL-2.0 attribution.
- ⚠️ **Gap:** `LICENSE` says PharmCAT is "licensed under the Mozilla Public
  License 2.0" — **UNVERIFIED** in this audit; not re-checked against PharmCAT's
  own repository.
- ⚠️ **Gap:** Flutter/Dart third-party dependencies (`dio`, `file_picker`, `web`,
  `cupertino_icons`) have no attribution anywhere. All are permissively licensed
  (MIT/BSD/Apache) but nothing states this. Low risk, easy to add.

---

## C. Remaining work, by who can do it

### 🤖 Bucket 1 — Machine-doable (a future Claude Code session)

> ✅ Six items below were completed in the 2026-07-23 fix pass and are struck
> through. The remainder are still open.

- [ ] **🟡 P2 · Split `Phenotype.Unknown` into `NoResult` and `Indeterminate`.**
      The two states are clinically opposite (see limitation #21) and the contract
      cannot express the difference, so the distinction currently rides in a
      warning string that no client can branch on. *Scope, all in one change:*
      `Phenotype` in `backend/app/models.py`, the `phenotype_map` entries for
      `"indeterminate"` / `"no result"` in `label_mapping.yaml`, the `Phenotype`
      enum in `app/lib/models/enums.dart` (wire values must stay in lockstep —
      `contract_test.dart` compares them), and any Unknown-keyed explanation
      entry whose prose should then say which state applies. *Then delete:* the
      warning workaround in `map_phenotype_noted()`, README limitation row #21,
      and this item. `test_phenotype_table.py::test_phenotype_enum_still_has_no_indeterminate_value`
      fails the moment the enum changes and names what else to update — that
      failure is the checklist, not an obstacle. *If skipped:* a called-but-
      unclassifiable gene stays indistinguishable from an uncalled one to every
      API consumer, which is the weaker of the two disclosures available.

- [x] ~~**🔴 P0 · Fix the Android package mismatch.**~~ ✅ **DONE** Either move
      `MainActivity.kt` to `.../kotlin/com/pharmaguard/app/` and change its
      `package` declaration, or revert `namespace`/`applicationId` to
      `com.pharmaguard.pharmaguard`. *Why:* the APK crashes on launch today.
      *If skipped:* the mobile half of the project does not exist in practice, and
      the demo's "installable Android app" claim is false.
- [x] ~~**🔴 P0 · Add a test that would have caught it**~~ ✅ **DONE** — `test_android_identity.py`, sabotage-verified. — assert the manifest's
      resolved launch activity exists as a class in the built dex, or at minimum
      that the Kotlin package path matches `namespace`. *If skipped:* the same
      class of bug recurs on the next refactor.
- [x] ~~**🟠 P1 · Fix `docker-compose.yml` mount targets**~~ ✅ **DONE** from
      `/opt/pharmaguard/*` to `/home/user/app/*` to match the Dockerfile's
      WORKDIR. *If skipped:* `docker compose up` runs stale baked-in code and
      developers debug phantom behaviour.
- [x] ~~**🟠 P1 · Set a safe `CORS_ALLOWED_ORIGINS` default or fail loudly at
      startup** when the app is clearly deployed (non-localhost) with an empty
      allowlist. *If skipped:* a correct deployment still yields a site where
      every analysis fails.
- [x] ~~**🟡 Delete `backend/app/stub_analyzer.py`**~~ ✅ **DONE** (417 lines, dead, contains
      fabricated clinical values) and fix the stale docstring at
      `backend/app/models.py:9`. *If skipped:* a reader or a future session may
      believe clinical values still come from a hardcoded table; worse, someone
      could import it.
- [ ] **🟡 Prune the ~19 stale `TODO(pharmcat)` / `TODO(llm)` markers** on
      completed Phase 2/3 work in `models.py`. *If skipped:* the codebase looks
      less finished than it is, and real TODOs are camouflaged.
- [ ] **🟡 Rewrite `infra/README.md`** — it still claims HF Spaces needs "no card
      required", directly contradicting `infra/DEPLOY_NOTES.md`. *If skipped:*
      two docs in the same repo give opposite deployment advice.
- [ ] **🟡 Unify the backend-URL config name.** Currently three variants:
      `secrets.API_BASE_URL` (deploy-web), `vars.API_BASE_URL` (build-apk),
      `vars.BACKEND_URL` (keepalive). *If skipped:* the human setting up CI will
      almost certainly mis-set one and get a confusing failure.
- [ ] **🟢 Update the home-screen copy** at `app/lib/screens/home_screen.dart:180`
      — it says explanations "are still placeholders", which understates Phase 3.
      Replace with the accurate caveat: grounded and provenance-verified, with
      no clinical expert review — see the disclaimer in `app/lib/config.dart`.
- [ ] **🟢 Add tests for currently untested modules:** `generator_llm.py` against
      a mocked SDK boundary, `retrieval.py` container-path fallback,
      `scripts/pregenerate_explanations.py`.
- [ ] **🟢 Add third-party attribution** for Flutter dependencies to `LICENSE`.
- [ ] **🟢 Add a CI workflow that runs the test suite.** All 333 tests exist but
      no workflow invokes them — `deploy-web.yml` runs `flutter test` only, and
      the backend suite runs nowhere. *If skipped:* the new regression guards
      only fire when someone remembers to run pytest locally, which is precisely
      how the original defects survived.
- [x] ~~**🟢 Decide the fate of `test-data/sample1.vcf` / `sample2.vcf`**~~ ✅ **DONE** — deleted; they returned 503, not Unknown. (Phase 1
      relics, 5 and 4 rows, produce no calls). Documented as such, but they
      confuse a first-time user who picks them.

### 🔑 Bucket 2 — Human-only: accounts & credentials

> None of these can be done by a tool. Each needs a login, a payment method, or a
> credential only you can create.

#### 2.1 GitHub repository (do this first — everything else depends on it)

1. `cd` to the repo root and run `git init`.
2. Create `.gitignore`-respecting first commit: `git add -A && git commit -m "Initial commit"`.
3. On <https://github.com/new>, create a repository named `pharmaguard`.
   Choose **Public** (GitHub Actions minutes are unlimited for public repos;
   private repos get 2,000 min/month, which is still enough but metered).
4. `git remote add origin https://github.com/<you>/pharmaguard.git`
5. `git branch -M main && git push -u origin main`
6. **Verify:** the Actions tab lists three workflows (Keepalive, Deploy web,
   Build APK).

> ⚠️ Until this is done, **no workflow has ever run** and the secret names below
> have nowhere to live.

#### 2.2 Backend host — decide first (see Bucket 4 · D1), then follow one path

**Path A — Hugging Face Spaces (requires PRO, ~$9/month)**

1. Sign up at <https://huggingface.co/join>.
2. Subscribe to PRO at <https://huggingface.co/pricing> — **Docker Spaces are no
   longer free** (verified 2026-07-23).
3. Go to <https://huggingface.co/new-space>. Name `pharmaguard`, License MIT,
   SDK **Docker**, template **Blank**, visibility **Public**.
4. Clone it: `git clone https://huggingface.co/spaces/<you>/pharmaguard hf-space`
5. Copy in, exactly as `infra/DEPLOY_NOTES.md` §1 describes:
   `backend/` → `hf-space/backend/`, `rag-corpus/` → `hf-space/rag-corpus/`,
   `infra/Dockerfile` → `hf-space/Dockerfile`,
   `infra/hf-space/README.md` → `hf-space/README.md`.
6. `cd hf-space && git add -A && git commit -m "Deploy" && git push`
7. In the Space → **Settings → Variables and secrets → New variable**:
   - Name `CORS_ALLOWED_ORIGINS`, value `https://pharmaguard.pages.dev`
     *(paste the real Pages URL from step 2.3.5 once you have it)*
   - Name `EXPLANATION_MODE`, value `static`
8. **Do NOT create a `GEMINI_API_KEY` secret.** The deployed path makes no API
   call, and the app logs a warning if it finds an unused key.
9. **Verify:** `curl https://<you>-pharmaguard.hf.space/ready` returns
   `{"status":"ready", ...}`. Record this URL — it is your `API_BASE_URL`.

**Path B — Google Cloud Run (free tier, but needs a card on file)**

1. Sign in at <https://console.cloud.google.com> and create a project.
2. **Billing → Link a billing account** and add a card. Usage stays inside the
   always-free tier (2M requests, 180k vCPU-s, 360k GiB-s per month), but Google
   will not enable Cloud Run without a billing account attached.
3. Install the CLI: <https://cloud.google.com/sdk/docs/install>, then
   `gcloud auth login` and `gcloud config set project <PROJECT_ID>`.
4. Run the two commands in `infra/DEPLOY_NOTES.md` §2 verbatim
   (`gcloud builds submit …` then `gcloud run deploy … --memory 2Gi`).
5. **Verify:** the deploy prints a `https://…run.app` URL; `curl <URL>/ready`
   returns ready. Record it — it is your `API_BASE_URL`.

#### 2.3 Cloudflare Pages (web frontend — genuinely free, no card)

1. Sign up at <https://dash.cloudflare.com/sign-up>.
2. Find your **Account ID**: Workers & Pages → right-hand sidebar. Copy it.
3. Create an API token: **My Profile → API Tokens → Create Token → Create
   Custom Token**. Permissions: **Account · Cloudflare Pages · Edit**. Create,
   then copy the token — *it is shown once only.*
4. Create the Pages project once:
   `npx wrangler pages project create pharmaguard --production-branch main`
5. Note the assigned URL, normally `https://pharmaguard.pages.dev`. **Go back
   and paste this into the backend's `CORS_ALLOWED_ORIGINS`** (step 2.2.7 / 2.2 Path B env var) — the site cannot call the API until you do.
6. In GitHub → **Settings → Secrets and variables → Actions → New repository
   secret**, add:
   - `CLOUDFLARE_API_TOKEN` = the token from step 3
   - `CLOUDFLARE_ACCOUNT_ID` = the ID from step 2
   - `API_BASE_URL` = your backend URL from 2.2
7. On the **Variables** tab (not Secrets) of the same page, add:
   - `API_BASE_URL` = the same backend URL *(build-apk.yml reads `vars.`, not `secrets.` — see Bucket 1 item on unifying this)*
   - `BACKEND_URL` = the same backend URL *(keepalive.yml reads this name)*
8. **Verify:** push to `main`; the *Deploy web* workflow should go green and the
   Pages URL should load and reach `ready`.

#### 2.4 Android signing keystore (must never leave your machine)

1. `keytool -genkey -v -keystore ~/pharmaguard-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias pharmaguard`
2. Answer the prompts; **record both passwords in a password manager.**
3. Create `app/android/key.properties` (already gitignored) containing:
   ```
   storePassword=<store password>
   keyPassword=<key password>
   keyAlias=pharmaguard
   storeFile=/absolute/path/to/pharmaguard-release.jks
   ```
4. Back the `.jks` up somewhere private and durable — **not this repo**. Losing it
   means you can never update an installed app.
5. For CI signing, add four GitHub **secrets**:
   - `ANDROID_KEYSTORE_BASE64` = output of `base64 -i ~/pharmaguard-release.jks`
   - `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`
6. **Do this only after the P0 package fix**, or you will sign a crashing APK.

#### 2.5 Google AI Studio / Gemini key — *only if you want real LLM prose*

1. Go to <https://aistudio.google.com/apikey>, sign in, **Create API key**.
2. Keep it **local**: `export GEMINI_API_KEY=…` in your shell only.
3. Use it to run `python scripts/pregenerate_explanations.py --generator llm …`,
   which regenerates `explanations.json` with model-written text.
4. **Never** add it to the deployed backend's variables. The deployed path is
   `static` and needs no key; the startup assertion warns if it finds one.

### 🧑‍⚖️ Bucket 3 — Human-only: review, judgement, external artifacts

- [ ] **Read all 20 entries yourself before any demo** — `python
      scripts/export_for_reading.py`, then `python scripts/author_read.py
      --author "<name>"`. Currently 0 of 20 have been read. *Why it matters:*
      the guard catches fabricated entities and the provenance verifier catches
      untraceable claims, but **neither can catch reversed reasoning** — "reduced
      CYP2C19 activity makes the drug accumulate" is backwards, and every word
      of it traces to a source. That is the one class of error only a reader
      finds. *This is not clinical approval and the CLI cannot record it as
      such;* it is the strongest check available here.
- ~~Faculty guide sign-off on `label_mapping.yaml`~~ and ~~on the
  explanations~~ — **removed from this list. Not an action item; a declared
  limitation.** There is no qualified clinical reviewer on this project and
  there will not be one, so leaving these as open checkboxes misrepresented a
  permanent condition as pending work. See *"Accepted limitation: no clinical
  reviewer"* below.
- [ ] **Check the direction-of-effect table** in `rag-corpus/README.md` against
      the six mechanism files. Activation (CYP2C19, CYP2D6) vs clearance (DPYD,
      CYP2C9) vs transport (SLCO1B1) vs metabolite braking (TPMT) behave in
      *opposite directions*, and a reversal reads perfectly fluently.
- [ ] **Download GeT-RM / 1000 Genomes samples** for real validation
      (<https://www.cdc.gov/labquality/get-rm/>,
      <https://www.internationalgenome.org/data>). Synthetic VCFs share their
      assumptions with the implementation, so they prove plumbing, not
      correctness. *If skipped:* you cannot claim the caller is accurate.
- [ ] **Record the demo video** with the tags/hashtags your problem statement
      requires, publish it, and paste the URL into the README's *Demo video* row.
- [ ] **Verify every citation in the written report resolves to a real DOI/PMID.**
      The six PMIDs in `rag-corpus/mechanisms/*.md` were extracted from PharmCAT's
      own output, but the report's wider bibliography has not been checked here.
- [ ] **Ask your guide whether the panel expects a trained ML model.** This
      project is deterministic by design (rules + retrieval), which is defensible
      and arguably safer — but if the rubric demands ML, you need to know now.
- [ ] **Supply real dates** for review/submission, and fill the Team table in the
      README (currently `<your name>`, `<guide name>`, `<institution>`).
- [ ] **Decide on the Apple Developer Program** ($99/yr) — see Bucket 4 · D4.

### 🚧 Bucket 4 — Blocked, needs a decision

**D1 · Which backend host?** *(blocks all deployment)*
- **HF Spaces:** matches all existing docs and the Space README; 16 GB RAM.
  Costs **$9/month PRO** — Docker Spaces are no longer free.
- **Cloud Run:** genuinely free at this scale; needs a **credit card on file**;
  needs `--memory 2Gi` for the JVM. Fastest cold starts.
- **Render:** free, **no card**; but **512 MB RAM** is very tight for a PharmCAT
  JVM and may OOM on larger VCFs; 750 instance-hours/month.
- *Trade-off:* money vs. a card on file vs. reliability. All three work with the
  existing image unchanged (it honours `$PORT`).

**D2 · Should `explanations.json` be regenerated with the LLM?**
- **Keep template-generated:** costs nothing, already guard-passed, prose is
  plain and slightly mechanical.
- **Regenerate with Gemini:** richer prose; needs a free API key; **every entry
  must then be re-verified** (`verify_provenance.py --write`), and provenance is
  a genuinely harder gate for model prose than for templates — the model has to
  say less than it wants to.
- *Trade-off:* presentation quality vs. verification workload and a new
  dependency. **Attempted 2026-07-23 and it failed** — see the Phase 5A run
  notes; the token-ceiling defect is now fixed but the run has not been redone.

**D3 · Fill the 16 explanation gaps, or leave the template fallback?**
- 20 of 36 enumerated (drug × phenotype) cases have entries. The 16 gaps are
  *legitimate* (codeine — CYP2D6 uncallable; warfarin — CPIC is algorithmic;
  RM/URM for genes with no such phenotype) and fall back to the deterministic
  template.
- *Trade-off:* accepting a plainer fallback for edge cases vs. authoring prose
  for cases that may never appear in a demo.

**D4 · iOS distribution.**
- **Simulator-only (current):** free; demo runs on your Mac.
- **Apple Developer Program ($99/yr):** TestFlight/App Store distribution.
- **Free personal team:** installs on your own device but the build **expires
  after 7 days**.
- *Trade-off:* cost vs. whether the panel expects a real iOS install.

**D5 · Keepalive workflow on or off?**
- **On:** demo is instant, no cold start.
- **Off:** no wasted quota. On Render it would consume the 750 h/month budget;
  GitHub also disables scheduled workflows after 60 days of repo inactivity.
- *Trade-off:* demo smoothness vs. free-tier budget. (Suggest: on for the
  submission window only.)

**D6 · Repository visibility.**
- **Public:** unlimited Actions minutes; anyone can read the code (there are no
  secrets in it).
- **Private:** 2,000 Actions min/month; code stays closed.
- *Trade-off:* CI budget and portfolio value vs. privacy before submission.

---

## D. Limitations register

| # | Limitation | Intentional? | User-visible impact | Disclosed? |
| --- | --- | --- | --- | --- |
| 1 | **CYP2D6 never called** — no diplotype from a plain VCF | ✅ Intentional, documented | codeine/tramadol always `Unknown` | ✅ README ×4, API warning, UI card |
| 2 | **GRCh38 required** — GRCh37/hg19 rejected | ✅ Intentional | Upload fails with `UNSUPPORTED_REFERENCE_BUILD` | ✅ README, error message |
| 3 | **Cold starts up to ~1 min** | ✅ Intentional (free tier) | First analysis after idle is slow | ✅ README + explicit waking UI with progress |
| 4 | **6 drugs / 7 genes only** | ✅ Intentional | Anything else → `Unknown` | ✅ README, UI chips |
| 5 | **warfarin always `Unknown`** — CPIC guidance is algorithmic | ✅ Intentional | A listed demo drug returns nothing useful | ✅ README |
| 6 | **`cpic_evidence_level` always `Unknown`** | ✅ Intentional | Field looks unimplemented | ✅ README + backend README |
| 7 | **No persistence / auth / history** | ✅ Intentional (privacy) | Results vanish on reload; no accounts | ⚠️ **Partial** — privacy framing is in README, but "you cannot save or revisit a result" is never stated |
| 8 | **No clinical expert review — permanently** | ✅ **Declared and accepted** | Clinical prose has had no expert eyes, and will not | ✅ **Strong** — in the disclaimer on every result, in `quality_metrics.warnings`, in the README limitations table, in `reports/provenance_report.md`, and CI fails if any artifact implies otherwise |
| 9 | ~~16 of 36 cases fall back to template~~ — **the figure was wrong** | ✅ Superseded | Real enumeration: 28 cases, 20 reachable, **all 20 authored**. 8 unreachable cases are not authored because doing so would require fabrication | ✅ **Now documented** — `scripts/README.md` §Reachability, and encoded in `test_phase5a_tooling.py::TestReachability` |
| 10 | **Guard is build-time, not request-time, in static mode** | ✅ Intentional | None directly | ✅ **Now disclosed** — README §"How explanations are checked" states the build-time/request-time split, and runtime slot verification now covers the injected values |
| 11 | **Rate limit 10 / 5 min, in-memory, spoofable key** | ✅ Intentional | A busy demo could self-throttle | ✅ README |
| 12 | **5 MB upload cap** | ✅ Intentional | Whole-genome VCFs rejected | ✅ README + error |
| 13 | **iOS simulator only** | ✅ Intentional (cost) | No installable iOS app | ✅ README + DEPLOY_NOTES |
| 14 | **Not clinically validated** — synthetic VCFs only | ✅ Intentional | Accuracy is unmeasured | ✅ README, LICENSE, UI banner |
| ~~15~~ | ~~**🔴 Release APK crashes on launch**~~ | ✅ **FIXED** | — | Resolved 2026-07-23; guarded by `test_android_identity.py`. **Still unverified on a physical device** |
| ~~16~~ | ~~**🟠 `docker compose up` runs stale baked-in code**~~ | ✅ **FIXED** | — | Resolved 2026-07-23; guarded by `test_infra_config.py`. **Unverified — Docker still unavailable here** |
| ~~17~~ | ~~**🟠 CORS unset in deploy config**~~ | ✅ **FIXED** | — | Set in compose; a hosted instance with an empty allowlist now refuses to start |
| 18 | **Free-tier caps** (HF 16 GB/2 vCPU; Render 512 MB & 750 h; Cloud Run 180k vCPU-s) | ✅ Intentional | Throttling/OOM under load | ✅ DEPLOY_NOTES table |
| ~~19~~ | ~~**Dead `stub_analyzer.py` with fabricated clinical values**~~ | ✅ **FIXED** | — | Deleted 2026-07-23 |
| 20 | **Live LLM path never executed** against the real API | ⚠️ Accidental | `live` mode is unproven | ❌ **NOT disclosed** — README presents it as a working mode |
| 21 | **`Phenotype.Unknown` conflates *no result* with *indeterminate*** | ⚠️ **Deferred, not intentional** — the right fix is a distinct enum value, held back only because it changes the response contract, the Pydantic model, and the Dart client together | A gene that WAS called but is unclassifiable reports identically to one never called. The prose served for both used to assert *"your genetic result was not available for this gene"* — false in the indeterminate case, and a claim the pipeline made about **its own inputs**, not a clinical judgement | ✅ **Disclosed** — the falsehood is removed (Unknown-keyed prose now says only that no *usable* result was established, true of both states); `map_phenotype_noted()` surfaces PharmCAT's raw phenotype string in `quality_metrics.warnings`; README limitations table states plainly that a warning is weaker than a typed field; `test_phenotype_table.py` pins both the removal and the deferral |

### 🔊 Loudest disclosure gaps

1. **#8 — "unreviewed clinical prose" is buried.** It is in the API response but
   the UI hides it behind a collapsed tile. For a clinical-adjacent tool this
   deserves to be as prominent as the not-a-medical-device banner. **Now the
   single loudest gap**, since the APK and guard-timing items are resolved.
2. **#20 — `live` mode has never run.** README documents it as a supported mode
   alongside `static`, without noting it is untested end-to-end.
3. **#9 was miscounted, and the real gap is different.** No *reachable* case
   falls back — all 20 are authored. The undisclosed fact is that all 20 are
   **template text, not model output**: the field named
   `llm_generated_explanation` has never held LLM prose. That is the honest
   disclosure gap, and it is larger than the one originally recorded.
4. ~~#15 APK broken~~ / ~~#10 guard timing~~ — both resolved 2026-07-23.

---

## Phase 6 — COMPLETE (closed 2026-07-25)

Validation. Every number below is measured and traceable to an artifact under
`reports/`; none is projected.

### Final numbers

| Measurement | Result | Scope |
| --- | ---: | --- |
| **Label-mapping correctness** | **92 / 105** | Exhaustive over every phenotype combination for all 6 drugs. 13 accepted divergences, individually justified |
| **Integration fidelity — 1000 Genomes** | **100.0000%** | 400 samples · 2 800 (sample, gene) pairs · **5 600 field comparisons** · 0 mismatches · 0 parser errors |
| **Integration fidelity — adversarial VCFs** | **0 mismatches** | All 74 of PharmCAT's own unit-test VCFs for our genes, 148 field comparisons |
| **CYP2D6 negative control** | **400 / 400 declined** | Not one fabricated call across the whole cohort |
| **Usable-result rate** | **82.79%** | 1 987 / 2 400 callable (sample, gene) pairs. A floor, not a production estimate — see below |
| **External genotype concordance** | **n = 1** | `NA12273`, 2/2 exact. Reported as n=1 throughout, never as a percentage |
| **Label/prose cross-check** | **0 divergences** | 20 / 20 reachable explanation entries |
| **Phenotype/label invariant** | **294 labels corrected** | 400 samples × 6 drugs. Every change removed a confident label; none added one. Checked at build time over all reachable cases and at request time on every response |
| **SAS breakout** | **n = 75** | CYP2C19 reduced-function (IM+PM) **53.3%** (40/75), second only to EAS. No per-population claim: n=8–23 per population |

Both halves of the 82.79%: the 1000 Genomes panel is filtered to polymorphic
sites, so slices carry only 19–57% of PharmCAT's required positions, and the absent
ones disproportionately define reference-like haplotypes — which is what produces
the 308 ambiguous calls making up most of the shortfall. A clinical panel would
call more. But the ambiguity is real, and for CYP2C9 all 71 ambiguous calls are
genuinely phenotype-discordant, so `Unknown` is correct there rather than an
artifact.

### Defects found by this phase

1. **Substring collision in `label_mapping.yaml`** — 16 azathioprine rows labelled
   `Safe` where CPIC directs a reduced starting dose. Fixed by precedence, against
   a pre-committed definition of "fixed" recorded before any edit.
2. **`sourceDiplotypes` vs `recommendationDiplotypes`** — displayed `Normal
   Metabolizer` where PharmCAT called `Indeterminate`, and dropped a carried variant
   from the reported genotype. 4 of 302 called DPYD samples. **Found only at n=400**;
   invisible to unit tests, to the exhaustive mapping validation, and to n=1
   concordance. Written up as Evidence 7 in `provenance_finding.md`.
3. **Tentative phenotype table gap** — SLCO1B1 `Possible Decreased Function`
   collapsed to `Unknown` under a red `Toxic` badge. Confirmed real in the cohort
   (4 occurrences).
4. **Unknown-keyed prose asserted a falsehood** — "your genetic result was not
   available" is untrue when the gene was called but unclassifiable.
5. **Wrapper-only PharmCAT dependency** — `/analyze` returned 503 on a machine
   holding a working jar and JRE. Now invoked via the jar directly.

Two defects were in my own measurement code and are recorded because they shaped
the results: a comparator that scored 26 documented normalisations as mismatches,
and a frequency estimator whose "stricter" variant was systematically worse
(dropping ambiguous calls pushed CYP2C9 `*2` in Europeans from a near-exact 13.3%
to 0.0% against a published 12.7%).

6. **🔴 phenotype → label was never verified** — the largest defect of the phase,
   and the fourth edge of the verification graph. A confident label could sit beside
   a phenotype the caller declined to assert: `lookup_keys` derive from
   `recommendationDiplotypes` (whose job is to find a table row, not to state what
   the patient has), and reading `candidate[0]` asserted one of several disagreeing
   candidates. Fixed as a general invariant gated before the CPIC lookup, plus a
   phenotype→label check at build and request time.

   **294 of 2 400 (drug, sample) results changed, every one removing a confident
   label:** simvastatin 195 `Safe`→`Unknown`, fluorouracil 81 `Safe`→`Unknown` and
   17 `Adjust Dosage`→`Unknown`, azathioprine 1. None moved the other way. 49% of
   the cohort had been shown a green `Safe` for simvastatin unsupported by evidence.

7. **The one defect in the opposite direction** — 30 SLCO1B1 calls where every
   informative candidate agrees function is decreased. A naive invariant would have
   suppressed those to `Unknown`, discarding a myopathy warning the source *did*
   assert. The invariant therefore keys on phenotype agreement, never on diplotype
   ambiguity, and `variant_rationale` states the split.

A correction worth recording: an earlier draft of the validation report claimed
those 30 calls returned `Unknown` and dropped a warning. They did not — they already
reported `Toxic`. The wrong figure came from the validation script's own failure
classification rather than from the pipeline, and checking the pipeline directly
disproved it. The real defect was the reverse and 6× larger.

Two further defects were in my own measurement code, recorded because they shaped
results: a first fix for the ambiguity case filtered every `UNKNOWN`-mapping
candidate out before comparing, which collapsed `{Normal Function, Indeterminate}`
to `{NM}` and left all 195 samples exactly as broken while measuring as a fix —
caught only by re-running the cohort. `n/a` is silence; `Indeterminate` is
testimony.

---

## Remaining work, project-wide

| Item | State | Blocker |
| --- | --- | --- |
| **Human adjudication of explanation prose** | **In progress** — 124 of 179 claim sentences decided, 55 outstanding | Human judgement; the release gate stays red until it is done. The explanation store is frozen while this runs |
| **Phase 5B — outside CYP2D6 diplotype input** | Not started | Needs a trustworthy external caller (Stargazer/Cyrius or a lab report). `-po` is already supported by PharmCAT 3.4.0; research mode stays disabled deliberately |
| **Phase 7 — docs, demo, team review** | Not started | Demo video, README links, team sign-off |
| **Phase 8 — deployment** | Not started | Accounts only the project owner can create; every step written and verified in `infra/DEPLOY_NOTES.md`. Blocked behind the adjudication gate by design |
| **`Phenotype.Unknown` enum split** | Deferred, documented (limitation #21) | Contract + Dart change; pinned by a test that fails if someone adds the value without updating the docs |
| **SLCO1B1 phenotype-without-diplotype state** | Proposed, not built | Awaiting decision (see above) |

## E. Top risks to a live demo

Ranked by likelihood × damage.

| # | Risk | Likelihood | Mitigation |
| --- | --- | --- | --- |
| 1 | **The APK has still never been launched on a device.** The crash is fixed and verified at the artifact level (manifest target now exists in the dex), but nobody has installed it. | Medium | Install the rebuilt APK on a real phone once and open it. The fix is verified statically; only a device proves it |
| 2 | **Nothing is deployed.** No HF Space, no Pages project, no git remote. The README's live links are placeholders. | **Certain** today | Complete Bucket 2 well before demo day. Budget a full evening — the first Docker build of a ~2 GB image is slow |
| 3 | **Deployed site loads but every analysis fails on CORS.** | **Low** — the backend now refuses to start with an empty allowlist, so this surfaces in the deploy log instead of at demo time | Still run one real analysis **from the deployed URL**, not localhost, before presenting |
| 4 | **Cold start makes the first analysis look like a hang.** ~1 min on free tiers. | High if the demo starts cold | Enable the keepalive workflow for the demo window, and **hit the site yourself 2 minutes before presenting**. The waking UI already explains the wait — let it show |
| 5 | **A panel member asks "who checked this clinical text?"** | Low–Medium | Answer directly: *nobody, and that is why the system writes no clinical content of its own.* Every clinical sentence is machine-verified to trace to a CPIC recommendation or a cited mechanism document — `scripts/verify_provenance.py`, 20/20 passing, enforced in CI. Show `reports/provenance_report.md`. The weak answer is "review is pending"; it is not pending, and the design is the response to that |
| 6 | **Docker build fails on first attempt** and has never been tested anywhere. | Medium | Build the image locally or in CI at least once, days ahead. Do not let the first-ever build be on demo day |
| 7 | **Rate limit trips mid-demo** — 10 analyses per 5 minutes, and a rehearsal plus the real run share one IP. | Medium | Raise `RATE_LIMIT_REQUESTS` for the demo window, or rehearse on a different network |
| ~~8~~ | ~~Someone picks `sample1.vcf` and gets a broken-looking result~~ | ✅ **Resolved** | The relics are deleted (they returned **503**, not Unknown). All three remaining samples are guarded by `test_sample_vcfs.py` |
| 9 | **You demo `live` LLM mode** to show off the AI angle, and it fails — it has never run against the real API. | Medium if attempted | Do not demo `live` mode unless you have tested it end-to-end with a real key first |
| 10 | **iOS is requested** and no simulator runtime is installed on the machine. | Low–Medium | Install an iOS runtime via Xcode → Settings → Components ahead of time (multi-GB), or state up front that iOS is simulator-only and out of scope |

---

## PASTE-BACK SUMMARY

```
PHARMAGUARD — PROJECT STATUS
Audited 2026-07-23 (read-only) · Fix pass 2026-07-23 · Phase 5A 2026-07-23
git baseline 6d758cc

WHAT IT IS
Pharmacogenomic risk prediction: VCF -> PharmCAT -> deterministic CPIC risk
label -> grounded explanation -> Flutter web/mobile client. Final-year project.
Research/educational only; explicitly not a medical device.

PHASE STATUS
- Phase 1 (seam/stub)          COMPLETE (dead stub file since deleted)
- Phase 2 (PharmCAT + CPIC)    COMPLETE and solid
- Phase 3 (explanations+guard) COMPLETE, but all 20 explanation entries are
                               template-generated and 0 are human-reviewed
- Phase 4 (deployment)         PARTIAL — code fixed, nothing deployed,
                               Docker image never built
- Phase 5A (real LLM gen)      TOOLING COMPLETE, RUN NOT EXECUTED. 11 CLIs and
                               44 tests exist and pass. Zero API calls have been
                               spent on generation, so explanations.json is still
                               byte-identical template output and there is NO
                               guard pass rate and NO fallback count to report.

TESTS
- Backend: 333 passed, 20 skipped, 0 failed  (249/1 -> 305/4 -> 333/20)
- Flutter: 21 passed; analyzer clean
- Skips: 1 live-LLM test (no API key) + 3 real-PharmCAT sample tests, which WERE
  run manually against real PharmCAT and passed + 16 real-model-output tests
  that skip until a generation run exists (each names the command that
  produces its input, rather than passing on no data)
- NOTE: no CI workflow runs the backend suite — tests only run when invoked
  locally. This is how the original defects survived.

SIX DEFECTS FIXED (each with a sabotage-verified regression test)
1. P0 Android: manifest launch target didn't exist in the APK's own dex ->
   installed and crashed instantly. Canonical id is now
   com.pharmaguard.pharmaguard across namespace/applicationId/Kotlin package
   (chosen because it needed 2 line edits AND matched iOS's existing bundle id).
   Rebuilt APK verified: launch target now present in classes.dex.
2. P0 Deleted a 417-line dead stub file containing fabricated doses and
   diplotypes. Repo-wide sweep found no other hardcoded clinical content; every
   dose string in tests traced back to a real PharmCAT fixture.
3. P1 CORS was set in no deploy config (default empty) -> deployed site would
   fail every analysis. Now set in compose, documented in the Dockerfile, and a
   hosted instance with an empty allowlist REFUSES TO START with a message
   naming the exact dashboard field per platform.
4. P1 docker-compose mounted /opt/pharmaguard/* while WORKDIR was
   /home/user/app -> compose silently ran stale baked-in code. Realigned.
5. P1 Legacy sample VCFs deleted. They were WORSE than the audit found: too
   sparse for PharmCAT to write any report, so /analyze returned 503, not
   "Unknown". A demo user picking the first file got a server error.
6. P1 Runtime slot values (diplotype, detected variants) were injected into
   guard-approved prose AFTER the guard ran, so nothing checked them. Now
   cross-checked against the response's own profile; mismatch demotes to the
   template and warns. Responses report guard=passed, slots=verified.

INTEGRITY CHECKS (unchanged unless noted)
- Schema drift:        NONE. 8 contract classes + 4 enums match exactly.
- Clinical provenance: CLEAN. Zero invented doses in served text.
- Label mapping:       DATA-DRIVEN YAML, 9 ordered rules, all with rationale.
- CYP2D6 honesty:      VERIFIED. Never fabricated; explicit warning.
- Guard:               Build-time gate in static mode PLUS runtime slot
                       verification. README now states this split accurately.
- Static mode:         Works with no API key at all.
- Data retention:      finally-block rmtree; tests cover the crash path too.
- Secrets:             Clean tree; .gitignore covers .env/*.jks/key.properties.
- Licensing:           PharmCAT + CPIC attributed. Gaps: MPL-2.0 claim
                       unverified; Flutter deps unattributed.

BUCKET 4 — DECISIONS STILL BLOCKING PROGRESS (unchanged)
D1 Backend host: HF Spaces (Docker Spaces now need PRO ~$9/mo) vs Cloud Run
   (free but needs a card on file, 2GiB) vs Render (free, no card, 512MB may
   OOM the JVM). All work with the existing $PORT-aware image.
D2 Regenerate explanations with Gemini (richer prose, needs key, resets all
   review) vs keep template output (free, guard-passed, plainer).
   -> Phase 5A built the tooling for this; it awaits approval to spend quota.
D3 RESOLVED BY EVIDENCE, not judgement. There are not 16 missing cases: the
   real enumeration is 28, of which 20 are reachable and all 20 ARE authored.
   The 8 unreachable ones cannot be authored without fabrication (CYP2D6
   uncallable x4, warfarin algorithmic x3, SLCO1B1 no increased-function x1).
D4 iOS: simulator-only (free) vs Apple Developer Program ($99/yr) vs free
   personal team (7-day expiry).
D5 Keepalive cron on (instant demo, burns quota) vs off (saves quota).
D6 Repo public (unlimited CI minutes) vs private (2000 min/mo).

UNRESOLVED LIMITATIONS NOT DISCLOSED TO USERS
- Explanations are unreviewed — surfaced only in a collapsed UI tile. Now the
  loudest gap.
- ALL 20 explanations are template text. The field named
  `llm_generated_explanation` has never held LLM output, so the faithfulness
  guard has only ever validated strings this codebase composed itself.
- CORRECTION to the original audit: the "16 of 36 cases fall back" figure was
  wrong — 36 was the naive drug x phenotype product. Real enumeration is 28,
  20 reachable, all 20 authored. No reachable case falls back.
- `live` LLM mode is documented as supported but has NEVER run against the real
  API.
- No persistence/history: results vanish on reload.

TOP DEMO RISKS
1. Nothing is deployed; README links are placeholders. Needs a full setup pass.
2. The APK crash is fixed and verified at artifact level, but the APK has still
   never been launched on a physical device. Install it once.
3. Docker image has never been built anywhere. Build it days ahead.
4. Cold start (~1 min) reads as a hang. Warm it 2 min before presenting.
5. "Who reviewed the clinical text?" — nobody, and the design answers for it:
   the system asserts no clinical content of its own. Every clinical sentence
   is machine-traced to a CPIC recommendation or a cited mechanism document
   (verify_provenance.py, 20/20, enforced in CI). Show provenance_report.md.
5b. "Where is the LLM?" — the tooling is built and tested but has never been
   run. Either run it (approve the quota spend) or present the pre-generation
   architecture as the deliberate design choice it is. Do not imply prose was
   model-generated when it was not.
6. Rate limit (10/5min) can trip between rehearsal and the real run.
7. No CI runs the backend tests, so a future regression won't be caught
   automatically.

HUMAN-ONLY WORK (no tool can do these)
Accounts/credentials: backend host account (see D1); Cloudflare account + Pages
project + API token; GitHub Actions secrets (CLOUDFLARE_API_TOKEN,
CLOUDFLARE_ACCOUNT_ID, API_BASE_URL) and variables (API_BASE_URL, BACKEND_URL);
Android keystore (keep local, gitignored); optional Gemini key for
pregeneration only.
Judgement: read all 20 explanations personally (export_for_reading.py +
author_read.py) -- catches reversed reasoning, which no automated check here
can. NOT clinical approval: no qualified reviewer exists and none is expected,
which is a declared limitation rather than an open action. Download GeT-RM/1000
Genomes for real validation; record + publish the demo video; verify report
citations resolve; confirm whether the panel expects a trained ML model;
supply real dates and team names.
```
