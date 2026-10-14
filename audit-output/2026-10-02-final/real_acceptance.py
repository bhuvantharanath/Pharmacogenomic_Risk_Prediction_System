"""Frozen public-input replay and evidence-loss controls; never invent reference calls."""
import json
from pathlib import Path
import subprocess
import sys
import time
import httpx
from run_checks import OUT,ROOT,run,save,bundle
sys.path.insert(0,str(ROOT/'backend'))
from app.pharmcat_runner import parse_report

F4=ROOT/'audit-output/2026-09-30-f4'
JAVA='/opt/homebrew/opt/openjdk/bin/java'
JAR=ROOT/'test-data/reference/tools/pharmcat-3.4.0-all.jar'
DRUGS='clopidogrel,simvastatin,fluorouracil,azathioprine,warfarin,codeine,ibuprofen,atorvastatin'

def post(case,path):
    record={'input':str(path),'sha256':bundle.sha256(path)}
    with httpx.Client(timeout=180) as client:
        for endpoint in ('coverage','analyze'):
            start=time.monotonic()
            with path.open('rb') as f:
                res=client.post('http://127.0.0.1:8000/'+endpoint,files={'file':(path.name,f)},
                    data={'drugs':DRUGS} if endpoint=='analyze' else {})
            payload=res.json();save(case+'.'+endpoint+'.json',payload)
            record[endpoint]={'status':res.status_code,'seconds':time.monotonic()-start}
            if endpoint=='analyze':record['labels']={a['drug']:a['risk_assessment']['risk_label'] for a in payload.get('analyses',[])}
    return record

def vcf_rows(path):
    return {int(c[1]):c for l in path.read_text().splitlines() if l and not l.startswith('#') for c in [l.split('\t')]}

def direct(name,path):
    dest=OUT/(name+'.pharmcat');dest.mkdir(exist_ok=True)
    result=run(name+'-pharmcat',[JAVA,'-Xmx208m','-XX:MaxMetaspaceSize=68m','-jar',str(JAR),'-vcf',str(path),'-o',str(dest),'-reporterJson'])
    assert result['exit_code']==0
    raw=json.loads(next(dest.glob('*.report.json')).read_text())
    parsed=parse_report(raw).model_dump(mode='json');save(name+'.parsed.json',parsed)
    return raw,parsed

def main():
    protocol=json.loads((F4/'frozen-protocol.json').read_text())
    assert bundle.sha256(F4/'frozen-protocol.json')==(F4/'frozen-protocol.sha256').read_text().strip()
    for name,expected in protocol['hashes'].items():assert bundle.sha256(ROOT/name)==expected,name
    results={};comparisons=[]
    for sample in protocol['samples']:
        path=F4/(sample+'.observed.vcf')
        evidence=json.loads((F4/(sample+'.evidence.json')).read_text())
        receipt=json.loads((F4/(sample+'.extraction.json')).read_text())
        assert bundle.sha256(F4/(sample+'.CYP2C19.bam'))==receipt['sha256']
        assert bundle.sha256(path)==evidence['observed_vcf_sha256']
        assert evidence['passing_positions']==35 and not evidence['missing_positions']
        results[sample]=post(sample,path)
        raw,parsed=direct(sample,path)
        truth=next(t['truth_raw'] for t in protocol['truth'] if t['sample_id']==sample)
        api=json.loads((OUT/(sample+'.analyze.json')).read_text())
        cov=json.loads((OUT/(sample+'.coverage.json')).read_text())
        clop=next(a for a in api['analyses'] if a['drug']=='clopidogrel')
        assert parsed['genes']['CYP2C19']['diplotype']==truth==clop['pharmacogenomic_profile']['diplotype']
        assert cov['answerable_drugs']==['clopidogrel']
        assert all(v=='Unknown' for k,v in results[sample]['labels'].items() if k!='clopidogrel')
        assert results[sample]['labels']['clopidogrel']==('No PGx-guided adjustment identified' if sample=='NA18526' else 'Ineffective')
        positions={r['position']:r for r in evidence['records']}
        for v in raw['genes']['CYP2C19']['variants']:
            r=positions[v['position']]; bases=[r['ref']]+(r['alt'] or [])
            assert sorted(bases[i] for i in r['GT'])==sorted(v['call'].replace('|','/').split('/'))
        assert any('source=template' in w for w in api['quality_metrics']['warnings'])
        comparisons.append({'sample':sample,'independent_truth':truth,'observed_qualified_positions':35,
            'DP_range':[min(r['DP'] for r in evidence['records']),max(r['DP'] for r in evidence['records'])],
            'pharmcat':raw['genes']['CYP2C19']['sourceDiplotypes'], 'parser':parsed['genes']['CYP2C19']['diplotype'],
            'final_profile':clop['pharmacogenomic_profile'],'label':results[sample]['labels']['clopidogrel'],
            'all_35_genotypes_preserved':True,'discrepancy':'none_in_evaluated_path'})
    cases={
        'real-incomplete':ROOT/'audit-output/2026-09-26/derived/NA18526.1000G2022.vcf.gz',
        'synthetic-normal':ROOT/'test-data/normal_metabolizer_control.vcf',
        'synthetic-actionable':ROOT/'test-data/cyp2c19_poor_metabolizer.vcf',
    }
    # Degradation-only transformations of the existing read-backed actionable input.
    original=(F4/'NA12878.observed.vcf').read_text().splitlines()
    for kind in ('variant-only','failed-filter','partial-gt','missing-required'):
        lines=[]; changed=False
        for line in original:
            if line.startswith('#'):lines.append(line);continue
            c=line.split('\t');fmt=c[8].split(':');values=c[9].split(':');i=fmt.index('GT')
            if kind=='variant-only' and values[i] in ('0/0','0|0'):continue
            if not changed and int(c[1])==94781859:
                changed=True
                if kind=='missing-required':continue
                if kind=='failed-filter':c[6]='LowQual'
                if kind=='partial-gt':values[i]='0/.';c[9]=':'.join(values)
            lines.append('\t'.join(c))
        target=OUT/('real-'+kind+'.vcf');target.write_text('\n'.join(lines)+'\n');cases['real-'+kind]=target
    for gene,chrom,start,end in [('TPMT','chr6',0,999999999),('NUDT15','chr13',0,999999999)]:
        lines=[l for l in cases['synthetic-normal'].read_text().splitlines() if l.startswith('#') or l.split('\t')[0]!=chrom]
        target=OUT/('missing-'+gene+'.vcf');target.write_text('\n'.join(lines)+'\n');cases['missing-'+gene]=target
    for name,path in cases.items():
        results[name]=post(name,path)
        assert all(results[name]['labels'][d]=='Unknown' for d in ('warfarin','codeine','ibuprofen','atorvastatin'))
        if name.startswith('real-'):assert all(v=='Unknown' for v in results[name]['labels'].values()),name
        if name.startswith('missing-'):assert results[name]['labels']['azathioprine']=='Unknown'
    path=ROOT/'audit-output/2026-10-01-f7/frozen-local/NA18861.1000G2022.vcf.gz'
    results['NA18861']=post('NA18861',path)
    raw,parsed=direct('NA18861',path)
    assert raw['genes']['SLCO1B1']['sourceDiplotypes'][0]['label']==parsed['genes']['SLCO1B1']['diplotype']=='*1/*43'
    assert results['NA18861']['labels']['simvastatin']=='Unknown'
    save('real-truth-comparison.json',comparisons);save('api-acceptance.json',results)
    print('Positive public cases, degradation-only controls, scope abstentions and NA18861 replay passed',flush=True)

if __name__=='__main__':main()
