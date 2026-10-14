"""Copy the frozen fixed candidate and the hash-verified public benchmark cache.

Usage: prepare_evaluation_copy.py <copy-root outside the repository>

Candidate = the Prompt 7 finite inventory (433 intended + 4 pinned external
artifacts) plus this task's two new regression-test files, copied from the
current working tree. The 208 cached PharmCAT reports and genomic slices are
verified against the frozen benchmark/report manifests before reuse. No caller
is run here and nothing is downloaded.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
A = D.parent
R = A.parents[1]
C = Path(sys.argv[1]).resolve()
assert R not in C.parents, 'the evaluation copy must live outside the repository'
assert not C.exists(), 'evaluation copy already exists; preserve the first run'
C.mkdir(parents=True)
sys.path.insert(0, str(R / 'scripts'))
from compatible_bundle import application_core_hash  # noqa: E402


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


inventory = json.loads((R / 'audit-output/2026-10-05-prompt7-5b236070c2/candidate-inventory.json').read_text())
new_files = ['backend/tests/test_disclosure_wording.py', 'app/test/disclosure_wording_test.dart']
paths = sorted({e['path'] for e in inventory} | set(new_files))
copied = []
for rel in paths:
    src, dst = R / rel, C / rel
    assert src.is_file(), rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_symlink():
        dst.symlink_to(src.readlink())
    else:
        shutil.copy2(src, dst)
    assert sha(dst) == sha(src), rel
    copied.append(dict(path=rel, bytes=src.stat().st_size, sha256=sha(src), symlink=src.is_symlink()))

bench = R / 'test-data/benchmark/external'
manifest = json.loads((bench / 'benchmark_manifest.json').read_text())
reports = json.loads((bench / 'pharmcat_report_manifest.json').read_text())
assert reports['report_count'] == len(reports['reports']) == 208
assert sha(R / manifest['genomic']['combined_path']) == manifest['genomic']['combined_sha256'] == reports['source_vcf_sha256']
assert sha(R / manifest['truth']['local_path']) == manifest['truth']['sha256']
assert sha(bench / 'sample_gene_truth.tsv') == manifest['sample_gene_truth_sha256']
assert sha(bench / 'cohort_lock.json') == manifest['cohort_lock_sha256']
assert sha(bench / 'protocol.json') == manifest['protocol_sha256']
for subdir in ('genomic', 'pharmcat_reports'):
    shutil.copytree(bench / subdir, C / 'test-data/benchmark/external' / subdir, dirs_exist_ok=True)
for part in manifest['genomic']['slices']:
    path = C / part['local_path']
    assert path.stat().st_size == part['bytes'] and sha(path) == part['sha256']
    assert sha(Path(str(path) + '.tbi')) == part['index_sha256']
combined = C / manifest['genomic']['combined_path']
assert sha(combined) == manifest['genomic']['combined_sha256']
assert sha(Path(str(combined) + '.tbi')) == manifest['genomic']['combined_index_sha256']
for record in reports['reports']:
    path = C / record['local_cache_path']
    assert path.stat().st_size == record['bytes'] and sha(path) == record['sha256'], record['sample_id']
assert len(list((C / 'test-data/benchmark/external/pharmcat_reports').glob('*.report.json'))) == 208
core_repo, core_copy = application_core_hash(R), application_core_hash(C)
assert core_repo == core_copy, (core_repo, core_copy)

(D / 'evaluation-copy-inputs.json').write_text(json.dumps({
    'copy_root': str(C), 'candidate_files': len(copied), 'new_files_in_this_task': new_files,
    'copied_candidate': copied,
    'application_core_sha256_repo_and_copy': core_repo,
    'historical_benchmark_id': manifest['benchmark_id'],
    'frozen_protocol_sha256': manifest['protocol_sha256'],
    'frozen_truth_workbook_sha256': manifest['truth']['sha256'],
    'frozen_truth_table_sha256': manifest['sample_gene_truth_sha256'],
    'frozen_cohort_lock_sha256': manifest['cohort_lock_sha256'],
    'combined_vcf_sha256': reports['source_vcf_sha256'],
    'upstream_reports_reused_after_hash_verification': len(reports['reports']),
    'upstream_caller_executions_in_this_run': 0,
}, indent=2) + '\n')
print(json.dumps({'copy_root': str(C), 'candidate_files': len(copied),
                  'verified_cached_reports': len(reports['reports']), 'core': core_repo,
                  'new_caller_executions': 0}, indent=2))
