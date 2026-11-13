# Phase 10 §5 — what was changed to make it a product

Measured 2026-11-12. Every figure below was read from a run or a file on that
date; where §5 of the brief turned out to be already done, that is said rather
than re-done.

## 1. The samples the web client offers are now real people

**Before:** the picker bundled four files. Two of them — the ones presented as
"Answers confidently" — had **authored genotypes**. Their positions and alleles
came from PharmCAT's own definitions, but the genotypes were chosen to produce
the answer being demonstrated, and no card said so. The only hint was a fourth
card describing NA12273 as "not synthetic", which tells a reader nothing unless
they already knew.

**After:** every bundled sample is a real, named public genome, transcribed
from the DRAGEN v4.4.7 reanalysis by `scripts/build_showcase_inputs.py`.

| Sample | What it shows | Outcome |
|---|---|---|
| HG02684 (PJL) | DPYD `c.1905+1G>A` on both copies | fluorouracil **Toxic** |
| HG00525 (CHS) | CYP2C19 `*2/*2` and SLCO1B1 `*45/*45` | clopidogrel **Ineffective**, simvastatin **Toxic** |
| HG02661 (PJL) | normal function across every gene read | all four **Safe** |
| HG02684, variants only | the same person, reference rows removed | every gene declined |
| NA12273 | a research VCF exactly as published | every gene declined |

The first and fourth cards are the S1/S2 contrast the brief asks to keep
visible, and it is now **the same real person** rather than a constructed pair:
same genotype, same pipeline, and the Toxic fluorouracil result disappears when
the reference rows go. The card header says so plainly, and the intro line
states that none of the samples is made up.

The old files are not deleted from the repository — `test-data/demo/` still
holds them, because `run_demo.py` needs them (section 4).

## 2. Cold start was already solved, better than the brief's target

The brief asks for the 6.01 GB image to be slimmed toward < 700 MB, or for a
keep-warm ping, or both. **Phase 9 B4 did the first, on 2026-11-04**, and the
numbers are recorded in `infra/DEPLOY_NOTES.md`:

| | |
|---|---|
| Image | **584 MB** uncompressed, linux/arm64, multi-stage (was 6.02 GB from `FROM pgkb/pharmcat:3.4.0`) |
| Cold start after ~15 min idle | **22.40 s, 22.45 s** |
| The old 6 GB image | 82.4 s cold; the 12.85 s figure was measured while it was still cached on the host |

The Dockerfile is already a three-stage build: the PharmCAT jar is copied out
of `pgkb/pharmcat:3.4.0` pinned by digest, the JRE out of `eclipse-temurin`,
onto `python:3.14.6-slim-trixie`, and the jar's SHA-256 is verified in the
image. The notes also record the measurement mistake the brief warns about,
and that it was corrected — so the figure now quoted is the post-eviction one.

Independently corroborated here: a cold `GET /health` against the live Render
instance took **22.59 s** on 2026-11-12, consistent with the recorded 22.4 s.

The keep-warm also exists: `.github/workflows/keepalive.yml`, with the
`schedule:` block deliberately commented out and a `workflow_dispatch` for
warming by hand before presenting. The comment explains the cost — about 144
runs a day, against Render's 750 instance-hours a month — which is why it is
not left on.

**Nothing was changed here.** The §5 cold-start bullet was written against
stale information.

## 3. Versions and result completeness were already in place

- **Versions.** `GuidelineProvenance` carries the PharmCAT version, the CPIC
  data version and the content hashes, and it is rendered on the About screen,
  on the results screen and in the printable summary. PharmVar is deliberately
  absent: PharmCAT 3.4.0 records no PharmVar release number, only a ClinPGx
  data version, so none is claimed.
- **Completeness.** Every cell already renders through dedicated widgets —
  coverage census, gene findings, unknown panel, unknown-reason panel, verdict
  card. The Unknown ledger confirms the outcome on real data: 34 of 42
  showcase cells carry a real CPIC label, and the 8 that do not are the
  declared warfarin abstention and one supplied CYP2D6 call PharmCAT would not
  phenotype. No blanks, no raw enum strings, no unresolved spinners.

## 4. The offline path works, and now says which files are authored

`scripts/run_demo.py` runs all six guard scenarios against a local backend.
Verified end to end on 2026-11-12: six scenarios, each returning its declared
label, with the S1/S2 contrast printed.

Its scenario files stay synthetic on purpose — each isolates **one** guard, and
the DPYD-indeterminate case in particular has no convenient real counterpart.
But the brief's rule is that a synthetic file must be labelled as such in the
filename, the UI and the report, and the terminal output was not labelling it.
It is now:

```
demo_confident.vcf  +  clopidogrel   [SYNTHETIC genotypes — authored to isolate one guard]
demo_na12273_1000g.vcf  +  codeine   [real public genome]
```

Two tests keep that honest: one asserts every scenario's `synthetic` flag
agrees with its file's own `##source=PharmaGuardSyntheticGenerator` header, so
a mislabelled file fails rather than being presented as a person; the other
asserts the marker actually reaches the screen.

## 5. Two stale things this work uncovered

**The captured demo payloads were out of date.** `test-data/demo/outputs/*.json`
are live captures, and running `run_demo.py` refreshed them. They went from
**7 genes to 9** — they had been captured before Phase 9 B5 added VKORC1 and
CYP4F2 to the requirements, so the client was being tested against a payload
shape the backend had stopped producing for a week.

`app/test/live_render_test.dart` had `7 of 7 genes` written into it, so it
failed on the refreshed fixtures. The literal is now **derived from the
payload** rather than written down, which is why the same drift cannot strand
it again. One assertion was deliberately weakened in the process and the reason
is recorded in the test: `demo_confident.vcf` clears only 7 of 9 genes, because
it too predates VKORC1 and CYP4F2. That is a fact about that file, not about
the client — and it is one more reason the web client now ships real samples,
which do carry all nine.

**The codeine limitation named four callers when the API accepts five.** Fixed:
`capabilities.json` now says "(Cyrius, BCyrius, Aldy, StellarPGx or DRAGEN)",
and `app/lib/generated/capabilities.g.dart` was regenerated from it.

## 6. What this cost, and what it did not

Three scientific-core files changed (`capabilities.json`, its generated client
constants, `sample_files.dart`), so the bundle was re-recorded as
`current-candidate-2026-11-12-phase10s5`. Unlike the §4 rebind, this one
**declares** a change, because the limitation string is repeated verbatim into
every CYP2D6 row:

| | |
|---|---:|
| Declared: CYP2D6 `eligibility_reason` rows | 208 |
| Declared: CYP2D6 discrepancy `detail` rows | 117 |
| Scored metrics changed | **0** |
| Exclusions changed | **0** |
| Discrepancy *classifications* changed | **0** |
| Genotypes, phenotypes, labels or abstentions changed | **0** |

Backend **1271 passed**, client **496 passed**, bundle verifier **PASS**, and
`release_status.py --run-required` reports **state: ready**.

## 7. Not verified here

The built web client could not be driven in a browser from this environment:
`flutter build web --release` succeeds and the five sample assets are present
in `build/web/assets/assets/samples/`, but a local static server on ports 3000
and 8080 was unreachable from the sandbox, while port 8000 worked. So the
picker's rendering is covered by widget tests — including the accessibility
tests, which iterate `kSampleFiles` and assert each one's buttons and text —
and by the fact that every bundled file was itself run through the real API,
locally and live. It has **not** been clicked through in a browser on this
machine. That belongs in §6 verification, on hardware where the port is free.
