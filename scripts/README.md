# `scripts/` — build-time tooling

Everything here runs **on a developer's machine, never in the deployed service.**
These scripts may read the API key, call Gemini, and write into
`backend/app/data/`. The deployed API imports none of them: it reads the
generated JSON and does deterministic slot filling, so the hosted service needs
no key, no network and no model.

> ⚠️ **There is no clinical reviewer on this project, and there will not be
> one.** An earlier design assumed a qualified clinician would eventually vet
> the generated prose. That backstop does not exist, so the project makes a
> narrower claim instead — and enforces it:
>
> **The system asserts no clinical content of its own.** Every sentence making a
> clinical claim must trace, word for word, to a CPIC recommendation as PharmCAT
> emitted it, or to a mechanism document carrying a citation and a retrieval
> date. `scripts/verify_provenance.py` checks this and exits non-zero on any
> failure; CI runs it on every push.
>
> That establishes the system invented nothing. It does **not** establish that
> the text is clinically correct — a sentence built entirely from source words
> can still describe a mechanism backwards. The API says so on every response.

---

## API key hygiene

**The key is BUILD-TIME ONLY.** It is needed to *produce* `explanations.json`.
It is not needed to serve it, and it must never reach a deployment.

| Rule | Why |
| --- | --- |
| Key lives in **repo-root `.env`**, gitignored | Checked with `git check-ignore`, not by reading `.gitignore` — only git can tell you what git will actually do |
| **Never `backend/.env`** | `app/security.py::assert_no_baked_secrets` refuses to boot if it finds one. Inside a deployed image such a file could only be a leaked credential |
| Never passed as a CLI argument | Arguments land in shell history and in `ps` output |
| Every exception render is passed through `_common.scrub()` | Error strings come from a third-party SDK whose behaviour we do not control |
| Only `_common.redact()` ever prints key material | Prints a short prefix and suffix plus the length — enough to confirm *which* key is loaded, not enough to use it |

`preflight.py` fails fatally if `.env` is unignored, and separately if `.env`
was ever *committed* — an ignored file can still be in history.

> 🔑 **Rotate the key if it has been exposed anywhere** — pasted into a chat, a
> ticket, a terminal recording, a CI log, or a screenshot. Revoke at
> <https://aistudio.google.com/apikey> and issue a new one. Rotation costs
> nothing here: the key is not embedded in any artifact, so a new one requires
> no rebuild, no redeploy, and no change to `explanations.json`. There is no
> reason to leave a possibly-exposed key live.

### Audit, 2026-07-23

Re-run after the first real generation run, against every path that renders an
exception.

| Check | Result |
| --- | --- |
| `.env` gitignored | ✅ `.gitignore:4` (`*.env`), confirmed with `git check-ignore` |
| `.env` ever committed | ✅ **0 commits** touch `.env` or `backend/.env`, across all refs |
| `.env` currently tracked | ✅ untracked |
| Key-shaped literals in git history | ✅ 0 matches for `AIza…{35}` or `AQ.Ab…` |
| Key-shaped literals in the working tree | ✅ none outside `.env` itself |
| `backend/.env` | ✅ absent (its presence blocks server startup by design) |
| SDK echoes the key in errors | ✅ **No** — tested live with a sentinel key; the 401 response contains no key material |
| Every exception-render path scrubs | ✅ verified empirically, sentinel key survived nowhere |

One real gap was found and closed: `guard_experiment.py` wrote `str(exc)` from
an SDK failure straight into `reports/guard_experiment_raw.json`, **which is
committed**. An SDK error that echoed the key would have published it. That
render is now scrubbed.

`scrub()` is applied even on paths where the exception provably cannot contain
a key. "Verified once" is not "guaranteed", the SDK is third-party code whose
error strings we do not control, and a leaked key in a committed artifact or a
captured terminal log is unrecoverable. The one place deliberately *not*
scrubbed is `_common.RateLimiter.is_rate_limit_error`, which builds a lowercase
string only to match against — scrubbing there would imply the value reaches
output, and it does not.

---

## Providers — the LLM layer is not tied to one vendor

The generation layer is provider-agnostic. Two keys hit their walls during this
project (Gemini's daily free-tier cap, then again), so the code that calls a
model was pulled behind an interface and vendors became configuration.

| Provider | `LLM_PROVIDER` | Key | Notes |
| --- | --- | --- | --- |
| **NVIDIA NIM** | `nvidia` | `NVIDIA_API_KEY` (`nvapi-…`) | OpenAI-compatible, `https://integrate.api.nvidia.com/v1`. The working provider for this phase |
| Google Gemini | `gemini` | `GEMINI_API_KEY` | The original. Quota-exhausted as of 2026-07-23 |
| Ollama (local) | `ollama` | none | Zero-quota dev against a local model (`OLLAMA_HOST`) |
| Template | `template` | none | Deterministic, no network. The fallback, and an honest benchmark baseline |

Select with two environment variables (or `--provider` / `--model` on any CLI):

```bash
export LLM_PROVIDER=nvidia
export LLM_MODEL=<id from list_models.py>
```

**Switching when a key runs out** is now a config change, not a code change:
set `LLM_PROVIDER` to another vendor and re-run with `--resume`. Errors are
normalised across vendors — a depleted account raises `QuotaExhausted` (NVIDIA
returns HTTP **402** for this; Gemini says `RESOURCE_EXHAUSTED`), which stops a
batch cleanly instead of emitting 20 template fallbacks that bury the cause.

**JSON output** is negotiated per model: the provider tries
`response_format={"type":"json_object"}` first and falls back to prompt-enforced
JSON, stripping any `<think>…</think>` reasoning block and unwrapping code
fences before parsing. Which mode a model needed is recorded on every entry
(`json_mode`).

---

## From a clean checkout to reviewed explanations

Eleven steps. Only steps 7 and 9 spend real quota; the rest are free.

```bash
# 1. Dependencies
python -m venv backend/.venv && source backend/.venv/bin/activate
pip install -r backend/requirements.txt -r backend/requirements-llm.txt

# 2. Provider + key (repo root .env, gitignored — NOT backend/.env)
echo 'LLM_PROVIDER=nvidia'       >  .env
echo 'NVIDIA_API_KEY=nvapi-...'  >> .env

# 3. Discover real model ids. Never write one from memory.
python scripts/list_models.py --provider nvidia
python scripts/list_models.py --provider nvidia --probe-json <id>   # check JSON support

# 4. Pick the model on evidence, not reputation (tiny spend).
python scripts/benchmark_models.py --auto --dry-run          # plan
python scripts/benchmark_models.py --models <a,b,c>          # runs 3 cases each
echo 'LLM_MODEL=<the winner>' >> .env

# 5. Gate everything on preflight. Exits non-zero if a run would fail.
python scripts/preflight.py

# 6. Derive which cases the pipeline can actually produce.
python scripts/enumerate_cases.py

# 7. Rehearse, then generate. --dry-run makes no API call.
python scripts/pregenerate_explanations.py --dry-run
python scripts/pregenerate_explanations.py --resume

# 8. The real numbers for the project report.
python scripts/generation_report.py

# 9. Adversarial validation of the guard. Separate quota spend.
python scripts/guard_experiment.py --dry-run
python scripts/guard_experiment.py

# 10. The release gate. Traces every clinical sentence to a cited source.
python scripts/verify_provenance.py --write
python scripts/review_status.py          # non-zero if anything is unverified

# 11. Optional but worthwhile: read them yourself. Not clinical approval —
#     nobody here can give that — but it catches direction-of-effect errors,
#     which no check in this repo can.
python scripts/export_for_reading.py
python scripts/author_read.py --author "<your name>"
```

Steps 5, 6, 8, 10 and 11 are safe to re-run at any time.

---

## The scripts

| Script | Spends quota | Purpose |
| --- | --- | --- |
| `_common.py` | — | Shared plumbing: provider/key resolution, throttle, redaction, atomic writes. Not a CLI |
| `list_models.py` | metadata only | Real model ids per provider (`--provider nvidia`), with a JSON-support probe |
| `benchmark_models.py` | **yes** (tiny) | Runs candidates on 3 real cases; ranks by guard > provenance > JSON. Picks the model |
| `preflight.py` | one metadata call | Provider-aware checks. Gate a run on its exit code |
| `enumerate_cases.py` | no | Derives reachable cases from PharmCAT's own phenotype definitions |
| `pregenerate_explanations.py` | **yes** | Generates via the selected provider, guards, retries, falls back. Writes `explanations.json` |
| `guard_experiment.py` | **yes** | Four adversarial arms. Evidence that the guard discriminates |
| `generation_report.py` | no | `reports/generation_report.md` — pass rates, fallbacks, coverage |
| `export_for_reading.py` | no | All explanations in one document, to read straight through |
| `verify_provenance.py` | no | **The release gate.** Traces every clinical sentence to its source; non-zero exit on any failure |
| `author_read.py` | no | Records that the author read an entry. No approve action — see below |
| `review_status.py` | no | Provenance and author-read coverage, reported separately |

### Model id

**Nothing hardcodes a model id in application source.** `_common.DEFAULT_MODEL`
reads `GEMINI_MODEL` from the environment, and every CLI takes `--model`. The
fallback default is `gemini-3.6-flash`, confirmed present in this project's own
`models.list()` output on **2026-07-23**.

Model ids change often and an id written from memory is a guess with a shelf
life. `list_models.py` is how you discover the current one; `preflight.py` fails
if the configured id is not in the key's list, so a stale id stops a run at the
gate rather than a third of the way through.

### Rate limits and throttling

Google no longer publishes free-tier RPM/TPM/RPD as fixed public numbers — the
rate-limit page redirects to a **per-project** dashboard at
<https://aistudio.google.com/rate-limit>. The real ceiling is therefore not
knowable from inside this repo, and the API does not return it.

The default is deliberately conservative:

| Setting | Value | Rationale |
| --- | --- | --- |
| `DEFAULT_DELAY_SECONDS` | `6.0` → **10 RPM** | Comfortably under every historical free tier |
| `BACKOFF_BASE_SECONDS` | `20.0`, doubling | 429 backoff: 20s, 40s, 80s, 160s |
| `MAX_RETRIES_ON_RATE_LIMIT` | `4` | Then the case falls back to the template and the run continues |

Override with `--delay` or `GEMINI_DELAY_SECONDS` **after** checking your own
dashboard. Expected volume for a full run:

- **Generation:** 20 reachable cases, 1 request each, plus 1 retry per guard
  failure → 20 minimum, 40 worst case. At 10 RPM: **2–4 minutes.**
- **Experiment:** 4 arms × 3 cases (`--cases`, default 3) → 12 requests.
  At 10 RPM: **~1.2 minutes.**

Both figures are what `--dry-run` prints, not estimates written by hand — check
them yourself before approving a spend.

### Observed on 2026-07-23 — the first real run, which mostly failed

These are measurements, not estimates. Both failure modes are worth knowing
before spending quota again.

| Observation | Detail |
| --- | --- |
| **Free-tier quota exhausted mid-run** | 4 of 12 experiment calls returned `429 RESOURCE_EXHAUSTED`. The 6s throttle does not help — this is a **daily** cap, not a per-minute one, and no delay setting evades it |
| **Truncated JSON on 5 of 12 calls** | `Invalid JSON: EOF while parsing a string at line 4 column 84`. **Not a parsing problem.** `gemini-3.6-flash` is a thinking model and reasoning tokens are drawn from `max_output_tokens`; the model spent the budget deliberating and the response was cut off mid-string |
| **Usable output: 3 of 12** | The generation run failed the same way and produced **zero** LLM explanations — its one attempted case fell back to the template |

Both are fixed in `app/explanation/generator_llm.py`:

- `MAX_OUTPUT_TOKENS` 2048 → **8192**
- `THINKING_BUDGET` → **0**. This task is not reasoning: the model composes prose
  from a closed context it may not add to, and the guard — not the model's
  deliberation — decides whether output is acceptable
- Truncation now raises a message naming the ceiling and the thinking-token
  count, rather than surfacing as a pydantic parse error. The misdiagnosis is
  what made the original failure expensive

**Before re-running:** check your own daily quota at
<https://aistudio.google.com/rate-limit>. A full run needs ~32 requests, and the
daily cap is what will stop you, not the rate.

### Resuming an interrupted run

Free-tier quota can stop a run at any point, so `explanations.json` is rewritten
atomically **after every single case**. An interrupted run has already saved
everything it generated.

```bash
python scripts/pregenerate_explanations.py --resume     # skip cases already present
python scripts/pregenerate_explanations.py --force      # regenerate everything
```

`--resume` keys on `drug:phenotype`. It skips exactly what is in the file and
generates exactly what is not — no duplicated spend, no silently skipped case.
This is covered by `TestResumeIdempotency` in
`backend/tests/test_phase5a_tooling.py`.

Useful narrowing flags:

| Flag | Effect |
| --- | --- |
| `--only <drug>` | One drug, e.g. after editing its mechanism file |
| `--only-phenotype <PM>` | One phenotype across all drugs |
| `--limit <n>` | Stop after n cases — the cheapest way to sample quality |
| `-v` | Print each generation and its guard verdict |
| `-o <path>` | Write elsewhere. Use this to diff before overwriting the real store |

---

## Reachability: 28 enumerated, 20 reachable, 8 not

`enumerate_cases.py` derives this from PharmCAT's own
`org/pharmgkb/pharmcat/phenotype/<GENE>.json`, not from an assumption. **6 drugs
× 6 phenotypes = 36 is fiction** — genes do not all have every phenotype.

Prose is **never** written for an unreachable case. Authoring text the pipeline
cannot produce would pad the coverage numbers with fiction; those cases are
documented instead, and fall back at runtime to a template that states plainly
that no recommendation was available.

| Unreachable | Count | Why |
| --- | --- | --- |
| codeine — IM, NM, PM, URM | 4 | CYP2D6 is **not callable from an unphased VCF**. Star alleles depend on structural and copy-number variation a VCF cannot express; PharmCAT reports `callSource=NONE` even with every definition position present |
| warfarin — IM, NM, PM | 3 | CPIC's warfarin guidance is a dosing **algorithm**, not per-phenotype text. There is no recommendation string to ground an explanation on |
| simvastatin — RM | 1 | SLCO1B1 is a transporter; CPIC has no increased-function row |

Every drug keeps a reachable **Unknown** case, because any gene can fail to call
and the system must have something honest to say when it does.

---

## Two traps this tooling exists to avoid

**Baked-in patient values.** Reviewed prose is reused across every patient
sharing a phenotype, so anything patient-specific must stay a slot
(`{diplotype}`, `{detected_variants}`, `{risk_label}`) filled at runtime. The
generation context therefore supplies the placeholder *strings themselves* —
not concrete values, which would bake one patient's genotype into everyone's
explanation, and not `None`, which would make the generator take its "nothing
was called" branch and assert that no genotype was found.

**Baked-in risk labels.** The risk label is derived from CPIC's *text* by the
rule engine, not from the phenotype. Clopidogrel + Poor Metaboliser is
`Ineffective`, which a phenotype-keyed guess would call `Adjust Dosage`.
Generation derives it with the production engine (`classify_annotation`), and
`{risk_label}` is a runtime slot — otherwise reviewed prose could contradict the
risk badge rendered directly above it.

---

## The guard

Every generation is checked before it is stored. A failure is retried once with
a stricter instruction naming the offending entities; a second failure falls
back to the deterministic template with `"fallback": true` and the reason
recorded. **Unguarded prose is never shipped.**

Two properties worth knowing:

**Matching is boundary-aware on purpose.** Naive substring matching silently
defeats the guard — an invented `50 mg` was once accepted because the mechanism
background contains "cytochrome P450", and `P450` contains `50`. See
`app/explanation/guard.py::_contains`.

**Build-time and request-time are different gates.** The build-time guard checks
prose against the CPIC context. Phase 4's runtime *slot verifier* separately
cross-checks the injected values against the response's own
`pharmacogenomic_profile`, and demotes to the template on mismatch.

`guard_experiment.py` evidences that this discriminates, by running four arms —
grounded, stripped, corrupted and coaxed — and recording what the guard did.

> ⚠️ **Experiment output is deliberately fabricated clinical text.** It exists
> to prove the guard works and is never served. The script asserts its output
> path is nowhere near `explanations.json` before writing, and
> `TestAdversarialArmsCaughtRealFabrication` re-checks that no experiment text
> reached the store.

---

## Regenerate when

- A mechanism file changes → `--only <that drug>`
- PharmCAT is upgraded → everything; new CPIC text may change derived labels
- A drug is added to the corpus → everything
- The prompt or `SYSTEM_INSTRUCTION` changes → everything; `prompt_hash` will
  differ, which is how a prompt change stays visible rather than remembered

**Re-verify after every regeneration.** Generated entries start with
`provenance_verified: false` — generation and verification are separate steps,
and an entry that certified itself would make the gate meaningless:

```bash
python scripts/verify_provenance.py --write
```

`read_by_author` is preserved across runs, because re-verifying is not
un-reading. `clinical_expert_review` stays `NOT_OBTAINED` permanently, and no
script in this directory can set it.
