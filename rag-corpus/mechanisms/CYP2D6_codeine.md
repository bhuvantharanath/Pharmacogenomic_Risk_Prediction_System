---
gene: CYP2D6
drug: codeine
aliases: [methylmorphine]
related_genes: [OPRM1, COMT]
source_guideline: "Annotation of CPIC Guideline for codeine and CYP2D6"
source_url: https://www.clinpgx.org/guidelineAnnotation/PA166104996
primary_citation: >-
  Crews KR et al. Clinical Pharmacogenetics Implementation Consortium Guideline
  for CYP2D6, OPRM1, and COMT Genotypes and Select Opioid Therapy.
  Clin Pharmacol Ther (2021). PMID: 33387367
retrieved: 2026-07-22
retrieved_via: "PharmCAT 3.4.0 report.json (CPIC Guideline Annotation citations)"
contains_dosing: false
reviewed_by: null
---

# CYP2D6 and codeine — mechanism

## What the gene product does

CYP2D6 is a hepatic cytochrome P450 enzyme responsible for metabolising a large
share of commonly used drugs. *CYP2D6* is unusually variable: as well as
single-nucleotide variants that alter or abolish activity, the gene is subject
to **whole-gene deletions and duplications**, so copy number differs between
people. Activity is conventionally summarised as an activity score derived from
both alleles.

## How the drug is handled

Codeine is a **prodrug** with little analgesic activity of its own. CYP2D6
O-demethylates a small fraction of a dose into morphine, and it is that morphine
that produces analgesia. Other routes (glucuronidation, CYP3A4) handle most of
the dose but do not produce the active compound.

Analgesia from codeine therefore depends almost entirely on how much CYP2D6
activity a person has.

## Why altered function changes the outcome

- **Absent or greatly reduced CYP2D6 activity** produces little morphine, so
  there is little analgesia. The problem is **lack of effect** — the patient's
  pain is untreated while they appear to be on an analgesic.

- **Greatly increased activity (gene duplication)** converts more codeine to
  morphine than expected, producing morphine exposure out of proportion to the
  administered dose. This is the **toxicity** direction, and the reason codeine
  carries warnings about respiratory depression in ultrarapid metabolisers,
  including in breastfed infants of ultrarapid mothers.

Codeine is unusual in having a serious risk at *both* ends of the activity
range, in opposite directions.

## A structural note for the explanation layer

**PharmCAT cannot call CYP2D6 from an ordinary VCF.** The star alleles depend on
structural and copy-number variation that a VCF does not represent, so PharmCAT
reports `callSource: NONE` even when every CYP2D6 position is present in the
file. PharmaGuard therefore returns `Unknown` for codeine and states why.

An explanation here must be explicit that **no CYP2D6 result was obtained**, and
must not imply a phenotype. The correct message is that this gene needs a
different assay (or an externally determined diplotype), not that the patient is
normal. Absence of a result is not a reassuring result.
