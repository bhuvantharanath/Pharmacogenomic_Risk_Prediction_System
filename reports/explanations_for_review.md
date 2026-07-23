# PharmaGuard — explanations for review

**Exported:** 2026-07-23 14:20 UTC  
**Model:** ``  
**Entries:** 20 (0 template fallback, 0 already reviewed)

---

## What you are being asked to check

Each explanation below is printed **next to the CPIC text it was
generated from**. For each one, please judge:

1. **Faithfulness** — does the explanation follow from the CPIC text
   above it, without adding anything?
2. **Direction of effect** — this is the one a machine cannot check.
   The automated guard verifies that every drug, gene, dose and allele
   mentioned appears in the source. It **cannot** tell that a mechanism
   has been described backwards. "Reduced enzyme activity causes the
   drug to accumulate" is fully grounded and completely wrong for a
   prodrug like clopidogrel, where reduced activity means *less* active
   drug. Please check each mechanism points the right way.
3. **Plain language** — is `Patient-friendly` genuinely readable by a
   non-specialist, without being alarming or falsely reassuring?
4. **Honest gaps** — where no result was obtained (CYP2D6, warfarin),
   does the text say so plainly rather than implying a normal result?

### About the placeholders

`{diplotype}` and `{detected_variants}` are **intentional**. Each
explanation is reused for every patient with that phenotype, and those
values are substituted per patient at request time (then cross-checked
against the actual genotype call). Please do not replace them with
specific values.

### Recording your decision

Sign the block under each entry, or return the document with comments.
Decisions are transcribed with:

```bash
python scripts/review.py --reviewer "<your name>"
```

---

## Contents

1. [azathioprine — IM](#1-azathioprine-im)
2. [azathioprine — NM](#2-azathioprine-nm)
3. [azathioprine — PM](#3-azathioprine-pm)
4. [azathioprine — Unknown](#4-azathioprine-unknown)
5. [clopidogrel — IM](#5-clopidogrel-im)
6. [clopidogrel — NM](#6-clopidogrel-nm)
7. [clopidogrel — PM](#7-clopidogrel-pm)
8. [clopidogrel — RM](#8-clopidogrel-rm)
9. [clopidogrel — URM](#9-clopidogrel-urm)
10. [clopidogrel — Unknown](#10-clopidogrel-unknown)
11. [codeine — Unknown](#11-codeine-unknown)
12. [fluorouracil — IM](#12-fluorouracil-im)
13. [fluorouracil — NM](#13-fluorouracil-nm)
14. [fluorouracil — PM](#14-fluorouracil-pm)
15. [fluorouracil — Unknown](#15-fluorouracil-unknown)
16. [simvastatin — IM](#16-simvastatin-im)
17. [simvastatin — NM](#17-simvastatin-nm)
18. [simvastatin — PM](#18-simvastatin-pm)
19. [simvastatin — Unknown](#19-simvastatin-unknown)
20. [warfarin — Unknown](#20-warfarin-unknown)

---

<a id="1-azathioprine-im"></a>

## 1. azathioprine — IM

| | |
| --- | --- |
| Gene | `TPMT` |
| Phenotype | `IM` |
| Risk label | **Safe** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> Initiate therapy with reduced starting doses (30-80% of standard starting dose) if
> standard starting dose is ≥2 mg/kg/day. If starting dose is already below standard
> starting dose, dose reduction might not be necessary. During therapy, adjust the doses
> of azathioprine based on the degree of myelosuppression and disease-specific guidelines.
> It usually takes at least 2-4 weeks of stable dosing to reach steady state after each
> dose adjustment.

**Mechanism source:**

> Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al.
> Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine
> Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026).
> PMID: 41618934

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> TPMT encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates
> thiopurine compounds and so diverts them away from the pathway that produces active
> metabolites.
>
> Source: Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et
> al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine
> Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026).
> PMID: 41618934

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results do not suggest a change to how this medicine is usually prescribed.
> Your {gene} gene result shows somewhat lower activity than most people, which is what
> this medicine's handling depends on. The clinical recommendation shown with this result
> comes from published CPIC guidance, not from this tool. Discuss this with your doctor or
> pharmacist before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="2-azathioprine-nm"></a>

## 2. azathioprine — NM

| | |
| --- | --- |
| Gene | `NUDT15` |
| Phenotype | `NM` |
| Risk label | **Safe** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> Initiate therapy with standard starting dose (e.g., 2 mg/kg/day for autoimmune
> diseases). During therapy, adjust doses of azathioprine based on disease-specific
> guidelines. It usually takes at least 2 weeks to reach steady state after each dose
> adjustment.

**Mechanism source:**

> Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al.
> Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine
> Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026).
> PMID: 41618934

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> TPMT encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates
> thiopurine compounds and so diverts them away from the pathway that produces active
> metabolites.
>
> Source: Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et
> al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine
> Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026).
> PMID: 41618934

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results do not suggest a change to how this medicine is usually prescribed.
> Your {gene} gene result shows activity in the usual range, which is what this medicine's
> handling depends on. The clinical recommendation shown with this result comes from
> published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist
> before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="3-azathioprine-pm"></a>

## 3. azathioprine — PM

| | |
| --- | --- |
| Gene | `TPMT` |
| Phenotype | `PM` |
| Risk label | **Toxic** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> Consider alternative nonthiopurine immunosuppressant therapy.

**Mechanism source:**

> Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al.
> Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine
> Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026).
> PMID: 41618934

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> TPMT encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates
> thiopurine compounds and so diverts them away from the pathway that produces active
> metabolites.
>
> Source: Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et
> al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine
> Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026).
> PMID: 41618934

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results suggest a higher chance of harmful effects from this medicine. Your
> {gene} gene result shows much lower activity than most people, which is what this
> medicine's handling depends on. The clinical recommendation shown with this result comes
> from published CPIC guidance, not from this tool. Discuss this with your doctor or
> pharmacist before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="4-azathioprine-unknown"></a>

## 4. azathioprine — Unknown

| | |
| --- | --- |
| Gene | `TPMT` |
| Phenotype | `Unknown` |
| Risk label | **Unknown** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> _(none — this is an Unknown case)_

**Mechanism source:**

> Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al.
> Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine
> Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026).
> PMID: 41618934

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> TPMT encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates
> thiopurine compounds and so diverts them away from the pathway that produces active
> metabolites.
>
> Source: Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et
> al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine
> Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026).
> PMID: 41618934

**Variant rationale**

> No genotype was called for {drug} in this analysis, so there is no variant-level
> rationale to report.

**Patient-friendly**

> This tool could not reach a conclusion about this medicine for you. That is not a
> reassuring result or a worrying one — it means this tool has nothing to say, and the
> question is still open. Discuss this with your doctor or pharmacist before making any
> change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="5-clopidogrel-im"></a>

## 5. clopidogrel — IM

| | |
| --- | --- |
| Gene | `CYP2C19` |
| Phenotype | `IM` |
| Risk label | **Ineffective** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> Avoid standard dose (75 mg) clopidogrel if possible. Use prasugrel or ticagrelor at
> standard dose if no contraindication.

**Mechanism source:**

> Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical
> Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide
> range of drug substrates. Its activity varies substantially between people because the
> CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme
> production.
>
> Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al.
> Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results suggest this medicine may not work as well for you as intended.
> Your {gene} gene result shows somewhat lower activity than most people, which is what
> this medicine's handling depends on. The clinical recommendation shown with this result
> comes from published CPIC guidance, not from this tool. Discuss this with your doctor or
> pharmacist before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="6-clopidogrel-nm"></a>

## 6. clopidogrel — NM

| | |
| --- | --- |
| Gene | `CYP2C19` |
| Phenotype | `NM` |
| Risk label | **Safe** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> If considering clopidogrel, use at standard dose (75 mg/day)

**Mechanism source:**

> Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical
> Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide
> range of drug substrates. Its activity varies substantially between people because the
> CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme
> production.
>
> Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al.
> Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results do not suggest a change to how this medicine is usually prescribed.
> Your {gene} gene result shows activity in the usual range, which is what this medicine's
> handling depends on. The clinical recommendation shown with this result comes from
> published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist
> before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="7-clopidogrel-pm"></a>

## 7. clopidogrel — PM

| | |
| --- | --- |
| Gene | `CYP2C19` |
| Phenotype | `PM` |
| Risk label | **Ineffective** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> Avoid clopidogrel if possible. Use prasugrel or ticagrelor at standard dose if no
> contraindication.

**Mechanism source:**

> Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical
> Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide
> range of drug substrates. Its activity varies substantially between people because the
> CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme
> production.
>
> Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al.
> Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results suggest this medicine may not work as well for you as intended.
> Your {gene} gene result shows much lower activity than most people, which is what this
> medicine's handling depends on. The clinical recommendation shown with this result comes
> from published CPIC guidance, not from this tool. Discuss this with your doctor or
> pharmacist before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="8-clopidogrel-rm"></a>

## 8. clopidogrel — RM

| | |
| --- | --- |
| Gene | `CYP2C19` |
| Phenotype | `RM` |
| Risk label | **Safe** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> If considering clopidogrel, use at standard dose (75 mg/day)

**Mechanism source:**

> Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical
> Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide
> range of drug substrates. Its activity varies substantially between people because the
> CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme
> production.
>
> Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al.
> Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results do not suggest a change to how this medicine is usually prescribed.
> Your {gene} gene result shows somewhat higher activity than most people, which is what
> this medicine's handling depends on. The clinical recommendation shown with this result
> comes from published CPIC guidance, not from this tool. Discuss this with your doctor or
> pharmacist before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="9-clopidogrel-urm"></a>

## 9. clopidogrel — URM

| | |
| --- | --- |
| Gene | `CYP2C19` |
| Phenotype | `URM` |
| Risk label | **Safe** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> If considering clopidogrel, use at standard dose (75 mg/day)

**Mechanism source:**

> Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical
> Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide
> range of drug substrates. Its activity varies substantially between people because the
> CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme
> production.
>
> Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al.
> Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results do not suggest a change to how this medicine is usually prescribed.
> Your {gene} gene result shows much higher activity than most people, which is what this
> medicine's handling depends on. The clinical recommendation shown with this result comes
> from published CPIC guidance, not from this tool. Discuss this with your doctor or
> pharmacist before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="10-clopidogrel-unknown"></a>

## 10. clopidogrel — Unknown

| | |
| --- | --- |
| Gene | `CYP2C19` |
| Phenotype | `Unknown` |
| Risk label | **Unknown** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> _(none — this is an Unknown case)_

**Mechanism source:**

> Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical
> Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide
> range of drug substrates. Its activity varies substantially between people because the
> CYP2C19 gene carries common variants that abolish, reduce, or increase enzyme
> production.
>
> Source: Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al.
> Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and
> Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

**Variant rationale**

> No genotype was called for {drug} in this analysis, so there is no variant-level
> rationale to report.

**Patient-friendly**

> This tool could not reach a conclusion about this medicine for you. That is not a
> reassuring result or a worrying one — it means this tool has nothing to say, and the
> question is still open. Discuss this with your doctor or pharmacist before making any
> change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="11-codeine-unknown"></a>

## 11. codeine — Unknown

| | |
| --- | --- |
| Gene | `CYP2D6` |
| Phenotype | `Unknown` |
| Risk label | **Unknown** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> _(none — this is an Unknown case)_

**Mechanism source:**

> Annotation of CPIC Guideline for codeine and CYP2D6 — Crews KR et al. Clinical
> Pharmacogenetics Implementation Consortium Guideline for CYP2D6, OPRM1, and COMT
> Genotypes and Select Opioid Therapy. Clin Pharmacol Ther (2021). PMID: 33387367

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> CYP2D6 is a hepatic cytochrome P450 enzyme responsible for metabolising a large share of
> commonly used drugs. CYP2D6 is unusually variable: as well as single-nucleotide variants
> that alter or abolish activity, the gene is subject to **whole-gene deletions and
> duplications**, so copy number differs between people. Activity is conventionally
> summarised as an activity score derived from both alleles.
>
> Source: Annotation of CPIC Guideline for codeine and CYP2D6 — Crews KR et al. Clinical
> Pharmacogenetics Implementation Consortium Guideline for CYP2D6, OPRM1, and COMT
> Genotypes and Select Opioid Therapy. Clin Pharmacol Ther (2021). PMID: 33387367

**Variant rationale**

> No genotype was called for {drug} in this analysis, so there is no variant-level
> rationale to report.

**Patient-friendly**

> This tool could not reach a conclusion about this medicine for you. That is not a
> reassuring result or a worrying one — it means this tool has nothing to say, and the
> question is still open. Discuss this with your doctor or pharmacist before making any
> change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="12-fluorouracil-im"></a>

## 12. fluorouracil — IM

| | |
| --- | --- |
| Gene | `DPYD` |
| Phenotype | `IM` |
| Risk label | **Adjust Dosage** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> Reduce starting dose by 50% followed by titration of dose based on toxicity or
> therapeutic drug monitoring (if available). Patients with the c.2846A&gt;T/c.2846A&gt;T
> genotype may require &gt;50% reduction in starting dose.

**Mechanism source:**

> Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical
> Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine
> Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther
> (2018). PMID: 29152729

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of
> pyrimidine catabolism. DPD is expressed widely, with high activity in the liver, and is
> responsible for breaking down the great majority of an administered fluoropyrimidine
> dose into inactive metabolites.
>
> Source: Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al.
> Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for
> Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin
> Pharmacol Ther (2018). PMID: 29152729

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results suggest this medicine may need to be prescribed differently from
> the usual approach. Your {gene} gene result shows somewhat lower activity than most
> people, which is what this medicine's handling depends on. The clinical recommendation
> shown with this result comes from published CPIC guidance, not from this tool. Discuss
> this with your doctor or pharmacist before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="13-fluorouracil-nm"></a>

## 13. fluorouracil — NM

| | |
| --- | --- |
| Gene | `DPYD` |
| Phenotype | `NM` |
| Risk label | **Safe** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> Based on genotype, there is no indication to change dose or therapy. Use label-
> recommended dosage and administration.

**Mechanism source:**

> Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical
> Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine
> Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther
> (2018). PMID: 29152729

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of
> pyrimidine catabolism. DPD is expressed widely, with high activity in the liver, and is
> responsible for breaking down the great majority of an administered fluoropyrimidine
> dose into inactive metabolites.
>
> Source: Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al.
> Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for
> Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin
> Pharmacol Ther (2018). PMID: 29152729

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results do not suggest a change to how this medicine is usually prescribed.
> Your {gene} gene result shows activity in the usual range, which is what this medicine's
> handling depends on. The clinical recommendation shown with this result comes from
> published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist
> before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="14-fluorouracil-pm"></a>

## 14. fluorouracil — PM

| | |
| --- | --- |
| Gene | `DPYD` |
| Phenotype | `PM` |
| Risk label | **Toxic** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> Avoid use of 5-fluorouracil or 5-fluorouracil prodrug-based regimens.

**Mechanism source:**

> Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical
> Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine
> Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther
> (2018). PMID: 29152729

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of
> pyrimidine catabolism. DPD is expressed widely, with high activity in the liver, and is
> responsible for breaking down the great majority of an administered fluoropyrimidine
> dose into inactive metabolites.
>
> Source: Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al.
> Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for
> Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin
> Pharmacol Ther (2018). PMID: 29152729

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results suggest a higher chance of harmful effects from this medicine. Your
> {gene} gene result shows much lower activity than most people, which is what this
> medicine's handling depends on. The clinical recommendation shown with this result comes
> from published CPIC guidance, not from this tool. Discuss this with your doctor or
> pharmacist before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="15-fluorouracil-unknown"></a>

## 15. fluorouracil — Unknown

| | |
| --- | --- |
| Gene | `DPYD` |
| Phenotype | `Unknown` |
| Risk label | **Unknown** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> _(none — this is an Unknown case)_

**Mechanism source:**

> Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical
> Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine
> Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther
> (2018). PMID: 29152729

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of
> pyrimidine catabolism. DPD is expressed widely, with high activity in the liver, and is
> responsible for breaking down the great majority of an administered fluoropyrimidine
> dose into inactive metabolites.
>
> Source: Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al.
> Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for
> Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin
> Pharmacol Ther (2018). PMID: 29152729

**Variant rationale**

> No genotype was called for {drug} in this analysis, so there is no variant-level
> rationale to report.

**Patient-friendly**

> This tool could not reach a conclusion about this medicine for you. That is not a
> reassuring result or a worrying one — it means this tool has nothing to say, and the
> question is still open. Discuss this with your doctor or pharmacist before making any
> change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="16-simvastatin-im"></a>

## 16. simvastatin — IM

| | |
| --- | --- |
| Gene | `SLCO1B1` |
| Phenotype | `IM` |
| Risk label | **Adjust Dosage** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> Prescribe an alternative statin depending on the desired potency (see Figure 1 of PMID:
> 35152405 for recommendations for alternative statins). If simvastatin therapy is
> warranted, limit dose to &lt;20mg/day.

**Mechanism source:**

> Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The
> Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and
> CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther
> (2022). PMID: 35152405

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> SLCO1B1 encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing) membrane
> of liver cells. Its job is to move drugs out of portal blood and into hepatocytes. It is
> a **transporter, not a metabolising enzyme**, which is why its phenotypes are described
> as function categories (normal, decreased, poor function) rather than metaboliser
> categories.
>
> Source: Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et
> al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1,
> ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin
> Pharmacol Ther (2022). PMID: 35152405

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results suggest this medicine may need to be prescribed differently from
> the usual approach. Your {gene} gene result shows somewhat lower activity than most
> people, which is what this medicine's handling depends on. The clinical recommendation
> shown with this result comes from published CPIC guidance, not from this tool. Discuss
> this with your doctor or pharmacist before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="17-simvastatin-nm"></a>

## 17. simvastatin — NM

| | |
| --- | --- |
| Gene | `SLCO1B1` |
| Phenotype | `NM` |
| Risk label | **Safe** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> Prescribe desired starting dose and adjust doses based on disease-specific guidelines.

**Mechanism source:**

> Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The
> Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and
> CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther
> (2022). PMID: 35152405

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> SLCO1B1 encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing) membrane
> of liver cells. Its job is to move drugs out of portal blood and into hepatocytes. It is
> a **transporter, not a metabolising enzyme**, which is why its phenotypes are described
> as function categories (normal, decreased, poor function) rather than metaboliser
> categories.
>
> Source: Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et
> al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1,
> ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin
> Pharmacol Ther (2022). PMID: 35152405

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results do not suggest a change to how this medicine is usually prescribed.
> Your {gene} gene result shows activity in the usual range, which is what this medicine's
> handling depends on. The clinical recommendation shown with this result comes from
> published CPIC guidance, not from this tool. Discuss this with your doctor or pharmacist
> before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="18-simvastatin-pm"></a>

## 18. simvastatin — PM

| | |
| --- | --- |
| Gene | `SLCO1B1` |
| Phenotype | `PM` |
| Risk label | **Adjust Dosage** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> Prescribe an alternative statin depending on the desired potency (see Figure 1 of PMID:
> 35152405 for recommendations for alternative statins).

**Mechanism source:**

> Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The
> Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and
> CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther
> (2022). PMID: 35152405

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> SLCO1B1 encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing) membrane
> of liver cells. Its job is to move drugs out of portal blood and into hepatocytes. It is
> a **transporter, not a metabolising enzyme**, which is why its phenotypes are described
> as function categories (normal, decreased, poor function) rather than metaboliser
> categories.
>
> Source: Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et
> al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1,
> ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin
> Pharmacol Ther (2022). PMID: 35152405

**Variant rationale**

> PharmCAT called {gene} as {diplotype}, which corresponds to a {phenotype} result. The
> non-reference positions supporting this call were {detected_variants}.

**Patient-friendly**

> Your genetic results suggest this medicine may need to be prescribed differently from
> the usual approach. Your {gene} gene result shows much lower activity than most people,
> which is what this medicine's handling depends on. The clinical recommendation shown
> with this result comes from published CPIC guidance, not from this tool. Discuss this
> with your doctor or pharmacist before making any change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="19-simvastatin-unknown"></a>

## 19. simvastatin — Unknown

| | |
| --- | --- |
| Gene | `SLCO1B1` |
| Phenotype | `Unknown` |
| Risk label | **Unknown** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> _(none — this is an Unknown case)_

**Mechanism source:**

> Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The
> Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and
> CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther
> (2022). PMID: 35152405

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> SLCO1B1 encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing) membrane
> of liver cells. Its job is to move drugs out of portal blood and into hepatocytes. It is
> a **transporter, not a metabolising enzyme**, which is why its phenotypes are described
> as function categories (normal, decreased, poor function) rather than metaboliser
> categories.
>
> Source: Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et
> al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1,
> ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin
> Pharmacol Ther (2022). PMID: 35152405

**Variant rationale**

> No genotype was called for {drug} in this analysis, so there is no variant-level
> rationale to report.

**Patient-friendly**

> This tool could not reach a conclusion about this medicine for you. That is not a
> reassuring result or a worrying one — it means this tool has nothing to say, and the
> question is still open. Discuss this with your doctor or pharmacist before making any
> change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

<a id="20-warfarin-unknown"></a>

## 20. warfarin — Unknown

| | |
| --- | --- |
| Gene | `CYP2C9` |
| Phenotype | `Unknown` |
| Risk label | **Unknown** |
| Source | LLM-generated |
| Model | `` |
| Prompt hash | `—` |
| Generated | 2026-07-23T04:10:28.115122+00:00 |
| Automated guard | ✅ passed |

### Grounding — the source this must follow from

**CPIC recommendation (verbatim, via PharmCAT):**

> _(none — this is an Unknown case)_

**Mechanism source:**

> Annotation of CPIC Guideline for warfarin and CYP2C9, CYP4F2, VKORC1 — Johnson JA et al.
> Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for
> Pharmacogenetics-Guided Warfarin Dosing: 2017 Update. Clin Pharmacol Ther (2017). PMID:
> 28198005

### Explanation as a user would see it

**Summary**

> {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.

**Mechanism**

> CYP2C9 is a hepatic cytochrome P450 enzyme. Among many substrates, it is the principal
> route of clearance for S-warfarin, the more pharmacologically potent of warfarin's two
> enantiomers.
>
> Source: Annotation of CPIC Guideline for warfarin and CYP2C9, CYP4F2, VKORC1 — Johnson
> JA et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for
> Pharmacogenetics-Guided Warfarin Dosing: 2017 Update. Clin Pharmacol Ther (2017). PMID:
> 28198005

**Variant rationale**

> No genotype was called for {drug} in this analysis, so there is no variant-level
> rationale to report.

**Patient-friendly**

> This tool could not reach a conclusion about this medicine for you. That is not a
> reassuring result or a worrying one — it means this tool has nothing to say, and the
> question is still open. Discuss this with your doctor or pharmacist before making any
> change to your medicines.

### Reviewer decision

| | |
| --- | --- |
| ☐ Approve — faithful, correct direction, readable | |
| ☐ Approve with edits *(note them below)* | |
| ☐ Reject *(state why)* | |

**Comments:**

```


```

**Reviewer:** ______________________  **Date:** ____________

---

## Sign-off

I have reviewed the explanations in this document. Those marked approved
are, to the best of my knowledge, faithful to the cited CPIC guidance and
correct in the direction of effect they describe.

I understand this is a research/educational prototype and **not a medical
device**, and that approval here is not clinical validation.

**Name:** ____________________________________

**Role / department:** _______________________

**Signature:** _______________  **Date:** ____________
