---
gene: TPMT
drug: azathioprine
aliases: [Imuran, thiopurine]
related_genes: [NUDT15]
source_guideline: "Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT"
source_url: https://www.clinpgx.org/guidelineAnnotation/PA166104933
primary_citation: >-
  Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC)
  Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes:
  2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934
retrieved: 2026-07-22
retrieved_via: "PharmCAT 3.4.0 report.json (CPIC Guideline Annotation citations)"
contains_dosing: false
reviewed_by: null
---

# TPMT (and NUDT15) and azathioprine — mechanism

## What the gene products do

*TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that
methylates thiopurine compounds and so diverts them away from the pathway that
produces active metabolites.

*NUDT15* encodes a nucleotide diphosphatase that dephosphorylates active
thioguanine nucleotides, limiting how much active metabolite is incorporated
into DNA. CPIC's thiopurine guideline covers both genes together, because either
one can independently limit a patient's tolerance.

## How the drug is handled

Azathioprine is a prodrug that is converted to mercaptopurine and then, through
several steps, into thioguanine nucleotides (TGNs). TGNs are the active species:
they are incorporated into DNA, and that incorporation produces both the
intended immunosuppressive effect and the drug's principal toxicity.

TPMT and NUDT15 both act as **brakes** on this pathway — TPMT by methylating
precursors away from TGN formation, NUDT15 by degrading active nucleotides.

## Why altered function changes the outcome

- **Reduced or absent TPMT (or NUDT15) function** removes a brake. More
  thioguanine nucleotide accumulates in haematopoietic cells for the same
  administered amount. The characteristic consequence is bone-marrow
  suppression: leukopenia, neutropenia, and in severe cases life-threatening
  myelosuppression. This is a **toxicity** problem, not a loss-of-effect problem.

- **Normal function in both genes** gives the metabolite exposure that standard
  thiopurine dosing was designed around.

- The two genes are **independent**: a patient can be normal for one and
  deficient for the other, and the deficient gene is the one that governs the
  recommendation. This is why PharmaGuard reports whichever of the two genes is
  more abnormal rather than defaulting to one.

## Notes for the explanation layer

- Frame reduced function as *accumulation of active metabolite*, with bone
  marrow as the tissue at risk.
- Do not state dose reductions, percentages, or monitoring intervals here — all
  of that is CPIC's, delivered through PharmCAT at runtime.
- Mercaptopurine and thioguanine are handled by the same pathway, but only
  discuss the drug actually being analysed.
