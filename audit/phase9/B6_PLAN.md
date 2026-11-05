# B6 — Input robustness

Part B item 6 of the Phase 9 brief ("Detect genome build (contig lengths in header
and/or REF checks at known positions); refuse GRCh37 with a specific message.
Normalise contig naming; define and enforce multi-sample behaviour; route gzip/BCF
through PharmCAT's preprocessor if supported, otherwise clean 4xx. Every A4 row
becomes a permanent test with its pre-committed expectation.").

Driven by A4 (`audit/phase9/A4_PRECOMMIT.md`; results `audit/phase9/a4/RESULTS.md`,
kept local) and findings F-02 (no REF identity check, high, false reassurance),
F-05 (contig names without `chr`) and F-06 (wrong-build and gVCF inputs declined
for the wrong reason). It also carries the file-level REF check that B3 left in
scope for B6 (`audit/phase9/B3_AC5_AMENDMENT.md`).

Written 2026-11-05 before any B6 code. Its sha256 is recorded in
`audit/phase9/B6.log` before the first edit. Nothing below is edited after
measurement; a criterion that fails is reported, not changed.

## State at B5 (f8fc84d)

- A4-02, GRCh37 coordinates with only `##contig=<ID=10,length=135534747>`: declined
  through coverage alone, under "assuming GRCh38" and the research-format/SNP-array
  diagnosis (PARTIAL).
- A4-03 (`10`) and A4-20 (`Chr10`): `/coverage` calls clopidogrel answerable and
  `/analyze` returns Unknown, because PharmCAT does not read those names (B3 now
  names the positions it did not use).
- A4-08b, gVCF with reference blocks: declined (right) under the research-format/
  SNP-array diagnosis (wrong).
- A4-09a and A4-09b, REF contradicting GRCh38 at 10 CYP2C19 rows or at rs4244285:
  clopidogrel declined by B3; azathioprine, fluorouracil and simvastatin keep
  confident labels from the same file.
- A4-22 and A4-23, an hg19-style file at GRCh38 coordinates with GRCh37 `length=`:
  every drug declined by B3, as 200 Unknown.
- A4-06, `.bcf`: 400 NOT_VCF, "is not a text VCF file"; BCF is not named.
- Every other A4 row passed and must keep passing.

PharmCAT's own rules, read 2026-11-05 from its documentation: a position not in
the VCF is a no-call; CHROM must begin with `chr`, which its preprocessor fixes;
its preprocessor refuses gVCF unless told the file is not one; its REF alleles are
GRCh38's, and a REF mismatch "cannot be fixed by normalizing". The jar path this
application uses has no preprocessor, so these rules are applied here.

## Design

1. **Contig names.** Before anything reads the rows, a CHROM of `N` or `chrN` in
   any letter case (`10`, `Chr10`, `CHR10`), for N in 1–22, X, Y, M and MT, is
   rewritten to `chrN` (`chrX`, `chrY`, `chrM`) in the data rows and in the
   `##contig` IDs. The coverage gate and PharmCAT both read the rewritten text. A
   file whose names are already `chrN` is passed on byte-identical. When a name
   was rewritten, a warning says which and to what.

2. **Build from contig lengths.**
   - **Source.** `scripts/derive_build_evidence.py` adds the GRCh38.p14 and
     GRCh37.p13 lengths of chromosomes 1–22, X and Y. They come from NCBI's
     assembly reports (GCF_000001405.40, GCF_000001405.25), and each report's URL
     and sha256 are recorded in `build_evidence.json`.
   - **Why this reverses the script's note.** The script currently says lengths
     are not used, because PharmCAT ships none and the brief of that time forbade
     memory or outside sources. This brief asks for contig lengths, and an NCBI
     report with its hash recorded is a source, not a memory.
   - **Rule.** For a `##contig` line naming a primary chromosome with `length=`:
     - equal to GRCh38's: GRCh38 evidence;
     - equal to GRCh37's: 400 `UNSUPPORTED_REFERENCE_BUILD`, naming the contig,
       its length and that this is GRCh37's length;
     - equal to neither: 400 `UNSUPPORTED_REFERENCE_BUILD`, naming the contig,
       its length and GRCh38's length.
   - **Conflicts.** GRCh37 and GRCh38 evidence in one header (lengths, accessions
     or declarations) stays 400 `CONFLICTING_REFERENCE_BUILD`.

3. **REF identity.**
   - **Data.** `scripts/derive_reference_alleles.py` writes
     `backend/app/data/reference_alleles.json`. It holds the GRCh38 reference
     base at every required position of the analysed genes (the 484 positions of
     `position_requirements.json`), taken as the first base of the VCF REF in the
     pinned PharmCAT jar's allele definitions, with the jar's sha256. `--check`
     re-derives the file and compares.
   - **Check.** For every data row at one of those positions, the first base of
     its REF, upper-cased, must equal that base.
   - **If any differ, the whole file is declined with a 400**, for every drug:
     - if at least 10 positions were compared and at least half differ:
       `UNSUPPORTED_REFERENCE_BUILD`, saying the REF alleles at n of m required
       positions differ from GRCh38, so the file was most likely aligned to
       another build;
     - otherwise `REFERENCE_ALLELE_MISMATCH` (a new code), naming the count and
       up to five positions (chrom:pos, rsID, gene, the file's base, GRCh38's
       base).
   - **The two codes differ in wording, not in safety:** both decline the whole
     file. The whole file, because a REF that contradicts GRCh38 means the file
     was not made against the reference this analysis reads. That cannot be
     confined to the rows where it shows.
   - **Build warning.** Today a header that names no build gets "...assuming
     GRCh38". When at least one position was compared and none differ, that
     warning is replaced by one stating the evidence ("the REF alleles at all n
     required positions in this file match GRCh38, so it is read as GRCh38").
     When the contig lengths already establish GRCh38, no build warning is given.

4. **gVCF.**
   - **Detection.** The coverage gate recognises reference blocks: ALT containing
     `<NON_REF>` or `<*>`, with INFO `END=` beyond POS.
   - **Coverage.** A required position inside a block without a row of its own
     stays not covered, as PharmCAT would read it.
   - **Warning.** When any required position lies inside a block, a warning names
     the file as a gVCF, gives the number of such positions, and says to export
     every required position as its own row.
   - **Diagnoses withheld.** Such a file gets neither the research-format/
     SNP-array diagnosis nor the variants-only warning.
   - **Unchanged case.** A gVCF-shaped file whose required positions all have
     their own rows (A4-08a) is analysed as today.

5. **BCF.** A BCF upload (BCF magic, compressed or not) gets 400 `NOT_VCF`. Its
   message names BCF and says to convert it to VCF (`bcftools view -Ov`).

6. **Multi-sample.** Unchanged: 400 `UNSUPPORTED_MULTISAMPLE`, now under a
   permanent test.

7. **Permanent A4 tests.** Every A4 row becomes a permanent pytest
   (`backend/tests/test_a4_inputs.py`).
   - Its input is rebuilt at test time from `test-data/demo/` by a test helper.
     The BCF comes from a committed fixture checked by sha256.
   - Its expectation is the pre-committed A4 one, narrowed to the behaviour above
     where A4 allowed a choice.

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | Contig names: A4-03 (`10`) and A4-20 (`Chr10`) give clopidogrel Ineffective with CYP2C19 `*2/*2`, as the base file does; `/coverage` lists clopidogrel answerable for both (preview and result agree); each response carries the rename warning; a `chr`-named file reaches PharmCAT byte-identical (test) |
| AC2 | Contig lengths: `build_evidence.json` lengths equal NCBI's reports (`--check`, logged); A4-02 → 400 `UNSUPPORTED_REFERENCE_BUILD` whose message names GRCh37 and the contig; one GRCh38 and one GRCh37 length → 400 `CONFLICTING_REFERENCE_BUILD`; a primary-contig length matching neither → 400 `UNSUPPORTED_REFERENCE_BUILD`; GRCh38 lengths with no declaration → accepted with no build warning |
| AC3 | REF identity: `reference_alleles.json` covers all 484 required positions and a test recomputes it from the jar; A4-09a → 400 `REFERENCE_ALLELE_MISMATCH` stating 10 positions; A4-09b → 400 `REFERENCE_ALLELE_MISMATCH` naming chr10:94781859 and rs4244285; A4-22 and A4-23 → 400 (every drug declined); `/coverage` returns the same status and code for each |
| AC4 | gVCF: A4-08b → clopidogrel Unknown with a warning naming gVCF and the number of required positions inside blocks, and neither the research-format/SNP-array diagnosis nor the variants-only warning; A4-08a → Ineffective, as the base |
| AC5 | BCF: A4-06 → 400 `NOT_VCF` whose message names BCF and says to convert to VCF |
| AC6 | Permanent A4: every A4 row has a test asserting its pre-committed expectation, with inputs rebuilt at test time. That covers A4-01 to A4-26, the 33 inputs of `A4_PRECOMMIT.md` and its addenda. Each rebuilt input equals the Part A input where that file exists locally: compressed inputs are compared after decompression, the gzip bomb by its expanded size. This is checked once and logged. The tests pass locally and in CI |
| AC7 | Multi-sample: A4-07 → 400 `UNSUPPORTED_MULTISAMPLE`, under test |

## Zero-regression (measured after implementation, against B5 at f8fc84d)

- **S1–S6:**
  - labels identical;
  - every warning identical, except the build warning of S3 and S4, whose inputs
    carry contig lengths and no build declaration; that warning may disappear
    (lengths establish GRCh38) or change to the evidence wording;
  - no other warning added or removed.
- **Cohort (400 samples, 2,400 results):** 0 label changes, 0 rejected files.
- **74 PharmCAT test VCFs:** 0 call mismatches against B5, 0 newly rejected files.
- **A4:** every row PASS under `A4_PRECOMMIT.md`. The only label changes allowed:
  - A4-03 and A4-20 move from Unknown to Ineffective. That is the base file's
    label from the same genotypes and the same CPIC text: "Avoid clopidogrel if
    possible. Use prasugrel or ticagrelor at standard dose if no contraindication."
    (label rule `avoid_for_lack_of_efficacy`).
  - A4-09a, A4-09b, A4-22 and A4-23 become 400s.
- **Suites:** backend and Flutter pass.
- **External evaluation:** the re-bind shows no change in eligibility or
  discrepancies, or else every change is declared, row-counted and justified
  before it is accepted.

## Sabotage

Each must turn a test red, and the files are restored byte-identical afterwards.

| id | sabotage | expected red |
|---|---|---|
| SB6-a | the REF check reports no mismatches | A4-09a, A4-09b, A4-22 tests |
| SB6-b | GRCh37 lengths removed from `build_evidence.json` | A4-02 test |
| SB6-c | contig rewrite disabled | A4-03, A4-20 tests |
| SB6-d | gVCF block detection disabled | A4-08b test |
| SB6-e | one base in `reference_alleles.json` flipped | the derivation test |
| SB6-f | BCF magic check removed | A4-06 test |

## Out of scope

- RefSeq accessions as CHROM values (`NC_000010.11`).
- Lifting GRCh37 over.
- Expanding gVCF blocks into explicit rows.
- Choosing one sample from a multi-sample file.

Each stays a decline with a specific reason.
