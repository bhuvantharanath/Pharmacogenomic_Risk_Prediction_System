# F4 — real observed-evidence acceptance

Execution: 30 September 2026. Local, uncommitted research/educational candidate. **F4's real-input objective is satisfied for CYP2C19/clopidogrel: one normal and one actionable public individual.** This is not clinical validation or general validation of every pathway.

## Result

| Public individual | Independent CDC consensus | Qualifying observed sites | Read depth at required sites | PharmCAT → parser → API | Final clopidogrel label |
|---|---|---|---|---|---|
| NA18526 | CYP2C19 `*1/*1` | 35/35, all PASS | 21–42 | `*1/*1`, normal metabolizer throughout | No PGx-guided adjustment identified |
| NA12878 | CYP2C19 `*1/*2` | 35/35, all PASS | 15–41 | `*1/*2`, intermediate metabolizer throughout | Ineffective |

Both `/coverage` calls and both `/analyze` calls returned HTTP 200. Only clopidogrel was answerable. Simvastatin, fluorouracil, azathioprine, warfarin and codeine were Unknown for both individuals. Two separate direct PharmCAT runs also exited 0. All 70 observed site genotypes were preserved in the corresponding PharmCAT gene reports. Exact source diplotypes and independently assigned phenotypes matched in both cases; no parser discrepancy or newly demonstrated production defect was found in this evaluated path.

The label `Ineffective` above is the application's categorical output, **not an observed clinical outcome or a guarantee of non-response**. Guideline-direction comparison concerns the preregistered hypothetical ACS/PCI context. The application reports that it selected the strongest of three population-specific recommendations and asks the reader to check the applicable population. These public reference donors are not asserted to have ACS, PCI, or an indication for medication. Independent phenotype assignment uses CPIC 2022 Table 1, and guidance comparison uses Table 2, not application output: [CPIC publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC9287492/).

## What changed from the previous acceptance run

The previous variant-only presentations lacked explicit observations at required reference positions. This run obtained the actual aligned reads and used an upstream standard caller to emit observed invariant and variant calls. **No production coverage threshold, application rule, PharmCAT definition, truth record or approval was changed.**

NA18526 contains 34 caller-produced homozygous-reference observations and one homozygous non-reference observation; NA12878 contains 32 reference observations and three non-reference observations. The normal `*1/*1` control is not synonymous with being reference at every GRCh38 base: both samples carry rs3758581 G/G at chr10:94842866, which is compatible with the pinned `*1` definition. No `0/0` was manually written, inserted for absent sites, copied from truth, or inferred from the application.

The minimum reference-call PL margin was 63 for NA18526 and 45 for NA12878, above the fixed 20 threshold; all variant GQ values were 127. Reference PL margins are likelihood comparisons, not fabricated GQ or calibrated confidence estimates. Every DP/GQ/AD/GT/FILTER and original PL observation is preserved in the per-sample evidence JSON.

## Freeze and identity

Protocol frozen **2026-09-30T13:57:04.602733+00:00**, before read extraction, genotype calling and new application scoring. Earlier variant-only results were known and disclosed; this is not described as blinded. No sample was replaced, no threshold tuned, and no genotype altered after results.

| Artifact | SHA-256 |
|---|---|
| Frozen protocol JSON | `7b9a30b40b08bcc31d95f3526c6d9df850fb46f8a26262de2fe28994db9fa706` |
| Exact chr10 reference FASTA | `5380b5de2f7c54026e87cb6cd30573f645bce6466481f15861d45557d7590933` |
| NA18526 observed VCF | `9829ae37bb8d5ecb5b5e93cc720ee795df8a5efcb850f5b8ca2b47d65d246548` |
| NA12878 observed VCF | `92d54bcaafb1ae065cbe38f1c333f5d72fd40ee263161ee431643975c9cca1a7` |
| Scientific bundle manifest | `718dbcf0480d8d73a40ff1356ef65962440a43acae24c781eaeeba232e95c7a8` |
| Tested release artifact | `de4434adc05db07271e6fc34175098cde0163283495466b395ed2d2fd415db44` |

Reference sequence identity: chr10 length 133797422, MD5 `c0eeee7acfdaf31b770a509bdaa6e51a`, matching both CRAM headers and the official 1000 Genomes reference dictionary. Bounded interval: chr10:94760900–94853914, one-based inclusive. Acquired 24,345 alignment records for NA18526 and 23,405 for NA12878; read filters were applied by the caller. Local BAM checksums and exact timestamps are in extraction receipts.

PharmCAT remains 3.4.0 / data `2026-07-13-11-40`. The known older CYP2C19 *2 definition is still coherently pinned; this run neither upgrades it nor claims the later PharmVar definition is included. Both observed read-derived inputs resolve under the pinned behavior and match the frozen consensus truth.

## Sources and acquisition

Independent genotype truth is the unchanged CDC GeT-RM consolidated 22 January 2025 V4 workbook, SHA-256 `c66174befa7a7bbb6cfaf174cc500a269565407807467204bd7bc6eaae3be109`, with existing exact extracted rows included in the freeze. [CDC source workbook](https://www.cdc.gov/lab-quality/media/files/2025/08/Consolidated_PGx-HLA_table_1-22-25-V4.xlsx).

Read data: public NYGC 30× Illumina NovaSeq WGS, study PRJEB31736 / ERP114329. Original CRAM headers retain the source alignment and processing provenance. [Collection README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/20190405_1000G_2504_high_cov_README.md).

| Sample | ENA run / sample | Exact CRAM URL | Archive-reported CRAM MD5 |
|---|---|---|---|
| NA18526 | ERR3239353 / SAMN00001593 | https://ftp.sra.ebi.ac.uk/vol1/run/ERR323/ERR3239353/NA18526.final.cram | `4abcd7da28419aba4ceeb29ebe45e7ee` |
| NA12878 | ERR3239334 / SAMN00801888 | https://ftp.sra.ebi.ac.uk/vol1/run/ERR323/ERR3239334/NA12878.final.cram | `7b60651143aa1b18e807ced767886fd2` |

Indexes are the same URLs plus `.crai`; downloaded index MD5s were checked against ENA. **Whole 15–16 GB remote CRAM MD5s were not locally recomputed**: indexed retrieval was used. The retained BAMs, reference, downloaded indexes and outputs have locally computed SHA-256 identities. This distinction is explicit in acquisition metadata.

Reference source: https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/GRCh38_reference_genome/GRCh38_full_analysis_set_plus_decoy_hla.fa, using its `.fai` and chr10 byte range recorded in `acquisition.json`. A pre-freeze UCSC reference attempt failed exact sequence identity and was rejected. The partial slow ENA reference download was stopped. Neither entered calling.

Source verification used direct primary-source web/API access. No separate Deep Research tool was available; no Deep Research session or human source review is claimed.

## Verification, explanation and release boundary

Eight preparation-policy checks pass. Twenty-four result-integrity/truth/parser/eligibility/explanation checks pass. Both Dart model/export checks pass: six analyses, diplotype/profile, label and explanation fields are retained. No Flutter UI was changed. The complete final mandatory-check result is in `release-status.json`; the earlier sandbox-limited attempt is retained separately and is not misrepresented as a product failure.

Final full checks: **903 backend tests passed, 8 skipped, zero failures/errors** (911 collected; retained JUnit); **198 Flutter tests passed**; Flutter analysis found no issues. Compatible-bundle verification, provenance verification and label-mapping validation passed. The latter retains the existing 13 documented baseline divergences; these are not newly validated biological matches. `git diff --check` passed.

Authoritative final gate: **NOT READY**, exit code 1, all six required software checks passing. Approved generated entries: **0**; unapproved: **20**; releasable generated: **0**; fallback-only cases: **20**; human review complete for releasable set: **null / not asserted**; clinical expert review: **NOT_OBTAINED**. Declared policy remains `human_review_all_stored_generated_entries`; effective runtime mode is `deterministic_template_only`. Nineteen claims remain outstanding, 36 decisions are automated, 124 are recorded human adjudications, and 0/20 entries have recorded author-read approval. The owner must complete the declared review requirements; the empty releasable generated set does not silently waive them.

Stored prose remained ineligible in both cases because its approval status is unresolved. The actual runtime used deterministic templates and explicitly stated that no clinical expert had reviewed the text. The historical `llm_generated_explanation` JSON field name does not imply a live LLM generated this output. **No human or expert approval was added.** F4 success does not close F1's mandatory review requirement or grant release permission.

Operational notes: sequential reading of unindexed intermediate pileup BCFs emitted harmless index-lookup messages; all 35 records per sample were read and verified. The initial evidence-export harness used a dataclass serializer on a Pydantic result; that harness-only error was corrected to `model_dump`, and direct PharmCAT/report export completed. Original HTTP results were retained. The Dart launcher initially required a non-writable SDK cache; invoking the installed Dart binary directly completed both checks. No input or clinical logic was changed for these tooling corrections.

## Limits and discrepancy classification

No discrepancy in the evaluated CYP2C19 pathway. This is **two selected positive controls**, not a population benchmark, sensitivity/specificity estimate, clinical outcome study, or a validation of structural variation/rare alleles. CDC supplies consensus star diplotypes, not independent truth for every one of the 70 base-level observations; base-level agreement here measures caller-to-PharmCAT fidelity, not independent per-base accuracy. Unphased genotypes remain unphased; no synthetic phase was assigned.

NUDT15 truth is unavailable for these selected individuals, so no paired TPMT/NUDT15 positive case is claimed. Other pathways remain unevaluated by this read-derived run. No new production defect was demonstrated; any later defect requires a separate authorized remediation.

## Files and reproducibility

All F4 additions are contained in this directory; production source, UI, truth snapshots, scientific configuration and approval data remain unchanged. `PROTOCOL.md` plus `frozen-protocol.json` contain all frozen rules; `commands.jsonl` contains the exact executed caller commands. `acquisition.json`, `*.ena.tsv`, headers, extraction receipts and `artifact-checksums.json` provide provenance. `*.observed.vcf`, `*.evidence.json`, `*.coverage.json`, `*.analyze.json`, `*.pharmcat/`, `*.parsed.json`, `*.dart-export.json`, and `truth-comparison.json` provide inputs and results.

Final Git status retains the preexisting dirty tree: **66 modified tracked files, 35 untracked status entries, 0 staged changes** (`audit-output/` is one untracked directory entry). Full status is saved in `git-status.txt`. F4 added this evidence directory only. The release artifact hash remains unchanged from before F4. No commit, push, merge, tag, release, deployment or redeployment was performed.

Install pysam 0.23.3 into a **separate validation environment**; use bcftools/htslib 1.24 and the unchanged project backend environment/JAR. To reproduce in a fresh repository copy, retain the original freeze evidence and run the provided scripts in a new run directory at the same two-level depth under the repository:

```sh
VALIDATION_PYTHON prepare.py acquire
VALIDATION_PYTHON prepare.py freeze
BACKEND_PYTHON test_preparation.py
VALIDATION_PYTHON derive.py
BACKEND_PYTHON score.py
BACKEND_PYTHON check_results.py
DART_BINARY check_models.dart
```

Replace the uppercase placeholders with the relevant interpreter paths; run from the new directory. `score.py` uses a temporary localhost-only port 8766 server and stops it. Read the exact frozen commands before rerunning. Existing freeze/observed inputs are deliberately not overwritten. Recreated VCF headers contain new timestamps and paths, so whole-file checksums identify a particular execution; genotype/evidence comparisons, reference identity and pinned inputs establish reproduction across runs. No commit, push or deployment is part of reproduction.
