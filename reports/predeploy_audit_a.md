# Pre-deployment audit A — correctness

Read-mostly audit. Nothing found here was repaired; the record of what was wrong
is the deliverable. Every claim below is backed by a command that was run, and
where a mutation was applied to source it was reverted with `git checkout --`
before the next one (the harness refuses to start on a dirty tree).

Date of audit: 2026-08-11.

> **Resolution note, 2026-08-12.** Findings below have since been repaired; the
> text is left exactly as written because the record of what was wrong is the
> deliverable. Two things it says are no longer true of the system:
>
> * **"DPYD alone passes"** — every gene now additionally requires each
>   decision-critical position, derived from PharmCAT's `functionValue`. DPYD
>   carries 8 of 28 and is gated. See `reports/decision_critical_positions.md`.
> * **The §4 finding recorded "output does not change"** for the compound-DPYD
>   revert. That was measured as the risk *label* alone and is **wrong** —
>   confidence moved 0.1 → 0.95 and the action text became a real CPIC
>   recommendation. The correction is in `tests/test_diplotype_source.py`.
>
> **Method hazard, recorded here because this audit recommends the technique.**
> Reverting a planted mutation with `git checkout -- <file>` discards *all*
> uncommitted work in that file, not just the plant. Doing this to `README.md`
> during a later session destroyed a turn's worth of edits. Snapshot the file
> and write the snapshot back instead; `git checkout` is only safe when the
> file is otherwise clean, which the harness's dirty-tree check does not
> guarantee per-file.
Baseline: 630 backend tests passing, 144 Flutter tests passing, `flutter analyze`
clean, on `feat/client-features-and-glossary-audit` @ `59e1ea2`.

---

## §1 Findings regression — does every fix still hold?

Method: for each documented finding, revert the fix in source, run the test that
is supposed to guard it, and record whether that test went red. A guard that
stays green while the bug is back is worse than no guard, because it is a claim
of safety that is not true.

Harness: `scratchpad/sabotage.py` (10 mutations, auto-reverting).

### Result table

| # | Finding | Fix site | Guard | Genuine sabotage test? |
| --- | --- | --- | --- | --- |
| F1 | Substring collision: `30-80% of standard starting dose` contains `standard starting dose` | `cpic_engine.py` regex conditions | `test_label_mapping*.py` | **YES — caught** |
| F1b | A rule establishing whether a directive exists must not read implications | `cpic_engine.py` `match_field` scoping | `test_label_mapping*.py` | **YES — caught** |
| F4 | Phenotype→label invariant (rendered `Safe` for 195/400 samples) | `cpic_engine.py:726` enforcement gate | `test_phenotype_label_invariant.py` | **NO — see below** |
| F5 | `sourceDiplotypes` vs `recommendationDiplotypes` | `pharmcat_runner.py:468` | `test_pharmcat_parser.py`, `test_captured_outputs.py` | **NO — see below** |
| F6 | Label/prose cross-check | `explanation/consistency.py` | `test_consistency.py` | **YES — caught** |
| F7 | Coverage gate thresholds | `position_requirements.json` | `test_coverage_gate.py` | **YES — caught** |
| F7b | Coverage gate disabled entirely | `coverage.py` `sufficient` | `test_coverage_gate.py` | **YES — caught** |
| F8 | No-data vs Indeterminate conflation | `cpic_engine.resolve_phenotype` | `test_phenotype_label_invariant.py`, `test_phenotype_table.py` | **YES — caught** |
| F9 | CYP2D6 never fabricated | `pharmcat_runner.py` gene list | `test_pharmcat_parser.py`, `test_sample_vcfs.py`, `test_captured_outputs.py` | **YES — caught** |
| F10 | Developer-string leak | `coverage.py` warning text | `test_no_developer_strings.py` | **NOT TESTED — anchor moved** |

---

### F5 — THE MOST DANGEROUS FINDING IN THIS AUDIT

**Reverting the fix silently turns a declined answer into a confident wrong one,
and the entire 630-test suite stays green.**

Mutation (one word):

```python
# app/pharmcat_runner.py:468
source = block.get("sourceDiplotypes") or []          # fixed
source = block.get("recommendationDiplotypes") or []  # reverted
```

Measured through the live API on `demo_dpyd_indeterminate.vcf`:

| | fluorouracil | capecitabine |
| --- | --- | --- |
| **baseline** | `Unknown`, confidence **0.1**, phenotype `Unknown` | `Unknown`, 0.1, `Unknown` |
| **reverted** | **`Safe`, confidence 0.95**, phenotype `NM` | **`Safe`, 0.95, `NM`** |

Diplotype rendered:

- baseline `c.85T>C (*9A)/[c.85T>C (*9A) + c.1371C>T]`
- reverted `c.85T>C (*9A)/c.85T>C (*9A)` — the compound half is dropped

These are the two drugs where DPYD deficiency is **fatal at a standard dose**.
The regression converts "we cannot say" into "Safe, 95% confident", and:

- `test_pharmcat_parser.py` — passes
- `test_captured_outputs.py` — passes
- full backend suite — **630 passed, 5 skipped**

**Why the existing tests miss it:** they assert on fixture reports whose
`sourceDiplotypes` and `recommendationDiplotypes` happen to agree, so the two
code paths are indistinguishable on the corpus being tested. No fixture exercises
a compound heterozygote where the two lists differ — which is precisely the case
the original finding was about.

### F4 — enforcement gate unguarded, currently saved by an undocumented second layer

Mutation:

```python
# app/cpic_engine.py:726
if gene_call is not None and not resolved.asserted:   # fixed
if False:                                             # reverted
```

- `test_phenotype_label_invariant.py` — passes
- full backend suite — **630 passed, 5 skipped**

**But the output does not change.** Probed directly at `evaluate()` with the
exact 195/400 shape (SLCO1B1 candidates `Normal Function` + `Indeterminate`):
both baseline and reverted return `label=Unknown, severity=none, conf=0.0`.

The reason is defence in depth that **nobody wrote down and nothing guards**:
`resolve_phenotype` still returns `Phenotype.UNKNOWN`, and `label_mapping.yaml`
happens to contain no rule keyed on an `Unknown` phenotype, so the lookup falls
through to Unknown anyway.

So the accurate statement is narrower than "the invariant is unguarded and
catastrophic", and worth stating precisely:

1. The early enforcement gate has **no test that fails when it is deleted**.
2. Deleting it is currently harmless **by accident**, not by design.
3. The property actually keeping users safe — *no mapping rule may key on an
   unasserted phenotype* — is **not asserted anywhere**. Adding such a rule, or
   changing `resolve_phenotype` to return a naive phenotype, would reopen the
   defect with both layers gone and every test still green.

`test_reverting_the_invariant_is_detected` does exist and is well written, but it
exercises `resolve_phenotype` — the **resolver**, not the **enforcement**. Same
structural shape as every other finding in this project: two components each
correct, and the edge between them unverified.

### F10 — not tested, anchor moved

The mutation targeted a sentence in `coverage.py` that the §2 rewording of the
glossary triage had already changed, so the harness reported ANCHOR-NOT-FOUND
rather than a result. `test_no_developer_strings.py` was separately verified as
genuine during the glossary work (it caught `picard`/`crossmap`/`liftovervcf`
live, which is why those strings were rewritten), but **it was not re-verified by
this harness** and should not be counted as confirmed here.

### Findings with no guarding test at all

- **F5's differing-diplotype case.** No fixture in the corpus has
  `sourceDiplotypes != recommendationDiplotypes`. The single most consequential
  fix in the project rests on a distinction no test data exercises.
- **The "no mapping rule may key on an unasserted phenotype" property** (F4's
  real second layer). Unwritten and unasserted.
- **Simvastatin Unknown-vs-alternative** and **the "No recommendation"
  provenance violation**: not reachable by the mutation harness because both are
  properties of `label_mapping.yaml` content rather than of a code branch. They
  were not verified in this audit. Recorded as **unverified**, not as passing.

---

## §2 Truth-labelled data — searched live, not assumed

### What PharmCAT itself did

Sangkuhl et al., *Clinical Pharmacology & Therapeutics* (2019), "Pharmacogenomics
Clinical Annotation Tool (PharmCAT)". Their validation compared **1000 Genomes
sequences of Coriell samples against GeT-RM characterisation, n=59**: concordant
on all 59 for CYP2C19, CYP2C9, CYP3A5, IFNL3, VKORC1, and 58/59 for TPMT.
Accessed 2026-08-11.

That is the route the brief hoped for, and it is the right one. It did not
reproduce here, for a reason worth recording.

### GeT-RM retrieval

- `https://www.cdc.gov/labquality/get-rm/...` → **HTTP 403** to scripted clients
  (unchanged from the previous attempt).
- `https://ftp.ncbi.nlm.nih.gov/pub/GeT-RM/` → **HTTP 404**.
- **A GeT-RM workbook is already vendored**: `test-data/reference/
  getrm_pharmacogenomics.xls` — a Composite Document created 2008-03-31, last
  saved 2015-06-26. One sheet, 115 rows, **107 distinct Coriell NA IDs**.

Its columns are **CYP2D6, CYP2C19, CYP2C9, VKORC1, UGT1A1**. Of our seven genes
that is an overlap of **two** (CYP2C19, CYP2C9) — CYP2D6 is present but we never
call it from a VCF by design. **No consensus exists in this table for SLCO1B1,
TPMT, NUDT15 or DPYD**, which is four of the six drugs we report on.

### The overlap actually found

Fetched the 1000 Genomes phase-3 panel
(`integrated_call_samples_v3.20130502.ALL.panel`, 2504 samples, accessed
2026-08-11) and intersected:

| | count |
| --- | ---: |
| GeT-RM Coriell IDs in the vendored table | 107 |
| 1000G phase-3 samples | 2504 |
| our previously-sliced n=400 cohort | 400 |
| **GeT-RM ∩ 1000G phase 3** | **1** |
| GeT-RM ∩ our n=400 cohort | **0** |

The single sample is **NA12273** — which is already this project's demo file.

Two things follow, and both are findings rather than failures:

1. **Our n=400 cohort was drawn entirely from `HG*` IDs** and could never have
   overlapped a `NA*`-keyed GeT-RM table. The 400-sample fidelity work was
   therefore self-consistency, never external truth, and nothing in the repo
   said so.
2. **PharmCAT's n=59 came from a different, later GeT-RM release.** The 2008/2015
   workbook on disk is not the table they used; the larger PGx characterisations
   (which do overlap 1000G/HapMap heavily) sit behind the CDC page that 403s.
   Obtaining it is a manual browser download, not a scripted one.

**Final usable truth-labelled set: n = 1 (NA12273), covering 2 of our 7 genes.**
Stated plainly, as instructed: that is a fact about the availability of
pharmacogenomic ground truth, not a shortfall of this audit.

## §3 GIAB callable regions vs the coverage gate

**Not performed.** GIAB high-confidence benchmarks exist for HG001-HG007 with
callable-region BEDs (NIST; benchmarks for HG002/HG003/HG004 public), but none of
HG001-HG007 appears in the vendored GeT-RM table, so a BED would not have been
attached to a truth-labelled PGx sample. Pairing them requires the larger GeT-RM
release blocked in §2. Recorded as **not attempted**, not as passed.

## §4 The one truth-labelled sample, end to end

Through the app, all six drugs. GeT-RM consensus beside ours:

| gene | GeT-RM consensus | ours | verdict |
| --- | --- | --- | --- |
| CYP2C19 | `*1/*2` | `*1/*2` | **diplotype CONCORDANT** |
| CYP2C9 | `*1/*2` | `Undetermined (2 equally likely)` | **DISCORDANT** |
| CYP2D6 | `*1/*1` | `Unknown` | correct refusal by design |
| VKORC1, UGT1A1 | present | — | genes we do not report |
| SLCO1B1, TPMT, NUDT15, DPYD | **no consensus** | — | no ground truth available |

Per-drug output and coverage:

| drug | gene | diplotype | phenotype | label | coverage |
| --- | --- | --- | --- | --- | --- |
| clopidogrel | CYP2C19 | `*1/*2` | Unknown | Unknown | 16/35 = 45.7% (min 100) |
| warfarin | CYP2C9 | Undetermined | Unknown | Unknown | 17/88 = 19.3% (min 100) |
| simvastatin | SLCO1B1 | `*1/*1` | Unknown | Unknown | 20/35 = 57.1% (min 100) |
| codeine | CYP2D6 | Unknown | Unknown | Unknown | 67/157 (never called) |
| azathioprine | TPMT | `*1/*1` | Unknown | Unknown | 9/45 = 20.0% (min 80) |
| **fluorouracil** | **DPYD** | **Reference/Reference** | **NM** | **`Safe`** | **31/83 = 37.3% (min 20)** |

### The finding in that table

**On the only truth-labelled sample available, the pipeline emits a confident
`Safe` for fluorouracil from a file it simultaneously judges too thin for every
other gene.**

Six genes are gated for insufficient coverage. DPYD alone passes — because its
threshold is 20% and it reached 37.3% — and produces `Reference/Reference` →
Normal Metabolizer → `Safe`. Fluorouracil is the drug where DPYD deficiency is
fatal at a standard dose.

The 37.3% figure is not new: `input_requirements.md` already records "DPYD passes
at 37.3% coverage with a 0% wrong rate" as the justification for the asymmetric
threshold. What this audit adds is that the same number, on a real 1000 Genomes
sample rather than a synthetic sweep, renders as a green `Safe` to a user while
the rest of the screen says the file is inadequate. The measured wrong rate that
justified the threshold was obtained on **synthetic** inputs where the true
genotype was known by construction; it has never been checked against an external
truth for DPYD, and §2 shows no such truth is currently obtainable.

This is reported, not repaired, and the threshold was not touched.

## §5–§7

**Not performed in this session.** See the checkpoint block below.

---

## Checkpoint — what was NOT done, and why

Stopped here on context budget, at a coherent boundary, with the repo consistent
(`git status` clean apart from this report; every sabotage mutation reverted and
verified reverted).

| section | status |
| --- | --- |
| §1 findings regression | **done** — 9 of 10 mutations executed, 1 anchor stale |
| §2 truth-labelled data | **done** — n=1, route documented |
| §3 GIAB callable regions | **not attempted** — blocked by §2, reason recorded |
| §4 truth samples end to end | **done for n=1** |
| §5 constructed-allele sweep | **NOT DONE** |
| §6 hostile/malformed input | **NOT DONE — and it has still never been run** |
| §7 contract + client state coverage | **NOT DONE** |

§6 is the most important omission. It was specified during the hardening pass,
was not executed then, and has not been executed now — so the claim "every
malformed input returns a clear 4xx" remains **unverified** for a second
consecutive audit. It needs no external data and is entirely self-contained; it
should be the first thing run next.

§5 needs PharmVar/PharmCAT allele definitions expanded into per-allele VCFs —
mechanical but compute-heavy. §7 is cheap and could be folded into the next pass.
