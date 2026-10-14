# Final post-remediation release verification

Finalized 3 October 2026 (Asia/Kolkata). Workload/test execution and primary-source refresh: 2 October 2026; final gate/freeze/cleanup check: 3 October. The directory retains its execution-date name.

# FAIL / NOT READY

The authoritative release gate returns exit 1, `release_ready=false`, `state=not-ready`, `content_ready=false`. Human review is incomplete and the compatible-bundle manifest no longer identifies the current scientific application. The live-backend suite has three failures. Browser JSON download now works, but clipboard and printed-output parity remain inconclusive. Passing component tests do not override these release blockers.

No candidate source, UI, clinical policy, evidence threshold, approval, manifest, or historical benchmark was changed during this verification. All 421 frozen intended files remained byte-identical. New verification scripts, receipts, results, and this report are confined to this audit directory. Isolated negative-test changes were restored. No human or clinical-expert review was performed or inferred.

This was an automated scientific/source and execution review, not clinical validation. Primary sources were checked directly; a dedicated Deep Research session/model switch was not available, and is not claimed.

## 1. F1–F7 acceptance matrix

Previous status below means the latest local remediation evidence before this verification, not a claim that every earlier finding had closed. Strict current status assesses the complete requested criterion, not just its repaired mechanism.

| Finding | Previous status | Current status | Evidence |
|---|---|---|---|
| F1 explanation/release approval | FAIL — runtime blocked unresolved prose, but required review incomplete | FAIL | 12 approval tests and 12 release-status tests pass; zero releasable generated entries; 55 claim decisions still require human action and 20 entries lack author-read approval. Declared all-stored-entry review policy still blocks release. |
| F2 portable scientific hash | FAIL — portability implemented, later F5/F6 bytes invalidated candidate manifest | FAIL | Hash itself is portable: baseline/copy/junk/restored identities agree; scientific mutations change it. Clean-copy compatibility still fails. 16 portable-hash tests pass, one fails against stale manifest. |
| F3 CYP2C19 definition metadata | PASS — known version delta recorded | PASS | Pinned 3.4.0/2026-07-13 data retains older companion constraints; live PharmVar PV03110 is newer. Manifest correctly says `not_included_in_pinned_bundle`; no biological rule patch. |
| F4 read-backed real guidance | PASS — two bounded CYP2C19 cases | PASS | Frozen protocol/read hashes checked; bcftools replay reproduces every normalized record; both real samples have 35/35 qualified positions. Independent diplotypes, PharmCAT, parser, API, browser, and saved JSON agree for the bounded pathway. |
| F5 512 MiB operation | PASS for recorded Linux/arm64 constrained workload | PASS for tested Linux/arm64 configuration | Fresh image build and workload: peak 496.46 MiB; no OOM or cgroup limit events; one JVM; timeout/cancellation cleanup verified. Not an AMD64-host or deployment claim. |
| F6 browser acceptance | FAIL — prior browser download cancellation, parity incomplete | INCONCLUSIVE | Actual chooser/upload, readiness, normal/actionable/Unknown, oversized rejection, scope warning, scrolling and saved JSON pass. Earlier download cancellation not reproduced. Clipboard read-back and exact printed summary remain unverified. |
| F7 NA18861 attribution | PASS — C/D nomenclature/definition-era attribution documented | PASS | Primary paper explicitly attributes this sample's *14/*43 difference to later nomenclature. Fresh PharmCAT/parser retain *1/*43 and application remains Unknown; old truth is unchanged. No complete read-backed NA18861 rerun claimed. |

Evidence entry points: [test summary](test-summary.json), [gate](release-gate-final.stdout), [real comparisons](real-truth-comparison.json), [read replay](read-replay.json), [container summary](container-summary.json), [export parity](browser-export-parity.json), and [F7 attribution](../2026-10-01-f7/attribution.json).

## 2. Exact candidate and release gate

The local dirty working tree is authoritative; HEAD alone is not the tested candidate.

| Identity | Value |
|---|---|
| Branch / base HEAD | `main` / `1dc7557da49f38e831b382545044b00a481507b6` |
| Frozen intended file count | 421 |
| Scientific application SHA-256 | `38451a563c6f6cfb52257626d41700eeff3a5621ebe91b3358f878b375a6a691` |
| Release-artifact SHA-256 | `9961033924dda2d4ab8e57d85450debeb98c4afdc392b3959d3d0ccf856f214c` |
| Checked manifest SHA-256 | `718dbcf0480d8d73a40ff1356ef65962440a43acae24c781eaeeba232e95c7a8` |
| Manifest's expected scientific SHA-256 | `204c315389f97f8de688b8ac3219bcc27f0a95c6e8c699fc50fd8b0df361725c` |
| Bundle identity | `pharmaguard-scientific-baseline-2026-09-24-portable-v2` |

Exact command, from repository root:

```sh
backend/.venv/bin/python scripts/release_status.py --run-required --candidate-sha 1dc7557da49f38e831b382545044b00a481507b6 --json
```

The gate fails closed at `compatible-bundle`; it does not run subsequent required commands after that failure. Those commands were therefore also run independently, with results below. They must not be represented as a successful gate run. Both initial and final gate receipts are retained.

| Gate content field | Actual result |
|---|---|
| Declared release policy | `human_review_all_stored_generated_entries` |
| Effective explanation mode | `deterministic_template_only` |
| Approved generated entries | 0 |
| Unapproved generated entries | 20 |
| Releasable generated entries | 0 |
| Fallback-only cases | 20 stored-context cases; not a count of every possible patient input |
| Human review complete for releasable set | `null` — empty eligible set does not establish review completion |
| Clinical expert review | `NOT_OBTAINED` |
| Outstanding claims | 19 |
| Recorded human / automated decisions | 124 / 36 — automated decisions remain automated |
| Entry-level author-read approvals | 0/20 |
| Explanation hash/context manifest compatibility | true |
| Scientific bundle compatibility | false |
| Tested/candidate revision and artifact agreement | true |
| Final release status | NOT READY |

Before remediation, stored prose and the release approval surface were insufficiently distinguished in reporting. Now the shared approval function, exact-content/source/context binding, explicit eligible-set counts, and fallback mode make that distinction enforceable. The policy still requires human review of all stored generated entries. It was not silently changed to allow a template-only release, and deterministic templates are not described here as human- or expert-reviewed.

The runtime and gate share `approval.evaluate`. Passing regressions cover unresolved/rejected/automated-only entries; content and source mutations; wrong gene context, phenotype and source row; fabricated expert-review claims; and an approved compatible fixture. Approval fixtures in tests are not real human approvals. Current public-input runs explicitly report template fallback.

Remaining owner work is enumerated in [the existing review packet](../../reports/release_content_review.md): 19 unresolved plus 36 automated-only claims require genuine human decisions; all 20 entries require exact-content author-read review. Candidate source spans are retrieval aids, not proof of support. Any edits must invalidate prior approval bindings. If the owner wants a different template-only release policy, that requires an explicit separate policy decision, not a gate bypass.

## 3. Clean-copy reproducibility and deliberate negative tests

An isolated copy was built from the enumerated intended-file inventory plus the pinned JAR and position artifacts, without `.git`, environment files, caches, audit output, or unrelated untracked files. Its exact `render.yaml` symlink to `infra/render.yaml` was preserved. There was no clean-checkout substitution of HEAD for the dirty candidate.

Hash policy v2 uses an explicit 90-path scientific allowlist: SHA-256 of the UTF-8 domain and NUL, followed by lexical POSIX relative path, NUL, raw bytes, NUL for each file. Relative paths and raw bytes are independent of parent directory and OS path separator. The self-referential bundle manifest is separately included in release identity. Policy changes are versioned; old and new hashes are not equated.

| Isolated check | Result |
|---|---|
| Clean intended tree in another parent directory | Same scientific/release/component hashes as working candidate |
| Add `.DS_Store`, editor backup, `__pycache__` artifact, log, temporary file | Scientific and release identities unchanged |
| Mutate scientific `cpic_engine.py` bytes | Scientific SHA changes to `14a4e3c9f54fad63cbebb5ccc624fc3b2460e4cf02f7b578cfb26483e03e180b`; gate exit 1 |
| Replace an explanation summary with deliberately invalid unreviewed prose | Scientific SHA changes to `23330f22dc0bf71b06c42478bbafb6a3855067136c09eff8d8f0805e8b0c9abf`; gate exit 1; explanation-manifest compatibility changes from true to false; zero releasable generated entries |
| Restore both mutations and remove only test-created junk | Exact baseline scientific/release/component identities restored |
| Clean-copy bundle compatibility | FAIL: same stale scientific hash and historical migration mismatch as original candidate |

The invalid-prose gate names both `approval manifest and explanation-store hashes differ` and `content hash mismatch: azathioprine/IM`. This is a new content-specific rejection, not merely the pre-existing stale-bundle rejection. Because the baseline release was already blocked, this is not presented as a successful release turning unsuccessful.

Regression tests additionally demonstrate capability-registry, position-requirements, explanation-content and scientific-source sensitivity; same bytes under different parents; ignored unlisted junk; and fail-closed scientific symlinks. Clean-copy test J remains failed until legitimate current-candidate evidence/manifest reconciliation is performed.

Key portable component hashes:

| Component | SHA-256 |
|---|---|
| Explanation store | `35cb17a98fd2a885da9f14264da647b9923c75481bc7e02eff9c433fea2c59e8` |
| Approval manifest | `b18c7d1d18d014fd1b2edf8ac24e2339a0c1df3f4252590c77db264df799f8a7` |
| Capability registry | `287a319b8ca1fdac9e765d7b6ec7de55ea8ee87cd3d142700be0b7601d2c1704` |
| PharmCAT JAR | `9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741` |

## 4. Real-world positive acceptance

The F4 protocol was frozen before calling/scoring, on 30 September. It selected NA18526 and NA12878 by independent truth and public read availability, not by application success. No sample substitution or quality-policy tuning occurred. Public ENA/NYGC GRCh38 read slices, reference identity, tool versions, acquisition accessions, commands, FILTER/DP/GQ/AD/GT evidence and checksums remain in the [F4 protocol/package](../2026-09-30-f4/PROTOCOL.md).

| Stage | Real normal: NA18526 | Real actionable: NA12878 |
|---|---|---|
| Independent CDC GeT-RM genotype | CYP2C19 `*1/*1` | CYP2C19 `*1/*2` |
| Read accession | ERR3239353 | ERR3239334 |
| Qualified required positions | 35/35, DP 21–42 | 35/35, DP 15–41 |
| PharmCAT 3.4.0 | `*1/*1`, normal metabolizer | `*1/*2`, intermediate metabolizer |
| Application parser/API | Same diplotype, NM | Same diplotype, IM |
| Clopidogrel result | No PGx-guided adjustment identified | Ineffective category, with the ACS/PCI guideline qualifier retained |
| Explanation | Deterministic template; no stored unresolved prose | Deterministic template; no stored unresolved prose |
| Browser / saved JSON | Same scientific content | Same scientific content |
| Discrepancy in evaluated pathway | None found | None found |

The read-backed workflow was genuinely rerun from preserved BAM slices using bcftools 1.24, its frozen commands and the verified chr10 reference. All 93,030/93,033 normalized VCF record lines respectively match the original call output, including genotype and quality fields; only header run paths/timestamps differ. The 35 target records in each sample remain genuinely observed. No absent genotype was filled as `0/0`.

Observed-VCF SHA-256:

- NA18526: `9829ae37bb8d5ecb5b5e93cc720ee795df8a5efcb850f5b8ca2b47d65d246548`.
- NA12878: `92d54bcaafb1ae065cbe38f1c333f5d72fd40ee263161ee431643975c9cca1a7`.

The independent truth is a star-allele consensus, not independent per-base truth for all 35 positions. Phenotype/action direction is compared separately against the [CPIC 2022 CYP2C19/clopidogrel guideline](https://pmc.ncbi.nlm.nih.gov/articles/PMC9287492/). The actionable comparison uses a hypothetical ACS/PCI context: it does not assert that a donor has that indication or that a drug actually failed. The application lacks patient-indication selection. No paired real TPMT/NUDT15, structural-variant, CYP2D6, warfarin-dose, other-pathway positive validation, population accuracy, or clinical utility is established by these two cases.

Full source CRAMs were not downloaded or locally whole-file-checksummed. Archive checksums are distinguished from verified local slice/reference hashes. Raw BAM/reference files remain local acquisition artifacts, not proposed Git additions.

## 5. Negative acceptance and monotonic evidence

Fresh `/coverage` and `/analyze` requests reconfirmed:

| Case | Result |
|---|---|
| Incomplete real NA18526 public VCF | No answerable pathway; final drugs Unknown; missing-evidence warning |
| Variant-only degradation of observed NA12878 | Unknown; no reference synthesis |
| Failed FILTER at required position | Unknown |
| Partial `0/.` genotype | Unknown |
| Remove required position | Unknown |
| Remove TPMT or NUDT15 partner from complete synthetic input | Azathioprine Unknown |
| Unsupported ibuprofen / atorvastatin | Unknown; no fabricated CPIC authority |
| CYP2D6/codeine | Unknown; no CYP2D6 calling added |
| Warfarin | Unknown; no dose calculation |
| Oversized real public file | HTTP 413 / clear 5 MB UI error; controls recover |

These are degradation-only transformations; reducing observed evidence did not increase final certainty. The legacy live demo test's expectation that incomplete input still exposes `*2/*2` conflicts with the current redacted `Unknown` profile. This is a real test failure, not proof that the conservative runtime result is wrong; no fix was made during verification.

## 6. NA18861 SLCO1B1 attribution

Classification remains C/D: truth-era nomenclature difference / PharmVar definition evolution. [Li et al., first published 9 November 2022, DOI 10.1002/cpt.2790](https://ascpt.onlinelibrary.wiley.com/doi/10.1002/cpt.2790) explicitly describes this exact NA18861 discrepancy and the later introduction of *43. Current verification independently retrieved that primary-source statement.

The frozen CDC workbook remains `*1/*14`; fresh pinned PharmCAT and application parser remain `*1/*43`. The application still abstains. The original uncompressed ~29 MB presentation was correctly rejected as oversized; the unchanged compressed presentation was used for the accepted API replay.

| GRCh38 locus | Public VCF | Pinned *14 requirement | Pinned *43 requirement |
|---|---|---|---|
| chr12:21176804 / rs2306283 | `0|1`, A/G | G | G |
| chr12:21176879 / rs11045819 | `0|1`, C/A | A | A |
| chr12:21196951 / rs11045852 | `0|1`, A/G | Not a defining core constraint | G |
| chr12:21206031 / rs74064213 | `0|1`, A/G | Not a defining core constraint | G |

The [35-position comparison](../2026-10-01-f7/variant-comparison.json) retains unobserved loci as unknown. Fifteen required positions are absent; the four listed loci have GT only, without DP/GQ/AD/explicit PS. Public-panel phase is not newly proven physical phase. No complete read-backed NA18861 VCF was produced by F4. No equivalence, revised CDC truth, or parser defect is invented; historical string discordance remains in the benchmark with an attribution overlay.

## 7. CYP2C19 *2 version status

Primary API receipts were refreshed 2 October:

- PharmVar current version: 6.2.29, updated `2026-09-22T21:55:42+00:00`.
- *2: PV03110, rs4244285, NM_000769.4:c.681G>A / GRCh38 g.94781859G>A. PV00599 replacement timestamp: `2026-07-31T19:30:32+00:00`; the recorded change belongs to PharmVar 6.2.28.
- [ClinPGx notice, 7 August 2026](https://blog.clinpgx.org/cyp2c19-2-core-allele-definition-update/) describes the updated core and relaxed companion-position representation.
- [Latest official PharmCAT release](https://github.com/PharmGKB/PharmCAT/releases/tag/v3.4.0) remains 3.4.0, published 14 July 2026; local data is `2026-07-13-11-40`. No newer coherent release containing the update was found.

The pinned translation still constrains companion bases G at 94775367 and 94842866. The manifest correctly records `not_included_in_pinned_bundle`, `coherent_older_definition`, `known_version_delta`. The metadata regression requires actual version/definition support for an included claim. No isolated allele edit or upgrade occurred. A future whole-bundle upgrade requires owner authorization and renewed coverage, mapping, explanation-context and independent benchmark checks; intentional older coherent pinning is not itself a biological implementation defect.

## 8. 512 MiB intended-image workload

The actual `infra/Dockerfile` was built from the clean intended-file context before negative-test mutations. Tested image: `sha256:8d2cf13f7b25a39d413f4bdebbb2a50b5cdf2dd9c386c9cf8195e22d015ccefe`. Linux/aarch64 via the available local Docker/Colima runtime. Limits: 536,870,912 bytes memory and equal total memory+swap limit (no additional swap). One Python worker, one concurrent PharmCAT JVM, `-Xmx208m -XX:MaxMetaspaceSize=68m`, queue timeout 90 s, normal analysis timeout 120 s, strict PharmCAT/static explanations. Local development CORS mode was used; no hosted service was contacted.

| Workload | Result / latency |
|---|---|
| Startup, `/health`, `/ready` | Successful, HTTP 200 |
| Real incomplete `/coverage` | 200, 0.178 s |
| Real incomplete analysis | 200 / Unknown, 16.624 s |
| Complete synthetic normal | 200, 3.834 s |
| Complete real normal | 200, 2.766 s |
| Sequential repeats | 200, 2.765 / 2.666 s |
| Three concurrent large real analyses | All 200; 21.307–52.771 s; maximum one JVM |
| Ten-analysis burst | Six 200; four bounded SERVER_BUSY 503 at ~90 s; successful requests 15.529–92.798 s |
| One analysis plus nine coverage requests | All 200 in a fresh rate window; 15.880–17.057 s |
| Forced 0.15 s timeout using same image | Controlled 503 in 0.218 s; no surviving JVM/temp/log tree |
| Cancel real running PharmCAT task | Actual JVM observed before cancellation; cancelled task, zero JVMs afterward; no owned analysis temp/log tree |

Overall cgroup peak: **496.46 MiB**. `memory.events` low/high/max/oom/oom_kill/oom_group_kill all zero. Largest sampled JVM RSS 314,028 KiB; Python RSS 196,872 KiB (separate process peaks, not an additive cgroup estimate). No OOM kill or crash during measurement; post-workload container state remained running. About 15.5 MiB margin is narrow and not a guarantee for arbitrary input/host combinations.

The first mixed-load attempt immediately after the burst hit the configured rate limiter: six HTTP 429 responses, four 200. This is retained, not counted as a successful mixed workload. After the rate window cleared, the complete mixed workload passed. Queueing is bounded; max supported active PharmCAT concurrency is one, not ten.

At final cleanup on 3 October, Colima was already stopped and both owned local server PIDs no longer existed. No runtime restart was performed. The saved lifecycle evidence proves request-level cleanup while the containers were running; a graceful final container-stop exit code and the optional late in-container byte comparison could no longer be collected. Build/JAR-verification layer receipts and exact measured image identity are retained. This is not a deployment test or native AMD64 memory measurement.

Starting the pre-existing local Colima VM for the workload also allowed unrelated pre-existing local containers to auto-start under their saved restart policies. They were not directly operated on or reconfigured. At final inspection the VM was stopped; this report does not attribute that shutdown to the verification agent. No remote or production deployment was performed.

## 9. Browser acceptance and parity

Actual release Flutter web build against local backend, Chromium in-app browser, genuine file chooser uploads; no mocked API. Cases exercised: real incomplete, complete synthetic normal/actionable, oversized public file, out-of-scope ibuprofen, real normal NA18526 and real actionable NA12878. Loading and readiness, expanded guideline/coverage content, warnings, provenance, scrolling, and 360×640 responsive access were exercised. No intentional visual changes were introduced; viewport override was reset.

The actionable screen retains population `CVI ACS PCI` and the CPIC qualification. Normal guidance is not a broad Safe verdict. Percentage-confidence results are absent; any transient loading percentage is progress, not clinical confidence. Unsupported drugs show an application limitation rather than an invented CPIC quotation.

Both real cases generated completed JSON transfers and readable files in Downloads. The actionable transfer receipt records 19,921 received bytes and `completed`, replacing the previous F6 observation of cancellation for this run only. No export fix was made; the cause of the earlier environment-specific cancellation remains unproven. Browser automation's download waiter still timed out despite real completed transfer; CDP events plus the actual saved files were used as evidence.

Saved exports match their actual browser API responses after the declared export transform: omit legacy `confidence_score`/`severity`, add a scope disclaimer and capability metadata. Added capability fields were independently checked against the authoritative registry. All other fields, including position-coverage counts, phenotype, diplotype, recommendation, explanations and warnings, agree. Thus scientific JSON parity passes; byte-for-byte API/JSON equality is intentionally not asserted.

`Copy JSON` showed success, but the browser clipboard read-back was empty. The print button was exercised, but browser commands timed out while entering the native print route; exact printable-output capture was not obtained. Native host-app access was unavailable. These are **INCONCLUSIVE**, not silently passed and not proven production defects. No code was changed to bypass the test limitation. Complete API = screen = copied JSON = print parity therefore remains open. Flutter print/model tests passing is not substituted for real-browser proof.

Screenshots, accessibility observations, network/download records and console capture are retained as `browser-*`. No error/warning console entries were captured in the final console snapshot; this is not a claim that every browser event throughout the run was exhaustively captured.

## 10. Complete tests, failures and skips

| Check | Result |
|---|---|
| Backend, final run with live backend | **908 passed, 3 failed, 5 skipped**, 9 warnings, 65.03 s |
| Earlier backend run without server | 906 passed, 2 failed, 8 skipped; superseded by live run for skip accounting |
| Flutter | **202 passed, 0 skipped** |
| Flutter analyzer | No issues |
| Flutter release web build | Passed |
| Provenance validator | 106/106 clinical assertions traceable; not human or clinical endorsement |
| Label mapping | 105 comparisons; 92 agreements / 13 recorded accepted divergences; exit 0; not independent clinical accuracy |
| Capability registry / generated Dart agreement | Passed |
| Scientific bundle | Failed current-core and migration binding |
| Exact release gate | Exit 1 / NOT READY |
| `git diff --check` | Passed |

All backend failures:

1. `test_compatible_bundle.py::test_checked_manifest_matches_declared_environment`: manifest expected older scientific core; historical benchmark identity does not bridge to current core.
2. `test_portable_scientific_hash.py::test_clean_isolated_copy_passes_bundle_verification`: same genuine compatibility failure in clean copy, not filesystem junk.
3. `test_demo_script.py::TestDemoAgainstLiveApi::test_the_contrast_actually_contrasts`: expects incomplete variant-only diplotype `*2/*2`; API correctly withholds it as `Unknown` under current evidence semantics. Test/invariant reconciliation requires a separate minimal change and review.

All remaining skips:

- `test_documented_numbers.py:263`: README no longer quotes a backend test count (one).
- `test_glossary_audit.py:284`: no recorded glossary decisions (one); not fabricated to eliminate skip.
- `test_sample_vcfs.py:286`: pipeline executable not on local PATH (three cases: CYP2C19 poor-metabolizer, DPYD variant carrier, normal control). Direct pinned-JAR API and container replays were separately run, but these three skipped test nodes are not relabelled passed.

Nine warnings are pytest deprecations for class-scoped instance-method fixtures. Initial Flutter attempts were blocked by toolchain cache sandbox permissions; the authorized reruns passed. These environment failures remain in their separate receipts. Full per-module counts and nonpassing test text are in `test-summary.json`; the final JUnit/raw logs remain local.

Relevant subsets included: approval 12 pass, release 12 pass, capability 11 pass, evidence validity 19 pass, coverage endpoint 32 pass, coverage gate 31 pass, resource ownership 9 pass, privacy 6 pass, external benchmark tests 9 pass, manifest 6 pass/1 fail, portable hash 16 pass/1 fail. No hidden numerical project score is assigned.

The historical independent benchmark remains 208 individuals, 1,456 sample/gene rows, 596 evaluable independent diplotype rows, and 208 PharmCAT reports. Variant-only inputs qualified for zero application guidance cases. Its transparent gene-level results and discrepancy denominators are preserved, not pooled into an accuracy claim. The entire 208-person cohort was **not rerun** for this final candidate. Nine benchmark regression tests and the two read-backed controls do not establish current identity binding for that historical evaluation; the gate correctly rejects the stale migration assertion.

## 11. Final stop-condition matrix

| Condition | PASS / FAIL / INCONCLUSIVE | Evidence |
|---|---|---|
| 1. All P0 correctness and release requirements closed | FAIL | Human prerequisites incomplete, gate exit 1, three backend failures |
| 2. Independent benchmark transparent and complete for claimed current scope | FAIL | Historical denominators are transparent, but current scientific identity is not supported by its manifest/migration; only one pathway has two real positive controls |
| 3. Scientific claims correctly bounded | INCONCLUSIVE | Tested outputs retain abstention, scope and population qualifiers; no clinical review, and complete copied/printed content parity remains unverified |
| 4. Release operationally repeatable | FAIL | Portable hash and measured container workload pass, but clean-copy compatibility and final gate fail; browser acceptance incomplete |
| 5. Practical limitations explicit | PASS | Older definitions, narrow real-input scope, benchmark identity gap, review gaps, skips, memory/platform limits and browser uncertainty are all retained |

## 12. Owner review package and remaining work

Existing dirty changes: **75 tracked files, 3,071 insertions and 1,216 deletions**; source/document/benchmark proposal also contains 45 pre-existing untracked intended files. The full tracked patch, per-file counts, status, 421-file byte inventory and proposal are retained. No tracked diff changed during this verification. No staged changes, commit, push or deployment were introduced by this verification.

The changed areas are backend evidence/coverage/capability and explanation eligibility; portable bundle/release tooling; resource lifecycle/admission/JVM settings; functional Flutter scope/export/Unknown handling; tests; and scientific/deployment/benchmark documentation. These are pre-existing local remediations, not newly implemented fixes in this review. The unrelated PDF/DOCX, scratch output, temporary data, environments, secrets, caches and raw large genomic files are excluded from the proposed commit list.

Required owner follow-up, before any release approval:

1. Complete genuine review of the 55 pending human-action claims and 20 exact-content entries, or explicitly authorize and review a different release policy. Never turn automation into human approval.
2. Reconcile current scientific bytes with benchmark evidence under the controlled evidence procedure; regenerate the candidate manifest only with appropriate current evidence, and rerun gate/clean-copy checks. Do not change only a hash to obtain a green result.
3. Reconcile the obsolete live demo assertion with the evidence-withholding invariant, without relaxing coverage or exposing unsupported confidence.
4. Verify copied JSON and printed summary in a usable native browser environment; preserve input/output evidence before any functional fix. Recheck the prior download problem if it recurs.
5. Retain all scope/platform limitations. Future source-bundle upgrades require a separate owner decision. No current clinical-expert review exists.

Defensible claims now: the pinned, bounded research application abstains when tested required evidence is absent/invalid; two independently characterized public CYP2C19 samples provide genuine read-backed normal/actionable pathway demonstrations; unresolved generated prose is ineligible; scientific identity ignores tested filesystem junk; the tested Linux/arm64 image completed the declared 512 MiB workload without OOM; real browser JSON downloads preserve scientific content; the two definition/nomenclature deltas are explicitly documented.

Prohibited claims: release-ready or clinically validated; human/expert-approved explanations; calibrated confidence/probability or patient-level safety; whole-genome/all-drug accuracy; complete real validation of TPMT/NUDT15 or other pathways; CYP2D6 calling; warfarin dosing; latest CYP2C19 *2 already in the pinned bundle; *14/*43 proven functionally equivalent; full NA18861 read-backed agreement; current 208-person benchmark validation; complete browser copy/print parity; guaranteed fit on every 512 MiB platform; any production deployment result.

# Proposed Release Files

The exact finite **236-file** proposal is [PROPOSED-RELEASE-FILES.txt](PROPOSED-RELEASE-FILES.txt), one repository-relative path per line, with [per-file hashes](proposed-file-hashes.json). It includes the 120 intended changed source/document/benchmark paths plus 116 explicitly selected review-evidence files from F4–F7 and this final verification. It contains no wildcard directory additions. The hash inventory excludes its own self-hash.

This is an owner-review proposal, **not a declaration that the current files are releasable or ready to commit**. No files were staged. The known stale manifest and failing tests remain visible. Large acquisition/reference/read caches and toolchain artifacts are intentionally omitted; acquisition instructions/checksums and the small observed VCFs are included. The complete current local raw evidence remains available outside the proposal.

### UI visual changes

`NONE` — no intentional visual changes introduced during final verification.

### Git commit

`NOT PERFORMED`

### Git push

`NOT PERFORMED`

### Tag/release

`NOT PERFORMED`

### Deployment/redeployment

`NOT PERFORMED`

### Production environment

`UNCHANGED`

### Current recommendation

`AWAITING OWNER VERIFICATION`
