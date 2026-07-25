# Regeneration scope after the §1/§2 fixes

**Recorded 2026-07-25. Nothing has been regenerated.** This file states what a
regeneration run *would* touch, so the scope can be approved before any quota is
spent. No model was called to produce it.

---

## Summary: the answer is 0 entries

The headline finding is that **no explanation needs regeneration**, and the
reason is worth stating precisely, because the intuitive expectation was 3.

| Change | Entries whose *label* moved | Entries whose *text* is now wrong | Needs regeneration |
| --- | ---: | ---: | ---: |
| §1 substring-collision fix | 3 (azathioprine family) | **0** | **0** |
| §2(A) `possible decreased function` → IM | 0 | **0** | **0** |
| §2(B) Unknown-prose rewrite | 0 | 2 sentences — **already fixed by hand** | **0** |

Verified by the label/prose cross-check: **0 divergences across all 20 reachable
entries**, run after every change above.

---

## §1 — why the 3 cascade entries do NOT need regeneration

The expectation was that moving azathioprine's label from `Safe` to
`Adjust Dosage` would strand prose written for `Safe`. It did not, because **the
prose was never the defective half.**

Divergence #1 in `consistency.py` records what was actually wrong: azathioprine:IM
carried a green `Safe` badge over prose reading *"your doctor may need to start
you on a lower dose"*. The model's text was correct; the substring collision
produced a wrong label beside it. Fixing the label made the pair agree.

Live labels and the prose now shipped against them:

| Entry | Live label | Summary prose asserts | Agrees? |
| --- | --- | --- | :---: |
| azathioprine:IM | `Adjust Dosage` | "moderate to high risk of myelosuppression" | ✅ |
| azathioprine:NM | `Safe` | "normal metabolizer … safe risk" | ✅ |
| azathioprine:PM | `Toxic` | "can increase the risk of serious side effects" | ✅ |

Regenerating these would replace text that is already correct, spend quota, and
discard the 18 human adjudication decisions attached to their sentences
(azathioprine:IM 7, :NM 6, :PM 5 — counted from the store). **Recommend
against it.**

> Observation, not a divergence: azathioprine:NM's phrase *"you are at safe
> risk"* is the label word `Safe` leaking into prose as an adjective, which is
> awkward English rather than a false claim. It is consistent with the label, so
> no check flags it. Flagged here for the adjudicator's attention, not fixed —
> editing it is a wording judgement, and it would orphan that sentence's decision.

## §2(A) — no text change at all

Adding `"possible decreased function": IM` changed **routing**, not content: a
request carrying SLCO1B1 `Possible Decreased Function` now resolves to the
existing `simvastatin:IM` entry instead of `simvastatin:Unknown`.

`simvastatin:IM` was verified present in the store, so the re-route lands on real
authored prose — there is no new (drug, phenotype) cell to fill. Confirmed:

- 105-combination mapping validation: **92 → 92 agreements, 0 regressions**
- Cross-check: the SLCO1B1 divergence is **gone**
- Severity still distinguishes confidence: tentative IM → `high`, confident
  Poor Function → `critical`

## §2(B) — 2 sentences, already rewritten by hand, 2 decisions returned to the queue

One entry asserted the falsehood: `simvastatin:Unknown`, in `summary` and
`patient_friendly`.

> **was:** …unknown because *your genetic result was not available for this gene*.
> **now:** …unknown because *no usable result for this gene was established*.

This was a hand edit of two clauses, not a generation — the rewrite had to be
true of **both** the no-data and indeterminate states, which is a logical
constraint, not a prose-quality one.

**Consequence, working as designed:** `sentence_key()` hashes the sentence text,
so editing a sentence invalidates any decision recorded against it. Measured:

```
simvastatin:Unknown: 2 of 7 records orphaned by the text edit
store total: 126 records, 124 counted as adjudicated  → gap of exactly 2
```

Those 2 sentences are back in the outstanding queue. That is the correct
outcome — a judgement about wording that no longer exists would be worse than no
judgement — and it means **the adjudication count going down here is evidence the
mechanism works**, not a regression.

---

## What would change if regeneration were approved anyway

Stated so the cost is visible rather than assumed:

- **20 reachable entries × 3 LLM-authored fields = 60 generations** for a full
  re-run; the 3 azathioprine entries alone would be 9.
- **All 124 existing adjudication decisions would be orphaned**, since every
  sentence's text would change. The gate would go from 55 outstanding to ~179.
- The guard, provenance, and cross-check would all have to be re-run, and any new
  divergence re-triaged from scratch.

There is no measured benefit on the other side of that ledger: the cross-check
already reports 0 divergences, and every field-level provenance check already
passes on the text now in the store.

**Recommendation: regenerate nothing.** The remaining work is human adjudication
of the 55 outstanding sentences, which no amount of regeneration reduces.
