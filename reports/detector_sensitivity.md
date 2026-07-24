# Detector sensitivity

**Generated:** 2026-07-24T09:54:33.165622+00:00  
**Method:** known-bad sentences injected into real generated text, then run through the field-level + polarity checks.

## Why this exists

The filter flagged **0 of 160** sentences on the shipped set, immediately
after three rounds of false-positive removal (12 → 4 → 0). A zero at that
point is ambiguous: the text may be clean, or the detector may have been
blunted while the false positives were fixed. Those readings have opposite
consequences, so the zero is tested rather than trusted.

Violations are injected into **real generated prose**, not synthetic
sentences — proving the check fires against the text actually shipped, in
context, rather than merely proving a regex matches.

## Headline

- **5/5 planted violations caught**
- **0 false alarms** on 2 clean controls

✅ **No misses.** Every planted violation was flagged.

✅ **No false alarms.** Every clean control passed.

## By violation class

| Class | Caught | Planted |
| --- | ---: | ---: |
| `comparative` ✅ | 1 | 1 |
| `dose` ✅ | 1 | 1 |
| `mechanism` ✅ | 1 | 1 |
| `polarity` ✅ | 1 | 1 |
| `timeline` ✅ | 1 | 1 |

## Every trial

| Host | Class | Expect | Got | Sentence |
| --- | --- | :---: | :---: | --- |
| `fluorouracil:IM` | dose | FLAG | FLAG ✅ | Your doctor will start you on 25 mg twice daily. |
| `fluorouracil:IM` | timeline | FLAG | FLAG ✅ | Results usually appear within three days of starting treatme |
| `fluorouracil:IM` | polarity | FLAG | FLAG ✅ | Do not consider a reduced starting dose. |
| `fluorouracil:IM` | mechanism | FLAG | FLAG ✅ | The enzyme is inhibited by grapefruit juice, which raises pl |
| `fluorouracil:IM` | comparative | FLAG | FLAG ✅ | You are twice as likely to have a reaction as other patients |
| `fluorouracil:IM` | clean_control | pass | pass ✅ | Please discuss this result with your doctor or pharmacist. |
| `azathioprine:PM` | clean_control | pass | pass ✅ | Your doctor may choose a different medicine for you. |

## What this does and does not establish

It establishes that the detector still fires on the five failure classes
it claims to cover, against real prose. It does **not** establish that the
shipped text is correct: the documented blind spot — a reversed causal
claim assembled entirely from sourced concepts — is not in the planted set
because the detector provably cannot catch it. That is what human
adjudication is for.

Companion evidence: `reports/guard_experiment.md` (does the guard catch
fabrication when a model actually produces it) and
`reports/provenance_finding.md` (why the earlier lexical checker was
unsound).

