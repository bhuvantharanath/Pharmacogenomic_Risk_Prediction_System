# Phase 10 — the Unknown ledger

Every Unknown and every missing value in the showcase run, with its root cause.
Measured 2026-11-12 against commit `fdb27cb`, PharmCAT 3.4.0, allele
definitions dated 2026-07-13.

Runs: all seven showcase samples through the local pipeline and through the
deployed API at `pharmaguard-api-baml.onrender.com`, six drugs each.

## The headline

| | |
|---|---:|
| Cells in the showcase (7 samples × 6 drugs) | 42 |
| Cells the shipped application can label from a VCF (4 drugs × 7) | 28 |
| **Of those, rendering a real CPIC-backed label** | **28 / 28** |
| Codeine cells, with a CYP2D6 diplotype supplied beside the file (§4) | 7 |
| **Of those, rendering a real CPIC-backed label** | **6 / 7** |
| **Cells with a real label, out of 42** | **34** |
| Cells Unknown | 8 |
| Of those, warfarin (declared abstention) | 7 |
| Of those, a supplied call PharmCAT would not phenotype | 1 |
| Unexpected Unknowns, blanks, "—" or "not available" | **0** |

Label spread across the 34: Toxic 4, Ineffective 4, Adjust Dosage 3,
"No PGx-guided adjustment identified" 23.

Before §4, codeine was Unknown on all seven. It is now answered on six, and the
seventh is withheld because PharmCAT returns `Indeterminate` for that
diplotype — not because anything was missing from the input.

## The ledger

| Sample / gene / drug | Unknown reason | Root cause | Fix | Fixed? |
|---|---|---|---|---|
| all 7 / CYP2C9 + VKORC1 / **warfarin** | Drug-level abstention: "No validated automated warfarin-dose implementation is provided" | **Category 4 — CPIC gives a dosing algorithm, not a per-genotype recommendation.** The algorithm needs ancestry and clinical inputs this application does not collect. Declared in `capabilities.json` as `explicit_abstention`, and in `demo/ACCEPTANCE.md` §2 F2 before any run | None available from input. The CYP2C9, VKORC1 and CYP4F2 calls are shown beside the abstention, and all three were assessed on every sample | **Deliberate** — correct output |
| all 7 / CYP2D6 / **codeine** | "CYP2D6 copy-number and structural variation is not called from the uploaded VCF" | **Category 4 / declared negative control.** CYP2D6 star alleles depend on copy number and CYP2D7 hybrids; no VCF content establishes them. Coverage reports CYP2D6 at 2.5–9.6% and `not_readable_from_vcf` | §4, now applied: an optional CYP2D6 diplotype supplied beside the file. **6 of 7 now return a real label when one is supplied**; the VCF alone still declines | **Fixed** without touching the decline — see §4 below |

That is the whole ledger for the showcase set. There are no rows in the three
categories acceptance criterion L3 requires to be empty:

- **Category 1, position missing from the source file** — zero. All seven files
  carry an explicit, PASS, observed genotype at 327 of 327 required positions
  across the eight VCF-readable genes. The builder refuses to write a file that
  does not.
- **Category 5, missing explanation entry** — zero. Every rendered cell drew a
  pre-generated, provenance-verified explanation; the store was not touched and
  its hash is unchanged.
- **Category 6, client rendering gap** — zero enum or reason strings outside the
  contract. Every Unknown carries a populated human-readable reason, and both
  are existing declared states rather than new ones.

## What was found on the way, and kept out of the showcase

These are real Unknowns from real samples. They are recorded because they are
the interesting part of the step, not failures to be hidden.

### A. Ambiguous DPYD diplotypes — kept as a deliberate exhibit

| Sample | Cell | What the application shows |
|---|---|---|
| NA10847 (CEU) | fluorouracil | `Undetermined (2 equally likely)`, both candidates listed, phenotype not asserted → Unknown |
| NA19236 (YRI) | fluorouracil | same |
| HG03911 (BEB) | fluorouracil | same |
| HG01253 (CLM), NA19028 (LWK) | fluorouracil | `Undetermined (3 equally likely)` |

**Category 2 — real biology, not a defect.** Each carries two heterozygous DPYD
variants. In cis they give one activity score, in trans another, and the two are
different clinical answers. The source gVCF carries **no `PS` phase-set field
and an unphased `0/1`** at these positions, so the caller never resolved them.
PharmCAT returns the arrangements as equally likely, the phenotype is withheld,
and the phenotype→label invariant returns Unknown rather than naming one of
several co-equal genotypes.

Per the brief, these stay out of the main flow. **NA10847 is kept as the
ambiguity exhibit** (`demo/samples/ambiguity-exhibit/`): it still returns a real
simvastatin **Toxic**, and its fluorouracil cell is the talking point. It is
also the one sample in the set with GeT-RM consensus truth, which agrees with
the SLCO1B1 call the pipeline made.

### B. Samples the source could not supply at all

**28 of 45 fetched samples could not produce a conforming input.** Twenty-seven
failed at a single SLCO1B1 position, `chr12:21222355` (rs71581941), which
DRAGEN v4.4.7 marks `LowGQ` (genotype quality 0) or leaves as a no-call. Three
failed at NUDT15 `chr13:48037782`, where the source writes an indel against a
different anchor base than PharmCAT's row uses.

**Category 1 in form, but the fix is not ours to make.** The position is
present; the caller declined to call it confidently, and that flag is carried
through rather than erased. Writing it as PASS would manufacture a simvastatin
recommendation from a position the caller itself would not stand behind.

Consequences worth stating plainly:

- Every one of the eight NUDT15 poor-metabolisers in the entire 3,202-sample
  reanalysis fails this check, so **an azathioprine Toxic driven by NUDT15
  cannot be shown from this source.** The two azathioprine Toxic cells in the
  showcase are driven by TPMT instead.
- DPYD poor metaboliser has exactly **one** candidate in all 3,202 samples,
  HG02684 — which does conform, and is the showcase's fluorouracil Toxic.

The principled fix for the NUDT15 anchor cases is `bcftools norm` against a
GRCh38 FASTA, which re-anchors indels by computation rather than by guessing.
It needs a 3 GB reference download and is not done here; it is the obvious next
step if more samples are needed.

## The check that makes these labels mean something

Criterion L5: the labels must come from the input and from nothing else. For
every showcase sample, the homozygous-reference rows were removed from the
file — same genotypes, same pipeline, only the input shape changed — and the
file was re-analysed.

| Sample | Complete coverage | Same genotypes, hom-ref rows removed |
|---|---|---|
| HG00525 | Ineffective, Toxic, Safe, Safe | Unknown ×4 |
| HG01502 | Ineffective, Safe, Toxic, Safe | Unknown ×4 |
| HG02661 | Safe, Safe, Safe, Safe | Unknown ×4 |
| HG02684 | Safe, Safe, Safe, Toxic | Unknown ×4 |
| HG03097 | Safe, Safe, Toxic, Safe | Unknown ×4 |
| NA20863 | Safe, Safe, Adjust Dosage, Safe | Unknown ×4 |
| NA21109 | Ineffective, Safe, Adjust Dosage, Adjust Dosage | Unknown ×4 |

**All 28 confident labels revert to Unknown.** The movement from Unknown to a
confident label is explained entirely by better input, and it is not
reproducible by weakening a check — because no check was weakened. The seventeen
protected files verify against `demo/protected_files.sha256` unchanged.

## §4 — codeine, answered without giving up the decline

The brief's route, taken as written: PharmCAT's outside-call mechanism, which
Phase 9 B10 already built. The CYP2D6 diplotype is supplied **beside** the VCF,
never inside it, and is labelled as supplied everywhere it appears.

Source: the same per-sample prefix, object `<ID>.targeted.json`, which carries
DRAGEN's targeted CYP2D6 caller output — a diplotype, a filter, a genotype
quality and a **total copy number**. Copy number is exactly what a VCF cannot
express and the reason this door exists.

### Result: 6 of 7 codeine cells now carry a real CPIC label

| Sample | CYP2D6 supplied | VCF alone | With the supplied call |
|---|---|---|---|
| HG02684 | `*1/*41` (CN 4) | Unknown | Safe — NM, activity score 1.25 |
| HG00525 | `*10+*36x2/*49` (CN 6) | Unknown | **Unknown** — see below |
| NA21109 | `*2/*2` (CN 4) | Unknown | Safe — NM, 2.0 |
| HG01502 | `*2/*4` (CN 4) | Unknown | Safe — IM, 1.0 |
| HG03097 | `*17/*2` (CN 4) | Unknown | Safe — NM, 1.5 |
| NA20863 | `*4/*5` (CN 3) | Unknown | **Ineffective** — PM, 0.0 |
| HG02661 | `*1/*41` (CN 4) | Unknown | Safe — NM, 1.25 |

NA20863 is the one worth showing: two no-function alleles, activity score 0.0,
poor metaboliser. Codeine is a prodrug this person cannot activate, so the
label is Ineffective — a real clinical finding on the most intuitive drug in
the panel, from a real public genome.

**HG00525 stays Unknown, correctly.** Its `*10+*36x2/*49` is a tandem with a
copy number, and PharmCAT returns `Indeterminate` for it — no CPIC phenotype
assignment exists. The phenotype→label invariant therefore withholds, and the
response says so in those words. This is category 3 in the brief's
classification: PharmCAT withheld the classification, so the application does
too, even though a diplotype is in hand. Nothing here is a code defect.

### The negative control, re-proved on the one case that could embarrass it

NA12273 is the project's standing CYP2D6 example: GeT-RM records it as `*1/*1`,
and DRAGEN independently calls it `*1/*1` too, so a right answer is available
and tempting.

| | |
|---|---|
| `demo_na12273_1000g.vcf` alone | **Unknown** — gene `Unknown`, `supplied_by` null |
| the same file + `*1/*1` from DRAGEN | Safe — NM, 2.0, `supplied_by: DRAGEN` |
| a later request with no call | **Unknown** again — nothing leaked between requests |

Defence in depth, measured rather than asserted: the shipped showcase files
carry **2.5% to 9.6%** of CYP2D6's 157 required positions, because DRAGEN's
targeted caller marks most of them with its own filters and those filters are
carried through. So even with the explicit CYP2D6 decline deleted, the coverage
gate alone still refuses every one of these files. Two independent layers, and
a sabotage run confirms the test catches removal of the first.

### One invariant file changed, deliberately, and only this much

`demo/protected_files.sha256` is the steps 1–4 record and is left as it was;
`backend/app/outside_calls.py` now reports `FAILED` against it, which is the
intended, documented exception:

```
old  06fd515e6b3bbe5a7abc53961bf6c6b040f496430c523a3546cf3242d792f204
new  8b6af05703bfde0d73ce6c3e719796fecda6006c2e82dd2f7a98f9432cd73529
```

The change is one entry in the accepted-caller list, from four names to five,
plus the comment explaining it. The grammar, the pinned gene, the 80-character
cap, the refusal of newlines and tabs, and the decline of CYP2D6 from a VCF are
all untouched — `git diff` is 20 lines, 14 of them comment.

The alternative was to pass DRAGEN's call under one of the four existing names.
That would have left the manifest clean and put a false statement in the
provenance line that every view of the result carries, which is the kind of
trade this project exists to refuse. The other 16 protected files still verify
`OK`.

### The consequence, and the one decision it leaves

`backend/app/outside_calls.py` and `app/lib/widgets/outside_call_field.dart` are
both in the 106-file scientific core that `backend/app/data/compatible_bundle.json`
hashes, so changing them invalidates the recorded bundle. Four tests now fail,
and they are **correct to fail**: they say the recorded evaluation no longer
provably describes the running code.

Whether that matters scientifically was measured rather than argued. The
external benchmark was re-run in an isolated copy of the working tree —
`prepare`, `fetch --resume`, `evaluate --resume`, 208 individuals, reusing all
208 cached PharmCAT reports, no new caller executions, 41 seconds:

> **`external_benchmark_results.json` is identical, field for field, apart from
> timestamps and self-referential hashes.** Cohort 208 → 208, truth rows
> 1456 → 1456, every per-gene Layer A and Layer B record unchanged.

That is what should be expected and is now shown: the benchmark supplies no
outside calls, so `CALLERS` is never read on that path, and a name added to it
cannot move a number.

So this is an identity change, not a result change — the case the repository
already has vocabulary for in `scripts/application_hash_migration.json` ("a
hash-policy identity migration for unchanged intended application bytes").
Re-recording it is a 44-second, precedented procedure; the last one was done on
2026-11-07 for finding F-20, which changed far more consequential code.

### Re-recorded, on the owner's instruction, 2026-11-12

The rebind was run, following the procedure the 2026-11-07 F-20 re-bind used
and with a receipt for every stage. New package:
`test-data/benchmark/current-candidate-2026-11-12-phase10s4/`, evaluation id
`pharmaguard-external-current-candidate-2026-11-12-phase10s4`. The
2026-11-07-f20 package and the historical benchmark are left byte-identical.

| Stage | Result |
|---|---|
| Isolated copy of the working tree | 2,537 tracked files; core hash in copy equals repo |
| Cached PharmCAT reports verified and reused | 208 of 208 |
| New PharmCAT caller executions | **0** |
| Application re-projection | 208 individuals, 1,456 sample-gene rows rescored |
| F4 read-backed positive controls | 2 of 2 passed, 18 of 18 checks |
| Scored metrics vs 2026-11-07-f20 | **byte-identical** |
| `discrepancies.tsv`, `exclusions.tsv` vs f20 | **byte-identical** |
| Eligibility rows differing vs f20 | 1,456 — `vcf_sha256` only, explained by the path-bearing bcftools header |
| Eligibility changes declared by this rebind | **none** |

Scientific core: `d4b90eaa…` → `fc0074dc…`. The bundle's own verifier reports
`compatible scientific bundle: PASS`, the backend suite is **1269 passed, 0
failed**, the client suite is **496 passed**, and
`scripts/release_status.py --run-required` now reports:

```
state                  ready
required checks        True
artifact hashes match  True
```

(The outstanding content-review items are pre-existing and, with the
explanation mode `deterministic_template_only`, block only if stored prose is
served.)

One client test needed updating with the change rather than because of a
defect: `app/test/outside_call_test.dart` pins the caller list exactly, so that
a name added on one side and not the other cannot slip through. It now pins
five names and says why.

### One wording inconsistency left open, deliberately

`capabilities.json` describes codeine's limitation as guidance produced "only
from a CYP2D6 diplotype supplied by a dedicated caller (Cyrius, BCyrius, Aldy
or StellarPGx)". The API now accepts a fifth. That string is also in the
scientific core and appears in 208 discrepancy-detail rows and 208
eligibility-reason rows, so changing it is a *declared* eligibility change
needing its own rebind — the mechanism supports it, and Phase 9 B5 and B10 both
used it. It belongs with the other user-facing wording in §5 rather than
bundled into this one, where it would obscure the fact that this rebind changed
no result at all.

## Local and deployed agree

All seven samples were run through both. Comparing the full response bodies
field by field, ignoring `processing_time_ms`, the only differing field in any
sample is the response `timestamp`. Genotypes, phenotypes, labels, confidence,
severity, CPIC recommendation text, warnings and the per-gene coverage census
are identical.
