# Final independent local verification and owner handoff

**Verdict: FAIL / NOT READY**

Verification ran 5–6 October 2026 against the authoritative dirty local tree. The six mandatory automated gate commands passed, but the declared all-stored-entry human-review policy remains unmet. Actual clipboard, downloaded JSON and native printed PDF now have fresh evidence. Printed source-checking wording also contains an unsupported assurance, recorded for separate remediation. No candidate edit was made to conceal that finding.

This is automated verification, not human/clinical review. A dedicated model switch to GPT-6 Astra/Sol and a separate Deep Research mode were unavailable in this session; authoritative primary sources and installed tools were used. No clinical validation or project score is asserted.

## 1. F1–F7 matrix

“Previous” uses the latest relevant Prompt3/5/6 receipts; the frozen October 2 report remains unchanged. In particular, its stale F2 failure was reconciled in Prompt5, not retroactively rewritten.

| Finding | Previous | Current | Evidence and bounded scope |
|---|---|---|---|
| F1 explanation/release approval | FAIL | FAIL | `release-gate.stdout`: 55 claim decisions need human action; 20 entries lack author-read approval. 0 approved/releasable, 20 fallback-only. |
| F2 portable candidate identity | PASS | PASS | `clean-copy-verification.json`, `freeze-comparison-final.json`: all 437 inventory entries unchanged; compatible baseline/copy/other-parent; junk ignored; six isolated mutations rejected and restored. |
| F3 CYP2C19 metadata | PASS | PASS | Fresh official snapshots in `source-receipts.json`; coherent older pin retained, newer *2 definition explicitly not included. |
| F4 bounded real guidance | PASS | PASS | Fresh read replay, actual JAR/parser/API and browser normal/actionable results. 35/35 observed required positions per case; hypothetical ACS/PCI qualifier retained. |
| F5 constrained release image | PASS | PASS | Prompt6 Linux/arm64 receipts still bind identical candidate bytes; fresh integrity check of 183 receipts and 437 build-context entries. Other architectures remain INCONCLUSIVE. |
| F6 browser acceptance | INCONCLUSIVE | FAIL | Upload/results/recovery, clipboard, native saved JSON and real native PDF mechanics PASS. Broader content acceptance fails on unsupported printed source-checking assurance; see `NEW-FINDINGS.md`. IAB download/print remain INCONCLUSIVE individually. |
| F7 NA18861 attribution | PASS | PASS | Frozen truth *1/*14 preserved; fresh JAR/parser *1/*43, final simvastatin Unknown; published nomenclature attribution retained. No functional-equivalence or complete read-level rerun claim. |

## 2. Candidate identity and exact gate

Base HEAD `1dc7557da49f38e831b382545044b00a481507b6`, branch `main`; dirty working tree is authoritative. `candidate-inventory.json` lists 433 intended project/release entries and four externally acquired artifacts (437 total) with exact paths, byte counts, symlink flags and SHA-256. Its SHA-256 is `9582a19acd61d841e6ecc9d98cdeef5796e654cdc790343d27b1dc0100af62da`. Symlink entries hash dereferenced content, matching the frozen policy; link type and target are preserved in isolated copies.

| Identity | SHA-256 |
|---|---|
| Scientific core v2 | `38451a563c6f6cfb52257626d41700eeff3a5621ebe91b3358f878b375a6a691` |
| Dirty release artifact | `0c1aa418159cc7e4456b058d37cbabf751ff0f2bf9a7050566e798d6e24fa92c` |
| Compatible manifest | `963a039ba16690d1c6ed772268ebb5c1512275beeb5fa117a6bef1c03aae7600` |
| Current evaluation manifest | `23a46b1070cd82b578c4f518ab77a0b87af71a30573513d87139328d61b7898a` |
| Pinned PharmCAT 3.4.0 JAR | `9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741` |

Bundle `pharmaguard-scientific-current-candidate-2026-10-04-v3`; data `2026-07-13-11-40`. Version2 hashes a domain separator and sorted finite POSIX-relative paths/raw bytes. The compatible manifest is excluded from scientific self-reference but separately bound in release identity. Evaluation outputs and their manifest are separately bound; the evaluation manifest excludes itself. Changing an evidence output can invalidate release compatibility without changing the scientific core. No hash policy was rewritten or target hash hard-coded.

After inspecting current help, executed:

```
backend/.venv/bin/python scripts/release_status.py --run-required --candidate-sha 1dc7557da49f38e831b382545044b00a481507b6 --json
```

Exit **1**, `state=not-ready`. All six required checks ran and returned 0: compatible bundle, backend tests, provenance, label mapping, Flutter analyzer, Flutter tests. The gate computed matching candidate/tested dirty artifact hashes as well as matching revisions; old receipts were not accepted solely by HEAD. `release-gate.execution.json` and `release-gate.stdout` are authoritative. Failing human prerequisites remain failures; compatible manifests and deterministic fallback do not waive them.

Human inventory: 179 flagged sentences; 160 decisions, comprising 124 recorded human decisions and 36 automated decisions; 19 outstanding. Thus 55 require human action. All 20 stored generated entries remain unapproved; author-read count 0. The 124 historical decisions were preserved; current validation checks bindings and does not extend them to new bytes. Clinical expert status is **NOT_OBTAINED**. The bounded research gate requires truthful status, not a fabricated expert sign-off; no additional clinical policy was invented.

Use the existing Prompt4A `OWNER-REVIEW-PACKET.md`, `reviewer-response-template.json` and `HANDOFF.md` in `../2026-10-03-prompt4a-8f4cbfbc76/` to return genuine source/content/context-bound decisions. Claim adjudication, author-read approval and clinical expert review are separate. The owner has supplied no new genuine decisions in this task. Do not treat a request to “complete it yourself” or test fixtures as human review. The default all-stored-entry requirement remains mandatory; no template-only policy change was applied.

## 3. Fresh tests, skips, warnings and failed attempts

Exact argv, cwd, exits and timestamps are consolidated in [COMMANDS.md](COMMANDS.md) and [command-index.json](command-index.json); individual stdout/stderr and execution receipts remain beside them. `environment.json` records macOS 27.0.1 arm64, Python 3.11.14, installed dependencies, OpenJDK 25.0.1, bcftools and pinned JAR versions. Explicit PHARMCAT_JAR/PHARMCAT_JAVA, static explanation mode and strict PharmCAT were used.

| Fresh execution | Result | Exit |
|---|---|---:|
| Full backend with real local API and pinned JAR | 919 passed, 2 skipped, 0 failures; 921 total | 0 |
| Flutter tests | 202 passed | 0 |
| Flutter analyzer | No issues | 0 |
| Release web build against localhost:8000 | Completed; build inventory retained | 0 |
| Bundle validator | Compatible | 0 |
| Provenance verifier | Automated source trace checks pass; not human approval | 0 |
| Label mapping validator | 13 divergences, all already in accepted baseline; none silently erased | 0 |
| Adjudication status | Incomplete, 55 human actions needed | 1 |
| Review status | Provenance complete, author-read 0/20, expert NOT_OBTAINED | 0 |
| Glossary report-only command | 124 undecided/undefined of 131 candidates | 0 |
| Exact release gate | All automated mandatory checks pass; human prerequisites fail | 1 |
| Six frozen bcftools replay commands | All normalized genotype records match | 0 each |
| Real API/adverse/F4/F7 acceptance harness | All assertions pass | 0 |
| PDF render and text extraction | Five rendered pages and field comparisons retained | 0 |

Full backend execution includes explanation, provenance, approval, release, capability, mapping, scientific/hash/benchmark, lifecycle/privacy and real sample-VCF integration tests. Synthetic approval fixtures exercise exact-compatible approval, automated/unresolved/rejected fallback, content/source/context/drug/gene/phenotype/source-row mismatch rejection and fabricated expert status rejection. They are tests, not real reviews. The three formerly skipped CYP2C19 poor, DPYD variant-carrier and normal-control integrations executed with the real pinned JAR; unrelated unit tests were not substituted.

Every remaining skip:

1. `test_documented_numbers.py:263`: README no longer quotes a backend test count. Legitimately not applicable; no artificial count added; no release implication.
2. `test_glossary_audit.py:284`: no recorded glossary decisions. Genuine human prerequisite for adjudicating optional glossary terms; the current precommitted policy is report-only because measured false-positive rate 41.5% exceeds the 25% threshold. It is not a mandatory release exemption invented here. 124 terms remain for optional owner review; no glossary decisions fabricated.

Nine existing `PytestRemovedIn10Warning` messages for class-scoped instance-method fixtures remain visible in backend/gate logs. Flutter reported 24 newer package versions incompatible with current constraints; no upgrades performed. Build font-tree-shaking/WebAssembly diagnostics and pip cache-permission warning are retained verbatim. Browser console receipts are preserved, including expected oversized-request failure. No warning filter or test skip was introduced.

Other failed/inconclusive attempts are preserved, not called application failures: initial sandbox loopback bind exit1 (authorized local rerun succeeded); stale historical F4 manifest assertion exit1 (audit harness corrected to check preserved historical manifest plus current compatible inventory, biological assertions unchanged); first owner-summary helper exit1 due to symlink target-string versus target-content hashing (corrected only helper to existing inventory contract, original receipt retained); sandbox process inspection denied before cleanup (escalated owned-process cleanup succeeded). IAB download cancellation and native-print automation timeout are detailed below. No assertion was weakened to hide a candidate defect.

## 4. Isolated copy and negative checks

The intended-files copy includes current uncommitted bytes and pinned external artifacts, excluding secrets, actual env files, caches and unrelated data. Baseline compatibility passes. Same intended bytes in another parent directory produce identical core/release hashes. `.DS_Store`, editor backup, pycache, log and temporary junk do not affect identity.

Six isolated mutations—scientific code, capability registry, position requirements, explanation store, approval manifest and current benchmark output—each invalidate their corresponding identity/validator. Exact 437-entry restoration was verified. An additional deliberately invalid explanation summary fails with named reasons `approval manifest and explanation-store hashes differ` and `content hash mismatch: azathioprine/IM`.

The **release gate baseline already fails** for human prerequisites. Therefore the content-only negative sequence is FAIL → additional named rejection → restored original FAIL, not a claimed PASS→FAIL→PASS release demonstration. The working candidate was never mutated. See `clean-copy-verification.json`, `negative-gate-summary.json`, and `isolated-content-*.stdout`.

## 5. Real biological evidence and benchmark boundaries

F4 retained its precommitted protocol, independent diplotype truth, public read/reference hashes and frozen inputs. Fresh bcftools mpileup/call/norm reproduced every normalized genotype row for NA18526 and NA12878; headers differ only in execution metadata. Each has 35/35 observed required CYP2C19 positions. NA18526 *1/*1 → NM → qualified normal clopidogrel; NA12878 *1/*2 → IM → Ineffective with the hypothetical CVI ACS/PCI population qualifier. Donor diagnosis is not inferred. JAR reports, parser reports, API responses, browser response bytes and exports are saved. The native saved JSON/PDF belong to the actionable repeat; both real cases have fresh browser/API evidence.

Fresh adverse cases preserved Unknown for variant-only/incomplete evidence, failed FILTER, partial GT, missing required position, missing TPMT/NUDT15 partner, unsupported ibuprofen/atorvastatin, CYP2D6/codeine and warfarin-dose pathways. Removing evidence did not increase certainty. See `api-acceptance.json` and `real-truth-comparison.json`. No unobserved 0/0 genotype was invented; no paired TPMT/NUDT15 positive-pathway, per-base independent truth or clinical outcome validation is claimed.

[Benchmark denominators and all discrepancies](BENCHMARK.md) retain 208 people, 1,456 sample-gene rows and 596 evaluable truth rows; 816 blank, 42 unsafe nomenclature and 2 unresolved truth rows remain excluded. Historical identity `9961033924dda2d4ab8e57d85450debeb98c4afdc392b3959d3d0ccf856f214c` is unchanged. Prompt5's current evaluation `pharmaguard-external-current-candidate-v2-2026-10-04` binds this exact scientific core. It legitimately reused 208 hash-verified caller reports and freshly ran application projection/scoring. **Zero cohort caller executions occurred in Prompt5's reuse stage or in this Prompt7 verification.** Fresh unit tests and two real controls are not described as a rerun of 208 people.

Current bundle validation checks the evidence and its candidate binding. Every application evaluable row abstains with these incomplete cohort inputs; eligible 0/208 for each gene. DPYD's 83 nomenclature mismatches and SLCO1B1's mismatches remain explicit. No pooled clinical accuracy, functional equivalence, false-reassurance rate or clinical utility claim is derived from caller/parser agreement.

## 6. Dated authoritative source verification

Fresh official HTTP200 snapshots on 5 October are in `source-receipts.json`, including URLs, times and hashes. [Official PharmCAT release metadata](https://api.github.com/repos/PharmGKB/PharmCAT/releases/latest) reported 3.4.0, published 14 July 2026. [PharmVar](https://www.pharmvar.org/gene/CYP2C19) reported database 6.2.29 (22 September update), active *2 PV03110, no function. Its history records PV00599→PV03110 on 31 July 2026; current core variant data include rs4244285, GRCh38 94781859G>A. The [ClinPGx 7 August announcement](https://blog.clinpgx.org/cyp2c19-2-core-allele-definition-update/) documents the definition update. The pinned caller retains its older companion constraints; the manifest explicitly says `not_included_in_pinned_bundle`. No external metadata was hand-applied to biological definitions.

For NA18861, the [primary PharmCAT tutorial](https://pmc.ncbi.nlm.nih.gov/articles/PMC10121724/) ([publisher DOI](https://ascpt.onlinelibrary.wiley.com/doi/abs/10.1002/cpt.2790), first published November 2022) attributes *1/*14 versus *1/*43 to later nomenclature. Fresh pinned caller/parser still yield *1/*43 on the frozen incomplete input; application simvastatin remains Unknown. Original CDC truth *1/*14 and frozen workbook hash are preserved. The current CDC workbook was not newly acquired; no CAPTCHA was bypassed. This attribution does not establish biological equivalence or a full read-backed rerun of NA18861.

## 7. Final image and constrained workload

Fresh integrity verification found zero mismatches across 183 Prompt6 receipts and 437 context entries. Its final successful report supersedes its preserved initial infrastructure-INCONCLUSIVE preflight. Since candidate bytes/configuration did not change, no new VM or container run was necessary in Prompt7.

Image `sha256:82abce68aaafd51da8ed41eba52a2e1d5e0909a6a0f06005c8aeb5b6e7016d90`, Linux/arm64. Limit 536,870,912 bytes memory and equal total memory-plus-swap, swap.max0. One Python worker and one active JVM, Xmx208m and metaspace68m. Measured cgroup peak **521,707,520 bytes = 497.5390625 MiB**; margin **15,163,392 bytes = 14.4609375 MiB**. No OOM/limit events; five owned containers exited143 after graceful SIGTERM, child/temp cleanup checked. JVM/Python RSS peaks are non-additive and are not substituted for cgroup peak.

Same-image startup, health/coverage, real incomplete/synthetic/real qualified cases, sequential/concurrent/queue burst, mixed coverage, rate recovery, timeout override and cancellation were tested in Prompt6. Ten-request burst had six successful analyses and four busy503 responses; expected admission/rate errors were not counted as successful analyses. Timeout override was test-only0.15s. In-image runtime/JAR/data bytes were inspected while containers remained accessible. No unrelated workloads were started. Native AMD64/actual hosting remains INCONCLUSIVE; narrow arm64 memory headroom is not a deployment guarantee. See `prompt6-receipt-integrity.json` and `../2026-10-05-prompt6-bb6a5821fb/PROMPT-6-REPORT.md`.

## 8. Actual browser acceptance and exports

Fresh release web build, API and input/output identities are in `browser-summary.json`, `web-build-inventory.json`, `browser-api/` and source inventory. Native Google Chrome **154.0.8037.98** performed actual chooser upload, saved JSON and UI print → native Save as PDF. IAB exercised incomplete, synthetic normal/actionable, oversized public, unsupported drug, both frozen real cases, loading/recovery, Unknowns, qualifiers, warnings, details/provenance, scroll and 1280×720/360×640 sizes. No cosmetic change was made; existing visual hierarchy is unchanged. Native Chrome repeated the actionable case and exports, not the entire IAB fixture matrix.

- **Clipboard PASS:** actual Copy JSON followed by permitted clipboard read, 30,189 bytes. `clipboard-raw-cua.json` SHA-256 `bdc29c085481488d763e71e5ab5da185c9db2b3b646cb2468a613384e4bc8089`; exact scientific parity with API0014. Only deprecated confidence/severity omission and declared scope/capability metadata were allowed; capability values match registry. No success-toast-only claim.
- **Native saved JSON PASS:** `native-NA12878-downloaded.json`, 30,189 bytes, SHA-256 `791e9f3122fc25f8ddb810f16c8680f99ae2f93ae7d10fde3cbacd4d91e80839`. Parsed actual disk bytes match API0020 at `2026-10-06T10:54:54.745948Z` under the same exact transform.
- **Native print mechanics/summary-field parity PASS:** actual UI route saved `native-NA12878-print.pdf`, five pages, SHA-256 `6ac727b750a38d50d36f82a05ccb340c32a3c9f3d4a23d1347c2a1632f80efe9`. All five rendered pages were visually inspected: no observed clipping/truncation, repeated research header, six results, five Unknown reasons, ACS/PCI qualifier, seven-gene census and provenance. All selected scientific fields match the same API0020. The raw comparison intentionally retains one timestamp mismatch: explanation generation is displayed as `24 Jul 2026` by the existing date getter, rather than its full timestamp. No scientific discrepancy was normalized away.
- **Print content acceptance FAIL:** unsupported disclaimer assurance identified in `NEW-FINDINGS.md`. All 21 raw pipeline warnings and expanded mechanism/rationale/patient-friendly fields are omitted by existing summary policy; this is not claimed full-API print parity. The exact omissions and owner decision are recorded separately.
- **IAB download INCONCLUSIVE:** native transfer canceled after 0/31,861 bytes, waiter timed out. Native Chrome succeeded; historical download success is not substituted for this failed IAB attempt.
- **IAB print INCONCLUSIVE:** iframe content was visible, automation call timed out before native document save. Native Chrome's actual saved PDF supplies a separate supported-browser success, not a fabricated IAB success.

No browser permission/security restriction was bypassed, no extension installed, no external genomic submission. Viewport override reset. Owned local API/static servers were terminated and ports8000/3000 had no listeners; cleanup receipts preserve exact PIDs/commands/exits. Native Chrome had no available window at cleanup, so no blind close action was performed. No remaining human browser step is required to establish the captured native workflow; owner content review and any additional target-browser/architecture certification remain outstanding.

## 9. Five-condition stop matrix

| Condition | Status | Evidence |
|---|---|---|
| All P0 correctness and release requirements closed | FAIL | Mandatory human review incomplete; exact release gate exits1. |
| Independent benchmark transparent and complete for claimed current scope | PASS | Current-candidate application evidence binds exact core; reuse/denominators/discrepancies disclosed; no broad positive/clinical claim. |
| Scientific claims correctly bounded | FAIL | Most result scopes/qualifiers are bounded, but the observed source-checking assurance overstates automated verification; separate remediation required. |
| Release operationally repeatable | FAIL | Build, compatibility and bounded arm64 workload repeatability pass; authoritative release gate still fails, and other deployment architectures are unverified. |
| Practical limitations explicit | PASS | Human blockers, summary omissions, IAB limitations, narrow memory margin, cohort abstention and untested pathways are enumerated. |

## 10. Owner package, changes and next authority

The finite candidate proposal identifies 134 changed intended project/release paths relative to HEAD, all inherited from earlier work. Only this new audit directory contains task-created source/evidence artifacts. No candidate code, approval, policy, manifest, biology or UI bytes changed. The full preexisting tracked diff is identical before/after (SHA-256 `4fc44c3c697ee68b06420e32375622999ce738b2c3fafb03f88200cc61ce3800`); staged diff is empty, `git diff --check` exits0, and all status entries outside this audit directory are unchanged. Before/after semantics are identical. `git-diff-start.stdout` and `git-diff-final.stdout` preserve the full preexisting tracked diff; `git-diff-stat-final.stdout` summarizes it. `git-status-start.stdout` and `git-status-final.stdout` preserve all dirty/untracked paths. Exact intended file changes versus HEAD are listed in `candidate-changed-files.json`; unrelated dirty changes are not swept into the proposal.

`PROPOSED-RELEASE-FILES.txt` lists exact proposed changed release/evidence paths, one per line, with SHA-256/size in `proposed-file-hashes.json`. **Proposal status: BLOCKED, NOT APPROVED FOR PUBLICATION.** It excludes actual env/secrets, caches, isolated copies, built web assets, large raw BAM/VCF/JAR acquisition, and unrelated artifacts. Pinned external acquisition/reuse receipts remain; the complete verification inventory separately identifies externally acquired artifacts. No wildcard staging is proposed. `artifact-checksums.json` inventories fresh owner artifacts with explicit self-reference exclusions.

Permitted claims: tested conservative abstention; two bounded CYP2C19 positive controls; transparent reused-caller/current-application benchmark; actual tested clipboard/JSON/PDF mechanisms; constrained Linux/arm64 workload at the measured limit. Prohibited claims: clinical readiness/validation, expert approval, complete independent positive-pathway validation, current PharmVar definition inclusion, native AMD64 certification, 208 fresh caller executions, all prose human-approved, or a passing release gate.

Remaining owner actions: provide genuine exact-bound decisions for the 55 claims and author-read approvals for 20 entries; review the separate printed wording findings and decide any required summary-warning policy change; after authorized remediation, refreeze/revalidate affected evidence and rerun final verification. Expert review remains NOT_OBTAINED unless actually performed. This task does not contact reviewers or publish anything.

### UI visual changes
NONE
### Git commit
NOT PERFORMED
### Git push
NOT PERFORMED
### Tag/release
NOT PERFORMED
### Deployment/redeployment
NOT PERFORMED
### Production environment
UNCHANGED
### Current recommendation
AWAITING OWNER VERIFICATION
