"""Stop only the local servers and containers owned by this acceptance run."""
import json
import os
import signal
import subprocess
from run_checks import OUT,ROOT,save,bundle
results={}
name='pgx-final-20261002'
daemon=subprocess.run(['docker','info'],capture_output=True,text=True)
if daemon.returncode:
    vm=subprocess.run(['colima','status'],capture_output=True,text=True)
    results['container_runtime']={'docker_available':False,'docker_error':daemon.stderr,'colima_status':vm.stdout+vm.stderr,'not_restarted':True}
    save('image-byte-check.json',{'status':'INCONCLUSIVE','reason':'Colima stopped before final optional in-container byte comparison. Build receipt and measured image ID retained; no new runtime comparison claimed.'})
else:
    jar=subprocess.check_output(['docker','exec',name,'sha256sum','/pharmcat/pharmcat.jar'],text=True).split()[0]
    assert jar=='9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741'
    paths=[p for p in bundle.load_hash_policy()['core_paths'] if p.startswith(('backend/app/','rag-corpus/'))]
    remote=['/home/user/app/'+(p.removeprefix('backend/') if p.startswith('backend/') else p) for p in paths]
    records=subprocess.check_output(['docker','exec',name,'sha256sum']+remote,text=True).splitlines()
    different=[p for p,line in zip(paths,records) if line.split()[0]!=bundle.sha256(ROOT/p)]
    save('image-byte-check.json',{'jar_sha256':jar,'scientific_application_files_checked':len(paths),'mismatches':different})
    assert not different
    for n in ('pgx-final-20261002','pgx-final-timeout-20261002'):
        results[n]={'stop_output':subprocess.check_output(['docker','stop','--time','15',n],text=True).strip()}
        results[n]['state']=json.loads(subprocess.check_output(['docker','inspect',n],text=True))[0]['State']
for pid,needle in zip(json.loads((OUT/'local-servers.json').read_text())['pids'],['uvicorn app.main:app --host 127.0.0.1 --port 8000','http.server 3000 --bind 127.0.0.1']):
    p=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True)
    if not p.stdout.strip():results[str(pid)]='already stopped';continue
    if needle not in p.stdout:results[str(pid)]='PID no longer owned; left unchanged';continue
    os.kill(pid,signal.SIGTERM);results[str(pid)]='sent SIGTERM to verified owned local acceptance server'
results['scope']='Only two named test containers and two verified local acceptance servers. Other containers and the existing Colima VM left unchanged. Test images retained locally; no deployment.'
save('cleanup.json',results)
print(json.dumps(results,indent=2))
