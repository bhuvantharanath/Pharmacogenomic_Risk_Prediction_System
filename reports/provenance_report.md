# Provenance verification

**Generated:** 2026-07-24T04:01:29.602734+00:00  
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

- **34 of 34 clinical-claim sentences have verified provenance (100.0%)** — target 100%

| Class | Verified | Traces to | Gates release |
| --- | ---: | --- | :---: |
| `CLINICAL` | 0/0 | CPIC recommendation text, verbatim from PharmCAT | ✅ |
| `LABEL_PARAPHRASE` | 20/20 | `label_paraphrases.yaml` → the label a named `label_mapping.yaml` rule derived from CPIC text | ✅ |
| `MECHANISM` | 37/37 | the corpus file for that gene-drug pair (cited, dated) | ➖ reported |
| `PROCESS` | 40 | describes this analysis, not a clinical claim | ➖ exempt |
| `FRAMING` | 58 | carries no clinical claim | ➖ exempt, listed below |

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
| `azathioprine:IM` | 2/2 | 1/1 | 3 | ✅ |
| `azathioprine:NM` | 2/2 | 1/1 | 3 | ✅ |
| `azathioprine:PM` | 2/2 | 1/1 | 3 | ✅ |
| `azathioprine:Unknown` | 1/1 | 1/1 | 2 | ✅ _no CPIC recommendation text for this case_ |
| `clopidogrel:IM` | 2/2 | 2/2 | 3 | ✅ |
| `clopidogrel:NM` | 2/2 | 2/2 | 3 | ✅ |
| `clopidogrel:PM` | 2/2 | 2/2 | 3 | ✅ |
| `clopidogrel:RM` | 2/2 | 2/2 | 3 | ✅ |
| `clopidogrel:URM` | 2/2 | 2/2 | 3 | ✅ |
| `clopidogrel:Unknown` | 1/1 | 2/2 | 2 | ✅ _no CPIC recommendation text for this case_ |
| `codeine:Unknown` | 1/1 | 3/3 | 2 | ✅ _no CPIC recommendation text for this case_ |
| `fluorouracil:IM` | 2/2 | 2/2 | 3 | ✅ |
| `fluorouracil:NM` | 2/2 | 2/2 | 3 | ✅ |
| `fluorouracil:PM` | 2/2 | 2/2 | 3 | ✅ |
| `fluorouracil:Unknown` | 1/1 | 2/2 | 2 | ✅ _no CPIC recommendation text for this case_ |
| `simvastatin:IM` | 2/2 | 2/2 | 4 | ✅ |
| `simvastatin:NM` | 2/2 | 2/2 | 4 | ✅ |
| `simvastatin:PM` | 2/2 | 2/2 | 4 | ✅ |
| `simvastatin:Unknown` | 1/1 | 2/2 | 3 | ✅ _no CPIC recommendation text for this case_ |
| `warfarin:Unknown` | 1/1 | 2/2 | 2 | ✅ _no CPIC recommendation text for this case_ |

## FRAMING sentences (exempt — read them anyway)

These carry no clinical claim, so nothing traces them. That makes this
the list where an unnoticed clinical assertion would hide, which is why
it is printed in full rather than counted.

- `azathioprine:IM` · *summary* — {drug}: {gene} {diplotype} ({phenotype}) — {risk_label}.
- `azathioprine:IM` · *variant_rationale* — The non-reference positions supporting this call were {detected_variants}.
- `azathioprine:IM` · *patient_friendly* — Discuss this with your doctor or pharmacist before making any change to your medicines.
- `simvastatin:IM` · *mechanism* — Its job is to move drugs out of portal blood and into hepatocytes.

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

