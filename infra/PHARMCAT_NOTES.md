# PharmCAT integration notes

Everything here was **discovered by running PharmCAT**, not read off a blog post.
Where something is inferred rather than executed, it says so.

- **PharmCAT version:** 3.4.0 (released 2026-07-14)
- **Allele definition / data version:** `2026-07-13-11-40`, source `CLINPGX`
- **Docker image:** `pgkb/pharmcat:3.4.0` (~1.97 GB) — pinned, never `:latest`

> **How this was verified.** Docker was not available in the environment where
> this was written, so verification used the *same artifacts the image contains*,
> pulled from the matching GitHub release: `pharmcat-3.4.0-all.jar` and
> `pharmcat-pipeline-3.4.0.tar.gz`, run under OpenJDK 25 and Python 3.11 with
> `bcftools`/`bgzip` 1.24. The CLI surface and JSON output below are real
> program output. What is **not** yet verified end-to-end is the Dockerfile
> build itself — see "Still to verify" at the bottom.

---

## 1. Discovering the CLI

```bash
# Java entry point (the JAR's Main-Class is org.pharmgkb.pharmcat.PharmCAT)
java -cp pharmcat.jar org.pharmgkb.pharmcat.PharmCAT --help

# The wrapper that runs preprocessor + pipeline together (this is what we use)
pharmcat_pipeline --help

# The preprocessor on its own
pharmcat_vcf_preprocessor --help
```

### Flags that matter to us

| Flag | Meaning |
| --- | --- |
| `-o <dir>` | Output directory |
| `-bf <name>` | Base filename for outputs (defaults to input's base name) |
| `-reporterJson` | **Machine-readable reporter output** — the one we parse |
| `-matcher` / `-phenotyper` / `-reporter` | Run a single stage independently |
| `-ma` | Return *all* possible diplotypes, not just top hits |
| `-rs CPIC,DPWG,FDA` | Limit recommendation sources |
| `-po <file.tsv>` | **Outside call file** — how a CYP2D6 diplotype gets injected (Phase 5) |
| `-research cyp2d6,combinations` | Research mode. **We deliberately do not use this** |
| `-del` | Delete intermediate files |
| `-0`, `--absent-to-ref` | Treat missing PGx positions as reference. Marked "DANGEROUS!" by PharmCAT itself; we do not use it |

### The command PharmaGuard actually runs

```bash
pharmcat_pipeline <input.vcf> -o <outdir> -reporterJson
```

That single invocation runs preprocessor → named allele matcher → phenotyper →
reporter. It writes:

```
<base>.preprocessed.vcf.bgz     normalised input
<base>.missing_pgx_var.vcf      positions absent from the input
<base>.match.json               named allele matcher output
<base>.phenotype.json           phenotyper output
<base>.report.json              reporter output  <-- the only one we parse
```

`report.json` is a superset of the other two for our purposes (it contains gene
calls *and* CPIC recommendations), so `pharmcat_runner.py` reads only that file.

Typical runtime for a 306-position PGx VCF: **~1.5 s** wall clock.

---

## 2. Operational hazards (learned the hard way)

### The preprocessor rewrites its input directory

Running the pipeline on `work/in/sample.vcf` leaves:

```
work/in/sample.vcf.bgz
work/in/sample.vcf.bgz.csi
```

— the original `.vcf` is **gone**. With `-del` it deleted the input outright
during an early test run.

**Consequence for the backend:** never point PharmCAT at a caller-owned path.
`pharmcat_runner.run_pharmcat()` copies the upload into a private
`tempfile.mkdtemp()` with a nested `in/` directory, and removes the whole tree in
a `finally`. This is not defensive padding; it is required for correctness.

### It may try to download a reference FASTA

The preprocessor downloads the GRCh38 FASTA when it needs to normalise
non-matching representations ("Downloading reference FASTA. This may take a
while..."). Inputs already aligned to PharmCAT's own positions skip this. The
Docker image ships the reference data, so this should not happen in the
container — **verify on first deploy**, because a surprise ~900 MB download
inside a request would blow the timeout.

---

## 3. `report.json` structure (as parsed by `pharmcat_models.py`)

```
report.json
├─ pharmcatVersion            "3.4.0"
├─ dataVersion                "2026-07-13-11-40"
├─ title                      the INPUT FILE's base name — NOT the sample id
├─ genes.<SYMBOL>
│   ├─ callSource             "MATCHER" | "NONE"
│   ├─ uncalledHaplotypes     [...]  populated when positions are missing
│   ├─ messages               [...]  PharmCAT's own caveats
│   ├─ recommendationDiplotypes[0]
│   │   ├─ label              "*2/*2" | "Unknown/Unknown"
│   │   ├─ phenotypes         ["Poor Metabolizer"] | ["No Result"]
│   │   ├─ activityScore      2.0 | null | "No Result"
│   │   ├─ lookupKey          ["Poor Metabolizer"]
│   │   └─ allele1/allele2    {name, function, activityValue}
│   └─ variants[]             {position, dbSnpId, call, referenceAllele, alleles[]}
└─ drugs
    └─ "CPIC Guideline Annotation".<drug>
        └─ guidelines[0]
            ├─ name, url
            └─ annotations[]
                ├─ drugRecommendation      <- verbatim clinical text
                ├─ implications[]          <- verbatim clinical text
                ├─ classification          "Strong"|"Moderate"|"Optional"|"Unspecified"
                ├─ population              "CVI ACS PCI" | "general" | "n/a"
                ├─ lookupKey[]             [{"TPMT":"Poor Metabolizer","NUDT15":"Normal Metabolizer"}]
                ├─ dosingInformation       bool
                ├─ alternateDrugAvailable  bool
                └─ otherPrescribingGuidance bool
```

Sibling sections `DPWG Guideline Annotation`, `FDA Label Annotation` and
`FDA PGx Association` exist; PharmaGuard reads **CPIC only**, by design.

### There is no CPIC level of evidence in this JSON

Searched the full report for `levelOfEvidence`, `evidenceLevel`, `"level"`,
`cpicLevel`, `LOE` — **zero hits**. What exists is `classification`, which is
CPIC's *strength of recommendation* (Strong/Moderate/Optional/Unspecified), a
different scale from the A/B/C/D *level of evidence*.

Therefore `cpic_evidence_level` in our contract is always `"Unknown"`, and the
strength is surfaced verbatim inside `cpic_recommendation`. Deriving an A–D grade
from the strength would be fabricating a clinical claim.
**TODO(phase4):** fetch real levels from the CPIC API.

### An empty `annotations[]` means "no CPIC guidance for this phenotype"

`codeine` returns `annotations: []` whenever CYP2D6 is uncalled. That is the
normal signal for an `Unknown` result — not an error.

Separately, `warfarin` returns an annotation whose `drugRecommendation` is the
**empty string** (CPIC's warfarin guidance is a dosing *algorithm*, not
per-phenotype text). `cpic_engine.select_annotation()` treats an empty
recommendation as unusable and reports Unknown with an explanatory warning.

---

## 4. CYP2D6 is not callable from a plain VCF

Verified directly. With a VCF containing **all 157 CYP2D6 definition positions**:

```
CYP2D6    callSource=NONE     label=Unknown/Unknown    phenotypes=['No Result']
```

and the matcher metadata reports `"callCyp2d": false`. Every other target gene
called normally from the same file. So this is a deliberate PharmCAT decision,
not missing data: CYP2D6 star alleles depend on structural and copy-number
variation that a VCF does not express.

PharmaGuard detects `callSource == "NONE"` and returns phenotype `Unknown` with:

> CYP2D6 structural/copy-number variation cannot be resolved from unphased VCF;
> outside diplotype input planned

**We do not enable `-research cyp2d6`.** PharmCAT documents research mode as
unvalidated; a research-grade call rendered inside a clinical-looking card would
be worse than an honest "Unknown".

**TODO(phase5):** accept an externally-determined CYP2D6 diplotype (Stargazer,
Cyrius, or a lab report) and pass it through `-po outside_calls.tsv`.

---

## 5. Building synthetic test VCFs — the non-obvious part

**A named allele is defined by a combination of positions, not by one famous
rsID.** Setting `rs4244285` (the CYP2C19\*2 marker) to `1/1` and leaving the
other 34 CYP2C19 positions at reference produces **no call at all**:

```
diplotypes: []      matchData.missingPositions: []      warnings: []
```

PharmCAT is not failing — that combination genuinely matches no defined
haplotype. CYP2C19\*2 requires **four** positions (`rs12769205`, `rs58973490`,
`rs4244285`, `rs3758581`).

So `test-data/generate_synthetic_vcf.py` reads the real allele definitions:

```bash
unzip -j pharmcat.jar 'org/pharmgkb/pharmcat/definition/alleles/*.json' -d definitions/
# or:  ./generate_synthetic_vcf.py --from-jar /pharmcat/pharmcat.jar --list CYP2C19
```

Each `<GENE>_translation.json` has `variants[]` (position, ref, alts,
`cpicToVcfAlleleMap`) and `namedAlleles[]` whose `alleles[]` is positionally
aligned to `variants[]`, with `null` meaning "inherit the reference allele".
Some entries are IUPAC ambiguity codes (`R`, `Y`, `M`) or `"X or Y"` alternatives
that must be resolved to one concrete base.

Also note: each gene's own reference allele differs — CYP2C19's is **`*38`**, not
`*1`; DPYD's is `Reference`. An all-reference VCF calls `*38/*38` for CYP2C19.

### Verified generated genotypes

| Requested | PharmCAT called | Phenotype |
| --- | --- | --- |
| `CYP2C19=*2/*2` | `*2/*2` | Poor Metabolizer |
| `CYP2C19=*17/*17` | `*17/*17` | Ultrarapid Metabolizer |
| `TPMT=*3A/*3A` | `*3A/*3A` | Poor Metabolizer |
| `DPYD=c.1905+1G>A (*2A)/Reference` | `c.1905+1G>A (*2A) (heterozygous)` | Intermediate Metabolizer |
| `DPYD=c.1905+1G>A (*2A)/…(*2A)` | homozygous | Poor Metabolizer |
| (all reference) | `*38/*38`, `*1/*1`, `Reference/Reference` | Normal |

---

## 6. Reproducing this locally without Docker

```bash
curl -LO https://github.com/PharmGKB/PharmCAT/releases/download/v3.4.0/pharmcat-pipeline-3.4.0.tar.gz
tar xzf pharmcat-pipeline-3.4.0.tar.gz -C pharmcat/
pip install colorama 'pandas>=2.3.3' packaging
brew install bcftools htslib          # provides bcftools + bgzip

export PHARMCAT_PIPELINE=/abs/path/to/pharmcat/pharmcat_pipeline
uvicorn app.main:app --reload --port 8000
```

`pharmcat_runner.py` reads `PHARMCAT_PIPELINE` (default `pharmcat_pipeline`) and
`PHARMCAT_TIMEOUT_SECONDS` (default 120).

---

## 7. Still to verify

- [ ] `docker compose -f infra/docker-compose.yml up --build` actually builds and
      serves — written against the documented layout of `pgkb/pharmcat:3.4.0`
      but not executed here (no Docker available).
- [ ] Confirm `pharmcat_pipeline` is on `PATH` inside the image, and that
      `/pharmcat/pharmcat.jar` is where the generator's `--from-jar` expects.
- [ ] Confirm no reference-FASTA download happens inside the container.
- [ ] Memory headroom on the HF Spaces free tier with a JVM per request.
