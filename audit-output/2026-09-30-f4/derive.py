"""Apply the frozen validation protocol; never synthesize a genotype or row."""
from pathlib import Path
import datetime
import json
import subprocess
import sys
from prepare import OUT, ROOT, digest, save


def quality_reasons(gt, dp, gq, reference_pl):
    reasons = []
    if gt is None or len(gt) != 2 or any(x is None for x in gt):
        reasons.append("incomplete_GT")
    if dp is None or dp < 10:
        reasons.append("DP_below_10_or_missing")
    if gt == (0, 0):
        if (not reference_pl or len(reference_pl) < 2 or
                any(x is None for x in reference_pl) or
                min(reference_pl[1:]) - reference_pl[0] < 20):
            reasons.append("reference_PL_margin_below_20_or_missing")
        if gq is not None and gq < 20:
            reasons.append("GQ_below_20")
    elif gq is None or gq < 20:
        reasons.append("variant_GQ_below_20_or_missing")
    return reasons


def run(command, log_name):
    commands = OUT / "commands.jsonl"
    with commands.open("a") as f:
        f.write(json.dumps({"at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "command": command}) + "\n")
    with (OUT / log_name).open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)


def main():
    import pysam
    frozen = OUT / "frozen-protocol.json"
    assert digest(frozen) == (OUT / "frozen-protocol.sha256").read_text().strip()
    protocol = json.loads(frozen.read_text())
    for name, expected in protocol["hashes"].items():
        assert digest(ROOT / name) == expected, f"Frozen artifact changed: {name}"
    assert "1.24" in subprocess.check_output(["bcftools", "--version"], text=True).splitlines()[0]
    reference = str(OUT / "GRCh38.chr10.fa")
    chrom, first, last = protocol["region_1based_inclusive"]
    region = f"{chrom}:{first}-{last}"
    required = set(map(tuple, protocol["positions"]))
    for sample, accession in protocol["samples"].items():
        assert not (OUT / f"{sample}.observed.vcf").exists(), "Do not overwrite prior observations"
        bam = OUT / f"{sample}.CYP2C19.bam"
        url = f"https://ftp.sra.ebi.ac.uk/vol1/run/ERR323/{accession}/{sample}.final.cram"
        if bam.exists():
            receipt_path = OUT / f"{sample}.extraction.json"
            assert receipt_path.exists(), "Incomplete extraction: preserve it and restart in a fresh directory"
            receipt = json.loads(receipt_path.read_text())
            assert digest(bam) == receipt["sha256"]
            assert digest(Path(str(bam) + ".bai")) == receipt["index_sha256"]
            assert receipt["reference_sha256"] == digest(Path(reference))
            assert receipt["frozen_protocol_sha256"] == digest(frozen)
        if not bam.exists():
            with pysam.AlignmentFile(url, "rc", reference_filename=reference,
                    index_filename=str(OUT / f"{sample}.final.cram.crai")) as source:
                assert {r["SM"] for r in source.header.to_dict()["RG"]} == {sample}
                n = 0
                with pysam.AlignmentFile(str(bam), "wb", template=source) as target:
                    for record in source.fetch(chrom, first - 1, last):
                        target.write(record)
                        n += 1
            pysam.index(str(bam))
            save(f"{sample}.extraction.json", {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "url": url, "method": "pysam.AlignmentFile.fetch, unchanged read records",
                "region_0based_half_open": [chrom, first - 1, last], "records": n,
                "sha256": digest(bam), "index_sha256": digest(Path(str(bam) + ".bai")),
                "reference_sha256": digest(Path(reference)), "frozen_protocol_sha256": digest(frozen)})
            print(sample, "read slice", n, "records", flush=True)
        pileup = OUT / f"{sample}.pileup.bcf"
        calls = OUT / f"{sample}.calls.vcf"
        normalized = OUT / f"{sample}.normalized.vcf"
        run(["bcftools", "mpileup", "-q", "20", "-Q", "20", "-d", "1000", "--ns",
             "UNMAP,SECONDARY,QCFAIL,DUP,SUPPLEMENTARY", "-a", "FORMAT/DP,FORMAT/AD", "-f", reference,
             "-r", region, "-Ob", "-o", str(pileup), str(bam)], f"{sample}.mpileup.log")
        run(["bcftools", "call", "-m", "--ploidy", "2", "-a", "FORMAT/GQ", "-Ov", "-o", str(calls), str(pileup)], f"{sample}.call.log")
        run(["bcftools", "norm", "-f", reference, "-Ov", "-o", str(normalized), str(calls)], f"{sample}.norm.log")
        likelihoods = {}
        with pysam.VariantFile(str(pileup)) as data:
            for record in data:
                if (record.contig, record.pos) in required and not record.info.get("INDEL", False):
                    likelihoods[(record.contig, record.pos)] = record.samples[sample].get("PL")
        evidence = []
        with pysam.VariantFile(str(normalized)) as source:
            source.header.filters.add("F4EvidenceFail", None, None, "Failed frozen F4 observed-evidence quality policy v1")
            source.header.add_line("##F4ProtocolSHA256=" + digest(frozen))
            with pysam.VariantFile(str(OUT / f"{sample}.observed.vcf"), "w", header=source.header) as target:
                for record in source:
                    if (record.contig, record.pos) not in required:
                        continue
                    call = record.samples[sample]
                    gt, dp, gq = call.get("GT"), call.get("DP"), call.get("GQ")
                    pl = likelihoods.get((record.contig, record.pos))
                    reasons = quality_reasons(gt, dp, gq, pl)
                    original = str(record).split("\t")
                    record.filter.clear()
                    record.filter.add("F4EvidenceFail" if reasons else "PASS")
                    after = str(record).split("\t")
                    assert original[:6] + original[7:] == after[:6] + after[7:], "Only FILTER may change"
                    target.write(record)
                    evidence.append({"chrom": record.contig, "position": record.pos, "ref": record.ref,
                        "alt": record.alts, "GT": gt, "DP": dp, "GQ": gq, "AD": call.get("AD"),
                        "QUAL": record.qual, "original_pileup_PL": pl,
                        "reference_likelihood_margin": min(pl[1:]) - pl[0] if pl and len(pl) > 1 else None,
                        "FILTER": list(record.filter), "reasons": reasons})
        covered = {(r["chrom"], r["position"]) for r in evidence}
        save(f"{sample}.evidence.json", {"sample": sample, "records": evidence,
            "missing_positions": sorted(required - covered),
            "passing_positions": sum(all(not x["reasons"] for x in evidence if (x["chrom"], x["position"]) == p) for p in covered),
            "required_positions": len(required), "observed_vcf_sha256": digest(OUT / f"{sample}.observed.vcf")})
        print(sample, "observed sites", len(covered), "failed records", sum(bool(r["reasons"]) for r in evidence), flush=True)


if __name__ == "__main__":
    main()
