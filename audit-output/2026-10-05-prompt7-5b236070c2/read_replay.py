"""Replay the frozen read-calling commands into a fresh evidence directory."""
import hashlib
import json
from pathlib import Path
from run_checks import ROOT,OUT,run,save
F4=ROOT/'audit-output/2026-09-30-f4'
protocol=json.loads((F4/'frozen-protocol.json').read_text())
assert hashlib.sha256((F4/'frozen-protocol.json').read_bytes()).hexdigest()==(F4/'frozen-protocol.sha256').read_text().strip()
outputs={str(F4/(s+ext)):str(OUT/(s+ext)) for s in protocol['samples'] for ext in ('.pileup.bcf','.calls.vcf','.normalized.vcf')}
commands=[json.loads(l)['command'] for l in (F4/'commands.jsonl').read_text().splitlines()]
for i,command in enumerate(commands):
    replay=[outputs.get(x,x) for x in command]
    assert run('read-replay-'+str(i),replay)['exit_code']==0
def rows(path):
    return [x for x in path.read_text().splitlines() if not x.startswith('#')]
results={}
for sample in protocol['samples']:
    old=rows(F4/(sample+'.normalized.vcf'));new=rows(OUT/(sample+'.normalized.vcf'))
    assert old==new,sample
    positions={(x[0],str(x[1])) for x in protocol['positions']}
    observed=[r for r in new if tuple(r.split('\t')[:2]) in positions]
    assert len(observed)==35
    results[sample]={'all_normalized_rows_identical':True,'read_called_rows':len(new),'required_observed_rows':len(observed),
        'genotype_DP_GQ_AD_unchanged':True,'note':'VCF headers differ in run timestamp/output paths; record bytes match exactly.'}
save('read-replay.json',results)
