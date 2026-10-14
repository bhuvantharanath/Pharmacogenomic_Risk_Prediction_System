"""Reproduce F7 from frozen evidence; no biological edits or truth relabeling."""
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
sys.path.insert(0, str(ROOT / 'backend'))
from app.pharmcat_runner import parse_report
from collect import digest, save


def main():
    frozen = OUT / 'frozen-local'
    for item in json.loads((OUT / 'local-evidence.json').read_text()):
        assert digest(OUT / item['snapshot']) == item['sha256'], item
        if 'jar_sha256' in item:
            assert digest(ROOT / item['source']) == item['jar_sha256']
        else:
            assert digest(ROOT / item['source']) == item['sha256'], item
    definition = json.loads((OUT / 'pinned-SLCO1B1_translation.json').read_text())
    alleles = {a['name']: a for a in definition['namedAlleles']}
    observed = {}
    for line in (frozen / 'NA18861.1000G2022.vcf').read_text().splitlines():
        if line.startswith('#'):
            continue
        cols = line.split('\t')
        if cols[0] == 'chr12':
            observed[int(cols[1])] = {'ref': cols[3], 'alt': cols[4],
                'qual': cols[5], 'filter': cols[6],
                'format': dict(zip(cols[8].split(':'), cols[9].split(':')))}
    core = {21176804: 'G', 21176879: 'A', 21196951: 'G', 21206031: 'G'}
    rows = []
    for index, locus in enumerate(definition['variants']):
        pos = locus['position']
        a14, a43 = (alleles[a]['alleles'][index] for a in ('*14', '*43'))
        obs = observed.get(pos)
        rows.append({'position_grch38': pos, 'rsid': locus['rsid'],
            'truth_expectation': 'heterozygous defining variant; original study notes cis/trans caveat'
                if pos in (21176804, 21176879) else 'not established by frozen star-label truth',
            'observed_public_vcf': obs, 'new_read_level_evidence': 'not acquired',
            'pinned_star14': a14, 'pinned_star43': a43,
            'current_pharmvar_core': ('*14 and *43' if pos in (21176804, 21176879)
                else '*43 only' if pos in core else 'not a core difference between *14 and *43')})
        if pos in core:
            assert obs['format'] == {'GT': '0|1'}
            assert obs['alt'] == a43 == core[pos]
            assert obs['filter'] == '.'
            assert a14 == (core[pos] if pos in (21176804, 21176879) else None)
    assert len(rows) == 35
    assert sum(r['observed_public_vcf'] is not None for r in rows) == 20
    save('variant-comparison.json', rows)
    historical = json.loads((frozen / 'locked_cohort.NA18861.report.json').read_text())
    parsed = parse_report(historical).model_dump(mode='json')
    save('frozen-report.parsed.json', parsed)
    result_dir = OUT / 'replay'
    result_dir.mkdir(exist_ok=True)
    command = ['/opt/homebrew/opt/openjdk/bin/java', '-Xmx256m', '-jar',
        str(ROOT / 'test-data/reference/tools/pharmcat-3.4.0-all.jar'), '-vcf',
        str(frozen / 'NA18861.1000G2022.vcf'), '-o', str(result_dir), '-reporterJson']
    start = datetime.datetime.now(datetime.timezone.utc)
    with (result_dir / 'execution.log').open('w') as log:
        run = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    assert run.returncode == 0
    reports = list(result_dir.glob('*.report.json'))
    assert len(reports) == 1
    raw = json.loads(reports[0].read_text())
    fresh = parse_report(raw).model_dump(mode='json')
    save('replay.parsed.json', fresh)
    for data in (historical, raw):
        assert [d['label'] for d in data['genes']['SLCO1B1']['sourceDiplotypes']] == ['*1/*43']
    for data in (parsed, fresh):
        assert data['genes']['SLCO1B1']['diplotype'] == '*1/*43'
    coverage = json.loads((frozen / 'NA18861-1000G2022.coverage.json').read_text())
    cov = next(g for g in coverage['genes'] if g['gene'] == 'SLCO1B1')
    assert cov['positions_found'] == 20 and cov['positions_required'] == 35 and not cov['passes']
    analysis = json.loads((frozen / 'NA18861-1000G2022.analyze.json').read_text())
    simvastatin = next(a for a in analysis['analyses'] if a['drug'] == 'simvastatin')
    assert simvastatin['risk_assessment']['risk_label'] == 'Unknown'
    diff_hash = hashlib.sha256(subprocess.check_output(['git', 'diff', '--binary'], cwd=ROOT)).hexdigest()
    baseline = json.loads((OUT / 'starting-working-tree.json').read_text())
    assert diff_hash == baseline['tracked_diff_sha256'], 'Tracked working tree changed during F7'
    save('verification.json', {'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'command': command, 'exit_code': run.returncode,
        'elapsed_seconds': (datetime.datetime.now(datetime.timezone.utc) - start).total_seconds(),
        'checks': {'frozen_checksums': True, 'source_artifacts_unchanged': True,
            'four_core_variants_observed': True, 'missing_positions_not_imputed': True,
            'fresh_pharmcat_call': '*1/*43', 'frozen_parser_call': '*1/*43',
            'fresh_parser_call': '*1/*43', 'frozen_final_simvastatin': 'Unknown',
            'tracked_diff_unchanged': True},
        'complete_read_backed_na18861_rerun': False,
        'coverage': cov, 'pinned_version': raw['pharmcatVersion'], 'data_version': raw['dataVersion']})
    gene = fresh['genes']['SLCO1B1']
    print(json.dumps({key: gene[key] for key in ('diplotype', 'phenotype_raw', 'candidate_diplotypes')}))
    print('F7 evidence checks passed. This replays the INCOMPLETE input, not a complete read-backed VCF.')


if __name__ == '__main__':
    main()
