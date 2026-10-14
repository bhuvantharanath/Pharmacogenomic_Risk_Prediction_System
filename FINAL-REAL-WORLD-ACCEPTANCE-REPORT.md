# 1. Executive Verdict

**FAIL / NOT READY for a bounded research release.**

Fresh execution demonstrated conservative handling of the selected public genomic inputs: oversized files were rejected, accepted but incomplete files returned Unknown, missing partner evidence did not produce azathioprine reassurance, and unsupported drugs stayed outside the guidance boundary. No unjustified reassuring conclusion was observed in this run.

The release nevertheless fails its own mandatory gate. Nineteen claim decisions remain outstanding, 36 recorded decisions are automated rather than human, and all 20 stored explanation entries remain unapproved. Runtime fallback prevented those entries from being served in the tested cases, but that does not make the release prerequisites complete.

There is also a reproducibility defect: the scientific application hash includes an ignored macOS `.DS_Store` file. Removing only that file in an isolated copy makes bundle verification fail. The CYP2C19 definition-delta manifest additionally says an update is included when the pinned definition still predates it.

**The main validation limitation is consequential:** none of the nine accepted primary real-file presentations met the application's evidence contract. This is a successful negative-input test, not a successful real-data guidance benchmark. Correct normal and actionable guidance from a fully covered real sample remains **INCONCLUSIVE**. Synthetic positive controls passed and are reported separately.

Execution: 26 September 2026; final evidence review: 27 September 2026, Asia/Kolkata. All results concern the recorded local working tree. No deployment was exercised.

# 2. Release Candidate Identity

| Item | Recorded value |
|---|---|
| Branch | `main` |
| HEAD | `1dc7557da49f38e831b382545044b00a481507b6` |
| Working tree | Existing implementation changes, including untracked implementation files; not a clean commit |
| Python | 3.11.14; CI specifies 3.12, which was not independently rerun here |
| Backend dependencies | Exact installed versions in [dependencies.txt](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/dependencies.txt>) |
| Flutter / Dart | 3.38.9 / 3.10.8 |
| Java | OpenJDK 25.0.1, Homebrew, macOS |
| bcftools / htslib | 1.24 |
| PharmCAT engine / data | 3.4.0 / `2026-07-13-11-40` |
| Reference | GRCh38; embedded definitions identify GRCh38.p14 |
| Capability registry | Version 1; four guidance pathways plus two explicit-abstention entries |
| Scientific bundle | `pharmaguard-scientific-baseline-2026-09-24` |
| Explanation mode | Explicitly `static` for execution; default and deployment configuration also static |
| Explanation store generation timestamp | `2026-07-24T09:53:53.175011+00:00` |
| Clinical expert review | `NOT_OBTAINED` |

Important SHA-256 identities:

| Artifact | SHA-256 |
|---|---|
| PharmCAT JAR | `9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741` |
| PharmCAT positions | `01a28fe31675c9e8a8b18bcab4afb82a62abdfea6606856aeca0e0378e7d6b58` |
| Position requirements | `d0996c09885b75d46fea45260d4c048ad3cd6a2ebf473294de85863c798f3ad3` |
| Label mapping | `5ade626cf83d410e620ac5fb9ba648854b152ef0e53abfe051c115c665514bc6` |
| Explanation store | `35cb17a98fd2a885da9f14264da647b9923c75481bc7e02eff9c433fea2c59e8` |
| Capability registry | `287a319b8ca1fdac9e765d7b6ec7de55ea8ee87cd3d142700be0b7601d2c1704` |
| Compatible-bundle manifest | `c55fc4ac6994d534f3a4d84ed9053aef63ab029d5954c776dd4f854844dd6c69` |
| Application core recorded by benchmark | `05ea05686782c0644c39b71fa728959d8a2efce0aebc51cae3172912d0206d5a` |
| Candidate/tested release artifact | `4c59a630a8b1640e5a519c23c581c7345a36afe904c5995d4801539c1595e8a4` |

The [initial status](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/initial-git-status.txt>), [initial diff](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/initial-diff.patch>), and [412-file hash inventory](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/initial-file-hashes.json>) identify the dirty candidate more precisely than HEAD alone. [Final verification](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/final-freeze-verification.json>) found **zero changes to those 412 files**. The owner added `Final-Scientific-Audit.md` during the task; other additions belong to the separate audit-output directory. No implementation changes were made by this audit.

The original scientific audit was initially absent. A provisional checklist was made before baseline testing; the owner then supplied the audit, and the [audit-derived checklist](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/acceptance-checklist-before-real-testing.md>) was frozen before any real-data application results. This sequencing limitation is disclosed rather than backdated.

Baseline verification in an isolated copy:

| Check | Result | Interpretation |
|---|---|---|
| Complete backend suite | **874 passed, 9 skipped, 0 failed, 0 errors**, 883 collected | [JUnit](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/backend-complete-junit.xml>), [log](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/backend-complete.log>); no expected failures |
| Flutter analyzer | PASS, no issues | [Log](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/flutter-analyze.log>) |
| Existing Flutter suite | **198 passed** | [Log](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/flutter-tests.log>) |
| Exact-candidate required checks | All six passed | Bundle, backend, provenance, mapping, analyzer, Flutter tests; final release status still NOT READY |
| CPIC label validator | 105 comparisons; 13 divergences, all in the declared accepted baseline | Accepted divergences are not counted as independent biological matches |
| Fresh PharmCAT test-VCF fidelity | 74 files, 148 field comparisons, zero parser mismatches | [Log](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/scientific-testvcfs.log>); upstream fixtures, not independent real truth |
| Fresh real-input direct PharmCAT | Nine executions, all exit 0 | Separate from the actual API runs |

The nine backend skips were three demo tests requiring localhost:8000, one obsolete README-count condition, one absent glossary-decision condition, one absent `.env` test, and three PATH-based wrapper tests. The real JAR was exercised separately; the skipped tests remain skips. The initial incomplete audit copy produced two failures and 13 skips because historical logs and an ignored Finder file had not been copied. Those results remain in [backend-tests.log](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/backend-tests.log>). Restoring the existing bytes in the temporary copy resolved the suite failures; the Finder-file dependency was retained as a product reproducibility finding. No production test or expectation was changed.

# 3. Public Real-World Data Used

The cohort was frozen before application output inspection: **all three individuals in the official PharmCAT tutorial set**, with corresponding 1000 Genomes data. No selected individual was removed after observing results. These are three people, not nine independent samples.

| Individual | Source population label | Genomic source / technology | Files tested |
|---|---|---|---|
| NA18526 | CHB | Public 1000 Genomes/NYGC Illumina WGS, nominal 30× per tutorial source, GRCh38 | Original bgzip, official preprocessed VCF, exact-row required-site subset, 2022 cohort sample extraction |
| NA18565 | CHB | Same source class | Same four presentations |
| NA18861 | YRI | Same source class | Same four presentations |

The tutorial was pinned to commit `30253e35773aeaf27345dee5ab3d8d01c49f0a46`. The [official tutorial](https://github.com/PharmGKB/PharmCAT-tutorial) and [1000 Genomes 2022 release directory](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/working/20220422_3202_phased_SNV_INDEL_SV/) were checked during this audit. Six tutorial VCFs and the CDC truth workbook were freshly downloaded. The 2022 paired inputs were freshly extracted from the existing, hashed local public cohort slice; that large cohort file was **not freshly downloaded**.

Exact per-file paths, source URLs, sizes, checksums and access times are in the [data inventory](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/DATA-INVENTORY.md>), [acquisition manifest](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/acquisition.json>), [preparation record](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/input-preparation.json>), and [derived-input manifest](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/derived-inputs.json>). Originals are retained unchanged. The cohort slice SHA-256 is `f54a547758e17c53bfa338f67617d18b587396c90e7bc71310290f74d9df95ba`.

Additional authoritative discovery included [CDC GeT-RM resources](https://www.cdc.gov/lab-quality/php/get-rm/reference-materials.html), [ENA PRJEB19931](https://www.ebi.ac.uk/ena/browser/view/PRJEB19931), the [2026 PGx-caller benchmark](https://pubmed.ncbi.nlm.nih.gov/42312650/) and its [companion repository](https://github.com/marcglf/benchmark-star-allele-callers), and public GIAB/PacBio variant resources. These were leads, not additional tested individuals. Compatible full-site real data were not successfully obtained from those leads in this run. Raw FASTQ/BAM resources were not converted through a new calling pipeline; no alternative build was relabeled or reference observations invented.

Class coverage: B (independent truth), C (actionable SLCO1B1 truth), D (reference truth), and E (incomplete/variant-only input) were represented. **Class A, a real input satisfying the full evidence contract, was not established.**

# 4. Truth Sources

Independent truth came from the [CDC consolidated PGx/HLA workbook, 22 January 2025 V4](https://www.cdc.gov/lab-quality/media/files/2025/08/Consolidated_PGx-HLA_table_1-22-25-V4.xlsx), freshly downloaded 26 September 2026. Its SHA-256 is `c66174befa7a7bbb6cfaf174cc500a269565407807467204bd7bc6eaae3be109`. The original workbook and [frozen extracted truth](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/independent-truth-frozen.json>) are preserved. Truth was not derived from this application or from its PharmCAT calls.

| Sample | CYP2C19 | CYP2C9 | SLCO1B1 | TPMT | DPYD | CYP2D6 | NUDT15 |
|---|---|---|---|---|---|---|---|
| NA18526 | `*1/*1` | `*1/*1` | `*1/*15` | `*1/*1` | `*1/*1` | `*1/*36x2+*10` | Unavailable |
| NA18565 | `*1/*1` | `*1/*1` | `*1/*1` | `*1/*1` | `*1/*1` | `*10/*36x2` | Unavailable |
| NA18861 | `*1/*1` | `*1/*1` | `*1/*14` | `*1/*1` | `*1/*9` | `*5/*29` | Unavailable |

Independent phenotype truth was not supplied in the extracted table. No application phenotype was used to fill that gap. The [CPIC statin guideline](https://pmc.ncbi.nlm.nih.gov/articles/PMC9035072/) supports classifying NA18526's SLCO1B1 `*1/*15` as a decreased-function, potentially actionable simvastatin state for the descriptive false-reassurance check. That contextual assessment was not used to manufacture a post-hoc phenotype-concordance denominator.

Equivalence rules were preregistered: exact unordered diplotype strings with whitespace normalization only; suballele/core equivalence reported separately if justified; candidate containment distinct from an asserted exact call; no functional equivalence without independent supporting evidence. No rule was changed to turn a mismatch into a match.

# 5. Input Preparation

The official preprocessed files were used unchanged as source-provided inputs. Our raw-file subsets retained only original lines at the frozen required coordinates. A final independent line-preservation check found **216 of 216 retained rows verbatim in each source file**: [row-preservation-check.json](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/row-preservation-check.json>). No absent site was filled with `0/0`.

Single-sample extraction used bcftools 1.24:

```sh
bcftools view --no-version -s NA18526 -Ov -o NA18526.1000G2022.vcf locked_cohort.vcf.gz
bgzip -c NA18526.1000G2022.vcf > NA18526.1000G2022.vcf.gz
```

The same commands were applied to NA18565 and NA18861; exact absolute argument arrays and outputs are retained in [input-preparation.json](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/input-preparation.json>). bcftools reported the source `AC` header-number warning; it did not fail extraction. Compression changed the file representation only, not genotype calls. No liftover, truth-driven genotype editing, new variant caller, or isolated allele-definition patch was performed.

Perturbations were made in separate derived copies. [run_acceptance.py](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/run_acceptance.py>) records exactly how records, headers, sample columns, FILTER and FORMAT fields were altered. These adversarial controls are not biological samples or prevalence estimates. Their hashes and reasons were frozen in [execution-cases-frozen.json](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/execution-cases-frozen.json>) before execution.

Reproduction commands and environment boundaries are provided in [REPRODUCTION.md](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/REPRODUCTION.md>). Replay should write a new output directory, preserving the frozen evidence from this run.

# 6. Real VCF Compatibility

| Presentation | Number | Upload / readiness / analysis | Reason |
|---|---:|---|---|
| Original tutorial bgzip | 3 | HTTP 413 at both endpoints | Each approximately 11.18–11.21 MB compressed, above the 5 MiB upload cap |
| Official preprocessed VCF | 3 | HTTP 200; no answerable drug; all final labels Unknown | Insufficient explicit observed positions |
| Exact-row required-site subset | 3 | HTTP 200; no answerable drug; all final labels Unknown | Missing required positions and critical evidence |
| Fresh 2022 single-sample extraction, bgzip | 3 | HTTP 200; no answerable drug; all final labels Unknown | Variant-oriented cohort representation remains incomplete |

All accepted primary inputs completed through the actual application, including PharmCAT. HTTP 200 indicates successful processing, not successful genomic inference.

For representative NA18526, required-position presence was:

| Gene | Required | Official preprocessed | Raw required-site subset | 2022 extraction |
|---|---:|---:|---:|---:|
| CYP2C19 | 35 | 19 | 19 | 16 |
| CYP2C9 | 88 | 24 | 28 | 17 |
| SLCO1B1 | 35 | 17 | 23 | 20 |
| TPMT | 45 | 12 | 12 | 9 |
| NUDT15 | 20 | 5 | 6 | 5 |
| DPYD | 83 | 46 | 46 | 31 |
| CYP2D6 | 157 | 65 | 82 | 67 |

TPMT/NUDT15 have nominal 80% thresholds but require all critical positions, which currently span all 45/20 positions. DPYD's 20% threshold also requires all 28 critical positions; the raw subset represents only 12 of them. Thus DPYD's 55.4% overall positional presence does not qualify it for guidance. CYP2D6 remains unsupported regardless of positional coverage. Source phasing and genotype metadata were retained; their presence does not establish missing-site callability.

# 7. End-to-End Real-Data Results

Each case ran `/coverage` before `/analyze`. The analysis request included clopidogrel, fluorouracil, azathioprine, simvastatin, warfarin, codeine, capecitabine, omeprazole, atorvastatin and mercaptopurine.

| Sample | Original file | Three accepted presentations | Final guidance-capable drug results | Direct PharmCAT |
|---|---|---|---|---|
| NA18526 | 413, size limit | All completed, 0 eligible genes | Four Unknown in each presentation | All three exit 0 |
| NA18565 | 413, size limit | All completed, 0 eligible genes | Four Unknown in each presentation | All three exit 0 |
| NA18861 | 413, size limit | All completed, 0 eligible genes | Four Unknown in each presentation | All three exit 0 |

All six additional requested drugs also returned Unknown. There were zero preview/final eligibility anomalies in [readiness-parity.json](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/readiness-parity.json>). This includes the positive synthetic controls, so parity was not assessed only on an all-abstention set.

The primary real set produced 90 drug results across nine file presentations; all were Unknown. The 36 guidance-pathway results are repeated presentations of 12 individual × drug combinations. They must not be reported as 36 independent people or successful clinical decisions.

The [execution summary](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/execution-summary.json>), per-case [API directory](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/api>), and separate [PharmCAT reports](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/pharmcat>) preserve both intermediate and final outputs. Thirty-seven total case pairs comprised 12 primary real presentations, 12 real-derived evidence/FORMAT controls, five input-validation controls, three existing synthetic positives and five synthetic degradations.

# 8. Independent PGx Concordance

The [row-level comparison](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/truth-caller-parser-application.json>) separates independent truth, upstream reported diplotype, parsed diplotype/candidates, parsed phenotype, final application phenotype and drug label. The [classified interpretation](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/classified-comparisons.json>) adds attribution without rewriting the frozen truth or initial comparison output.

The following findings were the same across all three accepted presentation types:

| Gene | Independent truth vs reported PharmCAT primary call | Parser vs PharmCAT | Final application |
|---|---|---|---|
| CYP2C19 | 3/3 exact `*1/*1` | Preserved | Unknown; incomplete input |
| CYP2C9 | 3/3 exact `*1/*1` | Preserved | Unknown; warfarin scope also prohibits dosing |
| TPMT | 3/3 exact `*1/*1` | Preserved | Unknown; thiopurine partner evidence incomplete |
| SLCO1B1 | 2/3 exact; NA18861 truth `*1/*14`, call `*1/*43` | Preserved, including upstream warnings | Unknown; no disagreement escaped the evidence gate |
| DPYD | Legacy truth `*1/*1`, `*1/*1`, `*1/*9`; caller `Reference/Reference`, `Reference/Reference`, `c.85T>C (*9A) (heterozygous)` | Preserved | Unknown; nonidentical representation is not automatically biological error |
| NUDT15 | Truth unavailable; caller `*1/*3`, `*1/*1`, `*1/*1` | Preserved | Unknown; no independent concordance claim |
| CYP2D6 | Complex structural truth; caller `Unknown/Unknown` | Parser marks not attempted | Unknown; intended unsupported pathway |

All 54 parsed non-CYP2D6 reported diplotypes matched their upstream representation across the nine presentations. The remaining nine CYP2D6 rows were explicitly not attempted. This is parser fidelity, not biological accuracy.

No independent phenotype-concordance score is reported because that truth denominator was unavailable and the final app abstained throughout. SLCO1B1's primary exact match for NA18526 is also subject to an upstream phase warning: `*5/*37` cannot be ruled out without phased data. A primary reported match is not proof of fully resolved haplotype identity.

# 9. Drug-Level Results

| Drug | Required evidence / scope | Real-input result | Separate positive control |
|---|---|---|---|
| Clopidogrel | CYP2C19 | Unknown for all accepted primary real inputs | Normal: “No PGx-guided adjustment identified”; synthetic `*2/*2`: “Ineffective,” source indication retained |
| Fluorouracil | DPYD plus critical positions | Unknown, including files above the nominal percentage threshold | Normal qualified result; synthetic variant carrier: “Adjust Dosage” |
| Azathioprine | Both TPMT and NUDT15 | Unknown; both dependencies disclosed | Full synthetic normal: qualified result; either missing partner: Unknown |
| Simvastatin | SLCO1B1 | Unknown, including NA18526 with independently actionable truth | Full synthetic normal: qualified result |
| Warfarin | Explicit abstention | Unknown, no automated dose | Unknown even with complete synthetic CYP2C9 evidence |
| Codeine | CYP2D6 structural/CNV pathway unsupported | Unknown | Unknown even in the complete synthetic input |
| Other requested drugs | Outside registry | Unknown | Unknown with complete synthetic evidence too |

The clopidogrel positive control retained the CPIC ACS/PCI population qualifier and contraindication wording in its recommendation and warnings. That is a source-row fidelity observation, not a patient-specific indication assessment.

# 10. Evidence-Sufficiency Tests

The real derivatives used NA18526's raw required-site subset. Its baseline already failed the evidence gate. These tests establish no gain in certainty from degraded evidence, but **cannot establish a valid-real-result-to-abstention transition**.

| Real-derived change | Current result | Interpretation |
|---|---|---|
| Remove a required record | Readiness incomplete; final Unknown | PASS for tested monotonic abstention |
| Remove a critical record | Same | PASS, with incomplete-baseline limitation |
| Remove TPMT | Azathioprine Unknown | PASS |
| Remove NUDT15 | Azathioprine Unknown | PASS |
| Variant-only subset | All Unknown; limitations retained | PASS, no inferred reference normality |
| Partial `0/.` / complete no-call | Invalid evidence excluded; Unknown | PASS |
| Explicit `LowQual` FILTER | Failed evidence excluded; Unknown | PASS |
| Missing GT | Not counted as a valid genotype; Unknown | PASS |
| GT after DP (`DP:GT`) | Accepted; appropriate incomplete result | PASS |
| Missing quality metadata / FILTER `.` | Input accepted; selected record classified quality-not-established; Unknown here | Not evidence of assay quality |
| DP/GQ set to zero on a selected record | No new guidance; Unknown | No invented universal biological quality threshold |

Independent positive-to-negative transitions were exercised with existing **synthetic** complete evidence: removing either thiopurine partner, making one NUDT15 GT partial, applying failed FILTER, or deleting a critical NUDT15 record changed azathioprine to Unknown while preserving the three unaffected guidance pathways. All five passed. Real complete paired thiopurine evidence, independent NUDT15 truth, and actionable combined-gene state validation remain INCONCLUSIVE.

Fresh ingress controls: contradictory reference headers → 400 `CONFLICTING_REFERENCE_BUILD`; GRCh37 header control → 400 `UNSUPPORTED_REFERENCE_BUILD`; duplicated second sample → 400 `UNSUPPORTED_MULTISAMPLE`; truncated gzip → 400 `CORRUPT_GZIP`; valid gzip → 200 with the same abstention; three oversized real files → 413 `FILE_TOO_LARGE`. Both endpoints agreed.

# 11. Original Audit Counterexample Closure

“Before” below refers to the supplied scientific audit, not a reconstruction of old source. Evidence for “now” is in the named fresh case outputs, complete regression suite and gate records.

| # | Previous audit behavior | Current behavior | Status | Fresh evidence |
|---:|---|---|---|---|
| 1 | Missing NUDT15 still yielded azathioprine Safe/95% | Missing partner yields Unknown; unrelated complete pathways retained | PASS | `synthetic-missing-NUDT15`; real missing-NUDT15 |
| 2 | Missing TPMT yielded Unknown, exposing an asymmetric partner gate | Both directions now require complete partner evidence | PASS | `synthetic-missing-TPMT`; real missing-TPMT |
| 3 | Partial `0/.` counted as complete and yielded reassurance | Partial evidence excluded; azathioprine Unknown | PASS | `synthetic-partial`; real partial-GT |
| 4 | Explicit failed FILTER still counted toward reassuring guidance | Failed record cannot support eligibility | PASS | `synthetic-filter`; real failed-FILTER |
| 5 | Insufficient evidence could retain normal prose | Unknown and explicit incomplete-evidence explanation | PASS | Nine primary real inputs; variant-only |
| 6 | Contradictory build declarations accepted | Rejected at both endpoints | PASS | `real-conflicting-build` |
| 7 | Truncated gzip accepted after decoding | Rejected at both endpoints | PASS | `real-truncated` |
| 8 | Multisample accepted then caller/output handling failed | Rejected before interpretation | PASS | `real-two-sample` |
| 9 | Out-of-scope atorvastatin/phenytoin could receive guidance | Registry boundary enforced | PASS for tested boundary | 88-drug real sweep; complete synthetic out-of-scope controls |
| 10 | Fixed score displayed as percentage confidence | No displayed/exported percentage; API compatibility field explicitly deprecated | PASS for permitted deprecation | Flutter/API-schema tests; actual exports; legacy-field caveat in §15 |
| 11 | Broad unconditional Safe label/prose | Qualified PGx label or Unknown | PASS | Claim scan, rendered real/synthetic outputs, exports |
| 12 | Unapproved generated text could be served | Runtime uses deterministic fallback; required human approval still incomplete | **FAIL overall**; runtime fallback PASS | Template warnings; 0/20 approved entries; gate |
| 13 | Release status could be bypassed by independent deployment paths | Workflow depends on gate; deliberate mismatch fails local gate | PASS for local rejection / dependency inspection; live CI enforcement INCONCLUSIVE | Negative gate and unchanged workflow; no workflow triggered |
| 14 | Child survived cancellation | Real JVM canceled/reaped; no observed survivor or temporary residue | PASS locally | `operational-inprocess.json`; descendant lifecycle regression tests |
| 15 | Preview and final interpretation could disagree about eligibility | No unexplained mismatch in 30 accepted case pairs | PASS | `readiness-parity.json` |

This is not a blanket statement that all P0 work is complete. Item 12 still prevents closure, and no live deployment enforcement test was performed under the deployment freeze.

# 12. Capability-Scope Validation

The common registry contains six presentation entries: guidance for clopidogrel, fluorouracil, azathioprine and simvastatin, and explicit abstention for warfarin and codeine. The API, generated frontend capability data and registry tests agree in the tested candidate.

Direct PharmCAT output exposed **88 distinct CPIC drug names**. Every name was submitted through the actual API in bounded batches on NA18526; none produced a non-Unknown final result. The same result was obtained with configured Java memory limits. Those 88 include in-scope names, so they are not 88 unsupported drugs.

Because the real sweep used incomplete evidence, it alone cannot prove all possible out-of-scope inputs are gated. Full-evidence synthetic controls additionally kept capecitabine, omeprazole, atorvastatin and mercaptopurine Unknown, alongside codeine and warfarin. Complete registry regression tests passed. Evidence: [upstream names](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/upstream-cpic-drugs.json>), [actual sweep](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/upstream-scope-sweep.json>), and [synthetic complete API response](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/api/synthetic-normal_metabolizer_control.analyze.json>).

# 13. Uncertainty / Abstention

All primary accepted real inputs had zero evidence-eligible genes and zero answerable drugs. Final profiles were Unknown rather than asserted normal diplotypes. Relevant warnings about missing positions, source allele assignment, and phase were retained.

NA18526's upstream SLCO1B1 `*1/*15` primary call and alternative `*5/*37` warning remained visible in the response warnings, while final simvastatin guidance was withheld. CYP2D6's structural uncertainty never became a definite application genotype. This supports bounded preservation of uncertainty in incomplete real inputs. It does **not** demonstrate correct resolution of a complete, phase-sensitive real input.

Abstention has a cost: no useful real drug guidance was retained in this small selected cohort. The evidence gate must not be weakened merely to increase the answered fraction. Obtaining a suitable observed-reference/callability input is the missing validation step.

# 14. False-Reassurance Analysis

| Sample | Gene / drug | Independent truth | Evidence available | Application output | Reassuring? | Correct? | Classification |
|---|---|---|---|---|---|---|---|
| NA18526 | SLCO1B1 / simvastatin | `*1/*15`, decreased-function context from CPIC | 23/35 positions in raw subset; phase caveat | Unknown, incomplete-evidence warning | No | Correct abstention under contract; actionable guidance untested | T1 |
| NA18526 | CYP2C19 / clopidogrel | `*1/*1` | 19/35 | Unknown | No | Correct abstention; no assertion of normality | T1 |
| NA18565 | SLCO1B1 / simvastatin | `*1/*1` | Incomplete | Unknown | No | Correct abstention; normal guidance untested | T1 |
| All three | TPMT + NUDT15 / azathioprine | TPMT `*1/*1`; no independent NUDT15 truth | Both partners incomplete | Unknown; both dependencies named | No | Correct withholding; paired biological accuracy unassessable | T1; missing truth |
| NA18861 | SLCO1B1 / simvastatin | `*1/*14`; upstream primary `*1/*43` | Incomplete | Unknown | No | Disagreement withheld; root cause unresolved | T1 + T3/T9 |
| NA18861 | DPYD / fluorouracil | `*1/*9` legacy nomenclature | Missing critical positions | Unknown | No | Correct abstention; representation equivalence not scored | T1 + T9 |
| All three | CYP2D6 / codeine | Complex structural diplotypes | Unsupported uploaded-VCF pathway | Unknown with structural limitation | No | Correct scope refusal | Unsupported/T1 |
| Real derivatives | Required/critical/partner evidence removed or invalid | Same public source truth; altered input only | Less usable evidence | Unknown | No | No gain in certainty observed | T1 |

**Zero unjustified reassuring or warning assertions were observed in the primary real outputs. There were also zero real guidance assertions.** No eligible-case error rate, clinical safety conclusion, or population false-reassurance bound can be inferred from that absence of assertions. Synthetic positive and degraded controls are evidence about software invariants, not independent patient outcomes.

# 15. Explanation Faithfulness

All tested real outputs used the deterministic template path with static mode enabled. They named the requested drug, described Unknown, and did not present missing evidence as a normal call. Drug-level actions identified incomplete gene dependencies; azathioprine named both TPMT and NUDT15. SLCO1B1 mechanism text described a transporter and function categories. Citations and the absence of qualified clinical review remained explicit.

The [claim scan](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/claim-scan.json>) found no Safe/95%/low-clinical-risk/high-clinical-risk claims in actions and served explanation fields across the accepted real and synthetic cases. Manual structured-output review and actual export tests complemented this lexical scan; lexical absence is not clinical validation.

**Legacy-field caveat:** raw API responses still contain deprecated `confidence_score` and `severity`. A synthetic positive response, for example, contains `0.95` and `critical`. The schema and README explicitly say these are neither calibrated probability nor validated clinical severity; the Flutter display and user export omit them. This is the compatibility/deprecation option allowed by the original audit. It would be inaccurate to claim the fields were removed from the API. External API consumers must not reinterpret them as risk estimates.

Templates and source traceability are not independently established clinical correctness. Detailed real positive explanations could not be validated because no complete real input generated guidance. The patient-friendly default for Unknown is conservative, but full human approval requirements remain unresolved.

# 16. Provenance / Approval

Real responses carried PharmCAT 3.4.0, CPIC data `2026-07-13-11-40`, static-store generation timestamp, drug-specific source references, and warnings identifying deterministic fallback. The saved candidate includes store, content, source and context hashes in its manifests. The API's template result does not expose every manifest hash or a complete per-result semantic approval record; the frozen artifacts are needed for that audit trail.

The exact release gate was executed with all required checks and the recorded candidate SHA. [release-gate.json](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/release-gate.json>) reports:

| Prerequisite | Result |
|---|---|
| Six required checks | PASS |
| Provenance tracing | PASS; 106/106 clinical assertions traced by the project verifier |
| Local scientific bundle / artifact hash match | PASS with the recorded local file set |
| Candidate/tested revision match | PASS for recorded HEAD; dirty artifact identity also recorded |
| Human adjudication complete | **FAIL** |
| Outstanding claims absent | **FAIL: 19 outstanding** |
| All explanation entries approved | **FAIL: 0 approved, 20 unresolved** |
| Approved entries bound to human review | **FAIL** |
| Author-read record | 0 of 20 entries recorded as read |
| Clinical expert review | NOT OBTAINED, honestly reported |
| Final release status | **NOT READY**, unsuccessful exit |

The 160 recorded adjudications comprise 124 human and 36 automated decisions. Automated decisions did not satisfy the human prerequisite. The mechanical provenance pass demonstrates traceability according to the verifier, not that a clinician endorsed the text.

A harmless JAR-hash mismatch was introduced **only in the isolated copy**. The gate rejected the incompatible bundle: [release-gate-negative.json](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/release-gate-negative.json>). The copied manifest was restored afterward. Existing approval/hash/context negative tests also passed. Deployment jobs were inspected as dependent on the gate; no CI or production deployment was triggered to test that dependency live.

# 17. Reproducibility

Two fresh executions of the selected real NA18526 input through the actual in-process application produced identical readiness and scientific analysis after excluding timestamp and processing duration. Diplotype/candidate representation, final phenotype/label, provenance versions and static explanation were stable: [operational results](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/operational-inprocess.json>), [run 1](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/repeat-1-analysis.json>), [run 2](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/repeat-2-analysis.json>).

This was an isolated filesystem copy using the existing virtual environment and installed toolchains. A clean Linux container was not available because the Docker daemon was unavailable. It is not a clean dependency-install or deployment-image reproducibility proof.

**Confirmed portable-bundle defect:** `application_core_hash()` recursively includes the ignored file `backend/app/.DS_Store`. It is absent from Git's tracked files. Removing that file only in the temporary copy changed the core hash from `05ea0568…` to `4088208d63a77c3e43bce7ba65fa3eb59e0cedc75cd01b1460dc8555bbcb0299` and caused benchmark/artifact compatibility failure. See [failure output](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/finder-file-omission.json>) and [original local pass](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/original-bundle-verification.json>). Restoring the original bytes restored compatibility. A normal clean checkout cannot reproduce a hash that depends on an untracked Finder file.

The temporary backend execution copy was no longer present when work resumed on 27 September. All primary inputs, API payloads, direct real PharmCAT reports, test logs, gate results and manifests were already preserved in this audit directory. The fresh 74-file validator's summary log is preserved; its detailed JSON was written inside that temporary copy and is not part of the delivered evidence. The report relies on the preserved summary for that supporting check, not on an unavailable detailed artifact.

# 18. Resource / Privacy Tests

Bounded local HTTP tests used the real NA18526 2022 file: 2,475,022 bytes compressed, 29,474,087 bytes decoded, 26,825 records. No public production host was stressed.

| Measure | Default local Java settings | Configured Java limits |
|---|---:|---:|
| `/coverage` | 0.137 s, HTTP 200 | 0.149 s, HTTP 200 |
| Single `/analyze` | 2.735 s, HTTP 200 | 3.383 s, HTTP 200 |
| Two concurrent analysis durations | 2.814 s and 5.347 s | 2.524 s and 4.802 s |
| Peak active JVMs | 1 | 1 |
| Peak owned child processes | 1 | 1 |
| Peak summed server + descendant RSS | 1,069.9 MiB | **639.0 MiB** |

Configured limits were `-Xmx256m -XX:MaxMetaspaceSize=80m`, with one concurrent PharmCAT process. The timing and process count support serialized JVM work in this test. Summed macOS RSS is not Linux cgroup memory and can count shared pages more than once. Nevertheless, the measured 639 MiB peak does **not** establish compliance with the intended 512 MiB deployment. No actual deployment OOM was observed or claimed. A representative container run under the intended memory limit remains necessary for operational acceptance.

Real JVM cancellation completed in approximately 0.134 s and the deliberately short 0.15 s timeout completed in approximately 0.159 s. No observed child survived and no owned temporary residue remained after success/failure. The process probe also observed its own monitoring process; those observations are not described as two surviving JVMs. Descendant-process lifecycle regression tests passed. Files above the upload cap and corrupt inputs were rejected as described in §10.

Privacy observations: static mode remained enabled; optional external LLM calls were not used; the actual Python application was run with a socket-connect audit hook that would reject outbound connections and recorded zero attempts. Source/provider checks and privacy tests passed. Local HTTP access logs recorded request paths/status rather than genomic rows. Owned analysis temporary files were removed in the controlled tests.

Limits: the Python hook does not trace native JVM system calls, and production reverse-proxy logs, crash dumps, hosting retention and platform analytics were not audited. Historical project logs were preserved, not deleted or represented as newly proven private. This supports a bounded local no-observed-exfiltration result, not an absolute privacy guarantee. Evidence: [uncapped resource trace](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/resource-http.json>), [capped trace](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/resource-capped.json>), [operational/private-path probe](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/operational-inprocess.json>).

# 19. Frontend Validation

The unchanged Flutter app passed its existing analyzer and 198-test suite and built a release web bundle against the local API. Browser-level upload could not be completed: the in-app browser could not load the local page, the Chrome browser provider was unavailable, and native computer control lacked the necessary permissions. These limitations are not frontend passes.

As a narrower executable check, six actual saved API payloads were loaded into the application's real Flutter models, readiness widget and result screen: three public individuals, one real variant-only derivative, and two synthetic positive controls. All six rendered without widget exceptions and passed export assertions. The isolated test harness loaded the existing font files for readable screenshots; it did not change fonts, styles or production UI code.

Representative [real incomplete screenshot](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/frontend/NA18526-tutorial-sites.png>) and [synthetic actionable screenshot](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/frontend/synthetic-cyp2c19_poor_metabolizer.png>) were visually inspected. They show Unknown versus qualified/actionable PGx labels, research limitations and no percentage confidence. These are Flutter test renders, not proof of browser file-picker/network integration. Only the captured viewport was inspected; scrolling, all expanded cards and platform print dialogs were not manually verified.

**Status:** model/widget payload handling PASS for the six cases; full browser upload-to-result acceptance INCONCLUSIVE; a successful fully covered real-result frontend case unavailable. **No UI visual changes were made.** Evidence: [payload test log](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/frontend-real-payload-tests.log>), [font-render rerun](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/frontend-font-render-tests.log>), [web build](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/flutter-web-build.log>).

# 20. Export Validation

The six Flutter cases generated actual JSON exports and print-summary HTML. Assertions checked drug lists, exact scientific profiles, final labels and explanation text against API input; deprecated confidence/severity fields were absent from the user export. HTML contained the research disclaimer and PharmCAT version and did not reintroduce the searched safety/probability claims.

Warnings, limitations and guideline version fields were inspected in the generated artifacts. Representative files: [NA18526 JSON](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/frontend/NA18526-tutorial-sites.export.json>), [NA18526 print HTML](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/frontend/NA18526-tutorial-sites.print.html>), and [synthetic actionable JSON](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/frontend/synthetic-cyp2c19_poor_metabolizer.export.json>).

**PASS** for tested model/export scientific parity. Native save/copy interactions, browser print behavior and final PDF pagination remain **INCONCLUSIVE**. The test does not establish that every presentation-only detail is byte-identical to the API, nor that every platform's export dialog works.

# 21. Benchmark Statistics

The unit is **three public individuals**. There are nine accepted primary file presentations and 63 sample-presentation × gene comparison rows. Repeated representations and multiple genes are not independent people. No pooled biological-accuracy score is justified.

| Gene | Unique individuals | Independent diplotype truth N | Upstream primary exact-string matches per presentation class | Descriptive 95% Wilson interval | Contract-eligible application N | App assertions A |
|---|---:|---:|---|---|---:|---:|
| CYP2C19 | 3 | 3 | 3/3 | 43.9–100% | 0 | 0 |
| CYP2C9 | 3 | 3 | 3/3 | 43.9–100% | 0 | 0 |
| SLCO1B1 | 3 | 3 | 2/3 | 20.8–93.9% | 0 | 0 |
| TPMT | 3 | 3 | 3/3 | 43.9–100% | 0 | 0 |
| DPYD | 3 | 3 | 0/3 literal strings; representation differs | Not interpreted as biological accuracy | 0 | 0 |
| NUDT15 | 3 | 0 | Not evaluable | Not estimable | 0 | 0 |
| CYP2D6 | 3 | 3 | Not a supported VCF calling target | Not applicable | 0 | 0 |

Under **N = evidence-eligible application benchmark cases**, N=0, A=0. Therefore assertion coverage A/N, conditional error E/A and overall asserted error E/N are **undefined**, not 0% error or 100% accuracy. For the broader truth-available cohort, descriptive assertion coverage is 0/3 per truth-bearing gene (Wilson interval 0–56.2%). This is a different denominator and is labeled separately. Abstention was 3/3 per primary gene/presentation class, and four guidance pathways abstained for all three individuals. No phenotype or functional-equivalence concordance estimate is available.

The exact-string intervals describe these selected counts only. The cohort is tiny and selected by public tutorial availability, not randomly sampled for population inference. CHB n=2 and YRI n=1 support descriptions only: all abstained; the SLCO1B1 primary-call mismatch occurred in the one YRI-labeled individual. No ancestry was inferred, no interpretation was changed by population label, and no subgroup accuracy or Indian/South Asian generalization is justified.

The existing repository's 208-person/596-truth benchmark is a separate historical artifact whose compatibility and tests were checked. Those counts were **not** added to this fresh cohort or presented as newly rerun biological concordance. Detailed fresh statistics: [benchmark-statistics.json](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/benchmark-statistics.json>).

# 22. Discrepancy Analysis

| Taxonomy | Observed result / attribution |
|---|---|
| T1 — Input insufficient | All nine accepted primary real presentations fail the contract; final abstention is expected, not counted as erroneous guidance |
| T2 — Truth ambiguity | No new alternative-truth case was adjudicated. NUDT15 is missing truth, explicitly not scored as a mismatch |
| T3 — Upstream disagreement | NA18861 SLCO1B1 `*1/*43` versus truth `*1/*14`; repeated in all three representations. Root cause remains T3/T9 unresolved with T1 confounding |
| T4 — Application parsing | No divergence in 54 supported parsed reported diplotypes; nine CYP2D6 not-attempted rows are intentional |
| T5 — Phenotype mapping | No observed asserted real phenotype error; accuracy cannot be estimated because final results abstained and independent phenotype truth was unavailable |
| T6 — Guideline mapping | No observed real asserted mapping error; positive real guidance untested. Separate synthetic/source-row tests passed with declared accepted divergences |
| T7 — Evidence gate | No unexplained readiness/final inconsistency or certainty increase in tested controls |
| T8 — Explanation/provenance | Runtime fallback worked; release approval prerequisites failed. No observed real false-normal explanation |
| T9 — Version/definition | DPYD nomenclature differs; no post-hoc equivalence credit. CYP2C19 source-delta inclusion claim is contradicted by pinned definition contents |

For DPYD, the nine nonidentical comparison rows are three people repeated in three presentations. They preserve the literal mismatch but are not labeled nine biological errors. For CYP2D6, the nine Unknown source rows represent intentional unsupported structural calling, not nine failed attempted calls. The initial generic mismatch extraction remains preserved in [discrepancies.json](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/discrepancies.json>); [classified-comparisons.json](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/classified-comparisons.json>) is the explicit reviewed attribution. No failed case was removed.

**CYP2C19 definition check:** the July 13 bundle's translation was modified February 5, 2026 and still requires G at GRCh38 94775367 and 94842866 alongside A at 94781859. The [7 August 2026 ClinPGx update](https://blog.clinpgx.org/cyp2c19-2-core-allele-definition-update/) describes c.681G>A as the sole core defining variant, with ambiguity at the other positions. The local manifest nevertheless states `included_in_pinned_pharmcat_data; no isolated manual patch`. That inclusion claim is incorrect. Pinning older coherent data can be legitimate if accurately documented; this metadata is not accurate. No tested individual had independent CYP2C19 *2 truth, so an actual real-sample effect of the new definition remains untested. The data were not patched. See [definition comparison](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/cyp2c19-definition-delta.json>).

# 23. Audit Stop-Condition Matrix

| Condition | PASS / FAIL / INCONCLUSIVE | Evidence |
|---|---|---|
| 1. Four P0 requirements closed | **FAIL** | Evidence/scope/wording controls passed within tested bounds; R4 human approval and release prerequisites remain incomplete |
| 2. Independent benchmark transparent and complete as a bounded study | **PASS for the frozen negative-input study** | Frozen cohort/truth/equivalence, no silent exclusions, per-gene counts and classified mismatches; complete-real-input positive acceptance remains INCONCLUSIVE |
| 3. Claims bounded and headline evidence reproducible from declared bundle | **FAIL overall** | Evidence categories are distinguished in current records, but Finder-file dependency and inaccurate CYP2C19 delta prevent full reproducibility/source-status acceptance |
| 4. Operational repeatability in intended environment | **FAIL overall** | Local suites and lifecycle tests pass; portable bundle fails; intended Linux memory-limit run and deployment identity remain unverified |
| 5. Practical limitations explicit | **PASS** | CYP2D6/codeine unsupported, no automated warfarin dosing, no calibrated individualized risk or clinical-utility claim; zero real assertion coverage disclosed |

The six final packages and required experiments are assessed separately:

| Original requirement | Status | Basis |
|---|---|---|
| Package 1, R1/P0, E1 | PASS for tested software invariants | Partner, genotype, FILTER, build, compression, samples and parity controls; real positive transition unavailable |
| Package 2, R2/R3 P0 | PASS within tested boundary | Shared scope, qualified labels, uncertainty, deprecated API fields omitted from display/export |
| Package 3, R4/P0 | **FAIL** | Runtime fallback works; release still lacks required human approval |
| Package 4, R5/P1, E2 | PASS for transparent bounded benchmark; positive real analytical performance INCONCLUSIVE | Independent truth compared; all real application cases ineligible |
| Package 5, R6/P1, E7 | **FAIL** | Ignored-file identity dependency and incorrect definition-update status |
| Package 6, R7/P1, E8 | **INCONCLUSIVE overall** | Local process/privacy checks pass; intended constrained deployment environment not validated |

Completion Decision: the original audit's completion criteria are **not all satisfied**. The failure is not a demand to expand genes, drugs or architecture.

# 24. Remaining Issues

| ID | Severity | Finding | Reproduction / owner decision |
|---|---|---|---|
| F1 | **BLOCKER** | Mandatory release evidence incomplete: 19 outstanding claims, automated decisions unresolved for human review, 0/20 approved entries | Run the exact gate in an isolated candidate; inspect `release-gate.json`. This is not a claim that unapproved stored text was served in these tests |
| F2 | **HIGH** | Scientific core hash includes ignored `.DS_Store`, preventing clean-checkout reproduction | In a copy only, remove `backend/app/.DS_Store`; run bundle verifier; compare `finder-file-omission.json` |
| F3 | **MEDIUM** | CYP2C19 update marked included despite older pinned definition | Inspect embedded translation and saved delta record against the dated ClinPGx update; actual carrier effect untested |
| F4 | **OBSERVATION — acceptance gap** | No real input met evidence contract; normal/actionable real guidance remains unverified | Review complete frozen cohort; acquire compatible observed evidence before claiming successful real guidance, without filling absent calls |
| F5 | **OBSERVATION — operational concern** | 639 MiB summed local RSS with configured JVM caps; 512 MiB target not validated | Replay representative input/concurrency inside intended image and memory limit; no deployed OOM asserted |
| F6 | **OBSERVATION — test limitation** | Browser upload/export interactions and complete-real-result UI could not be exercised | Manual owner validation remains required; widget/model and export-generator checks passed |
| F7 | **OBSERVATION — unresolved caller comparison** | NA18861 SLCO1B1 primary diplotype differs from independent truth | Retain exact raw report and incomplete input; resolve source/definition/callability attribution before accuracy claims |

No fix was made. These findings do not justify changing the evidence gate, fabricating reference calls, replacing truth labels, or adding new production capabilities during this validation.

# 25. Claims the Project Can Now Defend

- For the selected public inputs, the actual API completed nine compatible but incomplete real-file analyses and withheld all drug guidance; three oversized originals were rejected.
- The tested missing/invalid-evidence cases did not produce increased certainty or unsupported reassurance. Synthetic complete-evidence controls separately demonstrated correct loss of azathioprine eligibility when either required partner became insufficient.
- No unexplained preview/final eligibility mismatch was observed in the 30 accepted case pairs.
- The tested capability boundary prevented unsupported drug guidance, including codeine and automated warfarin dosing.
- Reported upstream diplotypes were preserved by the parser in the tested supported rows; selected direct-call disagreements and representation differences remain disclosed.
- Static deterministic explanations, local repeatability and owned-process cleanup worked in the measured environment. The release gate rejected both the incomplete approval state and a deliberate bundle mismatch.

These are finite software and analytical observations. They are not claims of prescribing validity, calibrated clinical risk or clinical benefit.

# 26. Claims the Project Still Cannot Make

- Ready for release under its current mandatory gate, or all original audit completion criteria closed.
- Successful validated guidance from a fully covered real public genome in this fresh run.
- Measured conditional application accuracy when there were zero eligible real assertions.
- Fully resolved phase-sensitive diplotypes, independently established NUDT15 performance, or validated combined thiopurine actionable states from this cohort.
- DPYD functional equivalence or biological-error rates inferred only from nonidentical nomenclature.
- Inclusion of the August 2026 CYP2C19 *2 definition change in the recorded July bundle.
- Clean-checkout scientific-bundle reproducibility, a fresh Python 3.12/Linux-container pass, or safe operation under the intended 512 MiB limit.
- Full browser/platform export acceptance, absolute privacy, universal safety, clinical validation for prescribing, or demonstrated clinical utility.
- Statistical performance for any population subgroup, including Indian or South Asian populations, from these three individuals.

# 27. Release Recommendation

**The audit package is ready for manual owner review. The candidate is not ready for push/release approval on the evidence collected here.** Review F1–F3 as concrete unresolved release/evidence defects and F4–F7 as stated acceptance limitations. Any implementation or human-adjudication work is a subsequent, separately authorized task; it has not been performed by this validation.

The appropriate result is FAIL / NOT READY, rather than conditional pass, because the project's mandatory approval and reproducibility conditions remain unsatisfied. The conservative real-input behavior is useful evidence and should be retained without overstating it.

# OWNER VERIFICATION CHECKLIST

- [ ] Inspect the independently reference sample **NA18565**: [API result](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/api/NA18565-tutorial-sites.analyze.json>). Expect Unknown because the input is incomplete; a successful real normal-guidance case is still missing.
- [ ] Inspect the independently actionable **NA18526 SLCO1B1 *1/*15** case: [comparison](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/classified-comparisons.json>) and [API result](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/api/NA18526-tutorial-sites.analyze.json>). Expect abstention, not a falsely normal simvastatin conclusion; actionable real guidance remains unverified.
- [ ] Inspect the [real variant-only result](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/api/real-variant-only.analyze.json>) and [readiness](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/api/real-variant-only.coverage.json>): no answerable drug and explicit limitations.
- [ ] Check codeine, warfarin and out-of-scope drugs in the [complete synthetic control](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/api/synthetic-normal_metabolizer_control.analyze.json>): all must stay Unknown.
- [ ] Read served explanation and source text, especially missing TPMT/NUDT15, phase warnings, research disclaimer, and the lack of clinical expert review. Do not interpret raw deprecated confidence/severity fields as risk estimates.
- [ ] Inspect the [real Flutter screenshot](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/frontend/NA18526-tutorial-sites.png>), then manually exercise browser upload, expanded results and scrolling. The screenshot is a test render, not completed browser acceptance.
- [ ] Compare [JSON export](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/frontend/NA18526-tutorial-sites.export.json>) and [print HTML](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/frontend/NA18526-tutorial-sites.print.html>) to the API; manually check save/copy/print behavior.
- [ ] Read the **NOT READY** [release gate](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/release-gate.json>), [negative gate](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/release-gate-negative.json>), and [Finder-file failure](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/finder-file-omission.json>). Do not waive them based on green unit tests.
- [ ] Review the [external truth comparison](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/truth-caller-parser-application.json>), [statistics](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/benchmark-statistics.json>), source workbook and unresolved SLCO1B1/DPYD attribution; keep three people distinct from repeated file presentations.
- [ ] Review the [CYP2C19 definition discrepancy](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/cyp2c19-definition-delta.json>) and [capped resource evidence](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/resource-capped.json>).
- [ ] Inspect [initial diff](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/initial-diff.patch>), [final Git status](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/final-git-status.txt>), and [freeze verification](</Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-26/final-freeze-verification.json>). All pre-existing modifications remain uncommitted; the audit added only separate evidence files, and the owner supplied the original audit document.
- [ ] Decide on follow-up work only after reviewing the entire package. No Git or deployment action is implied by completion of this report.

### Source code modifications made during this validation:
`NONE` — production source unchanged; test harnesses and evidence were created only in isolated/audit locations.

### UI visual modifications:
`NONE`. No UI visual changes were made.

### Git commit:
`NOT PERFORMED`

### Git push:
`NOT PERFORMED`

### Release/tag:
`NOT PERFORMED`

### Deployment/redeployment:
`NOT PERFORMED`

### Production environment modified:
`NO`

**STOP — awaiting owner review.**
