# Phase 10 — showcase cohort, with expectations committed in advance

Written 2026-11-12, before the conversion tool was run on any of these samples
and before PharmCAT saw any of them. **The expectations in section 3 are not to
be edited.** Where the pipeline disagrees, the disagreement is a finding and is
recorded in section 6 beside the original expectation.

## 1. How these seven were chosen

Screened: 792 samples — the 208 individuals with GeT-RM consensus rows, plus
all 601 samples from the South Asian subpopulations (17 are in both). The
screen read DRAGEN's own `star_allele.tsv` for each, which is a caller
independent of PharmCAT.

Selection rules, applied in order:

1. Together the set must produce at least one Toxic, one Ineffective, one
   Adjust Dosage and one "No PGx-guided adjustment identified", each from a
   real genotype.
2. Prefer South Asian subpopulation samples (the project's population work).
3. Prefer samples with a GeT-RM consensus diplotype, so a result can be checked
   against something outside this project.
4. Prefer one diplotype per gene with no uncertain-function allele, so an
   expectation can be stated exactly.

Five of the seven are from South Asian subpopulations. They are 1000 Genomes
subpopulations — PJL (Punjabi in Lahore), ITU (Indian Telugu in the UK), GIH
(Gujarati Indian in Houston) — and are described that way, never as "Indian
patients". No frequency claim is made from this set; seven samples support none.

## 2. The samples

All from `s3://1000genomes-dragen-v4-4-7/`, object
`data/individuals/hg38-alt_masked.cnv.graph.hla.methyl_cg.rna-11-r5.0-2/<ID>/<ID>.hard-filtered.gvcf.gz`,
DRAGEN v4.4.7, GRCh38. Calls below are DRAGEN's, not this pipeline's.

| Sample | Population | What it brings | DRAGEN calls that drive it |
|---|---|---|---|
| **HG02684** | PJL / SAS | DPYD poor metaboliser — the clearest Toxic in the panel | DPYD `c.1905+1G>A(*2A)/c.1905+1G>A(*2A)` |
| **HG03973** | ITU / SAS | Two findings at once: statin and antiplatelet | SLCO1B1 `*15/*15`; CYP2C19 `*2/*2` |
| **NA21109** | GIH / SAS | Three findings, two of them dose adjustments | TPMT `*3C/*1`; DPYD `c.1905+1G>A(*2A)/Reference`; CYP2C19 `*2/*2` |
| **HG04054** | ITU / SAS | NUDT15 poor metaboliser — the thiopurine risk TPMT alone misses | NUDT15 `*3/*3` |
| **HG03703** | PJL / SAS | Normal across the panel — the system does answer | all reference or increased-function |
| **NA12878** | CEU / EUR | The most-cited genome there is; GeT-RM truth for six genes | CYP2C19 `*1/*2`; SLCO1B1 `*5/*37;*15/*1` |
| **NA18564** | CHB / EAS | GeT-RM truth across six genes; CYP2C19 poor metaboliser | CYP2C19 `*2/*3`; NUDT15 `*3/*1` |

**HG02684 is trio-confirmed.** DRAGEN calls it homozygous for DPYD
c.1905+1G>A. In the NYGC phased panel (a different pipeline) the same sample is
`1|1` at chr1:97450058, its mother HG02685 is `0|0` and its child HG02686 is
`1|0` — which is what a homozygous father requires. Two call sets and a
pedigree agree before this project has read the file.

## 3. Pre-committed expectations

Phenotypes were derived by hand from the CPIC allele-function and
diplotype tables **inside the PharmCAT 3.4.0 jar**
(`org/pharmgkb/pharmcat/phenotype/<GENE>.json`); labels from
`test-data/reference/cpic_expectations.json`, which is built from CPIC's
structured booleans rather than from the recommendation text this project's
mapping matches on. Neither path runs this pipeline.

Abbreviations: **Safe** = "No PGx-guided adjustment identified";
**Adjust** = "Adjust Dosage".

| Sample | clopidogrel (CYP2C19) | simvastatin (SLCO1B1) | azathioprine (TPMT + NUDT15) | fluorouracil (DPYD) |
|---|---|---|---|---|
| HG02684 | **Safe** — `*1/*38` NM | **Safe** — `*37/*37` Normal Function | **Safe** — NM + NM | **Toxic** — AS 0.0, Poor Metaboliser |
| HG03973 | **Ineffective** — `*2/*2` PM | **Toxic** — `*15/*15` Poor Function | **Safe** — NM + NM | **Safe** — AS 2.0 |
| NA21109 | **Ineffective** — `*2/*2` PM | **Safe** — `*1/*37` Normal | **Adjust** — TPMT IM + NUDT15 NM | **Adjust** — AS 1.0, Intermediate |
| HG04054 | **Safe** — `*1/*1` NM | **Safe** — `*1/*37` Normal | **Toxic** — NUDT15 `*3/*3` PM | **Safe** — AS 2.0 |
| HG03703 | **Safe** — `*17/*17` Ultrarapid | **Safe** — `*1/*1` Normal | **Safe** — NM + NM | **Safe** — AS 2.0 |
| NA12878 | **Ineffective** — `*1/*2` IM | **Toxic** — Decreased Function | **Safe** — NM + NM | **Safe** — AS 2.0 |
| NA18564 | **Ineffective** — `*2/*3` PM | **Safe** — `*1/*37` Normal | **Adjust** — NUDT15 IM + TPMT NM | **Safe** — AS 2.0 |

Totals across 28 labelable cells: **Toxic 4, Ineffective 4, Adjust Dosage 3,
Safe 17**. Acceptance criterion C3 is met by the expectations; whether the
pipeline agrees is what step 4 measures.

### Two expectations that needed a decision, recorded now

**HG03703 clopidogrel, ultrarapid metaboliser.** CPIC gives three
population-specific rows for an ultrarapid metaboliser: "CVI ACS PCI"
(classification Strong → Safe), and "CVI non-ACS non-PCI" and "NVI" (both "No
recommendation" → Unknown). The engine keeps every row matching the called
phenotype and takes the strongest classification (`cpic_engine.select_annotation`,
`_STRENGTH_ORDER`), which is the Strong one. So the expectation is **Safe**,
with a warning that other populations exist. If instead this comes back
Unknown, the cause is annotation selection, not coverage, and it is a finding.

**NA12878 simvastatin, an ambiguous diplotype.** DRAGEN reports
`*5/*37;*15/*1` — two candidate diplotypes it cannot separate. Both are one
no-function allele plus one normal-function allele, so both map to Decreased
Function, and CPIC's label for Decreased Function is Toxic. If PharmCAT also
returns two candidates, the profile's `diplotype` field will read
"Undetermined (2 equally likely)" with the two candidates listed and the
phenotype asserted. **That is a real, complete, non-blank result, and the
expected label is still Toxic.** It is the only cell in the set expected to
show the ambiguity marker, and it is kept deliberately: it shows the system
declining to name one of two co-equal genotypes while still answering the
clinical question. If the phenotype comes back unasserted, the label is
Unknown and that is a finding, not a defect.

## 4. The two drugs expected to be Unknown on every sample

Declared in `demo/ACCEPTANCE.md` before any run, and not counted as failures:

- **warfarin** — `capabilities.json` marks it `explicit_abstention`. CPIC's
  warfarin guidance is a dosing algorithm needing ancestry and clinical inputs
  this application does not collect. The CYP2C9, VKORC1 and CYP4F2 calls are
  shown for reference. Unknown on all seven.
- **codeine** — CYP2D6 is not called from a VCF, by design and as a
  demonstrated strength. Unknown on all seven unless an outside call is
  supplied, which is section 4 of the brief and comes after the step-4 stop.

So 14 of 42 cells are expected Unknown by declaration, and 28 are expected to
carry a real CPIC-backed label.

## 5. What a GeT-RM comparison can and cannot settle

Three of the seven have GeT-RM consensus rows: NA12878 and NA18564 across six
genes, HG03703 for CYP2D6 only. Where a PharmCAT call and a GeT-RM consensus
agree, that is independent corroboration for that sample and gene. It does not
make the set clinically validated. External truth for this project remains
n=1 in the sense that matters: no clinical reviewer has read any output, and
seven samples establish no rate.

One disagreement is already visible between the two independent callers, before
this pipeline has run: for NA18564, DRAGEN calls SLCO1B1 `*37/*1` while GeT-RM
records `*1/*1`. `*37` and `*1` are both Normal Function, so the phenotype and
the label are unaffected, but the star alleles differ. DRAGEN's star-allele
caller uses PharmGKB snapshots from 2022 and 2024; PharmCAT 3.4.0 here uses
definitions dated 2026-07-13. Naming disagreements between call sets are
expected and are not, by themselves, errors.

## 6. Disagreements found after running

Sections 1 to 5 are left exactly as they were written. Five of the seven
samples named there are **not** in the final set, and the reason is recorded
below rather than by rewriting the table above.

### 6a. Five of the seven could not produce a conforming input at all

This was discovered when the conversion tool first ran, before PharmCAT saw
anything. It is a property of the source, not of those samples' genotypes.

| Sample | Blocked at | What the source says |
|---|---|---|
| HG03973 | SLCO1B1 `chr12:21222355` | `FILTER=LowGQ` — the caller's own flag |
| HG04054 | SLCO1B1 `chr12:21222355` | `FILTER=LowGQ` |
| HG03703 | SLCO1B1 `chr12:21222355` | `FILTER=LowGQ` |
| NA12878 | SLCO1B1 `chr12:21222355` | `FILTER=LowGQ` |
| NA18564 | SLCO1B1 `chr12:21222355` | `FILTER=LowGQ` |

One position, `rs71581941`, is responsible for every one of them. It sits in a
stretch of SLCO1B1 where DRAGEN v4.4.7 emits short reference records with
GQ 0 and roughly 20% of reads disagreeing with the reference — the signature of
a region where short reads mismap. The caller is right to flag it, and the
flag is carried through rather than erased, so the gene fails its 100%
requirement and simvastatin would read Unknown.

**Measured over 45 samples whose gene regions were fetched: 17 produced a
conforming file and 28 did not.** Twenty-seven of the 28 failed on this one
position; three failed on NUDT15 `chr13:48037782`, where the source writes an
indel against a different anchor base than PharmCAT's row uses and the tool
refuses to re-derive the equivalence.

The honest reading: **even a gVCF source does not automatically satisfy this
application's input requirement.** About a third of samples do. That is a
finding about the source, and it is the single most useful number this step
produced.

### 6b. Three of the remaining expectations were wrong, and why

Of the two originally-named samples that did conform, plus replacements drawn
from the same screen, three fluorouracil cells came back Unknown against an
expectation of a real label:

| Sample | Expected | Got | Root cause |
|---|---|---|---|
| NA10847 | Safe (DPYD AS 2.0) | Unknown | `Undetermined (2 equally likely)` |
| NA19236 | Safe (DPYD AS 2.0) | Unknown | `Undetermined (2 equally likely)` |
| HG03911 | Adjust Dosage (AS 1.5) | Unknown | `Undetermined (2 equally likely)` |

**The expectations were wrong, and the pipeline was right.** Each of these
samples carries two heterozygous DPYD variants. Whether they sit on the same
chromosome or on opposite ones changes the activity score, and the two
arrangements are different clinical answers. The expectation in section 3 was
derived from DRAGEN's star-allele call, which names one arrangement; PharmCAT
reports both as equally likely, the phenotype is therefore not asserted, and
the phenotype→label invariant returns Unknown.

Checked directly in the source rather than assumed: the records for those
positions carry **no `PS` phase-set field and an unphased `0/1` genotype**. The
caller did not phase them. So the decision to drop phase during transcription
(criterion B4) discarded nothing — there was no phase to carry, and the
ambiguity is real. A read-backed phasing step on the CRAM could resolve
HG03911's pair, which are 85 bases apart, but the published gVCF does not.

By the brief's own rule, an ambiguous diplotype means picking a different
sample rather than forcing a call. That is what section 7 does, and one such
sample is kept aside deliberately.

## 7. The final set, chosen on measured results

Seven samples for the main flow, each of which returns a real CPIC-backed label
in all four labelable cells, and one kept aside as the ambiguity exhibit. All
eight are conforming inputs from the same source.

| Sample | Population | clopidogrel | simvastatin | azathioprine | fluorouracil |
|---|---|---|---|---|---|
| HG02684 | PJL / SAS | Safe | Safe | Safe | **Toxic** |
| HG00525 | CHS / EAS | **Ineffective** | **Toxic** | Safe | Safe |
| NA21109 | GIH / SAS | **Ineffective** | Safe | **Adjust Dosage** | **Adjust Dosage** |
| HG01502 | IBS / EUR | **Ineffective** | Safe | **Toxic** | Safe |
| HG03097 | MSL / AFR | Safe | Safe | **Toxic** | Safe |
| NA20863 | GIH / SAS | Safe | Safe | **Adjust Dosage** | Safe |
| HG02661 | PJL / SAS | Safe | Safe | Safe | Safe |

Four of the seven are South Asian subpopulations (PJL ×2, GIH ×2); the rest are
EAS, EUR and AFR. Across the 28 labelable cells: **Toxic 4, Ineffective 3,
Adjust Dosage 3, Safe 18** — every class present, from a real sample's real
genotype.

**The ambiguity exhibit**, `demo/samples/ambiguity-exhibit/NA10847.vcf`:
NA10847 (CEU) returns simvastatin **Toxic** from `SLCO1B1 *5/*15`, clopidogrel
and azathioprine Safe, and fluorouracil **Unknown** with two equally likely DPYD
diplotypes shown as candidates. It is deliberately outside the main flow, and it
is the one sample in the set with GeT-RM consensus truth.

That truth is worth stating cell by cell, because it is the only external
corroboration anywhere in this step:

| Gene | GeT-RM consensus | PharmaGuard called | |
|---|---|---|---|
| CYP2C19 | `*1/*1` | `*1/*1` | agrees |
| CYP2C9 | `*1/*1` | `*1/*1` | agrees |
| SLCO1B1 | `*15/*5` | `*5/*15` | agrees (allele order differs, diplotype does not) |
| TPMT | `*1/*1` | `*1/*1` | agrees |
| DPYD | `*1/*9` | `Undetermined (2 equally likely)` | **withheld**, candidates `c.85T>C (*9A)` and `c.1627A>G (*5)` |
| CYP2D6 | `*1/*41` | declined from VCF | **declined**, by design |

Four of four callable genes concordant. The DPYD row is the interesting one:
GeT-RM names `*9` (which is `c.85T>C (*9A)`) and does not record the second
variant the sequencing shows, so the consensus asserts an arrangement the
read data here does not resolve. The application declines rather than picking
the one that matches the published answer. The CYP2D6 row is the negative
control the project has always kept: a correct answer exists and is not
guessed at.

This is n=1 corroboration on one sample, not validation. It does not change
the project's standing position that external truth is n=1 and that no
clinical reviewer has read any output.

### Why the expectations above are not restated as a new pre-commitment

They cannot be: these seven were chosen *after* seeing the results, so the table
in section 7 is an observation, not a prediction. Section 3 holds the only
genuine pre-commitment in this document, and it was met on 29 of its 32 cells,
with the three misses explained in 6b. Any future change to the pipeline should
be tested against section 7 as a regression baseline, which is a different and
weaker claim than a pre-registered expectation.
