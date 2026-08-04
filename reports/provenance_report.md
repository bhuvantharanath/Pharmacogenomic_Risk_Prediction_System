# Provenance verification

**Generated:** 2026-08-04T07:02:59.140432+00:00  
**Verifier:** `verify_provenance.py v1.0.0`  
**Store:** `backend/app/data/explanations.json`  
**Entries:** 20

## What this number means

This project has **no qualified clinical reviewer**, so it makes a
different and narrower claim than expert approval: *the system asserts
no clinical content of its own.* Every sentence carrying a clinical
claim is traced, word by word, to text this project did not write.

| | |
| --- | --- |
| ✅ **verified means** | every clinical word in the sentence appears in a cited source |
| ❌ **verified does NOT mean** | a clinician has agreed the sentence is correct |

Lexical tracing cannot detect a sentence that is assembled from source
words and still wrong — reversed causality, a hedge dropped, a
recommendation attached to the wrong phenotype. That needs a clinician.
**Do not quote the percentage below without this paragraph.**

## Headline

- **106 of 106 clinical-claim sentences have verified provenance (100.0%)** — target 100%

| Class | Verified | Traces to | Gates release |
| --- | ---: | --- | :---: |
| `CLINICAL` | 0/0 | CPIC recommendation text, verbatim from PharmCAT | ✅ |
| `LABEL_PARAPHRASE` | 0/0 | `label_paraphrases.yaml` → the label a named `label_mapping.yaml` rule derived from CPIC text | ✅ |
| `MECHANISM` | 0/0 | the corpus file for that gene-drug pair (cited, dated) | ➖ reported |
| `PROCESS` | 0 | describes this analysis, not a clinical claim | ➖ exempt |
| `FRAMING` | 73 | carries no clinical claim | ➖ exempt, listed below |

### Why `LABEL_PARAPHRASE` is a separate class

Patient-facing prose cannot quote CPIC verbatim and stay readable —
"Avoid standard dose (75 mg) clopidogrel if possible" is exactly what a
worried patient cannot parse. One sentence per result therefore restates
the derived risk label in plain words.

That sentence is a clinical claim whose words appear in no source. Left
implicit it would be the system asserting clinical content on its own
authority. Declaring each paraphrase in `label_paraphrases.yaml` makes
the chain explicit and checkable, and the verifier additionally requires
that a paraphrase match **this entry's** label — so the `Safe` wording
attached to a `Toxic` result fails rather than passing as "declared".

## ✅ No unverified clinical or mechanism sentences

## Per-entry

| Case | Clinical | Mechanism | Framing | Status |
| --- | ---: | ---: | ---: | --- |
| `azathioprine:IM` | 8/8 | 0/0 | 2 | ✅ |
| `azathioprine:NM` | 5/5 | 0/0 | 3 | ✅ |
| `azathioprine:PM` | 5/5 | 0/0 | 2 | ✅ |
| `azathioprine:Unknown` | 2/2 | 0/0 | 7 | ✅ _no CPIC recommendation text for this case_ |
| `clopidogrel:IM` | 6/6 | 0/0 | 4 | ✅ |
| `clopidogrel:NM` | 4/4 | 0/0 | 3 | ✅ |
| `clopidogrel:PM` | 7/7 | 0/0 | 3 | ✅ |
| `clopidogrel:RM` | 6/6 | 0/0 | 3 | ✅ |
| `clopidogrel:URM` | 5/5 | 0/0 | 4 | ✅ |
| `clopidogrel:Unknown` | 5/5 | 0/0 | 4 | ✅ _no CPIC recommendation text for this case_ |
| `codeine:Unknown` | 4/4 | 0/0 | 3 | ✅ _no CPIC recommendation text for this case_ |
| `fluorouracil:IM` | 8/8 | 0/0 | 2 | ✅ |
| `fluorouracil:NM` | 6/6 | 0/0 | 5 | ✅ |
| `fluorouracil:PM` | 5/5 | 0/0 | 2 | ✅ |
| `fluorouracil:Unknown` | 6/6 | 0/0 | 4 | ✅ _no CPIC recommendation text for this case_ |
| `simvastatin:IM` | 7/7 | 0/0 | 4 | ✅ |
| `simvastatin:NM` | 5/5 | 0/0 | 5 | ✅ |
| `simvastatin:PM` | 5/5 | 0/0 | 3 | ✅ |
| `simvastatin:Unknown` | 5/5 | 0/0 | 5 | ✅ _no CPIC recommendation text for this case_ |
| `warfarin:Unknown` | 2/2 | 0/0 | 5 | ✅ _no CPIC recommendation text for this case_ |

## FRAMING sentences (exempt — read them anyway)

These carry no clinical claim, so nothing traces them. That makes this
the list where an unnoticed clinical assertion would hide, which is why
it is printed in full rather than counted.

- `azathioprine:IM` · *summary* — Your genetic result may affect how well you tolerate azathioprine.
- `azathioprine:IM` · *variant_rationale* — The non-reference positions supporting this call were no non-reference variants were detected.
- `azathioprine:NM` · *patient_friendly* — This is because your body handles the medication in a normal way.
- `azathioprine:NM` · *patient_friendly* — However, it's always best to speak with your doctor or pharmacist to confirm this information and get personalized advice.
- `azathioprine:PM` · *patient_friendly* — They can help you find a safer option that works for you.
- `azathioprine:Unknown` · *summary* — Your genetic result has not been determined for the gene involved in how your body handles a certain medication.
- `azathioprine:Unknown` · *summary* — This means we cannot provide a specific recommendation for how to use this medication safely.
- `azathioprine:Unknown` · *mechanism* — Normally, certain enzymes help control the amount of these active compounds.
- `azathioprine:Unknown` · *variant_rationale* — No genotype was called for azathioprine in this analysis, so there is no variant-level rationale to report.
- `azathioprine:Unknown` · *patient_friendly* — We don't have enough information about how your body handles this medication.
- `azathioprine:Unknown` · *patient_friendly* — This means we can't give you specific advice on how to use it safely.
- `azathioprine:Unknown` · *patient_friendly* — It's always best to talk to your doctor or pharmacist about any concerns you have about your medication.
- `clopidogrel:IM` · *summary* — Your genetic result affects how well you respond to clopidogrel.
- `clopidogrel:IM` · *patient_friendly* — If you have a certain genetic result, clopidogrel might not work as well as it should.
- `clopidogrel:IM` · *patient_friendly* — This is because your body doesn't make enough of the active form of the medicine.
- `clopidogrel:NM` · *patient_friendly* — This means that you can take the standard dose of clopidogrel without worrying about it not working properly.
- `clopidogrel:NM` · *patient_friendly* — However, it's always best to speak with your doctor or pharmacist to confirm the right dose for you.
- `clopidogrel:PM` · *patient_friendly* — Always talk to your doctor or pharmacist about your specific situation and any concerns you may have.
- `clopidogrel:RM` · *patient_friendly* — If you're considering taking clopidogrel, you can take it at the standard dose.
- `clopidogrel:RM` · *patient_friendly* — However, it's always best to speak with your doctor or pharmacist to confirm the right dosage for you.
- `clopidogrel:URM` · *patient_friendly* — Your genetic result shows that you are a safe candidate for taking clopidogrel.
- `clopidogrel:URM` · *patient_friendly* — However, to make sure the drug works properly, it's recommended to take it at the standard dose.
- `clopidogrel:URM` · *patient_friendly* — This means you should talk to your doctor or pharmacist about the best way to take clopidogrel based on your individual needs.
- `clopidogrel:Unknown` · *summary* — Therefore, the CPIC recommendation is unknown.
- `clopidogrel:Unknown` · *variant_rationale* — No genotype was called for clopidogrel in this analysis, so there is no variant-level rationale to report.
- `clopidogrel:Unknown` · *patient_friendly* — This means we can't say for sure how well the drug will work for you.
- `clopidogrel:Unknown` · *patient_friendly* — It's always a good idea to talk to your doctor or pharmacist about your specific situation and any concerns you may have.
- `codeine:Unknown` · *summary* — Your genetic result for codeine is unknown, so we cannot explain how it will be handled by your body.
- `codeine:Unknown` · *variant_rationale* — No genotype was called for codeine in this analysis, so there is no variant-level rationale to report.
- `codeine:Unknown` · *patient_friendly* — If you're taking codeine, it's best to speak with your doctor or pharmacist to understand how it will affect you.
- `fluorouracil:IM` · *patient_friendly* — If you're taking fluorouracil, your doctor may need to adjust your dosage based on your genetic result.
- `fluorouracil:NM` · *summary* — Based on your genetic result, there is no indication to change the dose or therapy for fluorouracil.
- `fluorouracil:NM` · *summary* — Use the label-recommended dosage and administration.
- `fluorouracil:NM` · *patient_friendly* — You should be able to take the standard dose of fluorouracil without any problems.
- `fluorouracil:NM` · *patient_friendly* — However, it's always best to speak with your doctor or pharmacist to confirm the best course of treatment for you.
- `fluorouracil:PM` · *patient_friendly* — They can help you make an informed decision about your care.
- `fluorouracil:Unknown` · *mechanism* — Fluorouracil is a type of chemotherapy that works by disrupting DNA and RNA synthesis in dividing cells.
- `fluorouracil:Unknown` · *variant_rationale* — No genotype was called for fluorouracil in this analysis, so there is no variant-level rationale to report.
- `fluorouracil:Unknown` · *patient_friendly* — This is because the drug can build up in your body and cause problems.
- `fluorouracil:Unknown` · *patient_friendly* — It's always best to speak with your doctor or pharmacist about any concerns you have about your medication.
- `simvastatin:IM` · *summary* — Your genetic result affects how your body handles simvastatin, a type of statin medication.
- `simvastatin:IM` · *patient_friendly* — This is because your body may not be able to remove simvastatin from the circulation into the liver as efficiently as usual.
- `simvastatin:IM` · *patient_friendly* — Be sure to talk to your doctor or pharmacist about your genetic result and how it may affect your medication.
- `simvastatin:NM` · *summary* — You can be prescribed the desired starting dose and adjust doses based on disease-specific guidelines.
- `simvastatin:NM` · *patient_friendly* — You don't have a genetic variation that affects how your body handles simvastatin.
- `simvastatin:NM` · *patient_friendly* — This means you can take the usual dose and adjust it based on your disease and how you're responding to the medication.
- `simvastatin:PM` · *patient_friendly* — This is because your body is not able to remove simvastatin from the bloodstream as well as it should be, which can cause muscle problems.
- `simvastatin:Unknown` · *summary* — The recommendation for your genetic result and simvastatin is unknown because no usable result for this gene was established.
- `simvastatin:Unknown` · *mechanism* — Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both its site of action and its route of elimination.
- `simvastatin:Unknown` · *variant_rationale* — No genotype was called for simvastatin in this analysis, so there is no variant-level rationale to report.
- `simvastatin:Unknown` · *patient_friendly* — We don't have enough information about your genetic result to make a recommendation about taking simvastatin.
- `simvastatin:Unknown` · *patient_friendly* — This is because no usable result for this gene was established.
- `warfarin:Unknown` · *summary* — Your genetic result does not provide enough information to make a recommendation for warfarin dosing.
- `warfarin:Unknown` · *variant_rationale* — No genotype was called for warfarin in this analysis, so there is no variant-level rationale to report.
- `warfarin:Unknown` · *patient_friendly* — We don't have enough information about your genetic result to give you specific advice about taking warfarin.
- `warfarin:Unknown` · *patient_friendly* — Warfarin is a medication that helps prevent blood clots, but it can also cause bleeding.
- `warfarin:Unknown` · *patient_friendly* — If you're taking warfarin, it's essential to work closely with your doctor or pharmacist to monitor your treatment and adjust your dose as needed.

## Method

1. Prose is split into sentences (abbreviation-aware, so citations survive).
2. Each sentence is classified CLINICAL / MECHANISM / FRAMING by pattern.
   CLINICAL wins ties, so a dosing instruction cannot escape the strict
   check by also mentioning an enzyme.
3. Content words are extracted (stopwords and runtime slots removed).
4. Every content word must appear in the source, allowing for plural and
   tense variation. CLINICAL traces to the CPIC recommendation, its
   implications, and the derived risk label; MECHANISM traces to the
   corpus file for that gene-drug pair.

Stricter than the faithfulness guard, which checks only entities (doses,
numbers, rsIDs, star alleles, genes, drugs). A sentence can pass the guard
while making a claim the source never made, because its numbers all appear
somewhere. Here the whole claim must be present.

