# Proposed text changes — not applied, not approved

These 15 draft replacements are discussion material for the owner. They are not a comprehensive repair or a scientific adjudication. Other flagged claims still require review. No current decision transfers to a changed sentence, source or context. Drafts with multiple sentences must be split into new claim keys after final wording is selected.

The owner must review each final entry as a whole, locate the applicable source, and decide whether a revision is acceptable. Do not paste these into production or refresh approval manifests before genuine review and authorized integration.

## Separate source-metadata proposal

For the thiopurine 2025 update, propose replacing the first-author attribution `Relling MV et al.` with `Maillard M et al.` in the citation metadata after source review (PMID 41618934). Keep the version title and 2026 publication year. No metadata or biological definition was edited. This affects source bindings and requires review of the final source and affected entries.

## Other required owner checks without a fabricated replacement

- All 14 stored non-Unknown rationale fields assert that no non-reference variants were detected. No patient-specific evidence in this packet establishes that assertion. The current runtime rebuilds rationale; review the stored claim without inventing calls.
- The azathioprine IM stored label is `Safe` while its recorded source recommends reduced starting doses. Resolve the historical entry context; do not infer safety or hand-edit mapping/biology.
- Source-row identity and population are absent from the store. Candidate matching rows do not authorize choosing an indication or paired phenotype.
- Unknown prose must distinguish lack of usable evidence from a proven absence of genotype, and general biology from an individual result.

## azathioprine:NM / summary / bc23dfa001b3197e

Overbroad safety and missing paired-gene context.

```diff
- Your genetic result indicates that you are a normal metabolizer of azathioprine, which means you are at safe risk for thiopurine-related side effects such as leukopenia, neutropenia, and myelosuppression.
+ The recorded NUDT15 result is normal. A complete azathioprine interpretation also requires the TPMT result; this finding does not establish that treatment is safe.
```

Old binding: `{"content_hash": "9c8fda477cf31858e3d2268464f0a364150b62c4329c3628968a329146bf22c5", "context_hash": "8cdfd12f7611ebdcdeca3db98b6b71512d1a13a5807bcb1d0c1a247aa57affe0", "source_hash": "11068c6d0a5c7e4563487f2533cb945e47e4f468c375b40beb53cf1146a18ab1"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / azathioprine.

## azathioprine:NM / mechanism / 8bc65c1fa2d5e999

Do not turn one recorded gene into normal function in both genes or absence of adverse effects.

```diff
- Your genetic result indicates that you have normal function in the enzymes that handle this process, which means that you are not at increased risk for the side effects associated with this drug.
+ TPMT and NUDT15 influence thiopurine tolerance through different metabolic steps. Normal assessed function does not exclude adverse effects.
```

Old binding: `{"content_hash": "9c8fda477cf31858e3d2268464f0a364150b62c4329c3628968a329146bf22c5", "context_hash": "8cdfd12f7611ebdcdeca3db98b6b71512d1a13a5807bcb1d0c1a247aa57affe0", "source_hash": "11068c6d0a5c7e4563487f2533cb945e47e4f468c375b40beb53cf1146a18ab1"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / azathioprine.

## azathioprine:NM / patient_friendly / 72a7dd28cb3ef0b3

Remove unsupported general safety assurance.

```diff
- You are at safe risk for the side effects of azathioprine, such as low white blood cell count and anemia.
+ This genetic result does not rule out side effects from azathioprine.
```

Old binding: `{"content_hash": "9c8fda477cf31858e3d2268464f0a364150b62c4329c3628968a329146bf22c5", "context_hash": "8cdfd12f7611ebdcdeca3db98b6b71512d1a13a5807bcb1d0c1a247aa57affe0", "source_hash": "11068c6d0a5c7e4563487f2533cb945e47e4f468c375b40beb53cf1146a18ab1"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / azathioprine.

## azathioprine:IM / mechanism / d25611edde121f50

Distinguish TPMT handling of precursors from NUDT15 handling of active nucleotides; source review still required.

```diff
- However, your genetic result may affect how well your body breaks down these active metabolites.
+ Reduced TPMT activity can leave more precursor available for formation of active thioguanine nucleotides.
```

Old binding: `{"content_hash": "165675b3dd76a2a0c4a6785e43cd6fc1044721a29954a418ee130234d700dd01", "context_hash": "60d00ab1d27425db8cb65d4464fced3926cf83fc8532c7301267786f05b014e0", "source_hash": "104f9a935d11a954528b234aa5c9a0348fa250e3a4fd7c8fc1a9670a5ac59e52"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / azathioprine.

## azathioprine:IM / mechanism / 04e210d2e3ece79b

Avoid describing TPMT solely as degradation of active metabolites. Review together with the preceding draft.

```diff
- If your body breaks them down too slowly, it can lead to a buildup of toxic levels, causing myelosuppression.
+ Greater exposure to active thioguanine nucleotides can increase the risk of myelosuppression.
```

Old binding: `{"content_hash": "165675b3dd76a2a0c4a6785e43cd6fc1044721a29954a418ee130234d700dd01", "context_hash": "60d00ab1d27425db8cb65d4464fced3926cf83fc8532c7301267786f05b014e0", "source_hash": "104f9a935d11a954528b234aa5c9a0348fa250e3a4fd7c8fc1a9670a5ac59e52"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / azathioprine.

## clopidogrel:NM / summary / 3a1e82e37a6b1278

Restore scope and remove without-concern reassurance; reviewer must bind indication.

```diff
- Your genetic result suggests that you are a normal metabolizer of clopidogrel, which means that you can take the standard dose without concern.
+ For the applicable indication, CPIC recommends standard-dose clopidogrel for this CYP2C19 phenotype. This does not guarantee effectiveness or absence of adverse effects.
```

Old binding: `{"content_hash": "2782e5e684ff2590a8b00dd172f95451328be04852b222433b158aa77f1290c0", "context_hash": "ebf948b8cccd02052f46943a146060d746f22c7b9ab1cc7d6dfc8038edab53f8", "source_hash": "6f6a5b19cd75138f7d6ff4c977bc04386c63d77b5b46246fe17117a437b7c5da"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / clopidogrel.

## clopidogrel:NM / patient_friendly / bb7a139c086f1b01

Genotype does not guarantee drug effectiveness.

```diff
- This means that you can take the standard dose of clopidogrel without worrying about it not working properly.
+ Your clinician should consider the reason for treatment and other factors when deciding whether clopidogrel is appropriate.
```

Old binding: `{"content_hash": "2782e5e684ff2590a8b00dd172f95451328be04852b222433b158aa77f1290c0", "context_hash": "ebf948b8cccd02052f46943a146060d746f22c7b9ab1cc7d6dfc8038edab53f8", "source_hash": "6f6a5b19cd75138f7d6ff4c977bc04386c63d77b5b46246fe17117a437b7c5da"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / clopidogrel.

## clopidogrel:URM / patient_friendly / 0ada9de748876af4

Remove safe-candidate claim.

```diff
- Your genetic result shows that you are a safe candidate for taking clopidogrel.
+ This CYP2C19 result alone does not establish that clopidogrel is safe or appropriate for you.
```

Old binding: `{"content_hash": "e5615a782817e14353bc03de330bc84cb0786a7b739fe29763c120277b42bfcf", "context_hash": "348d477e7c7ed861a9c217db08bdd7ba4143c29887076e5ae5577024e14a56a2", "source_hash": "6f6a5b19cd75138f7d6ff4c977bc04386c63d77b5b46246fe17117a437b7c5da"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / clopidogrel.

## clopidogrel:URM / mechanism / 82173634a3b2698b

Remove unsupported greater-effectiveness inference.

```diff
- Increased formation of the active metabolite means the drug works more effectively, while reduced formation means the drug may not work as intended.
+ CYP2C19 activity affects active-metabolite formation, but this alone does not predict an individual clinical outcome.
```

Old binding: `{"content_hash": "e5615a782817e14353bc03de330bc84cb0786a7b739fe29763c120277b42bfcf", "context_hash": "348d477e7c7ed861a9c217db08bdd7ba4143c29887076e5ae5577024e14a56a2", "source_hash": "6f6a5b19cd75138f7d6ff4c977bc04386c63d77b5b46246fe17117a437b7c5da"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / clopidogrel.

## clopidogrel:PM / patient_friendly / b42f0e47358d6cf8

Resolve contradictory if-cannot-avoid wording and restore contraindication/indication qualifiers without prescribing.

```diff
- If you can't avoid it, your doctor may recommend a different medication, such as prasugrel or ticagrelor, at the standard dose.
+ For the applicable indication, the CPIC source names alternative antiplatelet therapy when there is no contraindication; your clinician must assess these conditions.
```

Old binding: `{"content_hash": "180ea78ddeb92bc4ed734d787813f5d754e511f2a89ab675537b703637f14560", "context_hash": "e5f2c49916f5edcd26d4381616af2be7219fa44ea1b09ccb72a772fd0f04f657", "source_hash": "72c0b3b4ddbc9b7e1721e4e5dbc37dbea010e0e66a4c9aba45c6acf725a7cae0"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / clopidogrel.

## fluorouracil:NM / mechanism / f6a33adcf03be61a

Normal-risk category is not a general safety prediction.

```diff
- If you have normal DPD activity, the standard dose of fluorouracil is likely to be safe.
+ Normal assessed DPD function does not rule out severe adverse effects from fluorouracil.
```

Old binding: `{"content_hash": "2774def9190902cd0d3a06a5ebe858bb0cd7c73aaa45ec5e35408449f7b1c428", "context_hash": "2696f2b3684005c9817d52ffdff77b6b9bcafdbe67acb126bd7118928a710b4d", "source_hash": "00c7a9f3b933989fca8c84397c3ab44b733ff80c545554dca03d5eaa3b136a6e"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / fluorouracil.

## fluorouracil:NM / patient_friendly / cfb556184673f3c9

Remove without-any-problems reassurance.

```diff
- You should be able to take the standard dose of fluorouracil without any problems.
+ Side effects can still occur, and treatment decisions require clinical assessment.
```

Old binding: `{"content_hash": "2774def9190902cd0d3a06a5ebe858bb0cd7c73aaa45ec5e35408449f7b1c428", "context_hash": "2696f2b3684005c9817d52ffdff77b6b9bcafdbe67acb126bd7118928a710b4d", "source_hash": "00c7a9f3b933989fca8c84397c3ab44b733ff80c545554dca03d5eaa3b136a6e"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / fluorouracil.

## simvastatin:NM / patient_friendly / bdaf0b2506069fe3

Do not infer absence of all genetic variation from a bounded normal-function result.

```diff
- You don't have a genetic variation that affects how your body handles simvastatin.
+ The assessed SLCO1B1 result corresponds to normal transporter function; this does not exclude other causes of muscle symptoms.
```

Old binding: `{"content_hash": "b6dd45959e8ed30ff61b1a718e8a2b4737ec5fb935090db2a6214adb1c65f8bd", "context_hash": "051ce9608867035acaf65bc548db0ed8af6ef3e24fa617783c440b01380b387a", "source_hash": "0d3f7124a484ee3fbd4e8ef1ddf9702d7f63d0327f50c02ff92204a2c90584f3"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / simvastatin.

## codeine:Unknown / summary / 439af963735c02e8

Explicit capability limitation; no new calling functionality.

```diff
- Your genetic result for codeine is unknown, so we cannot explain how it will be handled by your body.
+ This application does not provide CYP2D6-based codeine guidance because it does not call the required copy-number and structural variation.
```

Old binding: `{"content_hash": "49c331da80040518ef10e648a9b40277ebcc43aadbde8cf4514d66e60e609aad", "context_hash": "824c9e2c31759cebebae11c7d28fba910091bec8e144e8d3a74831c419188721", "source_hash": "a0efc23c38910c7da7233884eb247a3309625295b871bc5e40200bf2eb5e1cf5"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / codeine.

## warfarin:Unknown / summary / 9a20a93a47a3d00e

Explicit capability limitation; no new dosing functionality.

```diff
- Your genetic result does not provide enough information to make a recommendation for warfarin dosing.
+ This application has no validated automated warfarin-dose implementation and does not provide a dosing recommendation.
```

Old binding: `{"content_hash": "5e2aec107c44fa6d87c6292ca7a0fd2951fb6aeff905002bbf19ac2b80c1ff80", "context_hash": "797054b6acbdf8d18c79bf35d35e72b01e8f38f1ce84b85b79a34fb176bf4ca2", "source_hash": "9d670f0e43b50dac6f140024d15380686692773c9012727c150ca238605f7c2e"}`

Status: **UNREVIEWED_DRAFT_NOT_APPLIED**. Primary-source aids: `SOURCE-VERIFICATION.md` / warfarin.
