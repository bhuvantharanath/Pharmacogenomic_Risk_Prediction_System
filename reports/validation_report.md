# Validation against reference materials — Phase 6 COMPLETE

**Date:** 2026-07-25 · **Status:** Phase 6 closed. Integration fidelity measured at scale
(400 samples, §2b) alongside the exhaustive label-mapping validation (§4).
External genotype concordance remains **n=1** and is reported as n=1 throughout —
never as a percentage. Every number here is real; none is projected.

The validation harness is written: `scripts/validate_integration.py` (cohort
fidelity + failure classes), `scripts/validate_testvcfs.py` (PharmCAT's own
adversarial test VCFs), `scripts/validate_frequency.py` (aggregate frequency
concordance). Artifacts under `reports/*.json` carry every number below.

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

## 2b. Integration fidelity at scale — 400 samples, 2026-07-25

The n=1 external concordance above is unchanged and still n=1. This section
measures something different and much larger: **does PharmaGuard report what
PharmCAT actually said?** That question needs no truth labels, so it scales.

**Cohort.** 400 of the 3202 samples in the 1000 Genomes high-coverage phased
panel, stratified proportionally by superpopulation and selected deterministically
(seed 20260725): AFR 112, EUR 79, SAS 75, EAS 73, AMR 61. Sliced by remote region
extraction — no whole-genome download.

Two measurements made the run cheap enough to be routine: slicing cost is
dominated by reading the region's compressed blocks rather than by sample count
(1 sample 3.87 s, 300 samples 3.83 s, same region), and PharmCAT accepts a
multi-sample VCF, so the whole cohort costs one JVM start. Total wall clock for
400 samples: **11.7 minutes**.

### Result: 100.0000%

| | |
| --- | ---: |
| Samples requested | 400 |
| Samples with a PharmCAT report | **400** |
| (sample, gene) pairs compared | 2 800 |
| Field comparisons (diplotype + phenotype) | **5 600** |
| Mismatches | **0** |
| Samples erroring in our parser | **0** |

Compared field-by-field against `report.json` read independently of our parser —
deliberately not reusing `parse_report()`, because a comparator sharing code with
the thing it checks is the circularity that made an earlier provenance metric
meaningless.

### 🔴 One real defect, found and fixed by this run

The first run scored **95.60%**, and the 8 mismatches were all DPYD. PharmCAT
publishes two diplotype lists that mean different things:

| Field | NA19042 DPYD | Phenotype |
| --- | --- | --- |
| `sourceDiplotypes` | `c.85T>C (*9A)/[c.85T>C (*9A) + c.1371C>T]` | **Indeterminate** |
| `recommendationDiplotypes` | `c.85T>C (*9A)/c.85T>C (*9A)` | Normal Metabolizer |

`sourceDiplotypes` is what the matcher **called**. `recommendationDiplotypes` is
PharmCAT's own reduction for **looking up** a CPIC row — compound alleles split so
an activity score can be assigned. Our parser read the second for everything,
which is right for the lookup and wrong for the display. The consequence, in 4 of
302 called DPYD samples:

* a variant the patient carries (`c.1371C>T`) silently dropped from the reported
  genotype, and
* **`Normal Metabolizer` displayed where PharmCAT had said `Indeterminate`** —
  presenting certainty PharmCAT explicitly withheld.

That second one is over-claiming, the mirror image of limitation #21 where the
same enum under-claimed. Fixed architecturally rather than by special-casing DPYD:
`sourceDiplotypes` now drives what we report about the patient, and
`recommendationDiplotypes` continues to drive CPIC selection via `lookup_keys`, so
no recommendation changed. A new `recommendation_diplotype` field keeps the
reduction visible for audit. Re-measured: **100.0000%**.

A second class of apparent mismatch — 26 CYP2D6 rows of `'Unknown/Unknown'` vs
`None` — was a false positive of the comparator, not a defect: our parser
normalises every no-call sentinel to `None`, which `PharmcatGeneCall` documents.
The equivalence is now declared explicitly rather than silently ignored.

### Second fidelity check: PharmCAT's own test VCFs

The 1000 Genomes cohort exercises *common* variation. PharmCAT's unit-test VCFs
are hand-built to break the matcher — rare alleles, missing positions, compound
heterozygotes, hom/het boundaries. All 74 covering our genes were run, taken from
`src/test/resources/.../haplotype` at tag v3.4.0.

| | |
| --- | ---: |
| Files compared | **74 / 74** |
| Field comparisons | 148 |
| Mismatches | **0** |
| Errors | **0** |

Per gene: CYP2C19 27, SLCO1B1 17, TPMT 11, CYP2C9 9, DPYD 7, NUDT15 3.

**A secondary comparison, reported separately because it does not test us.**
These files are named after the genotype they encode (`s1s2.vcf` → \*1/\*2). Of
74, **29 names were decodable** by a strict star-pair rule; 45 were left undecoded
rather than guessed at, because inventing an expected value would manufacture a
denominator. Of the 29, **23 matched PharmCAT's call**. All 6 differences were
traced to the decoder, not to PharmCAT:

| File | Name encodes | PharmCAT called | Why the name is not the answer |
| --- | --- | --- | --- |
| `s1s4b`, `s4as4b`, `s4bs17` | \*4A / \*4B | \*4 | PharmCAT 3.4.0 defines no \*4A/\*4B — only \*4 (verified in the shipped allele definitions) |
| `s3bs3c` (TPMT) | \*3B/\*3C | \*1/\*3A | \*3A is defined by exactly the two positions of \*3B + \*3C; unphased data cannot distinguish cis from trans, so \*1/\*3A is the correct call |
| `s1s1s` (TPMT) | \*1/\*1S | \*1/\*1 | decoder mis-split the name |
| `s1s2b` (DPYD) | \*1/\*2B | `c.1627A>G (*5)` | DPYD does not use plain star nomenclature |

So the honest reading is 74/74 integration fidelity, and **zero** evidence of a
PharmCAT calling error in this set.

---

## 3. Call rates, failure characterisation, and frequency concordance

### Usable-result rate

A "usable" result means the gene produced a phenotype CPIC can act on. CYP2D6 is
excluded from the denominator because it is the negative control — it is *expected*
to fail, and counting it as failure would flatter nothing and confuse everything.

| | |
| --- | ---: |
| Callable (sample, gene) pairs — 6 genes × 400 | 2 400 |
| Produced a usable phenotype | 1 987 |
| **Usable-result rate** | **82.79%** |

**Both halves of that number, because either alone misleads.** 82.79% is what this
*validation input* yields, and it is a **floor rather than an estimate of production
performance**: the 1000 Genomes panel is filtered to polymorphic sites, so our
slices carry only 19–57% of the positions PharmCAT asks for (table below), and the
missing ones disproportionately define reference-like haplotypes — which is exactly
what produces the 308 ambiguous calls that make up three-quarters of the shortfall.
A clinical panel or unfiltered WGS covering PharmCAT's full position list would call
more. Equally, it is **not** a number to wave away: it is measured on real human
data, the ambiguity is genuine, and for CYP2C9 every ambiguous call is truly
phenotype-discordant, so `Unknown` is the honest answer there and not an artifact.

| Failure class | n | What it means |
| --- | ---: | --- |
| `not_attempted_structural` | 400 | CYP2D6, `callSource: NONE`. **400/400 — the negative control held perfectly.** Not one fabricated call |
| `ambiguous_multiple_diplotypes` | 308 | PharmCAT returned several equally-likely diplotypes |
| `called_but_unclassifiable` | 103 | genotype obtained, no CPIC phenotype assignment (`Indeterminate`) |
| `no_call_missing_positions` | 2 | matcher ran, could not call |

Per-gene call rate (phenotype obtained):

| Gene | Called | Rate |
| --- | ---: | ---: |
| NUDT15 | 400/400 | 100.0% |
| TPMT | 399/400 | 99.8% |
| CYP2C19 | 398/400 | 99.5% |
| CYP2C9 | 329/400 | 82.2% |
| DPYD | 302/400 | 75.5% |
| SLCO1B1 | 159/400 | 39.8% |
| CYP2D6 | 0/400 | 0.0% *(negative control)* |

**SLCO1B1's 39.8% is the headline weakness.** It is not a parsing failure — 398
of 400 samples got a *diplotype*; they just could not be resolved to a single one.
Ambiguity there is severe and population-structured: only 163 of 400 samples had
exactly one candidate, 153 had four, and 84 had ten.

### Input completeness — a property of the slices, stated plainly

Our sliced VCFs contain a minority of the positions PharmCAT asks for, because the
1000 Genomes panel is filtered to polymorphic sites: a position where nobody in
the panel varies simply is not there.

| Gene | Positions present / required |
| --- | ---: |
| SLCO1B1 | 20/35 (57.1%) |
| CYP2C19 | 16/35 (45.7%) |
| CYP2D6 | 67/157 (42.7%) |
| DPYD | 31/83 (37.3%) |
| NUDT15 | 5/20 (25.0%) |
| TPMT | 9/45 (20.0%) |
| CYP2C9 | 17/88 (19.3%) |

Checked directly: the defining positions for the alleles that matter clinically
(CYP2C9 \*2/\*3/\*8/\*9, CYP2C19 \*2/\*3/\*17, SLCO1B1 \*5/\*15/\*37) are **all
present**. The absent positions are ones that define reference-like haplotypes,
which is why they drive *ambiguity* rather than wrong calls.

This is a property of the validation input, not of the product: a clinical VCF
covering PharmCAT's full position list would not behave this way. It does mean the
call rates above are a **floor**, not an estimate of production performance.

### Is an ambiguous diplotype also an ambiguous phenotype? — measured 2026-07-25

The pipeline collapses every ambiguous call to `Unknown`. That is only correct if
the candidate diplotypes disagree about *function*, which does not follow from
disagreeing about *identity*. Measured over the same 400 samples, three ways:
**strict** (identical phenotype strings), **informative** (agreement among
candidates that say anything — `n/a` is an absence of a claim, not a competing one),
and **class** (all informative candidates map to one value of our `Phenotype` enum,
which is the actionable condition).

| Gene | Called | Ambiguous | Strict | Informative | Same class |
| --- | ---: | ---: | ---: | ---: | ---: |
| CYP2C19 | 400 | **0** | — | — | — |
| TPMT | 400 | **0** | — | — | — |
| NUDT15 | 400 | **0** | — | — | — |
| DPYD | 400 | **0** | — | — | — |
| CYP2D6 | 400 | **0** | — | — | — |
| CYP2C9 | 400 | 71 | 0 (0.0%) | 0 (0.0%) | **0 (0.0%)** |
| SLCO1B1 | 400 | 237 | 2 (0.8%) | 10 (4.2%) | **40 (16.9%)** |

Ambiguity is confined to two genes. Four of the seven — including every gene whose
call rate exceeds 99% — have no ambiguous calls at all.

**CYP2C9: 0 of 71 concordant by any definition.** `Unknown` is unambiguously the
right answer; this is a limitation to document, not a bug. The pattern is always a
real phenotype against `Indeterminate`, e.g. `*1/*3 → Intermediate Metabolizer`
versus `*1/*18 → Indeterminate`. We genuinely do not know.

**SLCO1B1: 40 of 237 class-concordant, but only 30 usefully so.** Ten of the forty
resolve to `Unknown` anyway (every informative candidate was itself
`Indeterminate`), so recovering them gains nothing. The remaining **30 (12.7% of
ambiguous calls, 7.5% of the cohort)** share one pattern exactly:

| Candidates | Informative phenotypes | Our enum |
| --- | --- | --- |
| `*5/*37`, `*5/*42`, `*5/*52`, `*5/*56` | `Decreased Function`, `Possible Decreased Function` | both → **IM** |

All 30 have that shape: every candidate that says anything agrees the transporter
function is **decreased**, differing only in confidence. We report `Unknown`.

#### What these 30 actually did — corrected

**They already reported `Toxic`.** An earlier draft of this section claimed they
returned `Unknown` and dropped a myopathy warning; that came from this script's own
failure classification rather than from the pipeline, and checking the pipeline
directly disproved it. They were correct — though only incidentally, because
`candidate[0]` happened to be the informative candidate. That is now principled
rather than accidental: the resolver requires every informative candidate to agree.

The real defect was the reverse, and much larger — see the correction below.

#### Proposal — NOT implemented

Recorded for a decision, deliberately unbuilt.

**The rule.** When a call is ambiguous, map every informative candidate phenotype
through `phenotype_map`. If they all yield one enum value, report that phenotype and
mark the diplotype as unresolved. If they do not, keep `Unknown` — which preserves
today's behaviour for 83% of ambiguous SLCO1B1 calls and 100% of CYP2C9's.

**Contract change: yes, and it cannot be avoided.** The response can currently say
"we know the genotype" or "we know nothing"; it has no way to say "we know the
function but not the genotype". Minimally:

* `diplotype` — set to a plain unresolved marker rather than one arbitrary candidate.
  Picking `sourceDiplotypes[0]` for display would assert a specific genotype we
  cannot support, repeating the §2b error in a new place.
* `candidate_diplotypes` — the list, already parsed and currently dropped.
* `phenotype_confidence` or similar — needed so a client can distinguish this state
  from a fully resolved call. A warning string will not do: the client cannot branch
  on prose, which is the same limitation already recorded as #21.

**What the client would show.** The risk badge and CPIC recommendation exactly as
for a resolved call — those follow from the phenotype, which is what we would now
know. The genotype line changes from `*5/*37` to something like *"decreased function
(4 possible genotypes)"*, expandable to the candidate list. The honest framing is
that the *functional consequence* is established while the *specific star alleles*
are not.

**Cost against benefit.** Pydantic, the response contract, the Dart model, the
expandable card, and new explanation-store routing for a phenotype-known /
diplotype-unknown state — for 7.5% of samples on one gene, where the root cause is
input incompleteness rather than pipeline design. Deferring is defensible. Doing it
silently is not, which is why both halves are in the limitations table.

### 🔴 Correction and the largest defect of the phase — phenotype → label

**An earlier draft of this report said 30 concordant SLCO1B1 calls "report
Unknown, dropping a myopathy warning". That was wrong**, and the error was mine:
the 39.8% figure came from the validation script's own failure classification, not
from the pipeline. Checked directly, the pipeline already reported `Toxic` for
those 30. Nothing was being dropped there.

What the direct check *did* find is larger and worse, in the opposite direction.

The verification graph had four edges and only three were checked —
explanation→CPIC, label→CPIC and explanation→label. **phenotype→label was not.**
A confident label could therefore sit beside a phenotype the caller declined to
assert, and every existing checker would pass, because each was correct about its
own edge.

Two mechanisms produced it:

1. **Unasserted phenotype reaching the lookup.** `lookup_keys` come from
   `recommendationDiplotypes`, which exists to *find a table row*. A DPYD
   `Indeterminate` call still carries activity score 2.0, so the lookup found the
   Normal Metabolizer row and the label engine rendered `Safe` — on fluorouracil,
   where deficiency is fatal.
2. **Reading `candidate[0]` when candidates disagree.** For SLCO1B1, one candidate
   said `Normal Function` and a co-equal one said `Indeterminate`; taking the first
   asserted a confident `Safe`.

Measured effect of the fix over the same 400 samples × 6 drugs:

| Drug | Change | n |
| --- | --- | ---: |
| simvastatin | `Safe` → `Unknown` | **195** |
| fluorouracil | `Safe` → `Unknown` | 81 |
| fluorouracil | `Adjust Dosage` → `Unknown` | 17 |
| azathioprine | `Safe` → `Unknown` | 1 |
| clopidogrel, warfarin, codeine | unaffected | 0 |

**294 of 2 400 results changed, every one removing a confident label. None moved
the other way.** 49% of the cohort had been shown a green `Safe` for simvastatin
on evidence that did not support it.

The invariant is general — *a phenotype the caller declined to assert can never
produce a confident label* — and gated **before** the CPIC lookup, so an unasserted
phenotype never reaches `lookup_keys`. A phenotype→label check now runs at build
time over every reachable case and at request time on every response, degrading to
`Unknown` with a warning rather than serving a contradiction.

**It keys on phenotype agreement, never on diplotype ambiguity.** 30 calls have
every informative candidate reading `Decreased Function` or `Possible Decreased
Function` — unanimous on function, differing only in confidence — and those still
produce a confident `Toxic`, with `variant_rationale` stating the split: function
known, exact star alleles undetermined. Suppressing them would have traded
over-claiming for under-claiming. The genuinely discordant 195 and all 71 ambiguous
CYP2C9 calls remain `Unknown`, which is correct for them.

A trap worth recording: the first implementation filtered every `UNKNOWN`-mapping
candidate out before comparing, collapsing `{Normal Function, Indeterminate}` to
`{NM}` and leaving all 195 samples as broken as before. `n/a` is silence;
`Indeterminate` is testimony. Only re-running the cohort caught it.


### Every rate here has a floor and a ceiling — both are stated

| Measure | Floor (1000G filtered slices, 19–57% position coverage) | Ceiling (complete coverage) |
| --- | ---: | ---: |
| Overall usable-result rate | **82.79%** (1 987/2 400) | **100%** — every gene resolves to one diplotype at complete coverage |
| SLCO1B1 single-diplotype rate | **39.8%** | **100%** |
| simvastatin confident label | **46%** (218/400 Unknown) | **100%** |
| DPYD confident label | **75.5%** | **100%** |

Neither number alone is honest. The floor is real, measured on human data, and is
what a variants-only VCF will produce. The ceiling is also real and is what a
clinical PGx panel produces. **The gap is input coverage, not pipeline capability.**

And a warning that belongs beside both: below complete coverage the pipeline does
not merely decline more often — for three of six genes it begins answering
*confidently and wrongly*, always replacing a reduced-function phenotype with a
normal one. See `docs/input_requirements.md`.


### Two input classes, always stated together

The rates below characterise **the input**, not the system. Quoting either alone
misrepresents it in opposite directions.

| Input class | Confident-label rate | Measured wrong rate |
| --- | ---: | ---: |
| **Complete coverage** (clinical PGx panel, all-sites WGS/WES) | **100%** | **0%** |
| **Polymorphic-filtered slices** (1000 Genomes, 19–57% position coverage) | **12.58%** | gate declines the remainder |

On the filtered slices the coverage gate declines 5 of 6 genes as unsuitable for
confident calling. **That 12.58% is a property of the input, not a failure rate of
the pipeline** — the same pipeline reaches 100% with 0% error on input that meets
the documented requirements. The gate is doing its job when it declines: the
alternative, measured, is a confident wrong call in the false-reassurance direction.

### Frequency concordance — an aggregate sanity check, and only that

**Stated explicitly: this is not per-sample validation.** It asks whether the
distribution of alleles we call across 400 unrelated people resembles CPIC's
published distributions. A pipeline that shuffled calls between samples at random
would still pass it. What it *is* sensitive to is whole-class error — a strand
flip, a coordinate off-by-one, a reference/alternate swap, or a population-specific
allele never being called.

**Source:** CPIC API, `https://api.cpicpgx.org/v1/population_frequency_view`,
verified live and **accessed 2026-07-25**; responses cached under
`test-data/reference/cpic_frequencies/`.

**The population mapping is approximate and load-bearing.** 1000G superpopulations
and CPIC biogeographic groups are different taxonomies: EUR→European,
EAS→East Asian, SAS→Central/South Asian, AFR→Sub-Saharan African, AMR→Latino.
CPIC's "Sub-Saharan African" and 1000G's AFR are not the same population. A few
points of deviation should be read against that, not as pipeline error.

#### Where it agrees

CYP2C19, TPMT and NUDT15 had **no ambiguous calls at all**, so their frequencies
are unqualified:

| Gene · allele | Ours | CPIC |
| --- | ---: | ---: |
| CYP2C19 \*2 | 21.6% | 19.2% |
| CYP2C19 \*17 | 14.8% | 14.9% |
| CYP2C19 \*17 in EAS | **0.0%** | 2.1% |
| TPMT \*1 | 94.8% | 95.6% |
| TPMT \*3A | 1.4% | 1.6% |
| NUDT15 \*3 | 3.5% | 3.4% |
| NUDT15 \*3 in SAS | 6.7% | 6.7% |

The near-absence of CYP2C19 \*17 in East Asians is reproduced, which is the kind
of population-specific structure a coordinate or strand error would destroy.

#### Deviations, reported rather than buried

**CYP2C19 \*1 in SAS: ours 39.3% vs CPIC 54.4% (−15.0 pp).** Explained by
nomenclature, not error. PharmCAT 3.4.0 calls \*38 where CPIC's frequency table
still counts \*1, and CPIC publishes no \*38 row at all. Combining them:

| | EUR | EAS | SAS | AFR | AMR |
| --- | ---: | ---: | ---: | ---: | ---: |
| ours \*1+\*38 | 62.0% | 64.4% | 48.7% | 54.9% | 72.1% |
| CPIC \*1 | 62.5% | 59.6% | 54.4% | 55.2% | 71.7% |

Three of five groups agree to within 0.5 pp.

**SLCO1B1: no defensible frequency estimate, and that is the finding.** Two
reasonable estimators disagree wildly, because 59% of SLCO1B1 calls are ambiguous
and the ambiguity is population-structured (EUR 10%, SAS 63%, AFR 82%, EAS 92%):

| Estimator | SLCO1B1 \*37 | SLCO1B1 \*1 | CYP2C9 \*2 in EUR |
| --- | ---: | ---: | ---: |
| take first candidate | 40.3% | 36.7% | 13.3% |
| unambiguous calls only | **0.0%** | 64.0% | **0.0%** |
| CPIC published | 53.2% | 32.5% | 12.7% |

Taking the first candidate is an arbitrary pick among equals; restricting to
unambiguous calls sounds stricter but is systematically worse, because variant
carriers are the ones most often ambiguous, so excluding them inflates the
reference allele — visibly so for CYP2C9 \*2, which falls from a near-exact 13.3%
to 0.0%. Publishing either number alone would hide that the answer depends on the
choice. Both are reported; where they differ by ≥5 pp (SLCO1B1 \*37, \*1, \*14 and
CYP2C9 \*1) **no frequency claim is made.**

### The SAS breakout — n is the honest headline

The project's motivation cites Indian populations; this is the first real data
behind that claim, and the data does not support a per-population statement.

| SAS population | Cohort n | CYP2C19 result |
| --- | ---: | --- |
| PJL (Punjabi, Lahore) | 23 | IM 12, RM 6, NM 4, URM 1 |
| BEB (Bengali, Bangladesh) | 16 | NM 5, PM 4, IM 4, RM 3 |
| GIH (Gujarati Indian, Houston) | 15 | NM 6, IM 3, RM 3, PM 1 |
| STU (Sri Lankan Tamil) | 13 | IM 8, PM 3, NM 2 |
| ITU (Indian Telugu) | 8 | IM 5, RM 1, NM 1 |

**No per-population conclusion is drawn.** At n=8 to n=23, one individual moves a
proportion by 4–12 points; these counts are reported so the sample size is visible,
not because they support inference.

At the **superpopulation** level SAS has n=75 (150 chromosomes), which supports a
cautious statement: **CYP2C19 reduced-function phenotypes (IM + PM) reach 53.3% in
SAS** (40/75; IM 42.7%, PM 10.7%) — the second-highest of the five groups after EAS
(57.5%) and well above EUR (32.9%). Allele frequencies agree with CPIC's
Central/South Asian figures (\*2 31.3% vs 27.0%; \*17 16.7% vs 17.1%).

That is a real, defensible result relevant to the stated motivation, and it is a
statement about the 1000 Genomes SAS panel — not about any clinical population, and
not a substitute for per-sample validation.

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
