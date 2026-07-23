---
gene: CYP2C9
drug: warfarin
aliases: [Coumadin, Jantoven]
related_genes: [VKORC1, CYP4F2]
source_guideline: "Annotation of CPIC Guideline for warfarin and CYP2C9, CYP4F2, VKORC1"
source_url: https://www.clinpgx.org/guidelineAnnotation/PA166104949
primary_citation: >-
  Johnson JA et al. Clinical Pharmacogenetics Implementation Consortium (CPIC)
  Guideline for Pharmacogenetics-Guided Warfarin Dosing: 2017 Update.
  Clin Pharmacol Ther (2017). PMID: 28198005
retrieved: 2026-07-22
retrieved_via: "PharmCAT 3.4.0 report.json (CPIC Guideline Annotation citations)"
contains_dosing: false
reviewed_by: null
---

# CYP2C9 and warfarin — mechanism

## What the gene product does

CYP2C9 is a hepatic cytochrome P450 enzyme. Among many substrates, it is the
principal route of clearance for S-warfarin, the more pharmacologically potent
of warfarin's two enantiomers.

VKORC1, a separate gene covered by the same CPIC guideline, encodes the drug's
*target* rather than its clearance route; CYP4F2 affects vitamin K turnover.
Warfarin response depends on all three, which is why the guideline is
multi-gene.

## How the drug is handled

Warfarin is administered as a racemic mixture. It inhibits vitamin K epoxide
reductase (VKORC1), depleting reduced vitamin K and so limiting the synthesis of
clotting factors II, VII, IX and X. S-warfarin drives most of that effect and is
cleared almost entirely by CYP2C9.

## Why altered function changes the outcome

- **Reduced CYP2C9 function** slows S-warfarin clearance, so the same
  administered amount produces higher steady-state exposure and a stronger
  anticoagulant effect. The clinical concern is over-anticoagulation and
  bleeding, particularly during initiation before INR monitoring has caught up.

- **Normal function** gives the clearance that standard initiation strategies
  assume.

Warfarin also has a very narrow therapeutic index and is monitored directly by
INR, which is why genotype informs the *starting* strategy rather than replacing
ongoing measurement.

## A structural note for the explanation layer

**CPIC's warfarin guidance is a dosing algorithm, not a phenotype-to-text
mapping.** It combines genotype with age, weight, height and interacting drugs
to compute a starting dose. As a result, PharmCAT returns warfarin annotations
with no per-phenotype recommendation text, and PharmaGuard reports `Unknown`
rather than inventing one.

An explanation for warfarin should therefore say plainly that a
phenotype-specific recommendation is not available from this pipeline and that
algorithmic dosing tools plus INR monitoring are how the guideline is applied.
Do not fill the gap with generalities that sound like guidance.
