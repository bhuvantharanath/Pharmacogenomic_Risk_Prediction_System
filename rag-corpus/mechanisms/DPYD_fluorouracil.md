---
gene: DPYD
drug: fluorouracil
aliases: ["5-FU", "5-fluorouracil", fluoropyrimidine]
source_guideline: "Annotation of CPIC Guideline for fluorouracil and DPYD"
source_url: https://www.clinpgx.org/guidelineAnnotation/PA166122686
primary_citation: >-
  Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC)
  Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine
  Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729
retrieved: 2026-07-22
retrieved_via: "PharmCAT 3.4.0 report.json (CPIC Guideline Annotation citations)"
contains_dosing: false
reviewed_by: null
---

# DPYD and fluorouracil — mechanism

## What the gene product does

*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.

## How the drug is handled

Fluorouracil is a fluoropyrimidine antimetabolite. Only a small fraction of a
dose is converted into the cytotoxic nucleotides that disrupt DNA and RNA
synthesis in dividing cells; the rest is inactivated by DPD. Capecitabine is an
oral prodrug that is converted to fluorouracil in the body and is subject to the
same catabolic step.

DPD is therefore the body's main protective route for this drug class: it sets
how long active drug persists and how much reaches healthy dividing tissue such
as bone marrow and gut epithelium.

## Why altered function changes the outcome

- **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
  to active drug is higher and lasts longer for the same administered amount.
  Because fluoropyrimidines already have a narrow therapeutic window, this shows
  up as more severe toxicity — myelosuppression, mucositis, diarrhoea,
  hand-foot syndrome — rather than as loss of anticancer effect.

- **Complete DPD deficiency** removes the protective catabolic route almost
  entirely. Standard exposure can then be severe or fatal, which is why this is
  among the strongest pharmacogenomic signals in oncology.

- **Normal DPD activity** gives the exposure the drug's standard dosing was
  designed around.

Unlike clopidogrel, the gene here is a **clearance/protection** route, not an
activation step: less enzyme means *more* drug effect, not less.

## Notes for the explanation layer

- Frame reduced function as reduced *clearance* and increased *exposure*.
- DPD activity is often described as a percentage of normal population activity;
  any such figure must come from PharmCAT's CPIC recommendation text at runtime,
  not from this file.
- Dose reductions and titration strategies are CPIC's to state, not ours.
