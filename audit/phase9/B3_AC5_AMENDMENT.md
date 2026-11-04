# B3 — AC5 amendment, by owner decision

Recorded 2026-11-04, AFTER measurement, at the owner's explicit instruction. The
original plan (`audit/phase9/B3_PLAN.md`, sha256 14ad1b5e…) is left unedited so its
hash still proves what was pre-committed.

## Why

AC5 as pre-committed failed (audit/phase9/B3.log): A4-09a and A4-09b alter
CYP2C19 rows only. The cross-check declines clopidogrel on both, but azathioprine,
fluorouracil and simvastatin keep their labels, because PharmCAT verified the REF
base at every TPMT, NUDT15, DPYD and SLCO1B1 position it used. Declining them would
need a whole-file rule. The two options were put to the owner, whose answer was,
verbatim:

> Per-gene, amend AC5

## Original AC5

A4-09a, A4-09b, A4-22, A4-23 decline every drug; A4-03 declines with a reason
naming positions PharmCAT did not use; no A4 row moves Unknown→confident.

## Amended AC5

A4-22 and A4-23 decline every drug. A4-09a and A4-09b decline every drug that
depends on a gene whose genotypes PharmCAT discarded (CYP2C19: clopidogrel); a
drug whose genes PharmCAT used in full keeps its label. A4-03 declines with a
reason naming positions PharmCAT did not use. No A4 row moves Unknown→confident.

A file-level REF/build check is not dropped. It remains in scope for B6, which
detects the genome build and checks REF at known positions.
