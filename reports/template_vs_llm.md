# Template vs LLM — all 20 shipped cases

**Generated:** 2026-07-24 (after the field-authorship split)  
**Template:** deterministic composition (archived)  
**LLM:** `meta/llama-3.1-8b-instruct`, genotype-agnostic prose

## Field authorship

| Field | Author |
| --- | --- |
| `clinical_recommendation` | verbatim CPIC via PharmCAT |
| `variant_rationale` | **composed by code** from the request's own profile |
| `summary`, `mechanism`, `patient_friendly` | LLM, genotype-agnostic |

| | Template | LLM |
| --- | ---: | ---: |
| Mean words per entry | 158 | 150 |

**Readability.** The template uses fixed frames, so every entry has the same
rhythm and reads as a form letter. The LLM varies structure per case and renders
terms of art into ordinary words.

**The split changed the failure mode.** The model no longer writes any factual
genotype statement, so it cannot omit or invent one — `variant_rationale` is
code-composed from the profile in the same response. Before the split, 10 of 14
entries had no diplotype slot at all.

---

## `azathioprine:IM` — Safe

> **CPIC (verbatim):** Initiate therapy with reduced starting doses (30-80% of standard starting dose) if standard starting dose is ≥2 mg/kg/day. If starting dose is already below standard starting dose, dose reduction might not be necessary. During therapy, adjust the doses of azathioprine based on the degree of myelosuppression and disease-specific guidelines. It usually takes at least 2-4 weeks of stable dosing to reach steady state after each dose adjustment.

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result may affect how well you tolerate azathioprine. You are an Intermediate Metabolizer, which means you may have a moderate to high risk of experiencing myelosuppression, a condition that can cause low blood cell counts. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| TPMT encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates thiopurine compounds and so diverts them away from the pathway that produces active metabolites.

Source: Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934 | Azathioprine is a medication that works by producing active metabolites that can affect the immune system. However, your genetic result may affect how well your body breaks down these active metabolites. If your body breaks them down too slowly, it can lead to a buildup of toxic levels, causing myelosuppression. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called TPMT as {diplotype}, which corresponds to a Intermediate Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results do not suggest a change to how this medicine is usually prescribed. Your {gene} gene result shows somewhat lower activity than most people, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | If you're taking azathioprine, your doctor may need to start you on a lower dose to help your body handle the medication. They will also need to monitor your blood cell counts closely to make sure you're not experiencing any side effects. It may take a few weeks for your body to adjust to the new dose, so be patient and work closely with your doctor to find the right balance. |

---

## `azathioprine:NM` — Safe

> **CPIC (verbatim):** Initiate therapy with standard starting dose (e.g., 2 mg/kg/day for autoimmune diseases). During therapy, adjust doses of azathioprine based on disease-specific guidelines. It usually takes at least 2 weeks to reach steady state after each dose adjustment.

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result indicates that you are a normal metabolizer of azathioprine, which means you are at safe risk for thiopurine-related side effects such as leukopenia, neutropenia, and myelosuppression. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| TPMT encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates thiopurine compounds and so diverts them away from the pathway that produces active metabolites.

Source: Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934 | Azathioprine is a prodrug that is converted into active metabolites, which are then incorporated into DNA. Your genetic result indicates that you have normal function in the enzymes that handle this process, which means that you are not at increased risk for the side effects associated with this drug. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called NUDT15 as {diplotype}, which corresponds to a Normal Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results do not suggest a change to how this medicine is usually prescribed. Your {gene} gene result shows activity in the usual range, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | You are at safe risk for the side effects of azathioprine, such as low white blood cell count and anemia. This is because your body handles the medication in a normal way. However, it's always best to speak with your doctor or pharmacist to confirm this information and get personalized advice. |

---

## `azathioprine:PM` — Toxic

> **CPIC (verbatim):** Consider alternative nonthiopurine immunosuppressant therapy.

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result affects how you metabolize a certain type of medication, which can increase the risk of serious side effects. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| TPMT encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates thiopurine compounds and so diverts them away from the pathway that produces active metabolites.

Source: Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934 | The medication is converted into an active form that can affect the bone marrow, leading to a decrease in white blood cells. Your genetic result removes a brake on this process, allowing more of the active form to accumulate and increase the risk of serious side effects. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called TPMT as {diplotype}, which corresponds to a Poor Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results suggest a higher chance of harmful effects from this medicine. Your {gene} gene result shows much lower activity than most people, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | If you have this genetic result, it's best to talk to your doctor or pharmacist about using a different medication that doesn't have the same risk of serious side effects. They can help you find a safer option that works for you. |

---

## `azathioprine:Unknown` — Unknown

> **CPIC (verbatim):** _(none)_

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result has not been determined for the gene involved in how your body handles a certain medication. This means we cannot provide a specific recommendation for how to use this medication safely. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| TPMT encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates thiopurine compounds and so diverts them away from the pathway that produces active metabolites.

Source: Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934 | This medication is converted into active compounds in your body, which can affect your bone marrow and cause low white blood cell counts. Normally, certain enzymes help control the amount of these active compounds. If these enzymes are not working properly, more of the active compounds can build up and cause problems. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| No genotype was called for {drug} in this analysis, so there is no variant-level rationale to report. | No genotype was called for azathioprine in this analysis, so there is no variant-level rationale to report. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| This tool could not reach a conclusion about this medicine for you. That is not a reassuring result or a worrying one — it means this tool has nothing to say, and the question is still open. Discuss this with your doctor or pharmacist before making any change to your medicines. | We don't have enough information about how your body handles this medication. This means we can't give you specific advice on how to use it safely. It's always best to talk to your doctor or pharmacist about any concerns you have about your medication. |

---

## `clopidogrel:IM` — Ineffective

> **CPIC (verbatim):** Avoid standard dose (75 mg) clopidogrel if possible. Use prasugrel or ticagrelor at standard dose if no contraindication.

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result affects how well you respond to clopidogrel. It's recommended to avoid the standard dose of clopidogrel if possible. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide range of drug substrates. Its activity varies substantially between people because the CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme production.

Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351 | Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme. The amount of active form produced depends on how well this enzyme is working. If the enzyme is not working well, less active form is produced, leading to weaker platelet inhibition. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Intermediate Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results suggest this medicine may not work as well for you as intended. Your {gene} gene result shows somewhat lower activity than most people, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | If you have a certain genetic result, clopidogrel might not work as well as it should. This is because your body doesn't make enough of the active form of the medicine. Your doctor or pharmacist can help you find a different medicine that works better for you. |

---

## `clopidogrel:NM` — Safe

> **CPIC (verbatim):** If considering clopidogrel, use at standard dose (75 mg/day)

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result suggests that you are a normal metabolizer of clopidogrel, which means that you can take the standard dose without concern. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide range of drug substrates. Its activity varies substantially between people because the CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme production.

Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351 | Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme. Your body's ability to convert clopidogrel into its active form is normal, which allows for the expected degree of platelet inhibition. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Normal Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results do not suggest a change to how this medicine is usually prescribed. Your {gene} gene result shows activity in the usual range, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | This means that you can take the standard dose of clopidogrel without worrying about it not working properly. However, it's always best to speak with your doctor or pharmacist to confirm the right dose for you. |

---

## `clopidogrel:PM` — Ineffective

> **CPIC (verbatim):** Avoid clopidogrel if possible. Use prasugrel or ticagrelor at standard dose if no contraindication.

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result affects how well you respond to clopidogrel. People with this result are at increased risk for the drug not working as intended, which can lead to serious cardiac and cerebrovascular events. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide range of drug substrates. Its activity varies substantially between people because the CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme production.

Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351 | Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme. Your genetic result affects how well this enzyme works, which in turn affects how well the drug works. If the enzyme doesn't work well, less of the active form is produced, and the drug may not work as intended. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Poor Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results suggest this medicine may not work as well for you as intended. Your {gene} gene result shows much lower activity than most people, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | If you have this result, it's best to avoid clopidogrel if possible. If you can't avoid it, your doctor may recommend a different medication, such as prasugrel or ticagrelor, at the standard dose. Always talk to your doctor or pharmacist about your specific situation and any concerns you may have. |

---

## `clopidogrel:RM` — Safe

> **CPIC (verbatim):** If considering clopidogrel, use at standard dose (75 mg/day)

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result indicates you are a rapid metabolizer of clopidogrel, meaning your body processes the medication quickly and effectively. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide range of drug substrates. Its activity varies substantially between people because the CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme production.

Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351 | Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme to work. Your genetic result shows that you have normal or increased function of this enzyme, which means the active form of the medication is formed quickly and effectively. This leads to normal or lower platelet reactivity, which is not associated with a higher risk of bleeding. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Rapid Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results do not suggest a change to how this medicine is usually prescribed. Your {gene} gene result shows somewhat higher activity than most people, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | If you're considering taking clopidogrel, you can take it at the standard dose. This is because your body is good at breaking down the medication and making it work. However, it's always best to speak with your doctor or pharmacist to confirm the right dosage for you. |

---

## `clopidogrel:URM` — Safe

> **CPIC (verbatim):** If considering clopidogrel, use at standard dose (75 mg/day)

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Based on your genetic result, the recommended dose for clopidogrel is at standard dose (75 mg/day). |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide range of drug substrates. Its activity varies substantially between people because the CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme production.

Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351 | Clopidogrel is a prodrug that needs to be converted into an active metabolite by an enzyme to work. Your genetic result affects how much of this active metabolite is formed, which in turn affects how well the drug works. Increased formation of the active metabolite means the drug works more effectively, while reduced formation means the drug may not work as intended. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Ultrarapid Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results do not suggest a change to how this medicine is usually prescribed. Your {gene} gene result shows much higher activity than most people, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | Your genetic result shows that you are a safe candidate for taking clopidogrel. However, to make sure the drug works properly, it's recommended to take it at the standard dose. This means you should talk to your doctor or pharmacist about the best way to take clopidogrel based on your individual needs. |

---

## `clopidogrel:Unknown` — Unknown

> **CPIC (verbatim):** _(none)_

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result does not provide enough information to determine how you metabolize clopidogrel. Therefore, the CPIC recommendation is unknown. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide range of drug substrates. Its activity varies substantially between people because the CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme production.

Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351 | Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme. The amount of active form produced depends on how much functional enzyme a person has. If the enzyme is not working properly, less active form is produced, and the drug may not work as intended. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| No genotype was called for {drug} in this analysis, so there is no variant-level rationale to report. | No genotype was called for clopidogrel in this analysis, so there is no variant-level rationale to report. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| This tool could not reach a conclusion about this medicine for you. That is not a reassuring result or a worrying one — it means this tool has nothing to say, and the question is still open. Discuss this with your doctor or pharmacist before making any change to your medicines. | We don't have enough information about how your body processes clopidogrel to give a specific recommendation. This means we can't say for sure how well the drug will work for you. It's always a good idea to talk to your doctor or pharmacist about your specific situation and any concerns you may have. |

---

## `codeine:Unknown` — Unknown

> **CPIC (verbatim):** _(none)_

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result for codeine is unknown, so we cannot explain how it will be handled by your body. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| CYP2D6 is a hepatic cytochrome P450 enzyme responsible for metabolising a large share of commonly used drugs. CYP2D6 is unusually variable: as well as single-nucleotide variants that alter or abolish activity, the gene is subject to **whole-gene deletions and duplications**, so copy number differs between people. Activity is conventionally summarised as an activity score derived from both alleles.

Source: Annotation of CPIC Guideline for codeine and CYP2D6 — Crews KR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2D6, OPRM1, and COMT Genotypes and Select Opioid Therapy. Clin Pharmacol Ther (2021). PMID: 33387367 | Codeine is a prodrug that is converted into morphine by the enzyme CYP2D6, which is responsible for metabolizing a large share of commonly used drugs. The amount of morphine produced depends on how much CYP2D6 activity a person has. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| No genotype was called for {drug} in this analysis, so there is no variant-level rationale to report. | No genotype was called for codeine in this analysis, so there is no variant-level rationale to report. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| This tool could not reach a conclusion about this medicine for you. That is not a reassuring result or a worrying one — it means this tool has nothing to say, and the question is still open. Discuss this with your doctor or pharmacist before making any change to your medicines. | We don't know how your body will handle codeine because we can't determine how active the enzyme that breaks it down is in your body. This enzyme, CYP2D6, helps turn codeine into a different medicine that actually helps with pain. If you're taking codeine, it's best to speak with your doctor or pharmacist to understand how it will affect you. |

---

## `fluorouracil:IM` — Adjust Dosage

> **CPIC (verbatim):** Reduce starting dose by 50% followed by titration of dose based on toxicity or therapeutic drug monitoring (if available). Patients with the c.2846A&gt;T/c.2846A&gt;T genotype may require &gt;50% reduction in starting dose.

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result indicates that you are an Intermediate Metabolizer of fluorouracil. This means that you may be at increased risk for severe or even fatal drug toxicity when treated with this medication. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism. DPD is expressed widely, with high activity in the liver, and is responsible for breaking down the great majority of an administered fluoropyrimidine dose into inactive metabolites.

Source: Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729 | DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism. DPD is responsible for breaking down fluorouracil into inactive metabolites. Reduced DPD activity slows inactivation, leading to higher and longer exposure to active drug, which can cause severe toxicity. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called DPYD as {diplotype}, which corresponds to a Intermediate Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results suggest this medicine may need to be prescribed differently from the usual approach. Your {gene} gene result shows somewhat lower activity than most people, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | If you're taking fluorouracil, your doctor may need to adjust your dosage based on your genetic result. This is because your body may not be able to break down the medication as well as others. Your doctor will work with you to find the right dose to minimize the risk of side effects. |

---

## `fluorouracil:NM` — Safe

> **CPIC (verbatim):** Based on genotype, there is no indication to change dose or therapy. Use label-recommended dosage and administration.

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Based on your genetic result, there is no indication to change the dose or therapy for fluorouracil. Use the label-recommended dosage and administration. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism. DPD is expressed widely, with high activity in the liver, and is responsible for breaking down the great majority of an administered fluoropyrimidine dose into inactive metabolites.

Source: Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729 | Fluorouracil is a type of chemotherapy that is broken down by an enzyme called dihydropyrimidine dehydrogenase (DPD). Your body's normal DPD activity helps to inactivate most of the drug, which reduces the risk of severe side effects. If you have normal DPD activity, the standard dose of fluorouracil is likely to be safe. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called DPYD as {diplotype}, which corresponds to a Normal Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results do not suggest a change to how this medicine is usually prescribed. Your {gene} gene result shows activity in the usual range, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | Your genetic result shows that you are a normal metabolizer of fluorouracil. This means that your body is able to break down the drug in a normal way, which reduces the risk of severe side effects. You should be able to take the standard dose of fluorouracil without any problems. However, it's always best to speak with your doctor or pharmacist to confirm the best course of treatment for you. |

---

## `fluorouracil:PM` — Toxic

> **CPIC (verbatim):** Avoid use of 5-fluorouracil or 5-fluorouracil prodrug-based regimens.

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result indicates that you are at a higher risk for severe or even fatal drug toxicity when treated with fluoropyrimidine drugs, such as fluorouracil. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism. DPD is expressed widely, with high activity in the liver, and is responsible for breaking down the great majority of an administered fluoropyrimidine dose into inactive metabolites.

Source: Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729 | The enzyme dihydropyrimidine dehydrogenase (DPD) is responsible for breaking down fluorouracil into inactive metabolites. If DPD activity is reduced or absent, the drug persists in the body for a longer period, leading to increased exposure and toxicity. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called DPYD as {diplotype}, which corresponds to a Poor Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results suggest a higher chance of harmful effects from this medicine. Your {gene} gene result shows much lower activity than most people, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | If you have a genetic result that shows you're at risk for severe side effects from certain cancer medications, it's best to talk to your doctor or pharmacist about alternative treatment options. They can help you make an informed decision about your care. |

---

## `fluorouracil:Unknown` — Unknown

> **CPIC (verbatim):** _(none)_

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | The mechanism behind how your genetic result affects fluorouracil is related to how the body breaks down the drug. Fluorouracil is inactivated by an enzyme called dihydropyrimidine dehydrogenase (DPD). If this enzyme is not working properly, the drug can build up in the body and cause more severe side effects. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism. DPD is expressed widely, with high activity in the liver, and is responsible for breaking down the great majority of an administered fluoropyrimidine dose into inactive metabolites.

Source: Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729 | Fluorouracil is a type of chemotherapy that works by disrupting DNA and RNA synthesis in dividing cells. The enzyme dihydropyrimidine dehydrogenase (DPD) is responsible for breaking down most of the drug into inactive metabolites. If DPD is not working properly, the drug can persist in the body for longer and cause more severe side effects. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| No genotype was called for {drug} in this analysis, so there is no variant-level rationale to report. | No genotype was called for fluorouracil in this analysis, so there is no variant-level rationale to report. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| This tool could not reach a conclusion about this medicine for you. That is not a reassuring result or a worrying one — it means this tool has nothing to say, and the question is still open. Discuss this with your doctor or pharmacist before making any change to your medicines. | If you have a problem with the way your body breaks down fluorouracil, you may experience more severe side effects. This is because the drug can build up in your body and cause problems. It's always best to speak with your doctor or pharmacist about any concerns you have about your medication. |

---

## `simvastatin:IM` — Adjust Dosage

> **CPIC (verbatim):** Prescribe an alternative statin depending on the desired potency (see Figure 1 of PMID: 35152405 for recommendations for alternative statins). If simvastatin therapy is warranted, limit dose to &lt;20mg/day.

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result affects how your body handles simvastatin, a type of statin medication. This can increase your risk of muscle toxicity. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| SLCO1B1 encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing) membrane of liver cells. Its job is to move drugs out of portal blood and into hepatocytes. It is a **transporter, not a metabolising enzyme**, which is why its phenotypes are described as function categories (normal, decreased, poor function) rather than metaboliser categories.

Source: Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405 | SLCO1B1 encodes OATP1B1, a hepatic uptake transporter that moves drugs out of portal blood and into liver cells. Efficient hepatic uptake delivers the drug to its target and keeps systemic exposure low. Reduced OATP1B1 function means less of each dose is taken up by the liver, leading to higher systemic exposure and muscle toxicity. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Decreased Function result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results suggest this medicine may need to be prescribed differently from the usual approach. Your {gene} gene result shows somewhat lower activity than most people, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | If you have this genetic result, your doctor may want to prescribe a different statin or limit the dose of simvastatin to less than 20mg per day. This is because your body may not be able to remove simvastatin from the circulation into the liver as efficiently as usual. This can increase your risk of muscle problems. Be sure to talk to your doctor or pharmacist about your genetic result and how it may affect your medication. |

---

## `simvastatin:NM` — Safe

> **CPIC (verbatim):** Prescribe desired starting dose and adjust doses based on disease-specific guidelines.

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result does not affect the typical risk of muscle toxicity from simvastatin. You can be prescribed the desired starting dose and adjust doses based on disease-specific guidelines. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| SLCO1B1 encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing) membrane of liver cells. Its job is to move drugs out of portal blood and into hepatocytes. It is a **transporter, not a metabolising enzyme**, which is why its phenotypes are described as function categories (normal, decreased, poor function) rather than metaboliser categories.

Source: Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405 | Simvastatin is a statin that works by inhibiting an enzyme inside liver cells. The liver's ability to take up simvastatin is important for keeping systemic exposure low and reducing the risk of muscle toxicity. Your genetic result does not affect the liver's ability to take up simvastatin, so the typical risk of muscle toxicity remains. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Normal Function result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results do not suggest a change to how this medicine is usually prescribed. Your {gene} gene result shows activity in the usual range, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | You don't have a genetic variation that affects how your body handles simvastatin. This means you can take the usual dose and adjust it based on your disease and how you're responding to the medication. It's always a good idea to talk to your doctor or pharmacist about your specific situation and any concerns you may have. |

---

## `simvastatin:PM` — Adjust Dosage

> **CPIC (verbatim):** Prescribe an alternative statin depending on the desired potency (see Figure 1 of PMID: 35152405 for recommendations for alternative statins).

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result suggests that you may be at increased risk for muscle toxicity when taking simvastatin. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| SLCO1B1 encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing) membrane of liver cells. Its job is to move drugs out of portal blood and into hepatocytes. It is a **transporter, not a metabolising enzyme**, which is why its phenotypes are described as function categories (normal, decreased, poor function) rather than metaboliser categories.

Source: Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405 | The OATP1B1 transporter, which helps remove simvastatin from the bloodstream into the liver, is not functioning properly in your body. This leads to higher levels of simvastatin in the bloodstream, which can cause muscle toxicity. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The non-reference positions supporting this call were {detected_variants}. | PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Poor Function result. The non-reference positions supporting this call were no non-reference variants were detected. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| Your genetic results suggest this medicine may need to be prescribed differently from the usual approach. Your {gene} gene result shows much lower activity than most people, which is what this medicine's handling depends on. The clinical recommendation shown with this result comes from published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist before making any change to your medicines. | Your doctor may want to consider a different type of statin that is safer for you to take. This is because your body is not able to remove simvastatin from the bloodstream as well as it should be, which can cause muscle problems. It's always best to talk to your doctor or pharmacist about any concerns you have about your medication. |

---

## `simvastatin:Unknown` — Unknown

> **CPIC (verbatim):** _(none)_

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | The recommendation for your genetic result and simvastatin is unknown because your genetic result was not available for this gene. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| SLCO1B1 encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing) membrane of liver cells. Its job is to move drugs out of portal blood and into hepatocytes. It is a **transporter, not a metabolising enzyme**, which is why its phenotypes are described as function categories (normal, decreased, poor function) rather than metaboliser categories.

Source: Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405 | SLCO1B1 encodes OATP1B1, a hepatic uptake transporter that moves drugs out of portal blood and into liver cells. Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both its site of action and its route of elimination. Efficient hepatic uptake delivers the drug to its target and keeps systemic exposure low. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| No genotype was called for {drug} in this analysis, so there is no variant-level rationale to report. | No genotype was called for simvastatin in this analysis, so there is no variant-level rationale to report. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| This tool could not reach a conclusion about this medicine for you. That is not a reassuring result or a worrying one — it means this tool has nothing to say, and the question is still open. Discuss this with your doctor or pharmacist before making any change to your medicines. | We don't have enough information about your genetic result to make a recommendation about taking simvastatin. This is because your genetic result was not available for this gene. Simvastatin works by being taken up by the liver, which helps keep systemic exposure low. If the liver doesn't take up the drug well, more of it stays in the bloodstream and can cause muscle problems. To understand your risk, you should speak with your doctor or pharmacist. |

---

## `warfarin:Unknown` — Unknown

> **CPIC (verbatim):** _(none)_

**summary**

| Template | LLM/composed |
| --- | --- |
| {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}. | Your genetic result does not provide enough information to make a recommendation for warfarin dosing. |

**mechanism**

| Template | LLM/composed |
| --- | --- |
| CYP2C9 is a hepatic cytochrome P450 enzyme. Among many substrates, it is the principal route of clearance for S-warfarin, the more pharmacologically potent of warfarin's two enantiomers.

Source: Annotation of CPIC Guideline for warfarin and CYP2C9, CYP4F2, VKORC1 — Johnson JA et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Pharmacogenetics-Guided Warfarin Dosing: 2017 Update. Clin Pharmacol Ther (2017). PMID: 28198005 | Warfarin is metabolized by the liver enzyme CYP2C9. Reduced function of this enzyme can lead to slower clearance of warfarin, resulting in higher exposure and a stronger anticoagulant effect. |

**variant_rationale** _(code-composed)_

| Template | LLM/composed |
| --- | --- |
| No genotype was called for {drug} in this analysis, so there is no variant-level rationale to report. | No genotype was called for warfarin in this analysis, so there is no variant-level rationale to report. |

**patient_friendly**

| Template | LLM/composed |
| --- | --- |
| This tool could not reach a conclusion about this medicine for you. That is not a reassuring result or a worrying one — it means this tool has nothing to say, and the question is still open. Discuss this with your doctor or pharmacist before making any change to your medicines. | We don't have enough information about your genetic result to give you specific advice about taking warfarin. Warfarin is a medication that helps prevent blood clots, but it can also cause bleeding. If you're taking warfarin, it's essential to work closely with your doctor or pharmacist to monitor your treatment and adjust your dose as needed. |

---

