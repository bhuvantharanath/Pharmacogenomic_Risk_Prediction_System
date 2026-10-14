"""Read-only candidate checks; outputs confined to this verification directory."""
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PY = str(ROOT / 'backend/.venv/bin/python')
sys.path.insert(0, str(ROOT / 'scripts'))
import compatible_bundle as bundle
import release_status

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, default=str) + '\n')

def run(name, cmd, cwd=ROOT, timeout=1800):
    started = time.monotonic()
    env = dict(os.environ, PHARMCAT_JAR=str(ROOT / 'test-data/reference/tools/pharmcat-3.4.0-all.jar'),
        PHARMCAT_JAVA='/opt/homebrew/opt/openjdk/bin/java', EXPLANATION_MODE='static',
        STRICT_PHARMCAT='1', PYTHONDONTWRITEBYTECODE='1')
    with (OUT / (name + '.stdout')).open('w') as out, (OUT / (name + '.stderr')).open('w') as err:
        try:
            p = subprocess.run(cmd, cwd=cwd, env=env, stdout=out, stderr=err, timeout=timeout)
            code = p.returncode
        except Exception as exc:
            err.write(repr(exc)); code = -1
    record = {'command': cmd, 'cwd': str(cwd), 'exit_code': code,
              'seconds': time.monotonic() - started, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(name + '.execution.json', record)
    print(name, code, round(record['seconds'], 2), flush=True)
    return record

def freeze():
    files = subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'], cwd=ROOT).decode().split('\0')
    def intended(p):
        return bool(p) and not p.startswith(('audit-output/', 'output/', 'tmp/')) and p not in ('PharmaGuard.pdf','PharmaGuard_IEEE_Research_Paper.docx')
    selected = set(filter(intended,files)) | set(bundle.load_hash_policy()['core_paths']) | set(release_status.RELEASE_IDENTITY_EXTRAS)
    records = {p: {'sha256':bundle.sha256(ROOT/p),'bytes':(ROOT/p).stat().st_size} for p in sorted(selected) if (ROOT/p).is_file()}
    save('candidate-files.json',records)
    status = subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    (OUT/'initial-git-status.txt').write_text(status)
    for name,args in [('initial-diff.patch',['git','diff','--binary']),('initial-diff-summary.txt',['git','diff','--stat']),('initial-diff-numstat.txt',['git','diff','--numstat'])]:
        (OUT/name).write_bytes(subprocess.check_output(args,cwd=ROOT))
    save('candidate-identity.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'application_core_sha256':bundle.application_core_hash(),
        'release_artifact_sha256':release_status.candidate_artifact_hash(),
        'inventory_sha256':bundle.sha256(OUT/'candidate-files.json'), 'files':len(records),
        'scope':'Local dirty candidate, not HEAD alone. No approval implied.'})
    changed = subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
    new = subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    proposal = sorted(set(changed) | {p for p in new if intended(p)})
    (OUT/'proposed-release-files.txt').write_text('\n'.join(proposal)+'\n')
    print('Frozen candidate',len(records),'files; proposed source/evidence files',len(proposal),flush=True)

def checks():
    head = json.loads((OUT/'candidate-identity.json').read_text())['head']
    commands = [
        ('release-gate',[PY,'scripts/release_status.py','--run-required','--candidate-sha',head,'--json'],ROOT),
        ('backend',[PY,'-m','pytest','backend/tests','-ra','--junitxml='+str(OUT/'backend.xml')],ROOT),
        ('bundle',[PY,'scripts/verify_compatible_bundle.py','--json'],ROOT),
        ('provenance',[PY,'scripts/verify_provenance.py','--no-report'],ROOT),
        ('mapping',[PY,'scripts/validate_label_mapping.py'],ROOT),
        ('flutter-analyzer',['flutter','analyze'],ROOT/'app'),
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda item:run(*item),commands))
    run('flutter-tests',['flutter','test','--reporter','json'],ROOT/'app')
    run('web-build',['flutter','build','web','--release','--dart-define=API_BASE_URL=http://127.0.0.1:8000'],ROOT/'app')

if __name__ == '__main__':
    {'freeze':freeze,'checks':checks}[sys.argv[1]]()
