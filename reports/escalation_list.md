# Escalation list — sentences automation would not decide

**19 items.** Every other outstanding sentence was auto-accepted against a quoted source passage; these are the ones where a person has to look.

Automation never rejects and never guesses. An item is here because it asserts something the aligned passage does not obviously support, or because no passage aligned at all.

There is deliberately **no recommended verdict** — a proposed answer invites rubber-stamping, and this list exists precisely because these sentences need judgement rather than a signature.

Clear them in one pass:

```bash
python scripts/adjudicate.py --escalated-only --adjudicator "<your real name>"
```

---

## 1. clopidogrel:RM · `mechanism`

**Sentence**

> This leads to normal or lower platelet reactivity, which is not associated with a higher risk of bleeding.

**Aligned source passage** — Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

> Platelet inhibition is at least as strong as expected; CPIC's own implications text for this group notes no association with higher bleeding risk.

**Why this needs your eyes**

- claims an ABSENCE. Invisible to every automated check here: it carries no assertion marker and contradicts no directive, and it errs toward reassurance. Always escalated. (“not associated”)
- adds a causal step that may not be in the source (“leads to”)
- makes a comparative or graded risk claim (“higher risk”)

**Decision** (accept / edit / reject) and why:

```

```

---

## 2. simvastatin:NM · `mechanism`

**Sentence**

> Your genetic result does not affect the liver's ability to take up simvastatin, so the typical risk of muscle toxicity remains.

**Aligned source passage** — Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405

> The concern is **muscle toxicity**, driven by drug that failed to reach the liver.

**Why this needs your eyes**

- claims an ABSENCE. Invisible to every automated check here: it carries no assertion marker and contradicts no directive, and it errs toward reassurance. Always escalated. (“does not”)

**Decision** (accept / edit / reject) and why:

```

```

---

## 3. azathioprine:IM · `mechanism`

**Sentence**

> Azathioprine is a medication that works by producing active metabolites that can affect the immune system.

**Aligned source passage:** :warning: **none found.** The aligner could not match this sentence to any corpus passage. That is not a finding of fabrication, but nothing supports it automatically.

**Why this needs your eyes**

- no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against.

**Decision** (accept / edit / reject) and why:

```

```

---

## 4. azathioprine:IM · `mechanism`

**Sentence**

> If your body breaks them down too slowly, it can lead to a buildup of toxic levels, causing myelosuppression.

**Aligned source passage:** :warning: **none found.** The aligner could not match this sentence to any corpus passage. That is not a finding of fabrication, but nothing supports it automatically.

**Why this needs your eyes**

- no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against.

**Decision** (accept / edit / reject) and why:

```

```

---

## 5. azathioprine:NM · `mechanism`

**Sentence**

> Your genetic result indicates that you have normal function in the enzymes that handle this process, which means that you are not at increased risk for the side effects associated with this drug.

**Aligned source passage:** :warning: **none found.** The aligner could not match this sentence to any corpus passage. That is not a finding of fabrication, but nothing supports it automatically.

**Why this needs your eyes**

- no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against.

**Decision** (accept / edit / reject) and why:

```

```

---

## 6. azathioprine:PM · `mechanism`

**Sentence**

> The medication is converted into an active form that can affect the bone marrow, leading to a decrease in white blood cells.

**Aligned source passage:** :warning: **none found.** The aligner could not match this sentence to any corpus passage. That is not a finding of fabrication, but nothing supports it automatically.

**Why this needs your eyes**

- no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against.

**Decision** (accept / edit / reject) and why:

```

```

---

## 7. azathioprine:PM · `mechanism`

**Sentence**

> Your genetic result removes a brake on this process, allowing more of the active form to accumulate and increase the risk of serious side effects.

**Aligned source passage:** :warning: **none found.** The aligner could not match this sentence to any corpus passage. That is not a finding of fabrication, but nothing supports it automatically.

**Why this needs your eyes**

- no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against.

**Decision** (accept / edit / reject) and why:

```

```

---

## 8. azathioprine:Unknown · `mechanism`

**Sentence**

> This medication is converted into active compounds in your body, which can affect your bone marrow and cause low white blood cell counts.

**Aligned source passage:** :warning: **none found.** The aligner could not match this sentence to any corpus passage. That is not a finding of fabrication, but nothing supports it automatically.

**Why this needs your eyes**

- no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against.

**Decision** (accept / edit / reject) and why:

```

```

---

## 9. fluorouracil:NM · `mechanism`

**Sentence**

> Your body's normal DPD activity helps to inactivate most of the drug, which reduces the risk of severe side effects.

**Aligned source passage:** :warning: **none found.** The aligner could not match this sentence to any corpus passage. That is not a finding of fabrication, but nothing supports it automatically.

**Why this needs your eyes**

- no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against.

**Decision** (accept / edit / reject) and why:

```

```

---

## 10. fluorouracil:Unknown · `mechanism`

**Sentence**

> If DPD is not working properly, the drug can persist in the body for longer and cause more severe side effects.

**Aligned source passage:** :warning: **none found.** The aligner could not match this sentence to any corpus passage. That is not a finding of fabrication, but nothing supports it automatically.

**Why this needs your eyes**

- no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against.

**Decision** (accept / edit / reject) and why:

```

```

---

## 11. simvastatin:PM · `mechanism`

**Sentence**

> This leads to higher levels of simvastatin in the bloodstream, which can cause muscle toxicity.

**Aligned source passage:** :warning: **none found.** The aligner could not match this sentence to any corpus passage. That is not a finding of fabrication, but nothing supports it automatically.

**Why this needs your eyes**

- no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against.

**Decision** (accept / edit / reject) and why:

```

```

---

## 12. simvastatin:Unknown · `summary`

**Sentence**

> The recommendation for your genetic result and simvastatin is unknown because no usable result for this gene was established.

**Aligned source passage:** :warning: **none found.** The aligner could not match this sentence to any corpus passage. That is not a finding of fabrication, but nothing supports it automatically.

**Why this needs your eyes**

- no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against.

**Decision** (accept / edit / reject) and why:

```

```

---

## 13. simvastatin:Unknown · `patient_friendly`

**Sentence**

> This is because no usable result for this gene was established.

**Aligned source passage:** :warning: **none found.** The aligner could not match this sentence to any corpus passage. That is not a finding of fabrication, but nothing supports it automatically.

**Why this needs your eyes**

- no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against.

**Decision** (accept / edit / reject) and why:

```

```

---

## 14. azathioprine:Unknown · `mechanism`

**Sentence**

> If these enzymes are not working properly, more of the active compounds can build up and cause problems.

**Aligned source passage** — Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934

> TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates thiopurine compounds and so diverts them away from the pathway that produces active metabolites.

**Why this needs your eyes**

- adds a causal step that may not be in the source (“cause”)

**Decision** (accept / edit / reject) and why:

```

```

---

## 15. clopidogrel:RM · `mechanism`

**Sentence**

> Your genetic result shows that you have normal or increased function of this enzyme, which means the active form of the medication is formed quickly and effectively.

**Aligned source passage** — Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351

> Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.

**Why this needs your eyes**

- adds a causal step that may not be in the source (“which means”)

**Decision** (accept / edit / reject) and why:

```

```

---

## 16. fluorouracil:IM · `mechanism`

**Sentence**

> Reduced DPD activity slows inactivation, leading to higher and longer exposure to active drug, which can cause severe toxicity.

**Aligned source passage** — Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

> Reduced DPD activity (partial deficiency)** slows inactivation, so exposure to active drug is higher and lasts longer for the same administered amount.

**Why this needs your eyes**

- adds a causal step that may not be in the source (“cause”)

**Decision** (accept / edit / reject) and why:

```

```

---

## 17. fluorouracil:NM · `mechanism`

**Sentence**

> If you have normal DPD activity, the standard dose of fluorouracil is likely to be safe.

**Aligned source passage** — Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729

> DPD is expressed widely, with high activity in the liver, and is responsible for breaking down the great majority of an administered fluoropyrimidine dose into inactive metabolites.

**Why this needs your eyes**

- asserts SAFETY. Reassurance is the direction every defect in this project ran in, so an affirmative safety claim is never auto-accepted. (“is likely to be safe”)

**Decision** (accept / edit / reject) and why:

```

```

---

## 18. simvastatin:NM · `mechanism`

**Sentence**

> The liver's ability to take up simvastatin is important for keeping systemic exposure low and reducing the risk of muscle toxicity.

**Aligned source passage** — Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405

> Efficient hepatic uptake therefore does two things at once: it delivers the drug to its target, and it keeps systemic — particularly skeletal muscle — exposure low.

**Why this needs your eyes**

- makes a comparative or graded risk claim (“reducing the risk”)

**Decision** (accept / edit / reject) and why:

```

```

---

## 19. warfarin:Unknown · `mechanism`

**Sentence**

> Reduced function of this enzyme can lead to slower clearance of warfarin, resulting in higher exposure and a stronger anticoagulant effect.

**Aligned source passage** — Annotation of CPIC Guideline for warfarin and CYP2C9, CYP4F2, VKORC1 — Johnson JA et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Pharmacogenetics-Guided Warfarin Dosing: 2017 Update. Clin Pharmacol Ther (2017). PMID: 28198005

> Reduced CYP2C9 function** slows S-warfarin clearance, so the same administered amount produces higher steady-state exposure and a stronger anticoagulant effect.

**Why this needs your eyes**

- adds a causal step that may not be in the source (“lead to”)

**Decision** (accept / edit / reject) and why:

```

```

---
