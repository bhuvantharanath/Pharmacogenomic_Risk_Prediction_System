# F7: NA18861 SLCO1B1 attribution

Investigation started 2026-10-01; completed 2026-10-02. Local, uncommitted evidence only.

## Conclusion

The defensible primary attribution is **C/D: truth-era nomenclature and PharmVar allele-definition evolution**. This is not a demonstrated application parser defect. The PharmCAT authors explicitly discuss this exact NA18861 *1/*14 versus *1/*43 discrepancy and explain that *43 entered PharmVar after GeT-RM tested the sample. See [Li et al., first published 2022-11-09, journal issue 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10121724/) (doi:10.1002/cpt.2790).

F7's attribution objective is resolved; **complete read-backed NA18861 validation is not completed**. The historical exact-label mismatch remains a mismatch. No truth, score, production rule, phenotype, or approval was changed. This does not make *14 and *43 interchangeable or clinically equivalent.

## Frozen source chain

- CDC workbook: `Consolidated_PGx-HLA_table_1-22-25-V4.xlsx`, internal modified property 2025-08-08 13:45:07, SHA256 `c66174befa7a7bbb6cfaf174cc500a269565407807467204bd7bc6eaae3be109`. `PGx HLA Genotypes!B280` is NA18861; `BC280` is *1/*14; `BD280` is study 2. Those cells have no comments. Study 2 is [Pratt et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC4695224/), doi:10.1016/j.jmoldx.2015.08.005, online 2015-11-24, January 2016 issue. The workbook's notes warn that labels retain each study's nomenclature, newer alleles may not have been tested, and *1 does not prove absence of untested variants. Its change sheet only records HG01190 CYP2C9 on 2025-08-01, not this SLCO1B1 result.
- The [current CDC page](https://www.cdc.gov/lab-quality/php/get-rm/reference-materials.html) still links that filename. A fresh binary download returned HTTP 403. Therefore no claim is made that the present remote bytes are identical or that a same-name revision is impossible.
- [PharmVar's current gene page](https://www.pharmvar.org/gene/SLCO1B1) lists *14 PV01631 and *43 PV01655 with the cores below. This was checked through the web-indexed primary page; the downloaded HTML is only a JavaScript shell, not a frozen database export.
- [PharmVar change log v1.5, 2025-06-10](https://a.storyblok.com/f/70677/x/c5918ca4bb/change-log_slco1b1_v1-5.pdf), Table 3 p.4, records *43.001/PV01670 and *43.002/PV01669 accepted **2021-05-21**, released **2021-10-14**, database **5.1**. These dates were read from the web-extracted table. Direct PDF download returned 403 and screenshot retrieval failed; visual verification was not completed. This corroborates, rather than substitutes for, the sample-specific authors' explanation.
- Pinned executable: PharmCAT **3.4.0**, JAR SHA256 `9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741`; data **2026-07-13-11-40**. Embedded SLCO1B1 definition modification date **2025-10-14T22:24:09.333Z**, format 2, GRCh38.p14/NC_000012.12. Its two allele cores agree with the current displayed PharmVar cores.

## Variant-level comparison

Coordinates are GRCh38 chr12; coding coordinates use NM_006446.5. In the *14 column, “unspecified” means null in the pinned definition, **not observed reference**. No variant state is inferred from absence or from a star label.

| Required variant | Frozen truth expectation | Public evidence / incomplete VCF | Pinned *14 | Pinned *43 | Current PharmVar core |
| --- | --- | --- | --- | --- | --- |
| 21176804 A>G; rs2306283; c.388A>G; N130D | One alternate copy under study's *1/*14 interpretation | A/G, GT 0\|1 | G | G | Both |
| 21176879 C>A; rs11045819; c.463C>A; P155T | One alternate copy under study's *1/*14 interpretation | C/A, GT 0\|1 | A | A | Both |
| 21196951 A>G; rs11045852; c.733A>G; I245V | Not established by frozen truth label | A/G, GT 0\|1 | Unspecified | G | *43 only |
| 21206031 A>G; rs74064213; c.1495A>G; I499V | Not established by frozen truth label | A/G, GT 0\|1 | Unspecified | G | *43 only |

`variant-comparison.json` enumerates **all 35** pinned SLCO1B1 positions, including every absent locus, allele-definition value and available input field. Twenty positions are present; fifteen are absent. All four discriminating records have FILTER `.` and FORMAT GT only: **no DP, GQ, AD, or explicit PS**. They are public-panel calls, not fresh read-level observations produced by this investigation.

The source is the 1000 Genomes high-coverage phased panel `20220422_3202_phased_SNV_INDEL_SV`, chr12. All four alternate bases occupy the same displayed haplotype. That supports the caller's phased interpretation but does not prove physical phase from new reads. The original GeT-RM paper explicitly retains a cis/trans caveat for the two *14 variants, including NA18861. Do not reinterpret the truth as experimentally resolved long-range phase across all four sites.

## Runtime and alternative explanations

Fresh pinned-PharmCAT replay of the **unchanged incomplete** derived VCF returned *1/*43, phenotype Indeterminate. Both frozen and replayed reports pass through the current parser as *1/*43, with one candidate and allele functions Normal function / Unknown function. “Definite” is the parser's candidate status, not evidence completeness. The frozen real API result for simvastatin remains **Unknown**; coverage reports 20/35 positions and 15 missing positions, with unfiltered calls. PharmCAT's retained *1 warning explicitly allows missing positions as well as reference positions; its SLCO1B1 recommendation note is also retained.

| Candidate explanation | Assessment |
| --- | --- |
| A: incomplete representation | Explains abstention and limits genotype certainty; not the primary explanation of this published label discrepancy. Both extra *43 core variants are actually present. |
| B: phasing ambiguity | Original truth has a phase caveat; panel phase is not new read-backed proof. Secondary uncertainty remains. |
| C/D: nomenclature/definition evolution | Primary documented attribution, supported by authors, timeline, and local variants. |
| E: pinned caller behavior | Reproduced under 3.4.0/data 2026-07-13-11-40; this same label discrepancy was documented in the earlier tutorial. |
| F: truth revision | Not established; frozen truth is retained and remote binary refresh was unavailable. |
| G: unexplained caller disagreement | Exact-label discordance remains, but primary literature supplies a specific version-history explanation. No claim of complete biological adjudication. |
| H: application parser defect | Not demonstrated: source and parsed calls agree exactly in both reports. |

## Read-level availability and remaining limitation

ENA **ERR1955362 / SAMEA103899733**, sample alias NA18861, exposes a **65,509,076,175-byte BAM** plus index and three FASTQ objects. Exact URLs, archive MD5 values and retrieval checksum are frozen in `ena-ERR1955362.tsv` and `acquisition.jsonl`. BAM archive MD5: `5f0cd9fb09f1feb0719274f6f61a7542`; this is archive metadata, **not a locally verified BAM checksum**. Alignment/reference build has not been established from its header. An attempted broader ENA study metadata transfer did not complete and was canceled; no partial response is used as evidence.

No full reads were downloaded or newly genotyped here. F4 produced CYP2C19 evidence for NA18526 and NA12878, not NA18861; its conditional complete-NA18861 rerun is therefore unavailable. The next independent confirmation would freeze a NA18861/SLCO1B1 read-calling protocol, verify sample/build/reference checksums, call every required locus without fabricated reference records, and rerun PharmCAT only if evidence passes. Long-range phase would still need appropriate support. This remains a validation limitation, not permission to patch the caller or production parser.

## Reproduction and checks

Run from the repository root:

```sh
backend/.venv/bin/python audit-output/2026-10-01-f7/verify.py
backend/.venv/bin/python -m pytest backend/tests/test_pharmcat_parser.py backend/tests/test_external_benchmark.py backend/tests/test_coverage_gate.py backend/tests/test_evidence_validity.py -q
```

The replay uses the existing trusted JAR and never fills missing records. `verification.json` contains the exact Java command, exit status, versions and checks. Replay exited 0; all evidence assertions passed. Relevant parser, external benchmark, coverage and evidence tests: **83 passed, zero failed/skipped** (retained JUnit). No production fix was justified, so no fix or full release recertification was performed. F7 does not change the release gate or claim release readiness.

Only this new evidence directory was added by F7. `attribution.json` is an explicit overlay on the historical generic discrepancy category; it does not overwrite `discrepancies.tsv`, truth rows or metrics. `local-evidence.json` freezes originals, reports, warnings, parsed/API inputs and bundle definition checksums. The tracked working-tree diff is byte-for-byte unchanged from F7's starting snapshot. Existing unrelated local changes remain intact. No commit, push, deployment, fabricated human review or clinical-expert approval.
