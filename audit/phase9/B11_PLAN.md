# B11 — South Asian population context (display only)

Part B item 11 of the Phase 9 brief:

> Show per-gene reduced-function frequency context for South Asians from our
> own measured 1000G SAS results (with the documented caveats and CI),
> optionally IndiGen published figures with citation. **Context only — never a
> prior that changes a call or label.** GenomeIndia raw data requires an access
> application; don't build on it without approval.

Written 2026-11-06 before any B11 code. Its sha256 goes into
`audit/phase9/B11.log` before the first edit. Nothing here is edited after
measurement.

## State at B10 (b036f36, live)

### What was measured (2026-08-14)

The sources are `reports/sas_frequencies.json`, `reports/sas_cohort_expansion.md`
and `reports/sas_deviation_filtered.json`/`.md`.

- **The sample.** 601 samples from the five 1000 Genomes SAS cohorts: PJL 146,
  BEB 131, STU 114, ITU 107, GIH 103. Four were collected outside India (Lahore,
  Bangladesh, the UK twice, Houston); GIH and ITU are Indian-origin diaspora.
- **The calls.** PharmCAT's calls on research-format, polymorphic-filtered
  input. The app's own coverage gate declines every one of these samples.
- **Pooled phenotype counts.** All six reported genes have counts. CYP2D6 has
  none: every sample is "No Result".
- **The figure the report quotes.** CYP2C19 reduced function (PM + IM), with
  95% Wilson intervals: pooled 57.1% [53.1, 61.0]; STU 64.0% [54.9, 72.3];
  ITU 60.7% [51.3, 69.5]; BEB 57.3% [48.7, 65.4]; PJL 54.1% [46.0, 62.0];
  GIH 49.5% [40.1, 59.0].
- **Positions present in the source data** (`sas_deviation_filtered.json`,
  `input_artifacts`): CYP2C19 16/35, CYP2C9 17/88, SLCO1B1 20/35, TPMT 9/45,
  NUDT15 5/20. DPYD was not measured.
- **Why the figures are lower bounds.** An absent position reads as reference,
  so a variant at a missing position is invisible. It turns a reduced-function
  call into a normal one, never the reverse.
- **Population definition.** CPIC's comparison group, Central/South Asian, is
  a different population definition (the report's own caveat).

The app shows none of this today.

## Design

### 1. The table is generated

`scripts/generate_population_context.py` reads
`reports/sas_frequencies.json` (phenotype counts per cohort and pooled) and
`reports/sas_deviation_filtered.json` (positions present). It writes
`app/lib/generated/population_context.g.dart`. For each of CYP2C19, CYP2C9,
SLCO1B1, TPMT, NUDT15 and DPYD it records:

- **The rate.** The reduced-function count and n, pooled and per cohort.
  Reduced function means Poor plus Intermediate Metabolizer; for SLCO1B1, Poor
  plus Decreased Function.
- **The interval.** The 95% Wilson interval.
- **Coverage.** The positions present and required, or "not measured".
- **What else is in the denominator.** The Indeterminate and no-result counts,
  which are counted in the denominator and never as reduced.

No figure is typed by hand. A test re-runs the generator and compares its
output with the committed file.

### 2. The display

When a result card is open, it shows a "South Asian context — not used for this
result" row for its gene. The row gives:

- the pooled rate and its interval, as "at least";
- n = 601 and the five cohorts;
- the per-cohort rates.

**The caveats it shows:**

- **What the calls are.** PharmCAT's calls on research-format data, which this
  application would itself decline.
- **Why the rate is a lower bound.** The positions present out of required,
  with the reason (or "not measured" for DPYD).
- **Who was sampled.** Four of the five cohorts were collected outside India,
  so the figure is not representative of India.
- **What the figure is not.** It is not an outcome rate.
- **The context-only promise.** "Context only: this does not change this
  result."
- **DPYD's Indeterminate share.**

A gene with no measured context, such as CYP2D6, gets no figure. The row says
none was measured.

### 3. What it never touches

- **No influence on any result.** No label, call, phenotype, warning or server
  response. The backend is not changed.
- **No export.** It is not in the printable summary, the PDF or the FHIR export,
  which carry what the analysis found, not context about other people.
- **No outside figures.** IndiGen published figures are not added: each number
  would need to be read from a cited source, and the item is optional.
  GenomeIndia is not used.

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | Figures from the artifacts, by test: the committed `population_context.g.dart` equals the generator's output from the two report JSONs, byte for byte. The generator's CYP2C19 figures reproduce the report's documented ones to one decimal: pooled 57.1 [53.1, 61.0]; STU 64.0 [54.9, 72.3]; ITU 60.7 [51.3, 69.5]; BEB 57.3 [48.7, 65.4]; PJL 54.1 [46.0, 62.0]; GIH 49.5 [40.1, 59.0] |
| AC2 | Context only, by test: the printable HTML summary and the FHIR bundle for every fixture are byte-identical to B10's. No backend file changes |
| AC3 | Caveats, by widget test, for every gene with a figure: the open card shows the "not used for this result" label, n = 601 and the five cohorts, the lower-bound wording with positions present out of required (or "not measured"), the research-format and outside-India caveats, and that a frequency is not an outcome |
| AC4 | The right gene, by widget test: each fixture's open card shows the context for its own primary gene's figure and no other. A gene without one (CYP2D6, an unsupported drug) shows the no-context sentence and no number |
| AC5 | Suites and gate: full backend and Flutter suites pass, and the release gate is ready |

## Zero-regression

- **S1–S6, cohort, 74 PharmCAT VCFs, A4:** identical to B10 in labels and
  statuses, and S1–S6 bodies identical. The backend is not changed.
- **Exports:** the printable HTML summaries and FHIR bundles for all nine
  fixtures are byte-identical to B10's.
- **External evaluation:** the re-bind (the app files are in the core) shows no
  eligibility or discrepancy change against B10's package.

## Sabotage

Each must turn a test red, and the files are restored byte-identical
afterwards.

| id | sabotage |
|---|---|
| SB11-a | one figure in the generated table is changed by hand |
| SB11-b | the interval uses z = 1.645 instead of 1.96 |
| SB11-c | the "not used for this result" label is dropped |
| SB11-d | the lower-bound caveat is dropped |
| SB11-e | the context is looked up for the wrong gene |
| SB11-f | the context leaks into the printable summary |

## After deploy (only if the owner approves a deploy)

Live criteria, to be logged before measuring:

- **Commit.** The Deploy run succeeds and `/ready` reports the commit.
- **S1–S6.** As at B10.
- **Bundle.** The production web bundle carries the context strings.
- **Browser.** In the built-in browser, an opened result card shows the context
  row with its caveats.

## Out of scope

- **IndiGen figures.** See above.
- **GenomeIndia.** It needs an access application.
- **Using any frequency as a prior.**
- **New measurement.** The figures are the 2026-08-14 measurement, shown with
  its date.
