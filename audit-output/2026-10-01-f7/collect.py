"""F7 evidence capture only; never changes production or frozen benchmark files."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import urllib.request
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, default=str) + '\n')


def download(url, name):
    dest = OUT / name
    if dest.exists():
        return
    request = urllib.request.Request(url, headers={'User-Agent': 'PharmaGuard-F7-source-verification/1.0'})
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read()
        dest.write_bytes(content)
        record = {'url': url, 'resolved_url': response.url, 'path': name,
                  'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'bytes': len(content), 'sha256': digest(dest),
                  'last_modified': response.headers.get('Last-Modified'),
                  'etag': response.headers.get('ETag')}
    with (OUT / 'acquisition.jsonl').open('a') as f:
        f.write(json.dumps(record) + '\n')
    print('saved', name, len(content), flush=True)


def local():
    sources = [
        'test-data/benchmark/external/Consolidated_PGx-HLA_table_1-22-25-V4.xlsx',
        'test-data/benchmark/external/sample_gene_truth.tsv',
        'test-data/benchmark/external/discrepancies.tsv',
        'test-data/benchmark/external/protocol.json',
        'test-data/benchmark/external/benchmark_manifest.json',
        'test-data/benchmark/external/pharmcat_report_manifest.json',
        'audit-output/2026-09-26/derived/NA18861.1000G2022.vcf',
        'audit-output/2026-09-26/derived/NA18861.1000G2022.vcf.gz',
        'audit-output/2026-09-26/derived/NA18861.raw-required-sites.vcf',
        'audit-output/2026-09-26/originals/NA18861.preprocessed.vcf',
        'audit-output/2026-09-26/originals/PharmCAT_tutorial_get-rm_wgs_30x_grch38.NA18861.vcf.bgz',
        'audit-output/2026-09-26/api/NA18861-1000G2022.analyze.json',
        'audit-output/2026-09-26/api/NA18861-1000G2022.coverage.json',
        'audit-output/2026-09-26/acquisition.json',
        'audit-output/2026-09-26/derived-inputs.json',
        'audit-output/2026-09-26/classified-comparisons.json',
        'backend/app/data/position_requirements.json',
    ]
    sources += [f'test-data/benchmark/external/pharmcat_reports/locked_cohort.NA18861.{suffix}'
                for suffix in ('report.json', 'match.json', 'phenotype.json', 'match_warnings.txt')]
    snapshot = OUT / 'frozen-local'
    snapshot.mkdir(exist_ok=True)
    records = []
    for relative in sources:
        src = ROOT / relative
        dst = snapshot / src.name
        if dst.exists():
            assert digest(src) == digest(dst), f'Frozen artifact differs: {src}'
        else:
            shutil.copyfile(src, dst)
        records.append({'source': relative, 'snapshot': str(dst.relative_to(OUT)),
                        'sha256': digest(dst), 'bytes': dst.stat().st_size})
    jar = ROOT / 'test-data/reference/tools/pharmcat-3.4.0-all.jar'
    with zipfile.ZipFile(jar) as z:
        member = 'org/pharmgkb/pharmcat/definition/alleles/SLCO1B1_translation.json'
        dest = OUT / 'pinned-SLCO1B1_translation.json'
        if not dest.exists():
            dest.write_bytes(z.read(member))
        records.append({'source': str(jar.relative_to(ROOT)), 'jar_sha256': digest(jar),
                        'member': member, 'snapshot': dest.name, 'sha256': digest(dest)})
    save('local-evidence.json', records)
    diff = subprocess.check_output(['git', 'diff', '--binary'], cwd=ROOT)
    save('starting-working-tree.json', {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'tracked_diff_sha256': hashlib.sha256(diff).hexdigest(),
         'status': subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
         'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()})
    print('Local evidence frozen', flush=True)


def online():
    urls = {
        'cdc-reference-materials.html': 'https://www.cdc.gov/lab-quality/php/get-rm/reference-materials.html',
        'current-Consolidated_PGx-HLA_table_1-22-25-V4.xlsx': 'https://www.cdc.gov/lab-quality/media/files/2025/08/Consolidated_PGx-HLA_table_1-22-25-V4.xlsx',
        'pharmvar-SLCO1B1.html': 'https://www.pharmvar.org/gene/SLCO1B1',
        'PGx2-genes-alleles-tested.pdf': 'https://www.cdc.gov/lab-quality/media/pdfs/2024/08/PGx2-genes-alleles-tested.pdf',
        'tutorial-article.html': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC10121724/',
        'getrm-2016-article.html': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC4695224/',
        'ena-ERR1955362.tsv': 'https://www.ebi.ac.uk/ena/portal/api/filereport?accession=ERR1955362&result=read_run&fields=run_accession,sample_accession,sample_alias,submitted_ftp,submitted_md5,submitted_bytes,fastq_ftp,fastq_md5&format=tsv',
        'ena-PRJEB31736.tsv': 'https://www.ebi.ac.uk/ena/portal/api/filereport?accession=PRJEB31736&result=read_run&fields=run_accession,sample_accession,sample_alias,submitted_ftp,submitted_md5,submitted_bytes&format=tsv',
    }
    for name, url in urls.items():
        try:
            download(url, name)
        except Exception as e:
            print('FAILED', name, repr(e), flush=True)
    for name in ('pharmvar-SLCO1B1.html', 'cdc-reference-materials.html'):
        path = OUT / name
        if path.exists():
            links = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', path.read_text())
            print(name, [u for u in links if any(x in u.lower() for x in ('slco','consolidated','pgx2','changelog'))], flush=True)


if __name__ == '__main__':
    import sys
    {'local': local, 'online': online}[sys.argv[1]]()
