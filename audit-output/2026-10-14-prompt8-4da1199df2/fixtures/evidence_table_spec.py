"""Frozen evidence table: written before any application result in this task was evaluated."""
import hashlib, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path

R = Path(sys.argv[1]); D = Path(sys.argv[2])
SIX = "clopidogrel,fluorouracil,azathioprine,simvastatin,warfarin,codeine"
NM_GUIDANCE = "No PGx-guided adjustment identified"
ABSTAIN = {"warfarin": "Unknown (explicit abstention: no automated dose)", "codeine": "Unknown (explicit abstention: CYP2D6 CNV/SV not called)"}
CPIC = {
 "clopidogrel": "CPIC 2022 CYP2C19/clopidogrel (PMID 35034351, PMC9287492): NM -> standard dose if indicated; IM/PM -> avoid standard-dose clopidogrel in ACS/PCI; recommendation applies to ACS/PCI population (hypothetical context; donor diagnosis not inferred)",
 "simvastatin": "CPIC 2022 SLCO1B1/ABCG2/CYP2C9 statins (PMID 35152405): normal function -> no PGx-guided change",
 "fluorouracil": "CPIC DPYD/fluoropyrimidines (2017 + 2024 update): activity score 2 -> standard dose; activity score 1 (one no-function allele) -> reduce starting dose 50%",
 "azathioprine": "CPIC TPMT/NUDT15 thiopurines (2018; 2025 update PMID 41618934): requires both genes; NM/NM -> standard dosing",
}
fixtures = [
 dict(id="D01", label="Complete synthetic normal control", src="test-data/normal_metabolizer_control.vcf", synthetic=True,
      provenance="Fabricated by test-data/generate_synthetic_vcf.py from PharmCAT 3.4.0 definitions (header: all genes reference; definition CLINPGX 2026-07-13-11-40). Not a person.",
      inspected="306 PASS hom-ref rows; 35/35 CYP2C19, 88/88 CYP2C9, 35/35 SLCO1B1, 45/45 TPMT, 20/20 NUDT15, 83/83 DPYD; CYP2D6 0/157",
      drugs=SIX, expected={"clopidogrel": NM_GUIDANCE + " + ACS/PCI qualifier", "simvastatin": NM_GUIDANCE, "fluorouracil": NM_GUIDANCE, "azathioprine": NM_GUIDANCE, **ABSTAIN},
      basis="Generator diplotypes (reference) + CPIC guideline direction + capability registry abstentions. Synthetic circular plumbing check, not independent validation.", browser=True),
 dict(id="D02", label="Complete synthetic CYP2C19 poor-metabolizer control", src="test-data/cyp2c19_poor_metabolizer.vcf", synthetic=True,
      provenance="Fabricated generator output, header CYP2C19=*2/*2; other genes reference.",
      inspected="306 PASS rows; CYP2C19 hom-alt at 94775367, 94775507, 94781859, 94842866; all six genes complete",
      drugs=SIX, expected={"clopidogrel": "Ineffective (CYP2C19 *2/*2, PM) + ACS/PCI qualifier", "simvastatin": NM_GUIDANCE, "fluorouracil": NM_GUIDANCE, "azathioprine": NM_GUIDANCE, **ABSTAIN},
      basis="Generator header *2/*2 -> PM (CPIC 2022 Table 1) -> avoid clopidogrel in ACS/PCI. Synthetic; not independent truth.", browser=True),
 dict(id="D03", label="Supported synthetic DPYD variant-carrier control", src="test-data/dpyd_variant_carrier.vcf", synthetic=True,
      provenance="Fabricated generator output, header DPYD=c.1905+1G>A (*2A)/Reference.",
      inspected="306 PASS rows; DPYD chr1:97450058 = 1/0 (c.1905+1G>A); all six genes complete",
      drugs=SIX, expected={"clopidogrel": NM_GUIDANCE + " + ACS/PCI qualifier", "simvastatin": NM_GUIDANCE, "fluorouracil": "Adjust Dosage (DPYD IM, activity score 1)", "azathioprine": NM_GUIDANCE, **ABSTAIN},
      basis="One no-function DPYD allele -> AS 1 -> IM -> 50% starting-dose reduction (CPIC). Synthetic.", browser=True),
 dict(id="D04", label="Frozen F4 NA18526 read-backed normal", src="audit-output/2026-09-30-f4/NA18526.observed.vcf", synthetic=False,
      provenance="Public 1000G/NYGC ERR3239353 reads, bcftools 1.24 frozen protocol (audit-output/2026-09-30-f4/PROTOCOL.md, frozen 2026-09-30T13:57:04Z, sha verified). Every required CYP2C19 record read-backed; no inferred 0/0.",
      inspected="35 PASS rows, CYP2C19 only (34 hom-ref, 94842866 1/1); other genes 0 positions",
      drugs=SIX, expected={"clopidogrel": NM_GUIDANCE + " (CYP2C19 *1/*1, NM) + ACS/PCI qualifier", "simvastatin": "Unknown (no SLCO1B1 evidence)", "fluorouracil": "Unknown (no DPYD evidence)", "azathioprine": "Unknown (no TPMT/NUDT15 evidence)", **ABSTAIN},
      basis="Independent CDC GeT-RM V4 consensus *1/*1 (sha c66174be...), frozen predicted phenotype Normal Metabolizer; CPIC 2022 NM -> standard therapy if indicated.", browser=True),
 dict(id="D05", label="Frozen F4 NA12878 read-backed actionable", src="audit-output/2026-09-30-f4/NA12878.observed.vcf", synthetic=False,
      provenance="Public ERR3239334 reads, same frozen F4 protocol.",
      inspected="35 PASS rows, CYP2C19 only; het at 94775367 and 94781859 (*2 core), 94842866 1/1",
      drugs=SIX, expected={"clopidogrel": "Ineffective (CYP2C19 *1/*2, IM) + ACS/PCI qualifier; hypothetical context, no donor diagnosis", "simvastatin": "Unknown", "fluorouracil": "Unknown", "azathioprine": "Unknown", **ABSTAIN},
      basis="Independent CDC GeT-RM *1/*2, frozen predicted phenotype Intermediate Metabolizer; CPIC 2022 IM in ACS/PCI -> avoid standard-dose clopidogrel.", browser=True),
 dict(id="D06", label="Real variant-only presentation (NA12878 minus hom-ref rows)", src="audit-output/2026-10-05-prompt7-5b236070c2/real-variant-only.vcf", synthetic=False,
      provenance="Degradation-only derivative of D05 by Prompt 7 real_acceptance.py: every 0/0 row deleted. No genotype edited.",
      inspected="3 PASS rows (94775367 0/1, 94781859 0/1, 94842866 1/1); CYP2C19 3/35",
      drugs=SIX, expected={d: "Unknown" for d in SIX.split(",")},
      basis="Documented contract (docs/input_requirements.md evidence-quality section): absent positions do not satisfy completeness and are never inferred as reference.", browser=True),
 dict(id="D07", label="Real incomplete public VCF (bundled NA12273, 1000G)", src="app/assets/samples/pharmaguard_sample_1000genomes.vcf", synthetic=False,
      provenance="Real 1000 Genomes high-coverage NA12273 restricted to PharmCAT positions (test-data/demo/README.md); polymorphic-filtered source; no build header.",
      inspected="169 rows FILTER '.'; CYP2C19 16/35, CYP2C9 17/88, SLCO1B1 20/35, TPMT 9/45, NUDT15 5/20, DPYD 31/83 (critical 8/28)",
      drugs=SIX, expected={d: "Unknown" for d in SIX.split(",")},
      basis="Every guidance gene below the documented contract; incomplete evidence must stay Unknown.", browser=True),
 dict(id="D08", label="Oversized public VCF (PharmCAT tutorial NA18526 bgzip)", src="audit-output/2026-09-26/originals/PharmCAT_tutorial_get-rm_wgs_30x_grch38.NA18526.vcf.bgz", synthetic=False,
      provenance="PharmCAT-tutorial commit 30253e35 raw.githubusercontent download, 2026-09-26, sha a3e4676b...",
      inspected="11,181,875 bytes (> 5,242,880 upload limit)",
      drugs=SIX, expected={"upload": "HTTP 413 FILE_TOO_LARGE at /coverage and /analyze; clear 5 MB message; controls re-enabled; next valid file analyses normally"},
      basis="Documented 5 MB limit (vcf_validation.MAX_UPLOAD_BYTES; docs/input_requirements.md).", browser=True),
 dict(id="D09", label="Malformed VCF (truncated gzip)", src="audit-output/2026-09-26/derived/real-truncated.vcf.gz", synthetic=False,
      provenance="2026-09-26 run_acceptance.py: real-valid-gzip.vcf.gz (NA18526 raw required sites, lossless gzip) with final 9 bytes removed.",
      inspected="22,878 bytes; gzip decode fails (EOF before end-of-stream marker)",
      drugs=SIX, expected={"upload": "HTTP 400 CORRUPT_GZIP; clear message; recovery"},
      basis="Documented structural validation; corrupt input is rejected, never partially analysed.", browser=True),
 dict(id="D10", label="Failed FILTER at CYP2C19 *2 core position", src="audit-output/2026-10-05-prompt7-5b236070c2/real-failed-filter.vcf", synthetic=False,
      provenance="Degradation of D05: FILTER=LowQual at chr10:94781859 only.",
      inspected="35 rows; 94781859 FILTER LowQual GT 0/1; usable 34/35",
      drugs=SIX, expected={d: "Unknown" for d in SIX.split(",")},
      basis="Contract: named FILTER failure does not satisfy completeness; CYP2C19 requires 35/35.", browser=True),
 dict(id="D11", label="Partial genotype at CYP2C19 *2 core position", src="audit-output/2026-10-05-prompt7-5b236070c2/real-partial-gt.vcf", synthetic=False,
      provenance="Degradation of D05: GT 0/. at chr10:94781859.",
      inspected="35 rows; 94781859 GT 0/.; usable 34/35",
      drugs=SIX, expected={d: "Unknown" for d in SIX.split(",")},
      basis="Contract: partial call 0/. does not satisfy completeness.", browser=True),
 dict(id="D12", label="Missing required CYP2C19 position", src="audit-output/2026-10-05-prompt7-5b236070c2/real-missing-required.vcf", synthetic=False,
      provenance="Degradation of D05: row chr10:94781859 deleted.",
      inspected="34 rows; 94781859 absent; usable 34/35",
      drugs=SIX, expected={d: "Unknown" for d in SIX.split(",")},
      basis="Contract: absent position is not inferred as reference.", browser=True),
 dict(id="D13", label="Missing TPMT partner evidence (synthetic)", src="audit-output/2026-10-05-prompt7-5b236070c2/missing-TPMT.vcf", synthetic=True,
      provenance="D01 with every chr6 row removed (Prompt 7).",
      inspected="261 rows; TPMT 0/45, NUDT15 20/20, others complete",
      drugs=SIX, expected={"azathioprine": "Unknown (TPMT evidence missing)", "clopidogrel": NM_GUIDANCE + " + ACS/PCI qualifier", "simvastatin": NM_GUIDANCE, "fluorouracil": NM_GUIDANCE, **ABSTAIN},
      basis="Registry: azathioprine evidence_dependencies TPMT AND NUDT15.", browser=True),
 dict(id="D14", label="Missing NUDT15 partner evidence (synthetic)", src="audit-output/2026-10-05-prompt7-5b236070c2/missing-NUDT15.vcf", synthetic=True,
      provenance="D01 with every chr13 row removed (Prompt 7).",
      inspected="286 rows; NUDT15 0/20, TPMT 45/45, others complete",
      drugs=SIX, expected={"azathioprine": "Unknown (NUDT15 evidence missing)", "clopidogrel": NM_GUIDANCE + " + ACS/PCI qualifier", "simvastatin": NM_GUIDANCE, "fluorouracil": NM_GUIDANCE, **ABSTAIN},
      basis="Registry: azathioprine requires both partners (original audit counterexample #1).", browser=True),
 dict(id="D15", label="Scope abstention: unsupported drug, CYP2D6/codeine, warfarin", src="app/assets/samples/pharmaguard_sample_normal.vcf", synthetic=True,
      provenance="Bundled synthetic DEMO_NORMAL (generator; CYP2D6 *1/*1 padded, 157/157 positions present).",
      inspected="463 PASS rows; all seven genes complete incl. CYP2D6 157/157 (2 hom-alt CYP2D6 rows of the *1 definition background)",
      drugs="clopidogrel,ibuprofen,codeine,warfarin", expected={"clopidogrel": NM_GUIDANCE + " + ACS/PCI qualifier (positive control in same request)", "ibuprofen": "Unknown (outside audited scope; no CPIC text invented)", "codeine": "Unknown even with 157/157 CYP2D6 positions", "warfarin": "Unknown (no dose calculation)"},
      basis="Capability registry + docs: CYP2D6 calling withheld; warfarin dosing not implemented; unregistered drug abstains.", browser=True),
 dict(id="D16", label="Real incomplete official tutorial preprocessed VCF (NA18526)", src="audit-output/2026-09-26/originals/NA18526.preprocessed.vcf", synthetic=False,
      provenance="PharmCAT-tutorial commit 30253e35 official preprocessed output, sha 188f839e...",
      inspected="236 rows incl. PCATxREF/PCATxALT filters; CYP2C19 19/35; TPMT 12/45; NUDT15 5/20; DPYD critical 12/28",
      drugs=SIX, expected={d: "Unknown" for d in SIX.split(",")},
      basis="Below contract for every gene.", browser=False),
]
inputs = D / "fixtures" / "inputs"; inputs.mkdir(parents=True, exist_ok=True)
for f in fixtures:
    src = R / f["src"]
    data = src.read_bytes()
    f["source_sha256"] = hashlib.sha256(data).hexdigest(); f["bytes"] = len(data)
    name = f"{f['id']}-{src.name}"
    dest = inputs / name
    shutil.copyfile(src, dest)
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == f["source_sha256"]
    f["upload_copy"] = str(dest.relative_to(R))
    f["cpic_basis"] = {d: CPIC[d] for d in CPIC if d in f["drugs"]}
table = {"frozen_utc": datetime.now(timezone.utc).isoformat(), "frozen_before_evaluation": True,
         "note": "Synthetic controls are fabricated plumbing checks (shared definitions with the caller) and are not independent clinical validation. F4 truth is consensus star-allele truth, not per-base truth.",
         "fixtures": fixtures}
(D / "fixtures" / "EVIDENCE-TABLE.json").write_text(json.dumps(table, indent=1) + "\n")
print(len(fixtures), "fixtures frozen")
