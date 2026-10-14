# Prompt 8 handoff (complete)

Read `PROMPT-8-REPORT.md` first. It holds the verdicts, the matrix, the defects, the identities and the human prerequisites. `DEFECTS.md` has the before/after record, and `DEMO-GUIDE.md` the walk-through.

Final candidate: scientific core `bd20329d…`, release artifact `dd013a62…`, bundle manifest `c9705961…`. The release gate is NOT READY. Only human prerequisites block it: 19 outstanding adjudications, 0/20 approved entries, and no clinical expert review.

## Processes

None left running. API, web and Chrome receipts with exit codes are in `servers/` and `browser/run-*/chrome-exit.json`. The scratch Chrome profiles and the isolated evaluation copy were deleted (`refresh/evaluation-copy-deleted.json`).

## Kept on disk, not committed

Large or regenerable outputs stay on disk and are left out of the commit:

- `builds/` (Flutter web builds)
- `fixtures/inputs/` (upload copies, including an 11 MB bgzip)
- `api-harness-*/pharmcat-direct/` (raw caller outputs)
- `api-captures-*`
- the full screenshot sets, downloads, events and browser-received bodies under `browser/run-*`
- `checkpoints/`
- `failed-attempts/`

The committed evidence is listed in `COMMITTED-EVIDENCE.txt`.

## Not this task's files

Other actors created these during the run. They were left untouched and are not committed:

- `test-data/vcf-library-2026-10-14/` and its `.zip`
- `output/repo-comparison-2026-10-14/`
- `output/PharmaGuard_Project_Report.docx`
- `tmp/college-report/`
- `tmp/college-ppt/`
