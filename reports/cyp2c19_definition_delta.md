# CYP2C19 *2 definition delta — F3

Source verification: **30 September 2026**. This record corrects release metadata;
it does not change allele calling or claim new biological or clinical validation.

## Verified source state

| Record | Exact version / date / identity | Primary evidence |
|---|---|---|
| Current PharmVar *2 core | PV03110; NM_000769.4:c.681G>A, rs4244285; GRCh38 NC_000010.11:g.94781859G>A | [Allele record](https://www.pharmvar.org/haplotype/3110), [allele API](https://www.pharmvar.org/api/haplotypes/3110?projection=FullHaplotypeInfo), [variant API](https://www.pharmvar.org/api/haplotypes/search/findAllVariantsForHap?id=3110) |
| Definition replacement | PV00599 replaced by PV03110 at `2026-07-31T19:30:32.000+00:00` | [PharmVar history API](https://www.pharmvar.org/get-haplotype-history?id=3110) |
| PharmVar release containing that change | 6.2.28; updated `2026-07-31T19:34:56.000+00:00` | [PharmVar version history](https://www.pharmvar.org/get-previous-versions) |
| ClinPGx announcement | 7 August 2026; aligned *2 representation permits A or G at the companion positions | [ClinPGx definition-update notice](https://blog.clinpgx.org/cyp2c19-2-core-allele-definition-update/) |
| Current PharmVar database at verification | 6.2.29; updated `2026-09-22T21:55:42.000+00:00`; PV03110 remains active | [Live version API](https://www.pharmvar.org/get-version), allele API above |
| Latest official PharmCAT release at verification | v3.4.0; published `2026-07-14T01:19:45Z`; not a prerelease | [Release](https://github.com/PharmGKB/PharmCAT/releases/tag/v3.4.0), [latest release API](https://api.github.com/repos/PharmGKB/PharmCAT/releases/latest), [release list](https://api.github.com/repos/PharmGKB/PharmCAT/releases?per_page=10) |

The live PharmVar APIs were used because its interactive page did not render
in the available browser, and indexed pages still reported 6.2.28. The static
CYP2C19 change-log PDF returned an August 2019 document; it is not used as
evidence for this 2026 change. The version and history dates above come from
the actual API responses, not from search publication-date labels.

## Pinned executable behavior and known gap

Local PharmCAT remains **3.4.0**, with data version `2026-07-13-11-40`.
The embedded `org/pharmgkb/pharmcat/definition/alleles/CYP2C19_translation.json`
identifies source `CLINPGX`, build `GRCh38.p14`, and modification time
`2026-02-05T20:58:29.114Z`.

- JAR SHA-256: `9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741`
- CYP2C19 translation SHA-256: `54896015c0874a40811a05d895a03a43139c495d4ebd162589d98d8543cfc873`

Reading the *2 allele vector against the embedded variant positions gives:

| Transcript position | GRCh38 position | Pinned required base | Updated ClinPGx representation |
|---|---:|---|---|
| c.332-23 | 94775367 | G | R (A or G) |
| c.449 | 94775507 | R | R (A or G) |
| c.681 | 94781859 | A | A |
| c.991 | 94842866 | G | R (A or G) |

The new PharmVar biological core contains only c.681G>A. The four-position
ClinPGx representation includes ambiguity codes; a PharmCAT `corePositions`
list by itself therefore cannot prove that the update is included. The actual
base constraints and version dates establish that this pinned bundle predates
the change. These constraints remain unchanged by F3.

The corrected manifest uses `status: not_included_in_pinned_bundle`,
`local_bundle_status: coherent_older_definition`, and `impact: known_version_delta`.
It preserves the definition hash and expands the existing definition-delta
fixture to include the actual base requirements. Pinning this coherent older
bundle is an explicit version choice; describing the later update as included
was the metadata error.

The acceptance study did not include an independently characterized updated-*2
carrier. No new carrier result or biological validation is asserted here.
See the historical [acceptance report](../FINAL-REAL-WORLD-ACCEPTANCE-REPORT.md)
and [saved comparison](../audit-output/2026-09-26/cyp2c19-definition-delta.json).

## Upgrade decision and impact

No official release newer than 3.4.0 was found on the verification date, so
there is **no verified newer coherent PharmCAT candidate** containing the
update. A newer PharmVar database alone is not a replacement PharmCAT bundle.
No candidate engine/data change list or candidate performance result is claimed.

When such a release is available, the owner must authorize a controlled whole
bundle upgrade under the existing manifest policy. Its impact assessment must:

1. Record the candidate engine release, data version, checksums, release notes,
   and all changed allele definitions; verify the *2 bases inside that bundle.
2. Regenerate affected evidence-position artifacts from the coherent bundle and
   rerun the definition-delta fixture, companion-variant and phase-sensitive
   CYP2C19 cases, and the complete relevant regression suites. Any change to
   required evidence needs explicit review; this correction relaxes nothing.
3. Review affected phenotype/guidance mappings and explanation source/context
   hashes, invalidating stale approvals wherever their bound inputs change.
4. Rerun the external benchmark with its frozen truth and declared denominators,
   report changed calls and remaining input limitations, and preserve the old
   benchmark as historical evidence. A metadata correction is not a benchmark rerun.
5. Regenerate the compatible manifest and pass the existing release gate,
   including its actual human-review prerequisites.

No isolated definition patch, dependency upgrade, UI change, commit, push, or
deployment is part of F3.
