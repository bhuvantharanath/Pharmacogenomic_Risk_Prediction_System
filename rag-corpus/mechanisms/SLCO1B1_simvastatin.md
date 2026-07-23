---
gene: SLCO1B1
drug: simvastatin
aliases: [Zocor]
source_guideline: "Annotation of CPIC Guideline for simvastatin and SLCO1B1"
source_url: https://www.clinpgx.org/guidelineAnnotation/PA166105005
primary_citation: >-
  Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation
  Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and
  Statin-Associated Musculoskeletal Symptoms.
  Clin Pharmacol Ther (2022). PMID: 35152405
retrieved: 2026-07-22
retrieved_via: "PharmCAT 3.4.0 report.json (CPIC Guideline Annotation citations)"
contains_dosing: false
reviewed_by: null
---

# SLCO1B1 and simvastatin — mechanism

## What the gene product does

*SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing)
membrane of liver cells. Its job is to move drugs out of portal blood and into
hepatocytes. It is a **transporter, not a metabolising enzyme**, which is why
its phenotypes are described as function categories (normal, decreased, poor
function) rather than metaboliser categories.

## How the drug is handled

Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
its site of action and its route of elimination. OATP1B1 performs the uptake
step that concentrates the drug (chiefly its active acid form) into liver cells.

Efficient hepatic uptake therefore does two things at once: it delivers the drug
to its target, and it keeps systemic — particularly skeletal muscle — exposure
low.

## Why altered function changes the outcome

- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.

- **Normal function** gives typical hepatic uptake, typical systemic exposure,
  and the background level of musculoskeletal risk that standard dosing assumes.

Note the direction of the effect: the problem is not that the drug is cleared
too slowly by an enzyme, but that it is *not removed from the circulation into
the liver* fast enough.

## Notes for the explanation layer

- Describe OATP1B1 as a hepatic uptake transporter; avoid calling it a
  metabolising enzyme or describing "metaboliser status" for this gene.
- CPIC's 2022 guideline frames the outcome as statin-associated musculoskeletal
  symptoms; that is the phrasing to mirror.
- Dose ceilings and alternative statins are CPIC's to state at runtime.
