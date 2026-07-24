# Provenance verifier — diagnosis

**Generated:** 2026-07-24T09:14:48.244329+00:00  
**Inputs:** the three captured `meta/llama-3.1-8b-instruct` outputs from the NVIDIA benchmark (Safe / Adjust Dosage / Toxic)  
**Sentences analysed:** 27 · **failing:** 16

## Verdict up front

**The matcher is lexical term-overlap. It measures copying, not**
**faithfulness.** The 0% score on LLM output and the 100% score on the
template are both artifacts of that: the template is assembled from
source words, so it passes by construction, and any paraphrase fails
however faithful it is.

## 1. What kind of matcher is it?

**(a) lexical / term-overlap.** Not entity-level, not claim-level. The
whole decision is a set-difference over content words:

```python
def traces_to(sentence: str, *sources: str) -> tuple[bool, set[str]]:
    """Does every content word of `sentence` appear in some source?"""
    haystack = " ".join(s or "" for s in sources).lower()
    present = set(re.findall(r"[a-z][a-z0-9\-]*|\d+(?:\.\d+)?", haystack))
    for word in list(present):
        present |= _normalise(word)
    untraced = {
        word for word in content_words(sentence) if not (_normalise(word) & present)
    }
    return (not untraced), untraced
```

There is no notion of a claim, a predicate, negation, or entailment
anywhere in it. A word is either present in the source string or it is
not.

## 2. The decisive probes

| Probe | Source | Candidate | A faithfulness metric should say | It actually says |
| --- | --- | --- | :---: | :---: |
| Faithful paraphrase — different words, same claim | `Consider dose reduction.` | `Your doctor may lower your dose.` | PASS | **FAIL** ❌ |
| Verbatim copy of the source claim | `Consider dose reduction.` | `Consider dose reduction.` | PASS | **PASS** ✅ |
| CONTRADICTION that reuses the source's vocabulary | `Consider dose reduction.` | `Do not consider dose reduction.` | FAIL | **PASS** ❌ |
| Unsourced addition using only common words | `Consider dose reduction.` | `Consider dose reduction every day.` | FAIL | **FAIL** ✅ |

**Read the third row.** A sentence that says the *opposite* of the source
passes, because it reuses the source's vocabulary. And the fourth adds an
unsourced frequency ("every day") using only words already present, and
also passes. So the checker has false positives *and* false negatives:
it rejects faithful rewording and accepts contradictions.

That is the answer to the critical question: **a faithful restatement in
different words FAILS.** The metric measures copying.

## 3. The 15 real failures, classified by hand

| Verdict | Count |
| --- | ---: |
| BORDERLINE | 1 |
| FALSE POSITIVE | 15 |

### Why they failed

| Cause | Count |
| --- | ---: |
| phenotype descriptor | 4 |
| plain-language rendering | 4 |
| connective word | 3 |
| wording drift | 1 |
| drug's own name | 1 |
| mechanism paraphrase | 1 |
| procedural framing | 1 |
| procedural framing + paraphrase | 1 |

**Not one failure is a fabricated clinical claim.** The categories are:

- **connective words** — `leading`, `allowing`, `due`. A correct causal
  sentence fails on its conjunction.
- **phenotype descriptors** — `intermediate`, `metabolizer`, `phenotype`.
  The sentence fails for naming the phenotype it was handed as input,
  because those words are not in the CPIC *recommendation* string.
- **the drug's own name** — one sentence's only untraced word is
  `fluorouracil`.
- **plain-language rendering** — `doctor`, `body`, `lower`, `side effects`,
  `low white blood cell count`. Translating `leukopenia` into words a
  patient understands is the entire purpose of `patient_friendly`, and the
  metric penalises exactly that.
- **procedural framing** — "your doctor or pharmacist can help you"
  asserts nothing clinical and should never have been scored.

### Every failing sentence

#### `azathioprine:IM` (Safe)

> **CPIC source:** Initiate therapy with reduced starting doses (30-80% of standard starting dose) if standard starting dose is ≥2 mg/kg/day. If starting dose is already below standard starting dose, dose reduction might not be necessary. During therapy, adjust the doses of azathioprine based on the degree of myelosuppression and disease-specific guidelines. It usually takes at least 2-4 weeks of stable dosing to re

🟢 **FALSE POSITIVE** (connective word) — *mechanism*, classified `MECHANISM`

> Reduced or absent function in these enzymes removes a brake, leading to bone-marrow suppression.

- untraced tokens: `leading`
- adjudication: Only 'leading' is untraced. The causal claim (reduced function -> marrow suppression) is in the mechanism corpus; the sentence fails on a conjunction.

🟢 **FALSE POSITIVE** (phenotype descriptor) — *variant_rationale*, classified `MECHANISM`

> The patient has an intermediate metabolizer phenotype, which means they have moderate to high erythrocyte concentrations of TGN metabolites and low concentrations of MeMPNs compared to normal metabolizers.

- untraced tokens: `intermediate`, `metabolizer`, `metabolizers`, `phenotype`
- adjudication: Untraced words are 'intermediate/metabolizer/phenotype' — the case's own input phenotype. The biochemical detail (TGN, MeMPN concentrations) DID trace. It fails for naming the phenotype it was given.

🟢 **FALSE POSITIVE** (plain-language rendering) — *patient_friendly*, classified `CLINICAL`

> If you're taking {drug} and your doctor is considering a standard dose of ≥2 mg/kg/day, you may need a lower dose.

- untraced tokens: `considering`, `doctor`, `lower`, `need`
- adjudication: A faithful restatement of 'Initiate therapy with reduced starting doses if standard starting dose is >=2 mg/kg/day'. The dose threshold traced; 'doctor/lower/need' are the plain words a patient needs.

🟢 **FALSE POSITIVE** (plain-language rendering) — *patient_friendly*, classified `CLINICAL`

> Your doctor will adjust the dose based on how your body is responding to the medicine and your disease-specific guidelines.

- untraced tokens: `body`, `doctor`, `medicine`, `responding`
- adjudication: 'adjust', 'dose', 'disease-specific', 'guidelines' all traced — the claim is sourced. Fails on 'body/doctor/medicine/responding'.

🟡 **BORDERLINE** (wording drift) — *patient_friendly*, classified `CLINICAL`

> It may take a few weeks to reach the right dose.

- untraced tokens: `right`
- adjudication: 'weeks' traced: CPIC states a steady-state interval after dose adjustment, so the timeline is sourced, not invented. But 'reach the right dose' is not the same claim as 'reach steady state' — a mild drift worth a human look, not an invention.

#### `fluorouracil:IM` (Adjust Dosage)

> **CPIC source:** Reduce starting dose by 50% followed by titration of dose based on toxicity or therapeutic drug monitoring (if available). Patients with the c.2846A&gt;T/c.2846A&gt;T genotype may require &gt;50% reduction in starting dose.

🟢 **FALSE POSITIVE** (phenotype descriptor) — *summary*, classified `MECHANISM`

> The patient has an intermediate metabolizer phenotype for the DPYD gene, which is associated with a decreased activity of the dihydropyrimidine dehydrogenase enzyme.

- untraced tokens: `associated`, `intermediate`, `metabolizer`, `phenotype`
- adjudication: Untraced: 'associated/intermediate/metabolizer/phenotype'. Restates the supplied phenotype and its known enzyme effect.

🟢 **FALSE POSITIVE** (drug's own name) — *summary*, classified `CLINICAL`

> This may increase the risk of severe or fatal toxicity when treated with fluorouracil.

- untraced tokens: `fluorouracil`
- adjudication: The ONLY untraced word is 'fluorouracil' — the name of the drug the explanation is about. 'severe or fatal toxicity' traced verbatim.

🟢 **FALSE POSITIVE** (mechanism paraphrase) — *mechanism*, classified `CLINICAL`

> Reduced DPD activity slows inactivation, leading to higher exposure to active drug and increased risk of toxicity.

- untraced tokens: `active`, `exposure`, `higher`, `inactivation`, `leading`, `slows`
- adjudication: Standard DPD mechanism, reworded. The corpus states the same causal chain in different words.

🟢 **FALSE POSITIVE** (phenotype descriptor) — *variant_rationale*, classified `CLINICAL`

> The patient's intermediate metabolizer phenotype is associated with decreased DPD activity, which may increase the risk of severe or fatal toxicity when treated with fluorouracil.

- untraced tokens: `associated`, `fluorouracil`, `intermediate`, `metabolizer`, `phenotype`
- adjudication: Same descriptors plus the drug name; the toxicity claim traced.

🟢 **FALSE POSITIVE** (plain-language rendering) — *patient_friendly*, classified `CLINICAL`

> This means you may be at higher risk for serious side effects.

- untraced tokens: `effects`, `higher`, `serious`, `side`
- adjudication: 'serious side effects' is the lay rendering of 'severe toxicity', which is in the source. Fails only because laypeople and guidelines use different vocabulary.

🟢 **FALSE POSITIVE** (procedural framing) — *patient_friendly*, classified `CLINICAL`

> Your doctor or pharmacist can help you understand what this means for your treatment and how to stay safe.

- untraced tokens: `doctor`, `help`, `pharmacist`, `safe`, `stay`, `treatment`, `understand`
- adjudication: Makes NO clinical claim at all. Advisory framing, misclassified as CLINICAL because it contains the word 'treatment'.

#### `azathioprine:PM` (Toxic)

> **CPIC source:** Consider alternative nonthiopurine immunosuppressant therapy.

🟢 **FALSE POSITIVE** (phenotype descriptor) — *summary*, classified `CLINICAL`

> The patient has a Poor Metabolizer phenotype for azathioprine, which means they have a greatly increased risk of thiopurine-related leukopenia, neutropenia, and myelosuppression.

- untraced tokens: `azathioprine`, `metabolizer`, `patient`, `phenotype`, `poor`
- adjudication: Untraced: phenotype descriptors and the drug name. The substantive claim (leukopenia, neutropenia, myelosuppression) traced verbatim.

🟢 **FALSE POSITIVE** (connective word) — *mechanism*, classified `MECHANISM`

> Reduced or absent TPMT function removes this brake, allowing more TGN to accumulate in haematopoietic cells, leading to bone-marrow suppression.

- untraced tokens: `allowing`, `leading`
- adjudication: Fails on 'allowing' and 'leading'. Two conjunctions.

🟢 **FALSE POSITIVE** (connective word) — *variant_rationale*, classified `MECHANISM`

> The patient's {phenotype} phenotype for azathioprine is due to {diplotype} of the TPMT gene.

- untraced tokens: `due`, `phenotype`
- adjudication: Fails on 'due' and 'phenotype'. The sentence is almost entirely slots.

🟢 **FALSE POSITIVE** (plain-language rendering) — *patient_friendly*, classified `CLINICAL`

> This means you're at higher risk for serious side effects like low white blood cell count.

- untraced tokens: `blood`, `cell`, `count`, `effects`, `higher`, `like`, `low`, `serious`, `side`, `white`
- adjudication: 'low white blood cell count' is the lay rendering of 'leukopenia', which IS in the source. Translating a term of art is the point of the field.

🟢 **FALSE POSITIVE** (procedural framing + paraphrase) — *patient_friendly*, classified `CLINICAL`

> Your doctor or pharmacist can help you choose a different medicine that's safer for you.

- untraced tokens: `choose`, `different`, `doctor`, `help`, `medicine`, `pharmacist`, `safer`
- adjudication: Restates 'Consider alternative nonthiopurine immunosuppressant therapy' in plain words, plus advisory framing.

## 4. What follows

The earlier conclusion — *"real LLMs fail the integrity bar"* — does not
hold. It was a measurement artifact. What the data actually shows is that
`llama-3.1-8b` produced clinically faithful text whose wording differs
from the source, which is what a plain-language explainer is supposed to
do.

It does **not** follow that the output is safe to ship unexamined. The
contradiction probe shows lexical overlap cannot certify anything, in
either direction. So the replacement is two-part:

1. **Field-level policy** — verbatim where verbatim matters (the CPIC
   recommendation), claim-level checks where wording may legitimately
   vary, and paraphrase explicitly permitted in `patient_friendly` under
   a no-new-claims rule.
2. **Human adjudication** — the automated layer flags candidates; a person
   decides. With 20 entries that is tractable, and it is the payoff of
   pre-generating rather than generating per request.

