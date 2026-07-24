# Model selection benchmark

**Generated:** 2026-07-24T04:36:21.497418+00:00  
**Provider:** `nvidia`  
**Candidates:** 5  
**Cases per model:** 3 (one each: Safe, Adjust Dosage, Toxic)

Ranked by guard pass rate, then provenance pass rate, then JSON
reliability. Latency and tokens are tiebreakers only — a fast model that
fabricates a dose is worse than a slow one that does not, because
fabrication is the failure this project exists to prevent.

## Result

**Recommended: `meta/llama-3.1-8b-instruct`** — guard 100%, provenance 0%, JSON 100%, 2.4s/case.

| Rank | Model | JSON ok | Guard pass | Provenance pass | Latency | Tokens |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `meta/llama-3.1-8b-instruct` ⭐ | 100% | 100% | 0% | 2.4s | 4807 |
| 2 | `meta/llama-4-maverick-17b-128e-instruct` | 100% | 67% | 0% | 2.5s | 4603 |
| 3 | `microsoft/phi-3.5-moe-instruct` | 0% | 0% | 0% | 0.1s | — |
| 4 | `ibm/granite-3.0-8b-instruct` | 0% | 0% | 0% | 0.5s | — |
| 5 | `mistralai/mixtral-8x7b-instruct-v0.1` | 0% | 0% | 0% | 51.7s | — |

## Detail

### `meta/llama-3.1-8b-instruct`

**Safe** (azathioprine:IM) — JSON ✅ (response_format) · guard ✅ · provenance ❌ · 3.4s
  - provenance unverified: MECHANISM:Reduced or absent function in these enzy, MECHANISM:The patient has an intermediate metaboli, CLINICAL:If you're taking {drug} and your doctor , CLINICAL:Your doctor will adjust the dose based o

  ```
  summary: Initiate therapy with reduced starting doses if the standard starting dose is ≥2 mg/kg/day. Dose reduction might not be necessary if the starting dose is already below standard.
  mechanism: Thiopurine S-methyltransferase, an enzyme that methylates thiopurine compounds, and a nucleotide diphosphatase, which dephosphorylates active thioguanine nucleotides, act as brakes on the pathway that produces active metabolites. Reduced or absent function in these enzymes removes a brake, leading to bone-marrow suppression.
  variant_rationale: The patient has an intermediate metabolizer phenotype, which means they have moderate to high erythrocyte concentrations of TGN metabolites and low concentrations of MeMPNs compared to normal metabolizers.
  patient_friendly: If you're taking {drug} and your doctor is considering a standard dose of ≥2 mg/kg/day, you may need a lower dose. This is because your body processes the medicine a bit differently. Your doctor will adjust the dose based on how your body is responding to the medicine and your disease-specific guidelines. It may take a few weeks to reach the right dose. Be sure to talk to your doctor or pharmacist about your specific situation.
  ```

**Adjust Dosage** (fluorouracil:IM) — JSON ✅ (response_format) · guard ✅ · provenance ❌ · 1.9s
  - provenance unverified: MECHANISM:The patient has an intermediate metaboli, CLINICAL:This may increase the risk of severe or , CLINICAL:Reduced DPD activity slows inactivation,, CLINICAL:The patient's intermediate metabolizer p

  ```
  summary: The patient has an intermediate metabolizer phenotype for the DPYD gene, which is associated with a decreased activity of the dihydropyrimidine dehydrogenase enzyme. This may increase the risk of severe or fatal toxicity when treated with fluorouracil.
  mechanism: DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism. DPD is responsible for breaking down fluorouracil into inactive metabolites. Reduced DPD activity slows inactivation, leading to higher exposure to active drug and increased risk of toxicity.
  variant_rationale: The patient's intermediate metabolizer phenotype is associated with decreased DPD activity, which may increase the risk of severe or fatal toxicity when treated with fluorouracil.
  patient_friendly: Your body breaks down fluorouracil differently than most people. This means you may be at higher risk for serious side effects. Your doctor or pharmacist can help you understand what this means for your treatment and how to stay safe.
  ```

**Toxic** (azathioprine:PM) — JSON ✅ (response_format) · guard ✅ · provenance ❌ · 2.0s
  - provenance unverified: CLINICAL:The patient has a Poor Metabolizer pheno, MECHANISM:Reduced or absent TPMT function removes , MECHANISM:The patient's {phenotype} phenotype for , CLINICAL:This means you're at higher risk for ser

  ```
  summary: The patient has a Poor Metabolizer phenotype for azathioprine, which means they have a greatly increased risk of thiopurine-related leukopenia, neutropenia, and myelosuppression.
  mechanism: Azathioprine is a prodrug that is converted to mercaptopurine and then into thioguanine nucleotides (TGNs). TPMT acts as a brake on this pathway by methylating precursors away from TGN formation. Reduced or absent TPMT function removes this brake, allowing more TGN to accumulate in haematopoietic cells, leading to bone-marrow suppression.
  variant_rationale: The patient's {phenotype} phenotype for azathioprine is due to {diplotype} of the TPMT gene.
  patient_friendly: Your body doesn't break down azathioprine as well as most people's do. This means you're at higher risk for serious side effects like low white blood cell count. Your doctor or pharmacist can help you choose a different medicine that's safer for you.
  ```

### `meta/llama-4-maverick-17b-128e-instruct`

**Safe** (azathioprine:IM) — JSON ✅ (response_format) · guard ✅ · provenance ❌ · 2.3s
  - provenance unverified: MECHANISM:The patient is an Intermediate Metaboliz, CLINICAL:Reduced function, as seen in Intermediat, CLINICAL:The {gene} {diplotype} results in Interm, MECHANISM:Your genetic test result shows that you 

  ```
  summary: The patient is an Intermediate Metabolizer of {drug} due to their {gene} {diplotype}. This results in an increased risk of myelosuppression.
  mechanism: {gene} encodes an enzyme that acts as a brake on the pathway that produces the active metabolites of {drug}. Reduced function, as seen in Intermediate Metabolizers, removes this brake, leading to higher levels of active metabolites and an increased risk of toxicity, specifically myelosuppression.
  variant_rationale: The {gene} {diplotype} results in Intermediate Metabolizer phenotype, which is associated with moderate to high levels of active {drug} metabolites and an increased risk of leukopenia, neutropenia, and myelosuppression.
  patient_friendly: Your genetic test result shows that you are an Intermediate Metabolizer of {drug}. This means that you may be more likely to experience side effects from {drug}, such as a decrease in blood cells. Your doctor may start you on a lower dose and monitor you closely to adjust the dose as needed. Please speak with your doctor or pharmacist to understand how this result affects your treatment plan.
  ```

**Adjust Dosage** (fluorouracil:IM) — JSON ✅ (response_format) · guard ❌ · provenance ❌ · 2.2s
  - guard caught: slot:{phenotype_label}
  - provenance unverified: CLINICAL:The patient's {gene} {diplotype} results, CLINICAL:The recommended action is to reduce the , CLINICAL:Reduced DPD activity slows inactivation,, CLINICAL:The patient's {phenotype_label} phenotyp

  ```
  summary: The patient's {gene} {diplotype} results in Intermediate Metabolizer phenotype, indicating decreased DPD activity and increased risk for severe toxicity when treated with {drug}. The recommended action is to reduce the starting dose.
  mechanism: {gene} encodes dihydropyrimidine dehydrogenase (DPD), the enzyme responsible for breaking down {drug} into inactive metabolites. Reduced DPD activity slows inactivation, increasing exposure to active drug and leading to more severe toxicity.
  variant_rationale: The patient's {phenotype_label} phenotype is associated with decreased DPD activity, which increases the risk of severe or fatal drug toxicity when treated with {drug}.
  patient_friendly: Your genetic test result shows that your body has a harder time breaking down {drug}. This means you are at a higher risk of having severe side effects from {drug}. To manage this risk, your doctor will likely start you on a lower dose and adjust it based on how you respond. Please speak with your doctor or pharmacist.
  ```

**Toxic** (azathioprine:PM) — JSON ✅ (response_format) · guard ✅ · provenance ❌ · 2.9s
  - provenance unverified: MECHANISM:The CPIC recommends considering alternat, MECHANISM:{gene} encodes an enzyme that methylates, MECHANISM:A Poor Metabolizer phenotype means this , CLINICAL:The {gene} {diplotype} results in a Poor

  ```
  summary: The CPIC recommends considering alternative nonthiopurine immunosuppressant therapy for {drug} due to {gene} {diplotype} resulting in a Poor Metabolizer phenotype.
  mechanism: {gene} encodes an enzyme that methylates {drug} and its metabolites, diverting them away from forming active species. A Poor Metabolizer phenotype means this enzyme has reduced or absent function, leading to increased levels of active metabolites.
  variant_rationale: The {gene} {diplotype} results in a Poor Metabolizer phenotype, greatly increasing the risk of {drug}-related toxicity, including leukopenia, neutropenia, and potentially fatal myelosuppression.
  patient_friendly: Your genetic test result shows that you are a Poor Metabolizer of {drug} due to your {gene} {diplotype}. This means you are at a higher risk of serious side effects from {drug}. Your doctor may consider an alternative treatment. Please speak with your doctor or pharmacist.
  ```

### `microsoft/phi-3.5-moe-instruct`

**Safe** (azathioprine:IM) — ❌ error: nvidia: model not available. Error code: 404 - {'status': 404, 'title': 'Not Found', 'detail': "Function 'e6cab982-62f4-481e-9a7a-3dedb87dbd01': Not found for account 'bOjSj-75mqCCx4Ybe7K4-upgZXjdk-o4
**Adjust Dosage** (fluorouracil:IM) — ❌ error: nvidia: model not available. Error code: 404 - {'status': 404, 'title': 'Not Found', 'detail': "Function 'e6cab982-62f4-481e-9a7a-3dedb87dbd01': Not found for account 'bOjSj-75mqCCx4Ybe7K4-upgZXjdk-o4
**Toxic** (azathioprine:PM) — ❌ error: nvidia: model not available. Error code: 404 - {'status': 404, 'title': 'Not Found', 'detail': "Function 'e6cab982-62f4-481e-9a7a-3dedb87dbd01': Not found for account 'bOjSj-75mqCCx4Ybe7K4-upgZXjdk-o4
### `ibm/granite-3.0-8b-instruct`

**Safe** (azathioprine:IM) — ❌ error: nvidia: model not available. Error code: 404 - {'status': 404, 'title': 'Not Found', 'detail': "Function '5a24a4f0-2d59-46b3-ac65-42307f2633d1': Not found for account 'bOjSj-75mqCCx4Ybe7K4-upgZXjdk-o4
**Adjust Dosage** (fluorouracil:IM) — ❌ error: nvidia: model not available. Error code: 404 - {'status': 404, 'title': 'Not Found', 'detail': "Function '5a24a4f0-2d59-46b3-ac65-42307f2633d1': Not found for account 'bOjSj-75mqCCx4Ybe7K4-upgZXjdk-o4
**Toxic** (azathioprine:PM) — ❌ error: nvidia: model not available. Error code: 404 - {'status': 404, 'title': 'Not Found', 'detail': "Function '5a24a4f0-2d59-46b3-ac65-42307f2633d1': Not found for account 'bOjSj-75mqCCx4Ybe7K4-upgZXjdk-o4
### `mistralai/mixtral-8x7b-instruct-v0.1`

**Safe** (azathioprine:IM) — ❌ error: nvidia: call failed. Error code: 500 - {'error': {'message': 'EngineCore encountered an issue. See stack trace (above) for the root cause.', 'type': 'Internal Server Error', 'param': None, 'code': 500
**Adjust Dosage** (fluorouracil:IM) — ❌ error: nvidia: request timed out after 120s.
**Toxic** (azathioprine:PM) — ❌ error: nvidia: call failed. Error code: 500 - {'error': {'message': 'EngineCore encountered an issue. See stack trace (above) for the root cause.', 'type': 'Internal Server Error', 'param': None, 'code': 500
## How to read this

- **Guard pass** — the faithfulness guard found no fabricated dose,
  number, rsID, allele, gene or drug. This is the primary criterion.
- **Provenance pass** — every clinical-claim sentence traces to the CPIC
  source or a declared paraphrase. Stricter than the guard.
- **JSON ok** — the output parsed into the four-field schema, after
  stripping any reasoning block and unwrapping any code fence.

Raw outputs above are captured verbatim. They are candidate generations,
not shipped content — the chosen model is re-run through the full
pregeneration pipeline (guard, retry, provenance) before anything ships.

