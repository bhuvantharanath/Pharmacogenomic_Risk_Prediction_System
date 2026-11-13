# Phase 10 — data sources

Checked 2026-11-12. Every figure below was read from the source on that date,
by the command or request shown. Nothing is carried over from the brief
unchecked; where the brief and the source differ, both are stated.

## The requirement a source has to meet

One row per required position, with an explicit genotype, homozygous-reference
included: 484 positions over nine genes
(`backend/app/data/position_requirements.json`). A source that omits
reference-matching positions cannot meet it, however good its variant calls
are. That is why the 1000 Genomes phased panel, used for the 400-sample cohort,
left every gene gated.

## Option A — 1000 Genomes DRAGEN reanalysis, per-sample gVCF. **Used.**

| | |
|---|---|
| Registry entry | "1000 Genomes Phase 3 Reanalysis with DRAGEN 3.5, 3.7, 4.0, 4.2, and 4.4", <https://registry.opendata.aws/ilmn-dragen-1kgp/> |
| Bucket | `s3://1000genomes-dragen-v4-4-7/` (also reachable as `https://1000genomes-dragen-v4-4-7.s3.amazonaws.com/`) |
| Access | Anonymous. No AWS account, no credentials, no request signing |
| Per-sample prefix | `data/individuals/hg38-alt_masked.cnv.graph.hla.methyl_cg.rna-11-r5.0-2/<SAMPLE>/` |
| Object used | `<SAMPLE>.hard-filtered.gvcf.gz`, with `<SAMPLE>.hard-filtered.gvcf.gz.tbi` |
| Samples present | 3,202 sample prefixes, listed over 7 pages. All 3,202 IDs in `test-data/reference/1000G_3202_populations.txt` are there |
| Caller | DRAGEN `SW: 13.021.779.4.4.7` (v4.4.7), from the gVCF header's `##DRAGENCommandLine` |
| Reference | `hg38-alt_masked` graph reference. Header contig lengths are GRCh38's (chr1 248,956,422; chr10 133,797,422) |
| Input to the caller | The sample's high-coverage CRAM (`--cram-input <SAMPLE>.final.cram`) |
| Object dates | gVCF objects carry `Last-Modified: 04 Feb 2026` |
| Managed by | Illumina, Inc. |
| Licence | **Listed as "TBD" on the registry page.** See "Licence" below |

### What was tested, and what came back

**R1, bucket reachability.**

```bash
curl -sS -o root.xml -w "%{http_code}\n" \
  "https://1000genomes-dragen-v4-4-7.s3.amazonaws.com/?list-type=2&delimiter=/&max-keys=50"
```

HTTP 200. The listing names one object and three prefixes: `data/`, `giab/`,
`pedigree_files/`.

**R2, indexed range read.**

```bash
bcftools view -H -r chr10:94781850-94781870 \
  "https://1000genomes-dragen-v4-4-7.s3.amazonaws.com/data/individuals/hg38-alt_masked.cnv.graph.hla.methyl_cg.rna-11-r5.0-2/NA12878/NA12878.hard-filtered.gvcf.gz"
```

Exit status 0, three records, about 11 seconds including the 1.3 MB index:

```
chr10 94781822 . T <NON_REF>   . PASS END=94781858  GT:AD:DP:GQ:MIN_DP:PL:SPL:ICNT  0/0:40,0:40:99:36:...
chr10 94781859 . G A,<NON_REF> 53.37 PASS DP=36;... GT:AD:AF:DP:...                 0/1:10,25,0:...
chr10 94781860 . G <NON_REF>   . PASS END=94781882  GT:AD:DP:GQ:MIN_DP:PL:SPL:ICNT  0/0:33,0:33:81:32:...
```

Two reference blocks around a heterozygous call at rs4244285, the CYP2C19\*2
site. This is the shape the requirement needs: the caller states, with a depth
and a genotype quality, that positions 94781822 to 94781858 were read and
matched the reference.

So a whole genome need not be downloaded. A sample's gVCF is 3.4 to 4.9 GB;
the nine gene regions are about 1.1 Mb of it.

### Why a reference block counts as evidence, and where that stops

A gVCF reference block is the caller's own statement about the positions it
spans: genotype `0/0`, a depth, and a genotype quality that is the minimum over
the block. Expanding a block into one row per required position repeats that
statement at single-position resolution. It adds no information and assumes
none. This repository already documents the same operation for users, as
`bcftools convert --gvcf2vcf` in `docs/input_requirements.md`.

Three limits, stated because they bound what a showcase file can claim:

1. **PASS is a low bar in this source.** The header defines the two filters
   that apply to a reference block as `LowGQ: GQ = 0` and `LowDepth: DP <= 1`.
   A block with GQ 1 and depth 2 is therefore PASS. The application's contract
   trusts an explicit PASS and sets no depth or quality threshold of its own,
   so such a row would count. The conversion tool does not add a threshold
   either, because inventing one is exactly what the contract declines to do.
   Instead each sample's sidecar records the lowest depth and genotype quality
   among its rows, per gene, so the strength of the evidence is on the page.
2. **A block is the caller's call, not a second measurement.** It inherits
   every limitation of short-read alignment in that region.
3. **CYP2D6 is not rescued by this.** Its star alleles depend on copy number
   and on hybrids with CYP2D7. Explicit genotypes at 157 positions do not
   establish them, and the application declines CYP2D6 from any VCF.

### Other objects under the same prefix, relevant later

- `<SAMPLE>.star_allele.tsv` (about 600 bytes): DRAGEN's own star-allele calls
  for 22 genes, among them CYP2C19, CYP2C9, SLCO1B1, TPMT, NUDT15, DPYD, VKORC1
  and CYP4F2. Used here to screen and to pre-commit expectations, as a caller
  independent of PharmCAT. **CYP2D6 is not in this file.**
- `<SAMPLE>.targeted.json`: the targeted callers. Its `cyp2d6` object carries a
  genotype, a filter, a quality and a total copy number. For NA12878 it reads
  `"genotype": "*3/*4+*68", "genotypeFilter": "PASS", "genotypeQuality": 150,
  "totalCopyNumber": 5`. This is where section 4 of the brief would take a
  CYP2D6 call from. The brief names `cyp2d6-tsv` and `star-allele-tsv`; in the
  4.4.7 layout the CYP2D6 call is in `targeted.json` and there is no
  `cyp2d6.tsv` object.
- The same file states which definitions DRAGEN's star-allele caller used:
  PharmGKB snapshots from 2022 and 2024, and "PharmCAT Phenotypes Version:
  Snapshot-2022.09.15". PharmCAT 3.4.0 here uses definitions dated 2026-07-13.
  Allele names can therefore differ between the two for the same genotype.

### Licence

The registry page lists the licence as **"TBD"**. The underlying samples are
1000 Genomes Project cell lines, released for open use. The reanalysis is
Illumina's, and Illumina has not stated terms for it on the registry.

What this project takes from it is small: for eight samples, the genotype at
484 positions each. The brief asks for those files to be committed. They are
committed locally; whether to publish them while the source's licence reads
"TBD" is the owner's decision and is raised in the step-4 report. Citation, as
the registry asks: *1000 Genomes Phase 3 Reanalysis with DRAGEN 3.5, 3.7, 4.0,
4.2, and 4.4 was accessed on 2026-11-12 from
https://registry.opendata.aws/ilmn-dragen-1kgp.*

## Option B — GIAB and GeT-RM reference samples. **Used for truth, not for input.**

The same bucket holds DRAGEN results for seven GIAB samples under `giab/`
(HG001 to HG007, from `giab-sample-sex.tsv`). They would convert the same way.
They were not needed: the 1000 Genomes prefix already contains NA12878, which
is HG001.

GeT-RM is where the truth comes from. The brief records that the vendored
workbook covers only CYP2D6, CYP2C19, CYP2C9, VKORC1 and UGT1A1. That is true of
`test-data/reference/getrm_pharmacogenomics.xls`. It is not true of the newer
table this repository froze for its external benchmark,
`test-data/benchmark/external/Consolidated_PGx-HLA_table_1-22-25-V4.xlsx`,
whose derived `sample_gene_truth.tsv` covers 208 individuals who are also in
1000 Genomes:

| Gene | Individuals with an evaluable consensus diplotype |
|---|---:|
| CYP2D6 | 117 |
| CYP2C19 | 101 |
| CYP2C9 | 100 |
| TPMT | 97 |
| SLCO1B1 | 87 |
| DPYD | 83 |
| NUDT15 | 11 |

Seventeen of the 208 are from the South Asian subpopulations. For those
seventeen the table holds a CYP2D6 consensus or a DPYD entry and nothing else.

That benchmark reports application input eligibility of 0 of 208, because its
genomic input was the polymorphic-filtered panel. The same 208 individuals have
gVCFs in the source above. Converting them is outside this step and is noted in
the step-4 report as the obvious next use of this tooling.

## Option C — calling from CRAM ourselves. **Assessed, not used.**

The per-sample prefix also holds `<SAMPLE>.cram` (10.8 GB for NA12878) with an
index, so region-restricted calling with every site emitted is possible, and
this repository has done it once, for CYP2C19 in two samples
(`audit-output/2026-09-30-f4/`). It was not used here because it would replace
a published, versioned call set with one produced by this project: more to
defend, a reference FASTA to fetch and pin, and no gain in coverage over the
gVCF. It stays the fallback if a needed sample has a position the gVCF does not
cover.

## Not used, by rule

- Hand-authored or synthetic VCFs presented as patient data. The synthetic
  files under `test-data/` stay labelled synthetic and are not part of the
  showcase set.
- Any step that fills an uncovered position with an assumed reference
  genotype, including PharmCAT's `--absent-to-ref`.

## Sources used to choose samples, none of them this pipeline

| Source | What it gave | Independence |
|---|---|---|
| DRAGEN `star_allele.tsv`, 792 samples (208 GeT-RM individuals and 601 South Asian samples, 17 in both) | Star-allele calls for eight genes | A different caller with older definitions |
| NYGC 1000 Genomes phased panel, local slices in `test-data/reference/cohort/` | Genotypes at ten marker sites for the South Asian candidates | A different pipeline from the same reads |
| GeT-RM consolidated table, as frozen in `sample_gene_truth.tsv` | Consensus diplotypes | Multi-laboratory consensus, independent of both |
| 1000 Genomes pedigree columns | One trio check | Independent of all calling |

The trio check is worth recording. DRAGEN calls HG02684 (PJL) homozygous for
DPYD c.1905+1G>A. The NYGC panel has the same sample `1|1` at chr1:97450058,
the mother HG02685 `0|0` and the child HG02686 `1|0`, which is what a
homozygous father requires. Two call sets and a pedigree agree.
