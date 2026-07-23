# Explanation generation report

**Generated:** 2026-07-23T14:21:13.327698+00:00  
**Explanation store:** `backend/app/data/explanations.json`  
**Store generator:** `template`  
**Store written:** 2026-07-23T04:10:28.115122+00:00

All figures below are computed from the generated artefacts, not estimated.

## Coverage

| Metric | Count |
| --- | ---: |
| Cases enumerated | 28 |
| **Reachable** | **20** |
| Unreachable (documented, never authored) | 8 |
| Entries in store | 20 |
| — LLM-generated, guard-passed | 0 |
| — Template fallback (guard rejected or API failed) | 0 |
| — Template, pre-LLM legacy | 20 |
| Reachable but missing | 0 |
| Human-reviewed | 0 / 20 |

## Reproducibility

| Field | Value |
| --- | --- |
| Model(s) | _none recorded_ |
| Entries with a prompt hash | 0 / 20 |
| Distinct prompt hashes | 0 |

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
| `clopidogrel` | 6 | 6 | 0 | 0 |
| `codeine` | 1 | 1 | 0 | 4 |
| `fluorouracil` | 4 | 4 | 0 | 0 |
| `simvastatin` | 4 | 4 | 0 | 1 |
| `warfarin` | 1 | 1 | 0 | 3 |

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

**0 of 20** entries carry a `reviewed_by`.

> ⚠️ **Not approved for demo or submission.** The API reports the
> unreviewed count in `quality_metrics.warnings` on every response.
> Run `python scripts/review.py --reviewer '<name>'` or share
> `reports/explanations_for_review.md` with the project guide.

---

_Regenerate with `python scripts/generation_report.py`._
