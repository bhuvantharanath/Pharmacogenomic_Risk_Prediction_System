from pathlib import Path
import json,hashlib,subprocess,xml.etree.ElementTree as ET,shlex,plistlib,datetime
D=Path(__file__).resolve().parent;R=D.parents[1]
def save(n,v): (D/n).write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inv=json.loads((D/'candidate-inventory.json').read_text())
diffs=[]
for x in inv:
 p=R/x['path']
 actual=sha(p)  # Frozen inventory hashes target bytes; symlink type recorded separately.
 if actual!=x['sha256']:diffs.append({'path':x['path'],'expected':x['sha256'],'actual':actual})
save('freeze-comparison-final.json',{'files':len(inv),'differences':diffs,'inventory_sha256':sha(D/'candidate-inventory.json')})
assert not diffs
root=ET.parse(D/'backend.xml').getroot();cases=root.findall('.//testcase')
skips=[{'id':c.get('classname')+'::'+c.get('name'),'message':c.find('skipped').get('message')} for c in cases if c.find('skipped') is not None]
f=[json.loads(l) for l in (D/'flutter-tests.stdout').read_text().splitlines() if l.startswith('{')]
save('test-summary.json',{'backend':{'total':len(cases),'passed':len(cases)-len(skips),'failures':[c.attrib for c in cases if c.find('failure') is not None or c.find('error') is not None],'skips':skips,'deprecation_warnings':9},'flutter':{'passed':sum(x.get('type')=='testDone' and x.get('result')=='success' and not x.get('hidden') for x in f),'done':f[-1]}})
receipts=json.loads((D/'commands.json').read_text())
for p in sorted(D.glob('*.execution.json')):receipts.append({'receipt':p.name,**json.loads(p.read_text())})
save('command-index.json',receipts)
lines=['# Executed command receipts','', 'Commands are shown with shell quoting for readability; raw argv, working directory, timestamps and exits are in command-index.json. Browser actions use CUA and have outcome receipts, not shell exit codes.','', '| Receipt | Exact command | Exit |','|---|---|---|']
for r in receipts:lines.append('| '+r.get('name',r.get('receipt',''))+' | `'+shlex.join(r.get('argv',r.get('command',[]))).replace('|','\\|')+'` | '+str(r['exit_code'])+' |')
(D/'COMMANDS.md').write_text('\n'.join(lines)+'\n')
b=json.loads((R/'test-data/benchmark/current-candidate-2026-10-04/external_benchmark_results.json').read_text())
lines=['# Candidate-bound benchmark denominators','', 'These are Prompt5 application-stage results verified against unchanged current bytes, not a new cohort caller execution in Prompt7. All 208 upstream caller reports were reused under the controlled protocol.','', '| Gene | Truth evaluable | Upstream exact | Upstream candidate-compatible | Conditional exact | Application eligible | Application abstention | Discrepancies |','|---|---:|---|---|---|---|---|---|']
for g,v in b['genes'].items():
 a=v['layer_A_upstream'];app=v['layer_B_application'];fr=lambda d:str(d['numerator'])+'/'+str(d['denominator'])
 lines.append('| '+g+' | '+str(v['truth_evaluable'])+' | '+' | '.join(fr(x) for x in [a['exact_diplotype_concordance'],a['candidate_compatible_concordance'],a['conditional_exact_accuracy'],app['input_eligible'],app['abstention']])+' | '+json.dumps(v['discrepancy_classification'])+' |')
lines+=['','208 unique individuals; 1,456 sample-gene rows; 596 evaluable; 816 blank; 42 unsafe nomenclature; 2 unresolved/discordant truth. No pooled accuracy. Phenotype, false reassurance, false warning and clinical utility are not estimable without independent corresponding truth. Every application evaluable row abstains; this does not demonstrate broad positive-pathway accuracy.','', 'All gene metrics, exclusions and discrepancy classifications equal the historical evaluation. All 1,456 input-eligibility rows have a changed temporary projected-VCF hash. A representative comparison has 172 identical genotype rows and different path-bearing tool headers. The old temporary bytes are unavailable, so historical per-file byte equivalence is not asserted.']
(D/'BENCHMARK.md').write_text('\n'.join(lines)+'\n')
p=json.loads((D/'native-print-verification.json').read_text())
save('print-policy-assessment.json',{'mechanical_route':'PASS','visual_legibility':'PASS','summary_scientific_fields':'PASS','exact_full_api_parity':'NOT_CLAIMED','raw_misses':p['missing'],'documented_display_transform':{'field':'guideline_provenance.explanations_generated_at','api':'2026-07-24T09:53:53.175011+00:00','printed':'24 Jul 2026','basis':'GuidelineProvenance.explanationsDate model getter; summary_document.dart uses date only'},'pipeline_warnings_omitted':p['pipeline_warning_count'],'all_pipeline_warnings_absent_verbatim':not any(p['pipeline_warnings_present_verbatim']),'content_review':'FAIL: unsupported assurance that automated source checking verifies nothing was invented; exact PDF page 1 and source disclaimer retained. No remediation performed in verification.'})
assert sha(D/'clipboard-raw-cua.json')==json.loads((D/'clipboard-verification.json').read_text())['actual_clipboard_sha256']
brows={'native_browser_version':plistlib.loads(Path('/Applications/Google Chrome.app/Contents/Info.plist').read_bytes())['CFBundleShortVersionString'],'version_basis':'installed native Google Chrome Info.plist; API request User-Agent also retained','API':'127.0.0.1:8000, production FastAPI app with passive audit-only ASGI response recorder','build':'fresh Flutter release web; source candidate-inventory.json; build artifact hashes in web-build-inventory.json','cases':[
 {'case':'real incomplete','input':'audit-output/2026-09-26/derived/NA18526.raw-required-sites.vcf','api':'0004-analyze.body','readiness':'0/7','result':'6 Unknown'},
 {'case':'synthetic normal and out-of-scope ibuprofen','input':'test-data/normal_metabolizer_control.vcf','api':'0006-analyze.body','readiness':'6/7','result':'4 qualified normal; codeine/warfarin Unknown; ibuprofen Unknown with scope warning'},
 {'case':'synthetic actionable','input':'test-data/cyp2c19_poor_metabolizer.vcf','api':'0008-analyze.body','readiness':'6/7','result':'CYP2C19 *2/*2 PM, clopidogrel Ineffective, ACS/PCI qualifier'},
 {'case':'frozen real normal','input':'audit-output/2026-09-30-f4/NA18526.observed.vcf','api':'0010-analyze.body','readiness':'1/7','result':'CYP2C19 *1/*1 NM; qualified clopidogrel normal; 5 Unknown'},
 {'case':'oversized public','input':'audit-output/2026-09-26/derived/NA18861.1000G2022.vcf','api':'0012-analyze.body','result':'HTTP 413; visible 5 MB limit; recovered with next upload'},
 {'case':'frozen real actionable','input':'audit-output/2026-09-30-f4/NA12878.observed.vcf','api':'0014-analyze.body','readiness':'1/7','result':'CYP2C19 *1/*2 IM, Ineffective; 5 Unknown; ACS/PCI qualifier'},
 {'case':'native Chrome actionable repeat','input':'audit-output/2026-09-30-f4/NA12878.observed.vcf','api':'0020-analyze.body','result':'same bounded scientific result, native saved JSON and PDF'}],
 'interaction_checks':{'real_chooser_uploads':'PASS','readiness_loading_recovery':'PASS','expanded_details_qualifier_provenance':'PASS','scrolling':'PASS','responsive_sizes':['1280x720','360x640'],'broad_Safe_verdict_seen':False,'clinical_confidence_percent_seen':False,'clipboard_after_UI_action':'PASS; raw bytes, exact JSON transform parity','native_saved_JSON':'PASS; actual disk bytes','native_UI_print_saved_PDF':'PASS; five pages inspected','IAB_download':'INCONCLUSIVE: actual transfer canceled, 0 received of 31861 bytes; waiter timeout. Native Chrome succeeded.','IAB_print':'INCONCLUSIVE: print iframe visible, automation call timeout; no saved PDF from IAB'},
 'limitations':['Full browser workflow set exercised in IAB; native Chrome repeated actionable upload and actual exports, not all fixture workflows.','Printed summary intentionally omits raw warning list and several expanded fields under existing implementation; not full API parity.','Printed unsupported source-checking assurance is a separate content defect; no candidate fix authorized by verification.','No permission/security bypass, extension installation or new clipboard permission grant.','No native Chrome window available at cleanup; no blind close action. IAB viewport reset.'], 'UI_visual_changes':'NONE'}
# Resolve exact observed input paths from frozen evidence instead of assuming placement.
for row in brows['cases']:
 if not (R/row['input']).exists() and 'observed.vcf' in row['input']:
  matches=list((R/'audit-output/2026-09-30-f4').rglob(Path(row['input']).name))
  if len(matches)==1:row['input']=str(matches[0].relative_to(R))
 if (R/row['input']).is_file():row['input_sha256']=sha(R/row['input'])
 else:row['input_path_status']='SEE real_acceptance.py exact path; unresolved summary path'
 row['api_sha256']=sha(D/'browser-api'/row['api'])
save('browser-summary.json',brows)
save('web-build-inventory.json',[{'path':str(p.relative_to(D/'web-build')),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((D/'web-build').rglob('*')) if p.is_file()])
print('Owner summaries assembled; candidate differences:',len(diffs))
