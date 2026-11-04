# B5 — label amendment, by owner decision

Recorded 2026-11-04, before any B5 code. `audit/phase9/B5_PLAN.md` (sha256 b5b1543a…)
is left unedited.

## Why

AC2 followed the Phase 9 brief ("Adjust Dosage" with the algorithm text once CYP2C9
and VKORC1 are called). After the plan was hashed, the existing independent
expectation table (`test-data/reference/cpic_expectations.json`, behind the 105-row
mapping validation) was found to read CPIC's warfarin text — an algorithm pointer —
as **Unknown**, derived from CPIC's structured fields; the engine agrees today. The
two options were put to the owner, whose answer was, verbatim:

> Keep Unknown, show genes

## Amended criteria (replace AC2 and AC5; AC1, AC3, AC4 unchanged)

AC2′ — Warfarin is Unknown in every case. When CYP2C9 and VKORC1 are both sufficient
(both evidence views) and called, the result carries per-gene findings for CYP2C9,
VKORC1 and CYP4F2 with their calls; its action quotes the pinned CPIC text verbatim
(a test asserts all 12 jar rows carry it); the serialized warfarin result contains no
dose (no number followed by mg or %); it states that ancestry is not collected and
that rs12777823 is not assessed; the label is identical with CYP4F2 absent, *1/*1 or a
*3 carrier.

AC5′ — Through the real PharmCAT, synthetic VCFs: (i) CYP2C9 *1/*1 + VKORC1 C/C →
Unknown with CYP2C9 and VKORC1 assessed; (ii) *3/*3 + T/T + CYP4F2 *1/*3 → Unknown with
all three reported, CYP4F2 *1/*3; (iii) VKORC1 row removed → Unknown naming VKORC1,
VKORC1 not assessed; (iv) CYP2C9 rows removed → Unknown naming CYP2C9.

Zero-regression tightens accordingly: no Unknown→confident change anywhere, warfarin
included. The expectation table and the label rules are not changed.
