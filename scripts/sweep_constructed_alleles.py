"""
Every named allele of the seven genes, constructed and run through the pipeline.

WHAT THIS IS, AND IS NOT

**Coverage testing, not external validation.** Each input is built FROM
PharmCAT's own allele definitions and then handed back to PharmCAT, so agreement
shows the pipeline round-trips its own definitions — it does not show the
definitions are right, and it is not evidence about real patient data. The only
external check this project has is n=1 (`NA12273`), and this does not add to it.

What it can find, which is worth finding:

  * an allele that never calls at all, so a real carrier would silently fall
    through to something else;
  * an allele that calls as a DIFFERENT allele, which would be a wrong answer
    given a perfect input;
  * a call whose risk label the CPIC mapping does not support.

Every input is complete-coverage — all seven genes emitted, the target gene at
`allele/allele` and the rest at reference — so the coverage gate never fires and
a decline means something else went wrong.

CYP2D6 IS EXPECTED TO FAIL EVERY ALLELE. It is not called from an unphased VCF
by design (copy-number and structural variation cannot be expressed), so its 172
alleles are swept and reported separately rather than counted as defects. A
sweep that quietly excluded it would be measuring a smaller system than the one
that ships.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JAR = REPO / "test-data/reference/tools/pharmcat-3.4.0-all.jar"
GENERATOR = REPO / "test-data/generate_synthetic_vcf.py"
DEF_PREFIX = "org/pharmgkb/pharmcat/definition/alleles/"

GENES = ("CYP2C19", "CYP2C9", "CYP2D6", "DPYD", "NUDT15", "SLCO1B1", "TPMT")

#: Not called from VCF by design; swept and reported, never counted as failure.
UNCALLABLE = {"CYP2D6"}

API = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8993"
OUT = REPO / "reports/constructed_allele_sweep.json"

#: One drug per gene, so every run also exercises the label path.
PROBE_DRUG = {
    "CYP2C19": "clopidogrel",
    "CYP2C9": "warfarin",
    "CYP2D6": "codeine",
    "DPYD": "fluorouracil",
    "NUDT15": "azathioprine",
    "SLCO1B1": "simvastatin",
    "TPMT": "azathioprine",
}


def named_alleles(gene: str) -> list[str]:
    with zipfile.ZipFile(JAR) as z:
        data = json.loads(z.read(f"{DEF_PREFIX}{gene}_translation.json"))
    return [a["name"] for a in data["namedAlleles"]]


def build_vcf(gene: str, allele: str, path: Path) -> bool:
    """Homozygous for `allele`, every other gene padded to reference."""
    others = ",".join(g for g in GENES if g != gene)
    result = subprocess.run(
        [sys.executable, str(GENERATOR),
         "--from-jar", str(JAR),
         "--diplotype", f"{gene}={allele}/{allele}",
         "--pad-genes", others,
         "--sample", "SWEEP",
         "-o", str(path)],
        capture_output=True, text=True)
    return result.returncode == 0 and path.exists() and path.stat().st_size > 0


def analyse(vcf: Path, drug: str) -> tuple[int, dict]:
    boundary = "----pgsweep"
    body = f"--{boundary}\r\n".encode()
    body += (f'Content-Disposition: form-data; name="file"; '
             f'filename="{vcf.name}"\r\n').encode()
    body += b"Content-Type: text/plain\r\n\r\n" + vcf.read_bytes() + b"\r\n"
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="drugs"\r\n\r\n{drug}\r\n'.encode()
    body += f"--{boundary}--\r\n".encode()

    request = urllib.request.Request(
        f"{API}/analyze", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw[:300]}


def called_diplotype(payload: dict, gene: str) -> tuple[str | None, str | None]:
    """
    The diplotype and phenotype the pipeline reported for `gene`.

    The profile is PER ANALYSIS, keyed by `primary_gene` — not a top-level list
    of gene calls. Reading it from the wrong place returned (None, None) for
    every allele, which would have scored the entire sweep as "no_call" and
    looked like a catastrophic finding rather than a broken harness.
    """
    for analysis in payload.get("analyses") or []:
        profile = analysis.get("pharmacogenomic_profile") or {}
        if profile.get("primary_gene") == gene:
            return profile.get("diplotype"), profile.get("phenotype")
    return None, None


def primary_gene(payload: dict) -> str | None:
    """Whichever gene the pipeline reported as driving the recommendation."""
    for analysis in payload.get("analyses") or []:
        profile = analysis.get("pharmacogenomic_profile") or {}
        if profile.get("primary_gene"):
            return profile["primary_gene"]
    return None


def main() -> None:
    scratch = Path("/tmp/pg_sweep"); scratch.mkdir(exist_ok=True)
    results: list[dict] = []
    started = time.time()

    for gene in GENES:
        alleles = named_alleles(gene)
        print(f"\n=== {gene}: {len(alleles)} alleles ===", flush=True)
        for i, allele in enumerate(alleles, 1):
            vcf = scratch / f"{gene}_{i}.vcf"
            record: dict = {"gene": gene, "allele": allele}

            if not build_vcf(gene, allele, vcf):
                record["outcome"] = "generator_failed"
                results.append(record)
                print(f"  [{i:3d}/{len(alleles)}] {allele:24s} GENERATOR FAILED",
                      flush=True)
                continue

            status, payload = analyse(vcf, PROBE_DRUG[gene])
            record["http"] = status

            if status != 200:
                record["outcome"] = "http_error"
                record["detail"] = str(payload)[:200]
            else:
                diplotype, phenotype = called_diplotype(payload, gene)
                record["called"] = diplotype
                record["phenotype"] = phenotype
                analyses = payload.get("analyses") or []
                if analyses:
                    risk = analyses[0].get("risk_assessment") or {}
                    record["label"] = risk.get("risk_label")
                    record["confidence"] = risk.get("confidence_score")

                expected = f"{allele}/{allele}"
                record["primary_gene"] = primary_gene(payload)
                if diplotype is None:
                    # NOT necessarily a no-call. Azathioprine is governed by
                    # BOTH TPMT and NUDT15, and the pipeline reports whichever
                    # gene drives the recommendation as `primary_gene`. With a
                    # normal-function NUDT15 allele, TPMT dominates and NUDT15
                    # never appears — so asking only for NUDT15 scored nine
                    # correct results as failures. The pipeline was right; the
                    # harness was asking the wrong question.
                    record["outcome"] = (
                        "other_gene_primary"
                        if record["primary_gene"] and record["primary_gene"] != gene
                        else "no_call")
                elif diplotype == expected:
                    record["outcome"] = "exact"
                else:
                    record["outcome"] = "different_call"

            results.append(record)
            vcf.unlink(missing_ok=True)
            if i % 10 == 0 or record["outcome"] != "exact":
                print(f"  [{i:3d}/{len(alleles)}] {allele:24s} "
                      f"{record['outcome']:16s} {record.get('called') or ''}",
                      flush=True)

    OUT.write_text(json.dumps({
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - started, 1),
        "api": API,
        "nature": "coverage testing against PharmCAT's own definitions — "
                  "NOT external validation",
        "uncallable_by_design": sorted(UNCALLABLE),
        "results": results,
    }, indent=2))
    print(f"\nwrote {OUT}  ({len(results)} alleles, "
          f"{time.time() - started:.0f}s)")


if __name__ == "__main__":
    main()
