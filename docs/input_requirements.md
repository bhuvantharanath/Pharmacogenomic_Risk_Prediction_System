# Input requirements — what a VCF must contain

**Measured 2026-07-26.** 120 synthetic samples, 12 random position subsets per
coverage level, two genotype backgrounds. Artifact: `reports/coverage_sensitivity.json`.

## The headline, because it is not the one we expected

We set out to measure "at what coverage does PharmaGuard decline to answer?" That
was the wrong question. **Reduced position coverage does not make the pipeline
decline. It makes PharmCAT confidently call the reference haplotype**, because a
variant whose defining position is absent from the VCF is simply invisible — and
every observed position then reads reference.

The error direction is **false reassurance**, every time:

| Coverage | True phenotype | Reported |
| ---: | --- | --- |
| 20% | `Decreased Function` (SLCO1B1 \*1/\*15) | **`Normal Function`** as \*1/\*1 |
| 20% | `Intermediate Metabolizer` (CYP2C9 \*1/\*2) | **`Normal Metabolizer`** as \*1/\*1 |
| 20% | `Intermediate Metabolizer` (TPMT \*1/\*3A) | **`Normal Metabolizer`** as \*1/\*1 |

Status `DEFINITE`, one candidate, phenotype asserted. Nothing in the response
signals doubt, because from the matcher's point of view there is none.

## Confidently-wrong rate vs position coverage

Percentage of samples where a phenotype was asserted that disagrees with the
complete-coverage truth for the same genotype.

| Gene | 100% | 80% | 60% | 40% | 20% |
| --- | ---: | ---: | ---: | ---: | ---: |
| **CYP2C9** | 0.0% | **17.4%** | 28.6% | 33.3% | 47.8% |
| **NUDT15** | 0.0% | 0.0% | **25.0%** | 29.2% | 37.5% |
| **SLCO1B1** | 0.0% | 0.0% | **15.0%** | 19.0% | 42.9% |
| **TPMT** | 0.0% | 0.0% | 8.3% | 20.8% | 20.8% |
| **CYP2C19** | 0.0% | 0.0% | 4.3% | 12.5% | 30.0% |
| **DPYD** | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |

DPYD is immune across the whole range because its clinically actionable variants
are each defined by a single position, and CPIC scores it by activity rather than
by matching a full reference haplotype.

## The requirement

| Gene | Minimum coverage of PharmCAT's defining positions |
| --- | --- |
| CYP2C19 | **100%** |
| CYP2C9 | **100%** |
| SLCO1B1 | **100%** |
| TPMT | 80% |
| NUDT15 | 80% |
| DPYD | 20% |

"Minimum" means the lowest level at which every replicate both resolved *and* was
correct. For three of six genes that is **complete coverage** — nothing less is
safe, because the failure mode is a confident wrong answer rather than a refusal.

### What this means in practice

**Supply a VCF covering all 306 positions in PharmCAT's positions file**, with an
explicit genotype at every one — including homozygous-reference calls. That is what
a clinical PGx panel or unfiltered whole-genome/exome calling produces.

**Do not supply a variants-only VCF.** A file listing only non-reference sites is
indistinguishable, to the matcher, from a file where those positions were never
assayed. This is the single most consequential input requirement here.

`pharmcat_positions_3.4.0.vcf` is fetched by
`scripts/fetch_reference_data.py --fetch-tools` and lists every required position.

### Why our own validation set falls short, and what that costs

The 1000 Genomes high-coverage panel is filtered to polymorphic sites, so a
position where nobody in the cohort varies is absent. Our slices therefore carry
19–57% of PharmCAT's positions:

| Gene | Positions present / required |
| --- | ---: |
| SLCO1B1 | 20/35 (57.1%) |
| CYP2C19 | 16/35 (45.7%) |
| DPYD | 31/83 (37.3%) |
| NUDT15 | 5/20 (25.0%) |
| TPMT | 9/45 (20.0%) |
| CYP2C9 | 17/88 (19.3%) |

Every rate measured on that set is therefore a **floor**, and — more importantly —
some of its confident answers are in the confidently-wrong band above. The
phenotype→label invariant suppresses the *ambiguous* cases, which is why
simvastatin returns `Unknown` for 54% of those samples. It cannot suppress a
confident wrong call, because nothing in the data marks it as wrong.

## Scope of this measurement

**Coverage sensitivity only.** Inputs are synthesised from PharmCAT's own allele
definitions, so the true genotype is known by construction and complete-coverage
runs are correct by definition. This cannot validate whether those definitions are
right, or whether PharmCAT calls real sequencing data correctly. External accuracy
against consensus genotypes remains **n=1** (`NA12273`), reported as n=1.

What it does establish, and could not be established any other way: the pipeline's
answers degrade **silently** as input coverage falls, and the degradation favours
reassurance.
