# Adjudication worksheet — outstanding mechanism claims

**Generated:** 2026-07-24 15:22 UTC  
**Outstanding sentences:** 53  
**Unique claims to decide:** 42  
**Alignment:** deterministic token-overlap against the cited mechanism corpus. No model was consulted.

---

## How to use this

Each section is one **claim**, with the corpus passage that would support
it quoted underneath. Decide once per claim; the decision applies to every
entry listed under *Occurrences*.

**There is deliberately no suggested answer.** These are all `mechanism`
sentences — the class where this project showed rule-based checking fails,
and the automated check covering them was retired at a measured 30%
false-positive rate precisely so a person would read them. A proposed
verdict here would invite agreement rather than judgement.

### The question to ask

> Does the source below actually support this claim — including the
> **direction** of the effect?

Direction is the one thing no check in this project can catch. For a
prodrug (clopidogrel, azathioprine) *less* enzyme activity means *less*
active drug. For a drug cleared by an enzyme (fluorouracil) *less*
activity means *more* drug. A sentence with the arrow reversed is fluent,
fully sourced term-by-term, and wrong.

To record decisions afterwards:

```bash
python scripts/adjudicate.py --adjudicator "<your name>" --by-claim
```

---

## Triage summary

| Tier | Meaning | Claims |
| --- | --- | ---: |
| **1** | no passage aligned by the matcher (see caveat below) | **3** |
| 2 | source found; claim adds a causal step or specificity | 34 |
| 3 | source found; claim differs only in wording | 5 |

### What TIER 1 does and does not mean

**TIER 1 means the deterministic matcher found no aligning passage. It
does NOT mean the claim is fabricated.** The matcher compares domain
terms against the cited corpus; a claim that renders technical content
in plain words can fall into TIER 1 purely because the corpus never uses
those words. During construction this misfired repeatedly — a claim the
corpus plainly supports (*"produces active metabolites"*, *"marrow as
the tissue at risk"*) landed in TIER 1 until inflection and hyphen
handling were fixed, which moved 10 claims out of it.

That is the same weakness that got the closed-vocabulary check retired
at a 30% false-positive rate. It is disclosed here rather than smoothed
over, because a triage tier that cries wolf on faithful text is worse
than no triage at all — the reader stops trusting it.

Read the *What differs* line under each claim: it names the exact terms
the corpus did not account for, so a plain-language rendering is
distinguishable from an invented mechanism at a glance.

⚠️ **3 claim(s) had no passage aligned.** Listed first — not
because they are wrong, but because they are where a reader's attention
is most likely to be repaid.

---

# TIER 1 — no passage aligned (NOT a finding of fabrication)

## `AZAT-03` · azathioprine ()

**Claim as generated:**

> If your body breaks them down too slowly, it can lead to a buildup of toxic levels, causing myelosuppression.

**Source consulted:** `TPMT_azathioprine.md`  
**Cited as:** Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934

**Supporting text from the source:**

> ❌ **NO CORRESPONDING SOURCE TEXT FOUND.**
> No passage in the cited corpus file shares enough content with this
> claim to be offered as support.

**What differs:** 8 of 8 domain terms appear nowhere in the corpus file: breaks, buildup, causing, lead, myelosuppression, slowly, too, toxic

**Occurrences (1):** `azathioprine:IM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `AZAT-05` · azathioprine ()

**Claim as generated:**

> Your genetic result indicates that you have normal function in the enzymes that handle this process, which means that you are not at increased risk for the side effects associated with this drug.

**Source consulted:** `TPMT_azathioprine.md`  
**Cited as:** Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934

**Supporting text from the source:**

> ❌ **NO CORRESPONDING SOURCE TEXT FOUND.**
> No passage in the cited corpus file shares enough content with this
> claim to be offered as support.

**What differs:** 4 of 9 domain terms appear nowhere in the corpus file: associated, increased, indicates, side

**Occurrences (1):** `azathioprine:NM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `FLUO-09` · fluorouracil ()

**Claim as generated:**

> If DPD is not working properly, the drug can persist in the body for longer and cause more severe side effects.

**Source consulted:** `DPYD_fluorouracil.md`  
**Cited as:** Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

**Supporting text from the source:**

> ❌ **NO CORRESPONDING SOURCE TEXT FOUND.**
> No passage in the cited corpus file shares enough content with this
> claim to be offered as support.

**What differs:** 2 of 7 domain terms appear nowhere in the corpus file: cause, side

**Occurrences (1):** `fluorouracil:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

# TIER 2 — source found; claim adds a causal step or specificity

## `AZAT-01` · azathioprine ()

**Claim as generated:**

> Azathioprine is a medication that works by producing active metabolites that can affect the immune system.

**Source consulted:** `TPMT_azathioprine.md`  
**Cited as:** Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934

**Supporting text from the source:**

> thioguanine nucleotides, limiting how much active metabolite is incorporated
>
> — *TPMT_azathioprine.md*, §What the gene products do, line 10 (overlap 33%)

> - Frame reduced function as *accumulation of active metabolite*, with bone
>
> — *TPMT_azathioprine.md*, §Notes for the explanation layer, line 42 (overlap 33%)

> *NUDT15* encodes a nucleotide diphosphatase that dephosphorylates active
>
> — *TPMT_azathioprine.md*, §What the gene products do, line 9 (overlap 17%)

**What differs:** terms absent from the corpus: immune, producing, system

**Occurrences (1):** `azathioprine:IM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `AZAT-02` · azathioprine ()

**Claim as generated:**

> However, your genetic result may affect how well your body breaks down these active metabolites.

**Source consulted:** `TPMT_azathioprine.md`  
**Cited as:** Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934

**Supporting text from the source:**

> thioguanine nucleotides, limiting how much active metabolite is incorporated
>
> — *TPMT_azathioprine.md*, §What the gene products do, line 10 (overlap 67%)

> - Frame reduced function as *accumulation of active metabolite*, with bone
>
> — *TPMT_azathioprine.md*, §Notes for the explanation layer, line 42 (overlap 67%)

> *NUDT15* encodes a nucleotide diphosphatase that dephosphorylates active
>
> — *TPMT_azathioprine.md*, §What the gene products do, line 9 (overlap 33%)

**What differs:** terms absent from the corpus: breaks

**Occurrences (1):** `azathioprine:IM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `AZAT-06` · azathioprine ()

**Claim as generated:**

> The medication is converted into an active form that can affect the bone marrow, leading to a decrease in white blood cells.

**Source consulted:** `TPMT_azathioprine.md`  
**Cited as:** Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934

**Supporting text from the source:**

> The characteristic consequence is bone-marrow
>
> — *TPMT_azathioprine.md*, §Why altered function changes the outcome, line 28 (overlap 20%)

> - Frame reduced function as *accumulation of active metabolite*, with bone
>
> — *TPMT_azathioprine.md*, §Notes for the explanation layer, line 42 (overlap 20%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: blood, decrease, form, leading, white

**Occurrences (1):** `azathioprine:PM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `AZAT-07` · azathioprine ()

**Claim as generated:**

> Your genetic result removes a brake on this process, allowing more of the active form to accumulate and increase the risk of serious side effects.

**Source consulted:** `TPMT_azathioprine.md`  
**Cited as:** Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934

**Supporting text from the source:**

> - **Reduced or absent TPMT (or NUDT15) function** removes a brake.
>
> — *TPMT_azathioprine.md*, §Why altered function changes the outcome, line 26 (overlap 18%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: allowing, form, increase, serious, side

**Occurrences (1):** `azathioprine:PM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `AZAT-08` · azathioprine ()

**Claim as generated:**

> If these enzymes are not working properly, more of the active compounds can build up and cause problems.

**Source consulted:** `TPMT_azathioprine.md`  
**Cited as:** Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934

**Supporting text from the source:**

> *TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that
>
> — *TPMT_azathioprine.md*, §What the gene products do, line 5 (overlap 17%)

> methylates thiopurine compounds and so diverts them away from the pathway that
>
> — *TPMT_azathioprine.md*, §What the gene products do, line 6 (overlap 17%)

> *NUDT15* encodes a nucleotide diphosphatase that dephosphorylates active
>
> — *TPMT_azathioprine.md*, §What the gene products do, line 9 (overlap 17%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: build, cause

**Occurrences (1):** `azathioprine:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `AZAT-09` · azathioprine ()

**Claim as generated:**

> Normally, certain enzymes help control the amount of these active compounds.

**Source consulted:** `TPMT_azathioprine.md`  
**Cited as:** Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934

**Supporting text from the source:**

> *TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that
>
> — *TPMT_azathioprine.md*, §What the gene products do, line 5 (overlap 25%)

> methylates thiopurine compounds and so diverts them away from the pathway that
>
> — *TPMT_azathioprine.md*, §What the gene products do, line 6 (overlap 25%)

> *NUDT15* encodes a nucleotide diphosphatase that dephosphorylates active
>
> — *TPMT_azathioprine.md*, §What the gene products do, line 9 (overlap 25%)

**What differs:** terms absent from the corpus: control

**Occurrences (1):** `azathioprine:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `AZAT-10` · azathioprine ()

**Claim as generated:**

> This medication is converted into active compounds in your body, which can affect your bone marrow and cause low white blood cell counts.

**Source consulted:** `TPMT_azathioprine.md`  
**Cited as:** Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934

**Supporting text from the source:**

> The characteristic consequence is bone-marrow
>
> — *TPMT_azathioprine.md*, §Why altered function changes the outcome, line 28 (overlap 18%)

> - Frame reduced function as *accumulation of active metabolite*, with bone
>
> — *TPMT_azathioprine.md*, §Notes for the explanation layer, line 42 (overlap 18%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: blood, cause, counts, low, white

**Occurrences (1):** `azathioprine:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `CLOP-01` · clopidogrel ()

**Claim as generated:**

> Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme.

<details><summary>Wording variants of this claim (2)</summary>

> Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme to work.
> Clopidogrel is a prodrug that needs to be converted into an active metabolite by an enzyme to work.

</details>

**Source consulted:** `CYP2C19_clopidogrel.md`  
**Cited as:** Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Supporting text from the source:**

> Clopidogrel is a **prodrug**: the molecule that is swallowed has no
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 12 (overlap 29%)

> active metabolite formed is directly tied to how much functional CYP2C19 a
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 20 (overlap 29%)

> - **Reduced or absent CYP2C19 function** means less prodrug is converted, so
>
> — *CYP2C19_clopidogrel.md*, §Why altered function changes the outcome, line 25 (overlap 29%)

**What differs:** terms absent from the corpus: needs

**Occurrences (6):** `clopidogrel:IM`, `clopidogrel:NM`, `clopidogrel:PM`, `clopidogrel:RM`, `clopidogrel:URM`, `clopidogrel:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `CLOP-02` · clopidogrel ()

**Claim as generated:**

> If the enzyme is not working well, less active form is produced, leading to weaker platelet inhibition.

**Source consulted:** `CYP2C19_clopidogrel.md`  
**Cited as:** Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Supporting text from the source:**

> Platelet inhibition is weaker
>
> — *CYP2C19_clopidogrel.md*, §Why altered function changes the outcome, line 26 (overlap 38%)

> The active metabolite then binds irreversibly to the platelet P2Y12
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 15 (overlap 25%)

> active metabolite formed is directly tied to how much functional CYP2C19 a
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 20 (overlap 25%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: leading, produced

**Occurrences (1):** `clopidogrel:IM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `CLOP-03` · clopidogrel ()

**Claim as generated:**

> The amount of active form produced depends on how well this enzyme is working.

<details><summary>Wording variants of this claim (1)</summary>

> The amount of active form produced depends on how much functional enzyme a person has.

</details>

**Source consulted:** `CYP2C19_clopidogrel.md`  
**Cited as:** Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Supporting text from the source:**

> Because the drug depends on being *switched on* by an enzyme, the amount of
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 19 (overlap 40%)

> active metabolite formed is directly tied to how much functional CYP2C19 a
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 20 (overlap 40%)

> CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that
>
> — *CYP2C19_clopidogrel.md*, §What the gene product does, line 5 (overlap 20%)

**What differs:** terms absent from the corpus: produced

**Occurrences (2):** `clopidogrel:IM`, `clopidogrel:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `CLOP-04` · clopidogrel ()

**Claim as generated:**

> Your body's ability to convert clopidogrel into its active form is normal, which allows for the expected degree of platelet inhibition.

**Source consulted:** `CYP2C19_clopidogrel.md`  
**Cited as:** Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Supporting text from the source:**

> expected degree of platelet inhibition.
>
> — *CYP2C19_clopidogrel.md*, §Why altered function changes the outcome, line 34 (overlap 44%)

> The active metabolite then binds irreversibly to the platelet P2Y12
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 15 (overlap 22%)

> active metabolite formed is directly tied to how much functional CYP2C19 a
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 20 (overlap 22%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: allows

**Occurrences (1):** `clopidogrel:NM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `CLOP-05` · clopidogrel ()

**Claim as generated:**

> If the enzyme doesn't work well, less of the active form is produced, and the drug may not work as intended.

<details><summary>Wording variants of this claim (1)</summary>

> If the enzyme is not working properly, less active form is produced, and the drug may not work as intended.

</details>

**Source consulted:** `CYP2C19_clopidogrel.md`  
**Cited as:** Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Supporting text from the source:**

> active metabolite formed is directly tied to how much functional CYP2C19 a
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 20 (overlap 33%)

> CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that
>
> — *CYP2C19_clopidogrel.md*, §What the gene product does, line 5 (overlap 17%)

> reduce, or increase enzyme production.
>
> — *CYP2C19_clopidogrel.md*, §What the gene product does, line 8 (overlap 17%)

**What differs:** terms absent from the corpus: doesn, intended, produced

**Occurrences (2):** `clopidogrel:PM`, `clopidogrel:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `CLOP-06` · clopidogrel ()

**Claim as generated:**

> Your genetic result affects how well this enzyme works, which in turn affects how well the drug works.

<details><summary>Wording variants of this claim (1)</summary>

> Your genetic result affects how much of this active metabolite is formed, which in turn affects how well the drug works.

</details>

**Source consulted:** `CYP2C19_clopidogrel.md`  
**Cited as:** Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Supporting text from the source:**

> CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that
>
> — *CYP2C19_clopidogrel.md*, §What the gene product does, line 5 (overlap 50%)

> reduce, or increase enzyme production.
>
> — *CYP2C19_clopidogrel.md*, §What the gene product does, line 8 (overlap 50%)

> Because the drug depends on being *switched on* by an enzyme, the amount of
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 19 (overlap 50%)

**What differs:** terms absent from the corpus: turn

**Occurrences (2):** `clopidogrel:PM`, `clopidogrel:URM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `CLOP-07` · clopidogrel ()

**Claim as generated:**

> This leads to normal or lower platelet reactivity, which is not associated with a higher risk of bleeding.

**Source consulted:** `CYP2C19_clopidogrel.md`  
**Cited as:** Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Supporting text from the source:**

> notes no association with higher bleeding risk.
>
> — *CYP2C19_clopidogrel.md*, §Why altered function changes the outcome, line 38 (overlap 38%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: associated, leads, lower

**Occurrences (1):** `clopidogrel:RM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `CLOP-08` · clopidogrel ()

**Claim as generated:**

> Your genetic result shows that you have normal or increased function of this enzyme, which means the active form of the medication is formed quickly and effectively.

**Source consulted:** `CYP2C19_clopidogrel.md`  
**Cited as:** Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Supporting text from the source:**

> active metabolite formed is directly tied to how much functional CYP2C19 a
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 20 (overlap 43%)

> - **Increased function** produces more active metabolite.
>
> — *CYP2C19_clopidogrel.md*, §Why altered function changes the outcome, line 36 (overlap 43%)

> - **Normal function** produces the expected amount of active metabolite and the
>
> — *CYP2C19_clopidogrel.md*, §Why altered function changes the outcome, line 33 (overlap 29%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: quickly

**Occurrences (1):** `clopidogrel:RM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `CLOP-09` · clopidogrel ()

**Claim as generated:**

> Increased formation of the active metabolite means the drug works more effectively, while reduced formation means the drug may not work as intended.

**Source consulted:** `CYP2C19_clopidogrel.md`  
**Cited as:** Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Supporting text from the source:**

> - **Increased function** produces more active metabolite.
>
> — *CYP2C19_clopidogrel.md*, §Why altered function changes the outcome, line 36 (overlap 50%)

> into an active thiol metabolite, and CYP2C19 is a major contributor to both
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 14 (overlap 33%)

> The active metabolite then binds irreversibly to the platelet P2Y12
>
> — *CYP2C19_clopidogrel.md*, §How the drug is handled, line 15 (overlap 33%)

**What differs:** terms absent from the corpus: formation, intended

**Occurrences (1):** `clopidogrel:URM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `CODE-01` · codeine ()

**Claim as generated:**

> Codeine is a prodrug that is converted into morphine by the enzyme CYP2D6, which is responsible for metabolizing a large share of commonly used drugs.

**Source consulted:** `CYP2D6_codeine.md`  
**Cited as:** Annotation of CPIC Guideline for codeine and CYP2D6 — Crews KR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2D6, OPRM1, and COMT Genotypes and Select Opioid Therapy. Clin Pharmacol Ther (2021). PMID: 33387367

**Supporting text from the source:**

> CYP2D6 is a hepatic cytochrome P450 enzyme responsible for metabolising a large
>
> — *CYP2D6_codeine.md*, §What the gene product does, line 5 (overlap 33%)

> share of commonly used drugs.
>
> — *CYP2D6_codeine.md*, §What the gene product does, line 6 (overlap 25%)

> Codeine is a **prodrug** with little analgesic activity of its own.
>
> — *CYP2D6_codeine.md*, §How the drug is handled, line 14 (overlap 17%)

**What differs:** terms absent from the corpus: converted, metabolizing

**Occurrences (1):** `codeine:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `CODE-02` · codeine ()

**Claim as generated:**

> The amount of morphine produced depends on how much CYP2D6 activity a person has.

**Source consulted:** `CYP2D6_codeine.md`  
**Cited as:** Annotation of CPIC Guideline for codeine and CYP2D6 — Crews KR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2D6, OPRM1, and COMT Genotypes and Select Opioid Therapy. Clin Pharmacol Ther (2021). PMID: 33387367

**Supporting text from the source:**

> - **Absent or greatly reduced CYP2D6 activity** produces little morphine, so
>
> — *CYP2D6_codeine.md*, §Why altered function changes the outcome, line 24 (overlap 60%)

> Analgesia from codeine therefore depends almost entirely on how much CYP2D6
>
> — *CYP2D6_codeine.md*, §How the drug is handled, line 19 (overlap 40%)

> **PharmCAT cannot call CYP2D6 from an ordinary VCF.** The star alleles depend on
>
> — *CYP2D6_codeine.md*, §A structural note for the explanation layer, line 39 (overlap 40%)

**What differs:** terms absent from the corpus: produced

**Occurrences (1):** `codeine:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `FLUO-02` · fluorouracil ()

**Claim as generated:**

> DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism.

**Source consulted:** `DPYD_fluorouracil.md`  
**Cited as:** Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

**Supporting text from the source:**

> *DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
>
> — *DPYD_fluorouracil.md*, §What the gene product does, line 5 (overlap 82%)

**What differs:** terms absent from the corpus: catabolism, pyrimidine

**Occurrences (1):** `fluorouracil:IM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `FLUO-03` · fluorouracil ()

**Claim as generated:**

> Reduced DPD activity slows inactivation, leading to higher and longer exposure to active drug, which can cause severe toxicity.

**Source consulted:** `DPYD_fluorouracil.md`  
**Cited as:** Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

**Supporting text from the source:**

> - **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
>
> — *DPYD_fluorouracil.md*, §Why altered function changes the outcome, line 24 (overlap 46%)

> to active drug is higher and lasts longer for the same administered amount.
>
> — *DPYD_fluorouracil.md*, §Why altered function changes the outcome, line 25 (overlap 23%)

> - **Normal DPD activity** gives the exposure the drug's standard dosing was
>
> — *DPYD_fluorouracil.md*, §Why altered function changes the outcome, line 34 (overlap 23%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: cause, leading

**Occurrences (1):** `fluorouracil:IM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `FLUO-04` · fluorouracil ()

**Claim as generated:**

> Fluorouracil is a type of chemotherapy that is broken down by an enzyme called dihydropyrimidine dehydrogenase (DPD).

**Source consulted:** `DPYD_fluorouracil.md`  
**Cited as:** Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

**Supporting text from the source:**

> *DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
>
> — *DPYD_fluorouracil.md*, §What the gene product does, line 5 (overlap 44%)

**What differs:** terms absent from the corpus: broken, called, chemotherapy, type

**Occurrences (1):** `fluorouracil:NM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `FLUO-05` · fluorouracil ()

**Claim as generated:**

> If you have normal DPD activity, the standard dose of fluorouracil is likely to be safe.

**Source consulted:** `DPYD_fluorouracil.md`  
**Cited as:** Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

**Supporting text from the source:**

> - **Normal DPD activity** gives the exposure the drug's standard dosing was
>
> — *DPYD_fluorouracil.md*, §Why altered function changes the outcome, line 34 (overlap 50%)

> DPD is expressed widely, with high activity in the
>
> — *DPYD_fluorouracil.md*, §What the gene product does, line 6 (overlap 33%)

> - **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
>
> — *DPYD_fluorouracil.md*, §Why altered function changes the outcome, line 24 (overlap 33%)

**What differs:** terms absent from the corpus: safe

**Occurrences (1):** `fluorouracil:NM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `FLUO-06` · fluorouracil ()

**Claim as generated:**

> Your body's normal DPD activity helps to inactivate most of the drug, which reduces the risk of severe side effects.

**Source consulted:** `DPYD_fluorouracil.md`  
**Cited as:** Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

**Supporting text from the source:**

> DPD is expressed widely, with high activity in the
>
> — *DPYD_fluorouracil.md*, §What the gene product does, line 6 (overlap 25%)

> synthesis in dividing cells; the rest is inactivated by DPD.
>
> — *DPYD_fluorouracil.md*, §How the drug is handled, line 14 (overlap 25%)

> - **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
>
> — *DPYD_fluorouracil.md*, §Why altered function changes the outcome, line 24 (overlap 25%)

**What differs:** terms absent from the corpus: reduces, risk, side

**Occurrences (1):** `fluorouracil:NM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `FLUO-07` · fluorouracil ()

**Claim as generated:**

> If DPD activity is reduced or absent, the drug persists in the body for a longer period, leading to increased exposure and toxicity.

**Source consulted:** `DPYD_fluorouracil.md`  
**Cited as:** Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

**Supporting text from the source:**

> - **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
>
> — *DPYD_fluorouracil.md*, §Why altered function changes the outcome, line 24 (overlap 36%)

> - **Normal DPD activity** gives the exposure the drug's standard dosing was
>
> — *DPYD_fluorouracil.md*, §Why altered function changes the outcome, line 34 (overlap 27%)

> - Frame reduced function as reduced *clearance* and increased *exposure*.
>
> — *DPYD_fluorouracil.md*, §Notes for the explanation layer, line 42 (overlap 27%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: absent, leading, period

**Occurrences (1):** `fluorouracil:PM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `FLUO-08` · fluorouracil ()

**Claim as generated:**

> Fluorouracil is a type of chemotherapy that works by disrupting DNA and RNA synthesis in dividing cells.

**Source consulted:** `DPYD_fluorouracil.md`  
**Cited as:** Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

**Supporting text from the source:**

> dose is converted into the cytotoxic nucleotides that disrupt DNA and RNA
>
> — *DPYD_fluorouracil.md*, §How the drug is handled, line 13 (overlap 33%)

> synthesis in dividing cells; the rest is inactivated by DPD.
>
> — *DPYD_fluorouracil.md*, §How the drug is handled, line 14 (overlap 33%)

**What differs:** terms absent from the corpus: chemotherapy, type

**Occurrences (1):** `fluorouracil:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `SIMV-01` · simvastatin ()

**Claim as generated:**

> Efficient hepatic uptake delivers the drug to its target and keeps systemic exposure low.

**Source consulted:** `SLCO1B1_simvastatin.md`  
**Cited as:** Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405

**Supporting text from the source:**

> Efficient hepatic uptake therefore does two things at once: it delivers the drug
>
> — *SLCO1B1_simvastatin.md*, §How the drug is handled, line 17 (overlap 44%)

> to its target, and it keeps systemic — particularly skeletal muscle — exposure
>
> — *SLCO1B1_simvastatin.md*, §How the drug is handled, line 18 (overlap 44%)

> - **Normal function** gives typical hepatic uptake, typical systemic exposure,
>
> — *SLCO1B1_simvastatin.md*, §Why altered function changes the outcome, line 29 (overlap 44%)

**What differs:** terms absent from the corpus: low

**Occurrences (2):** `simvastatin:IM`, `simvastatin:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `SIMV-02` · simvastatin ()

**Claim as generated:**

> Reduced OATP1B1 function means less of each dose is taken up by the liver, leading to higher systemic exposure and muscle toxicity.

**Source consulted:** `SLCO1B1_simvastatin.md`  
**Cited as:** Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405

**Supporting text from the source:**

> - **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
>
> — *SLCO1B1_simvastatin.md*, §Why altered function changes the outcome, line 23 (overlap 45%)

> to its target, and it keeps systemic — particularly skeletal muscle — exposure
>
> — *SLCO1B1_simvastatin.md*, §How the drug is handled, line 18 (overlap 27%)

> Higher systemic exposure is associated with
>
> — *SLCO1B1_simvastatin.md*, §Why altered function changes the outcome, line 24 (overlap 27%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: leading

**Occurrences (1):** `simvastatin:IM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `SIMV-04` · simvastatin ()

**Claim as generated:**

> Simvastatin is a statin that works by inhibiting an enzyme inside liver cells.

**Source consulted:** `SLCO1B1_simvastatin.md`  
**Cited as:** Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405

**Supporting text from the source:**

> Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
>
> — *SLCO1B1_simvastatin.md*, §How the drug is handled, line 13 (overlap 43%)

> membrane of liver cells.
>
> — *SLCO1B1_simvastatin.md*, §What the gene product does, line 6 (overlap 29%)

> step that concentrates the drug (chiefly its active acid form) into liver cells.
>
> — *SLCO1B1_simvastatin.md*, §How the drug is handled, line 15 (overlap 29%)

**What differs:** terms absent from the corpus: inhibiting

**Occurrences (1):** `simvastatin:NM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `SIMV-05` · simvastatin ()

**Claim as generated:**

> The liver's ability to take up simvastatin is important for keeping systemic exposure low and reducing the risk of muscle toxicity.

**Source consulted:** `SLCO1B1_simvastatin.md`  
**Cited as:** Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405

**Supporting text from the source:**

> to its target, and it keeps systemic — particularly skeletal muscle — exposure
>
> — *SLCO1B1_simvastatin.md*, §How the drug is handled, line 18 (overlap 27%)

> Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
>
> — *SLCO1B1_simvastatin.md*, §How the drug is handled, line 13 (overlap 18%)

> Higher systemic exposure is associated with
>
> — *SLCO1B1_simvastatin.md*, §Why altered function changes the outcome, line 24 (overlap 18%)

**What differs:** terms absent from the corpus: important, keeping, low, reducing

**Occurrences (1):** `simvastatin:NM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `SIMV-06` · simvastatin ()

**Claim as generated:**

> Your genetic result does not affect the liver's ability to take up simvastatin, so the typical risk of muscle toxicity remains.

**Source consulted:** `SLCO1B1_simvastatin.md`  
**Cited as:** Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405

**Supporting text from the source:**

> Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
>
> — *SLCO1B1_simvastatin.md*, §How the drug is handled, line 13 (overlap 29%)

> The concern is **muscle toxicity**, driven by drug that failed
>
> — *SLCO1B1_simvastatin.md*, §Why altered function changes the outcome, line 26 (overlap 29%)

**What differs:** terms absent from the corpus: remains

**Occurrences (1):** `simvastatin:NM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `SIMV-07` · simvastatin ()

**Claim as generated:**

> The OATP1B1 transporter, which helps remove simvastatin from the bloodstream into the liver, is not functioning properly in your body.

**Source consulted:** `SLCO1B1_simvastatin.md`  
**Cited as:** Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405

**Supporting text from the source:**

> - **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
>
> — *SLCO1B1_simvastatin.md*, §Why altered function changes the outcome, line 23 (overlap 43%)

> *SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing)
>
> — *SLCO1B1_simvastatin.md*, §What the gene product does, line 5 (overlap 29%)

> Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
>
> — *SLCO1B1_simvastatin.md*, §How the drug is handled, line 13 (overlap 29%)

**What differs:** terms absent from the corpus: bloodstream

**Occurrences (1):** `simvastatin:PM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `SIMV-08` · simvastatin ()

**Claim as generated:**

> This leads to higher levels of simvastatin in the bloodstream, which can cause muscle toxicity.

**Source consulted:** `SLCO1B1_simvastatin.md`  
**Cited as:** Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405

**Supporting text from the source:**

> The concern is **muscle toxicity**, driven by drug that failed
>
> — *SLCO1B1_simvastatin.md*, §Why altered function changes the outcome, line 26 (overlap 29%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: bloodstream, cause, leads

**Occurrences (1):** `simvastatin:PM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `WARF-01` · warfarin ()

**Claim as generated:**

> Reduced function of this enzyme can lead to slower clearance of warfarin, resulting in higher exposure and a stronger anticoagulant effect.

**Source consulted:** `CYP2C9_warfarin.md`  
**Cited as:** Annotation of CPIC Guideline for warfarin and CYP2C9, CYP4F2, VKORC1 — Johnson JA et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Pharmacogenetics-Guided Warfarin Dosing: 2017 Update. Clin Pharmacol Ther (2017). PMID: 28198005

**Supporting text from the source:**

> - **Reduced CYP2C9 function** slows S-warfarin clearance, so the same
>
> — *CYP2C9_warfarin.md*, §Why altered function changes the outcome, line 23 (overlap 31%)

> administered amount produces higher steady-state exposure and a stronger
>
> — *CYP2C9_warfarin.md*, §Why altered function changes the outcome, line 24 (overlap 23%)

> principal route of clearance for S-warfarin, the more pharmacologically potent
>
> — *CYP2C9_warfarin.md*, §What the gene product does, line 6 (overlap 15%)

**What differs:** states a causal link the matched passages do not; terms absent from the corpus: anticoagulant, lead, resulting, slower

**Occurrences (1):** `warfarin:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `WARF-02` · warfarin ()

**Claim as generated:**

> Warfarin is metabolized by the liver enzyme CYP2C9.

**Source consulted:** `CYP2C9_warfarin.md`  
**Cited as:** Annotation of CPIC Guideline for warfarin and CYP2C9, CYP4F2, VKORC1 — Johnson JA et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Pharmacogenetics-Guided Warfarin Dosing: 2017 Update. Clin Pharmacol Ther (2017). PMID: 28198005

**Supporting text from the source:**

> CYP2C9 is a hepatic cytochrome P450 enzyme.
>
> — *CYP2C9_warfarin.md*, §What the gene product does, line 5 (overlap 40%)

> - **Reduced CYP2C9 function** slows S-warfarin clearance, so the same
>
> — *CYP2C9_warfarin.md*, §Why altered function changes the outcome, line 23 (overlap 40%)

> principal route of clearance for S-warfarin, the more pharmacologically potent
>
> — *CYP2C9_warfarin.md*, §What the gene product does, line 6 (overlap 20%)

**What differs:** terms absent from the corpus: liver, metabolized

**Occurrences (1):** `warfarin:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

# TIER 3 — source found; claim differs only in wording

## `AZAT-04` · azathioprine ()

**Claim as generated:**

> Azathioprine is a prodrug that is converted into active metabolites, which are then incorporated into DNA.

**Source consulted:** `TPMT_azathioprine.md`  
**Cited as:** Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934

**Supporting text from the source:**

> thioguanine nucleotides, limiting how much active metabolite is incorporated
>
> — *TPMT_azathioprine.md*, §What the gene products do, line 10 (overlap 43%)

> Azathioprine is a prodrug that is converted to mercaptopurine and then, through
>
> — *TPMT_azathioprine.md*, §How the drug is handled, line 16 (overlap 43%)

> they are incorporated into DNA, and that incorporation produces both the
>
> — *TPMT_azathioprine.md*, §How the drug is handled, line 18 (overlap 29%)

**What differs:** wording differs; every domain term appears in the cited corpus

**Occurrences (1):** `azathioprine:NM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `FLUO-01` · fluorouracil ()

**Claim as generated:**

> DPD is responsible for breaking down fluorouracil into inactive metabolites.

<details><summary>Wording variants of this claim (1)</summary>

> The enzyme dihydropyrimidine dehydrogenase (DPD) is responsible for breaking down fluorouracil into inactive metabolites.

</details>

**Source consulted:** `DPYD_fluorouracil.md`  
**Cited as:** Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

**Supporting text from the source:**

> liver, and is responsible for breaking down the great majority of an
>
> — *DPYD_fluorouracil.md*, §What the gene product does, line 7 (overlap 33%)

> administered fluoropyrimidine dose into inactive metabolites.
>
> — *DPYD_fluorouracil.md*, §What the gene product does, line 8 (overlap 33%)

> *DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
>
> — *DPYD_fluorouracil.md*, §What the gene product does, line 5 (overlap 17%)

**What differs:** wording differs; every domain term appears in the cited corpus

**Occurrences (2):** `fluorouracil:IM`, `fluorouracil:PM`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `FLUO-10` · fluorouracil ()

**Claim as generated:**

> The enzyme dihydropyrimidine dehydrogenase (DPD) is responsible for breaking down most of the drug into inactive metabolites.

**Source consulted:** `DPYD_fluorouracil.md`  
**Cited as:** Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

**Supporting text from the source:**

> *DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
>
> — *DPYD_fluorouracil.md*, §What the gene product does, line 5 (overlap 50%)

> liver, and is responsible for breaking down the great majority of an
>
> — *DPYD_fluorouracil.md*, §What the gene product does, line 7 (overlap 25%)

> administered fluoropyrimidine dose into inactive metabolites.
>
> — *DPYD_fluorouracil.md*, §What the gene product does, line 8 (overlap 25%)

**What differs:** wording differs; every domain term appears in the cited corpus

**Occurrences (1):** `fluorouracil:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `SIMV-03` · simvastatin ()

**Claim as generated:**

> SLCO1B1 encodes OATP1B1, a hepatic uptake transporter that moves drugs out of portal blood and into liver cells.

**Source consulted:** `SLCO1B1_simvastatin.md`  
**Cited as:** Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405

**Supporting text from the source:**

> *SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing)
>
> — *SLCO1B1_simvastatin.md*, §What the gene product does, line 5 (overlap 55%)

> - Describe OATP1B1 as a hepatic uptake transporter; avoid calling it a
>
> — *SLCO1B1_simvastatin.md*, §Notes for the explanation layer, line 38 (overlap 36%)

> Its job is to move drugs out of portal blood and into
>
> — *SLCO1B1_simvastatin.md*, §What the gene product does, line 6 (overlap 27%)

**What differs:** wording differs; every domain term appears in the cited corpus

**Occurrences (2):** `simvastatin:IM`, `simvastatin:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## `SIMV-09` · simvastatin ()

**Claim as generated:**

> Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both its site of action and its route of elimination.

**Source consulted:** `SLCO1B1_simvastatin.md`  
**Cited as:** Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405

**Supporting text from the source:**

> Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
>
> — *SLCO1B1_simvastatin.md*, §How the drug is handled, line 13 (overlap 69%)

> its site of action and its route of elimination.
>
> — *SLCO1B1_simvastatin.md*, §How the drug is handled, line 14 (overlap 31%)

**What differs:** wording differs; every domain term appears in the cited corpus

**Occurrences (1):** `simvastatin:Unknown`

**Decision:** ☐ accept ☐ reject ☐ edit —

**Reasoning:** 

---

## What this worksheet is not

It is not a review. It locates source text; it does not judge adequacy.
Recording a decision is a separate, deliberate act performed by a named
person, and nothing in this file has been written to the explanation
store.

**No clinical expert has reviewed any of this.** This project has none.
Adjudication here is the project author checking prose against its cited
source — a narrower claim, and never described as more.

