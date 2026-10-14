import os,subprocess,json,signal
from run_checks import ROOT,OUT,PY,save
argv=[PY,'-m','uvicorn','capture_api:app','--app-dir',str(OUT),'--host','127.0.0.1','--port','8000','--workers','1']
env=dict(os.environ,PHARMCAT_JAR=str(ROOT/'test-data/reference/tools/pharmcat-3.4.0-all.jar'),PHARMCAT_JAVA='/opt/homebrew/opt/openjdk/bin/java',EXPLANATION_MODE='static',STRICT_PHARMCAT='1',PHARMAGUARD_ENV='development',CORS_ALLOWED_ORIGINS='http://127.0.0.1:3000',JAVA_TOOL_OPTIONS='-Xmx208m -XX:MaxMetaspaceSize=68m',MAX_CONCURRENT_PHARMCAT='1',PHARMCAT_QUEUE_TIMEOUT_SECONDS='90')
save('browser-server-command.json',{'argv':argv,'cwd':str(ROOT),'environment_overrides':{k:v for k,v in env.items() if k not in os.environ or os.environ[k]!=v}})
with (OUT/'browser-backend-server.log').open('w') as log:
 p=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
 save('browser-server-pid.json',{'pid':p.pid})
 try: p.wait()
 except KeyboardInterrupt:
  p.terminate();p.wait(timeout=20)
 save('browser-server-exit.json',{'exit_code':p.returncode})
