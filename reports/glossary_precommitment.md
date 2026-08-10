# Glossary coverage gate — rule recorded BEFORE measurement

Written before the extractor was run against the shipped corpus, for the same
reason the mechanism vocabulary check recorded its threshold in advance: a rule
chosen after seeing the number is not a rule, it is a rationalisation. See
`detector_sensitivity.md`, where that check was retired rather than tuned.

## What is being checked

Every string this project shows a user is scanned for domain vocabulary. A term
that appears in user-facing text and has no definition in the glossary is a
**gap**. The gate fails on gaps.

This is deliberately not a check that the glossary is *correct* — that is what
the human review in `glossary_review.py` is for. It checks only that the two
artifacts have been compared at all.

## The extraction rule

Fixed in advance. It does not decide biomedical-ness, and it consults no model
beyond a part-of-speech tagger and a frequency table.

1. **Sources.** Every user-facing string: `explanations.json` (all four prose
   fields of all entries), the template fallback text, backend error messages
   and warnings, the coverage warnings, the four Unknown reasons, the About
   screen copy, the readiness and results copy, the printable summary copy, the
   disclaimers, and the glossary definitions themselves.

2. **Tagging.** spaCy `en_core_web_sm`. Keep tokens tagged `NOUN` or `PROPN`.
   Adjectives and verbs are excluded — the mechanism vocabulary check measured
   that including them was the single largest source of noise (57% → 30% FP when
   narrowed to nouns).

3. **Normalisation.** Lemma, lowercased. Drop anything that is not alphabetic
   (allowing internal hyphens), and drop single characters.

4. **Frequency.** `wordfreq.zipf_frequency(lemma, 'en')`.

5. **Candidate iff `zipf < 4.0`.**

### Why 4.0, and how it was chosen

From the definition of the Zipf scale, not from inspecting the answer. Zipf 4.0
is **one occurrence per 10,000 words** — the conventional boundary on that scale
between everyday vocabulary and words a general reader may not hold. It was
fixed before the extractor was run over the corpus.

It was calibrated against exactly five probe words chosen because they were
already known from the demo (`enzyme`, `prodrug`, `phenotype`, `dose`, `liver`),
to confirm the threshold was not absurd. That is disclosed rather than hidden:
the threshold is a round number on a standard scale, and it was not moved
afterwards.

## The noise pre-commitment

The extractor will flag some ordinary English. Measured as the fraction of
distinct noun lemmas flagged in an **ordinary-English control corpus** that
contains no pharmacogenomics and no software writing:

> **FP rate < 25%** → keep the gate.
> **FP rate ≥ 25%** → report the rate, do NOT gate on it, and say so — the same
> branch the mechanism vocabulary check took at 30%.

### Why 25% here and 15% there

The costs are not the same, and the threshold reflects that rather than
convenience.

A false positive in the mechanism vocabulary check blocked a release, every
time, forever. A false positive here costs a human one keystroke, once: the term
is marked "ordinary English" in a decisions file and never surfaces again. The
gate then stays silent about it permanently.

So a higher rate is tolerable. It is not unlimited — past roughly a quarter, the
review becomes a chore that gets rushed, and a rushed review is how undefined
jargon gets waved through.

**The threshold will not be moved to obtain a green result.** If the rate lands
above 25%, the gate is reported and not enforced, and that is the finding.

## What the gate may never do

- It may not be satisfied by me writing definitions or marking terms as ordinary
  English. Those are human decisions, recorded with who made them and when, in
  the same shape as the adjudication records. An automated decision is recorded
  as automated or it is not recorded.
- It may not be narrowed by removing a source file from the scan.
- It may not be relaxed by raising the frequency threshold after seeing which
  terms that would silence.

## Expected initial state

**The gate is expected to FAIL on first run**, because no human has sorted the
candidate list yet. That is the correct state, not a defect: it is the gap this
audit exists to expose, made visible. It goes green when the review in §2 has
been run by a person — not before.

---

## Measured: two different numbers, and what each one means

Recorded after the first run and after triage. Neither was used to change the
extraction rule — the Zipf threshold is still 4.0 and the parts of speech are
still NOUN/PROPN.

### Out-of-domain false-positive rate: 41.5%

679 of 1,635 distinct noun lemmas flagged in `test-data/glossary/
ordinary_english_control.txt`, a vendored corpus of public-domain prose with no
pharmacogenomics and no software writing in it. Everything flagged there is
wrong by construction. It flags `squirrel`, `apron`, `teapot`, `vegetable`.

**This is the worst case, and it is the number the gate branches on.** It
measures the rule against text the rule was never aimed at.

### In-domain precision: 78.4%

Of the **134** candidates the first run produced on this project's own strings:

| | count | share |
| --- | ---: | ---: |
| developer strings and code identifiers (C, E) — **defects, now fixed** | 18 | 13.4% |
| lemmatiser artifacts (D) — dropped and logged | 4 | 3.0% |
| drug names (B) — already described on the About screen | 7 | 5.2% |
| **candidate glossary terms (A)** | **105** | **78.4%** |

Counting B as glossary work, since a reader may well not know what capecitabine
is, the figure is **83.6%**.

### Why both numbers are kept

They answer different questions, and reporting only one would mislead.

The 41.5% says *how blunt the rule is in general* — the honest measure of a
heuristic, taken on text it cannot have been fitted to. The 78.4% says *how well
it did here*, which is what determines whether a human review is worth someone's
afternoon.

The second is not a defence of the first. It is higher partly because this
corpus is dense with genuine domain vocabulary, which is a property of the
corpus and not a virtue of the extractor.

**Neither number changes the threshold.** The 78.4% is the more flattering
figure and it is precisely the one that must not be used to argue the rule is
sharper than it is. The gate's branch was decided in advance on the
out-of-domain measurement and stays there.

## What triage changed, and what it did not

Two corrections were made to *what is measured*, both after the first run:

1. **A stylesheet is not user-facing prose.** The printable summary embeds CSS
   as a Dart string; it contributed `consolas`, `menlo`, `tbody`. Excluded.
2. **Dart interpolations are code, not words.** `${c.positionsPresent}` was
   being read as prose, exactly as an f-string slot would have been on the
   Python side — where it was already stripped. The asymmetry was the bug.

Both narrow *the corpus* to what a reader actually sees. Neither touches the
threshold, the parts of speech, or the decision rule. The distinction the
project is holding to: correcting what is measured is legitimate; moving the
bar until the number looks better is not.

The 18 developer strings left the candidate list because **the strings were
rewritten**, not because the extractor stopped looking for them. A permanent
guard (`test_no_developer_strings.py`) now fails if any come back.
