# B10 — CYP2D6 from outside calls

Part B item 10 of the Phase 9 brief:

> - PharmCAT accepts "outside calls" for genes it can't call itself. Allow an
>   optional upload of a CYP2D6 diplotype produced by a dedicated caller from
>   BAM/CRAM (Cyrius, BCyrius, Aldy 4, StellarPGx). Keep VCF-only CYP2D6
>   declined exactly as now.
> - The UI must show provenance: "CYP2D6 supplied by <tool>, not called by
>   PharmaGuard."
> - Acceptance: codeine labels appear only when an outside call is supplied;
>   NA12273 negative control still declined without one.

The owner also decided, before this plan, to fix the codeine label mapping that
outside calls make reachable (answer: "Fix codeine mapping"). See "The label
mapping" below.

Written 2026-11-06 before any B10 code. Its sha256 goes into
`audit/phase9/B10.log` before the first edit. Nothing here is edited after
measurement.

## State at B9 (34f40db, live)

### CYP2D6 and codeine

- **CYP2D6 is never called.** PharmCAT reports CYP2D6 from a VCF with
  `callSource` `NONE`. The backend marks that not attempted and warns: "CYP2D6
  structural/copy-number variation cannot be resolved from unphased VCF;
  outside diplotype input planned".
- **Codeine is an explicit abstention.** It is in `capabilities.json` with
  `guidance_capable: false`, and `cpic_engine` returns Unknown for it before
  reading any guideline.
- **The way in was planned.** A TODO in `pharmcat_runner.py` names outside
  calls (`-po`) as the route, and warns against `-research cyp2d6`, which
  PharmCAT documents as unvalidated.

### What PharmCAT 3.4.0 does with an outside call

Measured 2026-11-06 with the pinned jar, `-po` and the NA12273 demo VCF. Every
call comes back `callSource` `OUTSIDE`, with a message that the outside source
supplies no position-level detail.

| Outside call | Phenotype (activity) | Codeine CPIC text |
|---|---|---|
| `*4/*4` | Poor Metabolizer (0.0) | "Avoid codeine use because of possibility of diminished analgesia. If opioid use is warranted, consider a non-tramadol opioid." |
| `*1x2/*1` | Ultrarapid Metabolizer (3.0) | "Avoid codeine use because of potential for serious toxicity. If opioid use is warranted, consider a non-tramadol opioid." |
| `*1/*2` | Normal Metabolizer (2.0) | "Use codeine label recommended age- or weight-specific dosing." |
| `*1xN/*4` | Indeterminate | "No recommendation" |
| `*999/*1` | Indeterminate | "No recommendation" |

PharmCAT accepts a non-existent allele without error. It reads the outside
file line by line, so a newline in a supplied diplotype would add a call for
another gene.

### The label mapping

`validate_label_mapping.py` checks all 105 CPIC rows for the six drugs.
Thirteen accepted divergences are listed in
`reports/label_mapping_accepted_divergences.json`; ten of them are codeine, and
codeine could not be reached until now:

- **IM** (activity 0.25–1.0), "Use codeine label recommended age- or
  weight-specific dosing. If no response and opioid use is warranted, consider
  a non-tramadol opioid." Mapped to Adjust Dosage; the independent expectation
  is No PGx-guided adjustment identified. Four rows.
- **NM** (activity 1.25–2.25), "Use codeine label recommended age- or
  weight-specific dosing." Mapped to Unknown (no rule matches); the expectation
  is No PGx-guided adjustment identified. Five rows.
- **The `xN` row** (not a valid input, per CPIC): Unknown. One row.

`standard_dosing` already lists "label recommended dosage". CPIC's codeine text
says "label recommended age- or weight-specific dosing", which no listed phrase
covers.

## Design

### 1. The input

`POST /analyze` takes two optional form fields:

- `cyp2d6_diplotype`;
- `cyp2d6_caller`, one of `Cyrius`, `BCyrius`, `Aldy`, `StellarPGx`.

The user enters the caller's diplotype and names the caller. Parsing each
tool's native output files is out of scope.

**Validation, before anything runs:**

- **Both or neither.** One field without the other is a 400
  `OUTSIDE_CALL_INCOMPLETE`.
- **The caller must be on the list.** Anything else is a 400
  `OUTSIDE_CALL_INVALID`.
- **The diplotype must fit a strict grammar.** Two haplotypes joined by `/`.
  Each haplotype is a star allele, `*N` or `*N.NNN`. It may carry a copy
  number (`x2` and up, or `xN`) or the binned `≥3`. It may be joined to other
  alleles by `+` (tandem), or be a bracketed combination `[*a + *b]`. At most
  80 characters, with no tab, newline or other characters. Anything else is a
  400 `OUTSIDE_CALL_INVALID`.
- **The call stays CYP2D6.** It names no gene, the server writes the gene
  itself, and no other gene can be supplied.

### 2. The run

- **The outside file.** The server writes `CYP2D6<TAB><diplotype>` into a file
  in the owned temp tree, which is removed on every path as in B8.
- **The flag.** PharmCAT gets it with `-po`, on both the jar and the wrapper
  invocation.
- **No research mode.** `-research` is never passed.

### 3. Codeine

- **The gate opens only for an accepted call.** Codeine stays an abstention
  unless CYP2D6 came from an accepted outside call: PharmCAT's `callSource` is
  `OUTSIDE` for this request. Then the matched CPIC text is mapped like any
  other drug's.
- **An Indeterminate call gives no label.** An `xN` copy number or an unknown
  allele makes PharmCAT return Indeterminate and "No recommendation", so
  codeine stays Unknown.
- **The capability text says this.** The capability table's codeine
  limitation and the client's scope text change to "Unknown unless a CYP2D6
  diplotype from a dedicated caller is supplied".

### 4. The label mapping (the owner's decision)

- **One phrase.** `standard_dosing` gains "label recommended age- or
  weight-specific dosing". That is CPIC's own directive to prescribe at the
  label dose.
- **No reordering.** The rule already runs before `dose_change_or_monitoring`,
  and after every avoid, toxicity and alternative rule. Nothing else changes.
- **The baseline shrinks.** The accepted-divergence baseline loses the nine
  codeine IM and NM rows.

### 5. Provenance

- **The API.** `pharmacogenomic_profile.supplied_by` (null otherwise) names the
  caller when the diplotype came from an outside call.
- **The warnings.** `quality_metrics.warnings` gains "CYP2D6 <diplotype>
  supplied by <caller>, not called by PharmaGuard." The not-attempted warning
  keeps its "structural/copy-number" wording, which the client matches, and
  ends "a CYP2D6 diplotype from a dedicated caller can be supplied" instead of
  "outside diplotype input planned".
- **The explanation.** The deterministic template for a supplied diplotype
  says it was supplied by the named caller, not called. It never says
  "PharmCAT called" or "PharmaGuard called" for it. The stored explanation
  file is not touched.
- **The client.** The results card, the printable summary, the PDF and the
  FHIR export carry "CYP2D6 supplied by <caller>, not called by PharmaGuard."
  for every result whose `supplied_by` is set. The summary adds that one line
  only for such results. The FHIR Genotype gets it as a note.
- **The home screen.** An optional "CYP2D6 from a dedicated caller" section:
  the diplotype field, a caller list, the same grammar as the server, and text
  saying the call is used as given and labelled as supplied.

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | Negative control: NA12273 (S3) and every S1–S6 file without an outside call give codeine Unknown, with labels and statuses as at B9 |
| AC2 | Codeine labels only with an outside call, by test through the real PharmCAT on the NA12273 VCF: `*4/*4` Ineffective; `*4/*10` (IM) No PGx-guided adjustment identified; `*1/*2` (NM) No PGx-guided adjustment identified; `*1/*1x2` (UM) Toxic; `*1xN/*4` and `*999/*1` Unknown. Each label's CPIC text is the one PharmCAT returned for that phenotype |
| AC3 | Provenance, by test: every result from an outside call has `supplied_by` equal to the caller. The API warning, the results card, the printable summary, the PDF and the FHIR Genotype note carry "CYP2D6 supplied by <caller>, not called by PharmaGuard." The explanation never says the call was PharmCAT's or PharmaGuard's |
| AC4 | Input safety, by test: a tab, a newline, a second gene, a lowercase or bare allele, more than 80 characters, a caller off the list, or one field without the other is refused with 400 before PharmCAT runs (a stand-in PharmCAT that records its calls is never called). `-research` never appears in a PharmCAT command |
| AC5 | Isolation, by test: for the S1 and S6 files, adding an outside call changes nothing in any analysis except those whose gene is CYP2D6 |
| AC6 | Label mapping: in `validate_label_mapping.py`, the nine codeine IM and NM rows now agree. No other row's actual label changes. The accepted-divergence baseline goes from 13 to 4 entries. The mapping diff is one phrase |
| AC7 | Suites and gate: full backend and Flutter suites pass; the FHIR validation (now including an outside-call fixture) has 0 errors; the release gate is ready |

## Zero-regression

- **Cohort, 74 PharmCAT VCFs, A4:** identical to B9 in labels and statuses. No
  outside calls are involved.
- **S1–S6:** labels identical to B9. Bodies are identical apart from three
  declared changes:
  - `pharmacogenomic_profile.supplied_by: null` in every analysis;
  - the reworded not-attempted CYP2D6 warning;
  - the codeine capability limitation text, where it appears.
- **Printable HTML summary:** byte-identical for B9's seven fixtures, which
  have no outside call.
- **External evaluation:** the re-bind shows no eligibility or discrepancy
  change against B9's package.

## Sabotage

Each must turn a test red, and the files are restored byte-identical
afterwards.

| id | sabotage |
|---|---|
| SB10-a | the diplotype grammar lets a newline through (a second gene could be injected) |
| SB10-b | codeine's gate opens without an outside call |
| SB10-c | `supplied_by` is not set for an outside call |
| SB10-d | the explanation template says "PharmCAT called CYP2D6" for a supplied diplotype |
| SB10-e | the new phrase is removed from `standard_dosing` (NM codeine back to Unknown) |
| SB10-f | the caller list accepts any name |
| SB10-g | `-research cyp2d6` is added to the PharmCAT command |
| SB10-h | the results card drops the provenance line |
| SB10-i | the printable summary drops the provenance line |

## After deploy (only if the owner approves a deploy)

Live criteria, to be logged before measuring:

- **Commit.** The Deploy run succeeds and `/ready` reports the commit.
- **S1–S6.** As at B9.
- **NA12273 demo VCF with codeine:** Unknown without an outside call; with
  `*4/*4` from Cyrius, Ineffective, `supplied_by` Cyrius, and the provenance
  warning.
- **Browser.** The home screen shows the new section, and the result for a
  supplied call shows the provenance line.

## Out of scope

- **Parsing callers' native output files.** Cyrius TSV, Aldy, StellarPGx
  `summary.txt`.
- **Outside calls for any gene but CYP2D6.**
- **The `/coverage` preview.** It does not take outside calls. The client
  states, beside the preview, that codeine will be answered from the supplied
  call.
- **PharmCAT research mode.**
