# Test fixtures

Real PharmCAT **3.4.0** `report.json` output, trimmed. These let the whole test
suite run with **no PharmCAT, no Java and no Docker** installed.

| File | Genotype it came from |
| --- | --- |
| `pharmcat_report_cyp2c19_pm.json` | `CYP2C19 *2/*2` (Poor Metaboliser), everything else reference |
| `pharmcat_report_dpyd_im.json` | `DPYD c.1905+1G>A (*2A)` heterozygote (Intermediate Metaboliser) |

## What "trimmed" means

Genes and drugs outside PharmaGuard's scope were dropped, along with keys the
parser never reads (`relatedDrugs`, `variantsOfInterest`,
`matcherComponentHaplotypes`, `matcherHomozygousComponentHaplotypes` on genes;
`citations`, `urls`, `variants` on drugs). That takes each file from ~1 MB to
~140 KB.

**No value was edited.** Every string the tests assert on is exactly what
PharmCAT emitted. That matters most for `test_label_mapping.py`, whose whole
purpose is to pin our label rules against genuine CPIC wording.

## Regenerating

```bash
# 1. Get PharmCAT (see infra/PHARMCAT_NOTES.md section 6)
curl -LO https://github.com/PharmGKB/PharmCAT/releases/download/v3.4.0/pharmcat-pipeline-3.4.0.tar.gz
mkdir -p pharmcat && tar xzf pharmcat-pipeline-3.4.0.tar.gz -C pharmcat/

# 2. Build the input VCF
python ../../test-data/generate_synthetic_vcf.py \
    --from-jar pharmcat/pharmcat.jar \
    --diplotype 'CYP2C19=*2/*2' \
    --pad-genes CYP2C19,CYP2C9,SLCO1B1,TPMT,NUDT15,DPYD \
    --sample CYP2C19_POOR_METABOLIZER -o /tmp/in/sample.vcf

# 3. Run the pipeline.
#    NOTE: the preprocessor REWRITES its input directory (it bgzips the .vcf in
#    place). Always give it a throwaway copy.
pharmcat/pharmcat_pipeline /tmp/in/sample.vcf -o /tmp/out -reporterJson

# 4. Trim /tmp/out/sample.report.json as described above.
```

## When to regenerate

On any PharmCAT upgrade. A new PharmCAT ships new allele definitions **and new
CPIC text**, and our label rules match on that text — so a version bump can
silently change a `risk_label`. Regenerate, re-run `pytest`, and read the diff on
any failing row in `test_label_mapping.py` before adjusting the rules.
