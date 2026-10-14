"""F4 validation-only preparation. Never import this into production."""
from pathlib import Path
import datetime
import csv
import gzip
import hashlib
import json
import subprocess
import sys
import urllib.request

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
SAMPLES = {"NA18526": "ERR3239353", "NA12878": "ERR3239334"}
REF_MD5 = "c0eeee7acfdaf31b770a509bdaa6e51a"


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def download(url, path):
    if not path.exists():
        with urllib.request.urlopen(url, timeout=90) as response, path.open("wb") as dest:
            while block := response.read(1024 * 1024):
                dest.write(block)
    return {"url": url, "path": str(path.relative_to(OUT)), "bytes": path.stat().st_size,
            "sha256": digest(path), "md5": digest(path, "md5")}


def acquire():
    import pysam
    records = []
    for sample, run in SAMPLES.items():
        base = f"https://ftp.sra.ebi.ac.uk/vol1/run/ERR323/{run}/{sample}.final.cram"
        meta_url = ("https://www.ebi.ac.uk/ena/portal/api/filereport?accession=" + run +
                    "&result=read_run&fields=run_accession,sample_accession,submitted_ftp,submitted_md5,submitted_bytes&format=tsv")
        records.append(download(meta_url, OUT / f"{sample}.ena.tsv"))
        idx = OUT / f"{sample}.final.cram.crai"
        records.append(download(base + ".crai", idx))
        fields = (OUT / f"{sample}.ena.tsv").read_text().splitlines()[1].split("\t")
        assert digest(idx, "md5") == fields[3].split(";")[1]
        with pysam.AlignmentFile(base, "rc", index_filename=str(idx)) as reads:
            header = reads.header.to_dict()
            assert {r["SM"] for r in header["RG"]} == {sample}
            assert next(s for s in header["SQ"] if s["SN"] == "chr10")["M5"] == REF_MD5
            save(f"{sample}.header.json", header)
    reference_url = ("https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/"
                     "GRCh38_reference_genome/GRCh38_full_analysis_set_plus_decoy_hla.fa")
    index = OUT / "source-reference.fa.fai"
    records.append(download(reference_url + ".fai", index))
    fields = next(l.split("\t") for l in index.read_text().splitlines() if l.startswith("chr10\t"))
    length, offset, line_bases, line_bytes = map(int, fields[1:])
    end = offset + ((length - 1) // line_bases) * line_bytes + (length - 1) % line_bases
    raw = OUT / "exact-reference-chr10.range"
    if not raw.exists():
        request = urllib.request.Request(reference_url, headers={"Range": f"bytes={offset}-{end}"})
        with urllib.request.urlopen(request, timeout=90) as response, raw.open("wb") as dest:
            assert response.status == 206, "Server must honor the bounded reference range"
            while block := response.read(1024 * 1024):
                dest.write(block)
    assert raw.stat().st_size == end - offset + 1
    records.append({"url": reference_url, "range": f"bytes={offset}-{end}", "path": raw.name,
                    "sha256": digest(raw), "bytes": raw.stat().st_size})
    sequence = b"".join(raw.read_bytes().split()).upper()
    assert len(sequence) == 133797422
    assert hashlib.md5(sequence).hexdigest() == REF_MD5
    reference = OUT / "GRCh38.chr10.fa"
    with reference.open("wb") as f:
        f.write(b">chr10\n")
        for start in range(0, len(sequence), 60):
            f.write(sequence[start:start + 60] + b"\n")
    pysam.faidx(str(reference))
    records.append({"path": reference.name, "sha256": digest(reference),
                    "sequence_md5": REF_MD5, "description": "Exact complete chr10 sequence matching both CRAM M5 headers, FASTA wrapped at 60."})
    save("acquisition.json", {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "artifacts": records})
    print("Reference and metadata acquired; no genotypes called.", flush=True)


def freeze():
    import pysam
    assert not (OUT / "frozen-protocol.json").exists(), "Never overwrite a freeze"
    reference = OUT / "GRCh38.chr10.fa"
    with pysam.FastaFile(str(reference)) as f:
        assert hashlib.md5(f.fetch("chr10").encode()).hexdigest() == REF_MD5
    requirements = ROOT / "backend/app/data/position_requirements.json"
    positions = json.loads(requirements.read_text())["genes"]["CYP2C19"]["positions"]
    assert len(positions) == 35
    workbook = ROOT / "test-data/benchmark/external/Consolidated_PGx-HLA_table_1-22-25-V4.xlsx"
    assert digest(workbook) == "c66174befa7a7bbb6cfaf174cc500a269565407807467204bd7bc6eaae3be109"
    truth_path = ROOT / "test-data/benchmark/external/sample_gene_truth.tsv"
    with truth_path.open() as f:
        truth = [r for r in csv.DictReader(f, delimiter="\t") if r["sample_id"] in SAMPLES and r["gene"] == "CYP2C19"]
    assert {r["sample_id"]: r["truth_raw"] for r in truth} == {"NA18526": "*1/*1", "NA12878": "*1/*2"}
    region = ["chr10", min(p[1] for p in positions) - 1000, max(p[1] for p in positions) + 1000]
    files = [OUT / "PROTOCOL.md", reference, requirements, workbook, truth_path,
             ROOT / "backend/app/data/compatible_bundle.json", ROOT / "test-data/reference/tools/pharmcat-3.4.0-all.jar"]
    value = {"frozen_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "protocol_version": 1,
             "before_genotype_calling": True, "before_application_scoring": True,
             "samples": SAMPLES, "truth": truth, "positions": positions, "region_1based_inclusive": region,
             "reference_sequence_md5": REF_MD5,
             "independent_predicted_phenotypes": {"NA18526": "Normal Metabolizer", "NA12878": "Intermediate Metabolizer"},
             "hashes": {str(p.relative_to(ROOT)): digest(p) for p in files},
             "bcftools": subprocess.check_output(["bcftools", "--version"], text=True),
             "pysam": pysam.__version__, "samtools": pysam.__samtools_version__,
             "acquisition": json.loads((OUT / "acquisition.json").read_text())}
    save("frozen-protocol.json", value)
    (OUT / "frozen-protocol.sha256").write_text(digest(OUT / "frozen-protocol.json") + "\n")
    print("FROZEN", digest(OUT / "frozen-protocol.json"), flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["acquire"]:
        acquire()
    elif sys.argv[1:] == ["freeze"]:
        freeze()
    else:
        raise SystemExit("Usage: prepare.py acquire")
