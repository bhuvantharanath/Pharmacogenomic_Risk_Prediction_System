# F-20 — no borrowed CPIC row when none matches the called phenotype

Owner instruction: "Plan the engine fix" (2026-11-07), after F-19 (12dc819). The
earlier finding is in `audit/phase9/F19_F20.log`.

Written 2026-11-07 before any code. Its sha256 goes into `audit/phase9/F20.log`
before the first edit. Nothing here is edited after measurement.

## State at 12dc819 (measured today, read-only)

### The fallback

`cpic_engine.select_annotation` keeps the CPIC rows whose lookup key matches the
called phenotypes:

```python
matched = [a for a in usable if _annotation_matches_calls(a, report)]
candidates = matched or usable
```

When nothing matches, `candidates` becomes **every** usable row, and the one with
the strongest CPIC classification is returned with a warning ("showing the
strongest available row. Treat with extra caution."). `evaluate` then derives the
label from that row against the patient's own phenotype. The request-time
contradiction check does not catch it.

"Strongest" ranks CPIC's strength of recommendation, which every clopidogrel row
shares ("Strong"), so in practice the choice is the first row in the list. It is
not related to the patient.

### What it does when reached

- **The exemplar.** The real CYP2C19 Poor Metabolizer fixture, with clopidogrel's
  guideline holding only CPIC's real Normal Metabolizer row (wording from
  `test-data/reference/cpic_expectations.json`). The untouched report gives
  Ineffective, "Avoid clopidogrel if possible…". The probe gives **"No PGx-guided
  adjustment identified"**, action **"If considering clopidogrel, use at standard
  dose (75 mg/day)"**, label rule `standard_dosing`.
- **Generalised.** All 16 fixtures, each drug's guideline given every real CPIC
  row for that drug *except* those matching the called phenotypes: **63 cases
  reach the fallback, and 63 of 63 return a confident label borrowed from another
  phenotype's row**. It is "No PGx-guided adjustment identified" or "Adjust Dosage"
  depending on row order. That covers both directions: a Poor Metabolizer told
  standard dose, a normal DPYD patient told to adjust.

### Whether it is reached

- **Runtime: never, on anything measured.** `evaluate()` reaches the fallback on
  none of the 16 fixtures and none of the 400 cohort reports × 6 drugs (2,400
  evaluations). None of S1–S6 (local and live), A4, the demo outputs or the client
  fixtures carry its warning. Calling `select_annotation` directly fires it 309
  times on the cohort, all on phenotypes that are not asserted, which
  `evaluate()`'s earlier gate turns into Unknown before selection.
- **Build time: yes, twice.** `scripts/enumerate_cases.py` (`cpic_text_for`) and
  `scripts/pregenerate_explanations.py` (`find_annotation`) call the selector
  without the runtime's asserted-phenotype gate. For `dpyd_compound_het` (DPYD
  "Indeterminate", mapped to Unknown), both take CPIC's **DPYD activity score 2.0
  row**, "Based on genotype, there is no indication to change dose or therapy. Use
  label-recommended dosage…", for fluorouracil and capecitabine. The runtime never
  selects that row for that call.
  This is the shape of the historical defect the comment in
  `_annotation_matches_calls` describes (an Indeterminate DPYD call selecting the
  normal row). The runtime half of that was fixed; the selector's fallback kept
  the other half alive.
- **Not realised in the frozen explanation store.** The store was generated
  2026-07-24; the `dpyd_compound_het` fixture was added 2026-08-11 (e1ed0b8). The
  stored fluorouracil · DPYD · Unknown entry carries none of that row's wording.
  The next regeneration would ground it on the normal-dose row.
- **The committed case matrix** (`backend/app/data/case_matrix.json`) stores
  reachability, not CPIC text. It is not affected.

## Design

1. **`select_annotation`.** When no usable row matches the called phenotypes,
   return no row, with a warning that says so and why. `evaluate()`'s existing
   `annotation is None` branch then returns Unknown with its existing reason
   ("PharmCAT returned no CPIC recommendation matching the called phenotype…").
   That branch is not new: warfarin, whose CPIC row has no per-phenotype text,
   already takes it.
2. **Unchanged:** the population choice among rows that *do* match, the matching
   rule itself, `evaluate`, `derive_label`, the label mapping, the explanation
   store, the case matrix and the client.

The build-time scripts need no change of their own: they call the same selector,
so they stop grounding on a borrowed row as soon as it stops returning one.

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | The exemplar, by test: CYP2C19 Poor Metabolizer with clopidogrel's guideline holding only CPIC's Normal Metabolizer row gives Unknown; the recommendation's action is the existing no-match reason and does not contain "use at standard dose"; a warning says no CPIC row matches |
| AC2 | Generalised, by test: the same construction over all 16 fixtures and every real CPIC row yields Unknown in every case that reaches the no-match branch, and its action contains none of the non-matching rows' recommendation text. The positive control: the no-match warning is present in each counted case and at least 63 cases are counted, so the test cannot pass by never reaching the branch |
| AC3 | Build time agrees with runtime, by test: for `dpyd_compound_het`, `find_annotation` and `cpic_text_for` no longer return the DPYD activity score 2.0 row for fluorouracil or capecitabine with phenotype Unknown |
| AC4 | Everything that matches is unchanged: every existing backend and Flutter test passes unmodified, including the compound-row, population and label-path-parity tests; the label-mapping validator still reports 101/105 with the 4 accepted divergences |
| AC5 | Suites and gate: full backend and Flutter suites pass, and the release gate is ready |

## Zero-regression

- **S1–S6, cohort, 74 PharmCAT VCFs, A4:** identical to B12 in labels and
  statuses, and S1–S6 bodies identical. Predicted by the measurement above: the
  runtime never reaches the fallback on any of these.
- **Exports:** the nine fixtures' printable summaries and FHIR bundles
  byte-identical to the baseline taken before the first edit.
- **Explanation store and case matrix:** untouched; 0 entries invalidated.
- **External evaluation:** the re-bind (`cpic_engine.py` is in the core) shows
  no eligibility or discrepancy change against B12's package, with nothing
  declared.

Against the standing rules:

- **Rule 5.** This moves confident to Unknown only on a path no measured input
  reaches.
- **Rule 6.** It enforces that only CPIC text for the called phenotype drives a
  label.
- **Rule 7.** The store is not touched.

## Sabotage

Each must turn a test red, and the file is restored byte-identical afterwards.

| id | sabotage |
|---|---|
| SBF20-a | the fallback is restored: `candidates = matched or usable` |
| SBF20-b | a different borrowing: the first usable row is returned when none matches |
| SBF20-c | no row is returned, but the warning is dropped, so the Unknown is silent |

## After deploy (only if the owner approves a deploy)

Live criteria are written into `F20.log` and hashed before measuring:

- the Deploy run succeeds and `/ready` reports the commit;
- live S1–S6 match the local run, and their bodies equal B12's live bodies.

## Out of scope

- **F-20's path 2: an Unknown label still carrying CPIC directive text.** It is
  not measured. Reading the code, two sub-paths label Unknown while building the
  recommendation from the matched row: the `fallback_unmatched` rule, and the
  request-time contradiction downgrade. Neither is changed here.
- **The four other stale F-19 items.**
- **Regenerating the explanation store or the case matrix.**
