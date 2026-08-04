# Demo files — provenance and purpose

Five files. **No demo mode, no simulated states**: every difference in output
comes from a difference in the input, through the same pipeline.

| File | Rows | How it was made | Demo point |
| --- | ---: | --- | --- |
| `demo_confident.vcf` | 463 | `generate_synthetic_vcf.py --diplotype CYP2C19=*2/*2` with all 7 genes padded to reference. **Complete coverage, clinical-panel-equivalent** — every PharmCAT position carries an explicit genotype including homozygous-reference | S1 · the system answers: clopidogrel **Ineffective**, critical |
| `demo_variants_only.vcf` | 6 | `demo_confident.vcf` with every homozygous-reference row deleted. **Identical genotype**, the common real-world file shape | S2 · the coverage gate declines: **Unknown** |
| `demo_normal.vcf` | 463 | Same generator, all genes at reference. Complete coverage | S5 · a confident **Safe** — the system is not merely cautious |
| `demo_na12273_1000g.vcf` | 169 | Real 1000 Genomes high-coverage slice for NA12273, restricted to PharmCAT's required positions (the full 28 MB slice exceeds the 5 MB upload cap). **The single GeT-RM ∩ 1000G overlap**, so external truth exists | S3 · CYP2D6 declined although GeT-RM records a real `*1/*1` |
| `demo_dpyd_indeterminate.vcf` | 169 | Real 1000 Genomes sample NA19042, same restriction. Carries a compound DPYD genotype PharmCAT classifies as `Indeterminate` | S4 · phenotype→label invariant: **Unknown, not Safe** |

## Why the last two are restricted to PharmCAT positions

The raw slices are ~28 MB and the API caps uploads at 5 MB. Restricting to the
positions PharmCAT actually reads is what a real submission would contain, and it
changes no genotype — only the rows nobody looks at are dropped. Both remain
genuine 1000 Genomes data, not synthesised.

## The pair that matters

`demo_confident.vcf` and `demo_variants_only.vcf` describe **the same patient with
the same genotype.** PharmCAT still calls `*2/*2` from the variants-only file — the
call is not lost. What changes is that the system can no longer verify the input
supported it, so it declines. That is the whole thesis in two files.

Captured responses are in `outputs/`, produced against the live HTTP API.
