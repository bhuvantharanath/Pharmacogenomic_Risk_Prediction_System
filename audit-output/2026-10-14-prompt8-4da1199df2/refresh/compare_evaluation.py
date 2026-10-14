"""Compare the fresh 208-individual application rerun with preserved evidence.

Usage: compare_evaluation.py <copy-root>
Compared with (1) the historical benchmark outputs in test-data/benchmark/external
and (2) the immediately previous versioned evaluation (2026-10-04). Nothing is
normalised except the documented generation timestamp and the per-row temporary
single-sample VCF hash (bcftools writes the absolute source path into a header).
"""
import collections
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
R = D.parents[2]
C = Path(sys.argv[1]).resolve()
B = 'test-data/benchmark/external/'
PREV = R / 'test-data/benchmark/current-candidate-2026-10-04'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


old = json.loads((R / (B + 'external_benchmark_results.json')).read_text())
new = json.loads((C / (B + 'external_benchmark_results.json')).read_text())
prev = json.loads((PREV / 'external_benchmark_results.json').read_text())
strip = lambda d: {k: v for k, v in d.items() if k != 'generated_at'}
assert strip(old) == strip(new) == strip(prev)
assert old['cohort_samples'] == new['cohort_samples'] == 208
assert old['sample_gene_truth_rows'] == new['sample_gene_truth_rows'] == 1456
assert old['truth_status_counts']['evaluable'] == new['truth_status_counts']['evaluable'] == 596
assert old['pharmcat_reports'] == new['pharmcat_reports'] == 208


def rows(path: Path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def differing(before, after):
    assert len(before) == len(after) == 1456
    counter, samples = collections.Counter(), set()
    for a, b in zip(before, after):
        assert (a['sample_id'], a['gene']) == (b['sample_id'], b['gene'])
        for key in a:
            if a[key] != b[key]:
                counter[key] += 1
                samples.add(a['sample_id'])
    return dict(counter), samples


vs_hist, hist_samples = differing(rows(R / (B + 'input_eligibility.tsv')), rows(C / (B + 'input_eligibility.tsv')))
vs_prev, _ = differing(rows(PREV / 'input_eligibility.tsv'), rows(C / (B + 'input_eligibility.tsv')))
assert vs_hist == {'vcf_sha256': 1456}, vs_hist
assert vs_prev == {'vcf_sha256': 1456}, vs_prev
assert len(hist_samples) == 208
for name in ('exclusions.tsv', 'discrepancies.tsv', 'sample_gene_truth.tsv', 'cohort_lock.json',
             'pharmcat_report_manifest.json'):
    assert digest(R / (B + name)) == digest(C / (B + name)), name
for name in ('exclusions.tsv', 'discrepancies.tsv'):
    assert digest(PREV / name) == digest(C / (B + name)), name
assert digest(R / 'reports/external_analytical_benchmark.md') == digest(C / 'reports/external_analytical_benchmark.md')

# Representative same-input projection: the path-bearing bcftools header is the
# only expected difference between the repository path and the isolated copy.
source_manifest = json.loads((R / (B + 'benchmark_manifest.json')).read_text())
sample = 'HG00111'
positions = R / 'test-data/reference/tools/pharmcat_positions_3.4.0.vcf.bgz'
projections = []
for label, root in (('historical-path', R), ('isolated-path', C)):
    source = root / source_manifest['genomic']['combined_path']
    target = D / (label + '.' + sample + '.vcf')
    run = subprocess.run(['bcftools', 'view', '-R', str(positions), '-s', sample,
                          '-Ov', '-o', str(target), str(source)], capture_output=True)
    assert run.returncode == 0, run.stderr.decode(errors='replace')
    lines = target.read_text().splitlines()
    projections.append(dict(label=label, path=target.name, sha256=digest(target),
                            command_lines=[x for x in lines if x.startswith('##bcftools_viewCommand=')],
                            records=[x for x in lines if not x.startswith('#')],
                            all_lines_except_command=[x for x in lines if not x.startswith('##bcftools_viewCommand=')]))
assert projections[0]['sha256'] != projections[1]['sha256']
assert projections[0]['all_lines_except_command'] == projections[1]['all_lines_except_command']
assert projections[0]['records'] == projections[1]['records']

summary = dict(
    historical_benchmark_id=old['benchmark_id'],
    historical_generated_at=old['generated_at'],
    previous_evaluation='pharmaguard-external-current-candidate-v2-2026-10-04',
    previous_generated_at=prev['generated_at'],
    new_generated_at=new['generated_at'],
    individuals=208, sample_gene_rows=1456, evaluable_truth_rows=596,
    all_metric_fields_equal_except_generation_time=True,
    equal_to_previous_evaluation_except_generation_time=True,
    eligibility_rows=1456, differing_eligibility_fields=vs_hist,
    differing_eligibility_fields_vs_previous_evaluation=vs_prev,
    individuals_with_vcf_sha_difference=len(hist_samples),
    exclusions_sha256=digest(C / (B + 'exclusions.tsv')),
    discrepancies_sha256=digest(C / (B + 'discrepancies.tsv')),
    report_manifest_sha256=digest(C / (B + 'pharmcat_report_manifest.json')),
    representative_projection=[{k: v for k, v in p.items() if k not in ('records', 'all_lines_except_command')}
                               for p in projections],
    representative_projection_record_count=len(projections[0]['records']),
    representative_biological_records_equal=True,
    interpretation=('The fixed candidate changed only user-facing wording and UI state. Its '
                    'application rerun over the same 208 individuals reproduces every scored metric, '
                    'exclusion and discrepancy of both the historical benchmark and the 2026-10-04 '
                    'evaluation. The only differing eligibility field is the hash of each regenerated '
                    'single-sample VCF, explained by the path-bearing bcftools header shown in the '
                    'representative projection. No new genotype concordance or clinical claim follows.'),
)
(D / 'evaluation-comparison.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k: summary[k] for k in ('individuals', 'sample_gene_rows', 'evaluable_truth_rows',
                                           'all_metric_fields_equal_except_generation_time',
                                           'differing_eligibility_fields',
                                           'differing_eligibility_fields_vs_previous_evaluation',
                                           'representative_biological_records_equal')}, indent=2))
