"""Fresh API replay of the two frozen F4 read-backed positive controls against the
live task-owned API running the frozen fixed candidate (same checks as Prompt 5,
plus the corrected disclaimer wording)."""
import hashlib
import json
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
R = D.parents[2]
F = R / 'audit-output/2026-09-30-f4'
sys.path.insert(0, str(R / 'scripts'))
from run_demo import post_analyze  # noqa: E402

artifacts = {row['path']: row for row in json.loads((F / 'artifact-checksums.json').read_text())['files']}
protocol = json.loads((F / 'frozen-protocol.json').read_text())
truth = {row['sample_id']: row for row in protocol['truth']}
assert protocol['before_genotype_calling'] and protocol['before_application_scoring']
cases = [('NA18526', '*1/*1', 'NM', 'No PGx-guided adjustment identified'),
         ('NA12878', '*1/*2', 'IM', 'Ineffective')]
receipts = []
for sample, diplotype, phenotype, label in cases:
    vcf = F / (sample + '.observed.vcf')
    data = vcf.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    frozen = artifacts[vcf.name]
    assert frozen['bytes'] == len(data) and frozen['sha256'] == digest
    assert truth[sample]['truth_normalized'] == diplotype
    response = post_analyze('http://127.0.0.1:8000', vcf, 'clopidogrel')
    (D / (sample + '.fresh-api.json')).write_text(json.dumps(response.body, indent=2) + '\n')
    assert response.status == 200, (sample, response.status, response.error)
    analysis = response.body['analyses'][0]
    profile = analysis['pharmacogenomic_profile']
    warnings = response.body['quality_metrics']['warnings']
    disclaimer = analysis['llm_generated_explanation']['disclaimer']
    checks = dict(
        independent_truth=truth[sample]['truth_normalized'] == diplotype,
        profile_diplotype=profile['diplotype'] == diplotype,
        phenotype=profile['phenotype'] == phenotype,
        label=analysis['risk_assessment']['risk_label'] == label,
        acs_pci_qualifier_retained='CVI ACS PCI' in analysis['clinical_recommendation']['cpic_recommendation'],
        deterministic_fallback=any('source=template' in w for w in warnings),
        no_static_prose=not any('source=static' in w for w in warnings),
        no_clinical_review_claim='No qualified clinical expert' in disclaimer,
        no_invention_guarantee='nothing was invented' not in disclaimer,
    )
    receipts.append(dict(sample=sample, source_accession=protocol['samples'][sample],
                         observed_vcf_sha256=digest, historical_frozen_artifact_sha256=frozen['sha256'],
                         response_sha256=hashlib.sha256((D / (sample + '.fresh-api.json')).read_bytes()).hexdigest(),
                         latency_ms=response.latency_ms, checks=checks, passed=all(checks.values()),
                         scope=('fresh current API/PharmCAT replay of a previously frozen read-backed VCF; '
                                'not a new raw-read extraction or independent genotype call')))
(D / 'f4-fresh-replay.json').write_text(json.dumps(receipts, indent=2) + '\n')
assert all(x['passed'] for x in receipts), receipts
print(json.dumps({'cases': len(receipts), 'passed': sum(x['passed'] for x in receipts),
                  'checks': sum(len(x['checks']) for x in receipts)}, indent=2))
