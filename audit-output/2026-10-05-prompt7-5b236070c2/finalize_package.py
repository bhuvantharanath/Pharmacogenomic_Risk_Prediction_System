import json,hashlib,subprocess,shlex
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(D/n).write_text(json.dumps(v,indent=2)+'\n')
inv=json.loads((D/'candidate-inventory.json').read_text())
assert all(sha(R/x['path'])==x['sha256'] for x in inv)
assert (D/'git-diff-start.stdout').read_bytes()==(D/'git-diff-final.stdout').read_bytes()
assert not (D/'git-staged-final.stdout').read_bytes()
changed=subprocess.check_output(['git','diff','--name-only','-z'],cwd=R).decode().split('\0')
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=R).decode().split('\0')
changedset=set(changed+untracked)
selected=[x for x in inv if x['intended'] and x['path'] in changedset]
save('candidate-changed-files.json',selected)
numstat=subprocess.check_output(['git','diff','--numstat'],cwd=R,text=True)
(D/'full-diff-summary.tsv').write_text('added_lines\tremoved_lines\tpath\n'+numstat)
# Exact finite evidence list: purpose-built audit receipts, never recursive staging.
paths={x['path'] for x in selected}
old=R/'audit-output/2026-10-02-final/PROPOSED-RELEASE-FILES.txt'
if old.exists():
 for line in old.read_text().splitlines():
  p=R/line
  if line.startswith('audit-output/') and p.is_file() and p.stat().st_size<2_000_000 and p.suffix not in {'.bam','.bai','.bcf','.gz','.jar'}:paths.add(line)
for dirname in ['2026-10-03-prompt4a-8f4cbfbc76','2026-10-04-prompt5-14c02de54f','2026-10-05-prompt6-bb6a5821fb']:
 for p in sorted((R/'audit-output'/dirname).iterdir()):
  if p.is_file() and p.stat().st_size<2_000_000 and p.suffix in {'.md','.json','.txt','.tsv','.xml','.stdout','.stderr'}:paths.add(str(p.relative_to(R)))
exclude={'artifact-checksums.json','proposed-file-hashes.json','PROPOSED-RELEASE-FILES.txt','git-status-final.stdout','git-status-final.stderr','final-git-receipt.json','task-created-files.json'}
for p in sorted(D.rglob('*')):
 rel=p.relative_to(D)
 if any(x in rel.parts for x in ['release-copy','different-parent','web-build','__pycache__']):continue
 if p.is_file() and p.name not in exclude and p.stat().st_size<2_000_000 and p.suffix not in {'.bcf','.bam','.bai','.gz','.jar','.pyc'}:paths.add(str(p.relative_to(R)))
paths=sorted(paths)
(D/'PROPOSED-RELEASE-FILES.txt').write_text('\n'.join(paths)+'\n')
save('proposed-file-hashes.json',{'status':'BLOCKED; proposal only, no stage/commit/publication','files':[{'path':s,'bytes':(R/s).stat().st_size,'sha256':sha(R/s)} for s in paths],'exclusions':'Actual env/secrets; external JAR/cohort/raw acquisition; caches; isolated copies; built assets; unrelated files; self-referencing inventory/control receipts. See candidate-inventory for external identity and supported acquisition receipts in preserved Prompt5.'})
# Consolidate only actually captured command records; avoid inferring shell argv for inline orchestration.
rec=json.loads((D/'commands.json').read_text())
for p in sorted(D.glob('*.execution.json')):rec.append({'receipt':p.name,**json.loads(p.read_text())})
rec.extend([{'command':['python3',str(D.relative_to(R)/'assemble_owner.py')],'exit_code':1,'note':'Initial symlink inventory helper error; preserved receipt'}, {'command':['python3',str(D.relative_to(R)/'assemble_owner.py')],'exit_code':0,'note':'Inventory-contract correction; candidate unchanged'}])
save('command-index.json',rec)
lines=['# Executed command receipts','','Exact argv are quoted below. Working directories, times and exit codes remain in command-index.json. Inline read/hash orchestration and CUA interaction outcomes are described in their receipts; no shell exit is invented for a browser action.','','| Receipt | Exact command | Exit |','|---|---|---|']
for r in rec:lines.append('| '+r.get('name',r.get('receipt',r.get('note','')))+' | `'+shlex.join(r.get('argv',r.get('command',[]))).replace('|','\\|')+'` | '+str(r['exit_code'])+' |')
(D/'COMMANDS.md').write_text('\n'.join(lines)+'\n')
# Start/final raw status excludes no user files. Metadata written afterward is separately inventoried.
p=subprocess.run(['git','status','--porcelain=v1','-uall'],cwd=R,capture_output=True)
(D/'git-status-final.stdout').write_bytes(p.stdout);(D/'git-status-final.stderr').write_bytes(p.stderr)
start=(D/'git-status-start.stdout').read_text().splitlines();final=p.stdout.decode().splitlines();prefix=str(D.relative_to(R))+'/'
outside=lambda lines:sorted(l for l in lines if prefix not in l)
receipt={'git_status_command':['git','status','--porcelain=v1','-uall'],'git_status_exit':p.returncode,'candidate_files_unchanged':len(inv),'tracked_diff_identical_start_final':True,'tracked_diff_sha256':sha(D/'git-diff-final.stdout'),'staged_diff_bytes':0,'status_entries_start':len(start),'status_entries_final':len(final),'outside_audit_status_unchanged':outside(start)==outside(final),'outside_audit_added_status':sorted(set(outside(final))-set(outside(start))),'outside_audit_removed_status':sorted(set(outside(start))-set(outside(final))),'proposed_paths':len(paths),'intended_changed_candidate_paths':len(selected),'scope':'No candidate source/approval/policy/manifest edits; only fresh audit artifacts. Ignored generated caches/builds are excluded from Git status. Final inventory control files listed separately.'}
save('final-git-receipt.json',receipt)
art=[]
for p in sorted(D.rglob('*')):
 rel=p.relative_to(D)
 if any(x in rel.parts for x in ['release-copy','different-parent','web-build','__pycache__']):continue
 if p.is_file() and p.name not in {'artifact-checksums.json','task-created-files.json'}:art.append({'path':str(rel),'bytes':p.stat().st_size,'sha256':sha(p)})
save('artifact-checksums.json',{'self_reference_exclusions':['artifact-checksums.json','task-created-files.json'],'generated_trees_excluded':['release-copy (437 frozen inventory)','different-parent (same437)','web-build (web-build-inventory.json)','__pycache__ (disposable)'],'files':art})
save('task-created-files.json',{'audit_directory':str(D.relative_to(R)),'files':[x['path'] for x in art]+['artifact-checksums.json','task-created-files.json'],'generated_trees':'See artifact-checksums exclusions and separate build/frozen inventories','candidate_changes':[]})
print(json.dumps(receipt,indent=2))
