# South Asian cohort — 75 → 601

Measured **2026-08-14**. Artifacts: `reports/sas_cohort_expanded.json`,
`reports/sas_frequencies.json`. Scripts: `scripts/expand_sas_cohort.py`,
`scripts/sas_frequencies.py`.

## What was available all along

| | |
| --- | --- |
| 1000G GRCh38 panel | **3202** samples |
| Superpopulation SAS | **601** |
| Previously analysed | **75** |

Verified against `test-data/reference/1000G_3202_populations.txt`, not assumed.

| code | n | where the cohort was collected | previously |
| --- | ---: | --- | ---: |
| PJL | 146 | Punjabi — Lahore, **Pakistan** | 23 |
| BEB | 131 | Bengali — **Bangladesh** | 16 |
| STU | 114 | Sri Lankan Tamil — **UK** | 13 |
| ITU | 107 | Indian Telugu — **UK** | 8 |
| GIH | 103 | Gujarati Indian — Houston, **USA** | 15 |

**The 75 was never a data limit.** It was the arithmetic of proportional
stratification: 400 samples split across five superpopulations by panel share.
Nothing had to be fetched that could not have been fetched before.

## Cost of the expansion

| | |
| --- | --- |
| Remote slicing, 7 gene regions × 601 samples | **41 s** |
| Downloaded | **98.3 MB** (93.9 MB combined VCF + per-chromosome parts) |
| PharmCAT, 601 samples | **1172 s** (1.95 s/sample) |
| Whole genomes downloaded | **none** — region slicing only |

## CYP2C19 reduced function — the figure the project quotes

Reduced function = Poor + Intermediate Metaboliser. 95% Wilson intervals.

| pop | n | PM | IM | reduced | 95% CI | n≥30? |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| STU | 114 | 22 | 51 | **64.0%** | [54.9, 72.3] | yes |
| ITU | 107 | 15 | 50 | **60.7%** | [51.3, 69.5] | yes |
| BEB | 131 | 21 | 54 | **57.3%** | [48.7, 65.4] | yes |
| PJL | 146 | 21 | 58 | **54.1%** | [46.0, 62.0] | yes |
| GIH | 103 | 16 | 35 | **49.5%** | [40.1, 59.0] | yes |
| **pooled** | **601** | 95 | 248 | **57.1%** | **[53.1, 61.0]** | yes |

**The old 53.3% was not wrong — it was imprecise.** It sits inside the new
interval. What changed is that the interval is now ±4 points instead of ±11, and
every subpopulation has n ≥ 103 rather than 8–23.

### Which populations now support a conclusion

**All five**, on the n≥30 convention — up from **none**. At the old n=8 for ITU,
one additional carrier moved the rate 12.5 points; at n=107 it moves 0.9.

But the five are **not distinguishable from each other**. GIH (49.5%) and STU
(64.0%) are the extremes and their intervals still overlap. The honest statement
is *"reduced-function CYP2C19 is common across South Asian cohorts, around
55–60%"*, **not** a ranking of subpopulations. Separating them would need
roughly 400 per cohort, not 100.

## Against published CPIC frequencies

> **SUPERSEDED — see .** This table mixes
> genuine deviations with input and naming artifacts and does not distinguish
> them. It is left in place because the correction below is about it.

CPIC `population_frequency_view`, group **Central/South Asian** (n≈7100).
"Outside" means the published value falls outside our 95% CI.

| gene | allele | ours (n=1202 chr) | CPIC | |
| --- | --- | ---: | ---: | --- |
| CYP2C19 | *2 | 0.3544 | 0.2699 | **outside — we call MORE** |
| CYP2C19 | *1 | 0.3677 | 0.5436 | **outside — we call FEWER** |
| CYP2C19 | *38 | 0.1007 | *(absent)* | reference haplotype CPIC folds into *1 |
| CYP2C19 | *17 | 0.1481 | 0.1708 | outside, narrowly |
| CYP2C19 | *3 | 0.0141 | 0.0157 | agrees |
| CYP2C9 | *2 | **0.0383** | **0.1138** | **outside — 3× under** |
| CYP2C9 | *3 | 0.1015 | 0.1099 | agrees |
| SLCO1B1 | *15 | 0.0349 | 0.0652 | outside |
| TPMT | *1 | 0.9834 | 0.9814 | agrees |
| TPMT | *3C | 0.0125 | 0.0112 | agrees |
| NUDT15 | *1 | 0.9318 | 0.9300 | agrees |
| NUDT15 | *3 | 0.0674 | 0.0670 | agrees |

### CORRECTION (2026-08-14): the mechanism named here was wrong

**An earlier version of this section stated that CYP2C9 `*2`'s defining
position, rs1799853 (chr10:94942290), was ABSENT from the slice and that its
absence accounted for the entire threefold shortfall. That is false. The
position is present.**

The check ran `bcftools query -r chr10` against `cohort_n601.vcf` — an
uncompressed, unindexed file. bcftools refuses that with *"not compressed with
bgzip"*, writes it to stderr, and **exits 255**. The call passed no `check=True`
and never read `returncode`, so the empty stdout became an empty position set;
every membership test then returned False and every position looked absent. Only
the one being looked for was reported.

**A second correction (2026-08-14):** this paragraph first said bcftools "exits
0 while refusing". It does not. That claim came from measuring `$?` after a
pipe — `bcftools … | head -5; echo $?` reports HEAD's status, not bcftools'.
The tool signalled failure clearly; the caller ignored it. Caught by a positive
control written for exactly this class of check.

An empty result set makes every "is X present?" question answer no. That is the
same shape as the other entries in the running tally — a check that returns a
confident answer while having examined nothing — and it is recorded there as
**#17**.

The corrected analysis, with per-chromosome position matching and a linear scan
that needs no index, is in
[`reports/sas_deviation_filtered.md`](sas_deviation_filtered.md). The deviation
table below is superseded by it.

## The coverage gate declines every one of these samples

Measured directly on three samples from different subpopulations:

```
HG01583: CYP2C19=16/35, CYP2C9=17/88, SLCO1B1=20/35, TPMT=9/45  passing=[]
HG03006: CYP2C19=16/35, CYP2C9=17/88, SLCO1B1=20/35, TPMT=9/45  passing=[]
NA20845: CYP2C19=16/35, CYP2C9=17/88, SLCO1B1=20/35, TPMT=9/45  passing=[]
```

Identical, because a panel VCF carries the same site list for every sample —
coverage here is a property of the slice, not of the individual. **No gene
passes for any of the 601.**

So the frequencies above are **PharmCAT's raw calls**, not what the deployed
product would report. Uploaded to PharmaGuard, every one of these 601 samples
returns `Unknown` with a coverage warning.

The gate and the frequency table agree: the calls are not trustworthy enough to
act on, and the gate is what stops them being acted on.

## What this is, and is not

**It strengthens the motivation. It is not clinical evidence.**

* **Not a representative Indian sample.** Four of the five cohorts were
  collected outside India — Houston, the UK (twice), Lahore, Bangladesh. Only
  GIH and ITU are Indian-origin at all, and both are diaspora. A larger n makes
  an estimate of *these cohorts* more precise; it cannot make them
  representative of a population they never sampled.
* **Still research-format input.** Polymorphic-filtered VCF, no
  homozygous-reference rows, so the gate declines everything.
* **Still not externally validated.** External concordance remains **n=1**
  (NA12273). These 601 have no truth labels; PharmCAT's call is the only call.
* **Frequencies are not outcomes.** A reduced-function rate is not a rate of
  harm. Nobody in this cohort took clopidogrel under observation.

What it does support: **reduced-function CYP2C19 is common — roughly 55–60% —
across five South Asian cohorts totalling 601 people**, which is a defensible
motivation for building this, where 75 split five ways was not.

## Surprises

1. **The data was already there.** No new access, no new source — 601 samples
   reachable by the script that already existed, and 41 seconds of slicing.
2. **The old number survived.** 53.3% → 57.1%, with the old estimate inside the
   new interval. Eight-fold more data moved the point estimate by 3.8 points.
3. **The "single missing position" explanation was wrong**, and wrong in the
   most embarrassing way available: the tool reported nothing because the file
   was unindexed, and nothing was read as absence. rs1799853 is present. See
   the correction above and `reports/sas_deviation_filtered.md`.
4. **CYP2C19 `*38`** at 10% has no CPIC row — it is the reference haplotype,
   which CPIC's table folds into `*1`. Comparing allele-by-allele against a
   source that uses a different nomenclature will always produce a "deviation"
   that is nothing of the kind.
