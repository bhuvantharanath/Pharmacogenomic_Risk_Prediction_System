# Test data

Synthetic GRCh38 VCFs for exercising the real PharmCAT pipeline.

> **These are fabricated.** They do not come from any person, biobank or
> reference sample. The *positions and alleles* are real — read out of PharmCAT's
> own allele-definition data — but the genotypes were chosen to demo specific
> phenotypes.

## Files

| File | Sample | PharmCAT calls | Demo |
| --- | --- | --- | --- |
| `cyp2c19_poor_metabolizer.vcf` | `CYP2C19_POOR_METABOLIZER` | `CYP2C19 *2/*2` → Poor Metaboliser | clopidogrel → **Ineffective** |
| `dpyd_variant_carrier.vcf` | `DPYD_VARIANT_CARRIER` | `DPYD c.1905+1G>A (*2A)` het → Intermediate Metaboliser | fluorouracil → **Adjust Dosage** |
| `normal_metabolizer_control.vcf` | `NORMAL_CONTROL` | all reference | everything → **Safe** |

Each file carries all 306 definition positions for CYP2C19, CYP2C9, SLCO1B1,
TPMT, NUDT15 and DPYD. **Every shipped sample is expected to produce a
non-`Unknown` result for its intended drug**, and
`backend/tests/test_sample_vcfs.py` enforces that — a sample with no declared
expectation, or too few positions to be callable, fails the build.

> **Removed:** `sample1.vcf` and `sample2.vcf` were Phase 1 relics carrying 5
> and 4 hand-picked rsIDs. Once PharmCAT became real they were not merely
> uninformative — a gene's *full* position set is required to call a diplotype,
> so PharmCAT exited without writing a report at all and `/analyze` returned
> **503 PHARMCAT_UNAVAILABLE**. Anyone who picked the first file in the list
> during a demo got a server error. They have been deleted.

## Generating your own

```bash
# List what can be built
python generate_synthetic_vcf.py --from-jar /pharmcat/pharmcat.jar --list CYP2C19

# A CYP2C19 poor metaboliser
python generate_synthetic_vcf.py --definitions-dir definitions/ \
    --diplotype 'CYP2C19=*2/*2' \
    --pad-genes CYP2C19,CYP2C9,SLCO1B1,TPMT,NUDT15,DPYD \
    --sample MY_SAMPLE -o my_sample.vcf
```

### Why the generator reads PharmCAT's definitions

**A named allele is a combination of positions, not one famous rsID.** Setting
`rs4244285` (the "CYP2C19\*2 marker") to `1/1` and leaving the gene's other 34
positions at reference yields **no call at all** — that combination matches no
defined haplotype. CYP2C19\*2 needs four positions together.

So the generator reads `<GENE>_translation.json` from the PharmCAT JAR and emits
every definition position for the gene, applying the requested haplotype and
inheriting reference elsewhere. `--pad-genes` adds other genes at their reference
diplotype so one file can exercise the whole panel.

Watch out: each gene's reference allele differs. CYP2C19's is **`*38`**, not
`*1`; DPYD's is `Reference`.

Always verify what you generated:

```bash
pharmcat_pipeline my_sample.vcf -o out/ -reporterJson
python -c "import json;r=json.load(open('out/my_sample.report.json'));\
print({g:(b['recommendationDiplotypes'] or [{}])[0].get('label') for g,b in r['genes'].items()})"
```

## Try it

```bash
curl -F "file=@test-data/cyp2c19_poor_metabolizer.vcf" \
     -F "drugs=clopidogrel,fluorouracil,codeine,aspirin" \
     http://localhost:8000/analyze
```

- `clopidogrel` → **Ineffective**, severity `critical`, `CYP2C19 *2/*2`, PM
- `fluorouracil` → **Safe** (DPYD is reference in this file)
- `codeine` → **Unknown** — CYP2D6 is not callable from a VCF; see
  [infra/PHARMCAT_NOTES.md](../infra/PHARMCAT_NOTES.md) §4
- `aspirin` → **Unknown** — no CPIC guideline

Gzipped uploads (`.vcf.gz`, bgzip or plain gzip) are accepted.

---

## Phase 6: real validation samples

Synthetic files prove the *plumbing*. They cannot prove the pipeline is
**correct**, because they were built from the same definitions PharmCAT calls
with — the test and the implementation share an assumption. Validating against
samples with independently established genotypes is the point of Phase 6.

### GeT-RM (the right starting point)

The CDC's Genetic Testing Reference Materials programme publishes consensus PGx
genotypes for Coriell cell lines, characterised across multiple labs and
platforms — a genuine ground truth.

- Consensus genotype tables: <https://www.cdc.gov/labquality/get-rm/>
- Cell lines and DNA: <https://www.coriell.org/> (NIGMS/NHGRI repositories)
- PharmCAT publishes its own GeT-RM benchmark results — compare against those
  first, since a mismatch there means our *invocation* is wrong, not PharmCAT.

### 1000 Genomes (free, no application)

Whole-genome VCFs, publicly downloadable, and overlapping the GeT-RM sample set
(the Coriell lines are largely 1000 Genomes participants) — so you get real data
*and* a consensus genotype to check against.

- <https://www.internationalgenome.org/data>
- GRCh38-aligned releases only — PharmCAT rejects GRCh37, and so do we.
- These are whole-genome and far over our 5 MB upload cap. Subset to the PGx
  regions first:
  ```bash
  bcftools view -R pharmcat_regions.bed input.vcf.gz -Oz -o pgx_only.vcf.gz
  ```
  `pharmcat_regions.bed` ships in the PharmCAT pipeline tarball.

### What a validation run should produce

For each sample: expected diplotype (GeT-RM consensus) vs. called diplotype, per
gene, with concordance counted and every discordance explained. Log the PharmCAT
version and data version — allele definitions change between releases, and a
"regression" is often just a definition update.

### Ethics note

1000 Genomes and Coriell data are consented for research and openly published,
which is why they are usable here. Do not put anyone's clinical or personal
genetic data through this project: it is a student prototype with no
safeguards, no access control, and an explicit not-for-clinical-use disclaimer.


## Demo set — `demo/`

Presentation files. The contrast is real: there is no demo mode and no simulated
state, only different input shapes through the same pipeline. Full provenance in
[`demo/README.md`](demo/README.md).

| File | Shape | Demonstrates |
| --- | --- | --- |
| `demo/demo_confident.vcf` | Complete coverage, clinical-panel-equivalent | CYP2C19 \*2/\*2 → clopidogrel **Ineffective** |
| `demo/demo_variants_only.vcf` | **Same genotype**, hom-ref rows removed | The coverage gate declines → **Unknown** |
| `demo/demo_normal.vcf` | Complete coverage, all-reference | A confident **Safe** — the system does answer |
| `demo/demo_na12273_1000g.vcf` | Real 1000 Genomes slice | CYP2D6 declined although GeT-RM records \*1/\*1 |
