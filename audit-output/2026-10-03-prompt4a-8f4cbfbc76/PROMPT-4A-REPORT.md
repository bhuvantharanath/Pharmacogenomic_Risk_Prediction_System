# Prompt 4A — completed preparation, human review outstanding

3 October 2026. **F1 remains open; release NOT READY. No human decisions or clinical approval were made.**

## Deliverables

- [Human handoff and schema instructions](HANDOFF.md)
- [Complete owner review packet](OWNER-REVIEW-PACKET.md): 20 entries, all 179 current claim occurrences, exact text, source/context information, source-row candidates, existing records and required actions.
- [Machine-readable inventory](inventory.json) and [blank reviewer response template](reviewer-response-template.json).
- [Primary-source verification](SOURCE-VERIFICATION.md), [source register](source-register.json), [web retrieval receipt](web-verification-receipt.json), and [pinned guideline rows](pinned-source-guidelines.json).
- [Separate proposed text changes](PROPOSED-TEXT-CHANGES.md): 15 unreviewed sentence replacements plus a citation-metadata proposal. Nothing applied.
- [Preserved human-labelled records](preserved-human-records.json), original store and approval manifest snapshots.

## Fresh inventory and binding results

**19 unresolved + 36 automated-only = 55 pending human claim decisions; 20 entries lack author-read records.** All entries remain in scope. Clinical expert review remains **NOT_OBTAINED**.

124 current human-labelled records match exact current sentence/field/key; all explicitly describe bulk decisions that were not individually read. This task verifies their stored contents, not reviewer identity or historical conduct. Two obsolete simvastatin Unknown records remain preserved and uncounted toward current claims.

None of the 124 records stores historical content/source/context hashes. Their historical source/context attestation cannot be recovered from those records alone. All 20 current manifest bindings match, but every entry is unresolved; matching current hashes must not be represented as historical approval. See HANDOFF.md for hash coverage and missing source-row/indication/paired-phenotype fields.

| Entry | Recorded human bulk | Automated-only | Unresolved | Missing author read |
|---|---:|---:|---:|---:|
| azathioprine:IM | 7 | 1 | 2 | 1 |
| azathioprine:NM | 6 | 1 | 1 | 1 |
| azathioprine:PM | 5 | 0 | 2 | 1 |
| azathioprine:Unknown | 6 | 1 | 2 | 1 |
| clopidogrel:IM | 7 | 3 | 0 | 1 |
| clopidogrel:NM | 5 | 2 | 0 | 1 |
| clopidogrel:PM | 7 | 3 | 0 | 1 |
| clopidogrel:RM | 6 | 1 | 2 | 1 |
| clopidogrel:URM | 6 | 3 | 0 | 1 |
| clopidogrel:Unknown | 6 | 3 | 0 | 1 |
| codeine:Unknown | 5 | 2 | 0 | 1 |
| fluorouracil:IM | 7 | 2 | 1 | 1 |
| fluorouracil:NM | 8 | 1 | 2 | 1 |
| fluorouracil:PM | 5 | 2 | 0 | 1 |
| fluorouracil:Unknown | 7 | 2 | 1 | 1 |
| simvastatin:IM | 8 | 3 | 0 | 1 |
| simvastatin:NM | 7 | 1 | 2 | 1 |
| simvastatin:PM | 6 | 1 | 1 | 1 |
| simvastatin:Unknown | 5 | 3 | 2 | 1 |
| warfarin:Unknown | 5 | 1 | 1 | 1 |

Review flags include broad safety/effectiveness assurances, thiopurine source attribution and paired-gene context, clopidogrel indication/contraindication qualifiers, fixed stored patient-variant assertions, and explicit-abstention wording. These are review aids, not new adjudications. The packet marks 144 occurrences with a flag or contextual reminder; that is not an additional gate count.

## Source verification and capability limits

Available primary-source web tools were used. No separate Deep Research capability or confirmable GPT-6 Astra switch was available. CPIC landing pages redirected to JavaScript-only ClinPGx pages; some PMC direct opens challenged the browser. Accessible official PDFs and indexed primary-paper text supplied bounded verification. No restriction was bypassed, and exhaustive live database currency is not claimed.

The thiopurine source names Maillard as first author for PMID 41618934, whereas the stored citation says Relling. This is a source-metadata review flag; no citation or biological definition was edited. The official 2026 DPYD notice is recorded as pending-update evidence, without upgrading the pinned bundle. Primary URLs, publication/version dates, supporting locations and limitations are in the source register.

## Candidate and preserved bytes

- Repository: `/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System`; branch `main`; HEAD `1dc7557da49f38e831b382545044b00a481507b6`. HEAD is only an identifier; all analysis used current dirty bytes.
- Current release artifact hash: `9961033924dda2d4ab8e57d85450debeb98c4afdc392b3959d3d0ccf856f214c`.
- Explanation store SHA-256: `35cb17a98fd2a885da9f14264da647b9923c75481bc7e02eff9c433fea2c59e8`.
- Pinned PharmCAT JAR SHA-256: `9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741`; 3.4.0 / data 2026-07-13-11-40 as recorded in the pinned bundle. No caller execution in this task.
- Prescribing-guidance member SHA-256: `5010bb813ed6aaacf504c689e1f74924ddc7c58383d5e35604074d299345d6a8`.
- 147 exact input files and byte counts are recorded in `scope-extended-before.json`; all match `scope-after.json`.
- The initial narrower inventory is retained as `scope-before.json`; the extension adds the full release core and pinned source before any source mutation (none occurred).
- Existing tracked binary diff: 388056 bytes, SHA-256 `4fc44c3c697ee68b06420e32375622999ce738b2c3fafb03f88200cc61ce3800`, unchanged from start to finish.
- Required historical reports and reports/release_content_review.md were read for their approval/release evidence and remain unchanged. No applicable AGENTS.md was found in the repository or checked ancestor locations. Current executable policy and schema were inspected directly.

## Fresh commands and outcomes

Exact argument arrays, exit codes, stdout and stderr paths are in [commands.json](commands.json). Commands below ran from the repository root with the existing backend virtual environment. Historical test successes are not relabelled as fresh executions.

| Command | Exit | Result |
|---|---:|---|
| `backend/.venv/bin/python scripts/adjudication_status.py --require-human --json` | 1 | Expected incomplete: 19 unresolved, 36 automated-only |
| `backend/.venv/bin/python scripts/review_status.py --json` | 0 | Machine provenance 20/20; human entry reads 0/20; not release approval |
| `backend/.venv/bin/python scripts/release_status.py --content-only --json` | 1 | NOT READY; content incomplete and scientific bundle stale |
| `backend/.venv/bin/python -m pytest backend/tests/test_explanation_approval.py backend/tests/test_release_status.py -q` | 0 | 24 passed; no failures, skips or warnings emitted |
| Audit `build_packet.py` (initial and final) | 0 each | Full inventory generated, no source mutations |
| Audit `build_drafts.py` (initial and final) | 0 each | Separate unreviewed proposals/source reading aid |
| Audit `validate_packet.py` | 0 | 38 integrity checks passed; 0 failed |
| Audit `finalize_report.py` | 0 | Source preservation, full tracked diff, HEAD/index and status-delta checks |

No full backend suite, Flutter run, live browser test, caller execution or full release gate was rerun for this packet-only task. The existing test approval fixtures are simulated fixtures, not real review. No required test was disabled, skipped, deleted, or changed; no test assertion was edited.

The content-only gate deliberately has `required_checks: []` and `required_checks_passed: false`; its internally equal candidate/tested hashes are not evidence of a fresh full suite. Scientific bundle verification still reports expected application core `204c315389f97f8de688b8ac3219bcc27f0a95c6e8c699fc50fd8b0df361725c` versus current `38451a563c6f6cfb52257626d41700eeff3a5621ebe91b3358f878b375a6a691`, plus migration-identity mismatch. No manifest was refreshed.

Exploratory inspection limitations: an unquoted nonexistent `reports/README*` glob produced a zsh no-matches diagnostic, followed by a successful explicit-path search; `ls backend/pytest.ini pytest.ini` reported that the root pytest.ini did not exist, and the actual backend configuration was read. These were inspection diagnostics, not failed acceptance tests. Some combined read outputs were truncated; policy/schema/source sections were subsequently read in focused calls. The captured acceptance outputs themselves are complete files. No pytest deprecation warning appeared in the targeted run; prior full-suite warnings were not claimed resolved.

## Changes, before/after semantics and remaining blockers

All new task files are confined to this unique audit directory. Existing application code, UI structure/rendering, biological definitions, explanation text, decisions, review flags, manifests, policies and frozen evidence remain unchanged. Before and after: 0 approved/releasable generated entries, deterministic fallback, 55 pending human claim decisions, 20 unread entries, no clinical expert review. Only the review package and evidence receipts were added.

Required human work: assess the pending 55 claims; read all 20 final exact entries with source/context; resolve flagged concerns, including those in prior bulk decisions; return actual decisions/times using the handoff template. Historical source/context attestation remains unproven. No automatic import, approval, text revision or manifest rebuild is authorized by returning an empty template.

F1 remains open. The all-stored-entry policy is unchanged; fallback does not waive it. A template-only policy requires separate explicit authorization and real review of applicable fallback content. Clinical expert review is neither fabricated nor newly made mandatory for the bounded research policy. No unconditional clinical-readiness claim is made.

## Final Git and authority boundary

Starting status: 1247 lines; final status: 1299 lines; 52 added untracked audit-file lines; 0 removed lines; no status changes outside this directory. Staged bytes: 0. See `git-status-start.txt`, `git-status-final.txt`, and `final-git-receipt.json`.

**No commit, staging, push, merge, tag, release, deployment or redeployment occurred. No remote configuration changed, no reviewer was contacted, and no genomic data were sent externally.**

## Changed files (new audit files only)

- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/HANDOFF.md`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/OWNER-REVIEW-PACKET.md`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/PROMPT-4A-REPORT.md`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/PROPOSED-TEXT-CHANGES.md`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/SOURCE-VERIFICATION.md`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/adjudication.stderr`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/adjudication.stdout`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/approval-release-tests.stderr`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/approval-release-tests.stdout`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/artifact-checksums.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/branch.txt`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/build-drafts-final.stderr`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/build-drafts-final.stdout`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/build-drafts.stderr`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/build-drafts.stdout`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/build-packet-final.stderr`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/build-packet-final.stdout`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/build-packet.stderr`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/build-packet.stdout`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/build_drafts.py`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/build_packet.py`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/commands.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/final-git-receipt.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/finalize_report.py`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/git-diff-final.txt`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/git-diff-start.txt`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/git-staged-final.txt`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/git-staged-start.txt`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/git-status-final.txt`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/git-status-start.txt`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/head.txt`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/inventory.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/original-explanation_approvals.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/original-explanations.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/packet-validation.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/packet-validation.stderr`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/packet-validation.stdout`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/pinned-source-guidelines.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/preserved-human-records.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/proposed-text-changes.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/release-content.stderr`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/release-content.stdout`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/review.stderr`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/review.stdout`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/reviewer-response-template.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/run_receipt.py`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/scope-after.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/scope-before.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/scope-extended-before.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/source-register.json`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/validate_packet.py`
- `audit-output/2026-10-03-prompt4a-8f4cbfbc76/web-verification-receipt.json`

Audit receipt checksums are in `artifact-checksums.json` (it excludes its own self-hash). These checksums are audit output, not a refresh of any production/scientific/approval manifest.
