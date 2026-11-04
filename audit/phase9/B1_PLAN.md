# B1 — Guideline refresh: plan and pre-committed acceptance criteria

Written 2026-11-04 before any B1 code change.

## What Part A found, and what B1 therefore does

The prompt anticipated stale TPMT/NUDT15 (2025 update) and SLCO1B1 (Oct 2025)
knowledge. Part A (A5) measured that it is **not** stale: PharmCAT 3.4.0's
embedded data (`2026-07-13-11-40`) already carries the 2025 thiopurine guideline
(PMID 41618934, including the compound-IM 20–50 % rows) and the Oct 2025 SLCO1B1
function table; every CPIC recommendation row for our five implemented drugs
matches CPIC's API text exactly. The project vendors no separate CPIC table —
the 105-row validation is extracted from the same jar.

So B1 does not change any clinical data. It makes the A5 result permanent and
closes the gaps around it:

1. **Vendor a pinned CPIC API snapshot** (allele functions for the six called
   genes; recommendations for our drugs) with fetch time, URL and SHA-256, plus
   the script that refreshes it, and a test that PharmCAT's embedded data agrees
   with it. B2's watcher will compare the live API against this snapshot.
2. **Re-derive, don't hand-edit**: regenerate the label-mapping expectation table,
   the decision-critical positions and the required positions from the jar, and
   confirm each equals what is committed. Add the missing generator for the
   required positions (Part A F-18).
3. **Compound IM, exactly as CPIC states it**: the label and text are already
   correct; the response names only one gene (Part A F-13). Add a code-composed
   warning naming both contributing genes whenever the selected CPIC row is a
   multi-gene row with two or more non-normal asserted phenotypes, and pin the
   compound rows with tests.
4. **Explanation store**: count stored entries whose CPIC source text no longer
   matches a current row; invalidate and regenerate only those.

## Acceptance criteria (pre-committed)

| id | criterion |
|---|---|
| AC1 | `test-data/reference/cpic_snapshot/` holds the API export with `fetched_utc`, endpoint URLs and per-file SHA-256; a test shows PharmCAT 3.4.0's embedded data agrees with it: 0 allele-function differences for CYP2C19, CYP2C9, SLCO1B1, TPMT, NUDT15, DPYD except the enumerated NUDT15 `*2`; 0 recommendation-text differences for clopidogrel, simvastatin, azathioprine, fluorouracil, capecitabine; PharmCAT-only rows exactly the enumerated set (codeine `xN combinations`, 12 warfarin algorithm pointers) |
| AC2 | Re-extracting the label-mapping expectation rows from the jar reproduces the committed 105 rows exactly (no growth) |
| AC3 | `scripts/validate_label_mapping.py` still reports 92/105 with exactly the 13 accepted divergences |
| AC4 | Every azathioprine CPIC row keyed TPMT ∈ {IM, PIM} and NUDT15 ∈ {IM, PIM} maps to `Adjust Dosage` with CPIC's 20%–50% text; the end-to-end compound-IM VCF returns `Adjust Dosage`, the 20%–50% text, and a warning naming both TPMT and NUDT15 with their phenotypes; single-IM cases get no such warning |
| AC5 | Decision-critical positions re-derived from the jar equal the committed ones for all 7 genes; a new `scripts/build_position_requirements.py` regenerates the required positions from `pharmcat_positions_3.4.0.vcf.bgz` and they equal the committed ones; the measured thresholds are carried over, never computed |
| AC6 | Stored explanation entries whose `cpic_recommendation_used` matches no current CPIC row for their drug: **0** expected; a test pins the count. If non-zero: list hashes, mark invalid, and stop for approval before any LLM regeneration |
| AC7 | An approved `(azathioprine, IM)` record is not servable for a compound-IM request (approval binds the exact CPIC row) |

Zero-regression condition: Part B harness vs `baseline` — S1–S6 6/6 labels;
cohort Unknown→confident = 0; 74 PharmCAT test VCFs 0 mismatches; no confident
label anywhere changes. The new warning may change warning lists only.

Sabotage: (a) mutate one vendored recommendation text → AC1 test red;
(b) delete the compound-warning code → AC4 warning test red; (c) change one
committed required position → AC5 test red.

If a criterion fails, stop and report rather than adjust it.
