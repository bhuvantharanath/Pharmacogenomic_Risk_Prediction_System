# Phase 10 — acceptance criteria

Written 2026-11-12, at commit `fdb27cb`, before any showcase sample was
converted or run. Nothing below is to be edited to fit a result. If a criterion
turns out to be wrong as written, it stays, and the correction is recorded
beside it with a date.

One thing was measured before this file existed, and it is stated here so the
order is not misread: the brief puts the source reachability test first and
asks for an immediate report if it fails, so that test (section 3, R1 and R2)
was run before this file was written. Both passed. Every other criterion was
written before its measurement.

## 1. The rule that outranks every criterion

No change to the coverage gate, the phenotype→label invariant, the
sourceDiplotypes handling, the ambiguity representation, or any verification
edge. A showcase cell that is Unknown after the data work is corrected by
better input or recorded as a genuine limitation. It is never corrected by a
loosened check.

How this is checked, not asserted: `demo/protected_files.sha256` holds the
SHA-256 of seventeen files as they stood at `fdb27cb` (the coverage gate, the
label engine and mapping, the evidence cross-check, the PharmCAT runner and
models, VCF validation, the REF check, the capability registry, the outside-call
door, the response models, the position requirements, the explanation store and
its approvals). At the end of the step,

```bash
shasum -a 256 -c demo/protected_files.sha256
```

must report every file `OK`. One `FAILED` line means "Invariants touched" is
not NONE, and the step stops there.

## 2. The product bar (from the brief, section 2)

1. A reviewer can open the public web URL on their own phone or laptop, upload
   one of the provided real sample files, and get a complete clinical result in
   a single pass.
2. For the curated showcase set, every gene–drug cell renders a real
   CPIC-backed label: no Unknown, no blank, no "—", no "not available". The
   single declared exception is CYP2D6 from a VCF, handled in section 4 of the
   brief.
3. Every result is traceable: real public sample ID, real PharmCAT call, real
   CPIC guideline row, with versions shown in the UI.
4. The showcase set contains genuine clinical variety, not six green badges: at
   least one Toxic, one Ineffective, one Adjust Dosage and one Safe, each from a
   real sample's real genotype.
5. Cold start does not make it look broken in front of a room.
6. Nothing in the UI claims clinical validity, faculty sign-off, or external
   concordance beyond what the project has (n=1 external truth).

Criteria 1, 5 and 6, and the UI half of criterion 3, belong to the work after
the step-4 stop. Criteria 2, 3 (data half) and 4 are measured at step 4.

### Facts found in the repository before any measurement

These were read from the tree at `fdb27cb`. They are recorded now because each
one changes how a criterion above can be met, and recording them after the
runs would look like fitting the bar to the result.

**F1. "Safe" is served as "No PGx-guided adjustment identified".**
`backend/app/models.py`, `RiskLabel.SAFE`. Wherever the brief says Safe, the
string to expect is that one.

**F2. Warfarin is a deliberate abstention, so criterion 2 cannot hold for it.**
`backend/app/data/capabilities.json` declares warfarin
`implementation_status: explicit_abstention`, `guidance_capable: false`. CPIC's
warfarin guidance is a dosing algorithm that needs ancestry and clinical
factors this application does not collect, so every warfarin result is Unknown
whatever the file contains, and the CYP2C9, VKORC1 and CYP4F2 calls are shown
for reference. The brief's table suggests "CYP2C9 intermediate → warfarin" as
an Adjust Dosage source; under the shipped registry that cell cannot produce a
label, and changing the registry is not input work.

Consequence, declared in advance: warfarin is counted as a second deliberate
Unknown beside CYP2D6-from-VCF. Criterion 2 is therefore reported two ways at
step 4, as cells with a real label out of all cells, and out of the cells the
shipped application can label, so neither number hides the other. Whether
warfarin should stay an abstention is the owner's decision and is raised in the
step-4 report.

**F3. Capecitabine is not in the capability registry.** The brief lists it
beside fluorouracil. A request for it returns Unknown as "outside the audited
application scope". The showcase therefore asks for the six registered drugs:
clopidogrel, simvastatin, azathioprine, fluorouracil, warfarin, codeine.

**F4. The requirement is 484 positions over nine genes, not 306 or 463.**
`backend/app/data/position_requirements.json`: CYP2C19 35, CYP2C9 88,
SLCO1B1 35, TPMT 45, NUDT15 20, DPYD 83 (these six are the brief's 306), CYP2D6
157 (which makes 463), and VKORC1 1 and CYP4F2 20 added in Phase 9. A
conforming showcase file carries all 484.

**F5. The application runs the PharmCAT jar directly, with no preprocessor.**
`backend/app/pharmcat_runner.py`. A file must already have one row per
required position in the REF/ALT form of PharmCAT's own positions file.

## 3. Step criteria, steps 1 to 4

### Step 1 — source reachability

- **R1.** An anonymous HTTPS list of `s3://1000genomes-dragen-v4-4-7/` returns
  HTTP 200 and names at least one object or prefix.
- **R2.** An indexed range read of one sample's `hard-filtered.gvcf.gz`
  returns records for the requested region with exit status 0, and at least one
  returned record is a reference block (`<NON_REF>` with `END=`).

If either fails: stop, report, no fallback.

### Step 2 — cohort

- **C1.** Six to eight samples, each a real 1000 Genomes sample ID present in
  `test-data/reference/1000G_3202_populations.txt` and in the source bucket.
- **C2.** Expected label per sample and drug written to `demo/COHORT.md` and
  committed before the conversion tool is run on any cohort sample. The
  expectation is derived from an independent caller's star alleles and
  `test-data/reference/cpic_expectations.json`, never from this pipeline.
- **C3.** The expectations, taken together, include at least one Toxic, one
  Ineffective, one Adjust Dosage and one "No PGx-guided adjustment identified".
- **C4.** At least two samples from the South Asian subpopulations (PJL, BEB,
  STU, ITU, GIH), described as 1000 Genomes subpopulations.
- **C5.** A disagreement between an expectation and the pipeline is listed as a
  finding. `COHORT.md` is not edited to remove it.

### Step 3 — conversion tool (`scripts/build_showcase_inputs.py`)

- **B1. Nothing assumed.** A row is emitted only where the source gVCF carries
  a record covering the position: a reference block, or a record at the
  position. A position with no covering record gets no row. `--absent-to-ref`
  and anything equivalent are not used.
- **B2. Nothing upgraded.** FILTER is copied from the source record. A row is
  never written as PASS unless every source record it rests on is PASS. A
  no-call in the source stays a no-call.
- **B3. Nothing guessed.** A genotype is transcribed only when each called
  allele is identical, base for base, to the reference or to an allele in
  PharmCAT's row for that position. An allele PharmCAT does not list, or a
  variant record that overlaps a required position without starting at it, is a
  refusal for that sample, not an approximation.
- **B4. Phase is not carried.** Genotypes are written unphased. DRAGEN's phase
  sets do not span a gene and PharmCAT reads `|` as phased across one, so
  carrying phase would state more than the source does.
- **B5. Refusal, not a weak file.** The tool writes a sample file only if the
  repository's own `validate_vcf` accepts it and `coverage.assess` reports
  every required position of the eight genes the application reads from a VCF
  (the six, VKORC1, CYP4F2) as `valid_observed_genotype`. That is 327 of 327,
  stricter than the gate's own thresholds and never weaker. CYP2D6 rows are
  carried where the source supports them and do not decide emission, because no
  VCF content makes this application call CYP2D6.
- **B6. The presence check has a positive control.** A test damages the input
  three ways (a covering record removed; a FILTER changed to a failing one; a
  genotype made a no-call) and the tool refuses each time, while the undamaged
  input is accepted. A check that reports success on all four is broken.
- **B7. Subprocess discipline.** Every subprocess runs with `check=True` and
  its return code is read; no pipe hides a status. A query that returns no
  records is a hard failure.
- **B8. Deterministic.** Two runs over the same retrieved slice produce
  byte-identical output, so the checksum in a sidecar can be reproduced.
- **B9. Every guard above has a test that fails when the guard is removed.**

### Step 4 — run and ledger

- **L1.** Every showcase sample is run through the local pipeline and the live
  API with the six registered drugs. The two responses agree field by field,
  apart from `processing_time_ms`.
- **L2.** `demo/UNKNOWN_LEDGER.md` has one row per Unknown or missing value,
  with its root cause from the six classes in the brief.
- **L3.** The ledger ends with zero rows in three classes: position missing
  from the source file, missing explanation entry, client rendering gap.
- **L4.** Every remaining row is a deliberate, documented state. By F2 and the
  brief's CYP2D6 exception, the rows expected in advance are exactly: warfarin
  on every sample, and codeine on every sample. Any other row is unexpected and
  is investigated to a root cause.
- **L5.** The labels come from the input and from nothing else. For every
  showcase sample, removing the homozygous-reference rows from the same file
  returns clopidogrel, simvastatin, azathioprine and fluorouracil to Unknown.
- **L6.** Section 1's hash check reports every file `OK`.

## 4. What these criteria do not establish

A passing step 4 shows that complete real input produces real CPIC-backed
labels through an unchanged pipeline. It does not validate those labels against
clinical truth. External truth for this project remains n=1, and no clinical
reviewer has read the output. The showcase is evidence about the input
requirement, not about accuracy.
