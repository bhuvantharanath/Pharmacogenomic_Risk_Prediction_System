"""Additional constrained local-container workloads; no production mutation."""
import importlib.util
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
spec=importlib.util.spec_from_file_location('measure',ROOT/'audit-output/2026-09-30-f5/measure.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=OUT
NAME='pgx-final-20261002'
data={}
def keep(name,value):
    data[name]=value
    (OUT/'container-extra.json').write_text(json.dumps(data,indent=2)+'\n')
    print(name,'recorded',flush=True)
def burst(mixed=False):
    with ThreadPoolExecutor(max_workers=10) as pool:
        return list(pool.map(lambda i:m.post(8767,'coverage' if mixed and i else 'analyze',m.REAL_INCOMPLETE,f'final-{("mixed" if mixed else "burst")}-{i}'),range(10)))
keep('burst10',m.envelope(NAME,'ten_concurrent_analysis',burst))
keep('mixed10',m.envelope(NAME,'one_analysis_nine_coverage',lambda:burst(True)))
keep('final_cgroup',m.cgroup(NAME))
keep('post_workload_processes',m.command('docker','top',NAME,'-eo','pid,ppid,comm,rss'))
keep('post_workload_temp_and_logs',m.command('docker','exec',NAME,'sh','-c','find /tmp /home/user/app -maxdepth 3 -name "pharmaguard_pharmcat_*" -o -name "*.log"'))
