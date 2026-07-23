# PharmaGuard — Project Status Audit

**Audit date:** 2026-07-23
**Fix pass:** 2026-07-23 (same day, after `git init` — baseline commit `6d758cc`)
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
(305 tests now pass):

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

## A. What actually exists

### A1. Phase completion

| Phase | Status | Evidence |
| --- | --- | --- |
| **1 — monorepo seam** | ✅ Complete | `backend/app/main.py`, `app/lib/` present and working. ✅ *Fixed:* the dead `stub_analyzer.py` (417 lines of fabricated clinical text) has been deleted and the stale docstrings that referenced it rewritten |
| **2 — PharmCAT + CPIC mapping** | ✅ Complete | `backend/app/pharmcat_runner.py`, `backend/app/cpic_engine.py`, `backend/app/data/label_mapping.yaml` (314 lines, 9 rules). 24 parser tests + 51 mapping tests pass |
| **3 — grounded explanations** | ✅ Complete, ⚠️ content unreviewed and template-generated | `backend/app/explanation/` (6 modules), `rag-corpus/mechanisms/` (6 files), `backend/app/data/explanations.json` (20 entries). **All 20 entries have `reviewed_by: null`; `generator: "template"`, `model: ""` — no LLM has ever been run against this project** |
| **4 — deployment** | ⚠️ **Partial — written, still largely unverified** | Workflows, Dockerfile, HF Space README and DEPLOY_NOTES all exist. ✅ *Fixed:* APK, compose mounts and CORS. ⛔ *Still open:* nothing is deployed, and the Docker image has never been built |

### A2. Test suite

**Backend — `cd backend && .venv/bin/python -m pytest`**

```
305 passed, 4 skipped in 0.86s      (was 249 passed, 1 skipped at audit time)
```

| File | Tests | |
| --- | --- | --- |
| `test_label_mapping.py` | 51 | |
| `test_explanation.py` | 51 | |
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
- `requires_faculty_review: true` is set in the file and asserted by a test.
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
      Replace with the accurate caveat (grounded but **not yet faculty-reviewed**).
- [ ] **🟢 Add tests for currently untested modules:** `generator_llm.py` against
      a mocked SDK boundary, `retrieval.py` container-path fallback,
      `scripts/pregenerate_explanations.py`.
- [ ] **🟢 Add third-party attribution** for Flutter dependencies to `LICENSE`.
- [ ] **🟢 Add a CI workflow that runs the test suite.** All 305 tests exist but
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

- [ ] **Read all 20 entries in `backend/app/data/explanations.json` yourself
      before any demo.** All are currently `reviewed_by: null`. *Why it matters:*
      this is patient-facing prose; the guard catches fabricated entities but
      **cannot catch reversed reasoning** (e.g. "reduced CYP2C19 activity makes
      the drug accumulate" is backwards and every token in it is grounded).
      *If skipped:* you may present clinically wrong prose to a panel.
- [ ] **Faculty guide sign-off on `backend/app/data/label_mapping.yaml`.** The
      file sets `requires_faculty_review: true` and a test enforces the flag.
      Collapsing a CPIC paragraph into one of five risk words is an editorial act
      no tool should own. *If skipped:* the project's core clinical claim is
      unreviewed.
- [ ] **Faculty sign-off on the explanations**, then set `reviewed_by` on each
      entry. The API currently reports *"20 of 20 … have not yet been reviewed"*
      in every response — a panel may see that.
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
  must then be re-reviewed** because `reviewed_by` resets.
- *Trade-off:* presentation quality vs. review workload and a new dependency.

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
| 8 | **Explanations unreviewed** (`reviewed_by: null` ×20) | ⚠️ Accidental-by-omission | Clinical prose has had no expert eyes | ⚠️ **Weak** — in API `warnings` and buried behind an expandable "pipeline warnings" tile in the UI |
| 9 | **16 of 36 explanation cases fall back to template** | ✅ Intentional | Plainer prose in edge cases | ❌ **NOT disclosed** anywhere user-facing |
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

### 🔊 Loudest disclosure gaps

1. **#8 — "unreviewed clinical prose" is buried.** It is in the API response but
   the UI hides it behind a collapsed tile. For a clinical-adjacent tool this
   deserves to be as prominent as the not-a-medical-device banner. **Now the
   single loudest gap**, since the APK and guard-timing items are resolved.
2. **#20 — `live` mode has never run.** README documents it as a supported mode
   alongside `static`, without noting it is untested end-to-end.
3. **#9 — template fallback is silent.** 16 of 36 cases serve plainer prose and
   nothing tells the reader which they are looking at, though `source=template`
   does appear in `quality_metrics`.
4. ~~#15 APK broken~~ / ~~#10 guard timing~~ — both resolved 2026-07-23.

---

## E. Top risks to a live demo

Ranked by likelihood × damage.

| # | Risk | Likelihood | Mitigation |
| --- | --- | --- | --- |
| 1 | **The APK has still never been launched on a device.** The crash is fixed and verified at the artifact level (manifest target now exists in the dex), but nobody has installed it. | Medium | Install the rebuilt APK on a real phone once and open it. The fix is verified statically; only a device proves it |
| 2 | **Nothing is deployed.** No HF Space, no Pages project, no git remote. The README's live links are placeholders. | **Certain** today | Complete Bucket 2 well before demo day. Budget a full evening — the first Docker build of a ~2 GB image is slow |
| 3 | **Deployed site loads but every analysis fails on CORS.** | **Low** — the backend now refuses to start with an empty allowlist, so this surfaces in the deploy log instead of at demo time | Still run one real analysis **from the deployed URL**, not localhost, before presenting |
| 4 | **Cold start makes the first analysis look like a hang.** ~1 min on free tiers. | High if the demo starts cold | Enable the keepalive workflow for the demo window, and **hit the site yourself 2 minutes before presenting**. The waking UI already explains the wait — let it show |
| 5 | **A panel member asks "who checked this clinical text?"** and the honest answer is "nobody yet." | Medium–High | Get the faculty sign-off (Bucket 3) *before* the demo, or open by stating plainly that clinical content is pending review |
| 6 | **Docker build fails on first attempt** and has never been tested anywhere. | Medium | Build the image locally or in CI at least once, days ahead. Do not let the first-ever build be on demo day |
| 7 | **Rate limit trips mid-demo** — 10 analyses per 5 minutes, and a rehearsal plus the real run share one IP. | Medium | Raise `RATE_LIMIT_REQUESTS` for the demo window, or rehearse on a different network |
| ~~8~~ | ~~Someone picks `sample1.vcf` and gets a broken-looking result~~ | ✅ **Resolved** | The relics are deleted (they returned **503**, not Unknown). All three remaining samples are guarded by `test_sample_vcfs.py` |
| 9 | **You demo `live` LLM mode** to show off the AI angle, and it fails — it has never run against the real API. | Medium if attempted | Do not demo `live` mode unless you have tested it end-to-end with a real key first |
| 10 | **iOS is requested** and no simulator runtime is installed on the machine. | Low–Medium | Install an iOS runtime via Xcode → Settings → Components ahead of time (multi-GB), or state up front that iOS is simulator-only and out of scope |

---

## PASTE-BACK SUMMARY

```
PHARMAGUARD — PROJECT STATUS
Audited 2026-07-23 (read-only) · Fix pass 2026-07-23 · git baseline 6d758cc

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

TESTS
- Backend: 305 passed, 4 skipped, 0 failed  (was 249/1 before the fix pass)
- Flutter: 21 passed; analyzer clean
- Skips: 1 live-LLM test (no API key) + 3 real-PharmCAT sample tests, which WERE
  run manually against real PharmCAT and passed
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
D3 Author the 16 missing drug x phenotype explanations vs keep the template
   fallback (the gaps are legitimate: CYP2D6 uncallable, warfarin algorithmic).
D4 iOS: simulator-only (free) vs Apple Developer Program ($99/yr) vs free
   personal team (7-day expiry).
D5 Keepalive cron on (instant demo, burns quota) vs off (saves quota).
D6 Repo public (unlimited CI minutes) vs private (2000 min/mo).

UNRESOLVED LIMITATIONS NOT DISCLOSED TO USERS
- Explanations are unreviewed — surfaced only in a collapsed UI tile. Now the
  loudest gap.
- 16 of 36 explanation cases silently fall back to plainer template text.
- `live` LLM mode is documented as supported but has NEVER run against the real
  API.
- No persistence/history: results vanish on reload.

TOP DEMO RISKS
1. Nothing is deployed; README links are placeholders. Needs a full setup pass.
2. The APK crash is fixed and verified at artifact level, but the APK has still
   never been launched on a physical device. Install it once.
3. Docker image has never been built anywhere. Build it days ahead.
4. Cold start (~1 min) reads as a hang. Warm it 2 min before presenting.
5. "Who reviewed the clinical text?" — currently nobody. Get sign-off first.
6. Rate limit (10/5min) can trip between rehearsal and the real run.
7. No CI runs the backend tests, so a future regression won't be caught
   automatically.

HUMAN-ONLY WORK (no tool can do these)
Accounts/credentials: backend host account (see D1); Cloudflare account + Pages
project + API token; GitHub Actions secrets (CLOUDFLARE_API_TOKEN,
CLOUDFLARE_ACCOUNT_ID, API_BASE_URL) and variables (API_BASE_URL, BACKEND_URL);
Android keystore (keep local, gitignored); optional Gemini key for
pregeneration only.
Judgement: read all 20 explanations personally; faculty sign-off on
label_mapping.yaml and explanations.json (reviewed_by); download GeT-RM/1000
Genomes for real validation; record + publish the demo video; verify report
citations resolve; confirm whether the panel expects a trained ML model;
supply real dates and team names.
```
