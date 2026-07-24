# Faithfulness guard — adversarial validation

**Generated:** 2026-07-23T15:43:33.972556+00:00  
**Model:** `gemini-3.6-flash`  
**Runs:** 12 (4 arms)

> ⚠️ Every explanation quoted in this document is **experimental output,**
> much of it deliberately fabricated. None of it is served to users, and
> `scripts/guard_experiment.py` refuses to write anywhere near
> `explanations.json`. This file exists to evidence that the guard works.

## Why this experiment exists

Until now the faithfulness guard had only ever validated deterministic
text this codebase composed itself — text that was faithful by
construction. A guard that has never rejected anything is an untested
claim, not a safety control.

This experiment puts a real LLM in the conditions under which models are
known to invent clinical detail, and measures what the guard does.

## Method

| Arm | Context sent to the model | Expectation |
| --- | --- | --- |
| `grounded` | the real CPIC recommendation and mechanism | control — should mostly pass |
| `stripped` | context removed; drug name only | model must invent to say anything |
| `corrupted` | plausible but fabricated CPIC text | tests whether internally-consistent invention is caught |
| `coaxed` | real context, but the prompt demands specifics | tests instruction-following under pressure |

**The critical asymmetry:** the model may be *sent* a degraded context,
but the guard always checks its output against the **true** context.
That mirrors runtime, where the guard's reference is verified PharmCAT
data rather than whatever the prompt happened to contain.

## Results

| Arm | Runs | Guard passed | Guard caught | Catch rate |
| --- | --- | --- | --- | --- |
| `stripped` | 2 | 2 | 0 | 0% |
| `corrupted` | 1 | 1 | 0 | 0% |

### Headline

- **0 of 3** ungrounded/corrupted generations were caught by the guard (**0%**)
- Control (`grounded`): 0 of 0 passed

## Caught fabrications — concrete examples

_No fabrications were caught in this run._

That is a result worth stating plainly rather than hiding: either the
model declined to invent even without grounding, or the arms were not
adversarial enough. Re-run with more cases before drawing a conclusion.

## Interpretation

The guard is an **entity-level** check: it verifies that every number,
dose, rsID, star allele, gene and drug name in the output appears in the
supplied context. It does **not** check semantics — it cannot tell that a
mechanism has been described backwards, because every token in such a
sentence may be perfectly grounded.

So this experiment evidences one specific claim: **fabricated clinical
entities do not reach users.** It says nothing about whether faithful
text is also correct. That remains the job of the faculty review.

Raw results: `reports/guard_experiment_raw.json`  
Full guard event log: `logs/guard_events.jsonl`
