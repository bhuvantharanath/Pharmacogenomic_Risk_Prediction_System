import importlib.util
import json
import subprocess
import time
from pathlib import Path
import httpx
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
spec=importlib.util.spec_from_file_location('measure',ROOT/'audit-output/2026-09-30-f5/measure.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=OUT
NAME='pgx-final-20261002';TIMEOUT='pgx-final-timeout-20261002'
data=json.loads((OUT/'container-lifecycle.json').read_text()) if (OUT/'container-lifecycle.json').exists() else {}
def keep(k,v):
    data[k]=v;(OUT/'container-lifecycle.json').write_text(json.dumps(data,indent=2)+'\n');print(k,flush=True)
from concurrent.futures import ThreadPoolExecutor
def mixed():
    with ThreadPoolExecutor(max_workers=10) as pool:
        return list(pool.map(lambda i:m.post(8767,'coverage' if i else 'analyze',m.REAL_INCOMPLETE,f'final-mixed-retry-{i}'),range(10)))
if 'cancellation' not in data:
    keep('mixed_fresh_rate_window',m.envelope(NAME,'one_analysis_nine_coverage',mixed))
    m.command('docker','cp',str(m.NORMAL_CONTROL),NAME+':/tmp/final-input.vcf')
    p=subprocess.run(['docker','exec','-i',NAME,'python3','-'],input=(OUT/'container_lifecycle.py').read_text(),capture_output=True,text=True)
    keep('cancellation',{'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
m.command('docker','exec','--user','root',NAME,'python3','-c',"from pathlib import Path; Path('/tmp/final-input.vcf').unlink()")
keep('post_cancel_cgroup',m.cgroup(NAME))
keep('post_cancel_processes',m.command('docker','top',NAME,'-eo','pid,ppid,comm,rss'))
keep('post_cancel_temp_logs',m.command('docker','exec',NAME,'sh','-c','find /tmp /home/user/app -maxdepth 3 -name "pharmaguard_pharmcat_*" -o -name "*.log"'))
keep('timeout_container_id',m.command('docker','run','-d','--name',TIMEOUT,'--memory','512m','--memory-swap','512m','-p','127.0.0.1:8768:7860','-e','PHARMAGUARD_ENV=development','-e','JAVA_TOOL_OPTIONS=-Xmx208m -XX:MaxMetaspaceSize=68m','-e','MAX_CONCURRENT_PHARMCAT=1','-e','PHARMCAT_QUEUE_TIMEOUT_SECONDS=90','-e','PHARMCAT_TIMEOUT_SECONDS=0.15','-e','EXPLANATION_MODE=static','-e','STRICT_PHARMCAT=1','pharmaguard-api:final-verification-20261002'))
for _ in range(30):
    try:
        if httpx.get('http://127.0.0.1:8768/health').status_code==200:break
    except httpx.HTTPError:pass
    time.sleep(.5)
keep('timeout',m.envelope(TIMEOUT,'forced_real_call_timeout',lambda:m.post(8768,'analyze',m.REAL_COMPLETE,'final-timeout')))
keep('timeout_processes',m.command('docker','top',TIMEOUT,'-eo','pid,ppid,comm,rss'))
keep('timeout_temp_logs',m.command('docker','exec',TIMEOUT,'sh','-c','find /tmp /home/user/app -maxdepth 3 -name "pharmaguard_pharmcat_*" -o -name "*.log"'))
keep('main_inspect',m.inspect(NAME));keep('timeout_inspect',m.inspect(TIMEOUT))
