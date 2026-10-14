# Prompt 8: verify the current build, demonstrate multiple VCFs, fix reproduced defects

Run 2026-10-14 11:12 UTC to 2026-10-14 19:05 UTC, on `main` at `1dc7557` with the dirty tree as the candidate. Paths are relative to this directory unless they start at the repository root. No clinical validation is claimed, and this report gives no numerical project score.

## Verdicts

| Question | Verdict | Basis |
|---|---|---|
| Does the local candidate build and pass every required check? | **PASS** | All six required gate checks exit 0 on the exact tested artifact (`tests/release-gate.stdout`). Backend 925 collected: 923 passed, 0 failed, 2 skipped. Flutter 220 passed. Analyzer clean |
| Do multiple VCF classes behave as documented, end to end? | **PASS** | 16 fixture classes; 16/16 API rows match the expectations frozen before evaluation; 15/15 real-Chrome cases on the final2 build, plus 3/3 again on the final build (`verification/case-matrix.md`) |
| Do exports and print match the API? | **PASS** | Download = clipboard = API after the one documented transform, 13/13 cases. 13 native Save-as-PDF summaries (5 baseline, 5 on final2, 3 on the final build) with the research header on every page and no intended field missing. All pages inspected |
| Were the reported defects real, and are they fixed? | **6 reproduced, 6 fixed**, plus one follow-up consistency fix | Red→green regression tests; repeated API, browser and print reproduction (`DEFECTS.md`) |
| Release ready? | **NOT READY** | `release_status.py` exit 1, blocked only by human prerequisites: adjudication 19 outstanding, 0/20 explanation entries approved, clinical expert review NOT_OBTAINED |
| Clinical validity | **Not claimed** | The two read-backed controls are bounded positives. The 208-person evaluation reused cached upstream reports and is not a fresh caller run |

## 1. Start state

- `start/START-STATE.json`: HEAD `1dc7557da49f38e831b382545044b00a481507b6`, tracked diff SHA-256 `4fc44c3c…` (equal to Prompt 7's final), 437/437 entries byte-identical to the Prompt 7 frozen candidate inventory, 0 differences. No `AGENTS.md` exists.
- Prior reports read: `Final-Scientific-Audit.md`, `FINAL-REAL-WORLD-ACCEPTANCE-REPORT.md`, `audit-output/2026-10-02-final/FINAL-POST-REMEDIATION-VERIFICATION.md`, Prompt 7 `PROMPT-7-REPORT.md` and `NEW-FINDINGS.md`.

## 2. Runtime

The real backend used the pinned PharmCAT 3.4.0 JAR (`9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741`, data 2026-07-13-11-40), JDK 17.0.17, `STRICT_PHARMCAT=1`, static explanations, and CORS from `infra/local-dev.env`, on 127.0.0.1:8000. A passive capture wrapper outside production code recorded the response bytes and the SHA-256 of each uploaded file (`capture_api.py`). The web side was a Flutter 3.38.9 release build served on 127.0.0.1:3000. The browser was a task-owned Google Chrome 155 with an isolated profile kept outside the repository. Uploads went through the browser's own file-chooser event, which CDP fulfilled with the fixture path. Downloads, the clipboard and kiosk Save-as-PDF came from the UI buttons (`browser/cdp_agent.mjs`, `browser/run_cases.py`). PharmCAT was not mocked. Server receipts are in `servers/`.

One external actor clicked in the first Chrome window. That run was discarded (`browser/baseline/`, marked exploratory). Later runs used an off-screen window and a per-case guard that compares the analyze requests the server saw with the clicks the script issued. Every recorded case reports `external_interference: false`.

## 3. Fixtures and pipeline comparison

`fixtures/EVIDENCE-TABLE.json` (SHA-256 `9015cb61…`) froze 16 fixtures and their expected outcomes before any evaluation:

- 4 synthetic: normal, CYP2C19 PM, DPYD carrier, and the bundled normal used for scope abstention.
- 2 read-backed real controls: F4 NA18526 and NA12878.
- Real or derived degradations: variant-only, failed FILTER, partial GT, missing required position, missing TPMT, missing NUDT15.
- A real incomplete 1000 Genomes sample.
- The official PharmCAT tutorial preprocessed output.
- An oversized bgzip and a truncated gzip.

For each fixture the chain input → PharmCAT (run directly with the same JAR) → parser and coverage → phenotype → drug result → explanation → API → browser → export was compared (`api_harness.py`, `api-harness-*/results.json`). The direct caller still reports CYP2C19 `*1/*2` for the variant-only, failed-FILTER, partial and missing-position files, while the application abstains (Unknown). That is the intended protective gate. The CVI ACS PCI population qualifier stays in the CYP2C19 quoted CPIC text.

| Case | Class | API coverage/analyze | Result (identical before and after the fixes) | Browser | Export | Native print |
|---|---|---|---|---|---|---|
| D01 | synthetic normal | 200/200 | 4 drugs no adjustment; warfarin and codeine Unknown | 200/200 | parity | — |
| D02 | synthetic CYP2C19 \*2/\*2 | 200/200 | clopidogrel Ineffective (PM) + ACS/PCI | 200/200 | parity | 4 pp |
| D03 | synthetic DPYD carrier | 200/200 | fluorouracil Adjust Dosage (IM) | 200/200 | parity | — |
| D04 | real NA18526 read-backed | 200/200 | clopidogrel no adjustment (\*1/\*1, NM); rest Unknown | 200/200 | parity | — |
| D05 | real NA12878 read-backed | 200/200 | clopidogrel Ineffective (\*1/\*2, IM) + ACS/PCI; rest Unknown | 200/200 | parity | 5 pp (final2), 5 pp (final) |
| D06 | real variant-only | 200/200 | all Unknown (direct caller: \*1/\*2) | 200/200 | parity | — |
| D07 | real incomplete 1000G | 200/200 | all Unknown | 200/200 | parity | 5 pp |
| D08 | oversized bgzip | 413/413 FILE_TOO_LARGE | rejected | 413/413, recovery 200 | n/a | — |
| D09 | truncated gzip | 400/400 CORRUPT_GZIP | rejected | 400/400, recovery 200 | n/a | — |
| D10 | failed FILTER at CYP2C19 core | 200/200 | all Unknown (caller: \*1/\*2) | 200/200 | parity | 5 pp (final2), 5 pp (final) |
| D11 | partial GT | 200/200 | all Unknown | 200/200 | parity | — |
| D12 | missing required position | 200/200 | all Unknown | 200/200 | parity | — |
| D13 | missing TPMT | 200/200 | azathioprine Unknown; others answer | 200/200 | parity | — |
| D14 | missing NUDT15 | 200/200 | azathioprine Unknown; others answer | 200/200 | parity | — |
| D15 | scope abstention (157/157 CYP2D6) | 200/200 | clopidogrel answers; ibuprofen, codeine, warfarin Unknown | 200/200 | parity | 3 pp (final2), 3 pp (final) |
| D16 | official tutorial preprocessed | 200/200 | all Unknown | API only | n/a | — |

`verification/case-matrix.md` and `.json` hold the full matrix, with fixture hashes, caller calls and every drug label. `build_matrix.py` rebuilds it from the recorded artifacts. It checks exact labels, diplotype and phenotype where the expectation names them, the ACS/PCI qualifier, typed error codes, browser = API status, recovery, export parity and print completeness. Result: 16/16 PASS, and no label changed against the baseline.

## 4. UX, exports, clipboard and print

- Uploads: every multipart file the server received hashed to its fixture. The bytes the browser received equal the bytes the server sent (`verification/exports-*.json`: `all_uploads_bound`, `all_api_bytes_match_browser`).
- Export JSON and Copy JSON: in 13/13 analysed cases (baseline and final2), the download equals the system clipboard byte for byte. Both equal the API response after the one documented transform: drop `confidence_score`/`severity`, add `assessment_scope` and `application_capability`. A deliberately broken comparison failed, which shows the check is not vacuous. The headless final-build rerun could not read the OS clipboard, so for it only the download was compared (`clipboard_checked: false`).
- Print: Printable summary → kiosk Save as PDF. Baseline: 5 PDFs (`verification/print-baseline.json`). final2: 5 PDFs (`print-final.json`). Final build: D05, D10 and D15 (`print-final4.json`, PDFs under `browser/run-final4-print/cases/`; the page contact sheets were inspected locally and are not committed). Every page carries the research header, no intended field is missing, and no clipping was seen on any page. By policy the summary omits pipeline warnings, mechanism, variant rationale, patient-friendly text and detected variants; the verifier lists these and does not call them parity.
- Opened result cards now stay open after a long scroll: `browser/run-final3/def5/repro.json` on the final build. Before the fix, every card collapsed (`browser/run-baseline/def5/`).

## 5. Defects

`DEFECTS.md` has the reproduction (recorded before any change), the violated invariant, the intended contract and the after-state.

| ID | Defect | Fix |
|---|---|---|
| DEF-1 | Disclaimer, warning, About page, home subtitle and print described automated provenance as verification that "nothing was invented". 0/20 entries are approved, and the served text is the deterministic template | States that no clinical expert reviewed the text, that recommendation text is quoted from CPIC via PharmCAT, and that automated source checks are not human review and cannot show that every statement is supported or correct for the person |
| DEF-2 | The app's CYP2D6 limit was described as a limit of the VCF format ("no VCF will resolve it"). VCF 4.3 §5.3 encodes SV/CNV, and PharmCAT accepts outside CYP2D6 calls (`sources/source-receipts.json`) | Now: "not called from an uploaded VCF by this application". Codeine stays Unknown |
| DEF-3 | The missing-is-reference hazard of genotype callers was worded as this application's output, shown on responses where every drug is Unknown | Attributed to genotype callers, and the text states that this app reports such genes as Unknown |
| DEF-4 | Present-but-unusable genotypes (failed FILTER, partial call) were explained as "not reported", with an "emit all sites" remedy | New `unusableGenotypes` reason, classified from the API's typed `evidence_counts`. Census, panel and print wording updated, with a re-call remedy |
| DEF-5 | Opened result cards collapsed after a long scroll (lazy list without keep-alive) | `AutomaticKeepAliveClientMixin` on `SummaryGrid` and `DisclosureRow` while open; nothing visible changes |
| DEF-6 | Warfarin and codeine were listed under "Drugs with CPIC guidance in this build" | Caption names the build's scope and says both always return Unknown |
| Follow-up | Print intro said "only one" Unknown reason is actionable; after DEF-4 two are | Sentence corrected; red→green test; verified in the final-build PDFs |

Process for each defect:

1. Reproduce through the API, the browser and the print.
2. Preserve the evidence.
3. Write the invariant.
4. Write a regression test and see it fail (`regression/*-red.stdout`).
5. Make the minimal change.
6. Run targeted, then full suites.
7. Repeat the reproduction.
8. Inspect the diff.

Assertions in seven existing test files were rewritten. Six of the files encoded the defective wording; one counted the reasons and moved from 5 to 6. Every one is listed in `DEFECTS.md`. No check was skipped, disabled or marked xfail, and no expected hash was patched.

## 6. Diff summary

`diff/task-changes.patch` is diffed against byte-verified start snapshots and indexed in `diff/task-changes.json`. It covers 30 files, +880/−175:

- **Product code (13 files):** `backend/app/{models,main,coverage}.py`; `app/lib/config.dart`; `models/{analysis,unknown_reason}.dart`; `print/summary_document.dart`; `screens/{about,home}_screen.dart`; `widgets/{coverage_census,disclosure_row,file_readiness,summary_grid,unknown_panel,unknown_reason_panel,verdict_card}.dart`.
- **Tests:** 2 new files, `backend/tests/test_disclosure_wording.py` (4 tests) and `app/test/disclosure_wording_test.dart` (16 tests). 7 existing test files updated.
- **Controlled evidence refresh:** `scripts/compatible_bundle.py`, `scripts/release_status.py`, two identity tests, and the rebuilt `backend/app/data/compatible_bundle.json`. Plus the new package `test-data/benchmark/current-candidate-2026-10-14/` (11 files).

Genes, drugs, labels, thresholds, biological definitions and the PharmCAT version are unchanged. Colours, typography, spacing, layout, icons and the component hierarchy are unchanged; one existing icon is reused for the new reason.

## 7. Controlled evidence refresh

The fixes touched files inside the scientific-core allowlist, so the core hash moved from `38451a56…` (start) through `790a9188…` (fixes, used for the final2 runs) to `bd20329df0c975a549f91640b785e35b9c5a7fe2afd081ea585413463c29a38f` (final, after the print-intro sentence). The previous evaluation therefore no longer bound the candidate. Following the Prompt 5 pattern:

1. An isolated copy (deleted afterwards; receipt `refresh/evaluation-copy-deleted.json`) re-projected all 208 cohort individuals from the 208 cached PharmCAT reports. All report hashes, the combined VCF, JAR, truth table, workbook and cohort lock were verified first. 0 new caller runs.
2. All 1,456 sample-gene rows were rescored.
3. The two F4 controls were replayed through the live API and the pinned caller: 2/2 passed, 18 checks.

Metrics, exclusions and discrepancies equal both the historical run and the 2026-10-04 evaluation. The only differences are `generated_at` and a temporary-file `vcf_sha256` that is path-dependent (`refresh/evaluation-comparison.json`). The package was published as `pharmaguard-external-current-candidate-v3-2026-10-14`, and the manifest was rebuilt through `scripts/build_compatible_bundle.py`. The 2026-10-04 package and the historical benchmark are byte-identical to before. The previous manifest is preserved at `refresh/historical-compatible_bundle-2026-10-04-v3.json`.

## 8. Tests, validators and gate

| Check | Result | Artifact |
|---|---|---|
| Backend pytest | 925 collected, 923 passed, 0 failed, 2 skipped (README no longer quotes a test count; no glossary decisions recorded yet) | `tests/backend-final.xml` |
| Flutter tests | 220 passed | `regression/flutter-full-after-print-intro.stdout`, gate `flutter-tests` |
| Flutter analyze | No issues found | gate `flutter-analyze` |
| Provenance validator | exit 0; 106/106 clinical assertions in stored entries trace to a cited source | gate `provenance` |
| Label mapping | exit 0; 13 divergences, all in the accepted baseline | gate `label-mapping` |
| Adjudication | exit 1; 179 flagged, 160 adjudicated, 19 escalated and outstanding, 0 rejected | `tests/adjudication.stdout` |
| Review | exit 0; author-read 0/20; clinical expert review NOT_OBTAINED | `tests/review.stdout` |
| Compatible bundle | PASS, `pharmaguard-scientific-current-candidate-2026-10-14-v4` | gate `compatible-bundle` |
| `git diff --check` | clean | `tests/git-diff-check.stdout` |
| `release_status.py --run-required --candidate-sha 1dc7557…` | exit 1, `not-ready`. All required checks passed; candidate = tested artifact | `tests/release-gate.stdout` |

## 9. Identities

| Item | Value |
|---|---|
| Base HEAD | `1dc7557da49f38e831b382545044b00a481507b6` |
| Scientific core (policy v2), start → final | `38451a563c6f6cfb52257626d41700eeff3a5621ebe91b3358f878b375a6a691` → `bd20329df0c975a549f91640b785e35b9c5a7fe2afd081ea585413463c29a38f` |
| Release artifact (candidate = tested) | `dd013a622416808744267f683cd3a538be9bdbc8c149d399e277315b3e5ec0dc` |
| Compatible bundle manifest | `c97059611776d460a1df9c50d62d5c27eb87e8621a1abdba0c22e0efc8b20a88` (previous `963a039ba16690d1c6ed772268ebb5c1512275beeb5fa117a6bef1c03aae7600`, preserved) |
| Evaluation manifest | `ef3202f4f159548b93f4353b00802bd5bf53c300f3633e3233d604988d879786` |
| Explanation store | `35cb17a98fd2a885da9f14264da647b9923c75481bc7e02eff9c433fea2c59e8` (unchanged) |
| PharmCAT JAR | `9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741` (3.4.0) |

## 10. Human prerequisites (not performed, not simulated)

1. Adjudicate the 19 escalated sentences (`scripts/adjudicate_claims.py`).
2. Read and approve the stored explanation entries, bound to a named human. Currently 0/20, so every response uses the deterministic template.
3. Obtain clinical expert review, if one is ever to be claimed. Status is NOT_OBTAINED.
4. Provision CI with the gitignored pinned artifacts that the identity checks hash: `test-data/reference/tools/pharmcat-3.4.0-all.jar`, the PharmCAT positions file and index, `test-data/benchmark/external/genomic/locked_cohort.vcf.gz` and the cached reports. Without them the hosted gate cannot reproduce the local PASS on required checks; it fails closed.
5. Owner decisions on the observations listed in `DEFECTS.md` (headline wording, raw Markdown in corpus text, the local "free shared CPU" message, the explanation-date stamp, `/ready` counts, "Answers confidently", the low-coverage "reported as safe" wording).

## 11. Cleanup

All task-owned servers and Chrome instances were stopped; their exit receipts are in `servers/` and `browser/run-*/chrome-exit.json`. The scratch Chrome profiles and the 555 MB isolated evaluation copy were deleted. The system clipboard may still hold a test JSON export from the final2 run. Build outputs (`builds/`, 128 MB), raw harness outputs, `fixtures/inputs/` (it includes an 11 MB bgzip) and full screenshot sets stay on disk and are not committed.

Files that other actors created during this run were not touched and not committed: `test-data/vcf-library-2026-10-14/` and its `.zip`, `output/repo-comparison-2026-10-14/`, `output/PharmaGuard_Project_Report.docx`, `tmp/college-report/`, `tmp/college-ppt/`.
