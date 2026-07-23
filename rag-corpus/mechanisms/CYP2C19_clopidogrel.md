---
gene: CYP2C19
drug: clopidogrel
aliases: [Plavix]
source_guideline: "Annotation of CPIC Guideline for clopidogrel and CYP2C19"
source_url: https://www.clinpgx.org/guidelineAnnotation/PA166104948
primary_citation: >-
  Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline
  for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update.
  Clin Pharmacol Ther (2022). PMID: 35034351
retrieved: 2026-07-22
retrieved_via: "PharmCAT 3.4.0 report.json (CPIC Guideline Annotation citations)"
contains_dosing: false
reviewed_by: null
---

# CYP2C19 and clopidogrel — mechanism

## What the gene product does

CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that
oxidises a wide range of drug substrates. Its activity varies substantially
between people because the *CYP2C19* gene carries common variants that abolish,
reduce, or increase enzyme production.

## How the drug is handled

Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.

Because the drug depends on being *switched on* by an enzyme, the amount of
active metabolite formed is directly tied to how much functional CYP2C19 a
person has.

## Why altered function changes the outcome

- **Reduced or absent CYP2C19 function** means less prodrug is converted, so
  less active metabolite reaches the platelets. Platelet inhibition is weaker
  than intended. The clinical concern is therefore **therapeutic failure** —
  the drug not working — rather than the drug being toxic. Residual platelet
  reactivity remains high while the patient and clinician believe they are
  protected, which in the setting of recent stenting or acute coronary syndrome
  is where the risk of ischaemic events arises.

- **Normal function** produces the expected amount of active metabolite and the
  expected degree of platelet inhibition.

- **Increased function** produces more active metabolite. Platelet inhibition is
  at least as strong as expected; CPIC's own implications text for this group
  notes no association with higher bleeding risk.

This is the key asymmetry to keep in mind when reading a clopidogrel result: a
poor metaboliser's problem is *loss of effect*, not poisoning. That is why
PharmaGuard labels this case `Ineffective` rather than `Toxic`.

## Notes for the explanation layer

- The gene acts as an **activator** here, not a clearance route. Do not describe
  reduced CYP2C19 function as "the drug building up" — the opposite is true.
- Antiplatelet alternatives exist and CPIC names them, but the specific agents
  and any dosing come from PharmCAT's recommendation text at runtime, never from
  this file.
