# B9 — Standards-based export

Part B item 9 of the Phase 9 brief:

> - Add "Download report" → (a) a PDF summary and (b) an **HL7 FHIR Genomics
>   Reporting IG (STU3, R4)** bundle: Genomics Report, Genotype/Haplotype
>   observations, Therapeutic Implication per drug, with the CPIC guideline as
>   the related artifact. Unknown results must be exported as Unknown with their
>   reason, never omitted.
> - Validate the bundle with the official HL7 FHIR validator CLI (free, Java —
>   same JDK) in CI.

Written 2026-11-06 before any B9 code. Its sha256 goes into `audit/phase9/B9.log`
before the first edit. Nothing here is edited after measurement.

## State at B8 (3b1755a, live)

### What a user can take away today

- **Printable summary.** `app/lib/print/summary_document.dart` builds one HTML
  document. On web it opens the print dialog; on iOS and Android the OS renders
  it to PDF. On web there is no PDF file to download. Its tests assert the
  disclaimer, every Unknown with its reason, the coverage census and the
  provenance as text.
- **Export JSON.** The raw `/analyze` response.
- **No FHIR export.**

### What the API serves per drug (S1–S6, local B8 run)

- The drug, the risk label, the primary gene, the diplotype and the phenotype.
- The CPIC action text, quoted from PharmCAT's CPIC annotation, and its
  evidence level.
- `source`: the guideline's name "(via PharmCAT)" and the label rule.
- For an Unknown result, gene, diplotype and phenotype are all the string
  `Unknown`.
- `quality_metrics.guideline_provenance` gives the PharmCAT version, the CPIC
  data version, the CPIC table SHA-256 and the allele-definitions version and
  SHA-256.
- The guideline's URL is in PharmCAT's report and parsed by the backend
  (`guideline_url`), but the API does not serve it.

### Which drugs have a gene

`kDrugCapabilities` (generated from `backend/app/data/capabilities.json`) gives
six drugs a primary gene:

- implemented: clopidogrel, fluorouracil, azathioprine, simvastatin;
- explicit abstentions: warfarin, codeine.

The API also accepts other drugs; S6 has ibuprofen. Such a drug comes back
Unknown, and the response names no gene for it.

### The validator (measured 2026-11-06)

- **Release.** HL7 FHIR validator CLI 7.0.2, from HAPI FHIR's GitHub release
  (2026-10-15): 204,412,235 bytes, sha256
  `e3e50f06b806437821b7aef8189a1b790415cb96c5036e0812ed62981452b377`.
- **Runs here.** It runs on this machine's JDK with
  `-version 4.0.1 -ig hl7.fhir.uv.genomics-reporting#3.0.0 -tx n/a`.
- **IG examples are clean.** The IG's own PGx examples `TxImp01` and
  `GenotypeExamplePharmVar` validate with 0 errors. They still have 0 errors
  with `subject`, `performer` and `specimen` removed and status `preliminary`.
- **Scientific core.** `app/lib/**` and the pubspec are in it, so B9 needs a
  re-bind.

## Design

### 1. FHIR bundle (client, `app/lib/export/`)

A pure function from the parsed `/analyze` response (plus the export time) to a
FHIR R4 `Bundle` of type `collection`:

- Resource ids are deterministic, so the same response gives the same bundle.
- No new network call.
- It is built in the client because the Unknown reasons a user reads are
  computed there (`classifyUnknown`, `unknownExplanation`). The export must
  carry the same words.

**Resources**

- **Genomic Report** (`DiagnosticReport`, profile `genomic-report`):
  - LOINC 51969-4 and category `GE`;
  - `effectiveDateTime` is the analysis time; `issued` is the export time;
  - `result` lists every Observation;
  - `conclusion` lists every drug with its label, in the summary's order;
  - a `genomic-report-note` coded `test-disclaimer` carries the printable
    summary's disclaimer;
  - a second note carries the guideline provenance.
- **Specimen**: the VCF's sample name as its identifier. No Patient resource is
  made up; a sample name is not a patient.
- **DocumentReference**: the uploaded VCF, described and not included.
- **Genotype** (`Observation`, profile `genotype`, LOINC 84413-4), one per gene
  assessed:
  - **Called** (the served gene and diplotype are not `Unknown`): value text
    `<gene> <diplotype>`.
  - **Not determined** (an Unknown drug with a capability gene): no value,
    `dataAbsentReason` `unknown`, and the Unknown reason as a note.
  - In both cases, the gene is the `gene-studied` component as text, and the
    observation is `derivedFrom` the DocumentReference.
- **Therapeutic Implication** (`Observation`, profile
  `therapeutic-implication`), exactly one per analysed drug, Unknown included:
  - `medication-assessed` (LOINC 51963-7) is the drug, as text.
  - `therapeutic-implication` is the served phenotype as text, or `Unknown` for
    an Unknown result.
  - `conclusion-string` is the served CPIC action text verbatim when it is a
    CPIC quote. For an Unknown result it is the app's Unknown explanation.
  - A note says `PharmaGuard result: <label>`. An Unknown result also gets its
    reason headline and what would fix it.
  - `workflow-relatedArtifact` (type `citation`, citation = the served `source`)
    when the result quotes a matched CPIC entry.
  - `derivedFrom` points to the gene's Genotype, if there is one, and always to
    the DocumentReference.
- **Narratives.** Every resource gets one.

**Honesty choices**

- **Statuses.** The report is `partial` and every Observation is `preliminary`.
  FHIR defines a final report as "complete and verified by an authorized
  person". No one verifies these results, and `partial` / `preliminary` say
  "unverified" in FHIR's own words.
- **Codes.** Every code is one the profiles fix. Drug, gene, phenotype and label
  are text, not codes from RxNorm, HGNC or the IG's phenotype value set. Mapping
  them would be new authored content the validator cannot check without a
  terminology server. Phenotype codes also depend on the gene: SLCO1B1's CPIC
  terms are function terms, not metabolizer terms.
- **The guideline.** It is cited by the served `source` text. Serving its URL
  needs an API change and is out of scope (see the end of this plan).

### 2. PDF summary (client, `app/lib/print/summary_pdf.dart`)

- **Content.** Built with the `pdf` package, already a dependency. It places
  the same text as the printable HTML summary, node for node, in the same
  order. The HTML builder is not edited.
- **Running header.** The disclaimer header repeats on every page
  (`MultiPage` header).
- **Fonts.** The app's own: Newsreader for prose, IBM Plex Mono for machine
  output.
- **Drift is prevented by a test, not by hope.** The builder records every
  string it places. A test compares that sequence with the HTML summary's text
  nodes for every fixture. If either document gains or loses a sentence, the
  test fails.
- **Character coverage.** A test checks that every character placed is in the
  font that draws it.

### 3. Download

- **The control.** A "Download report" control on the results screen offers
  "PDF summary (.pdf)" and "FHIR Genomics Report (.json)".
- **The seam.** One download function, split by platform the way
  `json_export` is: a blob download on web, a file in the temp directory
  elsewhere.
- **Unchanged.** "Printable summary" and "Export JSON".

### 4. Validation in CI and in the gate

- **The script.** `scripts/validate_fhir_exports.py` does five things:
  - fetches the validator if it is missing;
  - refuses a jar that does not match the pinned size and sha256 (the pin lives
    in `scripts/fhir_validator.json`);
  - has a Flutter test write one bundle per fixture response;
  - validates all of them with the pinned validator and IG, terminology server
    off;
  - fails on any error or fatal.
- **Positive control.** The same run validates a copy of one bundle with
  `DiagnosticReport.code` removed. If that copy has no error, the script fails.
- **Where it runs.** A seventh required check of the release gate
  (`fhir-validation`), and a step in `test.yml`'s Flutter job with Java added.

### 5. Fixtures

`app/test/fixtures/responses/` holds real `/analyze` responses:

- S1–S6, copied from the local B8 run (`audit/phase9/partb/B8/s1-s6`);
- X1: `demo_confident.vcf` with all six capability drugs plus ibuprofen,
  produced by the B8 backend in-process.

Together they cover:

- a confident CPIC quote (PM, NM);
- Unknown for missing coverage;
- Unknown by explicit abstention (codeine, warfarin);
- Unknown for a drug outside the capability table (ibuprofen);
- several drugs on one gene.

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | Validity: for every fixture, the exported bundle validates with the pinned validator 7.0.2 against `hl7.fhir.uv.genomics-reporting#3.0.0` (FHIR 4.0.1, `-tx n/a`) with 0 errors and 0 fatal. Every warning is listed in B9.log, grouped by message. In the same run the positive control (`DiagnosticReport.code` removed) has at least one error |
| AC2 | Completeness, by test, for every fixture: exactly one Therapeutic Implication per analysed drug, so every Unknown is there and no drug is dropped or doubled. Every `derivedFrom` and every `DiagnosticReport.result` entry resolves inside the bundle. `result` lists every Observation exactly once |
| AC3 | Fidelity, by test, for every Therapeutic Implication. (a) The medication text is the served drug. (b) The note's label is the served label. (c) The `conclusion-string` is the served action, character for character, for a matched CPIC entry, and the app's own `unknownExplanation` for an Unknown. (d) The related artifact is present, citing the served `source`, exactly when a CPIC entry matched. (e) The phenotype text is the served phenotype, and `Unknown` for an Unknown result. For every Genotype: the value is `<gene> <diplotype>` from the served profile. An Unknown whose served gene is `Unknown` gets `dataAbsentReason` and never a value |
| AC4 | Honesty, by test: (a) the report is `partial` and every Observation `preliminary`; (b) the report carries the printable summary's disclaimer (equal after whitespace normalisation) as a `test-disclaimer` note and in its narrative; (c) its provenance note equals the served `guideline_provenance` fields; (d) no Patient resource is created, and the sample appears only as the Specimen identifier |
| AC5 | PDF, by test, for every fixture: (a) the PDF builds; (b) the strings it places, in order, equal the HTML summary's text nodes, whitespace-normalised, apart from the running header; (c) the running header is on every page; (d) every placed character is in its font. Independently (evidence, not CI): for S1–S6, text extracted from the PDFs with pypdf contains every label, CPIC quote, Unknown reason and the disclaimer |
| AC6 | UI, by widget test: the results screen's "Download report" control offers both files. Each reaches the download seam as non-empty bytes, with a `.pdf` or `.json` name and the right media type. "Printable summary" and "Export JSON" behave as before |
| AC7 | CI: `validate_fhir_exports.py` runs as a required check of the release gate and in `test.yml`, and verifies the pinned jar before running it. The full backend and Flutter suites pass, and the release gate is ready |

## Zero-regression

- **S1–S6, cohort, 74 PharmCAT VCFs, A4:** identical to B8 in labels, statuses
  and warnings. The backend is not changed.
- **Printable HTML summary:** for every fixture, its sha256 is recorded before
  the first B9 edit and is unchanged after.
- **External evaluation:** the re-bind shows no eligibility or discrepancy
  change against B8's package.

## Sabotage

Each must turn a test (or the validation script) red, and the files are
restored byte-identical afterwards.

| id | sabotage |
|---|---|
| SB9-a | the FHIR builder skips Unknown results |
| SB9-b | the `conclusion-string` drops the last character of the CPIC text |
| SB9-c | the Genomic Report loses its LOINC code (the validator must fail it) |
| SB9-d | the related artifact is left off a matched CPIC entry |
| SB9-e | the report status becomes `final` |
| SB9-f | the PDF builder leaves out the Unknown section |
| SB9-g | the PDF's running header is left off pages after the first |
| SB9-h | the download control loses the FHIR item |

## After deploy (only if the owner approves a deploy)

Live criteria, to be logged before measuring:

- **Commit.** The Deploy run succeeds and `/ready` reports the commit.
- **S1–S6.** Labels, gene findings and warnings equal the local B9 run.
- **Bundle.** The production web bundle carries the new control's strings.
- **Exports from live responses.** The live S1–S6 responses, exported by the
  same code, validate with 0 errors.
- **Browser.** In the built-in browser, the production results page shows the
  "Download report" control with both items. Nothing is downloaded there
  without the owner's approval.

## Out of scope

- **Serving the guideline URL.** It needs a backend response change. It would
  let the related artifact carry a link, not only a citation.
- **Coded drug, gene and phenotype.** RxNorm, HGNC and LOINC answer codes, for
  the reasons above.
- **A server-side export endpoint.**
