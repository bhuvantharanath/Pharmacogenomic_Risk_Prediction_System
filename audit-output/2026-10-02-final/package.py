"""Prepare a finite owner-review proposal; never stage or commit it."""
import json
from pathlib import Path
from run_checks import ROOT,OUT,save,bundle
summary=[]
for filename in ('measurements-final-verification.json','container-extra.json','container-lifecycle.json'):
    data=json.loads((OUT/filename).read_text())
    cases=data.get('cases') or [v for v in data.values() if isinstance(v,dict) and 'results' in v]
    for case in cases:
        summary.append({k:v for k,v in case.items() if k!='samples'})
save('container-summary.json',{'records':summary,'lifecycle':{k:v for k,v in json.loads((OUT/'container-lifecycle.json').read_text()).items() if k in ('cancellation','post_cancel_cgroup','post_cancel_processes','post_cancel_temp_logs','timeout_processes','timeout_temp_logs')},
    'platform':'linux/aarch64','image_id':'sha256:8d2cf13f7b25a39d413f4bdebbb2a50b5cdf2dd9c386c9cf8195e22d015ccefe','memory_bytes':536870912,'memory_swap_total_bytes':536870912})

source_proposal=(OUT/'proposed-release-files.txt').read_text().splitlines()
evidence={
 'audit-output/2026-09-30-f4':[
  'PROTOCOL.md','REPORT.md','frozen-protocol.json','frozen-protocol.sha256','acquisition.json','commands.jsonl',
  'NA18526.observed.vcf','NA12878.observed.vcf','NA18526.evidence.json','NA12878.evidence.json',
  'NA18526.extraction.json','NA12878.extraction.json','NA18526.header.json','NA12878.header.json',
  'NA18526.ena.tsv','NA12878.ena.tsv','truth-comparison.json','prepare.py','derive.py','test_preparation.py','score.py','check_results.py','check_models.dart','finalize.py'],
 'audit-output/2026-09-30-f5':['REPORT.md','measure.py'],
 'audit-output/2026-10-01-f6':['REPORT.md'],
 'audit-output/2026-10-01-f7':['REPORT.md','attribution.json','variant-comparison.json','pinned-SLCO1B1_translation.json','local-evidence.json','verification.json','acquisition.jsonl','collect.py','verify.py'],
 'audit-output/2026-10-02-final':[
  'FINAL-POST-REMEDIATION-VERIFICATION.md','PROPOSED-RELEASE-FILES.txt','proposed-file-hashes.json',
  'candidate-identity.json','candidate-files.json','final-freeze.json','initial-diff-summary.txt','initial-diff-numstat.txt','final-git-status.txt',
  'test-summary.json','backend-live-complete.stdout','backend-live-complete.stderr','backend-live-complete.execution.json',
  'flutter-tests-complete.execution.json','flutter-analyzer-complete.stdout','flutter-analyzer-complete.execution.json','web-build-complete.execution.json',
  'provenance.stdout','mapping.stdout','release-gate-final.stdout','release-gate-final.execution.json','bundle.stdout',
  'clean-create-identity.json','clean-junk-identity.json','clean-mutated-identity.json','clean-invalid-prose-identity.json','clean-invalid-prose-gate.json','clean-restored-identity.json',
  'real-truth-comparison.json','read-replay.json','api-acceptance.json','NA18526.analyze.json','NA12878.analyze.json','NA18526.coverage.json','NA12878.coverage.json',
  'NA18861.analyze.json','NA18861.parsed.json','container-summary.json','cleanup.json','image-byte-check.json',
  'source-receipts.json','pharmcat-latest.json','pharmvar-version.json','pharmvar-2.json','pharmvar-2-history.json','pharmvar-2-variants.json',
  'browser-export-parity.json','browser-actionable-api.json','browser-actionable-export.json','browser-normal-api.json','browser-normal-export.json',
  'browser-actionable-download.json','browser-normal-download.json','browser-actionable-result.txt','browser-actionable-cpic.txt','browser-normal-result.txt',
  'browser-incomplete-readiness.txt','browser-incomplete-result.txt','browser-incomplete-details.txt','browser-synthetic-normal-result.txt','browser-synthetic-actionable-result.txt',
  'browser-unsupported.txt','browser-mobile-bottom.txt','browser-console.json','browser-actionable.jpg','browser-normal.jpg','browser-incomplete.jpg','browser-oversized-error.jpg',
  'run_checks.py','real_acceptance.py','clean_copy.py','serve.py','container_extra.py','container_lifecycle.py','finish_container.py','read_replay.py','source_refresh.py','summarize.py','package.py','cleanup.py']}
all_files=sorted(set(source_proposal)|{parent+'/'+name for parent,names in evidence.items() for name in names})
(OUT/'PROPOSED-RELEASE-FILES.txt').write_text('\n'.join(all_files)+'\n')
self_name=str((OUT/'proposed-file-hashes.json').relative_to(ROOT))
missing=[p for p in all_files if p!=self_name and not (ROOT/p).is_file()]
if missing:raise SystemExit('Create required report/receipts before final packaging: '+repr(missing))
save('proposed-file-hashes.json',{'purpose':'Exact owner-review proposal, not a releasable candidate or commit authorization','files':{p:bundle.sha256(ROOT/p) for p in all_files if p!=self_name},'self_excluded':self_name})
print('Finite proposed file list:',len(all_files),'paths; no Git mutation')
