# SAS frequency deviations, filtered

**2026-08-14.** Raw output: `reports/sas_deviation_filtered.json`. Script:
`scripts/filter_frequency_deviations.py`.

Every allele in the n=601 comparison, passed through two mechanical filters
before anything is called a population finding. 30 allele rows across five
genes.

| section | count |
| --- | ---: |
| **Input artifacts** — a defining position is absent | **6** |
| **Naming artifacts** — CPIC does not name it comparably | **9** |
| **Genuine population deviations** — survived both filters | **6** |
| Agrees with CPIC (survived both, CI contains published) | 9 |

---

## First: a correction to the previous report

The last report stated that CYP2C9 `*2`'s defining position — rs1799853,
chr10:94942290 — was **absent** from the slice, and that this accounted for the
entire threefold shortfall.

**That was wrong. The position is present**, carrying `ID=10:94942290:C:T`.

The check ran `bcftools query -r chr10` against `cohort_n601.vcf`, which is
uncompressed and unindexed. bcftools refuses that input with *"not compressed
with bgzip"* — on **stderr**, with **exit code 0** and no rows. stderr was
discarded, so the position set was built from empty output. Every `in` test then
returned False, so **every position looked absent**; only the one being looked
for got reported.

An empty result set answers "no" to every membership question. Recorded as **#17**
in the running tally of checks that returned a confident answer having examined
nothing.

The filter below reads positions by linear scan (no index required) and matches
on **(chromosome, position)** rather than position alone — a bare POS is not an
identity, and pooling across six contigs let a chr1 coordinate satisfy a chr10
lookup.

---

## Section 1 — INPUT ARTIFACTS (6)

An allele whose defining positions are not all present cannot be distinguished
from what it would be called instead. Its frequency measures the input.

| gene | allele | positions present | ours | CPIC |
| --- | --- | ---: | ---: | ---: |
| CYP2C19 | `*1` | 16/35 | 0.3677 | 0.5436 |
| CYP2C19 | `*38` | 16/35 | 0.1007 | *(none)* |
| CYP2C9 | `*1` | 17/88 | 0.8353 | 0.7721 |
| SLCO1B1 | `*1` | 20/35 | 0.4384 | 0.4697 |
| TPMT | `*1` | 9/45 | 0.9834 | 0.9814 |
| NUDT15 | `*1` | 5/20 | 0.9318 | 0.9300 |

**Every one is a reference allele, and that is not a coincidence.** `*1` is
defined by *every* position being reference, so it requires the complete set.
At 5 of 20 positions, `*1` is not observed — it is what remains when nothing
else matches. Its frequency is therefore an upper bound inflated by every
variant allele the input could not see.

This is the sharpest form of the project's central claim. The unobservable
default is the *normal-function* call, so missing data does not produce a
missing answer — it produces a **normal** one.

Note the direction: TPMT `*1` 0.9834 vs 0.9814 and NUDT15 `*1` 0.9318 vs 0.9300
look like close agreement. They are not evidence of anything; both genes are
~93–98% reference, so an inflated `*1` is nearly indistinguishable from a correct
one. Agreement here is a property of the allele being common, not of the
measurement being sound.

## Section 2 — NAMING ARTIFACTS (9)

CPIC's Central/South Asian table has no row for these. Absence of a row is not a
frequency of zero, and no comparison exists to deviate from.

| gene | allele | ours |
| --- | --- | ---: |
| CYP2C19 | `*40` | 0.0125 |
| CYP2C9 | `*14` | 0.0191 |
| SLCO1B1 | `*54` | 0.0308 |
| SLCO1B1 | `*14` | 0.0300 |
| SLCO1B1 | `*20` | 0.0050 |
| SLCO1B1 | `*51` | 0.0008 |
| CYP2C19 | `Unknown` | 0.0017 |
| CYP2C9 | `Unknown` | 0.0017 |
| SLCO1B1 | `Unknown` | 0.0150 |

`CYP2C19 *38` also belongs to this class conceptually — it is the reference
haplotype CPIC folds into `*1` — but it fails the coverage filter first and is
reported there. An allele can be more than one kind of artifact; the filters are
applied in order, and coverage is the more fundamental failure.

## Section 3 — GENUINE POPULATION DEVIATIONS (6)

Survived both filters: every defining position present, CPIC names the allele
and publishes a frequency, and the published value falls outside our 95% CI.

| gene | allele | ours | 95% CI | CPIC | direction | n (chr) |
| --- | --- | ---: | --- | ---: | --- | ---: |
| CYP2C19 | `*2` | 0.3544 | [0.3279, 0.3819] | 0.2699 | **higher** | 426 |
| CYP2C19 | `*17` | 0.1481 | [0.1291, 0.1693] | 0.1708 | lower | 178 |
| CYP2C9 | `*2` | 0.0383 | [0.0288, 0.0507] | 0.1138 | **lower** | 46 |
| SLCO1B1 | `*15` | 0.0349 | [0.0260, 0.0469] | 0.0652 | lower | 42 |
| CYP2C9 | `*66` | 0.0033 | [0.0013, 0.0085] | 0.0008 | higher | 4 |
| CYP2C19 | `*8` | 0.0008 | [0.0001, 0.0047] | 0.0000 | higher | 1 |

### A third filter these six have NOT passed

**The populations being compared are not the same population.** CPIC's group is
*Central/South Asian* — an aggregate including Central Asian cohorts. The 1000
Genomes SAS superpopulation is five specific South Asian cohorts. CYP2C9 `*2` is
substantially more common in Central Asian and Middle Eastern populations than
in the Indian subcontinent, which is a sufficient explanation for that row
without invoking any measurement problem.

So these six are **candidate** deviations. Distinguishing "these cohorts differ
from the published aggregate" from "the aggregate is a different population" is
not possible from this data, and is not claimed.

### Two of the six are single-chromosome artifacts of a different kind

`CYP2C19 *8` rests on **one** alternate chromosome out of 1202, and `CYP2C9 *66`
on **four**. They clear the CI test only because the published value is
near zero; one observation is not a population frequency. They are listed for
completeness and should not be quoted.

**That leaves four rows worth any discussion at all, and none of them survives
the population-definition caveat cleanly.**

---

## What this means for the headline

**Nothing in this table changes the reduced-function figure**, which is a
*phenotype* rate computed from diplotype calls (57.1%, [53.1–61.0], n=601), not
an allele-frequency comparison against CPIC.

But it does bound what the allele table can be used for. Of 30 rows: 6 measure
the input rather than the population, 9 have nothing to compare against, 9 agree,
and 6 differ for reasons that include a population-definition mismatch nobody
has controlled for.

**Number of allele-frequency deviations this analysis can attribute to South
Asian population genetics: zero, with confidence.** That is a legitimate result,
and a more honest one than a table of six findings would have been.
