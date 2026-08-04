# Onboarding — the mental model, and what you must not break

Read this before changing anything. It is short on purpose; the long-form evidence
lives in `reports/`.

## The one-sentence model

A VCF goes in, and every claim that comes out is either **copied verbatim from
CPIC**, **composed by code from that request's own data**, or **model-written prose
that has been machine-verified to trace to a cited source** — and anything the
system cannot support, it declines to say.

The pipeline:

```
VCF -> coverage gate -> PharmCAT -> CPIC label mapping -> explanation -> client
        (input check)   (genotype)  (rules as data)      (pre-generated)
```

## Three invariants. Breaking any of these is a safety regression, not a bug.

**1. Never assert a phenotype the caller withheld.**
If PharmCAT says `Indeterminate`, or candidate diplotypes disagree about function,
or input coverage is below the measured minimum — the answer is `Unknown`. Not a
best guess, not the first candidate, not the reference haplotype. This invariant was
added after a green `Safe` badge appeared on fluorouracil for a call PharmCAT had
explicitly declined to classify; DPYD deficiency causes fatal fluorouracil toxicity.

**2. Never emit clinical text that does not trace to CPIC.**
The system writes no dosing guidance of its own. `clinical_recommendation` is
byte-identical to PharmCAT's CPIC output. Model-written prose must survive the
provenance guard, which checks it against the cited source rather than against
plausibility. There is **no qualified clinical reviewer on this project** and there
will not be — that is why the machine checks are load-bearing.

**3. Never tune a check until it stops firing.**
The temptation is constant and the project has documented itself yielding to it. If
a check fires, either the code is wrong or the check is wrong — decide which, in
writing, before editing either. Thresholds get pre-committed (`reports/fix_precommitment.md`
is the template) and detectors get sabotage tests that fail when the thing they
guard is reverted.

## Why the architecture looks over-engineered

Because each layer was added after a defect proved it necessary. Five verification
edges now exist; four face the output and one faces the input:

| Edge | Catches |
| --- | --- |
| input → required positions | confidently wrong calls from incomplete VCFs |
| explanation → CPIC | invented clinical claims |
| label → CPIC | mapping errors |
| explanation → label | prose contradicting its own badge |
| phenotype → label | confident labels over unasserted phenotypes |

Eight defects were found in the system's own honesty layer, and **all eight erred in
the same direction** — toward sounding more confident and more reassuring than the
evidence supported. That is not coincidence: in variant-based genomics the reference
allele is the low-risk state, so missing data does not read as uncertainty, it reads
as *normal*. Expect the next defect to be in the same direction, wherever a layer
has to decide what to do with absent information.

## Running things

```bash
cd backend && python -m pytest                      # the whole backend suite
cd app && flutter test && flutter analyze           # client
python scripts/validate_label_mapping.py            # 92/105, exhaustive
python scripts/verify_provenance.py                 # explanation -> CPIC
python scripts/adjudication_status.py               # release gate (exits 1 until done)
```

Nothing above needs an API key. The deployed path makes no outbound call.

Exact test counts live in the README's Key results table and nowhere else — a
number repeated in two documents drifts the moment either one is edited.

Measurement scripts (slow, need the PharmCAT jar via
`python scripts/fetch_reference_data.py --fetch-tools`):

```bash
python scripts/validate_integration.py --limit 400  # integration fidelity
python scripts/measure_coverage_sensitivity.py      # coverage curve
```

## Where the findings live

| Document | What it is |
| --- | --- |
| `reports/provenance_finding.md` | **The primary result.** Twelve pieces of evidence, the unifying bias, and an optimisation rejected for a stated safety reason |
| `reports/validation_report.md` | All validation numbers, each scoped to its evidence |
| `docs/input_requirements.md` | What a VCF must contain, and why a variants-only file is unsafe |
| `PROJECT_STATUS.md` | Honest status, limitations register, remaining work |

## The thing that will confuse you first

`Unknown` is not a failure. It is frequently the correct and hard-won answer, and
several of this project's defects were cases where the system said something
confident instead. If a change makes `Unknown` rarer, that is a claim requiring
evidence — not an improvement.
