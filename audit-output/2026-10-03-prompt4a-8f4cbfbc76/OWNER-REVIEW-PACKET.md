# Owner review packet — no decisions applied

Machine-prepared retrieval and binding inventory. Candidate passages are not proof of support. Every claim, including existing bulk decisions, is listed. The JSON inventory retains exact fields and complete records.

**55 pending human claim decisions; 20 unread entries.** Existing human-labelled decisions are historical bulk records, not individual reads or expert approval.

Read `HANDOFF.md` first. Primary paper versions, locations, short spans and access limitations are in `SOURCE-VERIFICATION.md`. All review fields in `reviewer-response-template.json` remain null.

## azathioprine:IM

Gene/context: **TPMT / IM**; stored label `Safe` (historical; no broad safety endorsement).
Relevant genes: TPMT, NUDT15. A complete drug-level interpretation requires acceptable evidence for both TPMT and NUDT15.

Primary source: [azathioprine source record](SOURCE-VERIFICATION.md#azathioprine); 2025 update; epub 2026-01-31; April 2026 issue, 119(4):916–927. Official advance PDF accepted 2026-01-08.
Pinned guideline: `PA166104933`, version `59`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `165675b3dd76a2a0c4a6785e43cd6fc1044721a29954a418ee130234d700dd01`
- source_hash: `104f9a935d11a954528b234aa5c9a0348fa250e3a4fd7c8fc1a9670a5ac59e52`
- context_hash: `60d00ab1d27425db8cb65d4464fced3926cf83fc8532c7301267786f05b014e0`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

4 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"Initiate therapy with reduced starting doses (30-80% of standard starting dose) if standard starting dose is ≥2 mg/kg/day. If starting dose is already below standard starting dose, dose reduction might not be necessary. During therapy, adjust the doses of azathioprine based on the degree of myelosuppression and disease-specific guidelines. It usually takes at least 2-4 weeks of stable dosing to reach steady state after each dose adjustment."
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166297264`; population `general`; lookup `[{"TPMT": "Possible Intermediate Metabolizer", "NUDT15": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297271`; population `general`; lookup `[{"TPMT": "Intermediate Metabolizer", "NUDT15": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297276`; population `general`; lookup `[{"TPMT": "Normal Metabolizer", "NUDT15": "Intermediate Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297280`; population `general`; lookup `[{"TPMT": "Normal Metabolizer", "NUDT15": "Possible Intermediate Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result may affect how well you tolerate azathioprine. You are an Intermediate Metabolizer, which means you may have a moderate to high risk of experiencing myelosuppression, a condition that can cause low blood cell counts.",
  "mechanism": "Azathioprine is a medication that works by producing active metabolites that can affect the immune system. However, your genetic result may affect how well your body breaks down these active metabolites. If your body breaks them down too slowly, it can lead to a buildup of toxic levels, causing myelosuppression.",
  "variant_rationale": "PharmCAT called TPMT as {diplotype}, which corresponds to a Intermediate Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "If you're taking azathioprine, your doctor may need to start you on a lower dose to help your body handle the medication. They will also need to monitor your blood cell counts closely to make sure you're not experiencing any side effects. It may take a few weeks for your body to adjust to the new dose, so be patient and work closely with your doctor to find the right balance."
}
```

### bf52384a1f3e1cca — summary

**Exact sentence / claim to assess:**

Your genetic result may affect how well you tolerate azathioprine.

Sentence UTF-8 SHA-256: `f96791367b790a8ac73a2eea5d6df5c72c05eced7983b9c129ef44980336d69b`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result may affect how well you tolerate azathioprine.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847824+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 33–36 (How the drug is handled):

```text
Azathioprine is a prodrug that is converted to mercaptopurine and then, through
several steps, into thioguanine nucleotides (TGNs). TGNs are the active species:
they are incorporated into DNA, and that incorporation produces both the
intended immunosuppressive effect and the drug's principal toxicity.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- LEGACY_CONTEXT: stored label Safe coexists with a reduced-starting-dose recommendation; do not reinterpret that historical label as safety or approve it without resolving the context.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### baac17791617cac2 — summary

**Exact sentence / claim to assess:**

You are an Intermediate Metabolizer, which means you may have a moderate to high risk of experiencing myelosuppression, a condition that can cause low blood cell counts.

Sentence UTF-8 SHA-256: `f099d7f191f5cf45343e8fa4783e455db8f21f36e8d62970976797d003bcdee3`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "You are an Intermediate Metabolizer, which means you may have a moderate to high risk of experiencing myelosuppression, a condition that can cause low blood cell counts.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847976+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 43–47 (Why altered function changes the outcome):

```text
- **Reduced or absent TPMT (or NUDT15) function** removes a brake. More
  thioguanine nucleotide accumulates in haematopoietic cells for the same
  administered amount. The characteristic consequence is bone-marrow
  suppression: leukopenia, neutropenia, and in severe cases life-threatening
  myelosuppression. This is a **toxicity** problem, not a loss-of-effect problem.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- LEGACY_CONTEXT: stored label Safe coexists with a reduced-starting-dose recommendation; do not reinterpret that historical label as safety or approve it without resolving the context.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### bfd63de6cf9b36ef — mechanism

**Exact sentence / claim to assess:**

Azathioprine is a medication that works by producing active metabolites that can affect the immune system.

Sentence UTF-8 SHA-256: `3793e9cf27a05d57c465d2d6b0d40ed15af1e537c9b4307c2ffce216922df5df`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Azathioprine is a medication that works by producing active metabolites that can affect the immune system.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "",
  "basis_citation": "Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934",
  "escalated": true,
  "escalation_reasons": [
    "no-source"
  ],
  "escalation_detail": [
    "no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against."
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 22–24 (What the gene products do):

```text
*TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that
methylates thiopurine compounds and so diverts them away from the pathway that
produces active metabolites.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- LEGACY_CONTEXT: stored label Safe coexists with a reduced-starting-dose recommendation; do not reinterpret that historical label as safety or approve it without resolving the context.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### d25611edde121f50 — mechanism

**Exact sentence / claim to assess:**

However, your genetic result may affect how well your body breaks down these active metabolites.

Sentence UTF-8 SHA-256: `f7f5b6e52908389a8920e51f2aa3c513ef2af0c190ff070d863a65bbd8d670ec`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "However, your genetic result may affect how well your body breaks down these active metabolites.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates thiopurine compounds and so diverts them away from the pathway that produces active metabolites.",
  "basis_citation": "Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 22–24 (What the gene products do):

```text
*TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that
methylates thiopurine compounds and so diverts them away from the pathway that
produces active metabolites.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- LEGACY_CONTEXT: stored label Safe coexists with a reduced-starting-dose recommendation; do not reinterpret that historical label as safety or approve it without resolving the context.
- AMBIGUOUS_MECHANISM: distinguish TPMT diversion of precursors from NUDT15 handling of active nucleotides; broad degradation wording requires review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 04e210d2e3ece79b — mechanism

**Exact sentence / claim to assess:**

If your body breaks them down too slowly, it can lead to a buildup of toxic levels, causing myelosuppression.

Sentence UTF-8 SHA-256: `c36118f233b5e5240e0340e221966dd5e97cb37f6b3e5f59a19a9d05ca88fa95`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "If your body breaks them down too slowly, it can lead to a buildup of toxic levels, causing myelosuppression.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "",
  "basis_citation": "",
  "escalated": true,
  "escalation_reasons": [
    "no-source"
  ],
  "escalation_detail": [
    "no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against."
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 43–47 (Why altered function changes the outcome):

```text
- **Reduced or absent TPMT (or NUDT15) function** removes a brake. More
  thioguanine nucleotide accumulates in haematopoietic cells for the same
  administered amount. The characteristic consequence is bone-marrow
  suppression: leukopenia, neutropenia, and in severe cases life-threatening
  myelosuppression. This is a **toxicity** problem, not a loss-of-effect problem.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- LEGACY_CONTEXT: stored label Safe coexists with a reduced-starting-dose recommendation; do not reinterpret that historical label as safety or approve it without resolving the context.
- AMBIGUOUS_MECHANISM: distinguish TPMT diversion of precursors from NUDT15 handling of active nucleotides; broad degradation wording requires review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### bb4bf3bcbbdde104 — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called TPMT as {diplotype}, which corresponds to a Intermediate Metabolizer result.

Sentence UTF-8 SHA-256: `95d1a455858463bf606a8caf9ef90a655f420ba9a0407e9d8ae1a58e825b70b4`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called TPMT as {diplotype}, which corresponds to a Intermediate Metabolizer result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847978+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 22–24 (What the gene products do):

```text
*TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that
methylates thiopurine compounds and so diverts them away from the pathway that
produces active metabolites.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- LEGACY_CONTEXT: stored label Safe coexists with a reduced-starting-dose recommendation; do not reinterpret that historical label as safety or approve it without resolving the context.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 9f181da2471268dc — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847979+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- LEGACY_CONTEXT: stored label Safe coexists with a reduced-starting-dose recommendation; do not reinterpret that historical label as safety or approve it without resolving the context.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 0fd92512d5b39411 — patient_friendly

**Exact sentence / claim to assess:**

If you're taking azathioprine, your doctor may need to start you on a lower dose to help your body handle the medication.

Sentence UTF-8 SHA-256: `07240455b1d1c924048fc7d9dd9d25f9da1f96a6b8d798f753159836b4979c0f`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you're taking azathioprine, your doctor may need to start you on a lower dose to help your body handle the medication.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847986+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 59–64 (Notes for the explanation layer):

```text
- Frame reduced function as *accumulation of active metabolite*, with bone
  marrow as the tissue at risk.
- Do not state dose reductions, percentages, or monitoring intervals here — all
  of that is CPIC's, delivered through PharmCAT at runtime.
- Mercaptopurine and thioguanine are handled by the same pathway, but only
  discuss the drug actually being analysed.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- LEGACY_CONTEXT: stored label Safe coexists with a reduced-starting-dose recommendation; do not reinterpret that historical label as safety or approve it without resolving the context.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 0e03ddc88b11de8b — patient_friendly

**Exact sentence / claim to assess:**

They will also need to monitor your blood cell counts closely to make sure you're not experiencing any side effects.

Sentence UTF-8 SHA-256: `332b8c093dd35469d4b5cb117dfca0bf1f66f36bf027ba38d498486bb2c77fe3`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "They will also need to monitor your blood cell counts closely to make sure you're not experiencing any side effects.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847987+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 43–47 (Why altered function changes the outcome):

```text
- **Reduced or absent TPMT (or NUDT15) function** removes a brake. More
  thioguanine nucleotide accumulates in haematopoietic cells for the same
  administered amount. The characteristic consequence is bone-marrow
  suppression: leukopenia, neutropenia, and in severe cases life-threatening
  myelosuppression. This is a **toxicity** problem, not a loss-of-effect problem.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- LEGACY_CONTEXT: stored label Safe coexists with a reduced-starting-dose recommendation; do not reinterpret that historical label as safety or approve it without resolving the context.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### d9398bd7f3036b9f — patient_friendly

**Exact sentence / claim to assess:**

It may take a few weeks for your body to adjust to the new dose, so be patient and work closely with your doctor to find the right balance.

Sentence UTF-8 SHA-256: `0e2d18f97a70bb44601e94f98e967d865e95846d9f4afa0b6cd628450b50d431`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "It may take a few weeks for your body to adjust to the new dose, so be patient and work closely with your doctor to find the right balance.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847989+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 59–64 (Notes for the explanation layer):

```text
- Frame reduced function as *accumulation of active metabolite*, with bone
  marrow as the tissue at risk.
- Do not state dose reductions, percentages, or monitoring intervals here — all
  of that is CPIC's, delivered through PharmCAT at runtime.
- Mercaptopurine and thioguanine are handled by the same pathway, but only
  discuss the drug actually being analysed.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- LEGACY_CONTEXT: stored label Safe coexists with a reduced-starting-dose recommendation; do not reinterpret that historical label as safety or approve it without resolving the context.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## azathioprine:NM

Gene/context: **NUDT15 / NM**; stored label `Safe` (historical; no broad safety endorsement).
Relevant genes: TPMT, NUDT15. A complete drug-level interpretation requires acceptable evidence for both TPMT and NUDT15.

Primary source: [azathioprine source record](SOURCE-VERIFICATION.md#azathioprine); 2025 update; epub 2026-01-31; April 2026 issue, 119(4):916–927. Official advance PDF accepted 2026-01-08.
Pinned guideline: `PA166104933`, version `59`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `9c8fda477cf31858e3d2268464f0a364150b62c4329c3628968a329146bf22c5`
- source_hash: `11068c6d0a5c7e4563487f2533cb945e47e4f468c375b40beb53cf1146a18ab1`
- context_hash: `8cdfd12f7611ebdcdeca3db98b6b71512d1a13a5807bcb1d0c1a247aa57affe0`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

1 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"Initiate therapy with standard starting dose (e.g., 2 mg/kg/day for autoimmune diseases). During therapy, adjust doses of azathioprine based on disease-specific guidelines. It usually takes at least 2 weeks to reach steady state after each dose adjustment."
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166297277`; population `general`; lookup `[{"TPMT": "Normal Metabolizer", "NUDT15": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result indicates that you are a normal metabolizer of azathioprine, which means you are at safe risk for thiopurine-related side effects such as leukopenia, neutropenia, and myelosuppression.",
  "mechanism": "Azathioprine is a prodrug that is converted into active metabolites, which are then incorporated into DNA. Your genetic result indicates that you have normal function in the enzymes that handle this process, which means that you are not at increased risk for the side effects associated with this drug.",
  "variant_rationale": "PharmCAT called NUDT15 as {diplotype}, which corresponds to a Normal Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "You are at safe risk for the side effects of azathioprine, such as low white blood cell count and anemia. This is because your body handles the medication in a normal way. However, it's always best to speak with your doctor or pharmacist to confirm this information and get personalized advice."
}
```

### bc23dfa001b3197e — summary

**Exact sentence / claim to assess:**

Your genetic result indicates that you are a normal metabolizer of azathioprine, which means you are at safe risk for thiopurine-related side effects such as leukopenia, neutropenia, and myelosuppression.

Sentence UTF-8 SHA-256: `d8ea1f55c8ad18d62d1cbf058e6e474445caa9040343b035efc8a9095cda3cc6`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result indicates that you are a normal metabolizer of azathioprine, which means you are at safe risk for thiopurine-related side effects such as leukopenia, neutropenia, and myelosuppression.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847991+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 43–47 (Why altered function changes the outcome):

```text
- **Reduced or absent TPMT (or NUDT15) function** removes a brake. More
  thioguanine nucleotide accumulates in haematopoietic cells for the same
  administered amount. The characteristic consequence is bone-marrow
  suppression: leukopenia, neutropenia, and in severe cases life-threatening
  myelosuppression. This is a **toxicity** problem, not a loss-of-effect problem.
```

Flags (automated/editorial triage, no adjudication):

- OVERBROAD_SAFETY: normal or other assessed PGx function does not establish general safety or assured efficacy; human reassessment requested, including existing bulk decisions.
- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 6ef4284f6d79dab2 — mechanism

**Exact sentence / claim to assess:**

Azathioprine is a prodrug that is converted into active metabolites, which are then incorporated into DNA.

Sentence UTF-8 SHA-256: `d5902ef40b44fe7e13ddd15f98e08d4dacb82dd0cb62f22b1076c4eae8f124e7`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Azathioprine is a prodrug that is converted into active metabolites, which are then incorporated into DNA.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "NUDT15* encodes a nucleotide diphosphatase that dephosphorylates active thioguanine nucleotides, limiting how much active metabolite is incorporated into DNA.",
  "basis_citation": "Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 33–36 (How the drug is handled):

```text
Azathioprine is a prodrug that is converted to mercaptopurine and then, through
several steps, into thioguanine nucleotides (TGNs). TGNs are the active species:
they are incorporated into DNA, and that incorporation produces both the
intended immunosuppressive effect and the drug's principal toxicity.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 8bc65c1fa2d5e999 — mechanism

**Exact sentence / claim to assess:**

Your genetic result indicates that you have normal function in the enzymes that handle this process, which means that you are not at increased risk for the side effects associated with this drug.

Sentence UTF-8 SHA-256: `cc3b4116bfb8607272f57f446481b98ae8fbcc56cdc32b8eefd34dce2f677abc`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Your genetic result indicates that you have normal function in the enzymes that handle this process, which means that you are not at increased risk for the side effects associated with this drug.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "",
  "basis_citation": "",
  "escalated": true,
  "escalation_reasons": [
    "no-source"
  ],
  "escalation_detail": [
    "no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against."
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 59–64 (Notes for the explanation layer):

```text
- Frame reduced function as *accumulation of active metabolite*, with bone
  marrow as the tissue at risk.
- Do not state dose reductions, percentages, or monitoring intervals here — all
  of that is CPIC's, delivered through PharmCAT at runtime.
- Mercaptopurine and thioguanine are handled by the same pathway, but only
  discuss the drug actually being analysed.
```

Flags (automated/editorial triage, no adjudication):

- OVERBROAD_SAFETY: normal or other assessed PGx function does not establish general safety or assured efficacy; human reassessment requested, including existing bulk decisions.
- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 5d04b04c4cd3d224 — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called NUDT15 as {diplotype}, which corresponds to a Normal Metabolizer result.

Sentence UTF-8 SHA-256: `ad6309d21c6a624af8735b0d63a35ccedd7d4a273145820b9b6f8cbb3db82ccd`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called NUDT15 as {diplotype}, which corresponds to a Normal Metabolizer result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847993+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 26–29 (What the gene products do):

```text
*NUDT15* encodes a nucleotide diphosphatase that dephosphorylates active
thioguanine nucleotides, limiting how much active metabolite is incorporated
into DNA. CPIC's thiopurine guideline covers both genes together, because either
one can independently limit a patient's tolerance.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 9fecaac93dfc099d — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847994+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 72a7dd28cb3ef0b3 — patient_friendly

**Exact sentence / claim to assess:**

You are at safe risk for the side effects of azathioprine, such as low white blood cell count and anemia.

Sentence UTF-8 SHA-256: `4cb9e8b6e26f4848e4960411b78345e203b6b4e9b518a4f4e0d86354875f90a5`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "You are at safe risk for the side effects of azathioprine, such as low white blood cell count and anemia.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847995+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 33–36 (How the drug is handled):

```text
Azathioprine is a prodrug that is converted to mercaptopurine and then, through
several steps, into thioguanine nucleotides (TGNs). TGNs are the active species:
they are incorporated into DNA, and that incorporation produces both the
intended immunosuppressive effect and the drug's principal toxicity.
```

Flags (automated/editorial triage, no adjudication):

- OVERBROAD_SAFETY: normal or other assessed PGx function does not establish general safety or assured efficacy; human reassessment requested, including existing bulk decisions.
- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 43cec33f8bd4058e — patient_friendly

**Exact sentence / claim to assess:**

This is because your body handles the medication in a normal way.

Sentence UTF-8 SHA-256: `fe392f951641c8fdf00a8ac2855d315799769ca6b0675d2ba13c9d534a0c1d50`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This is because your body handles the medication in a normal way.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847997+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 1ee0f812d6c57ad4 — patient_friendly

**Exact sentence / claim to assess:**

However, it's always best to speak with your doctor or pharmacist to confirm this information and get personalized advice.

Sentence UTF-8 SHA-256: `a0f7590c39ca5dfc8d8f326a7d748b6ff7866586896a63de0f54bdc5bd3318ed`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "However, it's always best to speak with your doctor or pharmacist to confirm this information and get personalized advice.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847998+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## azathioprine:PM

Gene/context: **TPMT / PM**; stored label `Toxic` (historical; no broad safety endorsement).
Relevant genes: TPMT, NUDT15. A complete drug-level interpretation requires acceptable evidence for both TPMT and NUDT15.

Primary source: [azathioprine source record](SOURCE-VERIFICATION.md#azathioprine); 2025 update; epub 2026-01-31; April 2026 issue, 119(4):916–927. Official advance PDF accepted 2026-01-08.
Pinned guideline: `PA166104933`, version `59`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `ca9271f3b88e589c691a0395db41421c4cf288b62a576b9a10065c45ee9a844a`
- source_hash: `a9f90422a5fc8d4604a44393b2784c8a7278a229218e6242238bdfedb30e22fb`
- context_hash: `6b19b184ca07854053d292d3512f39aefeec92beb4078dd9e2a17c86f5cfef94`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

11 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"Consider alternative nonthiopurine immunosuppressant therapy."
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166297265`; population `general`; lookup `[{"TPMT": "Possible Intermediate Metabolizer", "NUDT15": "Poor Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297272`; population `general`; lookup `[{"TPMT": "Intermediate Metabolizer", "NUDT15": "Poor Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297279`; population `general`; lookup `[{"TPMT": "Normal Metabolizer", "NUDT15": "Poor Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297283`; population `general`; lookup `[{"TPMT": "Poor Metabolizer", "NUDT15": "Intermediate Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297284`; population `general`; lookup `[{"TPMT": "Poor Metabolizer", "NUDT15": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166429462`; population `None`; lookup `[{"TPMT": "Poor Metabolizer", "NUDT15": "Indeterminate"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166429461`; population `None`; lookup `[{"TPMT": "Indeterminate", "NUDT15": "Poor Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166429765`; population `None`; lookup `[{"TPMT": "Poor Metabolizer", "NUDT15": "No Result"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166429744`; population `None`; lookup `[{"TPMT": "No Result", "NUDT15": "Poor Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297286`; population `general`; lookup `[{"TPMT": "Poor Metabolizer", "NUDT15": "Poor Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297287`; population `general`; lookup `[{"TPMT": "Poor Metabolizer", "NUDT15": "Possible Intermediate Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result affects how you metabolize a certain type of medication, which can increase the risk of serious side effects.",
  "mechanism": "The medication is converted into an active form that can affect the bone marrow, leading to a decrease in white blood cells. Your genetic result removes a brake on this process, allowing more of the active form to accumulate and increase the risk of serious side effects.",
  "variant_rationale": "PharmCAT called TPMT as {diplotype}, which corresponds to a Poor Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "If you have this genetic result, it's best to talk to your doctor or pharmacist about using a different medication that doesn't have the same risk of serious side effects. They can help you find a safer option that works for you."
}
```

### 92b95f4e931acd94 — summary

**Exact sentence / claim to assess:**

Your genetic result affects how you metabolize a certain type of medication, which can increase the risk of serious side effects.

Sentence UTF-8 SHA-256: `c6d9094f033dd08e1ca115ec06b5049a88ebb8f91130373c67dbcfba06e64b25`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result affects how you metabolize a certain type of medication, which can increase the risk of serious side effects.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.847999+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 33–36 (How the drug is handled):

```text
Azathioprine is a prodrug that is converted to mercaptopurine and then, through
several steps, into thioguanine nucleotides (TGNs). TGNs are the active species:
they are incorporated into DNA, and that incorporation produces both the
intended immunosuppressive effect and the drug's principal toxicity.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 1f7732dcc26c182a — mechanism

**Exact sentence / claim to assess:**

The medication is converted into an active form that can affect the bone marrow, leading to a decrease in white blood cells.

Sentence UTF-8 SHA-256: `318b345428a2ccf1fdbc734d955cd7c8f03ee9cf5317c1dede9483e8a614014c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "The medication is converted into an active form that can affect the bone marrow, leading to a decrease in white blood cells.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "",
  "basis_citation": "Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934",
  "escalated": true,
  "escalation_reasons": [
    "no-source"
  ],
  "escalation_detail": [
    "no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against."
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 43–47 (Why altered function changes the outcome):

```text
- **Reduced or absent TPMT (or NUDT15) function** removes a brake. More
  thioguanine nucleotide accumulates in haematopoietic cells for the same
  administered amount. The characteristic consequence is bone-marrow
  suppression: leukopenia, neutropenia, and in severe cases life-threatening
  myelosuppression. This is a **toxicity** problem, not a loss-of-effect problem.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### baa6e6a5916f1bf7 — mechanism

**Exact sentence / claim to assess:**

Your genetic result removes a brake on this process, allowing more of the active form to accumulate and increase the risk of serious side effects.

Sentence UTF-8 SHA-256: `1966a5936b748fa596886ded450ecae7231f3352534d5b9821a0eebbe8968cbf`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Your genetic result removes a brake on this process, allowing more of the active form to accumulate and increase the risk of serious side effects.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "",
  "basis_citation": "Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934",
  "escalated": true,
  "escalation_reasons": [
    "no-source"
  ],
  "escalation_detail": [
    "no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against."
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 43–47 (Why altered function changes the outcome):

```text
- **Reduced or absent TPMT (or NUDT15) function** removes a brake. More
  thioguanine nucleotide accumulates in haematopoietic cells for the same
  administered amount. The characteristic consequence is bone-marrow
  suppression: leukopenia, neutropenia, and in severe cases life-threatening
  myelosuppression. This is a **toxicity** problem, not a loss-of-effect problem.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 78b406a25d863f33 — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called TPMT as {diplotype}, which corresponds to a Poor Metabolizer result.

Sentence UTF-8 SHA-256: `e70dddf461eaecb2e0fe42f4670ba7eab67ed2ab7e399659bfef122d6b550745`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called TPMT as {diplotype}, which corresponds to a Poor Metabolizer result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848000+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 22–24 (What the gene products do):

```text
*TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that
methylates thiopurine compounds and so diverts them away from the pathway that
produces active metabolites.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 9c88d8d1804b7198 — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848001+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 70f4f50e3749dd32 — patient_friendly

**Exact sentence / claim to assess:**

If you have this genetic result, it's best to talk to your doctor or pharmacist about using a different medication that doesn't have the same risk of serious side effects.

Sentence UTF-8 SHA-256: `e775a3dd43462348b286a0ecd7e2be856c25f2d5db31940b16b6d03777401321`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you have this genetic result, it's best to talk to your doctor or pharmacist about using a different medication that doesn't have the same risk of serious side effects.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848002+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 33–36 (How the drug is handled):

```text
Azathioprine is a prodrug that is converted to mercaptopurine and then, through
several steps, into thioguanine nucleotides (TGNs). TGNs are the active species:
they are incorporated into DNA, and that incorporation produces both the
intended immunosuppressive effect and the drug's principal toxicity.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### c9d99a9a1f5bc759 — patient_friendly

**Exact sentence / claim to assess:**

They can help you find a safer option that works for you.

Sentence UTF-8 SHA-256: `4a891426176a6388c8d6c601e7c36756e68e15be3d4aed56a08bdc643fb17998`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "They can help you find a safer option that works for you.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848004+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## azathioprine:Unknown

Gene/context: **TPMT / Unknown**; stored label `Unknown` (historical; no broad safety endorsement).
Relevant genes: TPMT, NUDT15. A complete drug-level interpretation requires acceptable evidence for both TPMT and NUDT15.

Primary source: [azathioprine source record](SOURCE-VERIFICATION.md#azathioprine); 2025 update; epub 2026-01-31; April 2026 issue, 119(4):916–927. Official advance PDF accepted 2026-01-08.
Pinned guideline: `PA166104933`, version `59`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `4364bd59b3579bf3d7bad7cc041b62b566a3a2a840a08704ebf86303a3408c43`
- source_hash: `30649615c531b5f13722cdb676cebb37c689b987286ae8a54b8b4a83e0639ce5`
- context_hash: `ee9cd1d99d477007adb005661ee4ac26076deade28e9a8515cbd3ded3726158c`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

No recommendation recorded for Unknown; no matched source row claimed.

### Recorded recommendation (exact stored bytes as JSON string)

```json
""
```

Candidate pinned rows (matching text does not prove original selection):

- None.

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result has not been determined for the gene involved in how your body handles a certain medication. This means we cannot provide a specific recommendation for how to use this medication safely.",
  "mechanism": "This medication is converted into active compounds in your body, which can affect your bone marrow and cause low white blood cell counts. Normally, certain enzymes help control the amount of these active compounds. If these enzymes are not working properly, more of the active compounds can build up and cause problems.",
  "variant_rationale": "No genotype was called for azathioprine in this analysis, so there is no variant-level rationale to report.",
  "patient_friendly": "We don't have enough information about how your body handles this medication. This means we can't give you specific advice on how to use it safely. It's always best to talk to your doctor or pharmacist about any concerns you have about your medication."
}
```

### f3d7a4347fd8522f — summary

**Exact sentence / claim to assess:**

Your genetic result has not been determined for the gene involved in how your body handles a certain medication.

Sentence UTF-8 SHA-256: `2ddbf639c0f53ae5be8d95fd28c5da04a6cd5442a9dce35b7dbf1d39073fd0ce`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `SUPPORT_NOT_LOCATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result has not been determined for the gene involved in how your body handles a certain medication.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848005+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### cd98b62663a21176 — summary

**Exact sentence / claim to assess:**

This means we cannot provide a specific recommendation for how to use this medication safely.

Sentence UTF-8 SHA-256: `a1eadae11e99b1ed3e6cc965f41a36064982c922eb9e556880ca2d9be6490295`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "This means we cannot provide a specific recommendation for how to use this medication safely.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848006+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 52–55 (Why altered function changes the outcome):

```text
- The two genes are **independent**: a patient can be normal for one and
  deficient for the other, and the deficient gene is the one that governs the
  recommendation. This is why PharmaGuard reports whichever of the two genes is
  more abnormal rather than defaulting to one.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### ceeb7f31a1265e4a — mechanism

**Exact sentence / claim to assess:**

This medication is converted into active compounds in your body, which can affect your bone marrow and cause low white blood cell counts.

Sentence UTF-8 SHA-256: `6ce782a5f842ec99a353cec712bb3913acfb02307a5e614c2fa55ce634f58b52`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "This medication is converted into active compounds in your body, which can affect your bone marrow and cause low white blood cell counts.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "",
  "basis_citation": "Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934",
  "escalated": true,
  "escalation_reasons": [
    "no-source"
  ],
  "escalation_detail": [
    "no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against."
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 43–47 (Why altered function changes the outcome):

```text
- **Reduced or absent TPMT (or NUDT15) function** removes a brake. More
  thioguanine nucleotide accumulates in haematopoietic cells for the same
  administered amount. The characteristic consequence is bone-marrow
  suppression: leukopenia, neutropenia, and in severe cases life-threatening
  myelosuppression. This is a **toxicity** problem, not a loss-of-effect problem.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 4d7ff29182363999 — mechanism

**Exact sentence / claim to assess:**

Normally, certain enzymes help control the amount of these active compounds.

Sentence UTF-8 SHA-256: `eeb6f56f0a123227fd1735e7cca9ad84a9e4fe43eba7782be87bfe014c13e7dc`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Normally, certain enzymes help control the amount of these active compounds.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates thiopurine compounds and so diverts them away from the pathway that produces active metabolites.",
  "basis_citation": "Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 22–24 (What the gene products do):

```text
*TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that
methylates thiopurine compounds and so diverts them away from the pathway that
produces active metabolites.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### aec582944cbb2b1a — mechanism

**Exact sentence / claim to assess:**

If these enzymes are not working properly, more of the active compounds can build up and cause problems.

Sentence UTF-8 SHA-256: `8119ee3e634380f49f469fc77264ff967d91c4a49fea6de43379052fa0561220`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "If these enzymes are not working properly, more of the active compounds can build up and cause problems.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that methylates thiopurine compounds and so diverts them away from the pathway that produces active metabolites.",
  "basis_citation": "Annotation of CPIC Guideline for azathioprine and NUDT15, TPMT — Relling MV et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Thiopurine Dosing Based on TPMT and NUDT15 Genotypes: 2025 Update. Clin Pharmacol Ther (2026). PMID: 41618934",
  "escalated": true,
  "escalation_reasons": [
    "causal"
  ],
  "escalation_detail": [
    "adds a causal step that may not be in the source (“cause”)"
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 22–24 (What the gene products do):

```text
*TPMT* encodes thiopurine S-methyltransferase, a cytosolic enzyme that
methylates thiopurine compounds and so diverts them away from the pathway that
produces active metabolites.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 4dc40f7cbb8ffa8c — variant_rationale

**Exact sentence / claim to assess:**

No genotype was called for azathioprine in this analysis, so there is no variant-level rationale to report.

Sentence UTF-8 SHA-256: `83246c4032d8e582be1d15e36444b0ab2e3fbd5e508f9cee7004f91fc83db351`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "No genotype was called for azathioprine in this analysis, so there is no variant-level rationale to report.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848007+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 33–36 (How the drug is handled):

```text
Azathioprine is a prodrug that is converted to mercaptopurine and then, through
several steps, into thioguanine nucleotides (TGNs). TGNs are the active species:
they are incorporated into DNA, and that incorporation produces both the
intended immunosuppressive effect and the drug's principal toxicity.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### a7128c15e04f3a54 — patient_friendly

**Exact sentence / claim to assess:**

We don't have enough information about how your body handles this medication.

Sentence UTF-8 SHA-256: `a627294f60228c25f7c5e8ede08a0a9bf39bfa3d6670b2d133bed209fecb690c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `SUPPORT_NOT_LOCATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "We don't have enough information about how your body handles this medication.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848008+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### c9b50714e5c206db — patient_friendly

**Exact sentence / claim to assess:**

This means we can't give you specific advice on how to use it safely.

Sentence UTF-8 SHA-256: `0f3f4197dbf56b83304398b2a85270f232f3c17948c3ec56ca63f8d370be4777`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This means we can't give you specific advice on how to use it safely.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848009+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/TPMT_azathioprine.md` lines 49–50 (Why altered function changes the outcome):

```text
- **Normal function in both genes** gives the metabolite exposure that standard
  thiopurine dosing was designed around.
```

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### db551f6c1f9bfae3 — patient_friendly

**Exact sentence / claim to assess:**

It's always best to talk to your doctor or pharmacist about any concerns you have about your medication.

Sentence UTF-8 SHA-256: `064798f08077ff5eb82323630647105e1d7122e9a09ddffd72e80040606c0a2c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `SUPPORT_NOT_LOCATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "It's always best to talk to your doctor or pharmacist about any concerns you have about your medication.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848010+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- SOURCE_METADATA: first-author mismatch in citation; see source register. Combined TPMT/NUDT15 state is not recorded in entry identity.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## clopidogrel:IM

Gene/context: **CYP2C19 / IM**; stored label `Ineffective` (historical; no broad safety endorsement).
Relevant genes: CYP2C19. Guidance is bounded to the CPIC annotation and the genomic evidence assessed by this application.

Primary source: [clopidogrel source record](SOURCE-VERIFICATION.md#clopidogrel); 2022 update; final edited form 2022-02-08; November 2022 issue, 112(5):959–967.
Pinned guideline: `PA166104948`, version `49`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `4493612b6afeff1064c2d7e4af77ffaa6b03f27d7fe7e8b7fdb6ada6eb679354`
- source_hash: `c443bfe6ea66381e66ab227d7c9a0a00cca430b5a4233b47488b4fbacb95d660`
- context_hash: `94e619b6bcbd770fc69b4bd368230ed9d85fa9d5c3f69afed170cd3715034916`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

1 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"Avoid standard dose (75 mg) clopidogrel if possible. Use prasugrel or ticagrelor at standard dose if no contraindication."
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166297570`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Intermediate Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result affects how well you respond to clopidogrel. It's recommended to avoid the standard dose of clopidogrel if possible.",
  "mechanism": "Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme. The amount of active form produced depends on how well this enzyme is working. If the enzyme is not working well, less active form is produced, leading to weaker platelet inhibition.",
  "variant_rationale": "PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Intermediate Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "If you have a certain genetic result, clopidogrel might not work as well as it should. This is because your body doesn't make enough of the active form of the medicine. Your doctor or pharmacist can help you find a different medicine that works better for you."
}
```

### a08b25ed7f58246d — summary

**Exact sentence / claim to assess:**

Your genetic result affects how well you respond to clopidogrel.

Sentence UTF-8 SHA-256: `a9d20a0a178256bb5880bdff116e9116d6b64c32a41110057e7514e5064a3ea6`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result affects how well you respond to clopidogrel.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848012+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 9510dcaf686365cb — summary

**Exact sentence / claim to assess:**

It's recommended to avoid the standard dose of clopidogrel if possible.

Sentence UTF-8 SHA-256: `f88d6640ef6466d65d372d2460302b780a2afa093273e10ff916d7ad896355ca`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "It's recommended to avoid the standard dose of clopidogrel if possible.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848012+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 3df5dd4b3008ba33 — mechanism

**Exact sentence / claim to assess:**

Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme.

Sentence UTF-8 SHA-256: `20a3e7b9b9a03d2189e5ffb736591f1b65b6a2454923a3486549cad061b023d9`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 98bb61a5e28fca66 — mechanism

**Exact sentence / claim to assess:**

The amount of active form produced depends on how well this enzyme is working.

Sentence UTF-8 SHA-256: `72f4b76abe7f65d60645a4720f5cf7734c14ccb3046869d8ab37546de087daa9`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "The amount of active form produced depends on how well this enzyme is working.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 35–37 (How the drug is handled):

```text
Because the drug depends on being *switched on* by an enzyme, the amount of
active metabolite formed is directly tied to how much functional CYP2C19 a
person has.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 5d6018a1893d07c7 — mechanism

**Exact sentence / claim to assess:**

If the enzyme is not working well, less active form is produced, leading to weaker platelet inhibition.

Sentence UTF-8 SHA-256: `a06e88f73d2ed521d72c5d35585bca9d730da65f239e71f3415ef47106c04635`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "If the enzyme is not working well, less active form is produced, leading to weaker platelet inhibition.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 41–47 (Why altered function changes the outcome):

```text
- **Reduced or absent CYP2C19 function** means less prodrug is converted, so
  less active metabolite reaches the platelets. Platelet inhibition is weaker
  than intended. The clinical concern is therefore **therapeutic failure** —
  the drug not working — rather than the drug being toxic. Residual platelet
  reactivity remains high while the patient and clinician believe they are
  protected, which in the setting of recent stenting or acute coronary syndrome
  is where the risk of ischaemic events arises.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### ad52527c6bca289f — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Intermediate Metabolizer result.

Sentence UTF-8 SHA-256: `4bba9b3aac4866dc7752801739d1fb330117f4fa9c0ebaef5cafbe1ae3088715`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Intermediate Metabolizer result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848014+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 62–66 (Notes for the explanation layer):

```text
- The gene acts as an **activator** here, not a clearance route. Do not describe
  reduced CYP2C19 function as "the drug building up" — the opposite is true.
- Antiplatelet alternatives exist and CPIC names them, but the specific agents
  and any dosing come from PharmCAT's recommendation text at runtime, never from
  this file.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### bafc2b0af21bd9c6 — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848015+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 21–24 (What the gene product does):

```text
CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that
oxidises a wide range of drug substrates. Its activity varies substantially
between people because the *CYP2C19* gene carries common variants that abolish,
reduce, or increase enzyme production.
```

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 81a7737cea726999 — patient_friendly

**Exact sentence / claim to assess:**

If you have a certain genetic result, clopidogrel might not work as well as it should.

Sentence UTF-8 SHA-256: `6a3153c3a0465d2a24e186d743f7bd09784c059bbb46ad5bf935f46c4e967590`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you have a certain genetic result, clopidogrel might not work as well as it should.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848016+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### b7b31b0a89a3bccd — patient_friendly

**Exact sentence / claim to assess:**

This is because your body doesn't make enough of the active form of the medicine.

Sentence UTF-8 SHA-256: `bf06dee99c206424f396bac34708c74298448452b36c6071538f124969e41b51`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This is because your body doesn't make enough of the active form of the medicine.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848017+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 35–37 (How the drug is handled):

```text
Because the drug depends on being *switched on* by an enzyme, the amount of
active metabolite formed is directly tied to how much functional CYP2C19 a
person has.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 9c73ef0c6b4e7f99 — patient_friendly

**Exact sentence / claim to assess:**

Your doctor or pharmacist can help you find a different medicine that works better for you.

Sentence UTF-8 SHA-256: `ff329cabd6555bd3114a16ef16001dc96239a8a715df0377b3982ea1fa606506`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "Your doctor or pharmacist can help you find a different medicine that works better for you.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848018+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## clopidogrel:NM

Gene/context: **CYP2C19 / NM**; stored label `Safe` (historical; no broad safety endorsement).
Relevant genes: CYP2C19. Guidance is bounded to the CPIC annotation and the genomic evidence assessed by this application.

Primary source: [clopidogrel source record](SOURCE-VERIFICATION.md#clopidogrel); 2022 update; final edited form 2022-02-08; November 2022 issue, 112(5):959–967.
Pinned guideline: `PA166104948`, version `49`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `2782e5e684ff2590a8b00dd172f95451328be04852b222433b158aa77f1290c0`
- source_hash: `6f6a5b19cd75138f7d6ff4c977bc04386c63d77b5b46246fe17117a437b7c5da`
- context_hash: `ebf948b8cccd02052f46943a146060d746f22c7b9ab1cc7d6dfc8038edab53f8`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

5 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"If considering clopidogrel, use at standard dose (75 mg/day)"
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166297565`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Ultrarapid Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297566`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Rapid Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297567`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297576`; population `CVI non-ACS non-PCI`; lookup `[{"CYP2C19": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297586`; population `NVI`; lookup `[{"CYP2C19": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result suggests that you are a normal metabolizer of clopidogrel, which means that you can take the standard dose without concern.",
  "mechanism": "Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme. Your body's ability to convert clopidogrel into its active form is normal, which allows for the expected degree of platelet inhibition.",
  "variant_rationale": "PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Normal Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "This means that you can take the standard dose of clopidogrel without worrying about it not working properly. However, it's always best to speak with your doctor or pharmacist to confirm the right dose for you."
}
```

### 3a1e82e37a6b1278 — summary

**Exact sentence / claim to assess:**

Your genetic result suggests that you are a normal metabolizer of clopidogrel, which means that you can take the standard dose without concern.

Sentence UTF-8 SHA-256: `ac884ef64477ab97c8f5dea084f28e025fd09100b9d40ff6efbf26e52e6e5e1c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result suggests that you are a normal metabolizer of clopidogrel, which means that you can take the standard dose without concern.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848019+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- OVERBROAD_SAFETY: normal or other assessed PGx function does not establish general safety or assured efficacy; human reassessment requested, including existing bulk decisions.
- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 88f1c0d3f52b365e — mechanism

**Exact sentence / claim to assess:**

Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme.

Sentence UTF-8 SHA-256: `20a3e7b9b9a03d2189e5ffb736591f1b65b6a2454923a3486549cad061b023d9`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### ee63c1aab4d888c7 — mechanism

**Exact sentence / claim to assess:**

Your body's ability to convert clopidogrel into its active form is normal, which allows for the expected degree of platelet inhibition.

Sentence UTF-8 SHA-256: `d62bc5ee433985c1bbf6c1c3c89bbb07416f3ad188382a429d04bd20acf0909a`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Your body's ability to convert clopidogrel into its active form is normal, which allows for the expected degree of platelet inhibition.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Normal function** produces the expected amount of active metabolite and the expected degree of platelet inhibition.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 49–50 (Why altered function changes the outcome):

```text
- **Normal function** produces the expected amount of active metabolite and the
  expected degree of platelet inhibition.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 4fd4c508a5993307 — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Normal Metabolizer result.

Sentence UTF-8 SHA-256: `fb01e07932c0aa08c9ff13967513498775b588c313237534c13a1f98f064308c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Normal Metabolizer result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848020+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 62–66 (Notes for the explanation layer):

```text
- The gene acts as an **activator** here, not a clearance route. Do not describe
  reduced CYP2C19 function as "the drug building up" — the opposite is true.
- Antiplatelet alternatives exist and CPIC names them, but the specific agents
  and any dosing come from PharmCAT's recommendation text at runtime, never from
  this file.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 32031b0049bfe9a0 — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848022+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 21–24 (What the gene product does):

```text
CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that
oxidises a wide range of drug substrates. Its activity varies substantially
between people because the *CYP2C19* gene carries common variants that abolish,
reduce, or increase enzyme production.
```

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### bb7a139c086f1b01 — patient_friendly

**Exact sentence / claim to assess:**

This means that you can take the standard dose of clopidogrel without worrying about it not working properly.

Sentence UTF-8 SHA-256: `046897ef8d53567b8f3d53cad421d39022b068f15507dbcd8c85836a10cad886`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This means that you can take the standard dose of clopidogrel without worrying about it not working properly.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848023+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- OVERBROAD_SAFETY: normal or other assessed PGx function does not establish general safety or assured efficacy; human reassessment requested, including existing bulk decisions.
- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 37f3e4775af9ac4c — patient_friendly

**Exact sentence / claim to assess:**

However, it's always best to speak with your doctor or pharmacist to confirm the right dose for you.

Sentence UTF-8 SHA-256: `bf980e5c4d5be54ed203610aae5a41ee99ac49a4ecdc44aca6d0ea1ff7951a01`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "However, it's always best to speak with your doctor or pharmacist to confirm the right dose for you.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848024+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## clopidogrel:PM

Gene/context: **CYP2C19 / PM**; stored label `Ineffective` (historical; no broad safety endorsement).
Relevant genes: CYP2C19. Guidance is bounded to the CPIC annotation and the genomic evidence assessed by this application.

Primary source: [clopidogrel source record](SOURCE-VERIFICATION.md#clopidogrel); 2022 update; final edited form 2022-02-08; November 2022 issue, 112(5):959–967.
Pinned guideline: `PA166104948`, version `49`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `180ea78ddeb92bc4ed734d787813f5d754e511f2a89ab675537b703637f14560`
- source_hash: `72c0b3b4ddbc9b7e1721e4e5dbc37dbea010e0e66a4c9aba45c6acf725a7cae0`
- context_hash: `e5f2c49916f5edcd26d4381616af2be7219fa44ea1b09ccb72a772fd0f04f657`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

4 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"Avoid clopidogrel if possible. Use prasugrel or ticagrelor at standard dose if no contraindication."
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166297571`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Likely Poor Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297572`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Poor Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297581`; population `CVI non-ACS non-PCI`; lookup `[{"CYP2C19": "Likely Poor Metabolizer"}]`; classification `{"term": "Moderate", "termId": "guidelineStrength:981501931"}`
- `PA166297582`; population `CVI non-ACS non-PCI`; lookup `[{"CYP2C19": "Poor Metabolizer"}]`; classification `{"term": "Moderate", "termId": "guidelineStrength:981501931"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result affects how well you respond to clopidogrel. People with this result are at increased risk for the drug not working as intended, which can lead to serious cardiac and cerebrovascular events.",
  "mechanism": "Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme. Your genetic result affects how well this enzyme works, which in turn affects how well the drug works. If the enzyme doesn't work well, less of the active form is produced, and the drug may not work as intended.",
  "variant_rationale": "PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Poor Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "If you have this result, it's best to avoid clopidogrel if possible. If you can't avoid it, your doctor may recommend a different medication, such as prasugrel or ticagrelor, at the standard dose. Always talk to your doctor or pharmacist about your specific situation and any concerns you may have."
}
```

### 9e5eb26eadf448c2 — summary

**Exact sentence / claim to assess:**

Your genetic result affects how well you respond to clopidogrel.

Sentence UTF-8 SHA-256: `a9d20a0a178256bb5880bdff116e9116d6b64c32a41110057e7514e5064a3ea6`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result affects how well you respond to clopidogrel.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848025+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 3ed47952af2af9f6 — summary

**Exact sentence / claim to assess:**

People with this result are at increased risk for the drug not working as intended, which can lead to serious cardiac and cerebrovascular events.

Sentence UTF-8 SHA-256: `d5ab5064a95b89850a290f5a8113b07e26a3add3e864b04e02d615bc4a8ae64d`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "People with this result are at increased risk for the drug not working as intended, which can lead to serious cardiac and cerebrovascular events.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848026+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 41–47 (Why altered function changes the outcome):

```text
- **Reduced or absent CYP2C19 function** means less prodrug is converted, so
  less active metabolite reaches the platelets. Platelet inhibition is weaker
  than intended. The clinical concern is therefore **therapeutic failure** —
  the drug not working — rather than the drug being toxic. Residual platelet
  reactivity remains high while the patient and clinician believe they are
  protected, which in the setting of recent stenting or acute coronary syndrome
  is where the risk of ischaemic events arises.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### a2a5c6d1fbc6adba — mechanism

**Exact sentence / claim to assess:**

Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme.

Sentence UTF-8 SHA-256: `20a3e7b9b9a03d2189e5ffb736591f1b65b6a2454923a3486549cad061b023d9`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### b73169b0071b79c5 — mechanism

**Exact sentence / claim to assess:**

Your genetic result affects how well this enzyme works, which in turn affects how well the drug works.

Sentence UTF-8 SHA-256: `96476df8395a2ae86327c7cefdaea858cf19114feba2aeebd74971add8484d6e`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Your genetic result affects how well this enzyme works, which in turn affects how well the drug works.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that oxidises a wide range of drug substrates.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 21–24 (What the gene product does):

```text
CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that
oxidises a wide range of drug substrates. Its activity varies substantially
between people because the *CYP2C19* gene carries common variants that abolish,
reduce, or increase enzyme production.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### ce9433e9e56934c8 — mechanism

**Exact sentence / claim to assess:**

If the enzyme doesn't work well, less of the active form is produced, and the drug may not work as intended.

Sentence UTF-8 SHA-256: `63650b3622cc3e5d57031548d3c84f54f94b434d0f82298da153b478b8a64733`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "If the enzyme doesn't work well, less of the active form is produced, and the drug may not work as intended.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 35–37 (How the drug is handled):

```text
Because the drug depends on being *switched on* by an enzyme, the amount of
active metabolite formed is directly tied to how much functional CYP2C19 a
person has.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 7df33ba7cc8dc76d — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Poor Metabolizer result.

Sentence UTF-8 SHA-256: `2253c25391d792041e70297003ddf5f027975244f7cd351c0b271802a1d56b84`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Poor Metabolizer result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848028+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 62–66 (Notes for the explanation layer):

```text
- The gene acts as an **activator** here, not a clearance route. Do not describe
  reduced CYP2C19 function as "the drug building up" — the opposite is true.
- Antiplatelet alternatives exist and CPIC names them, but the specific agents
  and any dosing come from PharmCAT's recommendation text at runtime, never from
  this file.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### ff90515cd10b345f — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848029+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 21–24 (What the gene product does):

```text
CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that
oxidises a wide range of drug substrates. Its activity varies substantially
between people because the *CYP2C19* gene carries common variants that abolish,
reduce, or increase enzyme production.
```

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 91e8719016511f27 — patient_friendly

**Exact sentence / claim to assess:**

If you have this result, it's best to avoid clopidogrel if possible.

Sentence UTF-8 SHA-256: `b719f7104c7c5d25f27f1b0d1c8844fb46f060c2d92cda3ecbb1e1bf4f80dbf7`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you have this result, it's best to avoid clopidogrel if possible.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848030+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### b42f0e47358d6cf8 — patient_friendly

**Exact sentence / claim to assess:**

If you can't avoid it, your doctor may recommend a different medication, such as prasugrel or ticagrelor, at the standard dose.

Sentence UTF-8 SHA-256: `ba0ccc8b7f6891e27cc1d901651cc881bf3fa6235f54272c8305b16c5471fe93`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you can't avoid it, your doctor may recommend a different medication, such as prasugrel or ticagrelor, at the standard dose.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848031+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 02a7e2b543069dbf — patient_friendly

**Exact sentence / claim to assess:**

Always talk to your doctor or pharmacist about your specific situation and any concerns you may have.

Sentence UTF-8 SHA-256: `be5eb9b3ec13c2020046822693941e4c65de3b0d3daab12346373fc1abb72135`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "Always talk to your doctor or pharmacist about your specific situation and any concerns you may have.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848032+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 41–47 (Why altered function changes the outcome):

```text
- **Reduced or absent CYP2C19 function** means less prodrug is converted, so
  less active metabolite reaches the platelets. Platelet inhibition is weaker
  than intended. The clinical concern is therefore **therapeutic failure** —
  the drug not working — rather than the drug being toxic. Residual platelet
  reactivity remains high while the patient and clinician believe they are
  protected, which in the setting of recent stenting or acute coronary syndrome
  is where the risk of ischaemic events arises.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## clopidogrel:RM

Gene/context: **CYP2C19 / RM**; stored label `Safe` (historical; no broad safety endorsement).
Relevant genes: CYP2C19. Guidance is bounded to the CPIC annotation and the genomic evidence assessed by this application.

Primary source: [clopidogrel source record](SOURCE-VERIFICATION.md#clopidogrel); 2022 update; final edited form 2022-02-08; November 2022 issue, 112(5):959–967.
Pinned guideline: `PA166104948`, version `49`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `ad33a801e57ff51f41d7170d95c19fa8988e2a8cea60c23563e0c3c2c48ef8e7`
- source_hash: `6f6a5b19cd75138f7d6ff4c977bc04386c63d77b5b46246fe17117a437b7c5da`
- context_hash: `f6bca6ecffcc174172cc52af5055860dd117a8d6acd3d2f3fe460deecb02017e`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

5 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"If considering clopidogrel, use at standard dose (75 mg/day)"
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166297565`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Ultrarapid Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297566`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Rapid Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297567`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297576`; population `CVI non-ACS non-PCI`; lookup `[{"CYP2C19": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297586`; population `NVI`; lookup `[{"CYP2C19": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result indicates you are a rapid metabolizer of clopidogrel, meaning your body processes the medication quickly and effectively.",
  "mechanism": "Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme to work. Your genetic result shows that you have normal or increased function of this enzyme, which means the active form of the medication is formed quickly and effectively. This leads to normal or lower platelet reactivity, which is not associated with a higher risk of bleeding.",
  "variant_rationale": "PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Rapid Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "If you're considering taking clopidogrel, you can take it at the standard dose. This is because your body is good at breaking down the medication and making it work. However, it's always best to speak with your doctor or pharmacist to confirm the right dosage for you."
}
```

### 8aeb7e866bbbb429 — summary

**Exact sentence / claim to assess:**

Your genetic result indicates you are a rapid metabolizer of clopidogrel, meaning your body processes the medication quickly and effectively.

Sentence UTF-8 SHA-256: `b5e4e4f8f89aeb994538d65ace785bbcb05458deda345bde43a8b154e9a0efc8`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result indicates you are a rapid metabolizer of clopidogrel, meaning your body processes the medication quickly and effectively.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848033+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 31d9e1f098f4b967 — mechanism

**Exact sentence / claim to assess:**

Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme to work.

Sentence UTF-8 SHA-256: `1737eb411107be4944a6b9d8ceceff875d306de11b4b028ff789502d5e327ff3`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme to work.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### fe5b22d519f803bb — mechanism

**Exact sentence / claim to assess:**

Your genetic result shows that you have normal or increased function of this enzyme, which means the active form of the medication is formed quickly and effectively.

Sentence UTF-8 SHA-256: `5b06271868d0d8d6f6ca681dbc20af43fecbe603a007114bd3651feb79e557f1`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Your genetic result shows that you have normal or increased function of this enzyme, which means the active form of the medication is formed quickly and effectively.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": true,
  "escalation_reasons": [
    "causal"
  ],
  "escalation_detail": [
    "adds a causal step that may not be in the source (“which means”)"
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 35–37 (How the drug is handled):

```text
Because the drug depends on being *switched on* by an enzyme, the amount of
active metabolite formed is directly tied to how much functional CYP2C19 a
person has.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 828c56c1065af4df — mechanism

**Exact sentence / claim to assess:**

This leads to normal or lower platelet reactivity, which is not associated with a higher risk of bleeding.

Sentence UTF-8 SHA-256: `648d0b01c792cedebbba0e655750b2f0177752d24e85dcae0a1ba1eb38e87376`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "This leads to normal or lower platelet reactivity, which is not associated with a higher risk of bleeding.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Platelet inhibition is at least as strong as expected; CPIC's own implications text for this group notes no association with higher bleeding risk.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": true,
  "escalation_reasons": [
    "absence",
    "causal",
    "comparative"
  ],
  "escalation_detail": [
    "claims an ABSENCE. Invisible to every automated check here: it carries no assertion marker and contradicts no directive, and it errs toward reassurance. Always escalated. (“not associated”)",
    "adds a causal step that may not be in the source (“leads to”)",
    "makes a comparative or graded risk claim (“higher risk”)"
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 52–54 (Why altered function changes the outcome):

```text
- **Increased function** produces more active metabolite. Platelet inhibition is
  at least as strong as expected; CPIC's own implications text for this group
  notes no association with higher bleeding risk.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 256c2b5256bc8d49 — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Rapid Metabolizer result.

Sentence UTF-8 SHA-256: `1fd8d2d997de37cabb33191e50d3d512c57211761d6e2f92360c0a1c414a0998`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Rapid Metabolizer result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848034+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 62–66 (Notes for the explanation layer):

```text
- The gene acts as an **activator** here, not a clearance route. Do not describe
  reduced CYP2C19 function as "the drug building up" — the opposite is true.
- Antiplatelet alternatives exist and CPIC names them, but the specific agents
  and any dosing come from PharmCAT's recommendation text at runtime, never from
  this file.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### e10f142088fa3911 — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848035+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 21–24 (What the gene product does):

```text
CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that
oxidises a wide range of drug substrates. Its activity varies substantially
between people because the *CYP2C19* gene carries common variants that abolish,
reduce, or increase enzyme production.
```

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### af96e55464ef795a — patient_friendly

**Exact sentence / claim to assess:**

If you're considering taking clopidogrel, you can take it at the standard dose.

Sentence UTF-8 SHA-256: `ee711fca8307786f8bdb2001cb97fc53cfab425e951832a5cbb7a32cb490270c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you're considering taking clopidogrel, you can take it at the standard dose.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848036+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### b15cf39d265ae4f0 — patient_friendly

**Exact sentence / claim to assess:**

This is because your body is good at breaking down the medication and making it work.

Sentence UTF-8 SHA-256: `4cda085c1776b51552793b57916863804987c710c0a57eb1045abd9d559b65ba`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This is because your body is good at breaking down the medication and making it work.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848037+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### b8c87dc6ac19dc49 — patient_friendly

**Exact sentence / claim to assess:**

However, it's always best to speak with your doctor or pharmacist to confirm the right dosage for you.

Sentence UTF-8 SHA-256: `bbfff701455ac1c97d43a869b223c81ad988590492f31e8807f5465eec5ad2b6`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "However, it's always best to speak with your doctor or pharmacist to confirm the right dosage for you.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848038+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## clopidogrel:URM

Gene/context: **CYP2C19 / URM**; stored label `Safe` (historical; no broad safety endorsement).
Relevant genes: CYP2C19. Guidance is bounded to the CPIC annotation and the genomic evidence assessed by this application.

Primary source: [clopidogrel source record](SOURCE-VERIFICATION.md#clopidogrel); 2022 update; final edited form 2022-02-08; November 2022 issue, 112(5):959–967.
Pinned guideline: `PA166104948`, version `49`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `e5615a782817e14353bc03de330bc84cb0786a7b739fe29763c120277b42bfcf`
- source_hash: `6f6a5b19cd75138f7d6ff4c977bc04386c63d77b5b46246fe17117a437b7c5da`
- context_hash: `348d477e7c7ed861a9c217db08bdd7ba4143c29887076e5ae5577024e14a56a2`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

5 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"If considering clopidogrel, use at standard dose (75 mg/day)"
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166297565`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Ultrarapid Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297566`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Rapid Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297567`; population `CVI ACS PCI`; lookup `[{"CYP2C19": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297576`; population `CVI non-ACS non-PCI`; lookup `[{"CYP2C19": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166297586`; population `NVI`; lookup `[{"CYP2C19": "Normal Metabolizer"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Based on your genetic result, the recommended dose for clopidogrel is at standard dose (75 mg/day).",
  "mechanism": "Clopidogrel is a prodrug that needs to be converted into an active metabolite by an enzyme to work. Your genetic result affects how much of this active metabolite is formed, which in turn affects how well the drug works. Increased formation of the active metabolite means the drug works more effectively, while reduced formation means the drug may not work as intended.",
  "variant_rationale": "PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Ultrarapid Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "Your genetic result shows that you are a safe candidate for taking clopidogrel. However, to make sure the drug works properly, it's recommended to take it at the standard dose. This means you should talk to your doctor or pharmacist about the best way to take clopidogrel based on your individual needs."
}
```

### 735994172b8fe365 — summary

**Exact sentence / claim to assess:**

Based on your genetic result, the recommended dose for clopidogrel is at standard dose (75 mg/day).

Sentence UTF-8 SHA-256: `2db3eb6fe6baed68cb877907455c5ab643ccf024bfa4a0ded8f39250e2fd6c9c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Based on your genetic result, the recommended dose for clopidogrel is at standard dose (75 mg/day).",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848039+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 4ff8ce44437d006c — mechanism

**Exact sentence / claim to assess:**

Clopidogrel is a prodrug that needs to be converted into an active metabolite by an enzyme to work.

Sentence UTF-8 SHA-256: `91631cf57c47a52bbc87ffa896f8b1ca14b4b9dec2de45caf1327754c789721c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Clopidogrel is a prodrug that needs to be converted into an active metabolite by an enzyme to work.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Reduced or absent CYP2C19 function** means less prodrug is converted, so less active metabolite reaches the platelets.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### e4da17b7660f2318 — mechanism

**Exact sentence / claim to assess:**

Your genetic result affects how much of this active metabolite is formed, which in turn affects how well the drug works.

Sentence UTF-8 SHA-256: `57333e07d888a0fdf8570324ff64b98365054b47648a89fdc36ee40c329846cb`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Your genetic result affects how much of this active metabolite is formed, which in turn affects how well the drug works.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 35–37 (How the drug is handled):

```text
Because the drug depends on being *switched on* by an enzyme, the amount of
active metabolite formed is directly tied to how much functional CYP2C19 a
person has.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 82173634a3b2698b — mechanism

**Exact sentence / claim to assess:**

Increased formation of the active metabolite means the drug works more effectively, while reduced formation means the drug may not work as intended.

Sentence UTF-8 SHA-256: `1839aa0888a3de9922bc4087b3fd520954ba1887e245e46a6610d98b39a18b27`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Increased formation of the active metabolite means the drug works more effectively, while reduced formation means the drug may not work as intended.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Reduced or absent CYP2C19 function** means less prodrug is converted, so less active metabolite reaches the platelets.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 41–47 (Why altered function changes the outcome):

```text
- **Reduced or absent CYP2C19 function** means less prodrug is converted, so
  less active metabolite reaches the platelets. Platelet inhibition is weaker
  than intended. The clinical concern is therefore **therapeutic failure** —
  the drug not working — rather than the drug being toxic. Residual platelet
  reactivity remains high while the patient and clinician believe they are
  protected, which in the setting of recent stenting or acute coronary syndrome
  is where the risk of ischaemic events arises.
```

Flags (automated/editorial triage, no adjudication):

- OVERBROAD_EFFICACY: active-metabolite formation does not itself establish superior clinical outcome.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 434e64aeb48c0f0a — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Ultrarapid Metabolizer result.

Sentence UTF-8 SHA-256: `32bb8b868a0f130c56873419f14da71eab238f73c2279d10fe7d360f85a03ef9`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called CYP2C19 as {diplotype}, which corresponds to a Ultrarapid Metabolizer result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848040+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 62–66 (Notes for the explanation layer):

```text
- The gene acts as an **activator** here, not a clearance route. Do not describe
  reduced CYP2C19 function as "the drug building up" — the opposite is true.
- Antiplatelet alternatives exist and CPIC names them, but the specific agents
  and any dosing come from PharmCAT's recommendation text at runtime, never from
  this file.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 5610887296801724 — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848041+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 21–24 (What the gene product does):

```text
CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that
oxidises a wide range of drug substrates. Its activity varies substantially
between people because the *CYP2C19* gene carries common variants that abolish,
reduce, or increase enzyme production.
```

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 0ada9de748876af4 — patient_friendly

**Exact sentence / claim to assess:**

Your genetic result shows that you are a safe candidate for taking clopidogrel.

Sentence UTF-8 SHA-256: `57290d4fbee24f09459afc66c1fa300e4ca77d0f93434502171b63e139cc3331`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "Your genetic result shows that you are a safe candidate for taking clopidogrel.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848042+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- OVERBROAD_SAFETY: normal or other assessed PGx function does not establish general safety or assured efficacy; human reassessment requested, including existing bulk decisions.
- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 4a9067a1243b577f — patient_friendly

**Exact sentence / claim to assess:**

However, to make sure the drug works properly, it's recommended to take it at the standard dose.

Sentence UTF-8 SHA-256: `8a80b1c2b1711d4722b8d80e13206af85f911d1f04a3c2a74e7b838f8f221a00`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "However, to make sure the drug works properly, it's recommended to take it at the standard dose.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848043+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### e4dd1071e6b2aa8c — patient_friendly

**Exact sentence / claim to assess:**

This means you should talk to your doctor or pharmacist about the best way to take clopidogrel based on your individual needs.

Sentence UTF-8 SHA-256: `b0331e5dbafad2bd1bd4147720370f6411d08adeea24652d57f2f4305441edc9`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This means you should talk to your doctor or pharmacist about the best way to take clopidogrel based on your individual needs.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848044+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- INDICATION_QUALIFIERS: verify row population, conditional prescribing wording and contraindications; indication is not stored.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## clopidogrel:Unknown

Gene/context: **CYP2C19 / Unknown**; stored label `Unknown` (historical; no broad safety endorsement).
Relevant genes: CYP2C19. Guidance is bounded to the CPIC annotation and the genomic evidence assessed by this application.

Primary source: [clopidogrel source record](SOURCE-VERIFICATION.md#clopidogrel); 2022 update; final edited form 2022-02-08; November 2022 issue, 112(5):959–967.
Pinned guideline: `PA166104948`, version `49`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `ca48868c71ee9fd4bfa8e16fe1e5305a02175fd6cb13e70017b45495cefc75a9`
- source_hash: `ae8d0e20c44e38122f34d5b279be8da18f22600380a9c5bf69437e84f7c94b78`
- context_hash: `9b5f5cb86f187006afe87d112982b6b5b95ccd153c1942822b052f9a2626de78`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

No recommendation recorded for Unknown; no matched source row claimed.

### Recorded recommendation (exact stored bytes as JSON string)

```json
""
```

Candidate pinned rows (matching text does not prove original selection):

- None.

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result does not provide enough information to determine how you metabolize clopidogrel. Therefore, the CPIC recommendation is unknown.",
  "mechanism": "Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme. The amount of active form produced depends on how much functional enzyme a person has. If the enzyme is not working properly, less active form is produced, and the drug may not work as intended.",
  "variant_rationale": "No genotype was called for clopidogrel in this analysis, so there is no variant-level rationale to report.",
  "patient_friendly": "We don't have enough information about how your body processes clopidogrel to give a specific recommendation. This means we can't say for sure how well the drug will work for you. It's always a good idea to talk to your doctor or pharmacist about your specific situation and any concerns you may have."
}
```

### 3fec09dafe73eca7 — summary

**Exact sentence / claim to assess:**

Your genetic result does not provide enough information to determine how you metabolize clopidogrel.

Sentence UTF-8 SHA-256: `46dabe7555edb9c95c8ec3d348e6297ffa274b828e746d2b42c51fc605f92443`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result does not provide enough information to determine how you metabolize clopidogrel.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848045+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 3f346e5affb10fb7 — summary

**Exact sentence / claim to assess:**

Therefore, the CPIC recommendation is unknown.

Sentence UTF-8 SHA-256: `d233d80dbea3533967d9c817d1b45d1f53b3d4c3fd51bbb1d1e5dce39be37eb0`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Therefore, the CPIC recommendation is unknown.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848046+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 62–66 (Notes for the explanation layer):

```text
- The gene acts as an **activator** here, not a clearance route. Do not describe
  reduced CYP2C19 function as "the drug building up" — the opposite is true.
- Antiplatelet alternatives exist and CPIC names them, but the specific agents
  and any dosing come from PharmCAT's recommendation text at runtime, never from
  this file.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 39f1c8c5686dd56a — mechanism

**Exact sentence / claim to assess:**

Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme.

Sentence UTF-8 SHA-256: `20a3e7b9b9a03d2189e5ffb736591f1b65b6a2454923a3486549cad061b023d9`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Clopidogrel is a prodrug that needs to be converted into an active form by an enzyme.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 28–33 (How the drug is handled):

```text
Clopidogrel is a **prodrug**: the molecule that is swallowed has no
antiplatelet activity of its own. It must be converted in two oxidative steps
into an active thiol metabolite, and CYP2C19 is a major contributor to both
steps. The active metabolite then binds irreversibly to the platelet P2Y12
receptor, blocking ADP-mediated platelet aggregation for the lifetime of the
platelet.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 9c744870354c7c97 — mechanism

**Exact sentence / claim to assess:**

The amount of active form produced depends on how much functional enzyme a person has.

Sentence UTF-8 SHA-256: `ec35b22751391135c9e3e83122bf113882fd6043a4f7cd07f4813bd5a15ce553`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "The amount of active form produced depends on how much functional enzyme a person has.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 35–37 (How the drug is handled):

```text
Because the drug depends on being *switched on* by an enzyme, the amount of
active metabolite formed is directly tied to how much functional CYP2C19 a
person has.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 88ab4061da7f7b0a — mechanism

**Exact sentence / claim to assess:**

If the enzyme is not working properly, less active form is produced, and the drug may not work as intended.

Sentence UTF-8 SHA-256: `33033e7ca2fa0ddf9c6725f885eedfee5066ad7b8cf2710e212e0333d2985d2a`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "If the enzyme is not working properly, less active form is produced, and the drug may not work as intended.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Because the drug depends on being *switched on* by an enzyme, the amount of active metabolite formed is directly tied to how much functional CYP2C19 a person has.",
  "basis_citation": "Annotation of CPIC Guideline for clopidogrel and CYP2C19 — Lee CR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update. Clin Pharmacol Ther (2022). PMID: 35034351",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 35–37 (How the drug is handled):

```text
Because the drug depends on being *switched on* by an enzyme, the amount of
active metabolite formed is directly tied to how much functional CYP2C19 a
person has.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### a17b69dfd4635b0a — variant_rationale

**Exact sentence / claim to assess:**

No genotype was called for clopidogrel in this analysis, so there is no variant-level rationale to report.

Sentence UTF-8 SHA-256: `77ec702f5934af9403aa15b5f72b8818fd1fcb8f6ade43e78143c06bb6e4556e`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "No genotype was called for clopidogrel in this analysis, so there is no variant-level rationale to report.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848047+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 21–24 (What the gene product does):

```text
CYP2C19 is a cytochrome P450 enzyme, expressed mainly in the liver, that
oxidises a wide range of drug substrates. Its activity varies substantially
between people because the *CYP2C19* gene carries common variants that abolish,
reduce, or increase enzyme production.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 9aedbdc7f03309a4 — patient_friendly

**Exact sentence / claim to assess:**

We don't have enough information about how your body processes clopidogrel to give a specific recommendation.

Sentence UTF-8 SHA-256: `2402f3ccc8f5d9f359670dddea88867bc9fcfb3b3e1dbe7bb6d550b54ec96df7`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "We don't have enough information about how your body processes clopidogrel to give a specific recommendation.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848048+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 62–66 (Notes for the explanation layer):

```text
- The gene acts as an **activator** here, not a clearance route. Do not describe
  reduced CYP2C19 function as "the drug building up" — the opposite is true.
- Antiplatelet alternatives exist and CPIC names them, but the specific agents
  and any dosing come from PharmCAT's recommendation text at runtime, never from
  this file.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### e81686bebcd0a3f6 — patient_friendly

**Exact sentence / claim to assess:**

This means we can't say for sure how well the drug will work for you.

Sentence UTF-8 SHA-256: `89d60811ad480f1f90c209740de71e399721c6aaeddd72a44b6b2a9dfa8ef3e3`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `SUPPORT_NOT_LOCATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This means we can't say for sure how well the drug will work for you.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848049+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 63a028a69b856192 — patient_friendly

**Exact sentence / claim to assess:**

It's always a good idea to talk to your doctor or pharmacist about your specific situation and any concerns you may have.

Sentence UTF-8 SHA-256: `db0f569561d1ce62635c0ccff5382d3d398d10d85663fe51b358bcec2d35587f`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "It's always a good idea to talk to your doctor or pharmacist about your specific situation and any concerns you may have.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848050+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C19_clopidogrel.md` lines 41–47 (Why altered function changes the outcome):

```text
- **Reduced or absent CYP2C19 function** means less prodrug is converted, so
  less active metabolite reaches the platelets. Platelet inhibition is weaker
  than intended. The clinical concern is therefore **therapeutic failure** —
  the drug not working — rather than the drug being toxic. Residual platelet
  reactivity remains high while the patient and clinician believe they are
  protected, which in the setting of recent stenting or acute coronary syndrome
  is where the risk of ischaemic events arises.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## codeine:Unknown

Gene/context: **CYP2D6 / Unknown**; stored label `Unknown` (historical; no broad safety endorsement).
Relevant genes: CYP2D6. CYP2D6 copy-number and structural variation is not called from the uploaded VCF in this application, so codeine guidance is not produced.

Primary source: [codeine source record](SOURCE-VERIFICATION.md#codeine); 2021; final edited form 2021-02-09; 110(4):888–896.
Pinned guideline: `PA166104996`, version `69`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `49c331da80040518ef10e648a9b40277ebcc43aadbde8cf4514d66e60e609aad`
- source_hash: `a0efc23c38910c7da7233884eb247a3309625295b871bc5e40200bf2eb5e1cf5`
- context_hash: `824c9e2c31759cebebae11c7d28fba910091bec8e144e8d3a74831c419188721`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

No recommendation recorded for Unknown; no matched source row claimed.

### Recorded recommendation (exact stored bytes as JSON string)

```json
""
```

Candidate pinned rows (matching text does not prove original selection):

- None.

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result for codeine is unknown, so we cannot explain how it will be handled by your body.",
  "mechanism": "Codeine is a prodrug that is converted into morphine by the enzyme CYP2D6, which is responsible for metabolizing a large share of commonly used drugs. The amount of morphine produced depends on how much CYP2D6 activity a person has.",
  "variant_rationale": "No genotype was called for codeine in this analysis, so there is no variant-level rationale to report.",
  "patient_friendly": "We don't know how your body will handle codeine because we can't determine how active the enzyme that breaks it down is in your body. This enzyme, CYP2D6, helps turn codeine into a different medicine that actually helps with pain. If you're taking codeine, it's best to speak with your doctor or pharmacist to understand how it will affect you."
}
```

### 439af963735c02e8 — summary

**Exact sentence / claim to assess:**

Your genetic result for codeine is unknown, so we cannot explain how it will be handled by your body.

Sentence UTF-8 SHA-256: `ed62733d834599965f7b87968cbf8faeee035567fe52c088c9bf58e285dfcbc7`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result for codeine is unknown, so we cannot explain how it will be handled by your body.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848051+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2D6_codeine.md` lines 56–59 (A structural note for the explanation layer):

```text
**PharmCAT cannot call CYP2D6 from an ordinary VCF.** The star alleles depend on
structural and copy-number variation that a VCF does not represent, so PharmCAT
reports `callSource: NONE` even when every CYP2D6 position is present in the
file. PharmaGuard therefore returns `Unknown` for codeine and states why.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 886082c9012d6c60 — mechanism

**Exact sentence / claim to assess:**

Codeine is a prodrug that is converted into morphine by the enzyme CYP2D6, which is responsible for metabolizing a large share of commonly used drugs.

Sentence UTF-8 SHA-256: `7150aac3e7549d10aad28f0e9f1341877661dcacc8fd1e11bcdae9b756048b90`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Codeine is a prodrug that is converted into morphine by the enzyme CYP2D6, which is responsible for metabolizing a large share of commonly used drugs.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "CYP2D6 is a hepatic cytochrome P450 enzyme responsible for metabolising a large share of commonly used drugs.",
  "basis_citation": "Annotation of CPIC Guideline for codeine and CYP2D6 — Crews KR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2D6, OPRM1, and COMT Genotypes and Select Opioid Therapy. Clin Pharmacol Ther (2021). PMID: 33387367",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2D6_codeine.md` lines 22–27 (What the gene product does):

```text
CYP2D6 is a hepatic cytochrome P450 enzyme responsible for metabolising a large
share of commonly used drugs. *CYP2D6* is unusually variable: as well as
single-nucleotide variants that alter or abolish activity, the gene is subject
to **whole-gene deletions and duplications**, so copy number differs between
people. Activity is conventionally summarised as an activity score derived from
both alleles.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 8016c0c335c310d5 — mechanism

**Exact sentence / claim to assess:**

The amount of morphine produced depends on how much CYP2D6 activity a person has.

Sentence UTF-8 SHA-256: `e835f574059b2416acfb67b9652838aada4edf13540ceacdb3e6731aa2275d86`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "The amount of morphine produced depends on how much CYP2D6 activity a person has.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Analgesia from codeine therefore depends almost entirely on how much CYP2D6 activity a person has.",
  "basis_citation": "Annotation of CPIC Guideline for codeine and CYP2D6 — Crews KR et al. Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2D6, OPRM1, and COMT Genotypes and Select Opioid Therapy. Clin Pharmacol Ther (2021). PMID: 33387367",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2D6_codeine.md` lines 31–34 (How the drug is handled):

```text
Codeine is a **prodrug** with little analgesic activity of its own. CYP2D6
O-demethylates a small fraction of a dose into morphine, and it is that morphine
that produces analgesia. Other routes (glucuronidation, CYP3A4) handle most of
the dose but do not produce the active compound.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### cf792672f88b468e — variant_rationale

**Exact sentence / claim to assess:**

No genotype was called for codeine in this analysis, so there is no variant-level rationale to report.

Sentence UTF-8 SHA-256: `81d005a978e92edca5186446d08cd5ae51f1374f98161a6cf052b24872b9347e`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "No genotype was called for codeine in this analysis, so there is no variant-level rationale to report.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848052+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2D6_codeine.md` lines 56–59 (A structural note for the explanation layer):

```text
**PharmCAT cannot call CYP2D6 from an ordinary VCF.** The star alleles depend on
structural and copy-number variation that a VCF does not represent, so PharmCAT
reports `callSource: NONE` even when every CYP2D6 position is present in the
file. PharmaGuard therefore returns `Unknown` for codeine and states why.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 3aba2ffda3dfdebb — patient_friendly

**Exact sentence / claim to assess:**

We don't know how your body will handle codeine because we can't determine how active the enzyme that breaks it down is in your body.

Sentence UTF-8 SHA-256: `122e909ead2bdf933ca7f3540cba02719b1773b97cc5a082026f1e91038f6dd7`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "We don't know how your body will handle codeine because we can't determine how active the enzyme that breaks it down is in your body.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848053+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2D6_codeine.md` lines 31–34 (How the drug is handled):

```text
Codeine is a **prodrug** with little analgesic activity of its own. CYP2D6
O-demethylates a small fraction of a dose into morphine, and it is that morphine
that produces analgesia. Other routes (glucuronidation, CYP3A4) handle most of
the dose but do not produce the active compound.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 4167c317eb19a0b4 — patient_friendly

**Exact sentence / claim to assess:**

This enzyme, CYP2D6, helps turn codeine into a different medicine that actually helps with pain.

Sentence UTF-8 SHA-256: `72e420067437c2e353d1439651ced15ff7382b03705a2638233450f465d96423`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This enzyme, CYP2D6, helps turn codeine into a different medicine that actually helps with pain.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848054+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2D6_codeine.md` lines 22–27 (What the gene product does):

```text
CYP2D6 is a hepatic cytochrome P450 enzyme responsible for metabolising a large
share of commonly used drugs. *CYP2D6* is unusually variable: as well as
single-nucleotide variants that alter or abolish activity, the gene is subject
to **whole-gene deletions and duplications**, so copy number differs between
people. Activity is conventionally summarised as an activity score derived from
both alleles.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### a6aa1b982ac99fe2 — patient_friendly

**Exact sentence / claim to assess:**

If you're taking codeine, it's best to speak with your doctor or pharmacist to understand how it will affect you.

Sentence UTF-8 SHA-256: `7e0876e148b7209fb50a32f566c6ecd00f6c311c0107dac8ecaf39d548d7f6c1`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you're taking codeine, it's best to speak with your doctor or pharmacist to understand how it will affect you.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848055+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2D6_codeine.md` lines 31–34 (How the drug is handled):

```text
Codeine is a **prodrug** with little analgesic activity of its own. CYP2D6
O-demethylates a small fraction of a dose into morphine, and it is that morphine
that produces analgesia. Other routes (glucuronidation, CYP3A4) handle most of
the dose but do not produce the active compound.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## fluorouracil:IM

Gene/context: **DPYD / IM**; stored label `Adjust Dosage` (historical; no broad safety endorsement).
Relevant genes: DPYD. Guidance is bounded to the CPIC annotation and the genomic evidence assessed by this application.

Primary source: [fluorouracil source record](SOURCE-VERIFICATION.md#fluorouracil); 2017 update; final edited form 2017-11-20; February 2018 issue, 103(2):210–216. See separate 2018 update and 2026 pending-update records.
Pinned guideline: `PA166122686`, version `53`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `5350de17a57b0f6d3e435eebabf6340a6daa587932a27d544fdd628aaddd215b`
- source_hash: `d0b8770a4494b6f7ca9ae2822d55cf4002047871219c4f80ee240c2e9f93efec`
- context_hash: `4465c229397014010d195686c78eb1f25ad863f07d02684cc60dff3b1a2d7694`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

1 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"Reduce starting dose by 50% followed by titration of dose based on toxicity or therapeutic drug monitoring (if available). Patients with the c.2846A&gt;T/c.2846A&gt;T genotype may require &gt;50% reduction in starting dose."
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166297898`; population `general`; lookup `[{"DPYD": "1.0"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result indicates that you are an Intermediate Metabolizer of fluorouracil. This means that you may be at increased risk for severe or even fatal drug toxicity when treated with this medication.",
  "mechanism": "DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism. DPD is responsible for breaking down fluorouracil into inactive metabolites. Reduced DPD activity slows inactivation, leading to higher and longer exposure to active drug, which can cause severe toxicity.",
  "variant_rationale": "PharmCAT called DPYD as {diplotype}, which corresponds to a Intermediate Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "If you're taking fluorouracil, your doctor may need to adjust your dosage based on your genetic result. This is because your body may not be able to break down the medication as well as others. Your doctor will work with you to find the right dose to minimize the risk of side effects."
}
```

### a2051c364d1f7875 — summary

**Exact sentence / claim to assess:**

Your genetic result indicates that you are an Intermediate Metabolizer of fluorouracil.

Sentence UTF-8 SHA-256: `24c81718a3bcd525d9a499fb860ced7893d2ff984f2c8af6354f2842c1cecc89`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result indicates that you are an Intermediate Metabolizer of fluorouracil.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848056+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 28–32 (How the drug is handled):

```text
Fluorouracil is a fluoropyrimidine antimetabolite. Only a small fraction of a
dose is converted into the cytotoxic nucleotides that disrupt DNA and RNA
synthesis in dividing cells; the rest is inactivated by DPD. Capecitabine is an
oral prodrug that is converted to fluorouracil in the body and is subject to the
same catabolic step.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 32bd81db5eb2a8cb — summary

**Exact sentence / claim to assess:**

This means that you may be at increased risk for severe or even fatal drug toxicity when treated with this medication.

Sentence UTF-8 SHA-256: `5b4c7c713890d6103ede45183464fbb6428e89a9174e4b70965890400ab19d0e`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "This means that you may be at increased risk for severe or even fatal drug toxicity when treated with this medication.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848057+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
  to active drug is higher and lasts longer for the same administered amount.
  Because fluoropyrimidines already have a narrow therapeutic window, this shows
  up as more severe toxicity — myelosuppression, mucositis, diarrhoea,
  hand-foot syndrome — rather than as loss of anticancer effect.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### f0e5d5bdbf2a2ed1 — mechanism

**Exact sentence / claim to assess:**

DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism.

Sentence UTF-8 SHA-256: `6fee0165edcfba7ceab53018e73fc6146acf39d4c7b28fe688cd9d143fb6449b`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "DPYD encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism.",
  "basis_citation": "Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 209025bd8e937007 — mechanism

**Exact sentence / claim to assess:**

DPD is responsible for breaking down fluorouracil into inactive metabolites.

Sentence UTF-8 SHA-256: `87ff6dfbc47d328aabbe099dd143ee64e86533c4178704704a36a5215bf79562`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "DPD is responsible for breaking down fluorouracil into inactive metabolites.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "DPD is expressed widely, with high activity in the liver, and is responsible for breaking down the great majority of an administered fluoropyrimidine dose into inactive metabolites.",
  "basis_citation": "Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 4c686eac9d3985ed — mechanism

**Exact sentence / claim to assess:**

Reduced DPD activity slows inactivation, leading to higher and longer exposure to active drug, which can cause severe toxicity.

Sentence UTF-8 SHA-256: `d2608dfbd78a99fde9f310ea2a2fb5e32927e76503b8d2b57060fc3fc0b6ecbc`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Reduced DPD activity slows inactivation, leading to higher and longer exposure to active drug, which can cause severe toxicity.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Reduced DPD activity (partial deficiency)** slows inactivation, so exposure to active drug is higher and lasts longer for the same administered amount.",
  "basis_citation": "Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729",
  "escalated": true,
  "escalation_reasons": [
    "causal"
  ],
  "escalation_detail": [
    "adds a causal step that may not be in the source (“cause”)"
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
  to active drug is higher and lasts longer for the same administered amount.
  Because fluoropyrimidines already have a narrow therapeutic window, this shows
  up as more severe toxicity — myelosuppression, mucositis, diarrhoea,
  hand-foot syndrome — rather than as loss of anticancer effect.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 49912aa25258ae89 — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called DPYD as {diplotype}, which corresponds to a Intermediate Metabolizer result.

Sentence UTF-8 SHA-256: `7188851f5ca54b74ed71424c5237df87913f3a23eb325e5319346e982792107f`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called DPYD as {diplotype}, which corresponds to a Intermediate Metabolizer result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848059+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 3a81c3ef20162a77 — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848059+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 7c1605942f79e995 — patient_friendly

**Exact sentence / claim to assess:**

If you're taking fluorouracil, your doctor may need to adjust your dosage based on your genetic result.

Sentence UTF-8 SHA-256: `d6be2b50b41a660c330f7036e7f37735a2e5efd4ceb99613e6cbd1be120bef53`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you're taking fluorouracil, your doctor may need to adjust your dosage based on your genetic result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848060+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 28–32 (How the drug is handled):

```text
Fluorouracil is a fluoropyrimidine antimetabolite. Only a small fraction of a
dose is converted into the cytotoxic nucleotides that disrupt DNA and RNA
synthesis in dividing cells; the rest is inactivated by DPD. Capecitabine is an
oral prodrug that is converted to fluorouracil in the body and is subject to the
same catabolic step.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 03f4fa5ef3869d25 — patient_friendly

**Exact sentence / claim to assess:**

This is because your body may not be able to break down the medication as well as others.

Sentence UTF-8 SHA-256: `8dec6b234686a6b38647851e3b272eecef69388c3e61fbf568fc0913c8b1f8c4`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This is because your body may not be able to break down the medication as well as others.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848062+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### e490223a20365af8 — patient_friendly

**Exact sentence / claim to assess:**

Your doctor will work with you to find the right dose to minimize the risk of side effects.

Sentence UTF-8 SHA-256: `3304c23bba4c78cfda6de303eec9f794e5ed17edd0e63bb68a57a03ffde0e6e5`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "Your doctor will work with you to find the right dose to minimize the risk of side effects.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848062+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## fluorouracil:NM

Gene/context: **DPYD / NM**; stored label `Safe` (historical; no broad safety endorsement).
Relevant genes: DPYD. Guidance is bounded to the CPIC annotation and the genomic evidence assessed by this application.

Primary source: [fluorouracil source record](SOURCE-VERIFICATION.md#fluorouracil); 2017 update; final edited form 2017-11-20; February 2018 issue, 103(2):210–216. See separate 2018 update and 2026 pending-update records.
Pinned guideline: `PA166122686`, version `53`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `2774def9190902cd0d3a06a5ebe858bb0cd7c73aaa45ec5e35408449f7b1c428`
- source_hash: `00c7a9f3b933989fca8c84397c3ab44b733ff80c545554dca03d5eaa3b136a6e`
- context_hash: `2696f2b3684005c9817d52ffdff77b6b9bcafdbe67acb126bd7118928a710b4d`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

1 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"Based on genotype, there is no indication to change dose or therapy. Use label-recommended dosage and administration."
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166297896`; population `general`; lookup `[{"DPYD": "2.0"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Based on your genetic result, there is no indication to change the dose or therapy for fluorouracil. Use the label-recommended dosage and administration.",
  "mechanism": "Fluorouracil is a type of chemotherapy that is broken down by an enzyme called dihydropyrimidine dehydrogenase (DPD). Your body's normal DPD activity helps to inactivate most of the drug, which reduces the risk of severe side effects. If you have normal DPD activity, the standard dose of fluorouracil is likely to be safe.",
  "variant_rationale": "PharmCAT called DPYD as {diplotype}, which corresponds to a Normal Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "Your genetic result shows that you are a normal metabolizer of fluorouracil. This means that your body is able to break down the drug in a normal way, which reduces the risk of severe side effects. You should be able to take the standard dose of fluorouracil without any problems. However, it's always best to speak with your doctor or pharmacist to confirm the best course of treatment for you."
}
```

### 5fc2d6166f138525 — summary

**Exact sentence / claim to assess:**

Based on your genetic result, there is no indication to change the dose or therapy for fluorouracil.

Sentence UTF-8 SHA-256: `e529fdb76e29c558fe3dd1bea0deb15ee4dc47adacd123ffd61a3279c5be0e00`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Based on your genetic result, there is no indication to change the dose or therapy for fluorouracil.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848063+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 28–32 (How the drug is handled):

```text
Fluorouracil is a fluoropyrimidine antimetabolite. Only a small fraction of a
dose is converted into the cytotoxic nucleotides that disrupt DNA and RNA
synthesis in dividing cells; the rest is inactivated by DPD. Capecitabine is an
oral prodrug that is converted to fluorouracil in the body and is subject to the
same catabolic step.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### a02b21fe1a497100 — summary

**Exact sentence / claim to assess:**

Use the label-recommended dosage and administration.

Sentence UTF-8 SHA-256: `3030a529209297498c605e85e66c6d79d54c4b488ccbc465b22b62447afc1a0b`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Use the label-recommended dosage and administration.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848064+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### d97e1d5d4d55e650 — mechanism

**Exact sentence / claim to assess:**

Fluorouracil is a type of chemotherapy that is broken down by an enzyme called dihydropyrimidine dehydrogenase (DPD).

Sentence UTF-8 SHA-256: `c48096316856f30d5ca02e81aa6eda206f6690670fd4bdb2019d06433a654c91`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Fluorouracil is a type of chemotherapy that is broken down by an enzyme called dihydropyrimidine dehydrogenase (DPD).",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme of pyrimidine catabolism.",
  "basis_citation": "Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### cc5100e3de4bbea8 — mechanism

**Exact sentence / claim to assess:**

Your body's normal DPD activity helps to inactivate most of the drug, which reduces the risk of severe side effects.

Sentence UTF-8 SHA-256: `5a7e4000cf7171b04820e5d0a92dc6dd329c61f99b0f13b4e8d7bdd4204f048c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Your body's normal DPD activity helps to inactivate most of the drug, which reduces the risk of severe side effects.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "",
  "basis_citation": "Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729",
  "escalated": true,
  "escalation_reasons": [
    "no-source"
  ],
  "escalation_detail": [
    "no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against."
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
  to active drug is higher and lasts longer for the same administered amount.
  Because fluoropyrimidines already have a narrow therapeutic window, this shows
  up as more severe toxicity — myelosuppression, mucositis, diarrhoea,
  hand-foot syndrome — rather than as loss of anticancer effect.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### f6a33adcf03be61a — mechanism

**Exact sentence / claim to assess:**

If you have normal DPD activity, the standard dose of fluorouracil is likely to be safe.

Sentence UTF-8 SHA-256: `7d0b6ea1402b32088546f2964e4345febd432a970b8b4841c35a977e5ebeaaa2`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "If you have normal DPD activity, the standard dose of fluorouracil is likely to be safe.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "DPD is expressed widely, with high activity in the liver, and is responsible for breaking down the great majority of an administered fluoropyrimidine dose into inactive metabolites.",
  "basis_citation": "Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729",
  "escalated": true,
  "escalation_reasons": [
    "safety-assertion"
  ],
  "escalation_detail": [
    "asserts SAFETY. Reassurance is the direction every defect in this project ran in, so an affirmative safety claim is never auto-accepted. (“is likely to be safe”)"
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- OVERBROAD_SAFETY: normal or other assessed PGx function does not establish general safety or assured efficacy; human reassessment requested, including existing bulk decisions.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 3f35b4d693b52e4f — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called DPYD as {diplotype}, which corresponds to a Normal Metabolizer result.

Sentence UTF-8 SHA-256: `22abeb324eaad47388611c27d337ee6c31e525d5311e0e1f6e717dfdfea1e539`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called DPYD as {diplotype}, which corresponds to a Normal Metabolizer result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848066+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 70184df6659a6f19 — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848067+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 89980a637fb7a392 — patient_friendly

**Exact sentence / claim to assess:**

Your genetic result shows that you are a normal metabolizer of fluorouracil.

Sentence UTF-8 SHA-256: `e6b1bd8bdabe292d31924a0b8ffaf975d872fbea96750eb9df4e5492ece28536`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "Your genetic result shows that you are a normal metabolizer of fluorouracil.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848068+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 28–32 (How the drug is handled):

```text
Fluorouracil is a fluoropyrimidine antimetabolite. Only a small fraction of a
dose is converted into the cytotoxic nucleotides that disrupt DNA and RNA
synthesis in dividing cells; the rest is inactivated by DPD. Capecitabine is an
oral prodrug that is converted to fluorouracil in the body and is subject to the
same catabolic step.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### f79ef39d60acfdbd — patient_friendly

**Exact sentence / claim to assess:**

This means that your body is able to break down the drug in a normal way, which reduces the risk of severe side effects.

Sentence UTF-8 SHA-256: `83e2ba1695a3b90c63ff9c7f09e4b35837a4ba34da92004e2d81a4eb2df12709`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This means that your body is able to break down the drug in a normal way, which reduces the risk of severe side effects.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848068+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
  to active drug is higher and lasts longer for the same administered amount.
  Because fluoropyrimidines already have a narrow therapeutic window, this shows
  up as more severe toxicity — myelosuppression, mucositis, diarrhoea,
  hand-foot syndrome — rather than as loss of anticancer effect.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### cfb556184673f3c9 — patient_friendly

**Exact sentence / claim to assess:**

You should be able to take the standard dose of fluorouracil without any problems.

Sentence UTF-8 SHA-256: `49d2d7119468ac1a614e0e826eff82705ea0d210833e5359e50b7e0d54efa8e1`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "You should be able to take the standard dose of fluorouracil without any problems.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848069+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 28–32 (How the drug is handled):

```text
Fluorouracil is a fluoropyrimidine antimetabolite. Only a small fraction of a
dose is converted into the cytotoxic nucleotides that disrupt DNA and RNA
synthesis in dividing cells; the rest is inactivated by DPD. Capecitabine is an
oral prodrug that is converted to fluorouracil in the body and is subject to the
same catabolic step.
```

Flags (automated/editorial triage, no adjudication):

- OVERBROAD_SAFETY: normal or other assessed PGx function does not establish general safety or assured efficacy; human reassessment requested, including existing bulk decisions.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### e641e2ad3db493f4 — patient_friendly

**Exact sentence / claim to assess:**

However, it's always best to speak with your doctor or pharmacist to confirm the best course of treatment for you.

Sentence UTF-8 SHA-256: `996a8ac4b7065188690d1eee9ab2952aae99a37f13084d95bd38894915df2abe`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "However, it's always best to speak with your doctor or pharmacist to confirm the best course of treatment for you.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848070+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## fluorouracil:PM

Gene/context: **DPYD / PM**; stored label `Toxic` (historical; no broad safety endorsement).
Relevant genes: DPYD. Guidance is bounded to the CPIC annotation and the genomic evidence assessed by this application.

Primary source: [fluorouracil source record](SOURCE-VERIFICATION.md#fluorouracil); 2017 update; final edited form 2017-11-20; February 2018 issue, 103(2):210–216. See separate 2018 update and 2026 pending-update records.
Pinned guideline: `PA166122686`, version `53`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `9ddea44ad8cceee5dec2fa4e2b5d2a0b4e5b14e305fc505ba289ca0920aaca14`
- source_hash: `49993401cc1118f17749bcf48b3409b8ef38ae9edafee9c73f809d696cc5f038`
- context_hash: `23de0e85aff6fc28b94de98e4fe6d15c27a1dc61744fcb4429ae9aced461697c`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

1 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"Avoid use of 5-fluorouracil or 5-fluorouracil prodrug-based regimens."
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166297900`; population `general`; lookup `[{"DPYD": "0.0"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result indicates that you are at a higher risk for severe or even fatal drug toxicity when treated with fluoropyrimidine drugs, such as fluorouracil.",
  "mechanism": "The enzyme dihydropyrimidine dehydrogenase (DPD) is responsible for breaking down fluorouracil into inactive metabolites. If DPD activity is reduced or absent, the drug persists in the body for a longer period, leading to increased exposure and toxicity.",
  "variant_rationale": "PharmCAT called DPYD as {diplotype}, which corresponds to a Poor Metabolizer result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "If you have a genetic result that shows you're at risk for severe side effects from certain cancer medications, it's best to talk to your doctor or pharmacist about alternative treatment options. They can help you make an informed decision about your care."
}
```

### 6b811a379c754241 — summary

**Exact sentence / claim to assess:**

Your genetic result indicates that you are at a higher risk for severe or even fatal drug toxicity when treated with fluoropyrimidine drugs, such as fluorouracil.

Sentence UTF-8 SHA-256: `889262dc6ce0117c977ce0cfa136ff75d25853e40cd048bcfbdd56685094b3f7`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result indicates that you are at a higher risk for severe or even fatal drug toxicity when treated with fluoropyrimidine drugs, such as fluorouracil.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848071+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
  to active drug is higher and lasts longer for the same administered amount.
  Because fluoropyrimidines already have a narrow therapeutic window, this shows
  up as more severe toxicity — myelosuppression, mucositis, diarrhoea,
  hand-foot syndrome — rather than as loss of anticancer effect.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 57cc7bb323e4726a — mechanism

**Exact sentence / claim to assess:**

The enzyme dihydropyrimidine dehydrogenase (DPD) is responsible for breaking down fluorouracil into inactive metabolites.

Sentence UTF-8 SHA-256: `ad493a8c024510f08e52caac5e8a96878386032ab8f2a2132b43eef69c9cbd7f`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "The enzyme dihydropyrimidine dehydrogenase (DPD) is responsible for breaking down fluorouracil into inactive metabolites.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "DPD is expressed widely, with high activity in the liver, and is responsible for breaking down the great majority of an administered fluoropyrimidine dose into inactive metabolites.",
  "basis_citation": "Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### d076a6b436b3a0be — mechanism

**Exact sentence / claim to assess:**

If DPD activity is reduced or absent, the drug persists in the body for a longer period, leading to increased exposure and toxicity.

Sentence UTF-8 SHA-256: `ada9e3d2e718920ea44817b52eaa39653b0f47ad784f79183b3b2abf61e94193`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "If DPD activity is reduced or absent, the drug persists in the body for a longer period, leading to increased exposure and toxicity.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Reduced DPD activity (partial deficiency)** slows inactivation, so exposure to active drug is higher and lasts longer for the same administered amount.",
  "basis_citation": "Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
  to active drug is higher and lasts longer for the same administered amount.
  Because fluoropyrimidines already have a narrow therapeutic window, this shows
  up as more severe toxicity — myelosuppression, mucositis, diarrhoea,
  hand-foot syndrome — rather than as loss of anticancer effect.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 88f28647f0c3e2e4 — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called DPYD as {diplotype}, which corresponds to a Poor Metabolizer result.

Sentence UTF-8 SHA-256: `ed8ffbe631693a21f10187f17e1ccdd5e1ae2b882c69eb0d1572acedd8b0348a`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called DPYD as {diplotype}, which corresponds to a Poor Metabolizer result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848072+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### cc1c491a73270387 — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848073+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 72e1aa60e346aa64 — patient_friendly

**Exact sentence / claim to assess:**

If you have a genetic result that shows you're at risk for severe side effects from certain cancer medications, it's best to talk to your doctor or pharmacist about alternative treatment options.

Sentence UTF-8 SHA-256: `b5e3fb31f8e4e1656291ea0ed02ce396624eb29b459f347be2cc1503dab19918`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you have a genetic result that shows you're at risk for severe side effects from certain cancer medications, it's best to talk to your doctor or pharmacist about alternative treatment options.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848074+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
  to active drug is higher and lasts longer for the same administered amount.
  Because fluoropyrimidines already have a narrow therapeutic window, this shows
  up as more severe toxicity — myelosuppression, mucositis, diarrhoea,
  hand-foot syndrome — rather than as loss of anticancer effect.
```

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 0c182fb59e78ad88 — patient_friendly

**Exact sentence / claim to assess:**

They can help you make an informed decision about your care.

Sentence UTF-8 SHA-256: `f30a8bc14b77238941f7ad60a8e73ca61486aa03d67ff2d6d710daf0b7cfa0ca`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "They can help you make an informed decision about your care.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848075+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## fluorouracil:Unknown

Gene/context: **DPYD / Unknown**; stored label `Unknown` (historical; no broad safety endorsement).
Relevant genes: DPYD. Guidance is bounded to the CPIC annotation and the genomic evidence assessed by this application.

Primary source: [fluorouracil source record](SOURCE-VERIFICATION.md#fluorouracil); 2017 update; final edited form 2017-11-20; February 2018 issue, 103(2):210–216. See separate 2018 update and 2026 pending-update records.
Pinned guideline: `PA166122686`, version `53`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `662b68148b27837a8e5f601c8700764c938d58add76e78dd043a47e25fe195a5`
- source_hash: `c1c57c85db15890f865f17a635d7bad8a8971a977ac8841bffc7cd10b2f08791`
- context_hash: `180f2336a87624bb2f7226c3b97616222411ba52933188a4ab1ccc48c8004457`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

No recommendation recorded for Unknown; no matched source row claimed.

### Recorded recommendation (exact stored bytes as JSON string)

```json
""
```

Candidate pinned rows (matching text does not prove original selection):

- None.

### Complete entry text — review all four fields

```json
{
  "summary": "The mechanism behind how your genetic result affects fluorouracil is related to how the body breaks down the drug. Fluorouracil is inactivated by an enzyme called dihydropyrimidine dehydrogenase (DPD). If this enzyme is not working properly, the drug can build up in the body and cause more severe side effects.",
  "mechanism": "Fluorouracil is a type of chemotherapy that works by disrupting DNA and RNA synthesis in dividing cells. The enzyme dihydropyrimidine dehydrogenase (DPD) is responsible for breaking down most of the drug into inactive metabolites. If DPD is not working properly, the drug can persist in the body for longer and cause more severe side effects.",
  "variant_rationale": "No genotype was called for fluorouracil in this analysis, so there is no variant-level rationale to report.",
  "patient_friendly": "If you have a problem with the way your body breaks down fluorouracil, you may experience more severe side effects. This is because the drug can build up in your body and cause problems. It's always best to speak with your doctor or pharmacist about any concerns you have about your medication."
}
```

### e2086357f2e9905d — summary

**Exact sentence / claim to assess:**

The mechanism behind how your genetic result affects fluorouracil is related to how the body breaks down the drug.

Sentence UTF-8 SHA-256: `49823a64a8dfed5c327583ec658e405bc8f27386efded1ef3574edd62bd0a11f`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "The mechanism behind how your genetic result affects fluorouracil is related to how the body breaks down the drug.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848076+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 28–32 (How the drug is handled):

```text
Fluorouracil is a fluoropyrimidine antimetabolite. Only a small fraction of a
dose is converted into the cytotoxic nucleotides that disrupt DNA and RNA
synthesis in dividing cells; the rest is inactivated by DPD. Capecitabine is an
oral prodrug that is converted to fluorouracil in the body and is subject to the
same catabolic step.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### ce72ff537b35602c — summary

**Exact sentence / claim to assess:**

Fluorouracil is inactivated by an enzyme called dihydropyrimidine dehydrogenase (DPD).

Sentence UTF-8 SHA-256: `e151a61d1488f08f2dddde4a646309f67241902037154f55f269467c24b60dde`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Fluorouracil is inactivated by an enzyme called dihydropyrimidine dehydrogenase (DPD).",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848077+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### f806b02130f8c581 — summary

**Exact sentence / claim to assess:**

If this enzyme is not working properly, the drug can build up in the body and cause more severe side effects.

Sentence UTF-8 SHA-256: `4daf9e9ff0845af1b33b174fd83af64b8d8188e17edf1aee2666dc7b62ffd0b1`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "If this enzyme is not working properly, the drug can build up in the body and cause more severe side effects.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848077+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
  to active drug is higher and lasts longer for the same administered amount.
  Because fluoropyrimidines already have a narrow therapeutic window, this shows
  up as more severe toxicity — myelosuppression, mucositis, diarrhoea,
  hand-foot syndrome — rather than as loss of anticancer effect.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### a06bd63d14a618ed — mechanism

**Exact sentence / claim to assess:**

Fluorouracil is a type of chemotherapy that works by disrupting DNA and RNA synthesis in dividing cells.

Sentence UTF-8 SHA-256: `d65545898ae2c78248134496b8134ed3b40ead584d1996203eb86b219f673bf0`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Fluorouracil is a type of chemotherapy that works by disrupting DNA and RNA synthesis in dividing cells.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Only a small fraction of a dose is converted into the cytotoxic nucleotides that disrupt DNA and RNA synthesis in dividing cells; the rest is inactivated by DPD.",
  "basis_citation": "Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 28–32 (How the drug is handled):

```text
Fluorouracil is a fluoropyrimidine antimetabolite. Only a small fraction of a
dose is converted into the cytotoxic nucleotides that disrupt DNA and RNA
synthesis in dividing cells; the rest is inactivated by DPD. Capecitabine is an
oral prodrug that is converted to fluorouracil in the body and is subject to the
same catabolic step.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### c93d885464821d40 — mechanism

**Exact sentence / claim to assess:**

The enzyme dihydropyrimidine dehydrogenase (DPD) is responsible for breaking down most of the drug into inactive metabolites.

Sentence UTF-8 SHA-256: `eef9b1e14897b458187b3e565a5a0b5d6f174666471dc22c44fb2e213564a19f`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "The enzyme dihydropyrimidine dehydrogenase (DPD) is responsible for breaking down most of the drug into inactive metabolites.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "DPD is expressed widely, with high activity in the liver, and is responsible for breaking down the great majority of an administered fluoropyrimidine dose into inactive metabolites.",
  "basis_citation": "Annotation of CPIC Guideline for fluorouracil and DPYD — Amstutz U et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Dihydropyrimidine Dehydrogenase Genotype and Fluoropyrimidine Dosing: 2017 Update. Clin Pharmacol Ther (2018). PMID: 29152729",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 21–24 (What the gene product does):

```text
*DPYD* encodes dihydropyrimidine dehydrogenase (DPD), the rate-limiting enzyme
of pyrimidine catabolism. DPD is expressed widely, with high activity in the
liver, and is responsible for breaking down the great majority of an
administered fluoropyrimidine dose into inactive metabolites.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### b4c12f957c807452 — mechanism

**Exact sentence / claim to assess:**

If DPD is not working properly, the drug can persist in the body for longer and cause more severe side effects.

Sentence UTF-8 SHA-256: `9b470eadb83cfb23844a026731e7cc0a256055604e0943347e44c49f00e67e9c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "If DPD is not working properly, the drug can persist in the body for longer and cause more severe side effects.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "",
  "basis_citation": "",
  "escalated": true,
  "escalation_reasons": [
    "no-source"
  ],
  "escalation_detail": [
    "no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against."
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
  to active drug is higher and lasts longer for the same administered amount.
  Because fluoropyrimidines already have a narrow therapeutic window, this shows
  up as more severe toxicity — myelosuppression, mucositis, diarrhoea,
  hand-foot syndrome — rather than as loss of anticancer effect.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### c65289189f7ea4dd — variant_rationale

**Exact sentence / claim to assess:**

No genotype was called for fluorouracil in this analysis, so there is no variant-level rationale to report.

Sentence UTF-8 SHA-256: `5540c538c735b7665f25be3954a2a1d79b4df43a7dbbeb2d49422b54a118480c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "No genotype was called for fluorouracil in this analysis, so there is no variant-level rationale to report.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848079+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 28–32 (How the drug is handled):

```text
Fluorouracil is a fluoropyrimidine antimetabolite. Only a small fraction of a
dose is converted into the cytotoxic nucleotides that disrupt DNA and RNA
synthesis in dividing cells; the rest is inactivated by DPD. Capecitabine is an
oral prodrug that is converted to fluorouracil in the body and is subject to the
same catabolic step.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 0c7edd1a6064f039 — patient_friendly

**Exact sentence / claim to assess:**

If you have a problem with the way your body breaks down fluorouracil, you may experience more severe side effects.

Sentence UTF-8 SHA-256: `e9f06a6fd4003e88839c59f516cf9e6cec07ae66ca2bf88fe65748de457e9130`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you have a problem with the way your body breaks down fluorouracil, you may experience more severe side effects.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848080+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/DPYD_fluorouracil.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced DPD activity (partial deficiency)** slows inactivation, so exposure
  to active drug is higher and lasts longer for the same administered amount.
  Because fluoropyrimidines already have a narrow therapeutic window, this shows
  up as more severe toxicity — myelosuppression, mucositis, diarrhoea,
  hand-foot syndrome — rather than as loss of anticancer effect.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 112b531a5a857190 — patient_friendly

**Exact sentence / claim to assess:**

This is because the drug can build up in your body and cause problems.

Sentence UTF-8 SHA-256: `669c4f5ae9eb455a9cda26f397dde8353e5ba102148cf074ad4bd5b7f05d8579`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `SUPPORT_NOT_LOCATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This is because the drug can build up in your body and cause problems.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848081+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### c4ba4a497b7d0488 — patient_friendly

**Exact sentence / claim to assess:**

It's always best to speak with your doctor or pharmacist about any concerns you have about your medication.

Sentence UTF-8 SHA-256: `b2eab6757d7b8b9b8f0cb817a9b9d71e20339f02c0cfc6e3bbe4cc1c5c9bbcf9`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `SUPPORT_NOT_LOCATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "It's always best to speak with your doctor or pharmacist about any concerns you have about your medication.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848081+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- VERSION_ADVISORY: original 2017 paper, 2018 update, and pending 2026 notice differ; review pinned source without silently upgrading definitions.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## simvastatin:IM

Gene/context: **SLCO1B1 / IM**; stored label `Adjust Dosage` (historical; no broad safety endorsement).
Relevant genes: SLCO1B1. SLCO1B1 is a transporter; the result must not be described as a metabolizer phenotype.

Primary source: [simvastatin source record](SOURCE-VERIFICATION.md#simvastatin); 2022; final edited form 2022-03-11; May 2022 issue, 111(5):1007–1021.
Pinned guideline: `PA166105005`, version `57`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `13f0895bcaaae4f3ec90c60df817513894b78a3379d5d82747eff17f6a13b116`
- source_hash: `94451ddf0721f987f6351d27b73657c19714049e91a6af7895afef46b58b5844`
- context_hash: `a9679a76bbe19c97391ab3e724a13c78a402161564a3cd779c84aad478a7055b`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

2 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"Prescribe an alternative statin depending on the desired potency (see Figure 1 of PMID: 35152405 for recommendations for alternative statins). If simvastatin therapy is warranted, limit dose to &lt;20mg/day."
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166298503`; population `general`; lookup `[{"SLCO1B1": "Possible Decreased Function"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166298504`; population `general`; lookup `[{"SLCO1B1": "Decreased Function"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result affects how your body handles simvastatin, a type of statin medication. This can increase your risk of muscle toxicity.",
  "mechanism": "SLCO1B1 encodes OATP1B1, a hepatic uptake transporter that moves drugs out of portal blood and into liver cells. Efficient hepatic uptake delivers the drug to its target and keeps systemic exposure low. Reduced OATP1B1 function means less of each dose is taken up by the liver, leading to higher systemic exposure and muscle toxicity.",
  "variant_rationale": "PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Decreased Function result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "If you have this genetic result, your doctor may want to prescribe a different statin or limit the dose of simvastatin to less than 20mg per day. This is because your body may not be able to remove simvastatin from the circulation into the liver as efficiently as usual. This can increase your risk of muscle problems. Be sure to talk to your doctor or pharmacist about your genetic result and how it may affect your medication."
}
```

### b17abd6bf5ed6ada — summary

**Exact sentence / claim to assess:**

Your genetic result affects how your body handles simvastatin, a type of statin medication.

Sentence UTF-8 SHA-256: `9a73168e5662a12f60fb8955bd91dfa908a4d9db72d06507dcc895bb0f4183a7`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result affects how your body handles simvastatin, a type of statin medication.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848082+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 30–32 (How the drug is handled):

```text
Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
its site of action and its route of elimination. OATP1B1 performs the uptake
step that concentrates the drug (chiefly its active acid form) into liver cells.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### eb429db49bbc3fbc — summary

**Exact sentence / claim to assess:**

This can increase your risk of muscle toxicity.

Sentence UTF-8 SHA-256: `b8a7da74a0664d57ee9d08b5f2bcb995872f4e495326751e625aaf800d32c744`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "This can increase your risk of muscle toxicity.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848083+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 27243bc4a155917f — mechanism

**Exact sentence / claim to assess:**

SLCO1B1 encodes OATP1B1, a hepatic uptake transporter that moves drugs out of portal blood and into liver cells.

Sentence UTF-8 SHA-256: `566e382884d99b5619c5fa3bee3fe7d4fe995c0886934e3d129f5ddf5df46e52`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "SLCO1B1 encodes OATP1B1, a hepatic uptake transporter that moves drugs out of portal blood and into liver cells.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing) membrane of liver cells.",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 22–26 (What the gene product does):

```text
*SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing)
membrane of liver cells. Its job is to move drugs out of portal blood and into
hepatocytes. It is a **transporter, not a metabolising enzyme**, which is why
its phenotypes are described as function categories (normal, decreased, poor
function) rather than metaboliser categories.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### fe7c7e670d319fd4 — mechanism

**Exact sentence / claim to assess:**

Efficient hepatic uptake delivers the drug to its target and keeps systemic exposure low.

Sentence UTF-8 SHA-256: `f2f9f1a8674c564876f17f0c100e780d589333f7613031398f173108826be562`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Efficient hepatic uptake delivers the drug to its target and keeps systemic exposure low.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Efficient hepatic uptake therefore does two things at once: it delivers the drug to its target, and it keeps systemic — particularly skeletal muscle — exposure low.",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 34–36 (How the drug is handled):

```text
Efficient hepatic uptake therefore does two things at once: it delivers the drug
to its target, and it keeps systemic — particularly skeletal muscle — exposure
low.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 4bcc4de28daf8561 — mechanism

**Exact sentence / claim to assess:**

Reduced OATP1B1 function means less of each dose is taken up by the liver, leading to higher systemic exposure and muscle toxicity.

Sentence UTF-8 SHA-256: `3a1b729f49b0528494247c966cbe92f5606cbc4760f7075f26ae679b363affa3`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Reduced OATP1B1 function means less of each dose is taken up by the liver, leading to higher systemic exposure and muscle toxicity.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Reduced OATP1B1 function** means less of each dose is taken up by the liver, so more circulates systemically.",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### f0dbf62e453398c1 — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Decreased Function result.

Sentence UTF-8 SHA-256: `88015c2df282ac161b5d501192162e1a1277f3434518347a7bee5f32d2b0560d`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Decreased Function result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848084+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 22–26 (What the gene product does):

```text
*SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing)
membrane of liver cells. Its job is to move drugs out of portal blood and into
hepatocytes. It is a **transporter, not a metabolising enzyme**, which is why
its phenotypes are described as function categories (normal, decreased, poor
function) rather than metaboliser categories.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 9b320b6d1cc1f8a4 — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848085+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 55–59 (Notes for the explanation layer):

```text
- Describe OATP1B1 as a hepatic uptake transporter; avoid calling it a
  metabolising enzyme or describing "metaboliser status" for this gene.
- CPIC's 2022 guideline frames the outcome as statin-associated musculoskeletal
  symptoms; that is the phrasing to mirror.
- Dose ceilings and alternative statins are CPIC's to state at runtime.
```

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### f814d9253ead348d — patient_friendly

**Exact sentence / claim to assess:**

If you have this genetic result, your doctor may want to prescribe a different statin or limit the dose of simvastatin to less than 20mg per day.

Sentence UTF-8 SHA-256: `cd18e3fbcd377e33cff028f1fd092900c155a8a6b646b131231de7c9e026e655`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you have this genetic result, your doctor may want to prescribe a different statin or limit the dose of simvastatin to less than 20mg per day.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848086+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### c70e7c55c5ecf9e5 — patient_friendly

**Exact sentence / claim to assess:**

This is because your body may not be able to remove simvastatin from the circulation into the liver as efficiently as usual.

Sentence UTF-8 SHA-256: `6798b2a02f88dd1dc7c554613d3cf78753a6f4ddcfc7cf26a74f34350a080343`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This is because your body may not be able to remove simvastatin from the circulation into the liver as efficiently as usual.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848087+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 49–51 (Why altered function changes the outcome):

```text
Note the direction of the effect: the problem is not that the drug is cleared
too slowly by an enzyme, but that it is *not removed from the circulation into
the liver* fast enough.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 805083cf06618917 — patient_friendly

**Exact sentence / claim to assess:**

This can increase your risk of muscle problems.

Sentence UTF-8 SHA-256: `1e0c48481cefc825045488fb3d4a787d4b0f0eae725aa0aa2c643fb4a7ab5f40`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This can increase your risk of muscle problems.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848088+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 34–36 (How the drug is handled):

```text
Efficient hepatic uptake therefore does two things at once: it delivers the drug
to its target, and it keeps systemic — particularly skeletal muscle — exposure
low.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 21fe71707159b6f0 — patient_friendly

**Exact sentence / claim to assess:**

Be sure to talk to your doctor or pharmacist about your genetic result and how it may affect your medication.

Sentence UTF-8 SHA-256: `dc6fc6f97f4f1325d7fd6ea8fbd3b970c35cc300007a415cfa7495ca956d16cf`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "Be sure to talk to your doctor or pharmacist about your genetic result and how it may affect your medication.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848089+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## simvastatin:NM

Gene/context: **SLCO1B1 / NM**; stored label `Safe` (historical; no broad safety endorsement).
Relevant genes: SLCO1B1. SLCO1B1 is a transporter; the result must not be described as a metabolizer phenotype.

Primary source: [simvastatin source record](SOURCE-VERIFICATION.md#simvastatin); 2022; final edited form 2022-03-11; May 2022 issue, 111(5):1007–1021.
Pinned guideline: `PA166105005`, version `57`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `b6dd45959e8ed30ff61b1a718e8a2b4737ec5fb935090db2a6214adb1c65f8bd`
- source_hash: `0d3f7124a484ee3fbd4e8ef1ddf9702d7f63d0327f50c02ff92204a2c90584f3`
- context_hash: `051ce9608867035acaf65bc548db0ed8af6ef3e24fa617783c440b01380b387a`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

2 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"Prescribe desired starting dose and adjust doses based on disease-specific guidelines."
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166298501`; population `general`; lookup `[{"SLCO1B1": "Increased Function"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`
- `PA166298502`; population `general`; lookup `[{"SLCO1B1": "Normal Function"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result does not affect the typical risk of muscle toxicity from simvastatin. You can be prescribed the desired starting dose and adjust doses based on disease-specific guidelines.",
  "mechanism": "Simvastatin is a statin that works by inhibiting an enzyme inside liver cells. The liver's ability to take up simvastatin is important for keeping systemic exposure low and reducing the risk of muscle toxicity. Your genetic result does not affect the liver's ability to take up simvastatin, so the typical risk of muscle toxicity remains.",
  "variant_rationale": "PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Normal Function result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "You don't have a genetic variation that affects how your body handles simvastatin. This means you can take the usual dose and adjust it based on your disease and how you're responding to the medication. It's always a good idea to talk to your doctor or pharmacist about your specific situation and any concerns you may have."
}
```

### c388d20d9b0d9349 — summary

**Exact sentence / claim to assess:**

Your genetic result does not affect the typical risk of muscle toxicity from simvastatin.

Sentence UTF-8 SHA-256: `2d0f71e8bdf1a44cb4c6f79a94638eb09f359f942b3197c256fd8b1cc93b4360`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result does not affect the typical risk of muscle toxicity from simvastatin.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848090+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 38fb8eb70e106d2b — summary

**Exact sentence / claim to assess:**

You can be prescribed the desired starting dose and adjust doses based on disease-specific guidelines.

Sentence UTF-8 SHA-256: `4b471a4018152fc65cc91ffecc83bc9d3f0cfbcbbd524af59498fa35b86879d5`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "You can be prescribed the desired starting dose and adjust doses based on disease-specific guidelines.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848091+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 55–59 (Notes for the explanation layer):

```text
- Describe OATP1B1 as a hepatic uptake transporter; avoid calling it a
  metabolising enzyme or describing "metaboliser status" for this gene.
- CPIC's 2022 guideline frames the outcome as statin-associated musculoskeletal
  symptoms; that is the phrasing to mirror.
- Dose ceilings and alternative statins are CPIC's to state at runtime.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 25416be57490f44a — mechanism

**Exact sentence / claim to assess:**

Simvastatin is a statin that works by inhibiting an enzyme inside liver cells.

Sentence UTF-8 SHA-256: `d1401aeb4e73f124f0d9f08880d7b94c08c2b6594e0393a320c0ec9ed0f5894e`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Simvastatin is a statin that works by inhibiting an enzyme inside liver cells.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both its site of action and its route of elimination.",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 30–32 (How the drug is handled):

```text
Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
its site of action and its route of elimination. OATP1B1 performs the uptake
step that concentrates the drug (chiefly its active acid form) into liver cells.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 32cae19aa16d96b3 — mechanism

**Exact sentence / claim to assess:**

The liver's ability to take up simvastatin is important for keeping systemic exposure low and reducing the risk of muscle toxicity.

Sentence UTF-8 SHA-256: `b61d529f7edbfc67fe9dfe45f540671304ff51e88af77e909954942b5760be0d`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "The liver's ability to take up simvastatin is important for keeping systemic exposure low and reducing the risk of muscle toxicity.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Efficient hepatic uptake therefore does two things at once: it delivers the drug to its target, and it keeps systemic — particularly skeletal muscle — exposure low.",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": true,
  "escalation_reasons": [
    "comparative"
  ],
  "escalation_detail": [
    "makes a comparative or graded risk claim (“reducing the risk”)"
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### c652d05d0f500268 — mechanism

**Exact sentence / claim to assess:**

Your genetic result does not affect the liver's ability to take up simvastatin, so the typical risk of muscle toxicity remains.

Sentence UTF-8 SHA-256: `5853322f20a97cc68e267512a3726d532dd11e2ffbe6adf2d2e4dae7e5f98547`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Your genetic result does not affect the liver's ability to take up simvastatin, so the typical risk of muscle toxicity remains.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "The concern is **muscle toxicity**, driven by drug that failed to reach the liver.",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": true,
  "escalation_reasons": [
    "absence"
  ],
  "escalation_detail": [
    "claims an ABSENCE. Invisible to every automated check here: it carries no assertion marker and contradicts no directive, and it errs toward reassurance. Always escalated. (“does not”)"
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 003198218644a1fe — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Normal Function result.

Sentence UTF-8 SHA-256: `24f44ddeed6e8c5e3899ac3219c4087b0576eca0e4443266a1777d3d2d1a26b1`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Normal Function result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848092+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 22–26 (What the gene product does):

```text
*SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing)
membrane of liver cells. Its job is to move drugs out of portal blood and into
hepatocytes. It is a **transporter, not a metabolising enzyme**, which is why
its phenotypes are described as function categories (normal, decreased, poor
function) rather than metaboliser categories.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### af82180a64d830aa — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848093+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 55–59 (Notes for the explanation layer):

```text
- Describe OATP1B1 as a hepatic uptake transporter; avoid calling it a
  metabolising enzyme or describing "metaboliser status" for this gene.
- CPIC's 2022 guideline frames the outcome as statin-associated musculoskeletal
  symptoms; that is the phrasing to mirror.
- Dose ceilings and alternative statins are CPIC's to state at runtime.
```

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### bdaf0b2506069fe3 — patient_friendly

**Exact sentence / claim to assess:**

You don't have a genetic variation that affects how your body handles simvastatin.

Sentence UTF-8 SHA-256: `3db87c0bebd9389f5ca3690b6d876e9576f2193dbaeb52f82441b751c9d54584`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "You don't have a genetic variation that affects how your body handles simvastatin.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848094+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 30–32 (How the drug is handled):

```text
Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
its site of action and its route of elimination. OATP1B1 performs the uptake
step that concentrates the drug (chiefly its active acid form) into liver cells.
```

Flags (automated/editorial triage, no adjudication):

- OVERBROAD_GENETIC_ABSENCE: assessed normal function does not establish absence of all relevant variation.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 88a710100765ed32 — patient_friendly

**Exact sentence / claim to assess:**

This means you can take the usual dose and adjust it based on your disease and how you're responding to the medication.

Sentence UTF-8 SHA-256: `04305aa95184ff315af628b001706415a6862dd2d8a3c59120a38827191029cc`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This means you can take the usual dose and adjust it based on your disease and how you're responding to the medication.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848095+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 01a370b76f7e36ed — patient_friendly

**Exact sentence / claim to assess:**

It's always a good idea to talk to your doctor or pharmacist about your specific situation and any concerns you may have.

Sentence UTF-8 SHA-256: `db0f569561d1ce62635c0ccff5382d3d398d10d85663fe51b358bcec2d35587f`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "It's always a good idea to talk to your doctor or pharmacist about your specific situation and any concerns you may have.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848096+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## simvastatin:PM

Gene/context: **SLCO1B1 / PM**; stored label `Adjust Dosage` (historical; no broad safety endorsement).
Relevant genes: SLCO1B1. SLCO1B1 is a transporter; the result must not be described as a metabolizer phenotype.

Primary source: [simvastatin source record](SOURCE-VERIFICATION.md#simvastatin); 2022; final edited form 2022-03-11; May 2022 issue, 111(5):1007–1021.
Pinned guideline: `PA166105005`, version `57`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `7a9a3d57d44821ae145e079562dcd96bfd2ba11c89f7b3091955805593b00f99`
- source_hash: `7e3b743be1ae79ff8e047a327ca8659a4d5108d794d4319b25a67e0700c0c14a`
- context_hash: `660f73f4984ebcadb1f6a7a78e47337db57d68ffdfcb6dec7170a1a750eb0c65`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

1 candidate row(s) match recommendation text. Store has no row ID/population/paired phenotype binding; reviewer must assess applicability.

### Recorded recommendation (exact stored bytes as JSON string)

```json
"Prescribe an alternative statin depending on the desired potency (see Figure 1 of PMID: 35152405 for recommendations for alternative statins)."
```

Candidate pinned rows (matching text does not prove original selection):

- `PA166298505`; population `general`; lookup `[{"SLCO1B1": "Poor Function"}]`; classification `{"term": "Strong", "termId": "guidelineStrength:981501930"}`

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result suggests that you may be at increased risk for muscle toxicity when taking simvastatin.",
  "mechanism": "The OATP1B1 transporter, which helps remove simvastatin from the bloodstream into the liver, is not functioning properly in your body. This leads to higher levels of simvastatin in the bloodstream, which can cause muscle toxicity.",
  "variant_rationale": "PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Poor Function result. The non-reference positions supporting this call were no non-reference variants were detected.",
  "patient_friendly": "Your doctor may want to consider a different type of statin that is safer for you to take. This is because your body is not able to remove simvastatin from the bloodstream as well as it should be, which can cause muscle problems. It's always best to talk to your doctor or pharmacist about any concerns you have about your medication."
}
```

### 1545e70746cf00d4 — summary

**Exact sentence / claim to assess:**

Your genetic result suggests that you may be at increased risk for muscle toxicity when taking simvastatin.

Sentence UTF-8 SHA-256: `4cf43f03f22ea020377fc1e07d7fa3cf71359fd3e9484a7a4e3e0ec6b643b9a7`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result suggests that you may be at increased risk for muscle toxicity when taking simvastatin.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848096+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 14213bc27358e2eb — mechanism

**Exact sentence / claim to assess:**

The OATP1B1 transporter, which helps remove simvastatin from the bloodstream into the liver, is not functioning properly in your body.

Sentence UTF-8 SHA-256: `57eb2772563fc718a3fc12e26b26aa262a4c6859f3bc59738f01cc0a85618ce7`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "The OATP1B1 transporter, which helps remove simvastatin from the bloodstream into the liver, is not functioning properly in your body.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing) membrane of liver cells.",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 22–26 (What the gene product does):

```text
*SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing)
membrane of liver cells. Its job is to move drugs out of portal blood and into
hepatocytes. It is a **transporter, not a metabolising enzyme**, which is why
its phenotypes are described as function categories (normal, decreased, poor
function) rather than metaboliser categories.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### c14d945677204db8 — mechanism

**Exact sentence / claim to assess:**

This leads to higher levels of simvastatin in the bloodstream, which can cause muscle toxicity.

Sentence UTF-8 SHA-256: `bde43f13ce38f507c765cc6c25131399646748779db25b0ad8c6f064f75eb6cd`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "This leads to higher levels of simvastatin in the bloodstream, which can cause muscle toxicity.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": true,
  "escalation_reasons": [
    "no-source"
  ],
  "escalation_detail": [
    "no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against."
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### e27e5201882d4e91 — variant_rationale

**Exact sentence / claim to assess:**

PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Poor Function result.

Sentence UTF-8 SHA-256: `c2e1a5b7d7e6a090e6122eb3d28ac468a3304d6099ba8b8144fa150a39fedf47`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "PharmCAT called SLCO1B1 as {diplotype}, which corresponds to a Poor Function result.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848097+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 22–26 (What the gene product does):

```text
*SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing)
membrane of liver cells. Its job is to move drugs out of portal blood and into
hepatocytes. It is a **transporter, not a metabolising enzyme**, which is why
its phenotypes are described as function categories (normal, decreased, poor
function) rather than metaboliser categories.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 1cbc81df47b72ae1 — variant_rationale

**Exact sentence / claim to assess:**

The non-reference positions supporting this call were no non-reference variants were detected.

Sentence UTF-8 SHA-256: `1f37f62e61f6a4951ddfcde3d69b702e2b5f7639194ac2bbcaaf8fba60ddaa45`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "The non-reference positions supporting this call were no non-reference variants were detected.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848098+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 55–59 (Notes for the explanation layer):

```text
- Describe OATP1B1 as a hepatic uptake transporter; avoid calling it a
  metabolising enzyme or describing "metaboliser status" for this gene.
- CPIC's 2022 guideline frames the outcome as statin-associated musculoskeletal
  symptoms; that is the phrasing to mirror.
- Dose ceilings and alternative statins are CPIC's to state at runtime.
```

Flags (automated/editorial triage, no adjudication):

- UNSUPPORTED_PATIENT_FACT: fixed stored assertion of no variants has no independent per-case evidence here; runtime rationale is rebuilt, but stored bytes still require review.
- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 68b5c8a2ffaeaab2 — patient_friendly

**Exact sentence / claim to assess:**

Your doctor may want to consider a different type of statin that is safer for you to take.

Sentence UTF-8 SHA-256: `2842ac61b29430efe5d216518d7d47e3b4d4c85ae2c4eb63b7721d7d3fec707b`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "Your doctor may want to consider a different type of statin that is safer for you to take.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848099+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 1460b22b2c9fa8b8 — patient_friendly

**Exact sentence / claim to assess:**

This is because your body is not able to remove simvastatin from the bloodstream as well as it should be, which can cause muscle problems.

Sentence UTF-8 SHA-256: `807d98b42ca18b4f44b541fdc30d2ffa688d343995834f2eb41e7a893cc92a51`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This is because your body is not able to remove simvastatin from the bloodstream as well as it should be, which can cause muscle problems.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848100+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 49–51 (Why altered function changes the outcome):

```text
Note the direction of the effect: the problem is not that the drug is cleared
too slowly by an enzyme, but that it is *not removed from the circulation into
the liver* fast enough.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 487f4c63cae6960a — patient_friendly

**Exact sentence / claim to assess:**

It's always best to talk to your doctor or pharmacist about any concerns you have about your medication.

Sentence UTF-8 SHA-256: `064798f08077ff5eb82323630647105e1d7122e9a09ddffd72e80040606c0a2c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "It's always best to talk to your doctor or pharmacist about any concerns you have about your medication.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848101+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- No specific lexical flag; still requires the stated review.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## simvastatin:Unknown

Gene/context: **SLCO1B1 / Unknown**; stored label `Unknown` (historical; no broad safety endorsement).
Relevant genes: SLCO1B1. SLCO1B1 is a transporter; the result must not be described as a metabolizer phenotype.

Primary source: [simvastatin source record](SOURCE-VERIFICATION.md#simvastatin); 2022; final edited form 2022-03-11; May 2022 issue, 111(5):1007–1021.
Pinned guideline: `PA166105005`, version `57`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `9b821f058ad455e3cdb623b414df1cf139fd19d4ccb0f01416b3e2ab187d550d`
- source_hash: `59c085efb1bff22380eb5a09f78cb7b81e8e50c998b569d4c3607ddb4ab76b71`
- context_hash: `4a74e0e835e9915ba833b149d97063d1e548a0489f8f9424aa472203e2bfa883`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

No recommendation recorded for Unknown; no matched source row claimed.

### Recorded recommendation (exact stored bytes as JSON string)

```json
""
```

Candidate pinned rows (matching text does not prove original selection):

- None.

### Complete entry text — review all four fields

```json
{
  "summary": "The recommendation for your genetic result and simvastatin is unknown because no usable result for this gene was established.",
  "mechanism": "SLCO1B1 encodes OATP1B1, a hepatic uptake transporter that moves drugs out of portal blood and into liver cells. Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both its site of action and its route of elimination. Efficient hepatic uptake delivers the drug to its target and keeps systemic exposure low.",
  "variant_rationale": "No genotype was called for simvastatin in this analysis, so there is no variant-level rationale to report.",
  "patient_friendly": "We don't have enough information about your genetic result to make a recommendation about taking simvastatin. This is because no usable result for this gene was established. Simvastatin works by being taken up by the liver, which helps keep systemic exposure low. If the liver doesn't take up the drug well, more of it stays in the bloodstream and can cause muscle problems. To understand your risk, you should speak with your doctor or pharmacist."
}
```

### c8a89ed79e294991 — summary

**Exact sentence / claim to assess:**

The recommendation for your genetic result and simvastatin is unknown because no usable result for this gene was established.

Sentence UTF-8 SHA-256: `e48e17be370840ed0e54f4fdf67a2b811b73ec193e401f138cf79ca9a4d60087`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "The recommendation for your genetic result and simvastatin is unknown because no usable result for this gene was established.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": true,
  "escalation_reasons": [
    "no-source"
  ],
  "escalation_detail": [
    "no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against."
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 30–32 (How the drug is handled):

```text
Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
its site of action and its route of elimination. OATP1B1 performs the uptake
step that concentrates the drug (chiefly its active acid form) into liver cells.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### c28fba73090a2466 — mechanism

**Exact sentence / claim to assess:**

SLCO1B1 encodes OATP1B1, a hepatic uptake transporter that moves drugs out of portal blood and into liver cells.

Sentence UTF-8 SHA-256: `566e382884d99b5619c5fa3bee3fe7d4fe995c0886934e3d129f5ddf5df46e52`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "SLCO1B1 encodes OATP1B1, a hepatic uptake transporter that moves drugs out of portal blood and into liver cells.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing) membrane of liver cells.",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 22–26 (What the gene product does):

```text
*SLCO1B1* encodes OATP1B1, an uptake transporter on the sinusoidal (blood-facing)
membrane of liver cells. Its job is to move drugs out of portal blood and into
hepatocytes. It is a **transporter, not a metabolising enzyme**, which is why
its phenotypes are described as function categories (normal, decreased, poor
function) rather than metaboliser categories.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### be5eaaa3ea68db45 — mechanism

**Exact sentence / claim to assess:**

Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both its site of action and its route of elimination.

Sentence UTF-8 SHA-256: `ad6253d1c74c98204f2158a7549fc37bf73847e8b44370ddf61c331d202f20e7`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both its site of action and its route of elimination.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both its site of action and its route of elimination.",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 30–32 (How the drug is handled):

```text
Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
its site of action and its route of elimination. OATP1B1 performs the uptake
step that concentrates the drug (chiefly its active acid form) into liver cells.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 609ba9acce64a324 — mechanism

**Exact sentence / claim to assess:**

Efficient hepatic uptake delivers the drug to its target and keeps systemic exposure low.

Sentence UTF-8 SHA-256: `f2f9f1a8674c564876f17f0c100e780d589333f7613031398f173108826be562`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Efficient hepatic uptake delivers the drug to its target and keeps systemic exposure low.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Efficient hepatic uptake therefore does two things at once: it delivers the drug to its target, and it keeps systemic — particularly skeletal muscle — exposure low.",
  "basis_citation": "Annotation of CPIC Guideline for simvastatin and SLCO1B1 — Cooper-DeHoff RM et al. The Clinical Pharmacogenetics Implementation Consortium Guideline for SLCO1B1, ABCG2, and CYP2C9 genotypes and Statin-Associated Musculoskeletal Symptoms. Clin Pharmacol Ther (2022). PMID: 35152405",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 34–36 (How the drug is handled):

```text
Efficient hepatic uptake therefore does two things at once: it delivers the drug
to its target, and it keeps systemic — particularly skeletal muscle — exposure
low.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 360c086ed40d7f6e — variant_rationale

**Exact sentence / claim to assess:**

No genotype was called for simvastatin in this analysis, so there is no variant-level rationale to report.

Sentence UTF-8 SHA-256: `9457271fb04fba8afef3d4db2442c8e304b1e6453f6e30def433f4e61d5bcc4c`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "No genotype was called for simvastatin in this analysis, so there is no variant-level rationale to report.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848103+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 30–32 (How the drug is handled):

```text
Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
its site of action and its route of elimination. OATP1B1 performs the uptake
step that concentrates the drug (chiefly its active acid form) into liver cells.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### a83839ed4bd79ac5 — patient_friendly

**Exact sentence / claim to assess:**

We don't have enough information about your genetic result to make a recommendation about taking simvastatin.

Sentence UTF-8 SHA-256: `a5a5f6633d66cbc95501cffc62889d239eb1f732158fcb0532565bd47c543ce4`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "We don't have enough information about your genetic result to make a recommendation about taking simvastatin.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848104+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 30–32 (How the drug is handled):

```text
Simvastatin inhibits HMG-CoA reductase inside hepatocytes, so the liver is both
its site of action and its route of elimination. OATP1B1 performs the uptake
step that concentrates the drug (chiefly its active acid form) into liver cells.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### b75ae57a7429362b — patient_friendly

**Exact sentence / claim to assess:**

This is because no usable result for this gene was established.

Sentence UTF-8 SHA-256: `34097dc5b6aa21fd2bb7e33faaf448b4b0d21f4c9d006bbb9d2ad5fc2a52b7a6`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `SUPPORT_NOT_LOCATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "This is because no usable result for this gene was established.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "",
  "basis_citation": "",
  "escalated": true,
  "escalation_reasons": [
    "no-source"
  ],
  "escalation_detail": [
    "no corpus passage aligned to this sentence. NOT a finding of fabrication — the aligner may simply have missed it — but it cannot be accepted automatically, because there is nothing to accept it against."
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

No aligned local passage located. Human must locate support or decline the claim.

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 3805e0dc02012432 — patient_friendly

**Exact sentence / claim to assess:**

Simvastatin works by being taken up by the liver, which helps keep systemic exposure low.

Sentence UTF-8 SHA-256: `b9cd53807429bdb6ce0ddf746b47ceb39523c50c1548053716e3c8d4355691df`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "Simvastatin works by being taken up by the liver, which helps keep systemic exposure low.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848106+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 34–36 (How the drug is handled):

```text
Efficient hepatic uptake therefore does two things at once: it delivers the drug
to its target, and it keeps systemic — particularly skeletal muscle — exposure
low.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 78131d9aac93415b — patient_friendly

**Exact sentence / claim to assess:**

If the liver doesn't take up the drug well, more of it stays in the bloodstream and can cause muscle problems.

Sentence UTF-8 SHA-256: `c335d02d2f6fc6d3232f85a34b7cb1424c93de217358d4dbad41e3baf711d275`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If the liver doesn't take up the drug well, more of it stays in the bloodstream and can cause muscle problems.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848107+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 40–44 (Why altered function changes the outcome):

```text
- **Reduced OATP1B1 function** means less of each dose is taken up by the liver,
  so more circulates systemically. Higher systemic exposure is associated with
  statin-associated musculoskeletal symptoms, ranging from myalgia to, rarely,
  rhabdomyolysis. The concern is **muscle toxicity**, driven by drug that failed
  to reach the liver.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### c9ba9b91c2af59bf — patient_friendly

**Exact sentence / claim to assess:**

To understand your risk, you should speak with your doctor or pharmacist.

Sentence UTF-8 SHA-256: `785750689af9eec716325017b71eaa250e5f7aadcfd168da3daadc2b7ac6f545`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "To understand your risk, you should speak with your doctor or pharmacist.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848108+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/SLCO1B1_simvastatin.md` lines 46–47 (Why altered function changes the outcome):

```text
- **Normal function** gives typical hepatic uptake, typical systemic exposure,
  and the background level of musculoskeletal risk that standard dosing assumes.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## warfarin:Unknown

Gene/context: **CYP2C9 / Unknown**; stored label `Unknown` (historical; no broad safety endorsement).
Relevant genes: CYP2C9. No validated automated warfarin-dose implementation is provided by this application; a gene call alone is not a complete dosing recommendation.

Primary source: [warfarin source record](SOURCE-VERIFICATION.md#warfarin); 2017 update; September 2017 issue, volume 102(3).
Pinned guideline: `PA166104949`, version `48`; PharmCAT 3.4.0, data 2026-07-13-11-40.

- content_hash: `5e2aec107c44fa6d87c6292ca7a0fd2951fb6aeff905002bbf19ac2b80c1ff80`
- source_hash: `9d670f0e43b50dac6f140024d15380686692773c9012727c150ca238605f7c2e`
- context_hash: `797054b6acbdf8d18c79bf35d35e72b01e8f38f1ce84b85b79a34fb176bf4ca2`

Author-read: **not recorded**. Manifest status: **unresolved**. All three current manifest hashes match recomputation.

No recommendation recorded for Unknown; no matched source row claimed.

### Recorded recommendation (exact stored bytes as JSON string)

```json
""
```

Candidate pinned rows (matching text does not prove original selection):

- None.

### Complete entry text — review all four fields

```json
{
  "summary": "Your genetic result does not provide enough information to make a recommendation for warfarin dosing.",
  "mechanism": "Warfarin is metabolized by the liver enzyme CYP2C9. Reduced function of this enzyme can lead to slower clearance of warfarin, resulting in higher exposure and a stronger anticoagulant effect.",
  "variant_rationale": "No genotype was called for warfarin in this analysis, so there is no variant-level rationale to report.",
  "patient_friendly": "We don't have enough information about your genetic result to give you specific advice about taking warfarin. Warfarin is a medication that helps prevent blood clots, but it can also cause bleeding. If you're taking warfarin, it's essential to work closely with your doctor or pharmacist to monitor your treatment and adjust your dose as needed."
}
```

### 9a20a93a47a3d00e — summary

**Exact sentence / claim to assess:**

Your genetic result does not provide enough information to make a recommendation for warfarin dosing.

Sentence UTF-8 SHA-256: `6b5acc774d3b1920833644688c6d3f2126359a84e1b45b96dab8556c5744a5d5`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "summary",
  "sentence": "Your genetic result does not provide enough information to make a recommendation for warfarin dosing.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848108+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C9_warfarin.md` lines 54–58 (A structural note for the explanation layer):

```text
**CPIC's warfarin guidance is a dosing algorithm, not a phenotype-to-text
mapping.** It combines genotype with age, weight, height and interacting drugs
to compute a starting dose. As a result, PharmCAT returns warfarin annotations
with no per-phenotype recommendation text, and PharmaGuard reports `Unknown`
rather than inventing one.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### d75177f6fd0b72e6 — mechanism

**Exact sentence / claim to assess:**

Warfarin is metabolized by the liver enzyme CYP2C9.

Sentence UTF-8 SHA-256: `4fdb69c9168cfec605d54fbdabef2c6f10d6205f4c61d5925a359a838e1e52f3`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **automated_only**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Warfarin is metabolized by the liver enzyme CYP2C9.",
  "decision": "accepted",
  "rationale": "restates an aligned corpus passage without adding a causal step, quantity, timeline, comparative or scope",
  "adjudicated_by": "automated",
  "adjudicated_at": "2026-08-05T05:49:50.403930+00:00",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "CYP2C9 is a hepatic cytochrome P450 enzyme.",
  "basis_citation": "Annotation of CPIC Guideline for warfarin and CYP2C9, CYP4F2, VKORC1 — Johnson JA et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Pharmacogenetics-Guided Warfarin Dosing: 2017 Update. Clin Pharmacol Ther (2017). PMID: 28198005",
  "escalated": false,
  "note": "AUTOMATED provenance adjudication under time constraint; not read by a person, and not clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C9_warfarin.md` lines 22–24 (What the gene product does):

```text
CYP2C9 is a hepatic cytochrome P450 enzyme. Among many substrates, it is the
principal route of clearance for S-warfarin, the more pharmacologically potent
of warfarin's two enantiomers.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 7df9bb276a0ff65d — mechanism

**Exact sentence / claim to assess:**

Reduced function of this enzyme can lead to slower clearance of warfarin, resulting in higher exposure and a stronger anticoagulant effect.

Sentence UTF-8 SHA-256: `a0c41317ae2ed92b04333f782f0d61456b8e2ae56fadf39c3484b54daf18f76a`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **unresolved**. Automated lexical check: `True`; escalation `True`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "mechanism",
  "sentence": "Reduced function of this enzyme can lead to slower clearance of warfarin, resulting in higher exposure and a stronger anticoagulant effect.",
  "adjudicated_by": "automated",
  "method": "deterministic alignment against the mechanism corpus",
  "model": null,
  "decided_at": "2026-08-05T05:49:50.403930+00:00",
  "basis": "Reduced CYP2C9 function** slows S-warfarin clearance, so the same administered amount produces higher steady-state exposure and a stronger anticoagulant effect.",
  "basis_citation": "Annotation of CPIC Guideline for warfarin and CYP2C9, CYP4F2, VKORC1 — Johnson JA et al. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Pharmacogenetics-Guided Warfarin Dosing: 2017 Update. Clin Pharmacol Ther (2017). PMID: 28198005",
  "escalated": true,
  "escalation_reasons": [
    "causal"
  ],
  "escalation_detail": [
    "adds a causal step that may not be in the source (“lead to”)"
  ],
  "note": "ESCALATED for human review; automation declined to decide"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C9_warfarin.md` lines 40–43 (Why altered function changes the outcome):

```text
- **Reduced CYP2C9 function** slows S-warfarin clearance, so the same
  administered amount produces higher steady-state exposure and a stronger
  anticoagulant effect. The clinical concern is over-anticoagulation and
  bleeding, particularly during initiation before INR monitoring has caught up.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Named human must assess final sentence and source/context, then return accepted/rejected/edited decision with rationale and actual review time; automation supplies no approval.

### 9f4bbdda9bef75a8 — variant_rationale

**Exact sentence / claim to assess:**

No genotype was called for warfarin in this analysis, so there is no variant-level rationale to report.

Sentence UTF-8 SHA-256: `98073a12d91da0b9124a39478f2a8cf7ea2e6bcbba017f5a4dbba3ddef77be06`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `PATIENT_SPECIFIC_SUPPORT_MISSING`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "variant_rationale",
  "sentence": "No genotype was called for warfarin in this analysis, so there is no variant-level rationale to report.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848109+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C9_warfarin.md` lines 54–58 (A structural note for the explanation layer):

```text
**CPIC's warfarin guidance is a dosing algorithm, not a phenotype-to-text
mapping.** It combines genotype with age, weight, height and interacting drugs
to compute a starting dose. As a result, PharmCAT returns warfarin annotations
with no per-phenotype recommendation text, and PharmaGuard reports `Unknown`
rather than inventing one.
```

Flags (automated/editorial triage, no adjudication):

- CONTEXT_REQUIRED: no actual patient call or variant evidence is supplied by this stored entry; a guideline cannot substantiate a patient-specific call. Runtime reconstruction does not waive stored review.
- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 9920b94bb5139c3b — patient_friendly

**Exact sentence / claim to assess:**

We don't have enough information about your genetic result to give you specific advice about taking warfarin.

Sentence UTF-8 SHA-256: `e61ea84634f510c5a7601ce8890d6e1067f02b4532ab3fb3a71f1002b82b8d1e`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "We don't have enough information about your genetic result to give you specific advice about taking warfarin.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848110+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C9_warfarin.md` lines 60–63 (A structural note for the explanation layer):

```text
An explanation for warfarin should therefore say plainly that a
phenotype-specific recommendation is not available from this pipeline and that
algorithmic dosing tools plus INR monitoring are how the guideline is applied.
Do not fill the gap with generalities that sound like guidance.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### dc3bc55d3753b524 — patient_friendly

**Exact sentence / claim to assess:**

Warfarin is a medication that helps prevent blood clots, but it can also cause bleeding.

Sentence UTF-8 SHA-256: `1905679c2be0b52f543bdfb145f455c4dc4842347708826563d421aaf95cff89`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "Warfarin is a medication that helps prevent blood clots, but it can also cause bleeding.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848111+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C9_warfarin.md` lines 40–43 (Why altered function changes the outcome):

```text
- **Reduced CYP2C9 function** slows S-warfarin clearance, so the same
  administered amount produces higher steady-state exposure and a stronger
  anticoagulant effect. The clinical concern is over-anticoagulation and
  bleeding, particularly during initiation before INR monitoring has caught up.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

### 51d731006d3604f7 — patient_friendly

**Exact sentence / claim to assess:**

If you're taking warfarin, it's essential to work closely with your doctor or pharmacist to monitor your treatment and adjust your dose as needed.

Sentence UTF-8 SHA-256: `68bf092067ed36763ecf4f69c3e0c1dac5eec7a0a25b06707583d381c2cf01e0`. Content/source/context hashes: the three exact hashes in this entry header (also repeated per item in inventory.json).

Existing status: **recorded_human_bulk**. Automated lexical check: `True`; escalation `False`.
Support status: `CANDIDATES_ONLY_NOT_ADJUDICATED`. Primary span: see the linked source record. Recommendation/row candidates: entry header above.

Existing record (preserved; no new decision):

```json
{
  "version": 1,
  "field": "patient_friendly",
  "sentence": "If you're taking warfarin, it's essential to work closely with your doctor or pharmacist to monitor your treatment and adjust your dose as needed.",
  "decision": "accepted",
  "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
  "adjudicated_by": "Bhuvan T",
  "adjudicated_at": "2026-07-24T10:13:25.848112+00:00",
  "note": "provenance adjudication by the project author; NOT clinical approval"
}
```

Candidate local source span (curated repository text, not primary-source proof):

`rag-corpus/mechanisms/CYP2C9_warfarin.md` lines 40–43 (Why altered function changes the outcome):

```text
- **Reduced CYP2C9 function** slows S-warfarin clearance, so the same
  administered amount produces higher steady-state exposure and a stronger
  anticoagulant effect. The clinical concern is over-anticoagulation and
  bleeding, particularly during initiation before INR monitoring has caught up.
```

Flags (automated/editorial triage, no adjudication):

- UNKNOWN_SCOPE: distinguish general biology from this individual; do not infer absent genotype, abnormal function, or a treatment recommendation solely from Unknown.
- CAPABILITY_LIMIT: explicit abstention, not a request to implement calling/dosing; clarify implementation limitation; keep entry in review set.

**Required human action:** Preserve recorded bulk decision; do not relabel as individual reading. Reassess flags during author-read; final context/source attestation cannot be inferred from historical record.

## Unmatched historical records

These are preserved and do not count toward the current 179 claims.

```json
[
  {
    "entry_id": "simvastatin:Unknown",
    "claim_key": "30677694ad44a8da",
    "record": {
      "version": 1,
      "field": "summary",
      "sentence": "The recommendation for your genetic result and simvastatin is unknown because your genetic result was not available for this gene.",
      "decision": "accepted",
      "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
      "adjudicated_by": "Bhuvan T",
      "adjudicated_at": "2026-07-24T10:13:25.848102+00:00",
      "note": "provenance adjudication by the project author; NOT clinical approval"
    },
    "disposition": "Preserve historical record; no matching current claim; do not transfer to edited text."
  },
  {
    "entry_id": "simvastatin:Unknown",
    "claim_key": "82991ae0bde1d7ce",
    "record": {
      "version": 1,
      "field": "patient_friendly",
      "sentence": "This is because your genetic result was not available for this gene.",
      "decision": "accepted",
      "rationale": "bulk: automated filter sourced every assertion in this sentence and found no polarity conflict; not individually read",
      "adjudicated_by": "Bhuvan T",
      "adjudicated_at": "2026-07-24T10:13:25.848105+00:00",
      "note": "provenance adjudication by the project author; NOT clinical approval"
    },
    "disposition": "Preserve historical record; no matching current claim; do not transfer to edited text."
  }
]
```
