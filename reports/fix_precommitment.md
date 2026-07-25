# Pre-commitment: what "fixed" means for the substring collision

**Recorded 2026-07-24, BEFORE any edit to `label_mapping.yaml`.**

This file exists because this project has twice watched a check get adjusted
until it agreed with whatever it was measuring — a detector tuned 12 → 4 → 0 and
blunted in the process, and a vocabulary check that needed a threshold fixed in
advance to stop the same thing. Writing the success condition down first is what
makes "we stopped here" auditable rather than convenient.

---

## Baseline, measured before the fix

| | |
| --- | ---: |
| Combinations | 105 |
| Agreements | 60 |
| Disagreements | 45 |
| — of which the `standard_dosing` collision | **16** |

## The 16 rows that must change

All 16 are azathioprine. Every one must move from **Safe** to **Adjust Dosage**,
because CPIC's text for each says to initiate therapy at a *reduced* starting
dose (30–80%, or 20–50%, of standard).

| # | TPMT | NUDT15 | now | required |
| ---: | --- | --- | --- | --- |
| 1 | Possible Intermediate Metabolizer | Normal Metabolizer | Safe | **Adjust Dosage** |
| 2 | Possible Intermediate Metabolizer | Intermediate Metabolizer | Safe | **Adjust Dosage** |
| 3 | Possible Intermediate Metabolizer | Possible Intermediate Metabolizer | Safe | **Adjust Dosage** |
| 4 | Intermediate Metabolizer | Normal Metabolizer | Safe | **Adjust Dosage** |
| 5 | Normal Metabolizer | Intermediate Metabolizer | Safe | **Adjust Dosage** |
| 6 | Normal Metabolizer | Possible Intermediate Metabolizer | Safe | **Adjust Dosage** |
| 7 | Intermediate Metabolizer | Intermediate Metabolizer | Safe | **Adjust Dosage** |
| 8 | Intermediate Metabolizer | Possible Intermediate Metabolizer | Safe | **Adjust Dosage** |
| 9 | No Result | Intermediate Metabolizer | Safe | **Adjust Dosage** |
| 10 | Possible Intermediate Metabolizer | No Result | Safe | **Adjust Dosage** |
| 11 | No Result | Possible Intermediate Metabolizer | Safe | **Adjust Dosage** |
| 12 | Intermediate Metabolizer | Indeterminate | Safe | **Adjust Dosage** |
| 13 | Intermediate Metabolizer | No Result | Safe | **Adjust Dosage** |
| 14 | Possible Intermediate Metabolizer | Indeterminate | Safe | **Adjust Dosage** |
| 15 | Indeterminate | Possible Intermediate Metabolizer | Safe | **Adjust Dosage** |
| 16 | Indeterminate | Intermediate Metabolizer | Safe | **Adjust Dosage** |

## Conditions the fix must satisfy

1. **All 16 become `Adjust Dosage`.** Nothing less counts.

2. **Zero regressions.** None of the 60 currently-agreeing rows may change. A fix
   that trades 16 wins for even one new loss is not a fix.

3. **It must be a precedence/specificity correction, not a special case.**
   Explicitly forbidden: any rule keyed on azathioprine, TPMT, NUDT15, or the
   literal percentages `30-80%` / `20%-50%`. The collision is general — a
   modifier-governed phrase matching an unmodified-phrase rule — and a targeted
   patch would leave the same class of bug live for every other drug whose CPIC
   text happens to say "…% of standard dose".

4. **The other five drugs must be checked** for the same collision shape, and the
   result reported whether or not any were affected.

5. **The mapping's input stays recommendation TEXT.** It must not start consuming
   CPIC's structured booleans, because the expectation table in the Section 1
   validation reads exactly those — consuming them would make the validation
   tautological and it would stop catching anything. Structured fields may be
   used only as an independent *cross-check* that fails loudly on contradiction.

6. **Expected outcome, stated in advance:** 60 → **76** agreements, 45 → **29**
   disagreements. If the post-fix number differs from 76, something other than
   the intended change happened and it must be explained, not accepted.

## What this pre-commitment does NOT license

Tuning any of the other 29 disagreements to raise the count. Those are triaged
separately and on their merits: two are provenance violations, three lose a
toxicity warning, ten need one uniform policy, and fourteen are accepted
divergences. None of them is an excuse to move a threshold.
