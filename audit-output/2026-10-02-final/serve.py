"""Local-only acceptance servers, with owned process cleanup."""
import os
import subprocess
import sys
import time
from run_checks import OUT, ROOT, PY, save
children=[]
logs=[]
try:
    env=dict(os.environ,PHARMCAT_JAR=str(ROOT/'test-data/reference/tools/pharmcat-3.4.0-all.jar'),
        PHARMCAT_JAVA='/opt/homebrew/opt/openjdk/bin/java',EXPLANATION_MODE='static',STRICT_PHARMCAT='1',
        PHARMAGUARD_ENV='development',JAVA_TOOL_OPTIONS='-Xmx208m -XX:MaxMetaspaceSize=68m',
        MAX_CONCURRENT_PHARMCAT='1',PHARMCAT_QUEUE_TIMEOUT_SECONDS='90')
    for name,cmd,cwd in [
        ('backend-server',[PY,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000'],ROOT/'backend'),
        ('frontend-server',[PY,'-m','http.server','3000','--bind','127.0.0.1','--directory',str(ROOT/'app/build/web')],ROOT)]:
        log=(OUT/(name+'.log')).open('a');logs.append(log)
        children.append(subprocess.Popen(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT))
    save('local-servers.json',{'pids':[p.pid for p in children],'ports':[8000,3000]})
    while all(p.poll() is None for p in children):time.sleep(1)
finally:
    for p in children:
        if p.poll() is None:p.terminate()
    for p in children:
        try:p.wait(timeout=10)
        except subprocess.TimeoutExpired:p.kill();p.wait()
    for log in logs:log.close()
