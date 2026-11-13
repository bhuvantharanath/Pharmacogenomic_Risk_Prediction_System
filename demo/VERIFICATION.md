# Phase 10 §6 — verified as if it were being reviewed

Run 2026-11-12 against the working tree after §1–§5. Every number below was
produced by a command on that date; where a check could not be run here, that
is said rather than skipped quietly.

## 1. The two regression sets are unchanged

Both were re-run in full against the current code and compared to their
recorded artifacts, ignoring only the generation timestamp.

### PharmCAT's 74 adversarial VCFs

`python scripts/validate_testvcfs.py` — 74 of 74 compared in 87 s.

| | Recorded 2026-07-26 | Now |
|---|---|---|
| Files compared | 74 / 74 | 74 / 74 |
| Field comparisons | 148 | 148 |
| Mismatches | **0** | **0** |
| Match rate | 100.0000% | 100.0000% |
| Per gene | CYP2C19 27, CYP2C9 9, DPYD 7, NUDT15 3, SLCO1B1 17, TPMT 11 | identical |

`reports/testvcf_fidelity.json` is **identical apart from the timestamp**.

### The 400-sample 1000 Genomes cohort

`python scripts/validate_integration.py --resume` — 400 of 400 samples, reusing
the cached PharmCAT reports.

| | Recorded 2026-07-25 | Now |
|---|---|---|
| Samples with a report | 400 / 400 | 400 / 400 |
| (sample, gene) compared | 2,800 | 2,800 |
| Field comparisons | 5,600 | 5,600 |
| Mismatches | **0** | **0** |
| Usable phenotype | 1,987 of 2,400 (82.79%) | identical |
| Reason classes | structural 400, ambiguous 308, unclassifiable 103, no-call 2 | identical |
| CYP2D6 call rate | 0 / 400 (negative control) | 0 / 400 |

`reports/integration_fidelity.json` is **identical apart from the timestamp and
the elapsed-time field**.

Neither set moved. Nothing in this phase touched the paths they exercise, and
these runs are what establishes that rather than asserting it.

## 2. Movement toward confident labels came from input, not from a weakened check

The brief's test: any Unknown that became a confident label must be impossible
to produce by weakening a check, proved by reverting the data change and
showing the Unknowns return.

For every showcase sample, the homozygous-reference rows were stripped from the
file — same genotypes, same pipeline, only the shape of the input changed — and
the file was re-analysed. **All 28 labels returned to Unknown** (recorded in
`demo/UNKNOWN_LEDGER.md`). The non-reference rows in the stripped file are
byte-identical to those in the full one, so the genotype is demonstrably the
same.

Independently: 15 of the 17 files listed in `demo/protected_files.sha256` —
every gate, the label engine and mapping, the evidence cross-check, the PharmCAT
runner, VCF validation, the REF check, the position requirements and the
explanation store — are byte-identical to where they stood at `fdb27cb`. The
two that moved are the CYP2D6 caller list and the sentence that names it,
neither of which can admit a gene.

## 3. Sabotage sweep: every named guard is load-bearing

Each guard was reverted in the source, the test that exists to catch that
reversion was run, and the test was required to **fail**. The file was then
restored and the test required to pass again, with the file byte-identical.
A guard whose test survives its own removal is not a guard; the restored leg
matters as much, because a test that fails either way would look like a catch.

| Guard | Reverted to | Test | Caught |
|---|---|---|---|
| Coverage gate (percentage) | `if False:` in `GeneCoverage.sufficient` | `test_coverage_gate.py` | **yes** |
| DPYD decision-critical identity | identity check disabled | `test_decision_critical_positions.py` | **yes** |
| Phenotype → label invariant | `check_phenotype_label` returns `None` | `test_phenotype_label_invariant.py`, `test_unasserted_phenotype_invariant.py` | **yes** |
| sourceDiplotypes | read `recommendationDiplotypes` instead | `test_diplotype_source.py` | **yes** |
| CYP2D6 decline from a VCF | `NOT_READABLE_FROM_VCF = {}` | `test_showcase_inputs.py` | **yes** |

5 of 5 caught; all five files restored byte-identical, and all 17 protected
files verify against the end-of-phase baseline afterwards.

Two more were swept during the phase and are recorded in the ledger: the
conversion tool's refusal to emit a non-conforming file, and its refusal to
infer an uncovered position as reference. Both are load-bearing.

## 4. Viewport, text scale and keyboard

**Viewport and text scale were already covered**, and are now exercised against
a current payload. `app/test/accessibility_test.dart` AC5 renders the results
screen at **1.0×, 1.5× and 2.0× text scale**, at **360×800 (phone)** and
**1440×900 (projector)** — six combinations — opening each disclosure row and
failing on any overflow. Its fixture is `S6_multidrug`, which this phase
refreshed from 7 genes to 9, so the matrix now runs against the payload the
backend actually produces.

**Keyboard-only was not covered, and now is.** The existing accessibility tests
check contrast, unique control names, named message nodes and non-colour risk
encoding — none of them pressed a key. `app/test/keyboard_only_test.dart` adds
three:

1. Tab must stop on a disclosure row, not merely somewhere.
2. A disclosure row reached by Tab must open with Enter.
3. The disclosure control must still paint a visible focus state.

The first version of these passed while the disclosure rows were made
**unfocusable**, because Tab still stopped on 14 other controls — export and
print buttons. That is recorded because it is the point: the tests were
rewritten to walk up from the focused element and require a `DisclosureRow`
ancestor, and only then did the sabotage fail them, with the diagnostic
"Tab stopped on 14 control(s) but never on a disclosure row". Dropping the
`focusColor` fails the third.

This matters for a keyboard user specifically: everything of substance on the
results screen — the CPIC recommendation, the mechanism, the coverage census,
the reason a gene was declined — sits behind a disclosure row. If a keyboard
cannot open them, the screen is five collapsed headings.

## 5. Local and deployed agree, with one fully-explained difference

All seven showcase samples were run through the local pipeline and through
`pharmaguard-api-baml.onrender.com`, six drugs each, and the full response
bodies compared field by field ignoring `processing_time_ms` and `timestamp`.

**14 differing fields across 7 samples — two per sample, all one cause.**
Local reports codeine's limitation as "(Cyrius, BCyrius, Aldy, StellarPGx or
DRAGEN)"; the deployed instance reports "(Cyrius, BCyrius, Aldy or
StellarPGx)". The deployed commit is `5ff0022`, which predates §4.

Every genotype, phenotype, risk label, confidence, severity, CPIC
recommendation text, warning and per-gene coverage figure is **identical**.

### The supplied-CYP2D6 path is local-only until a deploy

Running the same samples with `cyp2d6_caller=DRAGEN` against the live instance
returns **HTTP 400** on all seven:

```
{"detail":"The CYP2D6 caller must be one of: Cyrius, BCyrius, Aldy, StellarPGx.",
 "error_code":"OUTSIDE_CALL_INVALID"}
```

That is the deployed code refusing a caller it has never heard of, which is
correct behaviour for the code that is running. It means the §4 codeine result
— including NA20863's **Ineffective** — exists only locally at the moment. A
reviewer using the public URL today sees codeine Unknown on every sample.

## 6. Timing, measured today

### The offline path, this machine

`scripts/run_demo.py`, run twice back to back:

| | Run 1 | Run 2 |
|---|---:|---:|
| Warm-up request | 1,136 ms | 1,146 ms |
| Six scenarios, total | **7,121 ms** | **7,152 ms** |
| Wall clock | 8.31 s | 8.35 s |
| Slowest single scenario | 1,248 ms | 1,212 ms |

Six for six both times, every scenario returning its declared label.

### The live path, Render free tier

| | Measured 2026-11-12 |
|---|---|
| Cold `GET /health` after idle | **32.4 s** |
| Warm `POST /analyze`, showcase file, 6 drugs | **62.2 s, 63.5 s, 62.8 s** |

**The warm figure has moved and the project's notes are now behind it.**
`infra/DEPLOY_NOTES.md` records a warm p50 of ~51 s; today it is consistently
62–63 s. That is not caused by the new samples or by asking for more drugs —
all four combinations were measured and land in the same place:

| Input | Drugs | Time |
|---|---|---|
| showcase `HG02684.vcf` (480 rows) | 6 | 62.2 s |
| old `demo_confident.vcf` (463 rows) | 6 | 62.7 s |
| showcase `HG02684.vcf` | 1 | 62.7 s |
| old `demo_confident.vcf` | 1 | 63.1 s |

So it is the instance, not the input. The cause was not investigated further;
what matters for the runbook is that **a reviewer should be told ~60 seconds,
not ~50**.

The client's promises are still longer than reality, which is the direction
that matters: `kWakeupBudget` and the analyze receive timeout are both 180 s,
comfortably above the 63 s observed. One piece of copy is marginal —
`kColdStartExpectation` says "usually 20–30 seconds, occasionally" longer, and
today's cold `/health` took 32.4 s. It is inside the "occasionally" clause
rather than wrong, but it is at the edge.

## 6. What could not be verified here

- **The built web client was not driven in a browser.** `flutter build web
  --release` succeeds and the five sample assets are present in the build, but
  local static servers on ports 3000 and 8080 were unreachable from this
  sandbox while port 8000 worked. The picker is covered by widget and
  accessibility tests, and every bundled file was run through the real API.
  Nobody has clicked it in a browser on this machine.
- **The timed dry-runs were done on this machine, not on the presentation
  hardware and network.** The brief asks for the real venue setup; this is the
  development laptop against Render's free tier.
