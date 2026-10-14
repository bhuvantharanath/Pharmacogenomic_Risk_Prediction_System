# Reproduced defects — recorded before any code change

Candidate: base HEAD `1dc7557da49f38e831b382545044b00a481507b6`, dirty tree byte-identical to the Prompt 7 frozen inventory (437/437 entries, tracked diff SHA-256 `4fc44c3c…`; see `start/START-STATE.json`). Runtime: task-owned API on 127.0.0.1:8000 (capture wrapper over the unmodified app, pinned PharmCAT 3.4.0 JAR `9317ef63…`, JDK 17.0.17, `STRICT_PHARMCAT=1`, static explanations), release web build on 127.0.0.1:3000, task-owned Google Chrome 155 (isolated profile, CDP file-chooser fulfilment). Paths below are relative to this directory.

Regression tests were written first and run red against the unmodified code:
`regression/backend-red.stdout` (4/4 fail), `regression/flutter-red.stdout` (15 fail, 1 control passes). An earlier Flutter red attempt whose DEF-5 failure came from test set-up (off-screen taps), not the defect, is kept as `regression/flutter-red-attempt1-setup-issue.stdout`.

---

## DEF-1 — automated provenance described as a guarantee (previously reported, P1)

**Reproduced**
- API, every analysis: `llm_generated_explanation.disclaimer` = "…every clinical statement is machine-verified to come from a published CPIC recommendation, which checks that nothing was invented, not that it is correct for you." (`api-harness-baseline/D05.analyze.json`; identical in every case.)
- API warning in the same response: "This system writes no clinical content of its own: every clinical statement is machine-verified to trace to a CPIC recommendation…" while the adjacent provenance line says `explanation mode=static, source=template, guard=n/a (deterministic)` and "Pre-generated explanation was not served…".
- Browser: warnings disclosure shows the assurance (`browser/run-baseline/screens/D10/results-01.png`); About page box (`browser/run-baseline/screens/about/about-bottom-baseline.png`); home subtitle "…the explanations are pre-generated and checked against their source" (`browser/run-baseline/superseded/probe-offscreen-render-2.png`).
- Exports: the disclaimer travels in Export JSON and Copy JSON (e.g. `browser/run-baseline/cases/D05/download-*.json`, `clipboard.json`).
- Native print (Chrome Save-as-PDF via the UI route): "Every clinical statement here is machine-checked to trace back to a published CPIC recommendation. That verifies nothing was invented." (`verification/print-baseline.json` → `verbatim.source_checking_disclaimer`; D02/D05/D07/D10/D15).

**Facts that contradict the wording**: 0/20 stored entries are approved, so every served explanation is the deterministic template (`provenance_verified=False`, no runtime provenance check). `scripts/verify_provenance.py` reads only the stored `explanations.json` and documents itself as "a filter, not a verdict… It cannot detect a reversed claim assembled from sourced concepts".

**Violated invariant**: automated provenance must not be described as human review or as proof that invented claims are impossible, and served text must not be described as checked when it is not.

**Intended contract**: say that no clinical expert reviewed the text; that recommendation text is quoted from CPIC via PharmCAT; that automated source checks are not human review and cannot show every statement is supported or correct for the person.

**Surfaces**: `backend/app/models.py` DISCLAIMER = `app/lib/config.dart` kDisclaimer (byte-identity enforced by test); `backend/app/main.py` analysis warning; `app/lib/print/summary_document.dart` `_disclaimer()`; `app/lib/screens/about_screen.dart`; `app/lib/screens/home_screen.dart` subtitle.

## DEF-2 — this application's CYP2D6 limit described as a VCF format limit (NEW-FINDINGS item, reproduced)

**Reproduced**: `/coverage` CYP2D6 reason "Defined by copy-number and structural variation, which a VCF cannot express… no VCF will resolve it." (`api-harness-baseline/D01.coverage.json`); readiness footnote "CYP2D6: cannot be read from any VCF… a different file will not help" (`browser/run-baseline/screens/D01/readiness.png`); codeine card "…which a VCF cannot represent" and Unknown panel "A VCF records single positions, so it has no way to express that. This is a limit of the file format… No VCF, however complete, will." (`browser/run-baseline/screens/D10/results-0[3-8].png`); print "Not determinable from a VCF — …which a VCF file cannot represent" — D15's print shows this beside its own census row CYP2D6 157/157 present (`browser/run-baseline/cases/D15/print-page-3.png`).

**Primary sources** (`sources/source-receipts.json`): VCF v4.3 §5.3 "Encoding Structural Variants", reserved symbolic alleles DEL/DUP/CNV, FORMAT `CN` copy-number genotype; PharmCAT "Calling CYP2D6": does not recommend calling CYP2D6 from VCF because the phenotype is sensitive to SV/CNV, and accepts outside calls from specialised callers.

**Violated invariant**: an application capability boundary must not be presented as a property of the file format or as unresolvable "by any VCF".

**Intended contract**: this application does not call CYP2D6 from an uploaded VCF because copy-number/structural variation needs specialised read-level calling; uploading a different VCF here will not change the result. Calling behaviour is unchanged (codeine stays Unknown).

## DEF-3 — upstream missing-is-reference hazard described as this application's output (NEW-FINDINGS item, reproduced)

**Reproduced**: variants-only warning "…the consequence is NOT a missing result — it is a confident WRONG result: … a reduced-function patient is reported as normal" shown first in the expanded warnings of a response in which every drug is Unknown (`browser/run-baseline/screens/D06/results-00.png`, `api-harness-baseline/D06.analyze.json`). Print census note "A position that is absent reads as matching the reference, so missing data produces confident results rather than uncertain ones" on every PDF (`verification/print-baseline.json`).

**Fact**: the direct pinned caller does report CYP2C19 `*1/*2` from the variant-only file (`api-harness-baseline/pharmcat-direct/D06/`), while this application returns Unknown.

**Violated invariant**: the hazard belongs to genotype callers that read absence as reference; the application's own protective gate must be stated, not contradicted.

**Intended contract**: attribute the hazard to a genotype caller and state that this application reports genes without their required positions as Unknown. The measured figure and remedy are unchanged.

## DEF-4 — present-but-unusable genotypes explained as "not reported" (new, reproduced)

**Reproduced**: D10 (all 35 CYP2C19 rows present, FILTER=LowQual at chr10:94781859; API `evidence_counts` = `filter_failed: 1`, `absent_position: 0`) and D11 (`partial_genotype: 1`). UI: "1 of 35 positions were not reported in your file", "Your file did not report enough positions… carry no genotype", remedy "Upload a VCF that reports every position… A variants-only file cannot work here." (`browser/run-baseline/screens/D10/`, `D11/`); print "Your file is missing required positions… reports ALL positions" (`browser/run-baseline/cases/D10/print-page-4.png`); print census "reported 34".

**Violated invariant**: an Unknown explanation must describe the actual evidence failure; a FILTER failure or partial call is not an absent position, and its remedy is not "emit all sites".

**Intended contract**: when the API's typed counts show no absent positions but unusable genotypes, classify and explain it as unusable evidence (actionable: review/re-call), keep the absence explanation unchanged otherwise, and count the census line accordingly.

## DEF-5 — opened result cards collapse after a long scroll (new, reproduced)

**Reproduced**: fresh D01 analysis; open all six cards; scroll to Export/Copy/Printable; every card reports collapsed, still collapsed back at the top (`browser/run-baseline/def5/repro.json`, `01-expanded-top.png`, `02-bottom.png`, `03-back-at-top.png`). Widget test reproduces it (5/5 open → 0/5 after the same wheel jumps).

**Cause**: `SummaryGrid` keeps the open set in one lazily built `ListView` child without keep-alive (same pattern in `DisclosureRow`), so a long jump disposes and rebuilds it.

**Violated invariant**: expanded details stay expanded while the user scrolls the same results.

**Intended contract**: opened rows are kept alive while open; no visual or hierarchy change.

## DEF-6 — warfarin and codeine listed under "Drugs with CPIC guidance in this build" (new, reproduced)

**Reproduced**: home caption above the six chips (`browser/run-baseline/screens/D08/error.png`, `D01/readiness.png`) while the readiness panel on the same screen and every analysis return Unknown for both (explicit registry abstentions; `api-harness-baseline/D01.analyze.json`).

**Violated invariant**: scope copy must not promise guidance the build never gives.

**Intended contract**: name the six as this build's scope and say warfarin and codeine always return Unknown here.

---

## Observed, not changed (owner decisions or out of scope)

- Headline "Pharmacogenomic risk prediction" (original audit R3: product naming).
- Raw Markdown `**…**` in mechanism corpus text shown on cards (SLCO1B1, CYP2D6). Corpus bytes are bound into approval source hashes; changing them is a content/approval decision.
- Local progress panel says "free shared CPU… 50–60 seconds" against a local backend (~1.5 s measured).
- Provenance stamp "explanations generated 24 Jul 2026" while request-time templates are served.
- `/` reports `explanations_available: 20`, `/ready` "20 pre-generated (20 provenance-verified)" while 0 are servable.
- Sample labels "Answers confidently".
- API still returns deprecated `confidence_score`/`severity` (documented; exports omit them).
- Print omits pipeline warnings, mechanism, variant rationale, patient-friendly text and detected variants by summary policy (documented; JSON exports carry them).

---

# Fixes and after-state (appended after the fixes; the records above are unchanged)

Regression tests went red before any change (`regression/backend-red.stdout`, `regression/flutter-red.stdout`) and green after (`regression/backend-green.stdout`, `regression/flutter-green.stdout`). New test files: `backend/tests/test_disclosure_wording.py` (4 tests) and `app/test/disclosure_wording_test.dart` (16 tests). Full diff against byte-verified start snapshots: `diff/task-changes.patch` (30 files, +880/−175; index in `diff/task-changes.json`). Calling behaviour, labels, thresholds, genes, drugs and biological definitions are unchanged: every drug label in all 16 fixtures equals the baseline (`verification/case-matrix.json`, `labels_same_as_baseline`), and the API baseline→final difference is confined to four text paths (`verification/api-baseline-vs-final2.json`).

| Defect | Change | Regression tests | After-state evidence |
|---|---|---|---|
| DEF-1 provenance overclaim | `backend/app/models.py` DISCLAIMER = `app/lib/config.dart` kDisclaimer (byte-identical); `backend/app/main.py` analysis warning; `summary_document.dart` `_disclaimer()`; About box; home subtitle | disclaimer bounds + analysis response (backend); DEF-1 group (Flutter). `test_analyze_api.py` disclaimer assertion rewritten because it required the defective "nothing was invented" text | `api-harness-final2/*.analyze.json`; `verification/print-final4.json` (final build, native PDF); F4 replay `no_invention_guarantee` check (`refresh/f4-fresh-replay.json`) |
| DEF-2 CYP2D6 limit blamed on the VCF format | `coverage.py` CYP2D6 reason; readiness footnote; verdict card; Unknown panel and headline; print | CYP2D6 boundary incl. `/coverage` (backend); DEF-2 group (Flutter); `test_coverage_endpoint.py`, `print_summary_test.dart`, `redesign_test.dart`, `unknown_reason_test.dart` updated (they asserted the format claim) | `browser/run-final/screens/D10/results-04.png`; `browser/run-final4-print/cases/D15/print-page-3.png`; codeine is Unknown in all 15 label fixtures |
| DEF-3 caller hazard described as this app's output | `variants_only_warning()` attributes the hazard to genotype callers and states the app reports such genes as Unknown; print census note | variants-only attribution (backend); DEF-3 group (Flutter) | `api-harness-final2/D06.analyze.json` warnings; `verification/print-final4.json` → `census_note` |
| DEF-4 unusable genotype explained as absent | new `UnknownReason.unusableGenotypes`; `GeneCoverage.absentPositions/unusablePositions` from the API's typed `evidence_counts`; census, panel and print wording; census column "usable" | DEF-4 group (Flutter); `readiness_test.dart`, `state_census_test.dart` (enum count 5→6), `unknown_reason_test.dart` updated | `browser/run-final/screens/D10/results-03.png`; `browser/run-final4-print/cases/D10/print-page-4.png`; D12 (truly absent position) keeps the absence explanation |
| DEF-5 opened cards collapse after a long scroll | `SummaryGrid` and `DisclosureRow` keep themselves alive while any row is open (`AutomaticKeepAliveClientMixin`); no visual change | DEF-5 widget test (5 open → 5 open after ±3000 px × 8 wheel jumps) | `browser/run-final3/def5/repro.json`: cards still open at the bottom and back at the top (baseline: all collapsed) |
| DEF-6 warfarin/codeine listed as having guidance | home caption names the six as this build's scope and says warfarin and codeine always return Unknown | DEF-6 source-text test | `browser/run-final/screens/D01/readiness.png` (caption and the DEF-2 footnote on the same screen) |
| Follow-up (found while fixing DEF-4) | print Unknown-section intro said "Only one of these reasons is something the sample provider can act on", false once two reasons are actionable | red: `regression/flutter-red-print-intro.stdout`; green: `regression/flutter-full-after-print-intro.stdout` | `verification/print-final4.json` → `unknown_section` (D05, D10, D15 native PDFs from the final build) |
