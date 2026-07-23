# RAG corpus — mechanism background

Six short documents, one per gene-drug pair, holding the **biological and
pharmacological background** the explanation layer needs.

```
mechanisms/
├── CYP2C19_clopidogrel.md
├── CYP2C9_warfarin.md
├── CYP2D6_codeine.md
├── DPYD_fluorouracil.md
├── SLCO1B1_simvastatin.md
└── TPMT_azathioprine.md
```

---

## The provenance rule

> **Mechanism lives here. Dosing lives in PharmCAT's CPIC output. Never both.**

This is the single most important constraint in Phase 3, and it is enforced, not
just asserted:

| Kind of content | Comes from | Reaches the user via |
| --- | --- | --- |
| What the gene product does, how the drug is handled, why altered function matters | **this corpus** | `mechanism`, `variant_rationale` |
| What to actually do — dose changes, alternatives, monitoring, numbers | **PharmCAT's CPIC annotation, at runtime** | `clinical_recommendation` |

Two sources stating a dose is how a system ends up contradicting itself, and a
contradiction in a clinical number is the failure mode with the worst
consequences. So these files contain **no doses, no percentages, no mg values,
no monitoring intervals** — only mechanism.

Enforcement:

- Every file declares `contains_dosing: false` in its front matter.
- `backend/tests/test_corpus.py` scans all files for dose-like patterns (`mg`,
  `mcg`, `%`, `mg/kg`, "reduce by") and **fails the build** if any appear.
- The faithfulness guard (`backend/app/explanation/guard.py`) independently
  rejects any generated number that is not present in the supplied context, so
  a number smuggled in here still could not become a recommendation.

## Front matter

Every file carries a machine-readable block:

```yaml
---
gene: CYP2C19
drug: clopidogrel
aliases: [Plavix]
source_guideline: "Annotation of CPIC Guideline for clopidogrel and CYP2C19"
source_url: https://www.clinpgx.org/guidelineAnnotation/PA166104948
primary_citation: >-
  Lee CR et al. ... Clin Pharmacol Ther (2022). PMID: 35034351
retrieved: 2026-07-22
retrieved_via: "PharmCAT 3.4.0 report.json (CPIC Guideline Annotation citations)"
contains_dosing: false
reviewed_by: null
---
```

`aliases` feeds the retrieval fallback, so `5-FU` resolves to `fluorouracil`.

### Where the citations came from

They were **extracted from PharmCAT's own report**, not written from memory:
PharmCAT's CPIC annotation for each drug carries the guideline name, its
ClinPGx URL, and the citation list with PMIDs. The most recent guideline
citation per drug is quoted. Regenerate with:

```bash
pharmcat_pipeline test-data/normal_metabolizer_control.vcf -o out/ -reporterJson
python -c "import json;r=json.load(open('out/*.report.json'));\
print(r['drugs']['CPIC Guideline Annotation']['clopidogrel']['citations'])"
```

## How this is retrieved

`backend/app/retrieval.py` does an **exact `(gene, drug)` dictionary lookup** —
no embeddings, no vector store, no similarity search. With six documents, exact
lookup is more reliable, instant, free, and fully auditable. See that module's
docstring for the reasoning.

## Status: requires faculty review

> ⚠️ **This content has not been reviewed by the faculty guide.** Every file
> carries `reviewed_by: null` until it has been.

The mechanism descriptions were written against the CPIC guidelines cited in
each file, but they are a student's summary of that source material, not an
authoritative restatement of it. They feed patient-facing prose, so an error
here propagates into text a reader may take at face value.

Review should check that: the direction of effect is right (does reduced
function mean *more* drug effect or *less*?), the gene's role is correctly
described as activation vs clearance vs transport, and no dosing language has
crept in. Set `reviewed_by` when done.

### The direction-of-effect trap

The six pairs do not behave the same way, and getting this backwards produces
confident, fluent, wrong text:

| Pair | Gene's role | Reduced function means |
| --- | --- | --- |
| CYP2C19 / clopidogrel | **activates** a prodrug | *less* effect — therapeutic failure |
| CYP2D6 / codeine | **activates** a prodrug | *less* analgesia; *increased* function is the toxic direction |
| DPYD / fluorouracil | **clears** the drug | *more* exposure — toxicity |
| TPMT / azathioprine | **brakes** active metabolite formation | *more* active metabolite — myelosuppression |
| CYP2C9 / warfarin | **clears** the drug | *more* effect — bleeding risk |
| SLCO1B1 / simvastatin | **transports** drug into the liver | *more* systemic exposure — muscle symptoms |

## Two pairs that are deliberately negative

- **CYP2D6 / codeine** — PharmCAT cannot call CYP2D6 from a VCF at all. The file
  says so and instructs the explanation layer to state that no result was
  obtained rather than imply a phenotype.
- **CYP2C9 / warfarin** — CPIC's warfarin guidance is a dosing *algorithm*, so
  PharmCAT returns no per-phenotype recommendation text. The file says so.

Both are honest gaps, and the corpus documents them so the explanation layer
describes the gap instead of papering over it.

## Adding a pair

1. Create `mechanisms/<GENE>_<drug>.md` with complete front matter.
2. Mechanism only — no dosing. `test_corpus.py` will hold you to it.
3. Add the drug to `backend/app/data/label_mapping.yaml` → `drug_primary_gene`.
4. Re-run `scripts/pregenerate_explanations.py` and get the output reviewed.
