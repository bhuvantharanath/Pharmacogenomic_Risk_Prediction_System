"""Reproducible comparisons; no input generation or production mutation."""
import json
from prepare import OUT, ROOT, digest, save


def main():
    protocol = json.loads((OUT / "frozen-protocol.json").read_text())
    assert digest(OUT / "frozen-protocol.json") == (OUT / "frozen-protocol.sha256").read_text().strip()
    for name, expected in protocol["hashes"].items():
        assert digest(ROOT / name) == expected, name
    truth = {r["sample_id"]: r["truth_raw"] for r in protocol["truth"]}
    results = []
    for sample in protocol["samples"]:
        evidence = json.loads((OUT / f"{sample}.evidence.json").read_text())
        api = json.loads((OUT / f"{sample}.analyze.json").read_text())
        coverage = json.loads((OUT / f"{sample}.coverage.json").read_text())
        raw = json.loads(next((OUT / f"{sample}.pharmcat").glob("*.report.json")).read_text())["genes"]["CYP2C19"]
        parsed = json.loads((OUT / f"{sample}.parsed.json").read_text())["genes"]["CYP2C19"]
        profile = api["analyses"][0]["pharmacogenomic_profile"]
        positions = {r["position"]: r for r in evidence["records"]}
        base_matches = []
        for variant in raw["variants"]:
            r = positions[variant["position"]]
            alleles = [r["ref"]] + (r["alt"] or [])
            observed = sorted(alleles[i] for i in r["GT"])
            base_matches.append(observed == sorted(variant["call"].replace("|", "/").split("/")))
        checks = {
            "input_checksum": digest(OUT / f"{sample}.observed.vcf") == evidence["observed_vcf_sha256"],
            "all_35_qualifying_observed_sites": evidence["passing_positions"] == 35 and not evidence["missing_positions"],
            "no_failed_records": all(not r["reasons"] and r["FILTER"] == ["PASS"] for r in evidence["records"]),
            "coverage_only_clopidogrel": coverage["answerable_drugs"] == ["clopidogrel"],
            "observed_genotypes_preserved_in_pharmcat": len(base_matches) == 35 and all(base_matches),
            "direct_pharmcat_matches_truth": [x["label"] for x in raw["sourceDiplotypes"]] == [truth[sample]],
            "direct_pharmcat_matches_independent_phenotype": raw["sourceDiplotypes"][0]["phenotypes"] == [protocol["independent_predicted_phenotypes"][sample]],
            "parser_matches_direct_and_truth": parsed["diplotype"] == truth[sample] and parsed["phenotype_raw"] == protocol["independent_predicted_phenotypes"][sample],
            "api_matches_diplotype_and_phenotype": profile["diplotype"] == truth[sample] and profile["phenotype"] == ("NM" if sample == "NA18526" else "IM"),
            "other_five_drugs_abstain": len(api["analyses"]) == 6 and all(a["risk_assessment"]["risk_label"] == "Unknown" for a in api["analyses"][1:]),
            "template_fallback_truthful": any("source=template" in w for w in api["quality_metrics"]["warnings"]) and any("approval status is unresolved" in w for w in api["quality_metrics"]["warnings"]),
            "no_clinical_review_claim": "No qualified clinical expert has reviewed" in api["analyses"][0]["llm_generated_explanation"]["disclaimer"],
        }
        results.append({"sample": sample, "independent_truth": truth[sample], "observed_reference_calls": sum(r["GT"] == [0, 0] for r in evidence["records"]),
            "DP_range": [min(r["DP"] for r in evidence["records"]), max(r["DP"] for r in evidence["records"])],
            "reference_PL_margin_min": min(r["reference_likelihood_margin"] for r in evidence["records"] if r["GT"] == [0, 0]),
            "variant_GQ_min": min(r["GQ"] for r in evidence["records"] if r["GT"] != [0, 0]),
            "pharmcat_source_diplotypes": raw["sourceDiplotypes"], "parser_diplotype": parsed["diplotype"],
            "api_profile": profile, "api_label": api["analyses"][0]["risk_assessment"]["risk_label"],
            "api_recommendation": api["analyses"][0]["clinical_recommendation"], "checks": checks,
            "discrepancy_classification": "none_in_evaluated_CYP2C19_path" if all(checks.values()) else "investigate_failed_checks"})
    save("truth-comparison.json", {"results": results, "passed": sum(sum(r["checks"].values()) for r in results),
        "total": sum(len(r["checks"]) for r in results), "independent_per_base_truth_available": False,
        "clinical_expert_review": "NOT_OBTAINED", "scope": "two real controls, one gene/drug pathway; not clinical validation"})
    assert all(all(r["checks"].values()) for r in results), "Stop: investigate discrepancy; do not fix production"
    print("24/24 real-result integrity, truth, parser, eligibility and explanation checks passed")


if __name__ == "__main__":
    main()
