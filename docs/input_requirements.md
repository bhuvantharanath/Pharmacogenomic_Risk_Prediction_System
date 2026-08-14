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

## Where usable files come from — and where they do not

**The most likely first experience is disappointment**, and it is worth
pre-empting: someone downloads a public genome file, uploads it, and gets seven
Unknowns. Nothing is broken. Almost every freely available genome file is the
wrong *shape* for this question, for one of two reasons.

| source | usable? | why |
| --- | --- | --- |
| **Clinical PGx panel** (targeted sequencing) | **Yes** | Built to report every position in the genes it covers, reference matches included |
| **Whole-genome / exome, re-emitted with all sites** | **Yes** | Same property, if the pipeline is asked for it — see the commands below |
| **1000 Genomes, gnomAD, most public research VCFs** | **No** | **Polymorphic-filtered.** They list only positions where someone differed from the reference. Positions that matched are absent, and absent is indistinguishable from never-tested |
| **23andMe, AncestryDNA, MyHeritage exports** | **No** | **A genotyping array, not sequencing.** It reports a few hundred thousand chosen positions across the whole genome — not every position that one gene needs |
| **A VCF from a variant-calling pipeline's default output** | **Usually no** | Defaults emit variants only. The fix is a flag, not a different assay — see below |

### Why a consumer export cannot work, even though it mentions your genes

A 23andMe file may well contain `rs4244285` — a CYP2C19 `*2` marker — and that
makes it tempting to think the file is enough. It is not. An array reports the
positions it was designed to interrogate; PharmCAT needs **every** position that
defines any allele of the gene, because an allele is a *combination* across
positions. Having some of them determines nothing, and the missing ones are
silently read as reference.

This is the same failure as a variants-only file, arriving by a different route.

### The one honest thing to do with an unusable file

Nothing. There is no post-processing that recovers a position that was never
measured — imputation would invent the very data the gate exists to require.
The file is not broken; it answers a different question.

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

## File size — a spec detail, not a constraint to work around

A VCF restricted to PharmCAT's required positions is **~194 KB** for all seven
genes. The API accepts up to **5 MB**, so a conforming file has roughly **25×
headroom**.

That ratio is the useful part: a rejected upload is almost never a file that is
genuinely too big for pharmacogenomics — it is a file covering the wrong *region*.
A raw whole-chromosome 1000 Genomes slice is 28 MB because it carries millions of
positions nobody here reads.

Restrict by position, not by truncation:

```bash
bcftools view -R pharmcat_positions_3.4.0.vcf your.vcf.gz -Oz -o pgx.vcf.gz
```

Trimming the file some other way to get under the cap is the trap: dropping
homozygous-reference rows produces a small file that is *accepted and silently
wrong*, which is the failure this whole document exists to prevent.

## Fixing a file that was rejected

The error messages the API returns say *what is wrong* and point here. They do
not name tools, because the person who hit the error is usually not the person
who built the file — and a message that answers only a bioinformatician reads as
a dead end to everybody else. The commands live here instead.

### "Every position must be reported" — a variants-only file

The most common rejection, and the one with the most dangerous failure mode: a
file listing only differences is indistinguishable from one where the missing
positions were never tested, so a reduced-function result reads as normal.

Re-call emitting **all** sites, not just variant ones:

```bash
# GATK
gatk GenotypeGVCFs -R GRCh38.fa -V input.g.vcf.gz -O all-sites.vcf.gz \
  --include-non-variant-sites

# bcftools — note the ABSENCE of -v, which is what restricts output to variants
bcftools mpileup -f GRCh38.fa input.bam | bcftools call -m -Oz -o all-sites.vcf.gz
```

Then restrict to the positions this analysis needs, using the command in the
file-size section above. Do those in that order: restricting first and re-calling
second loses the reference calls again.

### "This file uses GRCh37 coordinates"

The two builds number the same positions differently, so a GRCh37 file read as
GRCh38 produces confident wrong calls rather than an error. Convert it:

```bash
# CrossMap
CrossMap vcf hg19ToHg38.over.chain.gz input.vcf GRCh38.fa lifted.vcf

# Picard
picard LiftoverVcf I=input.vcf O=lifted.vcf CHAIN=hg19ToHg38.over.chain.gz \
  REJECT=rejected.vcf R=GRCh38.fa
```

Check the reject file. Positions that fail to lift are silently absent from the
output, which puts you straight back into the variants-only failure above.

### "This file looks compressed but could not be opened"

A `.vcf.gz` produced by plain `gzip` is not the same thing as one produced by
`bgzip`, and only the second is readable here:

```bash
gunzip -c broken.vcf.gz | bgzip -c > fixed.vcf.gz
```

## Scope of this measurement

**Coverage sensitivity only.** Inputs are synthesised from PharmCAT's own allele
definitions, so the true genotype is known by construction and complete-coverage
runs are correct by definition. This cannot validate whether those definitions are
right, or whether PharmCAT calls real sequencing data correctly. External accuracy
against consensus genotypes remains **n=1** (`NA12273`), reported as n=1.

What it does establish, and could not be established any other way: the pipeline's
answers degrade **silently** as input coverage falls, and the degradation favours
reassurance.

---

## The gate, and an honest caveat about its thresholds

These thresholds are enforced at upload (`backend/app/coverage.py`). Coverage is
computed from the VCF **before PharmCAT runs**, and any gene below its minimum is
reported `Unknown` with a warning naming the coverage achieved and required.
Per-gene coverage appears in `quality_metrics.position_coverage` on every response,
pass or fail.

Applied to our own 1000 Genomes validation slices, the effect is drastic:

| Gene | Slice coverage | Minimum | Result |
| --- | ---: | ---: | --- |
| SLCO1B1 | 57.1% | 100% | gated |
| CYP2C19 | 45.7% | 100% | gated |
| DPYD | 37.3% | 20% | **gated** — meets the percentage but carries only 8 of 28 decision-critical positions |
| NUDT15 | 25.0% | 80% | gated |
| TPMT | 20.0% | 80% | gated |
| CYP2C9 | 19.3% | 100% | gated |

Usable-result rate over 2 400 (sample, gene) pairs: **82.79% → 12.58%**, with
**1 685** results moving from confident to honest `Unknown` and **zero** moving the
other way. No gene clears its bar on these slices. DPYD was the sole exception until
the decision-critical requirement was added: it meets the 20% percentage but carries
only 8 of the 28 positions that define a non-normal-function allele, so it is now
gated too.

### These thresholds are deliberately strict, and stay that way

**Decision recorded 2026-07-26: the monomorphic-aware relaxation was rejected.** It
would assert "this position is usually reference, therefore this patient is
reference" — the structural bias the gate exists to prevent, with a probability
attached. It fails worst for rare severe variants: DPYD deficiency alleles are rare
(hence monomorphic in a panel) and missing one is fatally consequential. See the
postscript in `reports/provenance_finding.md`.

The caveat below still holds and is the honest reason the gate is blunt rather than
wrong:


Stated plainly because it affects how the number above should be read. The sweep
that produced them dropped positions **at random**. 1000 Genomes filtering does not:
it drops **monomorphic** positions — sites where nobody in the cohort carries a
variant, and where reference is therefore the *correct* call.

Random dropping removes rare functional variants at the same rate as invariant
sites, so it manufactures wrong calls that filtering largely would not. The measured
confidently-wrong rates are consequently an **upper bound** for a
monomorphic-filtered panel, and the 100% thresholds derived from them are stricter
than that input actually requires.

The bound is stated qualitatively on purpose: quantifying it needs a truth set for
this cohort, which does not exist at n>1. What is certain is the direction — the real
risk on 1000G-style input is *lower* than 47.8%, and the safe-but-blunt behaviour of
the gate is the price of not knowing by how much.

For a clinical PGx panel or all-sites WGS the question does not arise: coverage is
complete, every gene passes, and the measured wrong rate is 0%.
