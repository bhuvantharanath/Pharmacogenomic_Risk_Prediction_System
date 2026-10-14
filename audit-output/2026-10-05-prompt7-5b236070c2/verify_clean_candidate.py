"""Build the intended dirty-tree copy and test identity/invalidation in that copy."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

D = Path(__file__).resolve().parent
R = D.parents[1]
C = D / 'release-copy'
O = D / 'different-parent' / 'release-copy'
assert not C.exists() and not O.exists(), 'preserve first clean-copy execution'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

inventory=json.loads((D/'candidate-inventory.json').read_text())
intended=[i['path'] for i in inventory if i['intended']]
for row in inventory:
    relative=row['path'];src=R/relative;dst=C/relative
    assert sha(src)==row['sha256']
    dst.parent.mkdir(parents=True,exist_ok=True)
    if src.is_symlink():dst.symlink_to(src.readlink())
    else:shutil.copy2(src,dst)
    assert sha(dst)==row['sha256']

def identities(root):
    code = '''import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"scripts"))
import compatible_bundle,release_status
print(json.dumps({"core":compatible_bundle.application_core_hash(),"release":release_status.candidate_artifact_hash()}))'''
    run = subprocess.run([sys.executable, '-c', code], cwd=root, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout)

def validator(root):
    run = subprocess.run([sys.executable, str(root / 'scripts/verify_compatible_bundle.py'), '--json'],
                         cwd=root, capture_output=True, text=True)
    return dict(exit_code=run.returncode, payload=json.loads(run.stdout), stderr=run.stderr)

source = identities(R)
baseline = identities(C)
assert source == baseline
baseline_check = validator(C)
assert baseline_check['exit_code'] == 0 and baseline_check['payload']['compatible']

junk = ('backend/app/.DS_Store', 'backend/app/main.py~',
        'backend/app/__pycache__/audit.cpython-311.pyc', 'backend/app/local.log',
        'backend/app/temporary.tmp')
for name in junk:
    target = C / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b'audit-only junk')
assert identities(C) == baseline
for name in junk:
    (C / name).unlink()

mutations = []
for relative in (
    'backend/app/cpic_engine.py', 'backend/app/data/capabilities.json',
    'backend/app/data/position_requirements.json',
    'backend/app/data/explanations.json',
    'backend/app/data/explanation_approvals.json',
    'test-data/benchmark/current-candidate-2026-10-04/external_benchmark_results.json',
):
    target = C / relative
    original = target.read_bytes()
    target.write_bytes(original + b'\n')
    changed = identities(C)
    decision = validator(C)
    assert decision['exit_code'] == 1 and decision['payload']['compatible'] is False, relative
    assert changed['release'] != baseline['release'], relative
    if relative.startswith('backend/app/'):
        assert changed['core'] != baseline['core'], relative
    else:
        assert changed['core'] == baseline['core'], relative
    mutations.append(dict(path=relative, changed_core=changed['core'] != baseline['core'],
                          changed_release=changed['release'] != baseline['release'],
                          validator_exit=decision['exit_code'],
                          problems=decision['payload']['problems'][:5]))
    target.write_bytes(original)
    assert identities(C) == baseline and validator(C)['exit_code'] == 0

O.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(C, O, symlinks=True)
assert identities(O) == baseline
assert validator(O)['exit_code'] == 0
for row in inventory:
    if row['intended']:
        path = C / row['path']
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']

result = dict(intended_file_count=len(intended), copied_file_count=len(inventory),
              baseline=baseline, clean_validator=baseline_check,
              junk_ignored=list(junk), mutations=mutations,
              different_parent_identity=identities(O),
              final_clean_identity=identities(C), final_clean_validator=validator(C),
              restored_exactly=True)
(D / 'clean-copy-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ('intended_file_count','copied_file_count',
    'baseline','junk_ignored','restored_exactly')}, indent=2))
print('mutations rejected:', len(mutations))

# Baseline release gate is blocked by real human prerequisites. This explicitly
# does not demonstrate a release PASS -> FAIL -> PASS sequence.
def content_gate(name):
    argv=[sys.executable,str(C/'scripts/release_status.py'),'--content-only','--candidate-sha','1dc7557da49f38e831b382545044b00a481507b6','--json']
    r=subprocess.run(argv,cwd=C,capture_output=True)
    (D/(name+'.stdout')).write_bytes(r.stdout);(D/(name+'.stderr')).write_bytes(r.stderr)
    (D/(name+'.execution.json')).write_text(json.dumps(dict(command=argv,cwd=str(C),exit_code=r.returncode),indent=2)+'\n')
    return json.loads(r.stdout)
base=content_gate('isolated-content-baseline')
assert base['content_ready'] is False
p=C/'backend/app/data/explanations.json';before=p.read_bytes()
value=json.loads(before)
# Mutate exact stored prose in the isolated copy only.
def mutate(v):
    if isinstance(v,dict):
        if isinstance(v.get('summary'),str):v['summary']='DELIBERATELY INVALID AUDIT CONTENT';return True
        return any(mutate(x) for x in v.values())
    if isinstance(v,list):return any(mutate(x) for x in v)
    return False
assert mutate(value)
try:
    p.write_text(json.dumps(value,indent=2)+'\n')
    bad=content_gate('isolated-content-invalid')
    assert bad['manifest']['compatible'] is False
finally:p.write_bytes(before)
restored=content_gate('isolated-content-restored')
assert restored['manifest']==base['manifest']
assert identities(C)==baseline
for row in inventory:assert sha(C/row['path'])==row['sha256']
(D/'negative-gate-summary.json').write_text(json.dumps({'baseline_release_pass':False,'scope':'content-only gate in isolated copy; full working-candidate gate run separately','baseline':base['prerequisites'],'invalid':bad['prerequisites'],'rejection_reasons':bad['manifest']['problems'],'restored':restored['prerequisites'],'exact_restoration':True},indent=2)+'\n')
