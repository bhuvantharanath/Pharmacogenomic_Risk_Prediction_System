# Ordinary-English control corpus

`ordinary_english_control.txt` — the text the glossary extractor's
false-positive rate is measured against.

## What it is

Two public-domain works, concatenated:

- *Alice's Adventures in Wonderland*, Lewis Carroll (1865)
- *The Wonderful Wizard of Oz*, L. Frank Baum (1900)

Retrieved once from Project Gutenberg and **vendored here on purpose**. A
false-positive rate measured against something that has to be downloaded is a
rate nobody can reproduce, in CI or otherwise.

## Why these

The measurement needs prose containing **no pharmacogenomics and no software
writing**, so that every term the extractor flags is wrong by construction —
there is nothing in here for it to correctly find. Plain narrative English with
a small vocabulary is the closest available approximation to "what an ordinary
reader already knows".

## The honest limitation

They are Victorian children's books. `gryphon`, `juryman`, `sunbonnet` and
`blacking` are flagged and counted as false positives, which inflates the rate
above what a modern corpus would give. The measured **41.5%** is therefore an
**upper bound**, and it is reported as one.

It was not swapped for something more flattering after the number came in. The
rate decides whether the gate blocks CI (see `reports/glossary_precommitment.md`),
and changing the measurement after seeing the result is the thing that
pre-commitment exists to prevent. A better control corpus would be a change to
make deliberately, in advance, and to re-report both numbers against.

## Licensing

Both works are in the public domain in the United States and in most
jurisdictions — Carroll died in 1898, Baum in 1919.

The Project Gutenberg header and footer were stripped before vendoring, which
also removes the Project Gutenberg trademark and licence notice. That is the
condition under which Gutenberg permits unrestricted reuse: the text itself is
public domain, and the licence attaches to the branding rather than to the
words. Nothing here is redistributed under the Gutenberg trademark.

The boilerplate was removed for a second reason as well — legal prose is not
ordinary narrative English, and leaving it in would have measured the wrong
thing.

## Regenerating

Not automated on purpose. Re-fetching would silently change a number that other
documents quote. If it ever needs replacing, do it as a deliberate step and
re-run:

```bash
python scripts/extract_glossary_candidates.py --fp-only
```

then update `reports/glossary_precommitment.md` with both the old and new rates
and say why the corpus changed.
