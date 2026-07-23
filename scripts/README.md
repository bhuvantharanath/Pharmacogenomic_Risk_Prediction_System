# Scripts

## `pregenerate_explanations.py`

Generates the static explanation set that the deployed service serves.

> ⚠️ **`backend/app/data/explanations.json` requires faculty review before any
> demo or submission.** Every entry is written with `"reviewed_by": null`, and
> the API reports the unreviewed count in `quality_metrics.warnings` on every
> response. Nothing here is approved until a human has read it.

### Why pre-generate at all

The explanation space is enumerable: six drugs × a handful of phenotypes. That
makes it possible to have **every string a user can ever see** reviewed by a
person before it ships. An LLM in the request path forecloses that — you can
review a sample, never the thing the next user actually gets.

It also takes the API key, the rate limit, the latency and the network failure
mode out of the deployed service. Runtime does a dictionary lookup and
deterministic slot filling.

### The workflow

```
1. generate   ->  2. inspect  ->  3. faculty review  ->  4. ship
   this script     read the        set reviewed_by       commit the JSON
                   JSON diff       on every entry
```

**1. Generate.** Needs PharmCAT reports to source real CPIC text from. The
repo's two test fixtures cover a few phenotypes; for full coverage, generate
VCFs across the phenotype space first (see *Getting full coverage* below).

```bash
export GEMINI_API_KEY=...          # only for --generator llm
python scripts/pregenerate_explanations.py --reports out/*.report.json
```

**2. Inspect.** The script prints a per-case audit table and a summary:

```
SUMMARY
  cases enumerated : 36
  generated        : 20
  guard failures   : 0
  fallbacks        : 0
  gaps (no CPIC)   : 16
```

A non-zero **guard failure** count means the model invented entities and its
output was rejected — check `backend/logs/guard_violations.jsonl` for what it
tried to say. **Gaps** are cases with no CPIC recommendation at all; those are
legitimate and fall back to the deterministic template at runtime.

**3. Review.** For each entry, check that: the direction of effect is right
(does reduced function mean more drug effect or less?), no dosing number appears
that CPIC did not state, `patient_friendly` is genuinely plain language, and the
"Unknown" cases do not imply a normal result. Then set `reviewed_by`.

**4. Ship.** Commit `explanations.json`. The runtime picks it up on next start.

### Options

| Flag | Purpose |
| --- | --- |
| `--dry-run` | Enumerate cases and print the table without spending quota |
| `--generator template` | Deterministic composition, no API key — usable in CI |
| `--generator llm` | Gemini (default). Needs `GEMINI_API_KEY` |
| `--model <id>` | Override the model id |
| `--drug <name>` | Regenerate one drug, e.g. after editing its mechanism file |
| `--reports <paths>` | PharmCAT `report.json` files to source CPIC text from |

### Getting full coverage

The CPIC text for a case can only come from a PharmCAT report in which that gene
actually has that phenotype. Two fixtures are not enough — they cover the
phenotypes those two samples happen to have. Generate a spread first:

```bash
DEFS=definitions/                  # extracted from the PharmCAT JAR
GEN=test-data/generate_synthetic_vcf.py
ALL=CYP2C19,CYP2C9,SLCO1B1,TPMT,NUDT15,DPYD

for spec in "CYP2C19=*2/*2" "CYP2C19=*1/*2" "CYP2C19=*17/*17" "CYP2C19=*1/*17" \
            "CYP2C9=*3/*3" "CYP2C9=*1/*2" "SLCO1B1=*5/*5" "SLCO1B1=*1/*5" \
            "TPMT=*3A/*3A" "TPMT=*1/*3A" \
            "DPYD=c.1905+1G>A (*2A)/c.1905+1G>A (*2A)" \
            "DPYD=c.1905+1G>A (*2A)/Reference"; do
  python $GEN --definitions-dir $DEFS --diplotype "$spec" --pad-genes $ALL \
              --sample S -o work/in.vcf
  pharmcat_pipeline work/in.vcf -o "work/out_$(echo $spec | tr -d '*/=. ')" -reporterJson
done

python scripts/pregenerate_explanations.py --reports work/out_*/*.report.json
```

That yields 20 generated cases and 16 gaps.

### The 16 gaps are real, not bugs

| Gap | Why |
| --- | --- |
| codeine, all phenotypes | PharmCAT cannot call CYP2D6 from a VCF at all |
| warfarin, all phenotypes | CPIC's warfarin guidance is a dosing *algorithm*, not per-phenotype text |
| azathioprine RM/URM | TPMT and NUDT15 have no rapid/ultrarapid phenotype |
| fluorouracil RM/URM | DPYD has no rapid/ultrarapid phenotype |
| simvastatin RM/URM | SLCO1B1 is a transporter; CPIC has no increased-function row |

Each falls back at runtime to the template generator, which states plainly that
no recommendation was available rather than inventing one.

### Two traps this script exists to avoid

**Baked-in patient values.** Reviewed prose is reused across patients, so
anything patient-specific must be a slot (`{diplotype}`, `{detected_variants}`)
filled at runtime. The pre-generation context therefore supplies the placeholder
*strings themselves* rather than concrete values — and rather than `None`, which
would make generators take their "nothing was called" branch and bake in text
asserting no genotype was found.

**Baked-in risk labels.** The risk label is derived from CPIC's *text* by the
rule engine, not from the phenotype. Clopidogrel + Poor Metaboliser is
`Ineffective`, which a phenotype-keyed guess would call `Adjust Dosage`. The
script therefore derives it with the production engine (`classify_annotation`),
and `{risk_label}` is a runtime slot — otherwise the reviewed summary could
contradict the risk badge rendered directly above it.

### Regenerate when

- A mechanism file changes → `--drug <that drug>`
- PharmCAT is upgraded → everything; new CPIC text may change labels
- A drug is added to the corpus → everything

**Re-review after every regeneration.** `reviewed_by` resets to `null`.
