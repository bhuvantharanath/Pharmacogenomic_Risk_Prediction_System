# F6 browser acceptance continuation — 2026-10-01

Status: **open**. The app's JSON export reports success, but the browser cancels the download before receiving any bytes. The release gate remains NOT READY. No deployment or Git publication occurred.

## Local test setup

- Flutter web build served at `http://127.0.0.1:3000/`; local FastAPI/PharmCAT backend at `http://127.0.0.1:8000/` using pinned `pharmcat-3.4.0-all.jar` and `EXPLANATION_MODE=template`.
- Browser: Codex in-app Chromium browser, actual file chooser and rendered Flutter application. Service-worker/cache bypass was enabled in this test browser after rebuilding, to ensure the current local build loaded.
- Inputs: `audit-output/2026-09-26/derived/NA18526.1000G2022.vcf.gz`, `test-data/normal_metabolizer_control.vcf`, `test-data/cyp2c19_poor_metabolizer.vcf`, `audit-output/2026-09-26/originals/PharmCAT_tutorial_get-rm_wgs_30x_grch38.NA18526.vcf.bgz`, and `audit-output/2026-09-30-f4/NA18526.observed.vcf`.

## Observed browser cases

| Case | Result |
| --- | --- |
| Incomplete real VCF | File picker/upload succeeded (2.4 MB). Readiness 0/7; clopidogrel/codeine/warfarin Unknown. Clopidogrel detail now gives the missing CYP2C19 evidence (16/35 positions), without false reassurance. |
| Complete synthetic normal | Rendered supported no-PGx-change guidance and Unknown for unsupported codeine/warfarin. No percentage confidence displayed. Expanded genotype, coverage, warning, and provenance views were reachable. |
| Complete synthetic actionable | CYP2C19 *2/*2 poor metabolizer rendered clopidogrel Ineffective with the qualified CPIC action; no broad Safe claim. |
| Oversized real VCF | Clear 5 MB validation error and HTTP 413. No stuck loading state. After the functional fix, the backend connection indicator stays ready. |
| Unsupported ibuprofen | Unknown, with explicit audited-scope abstention. Expanded detail labels the action `APPLICATION LIMITATION — NOT A CPIC QUOTE`; template mechanism text does not claim CPIC authority. |
| F4 observed real NA18526 VCF | File picker/upload succeeded (170.8 KB). Readiness CYP2C19 1/7; clopidogrel *1/*1 normal guidance rendered and matched the API's patient/drug/risk/phenotype/action/summary. |
| Print | Actual browser print route opened a printable iframe/dialog. Unknowns carried their specific limitations and application abstentions were not labelled as CPIC quotes. |
| Scrolling/responsive | Expanded details and lower actions remained reachable; 360×640 narrow-screen view and desktop-sized viewport were inspected. No intentional visual redesign. |

## Export finding

- `Copy JSON` triggers the browser's success notification. The client model was corrected to retain backend `quality_metrics.position_coverage` evidence counts and decision-critical fields in its export; this is covered by a contract test. A full post-fix API-versus-export byte comparison is still outstanding.
- `Export JSON` triggers the app's “Downloaded …json” notification, but Chrome DevTools records `Page.downloadWillBegin` followed immediately by `Page.downloadProgress {receivedBytes: 0, state: canceled}` for the 15,767-byte Blob. Both export buttons behave this way. Waiting 30 seconds did not produce a completed download.
- A same-origin, test-only HTML probe using a 16,000-byte `Uint8Array` Blob and immediate URL revocation reached `receivedBytes: 16000, state: completed`. Thus the browser can download a comparable Blob, and immediate revocation alone is not an established cause. Temporary app experiments using delayed URL revocation and a string-backed Blob both still canceled and were reverted. No unverified production export workaround was left in place; the local web build was rebuilt from the reverted source.
- The browser automation download-event waiter timed out even on a probe whose DevTools progress reached `completed`; DevTools transfer events are the more reliable evidence in this environment.

## Fixes and checks

- Unknown results now use the audited drug/gene capability context when the backend redacts a gene to `Unknown`; an explicit backend abstention is displayed rather than “no reason recorded.”
- Application abstentions are separated from genuine CPIC quotations on screen and in print. The deterministic template no longer claims CPIC authority when no CPIC row matched.
- HTTP validation failures no longer mark a responsive backend as unreachable.
- Focused Flutter tests: 45 passed. Focused backend explanation/API tests: 86 passed. Full Flutter suite: 202 passed. Flutter static analysis: no issues. Web build: passed. Full backend suite: two failures in compatible-bundle identity checks; all other tests passed or were skipped.
- The two backend failures are expected evidence invalidation after changing a hashed scientific explanation file: the current application-core SHA differs from the checked manifest and the historical benchmark-to-portable-hash migration does not bridge to the changed core. Historical benchmark evidence was not rewritten or represented as rerun.
- `scripts/release_status.py --json`: `release_ready=false`, `state=not-ready`, 0 approved/releasable generated entries, 20 unapproved generated entries, 19 outstanding claims, clinical expert review `NOT_OBTAINED`, scientific bundle incompatible. This is the authoritative current gate result.

## Remaining work

1. Diagnose and fix the app-specific JSON download cancellation, with a browser regression showing a completed transfer and a readable saved file.
2. Recheck exact API/screen/copied/exported/printed scientific parity after the export fix, especially the retained coverage-evidence fields.
3. Perform a controlled scientific-manifest/benchmark identity update only under the repository's evidence procedure. Do not claim the old benchmark was rerun against the changed scientific core.

No human or clinical-expert approval was asserted; no release gate was weakened; no genomic evidence thresholds, PharmCAT calling, UI styling, or deployment state were changed for F6.
