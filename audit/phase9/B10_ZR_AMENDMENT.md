# B10 — external-evaluation zero-regression amendment, by owner decision

Recorded 2026-11-06, after measurement, at the owner's explicit instruction. The plan
(`audit/phase9/B10_PLAN.md`, sha256 1f557a8a…) is left unedited, so its hash still
proves what was pre-committed.

## What happened

The first re-bind attempt (tag `2026-11-06-b10`) stopped on its own check. Against
B9's package, `input_eligibility.tsv` differed in 208 CYP2D6 rows of
`eligibility_reason`, beyond the per-file VCF hashes. The scored results had
already been checked and were unchanged.

The cause is that the evaluation records codeine's capability limitation as
CYP2D6's eligibility reason, and B10 rewords that limitation. The plan declared
the rewording for the S1–S6 responses, but not for the evaluation.

While the declaration was being prepared, the same text was found again. It
repeats in the free-text `detail` column of 117 CYP2D6 rows of
`discrepancies.tsv`, a file the first attempt had stopped before comparing. Rows,
keys and scored columns are unchanged.

Two options were put to the owner:

- declare the text change;
- keep the old wording, which would then be false for anyone who supplies a call.

The owner's answer, verbatim:

> Accept, declare it

## Original clause

> **External evaluation:** the re-bind shows no eligibility or discrepancy change
> against B9's package.

## Amended clause

**External evaluation.** Against B9's package, the re-bind shows exactly two
changes besides the per-file VCF hashes. Both are the same rewording of codeine's
capability limitation:

- **`input_eligibility.tsv`**: CYP2D6 `eligibility_reason`, 208 rows.
- **`discrepancies.tsv`**: CYP2D6 `detail`, 117 rows.

The old text in both:

> CYP2D6 copy-number and structural variation is not called from the uploaded VCF
> in this application, so codeine guidance is not produced.

The new text in both:

> CYP2D6 copy-number and structural variation is not called from the uploaded VCF
> in this application, so codeine guidance is produced only from a CYP2D6 diplotype
> supplied by a dedicated caller (Cyrius, BCyrius, Aldy or StellarPGx).

Nothing else may change: no eligibility status, no scored metric, no exclusion and
no discrepancy classification. Both changes are declared with their exact values
and row counts in
`audit/phase9/partb/rebind/declared-changes-2026-11-06-b10.json`. The re-bind
checks that every observed change is declared and that every declared change is
observed, so anything else still stops it.

## Scope of the decision

The owner's decision was given on the 208 eligibility rows. The 117
discrepancy-detail rows carry the identical text, in the second file the
evaluation writes, and were found while the declaration was being prepared. They
are declared on the same basis, and this is reported to the owner rather than
folded in silently.
