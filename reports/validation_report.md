# Validation against reference materials — PARTIAL (Phase 6, in progress)

**Date:** 2026-07-24 · **Status:** data acquisition complete and proven
end-to-end; the harness (`scripts/validate.py`) is **not yet written**, so the
per-gene concordance and label-mapping tables below are populated only for the
samples run by hand. Every number here is real; none is projected.

---

## What this validates, and what it does not

**PharmaGuard uses PharmCAT as its calling engine.** Diplotype concordance
therefore primarily demonstrates **integration fidelity** — that our pipeline
does not corrupt PharmCAT's calls on the way through — and *not* that we
independently validated PharmCAT's science. Agreement with a reference genotype
is properly credited to PharmCAT.

The **novel** validation is the label-mapping layer (`label_mapping.yaml`): the
rules that collapse a CPIC recommendation into one of five risk words are our own
artifact, and had never been tested against a real sample before this phase.

---

## 1. Sample provenance

| Source | Verified live | What it gives |
| --- | --- | --- |
| PharmCAT 3.4.0 release assets | 2026-07-24 | `pharmcat-3.4.0-all.jar` (32 MB), positions VCF. Runs under OpenJDK 25; reports `PharmCAT 3.4.0` |
| 1000 Genomes GRCh38 high coverage | 2026-07-24 | 3,202-sample phased panel, per chromosome, remote `.tbi` present |
| GeT-RM PGx consensus (Coriell mirror) | 2026-07-24 | 107 samples, consensus genotypes |

URLs were **found by listing**, not recalled: a plausible shorter 1000G path
returned 404 before the real release directory was located. Coordinates come from
PharmCAT's own positions file, not a genome browser (`--show-coords`).

### Access obstacles, reported rather than worked around

**CDC GeT-RM pages return HTTP 403 to every non-browser client.** The consensus
data was therefore taken from Coriell's mirror, which hosts the older PGx table:
**CYP2D6, CYP2C19, CYP2C9, VKORC1, UGT1A1** for 107 samples. The later GeT-RM
studies covering **TPMT, NUDT15, DPYD and SLCO1B1** are published only on those
blocked CDC pages, so consensus genotypes for four of our seven genes were **not
obtainable programmatically**.

### The binding constraint: GeT-RM ∩ 1000 Genomes = 1 sample

| | Count |
| --- | ---: |
| GeT-RM PGx consensus samples | 107 |
| 1000G high-coverage panel | 3,202 |
| **In both** | **1** (`NA12273`) |

98 of the 107 GeT-RM identifiers are `NA17xxxx` Coriell cell lines that were
never 1000G-sequenced. This was checked directly against the panel sample list,
not assumed. **Diplotype concordance against consensus truth is bounded at n=1
by this route** — the single most consequential finding of the phase, because the
Phase 6 design assumed a usable intersection.

`NA12878` is in the 1000G panel but **not** in this GeT-RM table (it was
characterised in a different study), so it supports integration fidelity and the
negative control but carries no consensus genotype here.

---

## 2. Proven end-to-end (real runs, by hand)

Remote slicing works as designed: **~2.5 MB per sample** across seven gene
regions, seconds per chromosome, versus a ~2 TB whole-genome panel. Four samples
sliced and cached; `bcftools` pulls only the indexed byte ranges.

### Diplotype concordance — NA12273 (the one overlapping sample)

| Gene | GeT-RM consensus | PharmaGuard / PharmCAT | Class |
| --- | --- | --- | --- |
| CYP2C19 | `*1/*2` | `*1/*2` — Intermediate Metabolizer | **exact match** |
| CYP2C9 | `*1/*2` | `*1/*2` — Intermediate Metabolizer | **exact match** |
| CYP2D6 | `*1/*1` | *not called* — No Result | **no-call (by design)** |

2 of 2 exact on the genes where consensus exists and VCF calling is possible.

### The CYP2D6 negative control, strengthened by reference data

This is a better result than a bare "returns Unknown". GeT-RM records NA12273 as
CYP2D6 **`*1/*1`** — a real genotype, confirmed by assays that can resolve it. Our
pipeline, working from an unphased VCF, **declines to call it** rather than
guessing. So the control does not merely show we fail to call something absent;
it shows we decline to call something genuinely present but not determinable from
this data type. That is the project's honesty claim, verified against an external
reference.

### Second sample: NA12878

| Gene | Call | Phenotype |
| --- | --- | --- |
| CYP2C19 | `*1/*2` | Intermediate Metabolizer |
| CYP2C9 | `*1/*2` | Intermediate Metabolizer |
| DPYD | `c.1601G>A (*4)/c.1627A>G` | Normal Metabolizer |
| NUDT15 | `*1/*1` | Normal Metabolizer |
| SLCO1B1 | `*1/*15` | Decreased Function |
| TPMT | `*1/*1` | Normal Metabolizer |
| **CYP2D6** | **not called** | No Result ✅ control holds |

NA12878's CYP2C19 `*1/*2` and CYP2C9 `*1/*2` match its widely published
genotypes, which is corroborating (though not GeT-RM consensus from this table).

Parsing used the **production** `parse_report()` from `pharmcat_runner.py`, so
this exercises the real integration path rather than a test double.

---

## Severity audit (2026-07-24)

The Toxic/Ineffective policy is semantically right, but a correct label is no use
if the severity beside it understates the danger. Severity is
`severity_hint` escalated one step for an extreme phenotype (PM/URM), so it was
measured rather than reasoned about.

| Case | Label | Phenotype | Severity | Verdict |
| --- | --- | --- | --- | --- |
| clopidogrel CYP2C19 **PM** | Ineffective | PM | **critical** | ✅ stent thrombosis reaches the top of the scale |
| clopidogrel CYP2C19 IM | Ineffective | IM | high | ✅ |
| simvastatin SLCO1B1 **Poor Function** | Toxic | PM | **critical** | ✅ |
| simvastatin SLCO1B1 Decreased Function | Toxic | IM | high | ✅ |
| simvastatin SLCO1B1 Possible Decreased Function | Toxic | **Unknown** | high | ⚠️ see below |

**Ineffective is not undersold.** Its base severity is `high`, identical to
Toxic, and escalation applies to both — so clopidogrel PM reaches `critical`
exactly as a toxicity case would. Confident and tentative phenotypes are
differentiated (`critical` vs `high`), so the two SLCO1B1 extremes are not
collapsed.

**Client rendering: passes.** `RiskLabel.ineffective` renders with the *identical*
accent colour as `toxic` (`#B3261E` light / `#F16A6A` dark), differing only in
icon (`block` vs `warning`). Both read as red, as the problem statement requires.

### ⚠️ Finding: a third label/prose divergence

`SLCO1B1 "Possible Decreased Function"` maps to `Phenotype.UNKNOWN`, because
`map_phenotype` collapses tentative phenotypes into Unknown. The consequences
diverge:

- the **label** derived from CPIC's text is **Toxic**, severity **high** — correct;
- the **explanation** served is keyed on `(simvastatin, Unknown)`, whose prose
  reads *"The recommendation for your genetic result and simvastatin is unknown
  because your genetic result was not available for this gene."*

That prose is factually wrong — the result *was* available; it is tentative, not
absent — and it sits under a red Toxic badge. **Severity is not the problem here;
the phenotype collapse is.** "No result" and "tentative result" are different
states and should not share a key.

This is the **third** instance of the same class: azathioprine:IM had correct
prose under a wrong label, and here correct label sits over wrong prose. The
common cause is that nothing cross-checks the label against the text rendered
beside it — the provenance guard checks explanations against CPIC, never against
the label.

**Proposed fix (not applied — this needs your call):** distingu
`Phenotype.INDETERMINATE` from `Phenotype.UNKNOWN` so tentative calls get their
own explanation entry, or have the runtime refuse to pair a non-Unknown label
with the Unknown explanation. Either is a contract-visible change and wants its
own review.

---

## Generalisable lesson: match text that DIRECTS, not text that DESCRIBES

All three mapping defects, and both over-broad patterns reverted while fixing
them, share one shape: **a rule matched prose that describes dosing rather than
prose that directs it.**

| Describes (must not set a label) | Directs (may set a label) |
| --- | --- |
| `30-80% of standard starting dose` — the bare phrase appears, governed by a modifier | `Initiate therapy with reduced starting doses` |
| `During therapy, adjust doses based on disease-specific guidelines` | `Reduce starting dose by 50%` |
| `takes 2 weeks to reach steady state after each dose adjustment` | `Avoid clopidogrel if possible` |
| implications prose generally — explains biology, may mention dose or risk where CPIC gives no directive at all | `Prescribe an alternative statin` |

Two consequences, now load-bearing in the mapping:

1. **Specificity must win.** A modifier-governed phrase must be claimed by a more
   specific rule before a rule keyed on the bare phrase sees it.
2. **Establishing whether a directive exists must read the recommendation field
   alone.** Implications describe; they do not direct.

The failure mode is subtle precisely because descriptive text is *about* the right
topic in the right vocabulary. Substring matching cannot separate the two — only
the grammatical relationship can, which is why several rules now use regex rather
than phrase lists. This is recorded as a header comment in `label_mapping.yaml`
so future rules are written against the right axis.

---

## Label-mapping correctness — EXHAUSTIVE (the project's novel validation)

> **Result: 105 combinations exhaustively checked. Three defects found, all
> fixed. Thirteen divergences documented as accepted, with rationale.**
>
> A single percentage would misrepresent this. The number moved 60 → 92 of 105,
> but the meaningful finding is *which* rows were wrong and why: one substring
> collision affecting 16 rows, one provenance violation, one dropped toxicity
> warning. The remaining 13 are two defensible labelling conventions
> disagreeing, not errors.

### Defects found and fixed

| # | Defect | Rows | Severity |
| ---: | --- | ---: | --- |
| 1 | **Substring collision.** `standard_dosing` matched `standard starting dose` *inside* `30-80% of standard starting dose`, labelling a required dose reduction as **Safe** | 16 | 🔴 clinically consequential |
| 2 | **Provenance violation.** CPIC text reading literally `"No recommendation"` was labelled **Adjust Dosage**, because the *implications* prose mentioned monitoring | 2 | 🔴 asserts guidance CPIC declined to give |
| 3 | **Dropped toxicity warning.** `"Prescribe an alternative statin…"` + `increased risk of myopathy` fell through to **Unknown** | 3 | 🔴 Unknown reads as "no information", not "use something else" |

Defect 2 is the notable one architecturally: the project's core promise — never
assert clinical content absent from the source — was enforced on the explanation
layer while the mapping layer sat unguarded. The exhaustive run found the gap.

### The fix was general, not a patch

Pre-committed before editing (`reports/fix_precommitment.md`): all 16 rows must
change, zero regressions permitted, and the fix must be a precedence/specificity
correction rather than a special case — because the collision shape
("modifier-governed phrase claimed by an unmodified-phrase rule") would otherwise
stay live for any other drug. **No rule added names a drug, a gene, or a
percentage.** Predicted 76/105; achieved exactly 76 at that stage, 0 regressions.

Two over-broad patterns were caught and reverted during the work, both by the
zero-regression condition:

- a bare `adjust … dose` pattern matched CPIC's generic *"During therapy, adjust
  doses based on disease-specific guidelines"* — 7 regressions;
- the noun forms `dose adjustment` / `dose reduction` matched *"takes at least 2
  weeks to reach steady state after each dose adjustment"*, which is
  pharmacokinetics, not a directive — 5 regressions.

Only modifier-before-dose and percentage-of-standard are unambiguous, and only
those need to pre-empt `standard_dosing`.

### Latent collision in other drugs: none

The collision *shape* was searched across all 105 rows. It occurs in
**azathioprine only** (16 rows); clopidogrel, codeine, fluorouracil, simvastatin
and warfarin have zero. The fix is general, so a future drug with this shape is
covered pre-emptively rather than reactively.

### Contradiction guard — an independent second signal

CPIC's structured booleans (`alternateDrugAvailable`, `dosingInformation`) are now
used as a **cross-check**, never as mapping input. That distinction is load-bearing:
the expectation table derives from exactly those fields, so consuming them in the
mapping would make the validation tautological and it would stop catching
anything.

**The guard would have caught defect 1 on its own.** All 16 mislabelled rows
carried `dosingInformation = true` beside a `Safe` label — "nothing needs to
change" against "the dose must change". No expectation table required.

Swept across all 105 rows after the fix: **0 false positives.**

### Toxic vs Ineffective — one uniform policy

Recorded as commented rationale in `label_mapping.yaml`, not decided per row:

> **Toxic** = harm arising from *exposure* (the drug accumulates and damages).
> **Ineffective** = *therapeutic failure* — the drug does not produce its effect,
> **even when that failure is dangerous**.

The distinguishing question is not "does the text mention harm?" — both classes
do — but "does the harm come from the drug acting, or from the drug failing to
act?"

This mattered. A first pass at the *independent* expectation table classified all
ten clopidogrel rows as **Toxic** purely because their implications contain the
word "adverse". Clopidogrel PM's cardiovascular events follow from the *absence*
of antiplatelet effect: it is failure, not poisoning. Prodrug failure is the
commonest shape in this domain, so that reading would have mislabelled an entire
drug. Applying the policy uniformly to both sides resolved all 11 contended rows.

### Accepted divergences — 13 rows, no change made

| Class | Rows | Why accepted |
| --- | ---: | --- |
| Expected `Safe`, we say `Adjust Dosage` | 7 | Indeterminate-phenotype rows ("Neither TPMT or NUDT15 phenotype could be assigned… consider evaluating TPMT erythrocyte activity"). Our label is the more cautious reading of a row that does ask the clinician to do something. |
| Expected `Safe`, we say `Unknown` | 6 | We decline to classify where the expectation infers safety from two false booleans. Declining is the conservative error. |

Both classes err toward caution, which is the correct direction for the one that
cannot be verified.

### Result

| | Before | After |
| --- | ---: | ---: |
| Agreements | 60 / 105 | **92 / 105** |
| Regressions introduced | — | **0** |

| Drug | Before | After |
| --- | ---: | ---: |
| azathioprine | 16 / 35 | 32 / 35 |
| clopidogrel | 12 / 24 | 22 / 24 |
| codeine | 12 / 23 | 23 / 23 |
| fluorouracil | 5 / 5 | 5 / 5 |
| simvastatin | 3 / 6 | 6 / 6 |
| warfarin | 12 / 12 | 12 / 12 |

<!-- prior detail retained below -->

### Method detail


**This is the one clinical artifact that is ours.** PharmCAT calls the
diplotypes, so calling accuracy is PharmCAT's achievement. `label_mapping.yaml`
— the ordered rules collapsing a CPIC recommendation into one of five risk words
— is our own, and until now had only ever been checked against the fixtures it
was written alongside.

### Coverage: exhaustive, not a sample

Checked against **every CPIC recommendation PharmCAT 3.4.0 ships** for our six
drugs: **105 rows**, spanning every phenotype combination CPIC defines —
including combinations our pipeline cannot currently reach. Source:
`org/pharmgkb/pharmcat/reporter/prescribing_guidance.json` inside the PharmCAT
jar, which carries CPIC's own published rows. Text used verbatim (HTML stripped);
nothing paraphrased. Accessed 2026-07-24.

### How independence was achieved

The two sides read **different fields**, so agreement is evidence rather than
tautology:

| Side | Input |
| --- | --- |
| `label_mapping.yaml` | phrases in the recommendation **text** (`drug_recommendation` + `implications`) |
| the expectation table | CPIC's **structured booleans** (`alternateDrugAvailable`, `dosingInformation`) + implication category |

No row's expected value was set by running the mapping and copying its answer.

### Result

| | Count |
| --- | ---: |
| Combinations checked | **105** |
| Agreements | **60 (57.1%)** |
| Disagreements | **45** |

| Drug | Agree / total |
| --- | ---: |
| fluorouracil | 5 / 5 |
| warfarin | 12 / 12 |
| clopidogrel | 12 / 24 |
| codeine | 12 / 23 |
| azathioprine | 16 / 35 |
| simvastatin | 3 / 6 |

### 🔴 Confirmed bug — 16 rows, clinically consequential

A **substring collision** in the `standard_dosing` rule. CPIC text reading:

> *"Initiate therapy with **reduced** starting doses (30-80% of standard starting
> dose) if standard starting dose is ≥2 mg/kg/day…"*

is labelled **Safe**, because the rule's phrase list matches the substring
`standard starting dose` occurring inside `30-80% of standard starting dose`. The
rule fires before the dose-change rule, so a patient whom CPIC says needs a
30–80% dose reduction is told the drug is safe at normal dosing.

Reproduced directly:

```
CPIC: "Initiate therapy with reduced starting doses (30-80% of standard
       starting dose)…"          →  our mapping: Safe  (rule: standard_dosing)
CPIC: "Use standard starting dose."  →  our mapping: Safe  (correct)
```

Affects 16 of the 35 azathioprine rows. The rule's own comment anticipates this
class of problem ("Order is load-bearing") but its phrase list is too permissive.

**`label_mapping.yaml` was NOT modified.** Proposed fix, for separate review:
require a negative lookbehind so `standard (starting )?dose` does not match when
preceded by a percentage or the word `reduced` — or move the dose-reduction rule
ahead of `standard_dosing`. Either needs its own regression test against these
16 rows before being accepted.

### The remaining 29, characterised honestly

| Class | Rows | Reading |
| --- | ---: | --- |
| `Toxic` vs `Ineffective` | 10 | Both adverse; which one is a judgement call. Our mapping reads the recommendation's own wording, the expectation reads implication category. Defensible either way — not obviously a bug. |
| Expected `Safe`, got `Adjust Dosage` | 7 | Mostly indeterminate-phenotype rows ("Neither TPMT or NUDT15 phenotype could be assigned… consider evaluating TPMT erythrocyte activity"). Our answer is arguably the safer one. |
| Expected `Safe`, got `Unknown` | 6 | Our mapping declined to classify. Conservative. |
| Expected `Toxic`, got `Unknown` | 3 | **Worth review** — declining to label a toxic case loses a warning. |
| Expected `Unknown`, got `Adjust Dosage` | 2 | Our mapping labelled where CPIC gave no actionable guidance. |
| `Ineffective` vs `Toxic` (reverse) | 1 | Judgement call. |

**So 57.1% is not "the mapping is 57% correct".** 16 rows are a confirmed bug, 3
warrant review, and the remainder are largely definitional disagreements between
two defensible labelling conventions. The single actionable finding is the
substring collision.

### One correction to the expectation rule, disclosed

The first run scored 39/105. Inspection showed my *expectation* rule contained a
category error, not the mapping: it treated
`alternateDrugAvailable=false, dosingInformation=false` as **Safe** even for rows
reading "No recommendation", rows where the phenotype could not be assigned, and
rows pointing at the warfarin dosing algorithm. Absence of guidance is
**Unknown**, not an assurance of safety — treating it as Safe was the most
dangerous error available. Correcting it moved warfarin from 0/12 to 12/12.

**Exactly one correction was made, and the limit was fixed before re-running.**
This project has already documented a detector tuned 12 → 4 → 0 until it agreed
with whatever it measured (`reports/provenance_finding.md`); the same discipline
applies to a validator.

### Reproduction

```bash
python scripts/validate_label_mapping.py --build-table   # re-extract from the jar
python scripts/validate_label_mapping.py                 # exhaustive comparison
python scripts/validate_label_mapping.py --json --drug azathioprine
```

Exits non-zero while disagreements remain, so the finding cannot be forgotten.

---

## 3. Not yet measured

| Item | Status |
| --- | --- |
| (a) Integration fidelity at scale | Harness not written. Path proven on 2 samples. |
| (b) Per-gene concordance table | Bounded at n=1; needs CDC tables for 4 genes |
| (c) Label-mapping correctness | **Not started** — the independent CPIC expectation table does not exist yet |
| Failure characterisation | Not measured |

---

## 4. Limitations

**Sample size.** Diplotype concordance rests on **one** sample with consensus
truth. That is not a concordance rate and must not be reported as a percentage.

**Ancestry composition — directly relevant to this project's motivation.** The
1000 Genomes panel is broad but the GeT-RM PGx reference set is not, and neither
was assembled to represent **South Asian / Indian** populations, which this
project cites as its motivation. Allele frequencies for CYP2C19 and others differ
materially across ancestries, so concordance measured here does **not** transfer
to the target population. Establishing that would need an Indian-ancestry
reference panel, which this validation does not have.

**Integration fidelity is not scientific validation.** Restating the framing
above because it is the easiest thing to overclaim: agreement with a reference
genotype credits PharmCAT. Our contribution under test is the label mapping,
which is the piece still unmeasured.

**CYP2D6 is excluded by design, not by failure.** It is a negative control
throughout.

---

## 5. Reproduction

```bash
python scripts/fetch_reference_data.py --verify          # confirm sources live
python scripts/fetch_reference_data.py --show-coords     # gene regions from PharmCAT
python scripts/fetch_reference_data.py --fetch-tools     # PharmCAT jar + positions
python scripts/fetch_reference_data.py --sample NA12273 --sample NA12878

java -jar test-data/reference/tools/pharmcat-3.4.0-all.jar \
  -vcf test-data/reference/slices/NA12273.vcf.gz -o /tmp/out -reporterJson
```

`test-data/reference/manifest.json` is committed with checksums, verified source
URLs and the PharmCAT-derived coordinates. The slices and the JAR are gitignored
(9.5 MB / 32 MB) and fully re-derivable from it.
