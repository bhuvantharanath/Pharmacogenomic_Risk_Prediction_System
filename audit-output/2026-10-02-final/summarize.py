"""Summarize recorded checks without altering candidate or historical evidence."""
import collections
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from run_checks import ROOT,OUT,PY,run,save,bundle,release_status
import generate_capabilities

def junit(name):
    root=ET.parse(OUT/name).getroot();counts=collections.Counter();details=[];modules={}
    for tc in root.iter('testcase'):
        status='failed' if tc.find('failure') is not None else 'error' if tc.find('error') is not None else 'skipped' if tc.find('skipped') is not None else 'passed'
        counts[status]+=1
        module=tc.get('classname').split('.')[1]
        modules.setdefault(module,collections.Counter())[status]+=1
        if status!='passed':details.append({'name':tc.get('classname')+'::'+tc.get('name'),'status':status,'detail':ET.tostring(tc,encoding='unicode')})
    return {'counts':dict(counts),'nonpassing':details,'by_module':modules}
data={'backend_without_server':junit('backend-complete.xml'),'backend_with_server':junit('backend-live-complete.xml')}
events=[]
for line in (OUT/'flutter-tests-complete.stdout').read_text().splitlines():
    try:events.append(json.loads(line))
    except ValueError:pass
done=[e for e in events if e.get('type')=='testDone' and not e.get('hidden')]
data['flutter']={'tests':len(done),'results':dict(collections.Counter(e['result'] for e in done)),'skipped':sum(e['skipped'] for e in done)}
data['capability_generated_file_matches']=generate_capabilities.render()==generate_capabilities.TARGET.read_text()
save('test-summary.json',data)

parity={}
registry={x['drug']:x for x in json.loads((ROOT/'backend/app/data/capabilities.json').read_text())['capabilities']}
capability_keys=('drug','primary_gene','relevant_genes','evidence_dependencies','implementation_status','guidance_capable','limitation','explanation_available','ui_available','export_available')
for sample,label in [('NA18526','normal'),('NA12878','actionable')]:
    raw=json.loads((OUT/f'browser-{label}-api.json').read_text())
    timestamp=raw['timestamp'].replace(':','-').replace('.','-')
    downloaded=Path('/Users/bhuvant/Downloads')/f'pharmaguard_{sample}_{timestamp}.json'
    if label=='normal':shutil.copyfile(downloaded,OUT/f'browser-{label}-export.json')
    exported=json.loads((OUT/f'browser-{label}-export.json').read_text())
    expected=json.loads(json.dumps(raw))
    for a in expected['analyses']:
        a['risk_assessment'].pop('confidence_score',None);a['risk_assessment'].pop('severity',None)
        a['risk_assessment']['assessment_scope']='PGx interpretation only; not a clinical safety, probability, or severity assessment'
        cap=registry.get(a['drug'])
        a['application_capability']={k:cap[k] for k in capability_keys} if cap else {'drug':a['drug'],'guidance_capable':False,'export_available':False,'limitation':'Outside the audited application scope.'}
    parity[sample]={'scientific_content_equal_after_declared_export_transform':expected==exported,
        'intentional_differences':['omit legacy confidence_score','omit legacy severity','add assessment_scope disclaimer','add capability registry metadata, independently matched to authoritative registry'],
        'export_sha256':bundle.sha256(OUT/f'browser-{label}-export.json'),'download_file':str(downloaded)}
    assert expected==exported
save('browser-export-parity.json',parity)

frozen=json.loads((OUT/'candidate-files.json').read_text())
changed=[p for p,r in frozen.items() if not (ROOT/p).is_file() or bundle.sha256(ROOT/p)!=r['sha256']]
save('final-freeze.json',{'candidate_files':len(frozen),'changed_candidate_files_during_verification':changed,
    'application_core_sha256':bundle.application_core_hash(),'release_artifact_sha256':release_status.candidate_artifact_hash(),
    'git_tracked_diff_unchanged':subprocess.check_output(['git','diff','--binary'],cwd=ROOT)==(OUT/'initial-diff.patch').read_bytes(),
    'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()})
assert not changed
(OUT/'final-git-status.txt').write_bytes(subprocess.check_output(['git','status','--short'],cwd=ROOT))
run('git-diff-check',['git','diff','--check'])
print(json.dumps({'backend':data['backend_with_server']['counts'],'flutter':data['flutter'],'export_parity':parity,'candidate_changes':changed},indent=2))
