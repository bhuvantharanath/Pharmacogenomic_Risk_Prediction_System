# PharmaGuard — backend

FastAPI service. Genotypes come from PharmCAT, clinical guidance from CPIC
(verbatim), and narrative explanations from a pre-generated, guard-checked
static set.

## Pipeline

```
upload -> vcf_validation -> pharmcat_runner -> cpic_engine -> explanation -> AnalyzeResponse
          structural       subprocess+parse   label mapping   static lookup
                                                              + slot fill
```

| Module | Responsibility |
| --- | --- |
| `vcf_validation.py` | Structural validation; rejects with a `VcfErrorCode`, never a 500 |
| `pharmcat_runner.py` | Runs `pharmcat_pipeline`; parses `report.json` |
| `pharmcat_models.py` | Typed intermediates — the only code that knows PharmCAT's JSON |
| `cpic_engine.py` | CPIC → contract fields. The clinical interpretation layer |
| `data/label_mapping.yaml` | Risk-label rules, as reviewable data |
| `retrieval.py` | `(gene, drug)` → mechanism document. Exact lookup, no embeddings |
| `explanation/` | The narrative layer — three modes, one guard |
| `data/explanations.json` | Pre-generated explanations. **Requires faculty review** |

## Run it

### With Docker (recommended)

```bash
docker compose -f ../infra/docker-compose.yml up --build
```

### Without Docker

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# PharmCAT — see ../infra/PHARMCAT_NOTES.md §6
brew install openjdk bcftools htslib
pip install colorama 'pandas>=2.3.3' packaging
curl -LO https://github.com/PharmGKB/PharmCAT/releases/download/v3.4.0/pharmcat-pipeline-3.4.0.tar.gz
mkdir -p pharmcat && tar xzf pharmcat-pipeline-3.4.0.tar.gz -C pharmcat/
export PHARMCAT_PIPELINE="$PWD/pharmcat/pharmcat_pipeline"

uvicorn app.main:app --reload --port 8000
```

**No API key is needed.** `GET /` reports `requires_api_key: false` in the
default configuration.

| Env var | Default | Purpose |
| --- | --- | --- |
| `EXPLANATION_MODE` | `static` | `static` \| `live` \| `template` |
| `GEMINI_API_KEY` | — | Live mode and offline pre-generation only |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Model override |
| `PHARMAGUARD_CORPUS_DIR` | auto | Mechanism corpus location |
| `GUARD_LOG_PATH` | `logs/guard_violations.jsonl` | Guard violation log |
| `PHARMCAT_PIPELINE` | `pharmcat_pipeline` | Pipeline executable |
| `PHARMCAT_TIMEOUT_SECONDS` | `120` | Kill a wedged run |

## The explanation layer

### Three modes, one interface

```python
from app.explanation import generate_explanation
result = generate_explanation(context)   # never raises
```

| Mode | What it does | API call? |
| --- | --- | --- |
| `static` **(default)** | Look up `explanations.json` by `(drug, phenotype)`, fill slots | **No** |
| `live` | Call Gemini, run the guard, retry once, else fall back | Yes |
| `template` | Deterministic composition from fixed sentences | No |

Every path degrades downward — live → static → template — so a caller always
gets a complete explanation. The disclaimer is populated on every response by
`Explanation.to_contract()`, regardless of which generator ran.

### Why pre-generate

The explanation space is enumerable: 6 drugs × ~6 phenotypes. Every string a
user can see is therefore a string a human can read **before** it ships. An LLM
in the request path forecloses that — you can review a sample, never the thing
the next user gets. It also removes the key, the rate limit, the latency and
the network failure from the deployed service.

### Slots

Reviewed prose is reused across patients, so patient-specific values are
placeholders filled at runtime: `{diplotype}`, `{detected_variants}`, `{gene}`,
`{drug}`, `{phenotype}`, `{risk_label}`.

`{risk_label}` is a slot for a non-obvious reason: entries are keyed by
`(drug, phenotype)`, but the label is derived from CPIC's *text* by
`cpic_engine`. Those are not the same function — clopidogrel + Poor Metaboliser
is `Ineffective`, not the `Adjust Dosage` a phenotype-keyed guess produces.
Baking it in would let the summary contradict the risk badge above it.

### The faithfulness guard

`explanation/guard.py` is deterministic, free, and always on. It extracts every
number, dose, rsID, star allele, gene symbol and drug name from generated text
and asserts each appears in the supplied context. Anything else is a
hallucination → retry once → fall back to the template → log to JSONL.

**What it does not do is semantics.** It cannot tell that "reduced CYP2C19
function causes the drug to accumulate" is backwards — every token in that
sentence is in the context. It catches fabricated *entities*, which is the
failure with the sharpest clinical edge. Reasoning errors are what the corpus
review and faculty sign-off are for.

> A regression worth knowing about: the first implementation used naive
> substring matching, and an invented "50 mg" passed because the corpus says
> "cytochrome P450" and "P450" contains "50". Matching is now boundary-aware,
> pinned by `test_guard.py::TestSubstringFalseNegatives`.

### Regenerating

```bash
python ../scripts/pregenerate_explanations.py --dry-run
```

See [../scripts/README.md](../scripts/README.md). Output requires faculty
review; the API reports the unreviewed count on every response.

## Endpoints

| Method | Path | Returns |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/` | Metadata, `explanation_mode`, `requires_api_key` |
| `POST` | `/analyze` | `AnalyzeResponse` |

```bash
curl -F "file=@../test-data/cyp2c19_poor_metabolizer.vcf" \
     -F "drugs=clopidogrel,fluorouracil,codeine,aspirin" \
     http://localhost:8000/analyze
```

`quality_metrics.warnings` carries a provenance line per distinct generation
path, e.g. `explanation mode=static, source=static, guard=passed, reviewed=NO`.

### Errors

| Status | `error_code` | When |
| --- | --- | --- |
| 400 | `EMPTY_FILE`, `NOT_VCF`, `CORRUPT_GZIP`, `DECOMPRESSED_TOO_LARGE` | Not a usable VCF |
| 400 | `UNSUPPORTED_VCF_VERSION`, `MISSING_CHROM_HEADER`, `NO_SAMPLE_COLUMN`, `NO_VARIANTS` | Structurally wrong |
| 400 | `UNSUPPORTED_REFERENCE_BUILD` | GRCh37/hg19 |
| 413 | `FILE_TOO_LARGE` | Over 5 MB |
| 422 | `NO_DRUGS`, `TOO_MANY_DRUGS` | Bad drug list |
| 503 | `PHARMCAT_UNAVAILABLE` | PharmCAT missing, timed out, or crashed |

An unrecognised **drug** is never an error.

## Two honest gaps (unchanged from Phase 2)

**`cpic_evidence_level` is always `Unknown`** — PharmCAT's report carries CPIC's
*strength of recommendation*, not the A/B/C/D *level of evidence*. The strength
is surfaced verbatim in `cpic_recommendation`. `TODO(phase4)`.

**CYP2D6 is never called** — its star alleles need copy-number data a VCF cannot
express. Codeine returns `Unknown` with an explicit warning. `TODO(phase5)`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest                                   # 216 passed, 1 skipped
```

No PharmCAT, Java, Docker or API key required.

| File | Covers |
| --- | --- |
| `test_vcf_validation.py` | Every rejection path |
| `test_label_mapping.py` | Table-driven, against verbatim real CPIC text |
| `test_pharmcat_parser.py` | Real output + malformed-input degradation |
| `test_guard.py` | Adversarial: invented doses, rsIDs, alleles, drugs, genes |
| `test_explanation.py` | Retrieval, slots, mode dispatch, mocked live mode |
| `test_corpus.py` | The no-dosing-in-the-corpus rule, as a build gate |
| `test_analyze_api.py` | `/analyze` end to end, incl. API-free static mode |

The skipped test is live mode against the real Gemini API; it runs only when
`GEMINI_API_KEY` is set.
