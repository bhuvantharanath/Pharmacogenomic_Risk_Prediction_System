# Demo guide: several VCFs through the real UI

Use this alongside the 5-minute runbook in `docs/DEMO_SCRIPT.md`; its pre-flight section covers JDK 17, `infra/local-dev.env`, the pinned PharmCAT JAR and starting the backend. This guide adds a longer walk through the fixture classes verified in this audit. In the screenshots, `results-00.png` is the top of the results page and higher numbers scroll down. Every "expected" line below was observed in this audit's API and real-Chrome runs (`verification/case-matrix.md`). Results are research and educational output only. No clinical review has been obtained.

## Setup used in this audit

- Backend: `uvicorn app.main:app` on 127.0.0.1:8000, one worker, with `PHARMCAT_JAR` set to the pinned PharmCAT 3.4.0 JAR (SHA-256 `9317ef63…`), JDK 17, `STRICT_PHARMCAT=1`, `EXPLANATION_MODE=static` and CORS from `infra/local-dev.env`. The exact receipts are in `servers/final4-backend.command.json`.
- Web: `flutter build web --release --dart-define=API_BASE_URL=http://127.0.0.1:8000`, served on 127.0.0.1:3000 (`builds/web-final3.execution.json`).
- Each file goes in through the upload card (the browser's file chooser). Type the drug list into the drugs field, or use "Check all 6 medicines".

## Suggested order

| # | File (committed path) | Drugs | What you should see | Screens from this audit |
|---|---|---|---|---|
| 1 | `test-data/cyp2c19_poor_metabolizer.vcf` (synthetic) | all 6 | clopidogrel **Ineffective**, CYP2C19 \*2/\*2, PM. The quoted CPIC text keeps "Population: CVI ACS PCI". fluorouracil, azathioprine and simvastatin show No PGx-guided adjustment identified. warfarin and codeine are Unknown | `browser/run-final/screens/D02/results-00.png` |
| 2 | `audit-output/2026-09-30-f4/NA12878.observed.vcf` (real, read-backed) | all 6 | clopidogrel **Ineffective**, \*1/\*2, IM, ACS/PCI qualifier retained. The other drugs are Unknown because this file carries only the CYP2C19 positions. ACS/PCI is the guideline's population, not a diagnosis of the donor | `browser/run-final/screens/D05/results-00.png`, native PDF `browser/run-final4-print/cases/D05/print.pdf` |
| 3 | `audit-output/2026-09-30-f4/NA18526.observed.vcf` (real) | all 6 | clopidogrel No PGx-guided adjustment identified (\*1/\*1, NM). Everything else is Unknown | `browser/run-final/screens/D04/results-00.png` |
| 4 | `audit-output/2026-10-05-prompt7-5b236070c2/real-variant-only.vcf` (NA12878 with every 0/0 row removed) | all 6 | **every drug Unknown**. PharmCAT run directly on this file still reports CYP2C19 \*1/\*2 because it reads absent positions as reference. The app declines instead, and the warning says so | `browser/run-final/screens/D06/results-00.png` |
| 5 | `audit-output/2026-10-05-prompt7-5b236070c2/real-failed-filter.vcf` (one CYP2C19 position FILTER=LowQual) | all 6 | clopidogrel Unknown, under the heading **"A required genotype could not be used"**, with the remedy "re-call". Compare with #6 | `browser/run-final/screens/D10/results-03.png`, PDF page 4 `browser/run-final4-print/cases/D10/print-page-4.png` |
| 6 | `audit-output/2026-10-05-prompt7-5b236070c2/real-missing-required.vcf` (same position deleted) | all 6 | clopidogrel Unknown, under "Your file did not report enough positions" (the printed summary says "Your file is missing required positions"). The position is absent here, not unusable | `browser/run-final/screens/D12/results-03.png` |
| 7 | `test-data/demo/demo_normal.vcf` (synthetic, all 157 CYP2D6 positions present) | `clopidogrel,ibuprofen,codeine,warfarin` | clopidogrel answers (positive control). ibuprofen is outside the audited scope, so Unknown with no invented CPIC text. codeine is Unknown **even with 157/157 CYP2D6 positions**: "not called from an uploaded VCF by this application". warfarin is Unknown (no dose calculation) | `browser/run-final/screens/D15/results-00.png`, PDF `browser/run-final4-print/cases/D15/print.pdf` |
| 8 | any VCF over 5 MB (the audit used the PharmCAT-tutorial NA18526 bgzip, SHA-256 `a3e4676b…`, 11,181,875 bytes; not committed) | all 6 | HTTP 413 with the 5 MB message. Controls stay usable, and the next valid file analyses normally | `browser/run-final/screens/D08/error.png`, `browser/run-final/screens/D08/recovery-results.png` |
| 9 | a truncated gzip (the audit used `D09-real-truncated.vcf.gz`, SHA-256 `729feae0…`; any `.vcf.gz` with its last bytes cut works) | all 6 | HTTP 400, CORRUPT_GZIP: the file is rejected and never partly analysed, then recovery | `browser/run-final/screens/D09/error.png`, `browser/run-final/screens/D09/recovery-results.png` |

On result 2, finish with **Export JSON**, **Copy JSON** and **Printable summary**. In this audit the downloaded JSON and the clipboard JSON were byte-identical. Both equalled the API response after the one documented export transform: drop the deprecated `confidence_score`/`severity`, add `assessment_scope` and `application_capability` (`verification/exports-final.json`). The printed summary repeats the research header on every page. By policy it leaves out pipeline warnings, mechanism text and detected variants (`verification/print-final4.json` lists them).

## Points to make, and claims to avoid

- Say: "recommendation text is quoted from CPIC via PharmCAT". Avoid: "every statement is verified". The disclaimer now says that automated source checks are not human review.
- Say: "this application does not call CYP2D6 from a VCF". Avoid: "a VCF cannot represent CYP2D6". VCF 4.3 can encode copy number and structural variants; the limit belongs to this application.
- Say: "a genotype caller that reads a missing position as reference can give a confident wrong answer, so this application returns Unknown". Avoid implying that the app itself produces that wrong answer.
- Do not present the two read-backed controls (#2, #3) as validation. They are bounded positive controls. The 208-person cohort evaluation is described in `test-data/benchmark/current-candidate-2026-10-14/EVALUATION-REPORT.md`, and it reused the cached upstream reports; it was not a new caller run.

## Known rough edges you may be asked about (not changed in this audit)

The headline still reads "Pharmacogenomic risk prediction". Some mechanism text shows raw `**` Markdown. The progress panel quotes a "free shared CPU" wait even when the backend is local. The provenance stamp says "explanations generated 24 Jul 2026" although request-time templates are served. `/ready` reports 20 pre-generated explanations although none are approved for serving. The low-coverage explanation still says a reduced-function result "could be reported as safe".
