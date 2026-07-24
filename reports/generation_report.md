# Explanation generation report

**Generated:** 2026-07-24T02:00:56.751704+00:00  
**Explanation store:** `backend/app/data/explanations.json`  
**Store generator:** `llm`  
**Store written:** 2026-07-23T15:41:55.774856+00:00

All figures below are computed from the generated artefacts, not estimated.

## Coverage

| Metric | Count |
| --- | ---: |
| Cases enumerated | 28 |
| **Reachable** | **20** |
| Unreachable (documented, never authored) | 8 |
| Entries in store | 20 |
| — LLM-generated, guard-passed | 0 |
| — Template fallback (guard rejected or API failed) | 1 |
| — Template, pre-LLM legacy | 19 |
| Reachable but missing | 0 |
| Human-reviewed | 0 / 20 |

## Reproducibility

| Field | Value |
| --- | --- |
| Model(s) | `gemini-3.6-flash` |
| Entries with a prompt hash | 1 / 20 |
| Distinct prompt hashes | 1 |

Each entry records the exact model id, a SHA-256 prefix of (model + system instruction + user prompt), and an ISO timestamp. A prompt change is therefore visible as a hash change rather than having to be remembered.

## Faithfulness guard

| Metric | Value |
| --- | ---: |
| Guard evaluations logged | 0 |
| Passed | 0 |
| Rejected | 0 |
| Pass rate | n/a (no events logged) |

_No guard rejections recorded._

For a run against a real model this is worth interrogating rather than
celebrating: check `logs/guard_events.jsonl` is actually being written,
and see `reports/guard_experiment.md` for the adversarial validation
that deliberately provokes fabrication.

## Per-drug coverage

| Drug | Reachable | Generated | Fallback | Unreachable |
| --- | ---: | ---: | ---: | ---: |
| `azathioprine` | 4 | 4 | 0 | 0 |
| `clopidogrel` | 6 | 5 | 1 | 0 |
| `codeine` | 1 | 1 | 0 | 4 |
| `fluorouracil` | 4 | 4 | 0 | 0 |
| `simvastatin` | 4 | 4 | 0 | 1 |
| `warfarin` | 1 | 1 | 0 | 3 |

### Fallback entries and why

| Case | Reason |
| --- | --- |
| `clopidogrel` / `IM` | API error: Gemini returned output that did not match the schema: 1 validation error for _ExplanationSchema
  Invalid JSON: EOF while parsing a string  |

## Unreachable cases

Explanations are **not** authored for these. Writing prose for a case the
pipeline cannot produce would inflate the coverage figure with fiction.

| Drug | Gene | Phenotype | Why unreachable |
| --- | --- | --- | --- |
| `codeine` | CYP2D6 | IM | gene not callable from unphased VCF — star alleles depend on structural/copy-number variation a VCF cannot express; PharmCAT reports callSource=NONE even with a |
| `codeine` | CYP2D6 | NM | gene not callable from unphased VCF — star alleles depend on structural/copy-number variation a VCF cannot express; PharmCAT reports callSource=NONE even with a |
| `codeine` | CYP2D6 | PM | gene not callable from unphased VCF — star alleles depend on structural/copy-number variation a VCF cannot express; PharmCAT reports callSource=NONE even with a |
| `codeine` | CYP2D6 | URM | gene not callable from unphased VCF — star alleles depend on structural/copy-number variation a VCF cannot express; PharmCAT reports callSource=NONE even with a |
| `simvastatin` | SLCO1B1 | RM | no CPIC recommendation text for this gene-phenotype-drug triple in the available PharmCAT output — the pipeline returns Unknown, so there is no recommendation t |
| `warfarin` | CYP2C9 | IM | no CPIC recommendation text for this gene-phenotype-drug triple in the available PharmCAT output — the pipeline returns Unknown, so there is no recommendation t |
| `warfarin` | CYP2C9 | NM | no CPIC recommendation text for this gene-phenotype-drug triple in the available PharmCAT output — the pipeline returns Unknown, so there is no recommendation t |
| `warfarin` | CYP2C9 | PM | no CPIC recommendation text for this gene-phenotype-drug triple in the available PharmCAT output — the pipeline returns Unknown, so there is no recommendation t |

## Review status

**0 of 20** entries have been read by the project author. No qualified clinical expert has reviewed any of them, and none is expected to — see `reports/provenance_report.md` for what is machine-verified in place of that.

> ⚠️ **Not approved for demo or submission.** The API reports the
> unreviewed count in `quality_metrics.warnings` on every response.
> Run `python scripts/review.py --reviewer '<name>'` or share
> `reports/explanations_for_review.md` with the project guide.

---

_Regenerate with `python scripts/generation_report.py`._
