# B6 — A4 zero-regression amendment, by owner decision

Recorded 2026-11-05, after measurement, at the owner's explicit instruction. The plan
(`audit/phase9/B6_PLAN.md`, sha256 8150d8ef…) is left unedited, so its hash still
proves what was pre-committed.

## Why

The plan's A4 zero-regression clause listed the only label changes allowed. The list
was written around A4's own question, which is clopidogrel. Measured with all six drugs
(`audit/phase9/partb/a4_labels.py`, B5-after against B6-after), the contig rename also
moves three other drugs on A4-03 and A4-20 from Unknown to the base file's labels.

Each A4-03 and A4-20 response equals the base file's for all four drugs: label, gene,
diplotype, phenotype, CPIC text and source. That is expected, because after the rename
these are the base file's genotypes.

The two options were put to the owner: accept and amend the clause, or decline
unprefixed contig names instead of renaming them. The owner's answer, verbatim:

> Accept, amend clause

## Original clause

> A4: every row PASS under `A4_PRECOMMIT.md`. The only label changes allowed:
> A4-03 and A4-20 move from Unknown to Ineffective. That is the base file's label from
> the same genotypes and the same CPIC text: "Avoid clopidogrel if possible. Use
> prasugrel or ticagrelor at standard dose if no contraindication." (label rule
> `avoid_for_lack_of_efficacy`). A4-09a, A4-09b, A4-22 and A4-23 become 400s.

## Amended clause

A4: every row PASS under `A4_PRECOMMIT.md`. These are the only label changes allowed.

**A4-03 and A4-20 take the base file's label for every drug.** Each change is
justified by the CPIC text that the base file's own result quotes (via PharmCAT):

| Drug | Label | Genotype | CPIC text | Label rule |
|---|---|---|---|---|
| clopidogrel | Ineffective | CYP2C19 \*2/\*2, PM | "Avoid clopidogrel if possible. Use prasugrel or ticagrelor at standard dose if no contraindication." | `avoid_for_lack_of_efficacy` |
| azathioprine | No PGx-guided adjustment identified | TPMT \*1/\*1, NM | "Initiate therapy with standard starting dose (e.g., 2 mg/kg/day for autoimmune diseases). During therapy, adjust doses of azathioprine based on disease-specific guidelines. It usually takes at least 2 weeks to reach steady state after each dose adjustment." | `standard_dosing` |
| fluorouracil | No PGx-guided adjustment identified | DPYD Reference/Reference, NM | "Based on genotype, there is no indication to change dose or therapy. Use label-recommended dosage and administration." | `standard_dosing` |
| simvastatin | No PGx-guided adjustment identified | SLCO1B1 \*1/\*1, NM | "Prescribe desired starting dose and adjust doses based on disease-specific guidelines." | `standard_dosing` |

Warfarin and codeine stay Unknown, as for the base file.

**A4-02, A4-09a, A4-09b, A4-22 and A4-23 become 400s.** A4-02 is named here
because AC2 already requires its 400, which the original list omitted.

Every other A4 status, error code and label is unchanged from B5. The label rules, the
mapping and the expectation table are not changed.
