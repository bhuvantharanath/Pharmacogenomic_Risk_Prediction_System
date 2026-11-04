# B3 — Cross-check the coverage gate with PharmCAT's own evidence: plan and pre-committed criteria

Written 2026-11-04 before any B3 code change. Facts below were checked by
reading the pinned jar and running it on adversarial inputs; no criterion below
has been measured yet.

## Facts that shape the design

1. PharmCAT 3.4.0's native minimum-data rule is `requiredPositions` in the jar's
   `definition/alleles/exemptions.json`. It is non-empty only for NAT2
   (18400194, 18400344, 18400593, 18400806, 18400860). It is empty for CYP2C19,
   CYP2C9, DPYD, NUDT15, TPMT, VKORC1 and CYP2D6; SLCO1B1 has no entry. PharmCAT's
   own rule therefore never fires for any PharmaGuard gene.
2. `amp1Positions` (AMP Tier 1) exist for several genes, but `missingAmp1Positions`
   stayed empty in every probe — including `_base_copy.vcf` with chr10:94761900
   (rs12248560, an AMP Tier-1 position) deleted: missingPositions [94761900],
   missingAmp1Positions []. The v3.4.0 source has code to fill it; observed output
   does not. Not relied upon.
3. PharmCAT's own per-position evidence is in report.json `genes.<G>.variants[]`:
   `call` is null when PharmCAT had no usable genotype, and per-variant `warnings`
   say why (e.g. "Discarded genotype at this position because REF in VCF (C) does
   not match expected reference (G)"). For the six called genes PharmCAT reports
   exactly our required position set (35/88/35/45/20/83).
4. On A4 probes the two views diverge: A4-09b PharmCAT discards rs4244285 and
   still calls *2/*2 (we show confident Ineffective); A4-09a discards 10 CYP2C19
   rows; A4-22 discards 444 rows (DPYD 81/83, TPMT 44/45 unused) while our gate
   counts 83/83 and 45/45 (confident "No PGx-guided adjustment identified", F-02);
   A4-03 (contig `10`) PharmCAT uses no position, our gate counts all (F-05).
5. The VCF preprocessor is not on the served path (Dockerfile sets the
   sha-verified PHARMCAT_JAR; resolve_invoker prefers the jar) nor used by tests
   or benchmarks; local bcftools is 1.24. Nothing to adopt; recorded.

## Design

`backend/app/evidence_crosscheck.py` (new, enrolled in the scientific core): the
same invariant evaluated on PharmCAT's evidence — the thresholds and
decision-critical sets from position_requirements.json applied to the positions
PharmCAT reports a non-null call for, plus PharmCAT's native requiredPositions
read from the pinned jar. It never reads the VCF and shares no code with
`coverage.assess`. A drug gets a confident label only if BOTH verdicts are
sufficient for every gene it depends on; otherwise Unknown, with a warning naming
the gene, up to 5 positions (rsid) and PharmCAT's own reason. Per-gene
`position_coverage` gains `pharmcat_positions_used` and `pharmcat_sufficient`.

## Acceptance criteria (pre-committed)

| id | criterion |
|---|---|
| AC1 | A test pins the jar's requiredPositions: NAT2's five, empty for every PharmaGuard gene; a positive control injects a required position for CYP2C19 and the cross-check then declines |
| AC2 | Independence: the module takes PharmCAT's evidence only from the parsed report and does not import coverage's evidence functions (test) |
| AC3 | Invariant: across S1–S6, the 2,400 cohort results and the A4 inputs, 0 confident labels where either verdict is insufficient for a required gene (harness check) |
| AC4 | Disagreement table (cohort, A4, S1–S6) per gene with (ours, PharmCAT) counts; every disagreement assigned a named position-level cause; unexplained = 0 |
| AC5 | A4-09a, A4-09b, A4-22, A4-23 decline every drug; A4-03 declines with a reason naming positions PharmCAT did not use; no A4 row moves Unknown→confident |
| AC6 | Preprocessor/bcftools finding recorded; a test asserts the Dockerfile sets PHARMCAT_JAR |

Zero-regression vs B2: S1–S6 6/6 labels; cohort 0 Unknown→confident (any
confident→Unknown listed and justified by a PharmCAT discard); 74 test VCFs 0
mismatches.

Sabotage: (a) cross-check always "sufficient" → A4-09b test red; (b) a null
PharmCAT call counted as used → red; (c) native requiredPositions ignored → AC1
positive control red.

If a criterion fails, stop and report rather than adjust it.
