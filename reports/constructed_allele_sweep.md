# Constructed-allele sweep — all 503 named alleles

Audit A carry-forward, closed **2026-08-13**. Raw results:
`reports/constructed_allele_sweep.json`. Harness:
`scripts/sweep_constructed_alleles.py`.

## What this is, and what it is not

**Coverage testing. Not external validation.**

Every input was built *from* PharmCAT's own allele definitions and handed back to
PharmCAT. Agreement therefore shows the pipeline round-trips its own definitions
without losing or corrupting a call. It says nothing about whether those
definitions are correct, and it is not evidence about real patient data.

External concordance in this project remains **n=1** (`NA12273`). This sweep does
not change that number and must never be quoted as though it did.

## Method

For each of the 503 named alleles across the seven genes:

1. build a **complete-coverage** VCF — the target gene at `allele/allele`, all
   six other genes padded to reference, so the coverage gate never fires and a
   decline means something other than thin input;
2. POST it to the real `/analyze` with a drug governed by that gene;
3. compare the reported diplotype against `allele/allele`, and record the
   phenotype, the risk label and which gene the pipeline treated as primary.

681.8 s for 503 alleles against a local backend.

## Result

| gene | alleles | exact | core-allele | other gene primary | anomalies |
| --- | ---: | ---: | ---: | ---: | ---: |
| CYP2C19 | 36 | 36 | — | — | 0 |
| CYP2C9 | 94 | 94 | — | — | 0 |
| DPYD | 84 | 84 | — | — | 0 |
| TPMT | 49 | 49 | — | — | 0 |
| SLCO1B1 | 46 | 44 | 2 | — | 0 |
| NUDT15 | 22 | 13 | — | 9 | 0 |
| **subtotal, callable** | **331** | **320** | **2** | **9** | **0** |
| CYP2D6 | 172 | — | — | — | *not callable by design* |

**No allele failed to call, called as the wrong allele, or produced a label the
CPIC table does not support.**

### The two SLCO1B1 cases are correct, and provably so

`*45.001` and `*45.002` were each reported as `*45/*45`. That is not a lost
sub-allele — it is required:

| file | contains |
| --- | --- |
| `SLCO1B1_translation.json` (matching) | `*45.001`, `*45.002` — and **no `*45`** |
| `SLCO1B1.json` (phenotype) | `*45` = *No function* — and **neither sub-allele** |

PharmCAT matches at sub-allele resolution and reports at core-allele resolution,
because the phenotype table is only defined at the core. Reporting `*45.001`
would produce a diplotype with no phenotype to join to. The resulting label was
**Toxic**, consistent with *No function*.

SLCO1B1 is the only one of the seven genes with dotted sub-alleles, which is why
this appears once and nowhere else.

### CYP2D6: 172 of 172 declined, which is the designed behaviour

Every CYP2D6 allele returned `Unknown`. The gene is defined by copy-number and
structural variation that an unphased VCF cannot express, so the pipeline
declines rather than guessing — the negative control this project has asserted
throughout, here exercised across the entire allele set rather than one cohort.

Reported separately rather than excluded: a sweep that quietly skipped CYP2D6
would be measuring a smaller system than the one that ships.

## The harness was wrong before the pipeline was

The first run scored **nine NUDT15 alleles as `no_call`** — which read as a
serious finding, and was not.

Azathioprine is governed by **TPMT and NUDT15 together**, and the pipeline
reports whichever gene drives the recommendation as `primary_gene`. For a
normal-function NUDT15 allele, TPMT dominates and NUDT15 never appears in the
response. The harness asked "what did you call NUDT15?", got nothing, and
recorded a failure.

What the pipeline actually returned was `TPMT *1/*1 → Safe` — correct for a
patient with a normal NUDT15 and a normal TPMT.

Verified directly:

```
NUDT15=*1   -> primary_gene=TPMT     diplotype=*1/*1  label=Safe   conf=0.95
NUDT15=*3   -> primary_gene=NUDT15   diplotype=*3/*3  label=Toxic  conf=0.95
```

The harness now records the primary gene and distinguishes *"another gene drove
this recommendation"* from *"nothing was called"*. This is instance **#15** in
the running tally of checks that measured something other than what they claimed
— and, like #10–#13, it is mine.

## What this closes, and what it does not

**Closes:** the audit A carry-forward. Every named allele of every gene has been
constructed, run end to end, and its call and label checked.

**Does not close:** external validation. Every input here was generated from the
same definitions used to interpret it. The sweep cannot detect an error *in* the
definitions, only a failure to apply them faithfully — which is precisely the
limit recorded as Evidence 11 for the 100.0000% integration-fidelity figure, and
it applies here for the same reason.
