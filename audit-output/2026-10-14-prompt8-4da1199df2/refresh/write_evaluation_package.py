"""Publish the new versioned evaluation without touching historical evidence.

Usage: write_evaluation_package.py <copy-root>
Writes test-data/benchmark/current-candidate-2026-10-14/ (schema 2, same
structure the bundle verifier already checks). The 2026-10-04 package and the
historical benchmark are left byte-identical.
"""
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

D = Path(__file__).resolve().parent
R = D.parents[2]
C = Path(sys.argv[1]).resolve()
REL = 'test-data/benchmark/current-candidate-2026-10-14'
EVAL_ID = 'pharmaguard-external-current-candidate-v3-2026-10-14'
P = R / REL
assert not P.exists(), 'versioned evidence package already exists'
B = 'test-data/benchmark/external/'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def ref(path: str) -> dict:
    p = R / path
    return {'path': path, 'bytes': p.stat().st_size, 'sha256': sha(p)}


inputs = json.loads((D / 'evaluation-copy-inputs.json').read_text())
frozen = {row['path']: row for row in inputs['copied_candidate']}
for path in (B + 'protocol.json', B + 'benchmark_manifest.json', B + 'cohort_lock.json',
             B + 'sample_gene_truth.tsv', B + 'pharmcat_report_manifest.json',
             B + 'external_benchmark_results.json'):
    assert ref(path)['sha256'] == frozen[path]['sha256'], path

commands = json.loads((D / 'commands.json').read_text())
stages = [x for x in commands if x['name'] in {
    'prepare-evaluation-copy', 'cohort-prepare', 'cohort-fetch-resume',
    'cohort-evaluate-resume', 'compare-evaluation', 'f4-fresh-replay'}]
assert len(stages) == 6 and all(x['exit_code'] == 0 for x in stages)

P.mkdir(parents=True)
outputs = {
    'raw_benchmark_manifest.json': B + 'benchmark_manifest.json',
    'external_benchmark_results.json': B + 'external_benchmark_results.json',
    'input_eligibility.tsv': B + 'input_eligibility.tsv',
    'exclusions.tsv': B + 'exclusions.tsv',
    'discrepancies.tsv': B + 'discrepancies.tsv',
    'raw_scoring_report.md': 'reports/external_analytical_benchmark.md',
}
for name, src in outputs.items():
    shutil.copy2(C / src, P / name)
shutil.copy2(D / 'evaluation-comparison.json', P / 'evaluation-comparison.json')
shutil.copy2(D / 'f4-fresh-replay.json', P / 'f4-fresh-replay.json')
(P / 'stage-command-receipts.json').write_text(json.dumps(stages, indent=2) + '\n')

result = json.loads((P / 'external_benchmark_results.json').read_text())
raw = json.loads((P / 'raw_benchmark_manifest.json').read_text())
source = json.loads((R / (B + 'benchmark_manifest.json')).read_text())
comparison = json.loads((P / 'evaluation-comparison.json').read_text())
f4 = json.loads((P / 'f4-fresh-replay.json').read_text())
sys.path.insert(0, str(C / 'scripts'))
from compatible_bundle import application_core_hash  # noqa: E402
assert raw['local_production_artifact_sha256'] == application_core_hash(C) == application_core_hash(R)
assert raw['protocol_sha256'] == source['protocol_sha256']
assert result['cohort_samples'] == 208 and result['sample_gene_truth_rows'] == 1456
assert result['truth_status_counts']['evaluable'] == 596 and result['pharmcat_reports'] == 208
assert comparison['all_metric_fields_equal_except_generation_time']
assert all(row['passed'] for row in f4)

lines = [
    '# Current candidate evaluation, version 3', '',
    f'Evaluation ID: `{EVAL_ID}`.',
    f"Current portable scientific core: `{raw['local_production_artifact_sha256']}`.",
    f"Historic frozen protocol: `{source['protocol_sha256']}`. Truth and cohort locks are unchanged.",
    '',
    'Why a new version: the 2026-10-14 remediation changed only user-facing wording (provenance disclaimer, CYP2D6 boundary, missing-position attribution, unusable-genotype explanation, drug-scope caption) and kept opened result rows alive while scrolling. Those files are inside the scientific-core allowlist, so the previous evaluation no longer bound the candidate. It is preserved unchanged as `current-candidate-2026-10-04/`.',
    '',
    'The 208 public-cohort PharmCAT reports were reused only after all 208 report hashes, the exact combined VCF, pinned JAR, truth table, workbook and cohort lock were checked. No new 208-person PharmCAT caller run is claimed. The application reprojected each of the 208 people and rescored all 1,456 sample-gene rows using the frozen fixed candidate in an isolated copy. The two frozen F4 read-backed VCF controls were separately replayed through the live local API and pinned caller; they are bounded positives, not a replacement for the cohort.',
    '',
    'Compared with both the historical run and the 2026-10-04 evaluation, per-gene metrics, exclusions and discrepancies are equal. The only changed field in all 1,456 eligibility rows is the temporary single-sample VCF SHA-256; a representative same-input replay shows the path-bearing bcftools command header changes the file bytes while genotype records stay identical.',
    '',
    '| Gene | Evaluable truth rows | Application eligible | Application abstention |',
    '|---|---:|---:|---:|',
]
for gene, row in result['genes'].items():
    layer = row['layer_B_application']
    lines.append(f"| {gene} | {row['truth_evaluable']} | {layer['input_eligible']['numerator']} | {layer['abstention']['numerator']} |")
lines += [
    '',
    'The source VCF is polymorphic-filtered. Missing required coordinates remain unknown. Independent phenotype and actionability truth are unavailable in this cohort, so false reassurance and false warning are not estimable. No pooled accuracy or clinical utility claim follows. The F4 read-backed controls cover only the qualified CYP2C19/clopidogrel path; ACS/PCI is a guideline qualifier, not a donor diagnosis.',
    '',
    'Current generated explanations remain unapproved and use deterministic runtime fallback. Human adjudication is outstanding; this evaluation does not close the release gate.',
]
(P / 'EVALUATION-REPORT.md').write_text('\n'.join(lines) + '\n')

package_refs = [ref(REL + '/' + name) for name in sorted(p.name for p in P.iterdir() if p.is_file())]
manifest = {
    'schema_version': 2,
    'evaluation_id': EVAL_ID,
    'created_at': datetime.now(timezone.utc).isoformat(),
    'candidate_application_core_sha256': raw['local_production_artifact_sha256'],
    'application_hash_policy_version': 2,
    'base_head_metadata_only': (R / '.git/HEAD').exists() and __import__('subprocess').run(
        ['git', 'rev-parse', 'HEAD'], cwd=R, capture_output=True, text=True).stdout.strip(),
    'previous_evaluation': ref('test-data/benchmark/current-candidate-2026-10-04/evaluation_manifest.json'),
    'historical_benchmark_id': source['benchmark_id'],
    'frozen_protocol': ref(B + 'protocol.json'),
    'frozen_cohort_lock': ref(B + 'cohort_lock.json'),
    'independent_truth_workbook': ref(source['truth']['local_path']),
    'independent_truth_table': ref(B + 'sample_gene_truth.tsv'),
    'frozen_combined_vcf': ref(source['genomic']['combined_path']),
    'pinned_jar': ref('test-data/reference/tools/pharmcat-3.4.0-all.jar'),
    'upstream_report_manifest': ref(B + 'pharmcat_report_manifest.json'),
    'historical_benchmark_manifest': ref(B + 'benchmark_manifest.json'),
    'upstream_reuse': {
        'verified_report_count': 208,
        'new_caller_executions_for_208_person_cohort': 0,
        'source_vcf_sha256': source['genomic']['combined_sha256'],
        'report_manifest_source_vcf_sha256': json.loads((R / (B + 'pharmcat_report_manifest.json')).read_text())['source_vcf_sha256'],
        'reason': 'same hashed source VCF, pinned JAR/definitions, 208 individually verified report hashes and frozen truth',
    },
    'fresh_stages': {'application_individuals': 208, 'scored_sample_gene_rows': 1456, 'f4_local_api_cases': 2},
    'denominators': {'unique_individuals': 208, 'sample_gene_rows': 1456,
                     'truth_evaluable_rows': 596, 'pharmcat_reports': 208},
    'comparison': {'all_metrics_equal_except_generation_time': True,
                   'equal_to_previous_evaluation_except_generation_time': True,
                   'differing_eligibility_field': 'vcf_sha256',
                   'differing_eligibility_rows': 1456,
                   'representative_biological_records_equal': True},
    'outputs': package_refs,
    'self_reference': 'This manifest hashes its outputs, not itself. The bundle manifest separately hashes this file.',
    'clinical_review': 'NOT_OBTAINED',
}
(P / 'evaluation_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'package': REL, 'evaluation_id': EVAL_ID, 'outputs': len(package_refs),
                  'current_core': manifest['candidate_application_core_sha256']}, indent=2))
