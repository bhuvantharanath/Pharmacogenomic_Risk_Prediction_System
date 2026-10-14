"""Audit-only passive response recorder; forwards ASGI messages unchanged."""
import sys,json,hashlib,datetime
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D.parents[1]/'backend'))
from app.main import app as production_app
class Capture:
 def __init__(self,inner):self.inner=inner;self.n=0
 async def __call__(self,scope,receive,send):
  chunks=[];status=None
  async def record(message):
   nonlocal status
   if message['type']=='http.response.start':status=message['status']
   if message['type']=='http.response.body':chunks.append(message.get('body',b''))
   await send(message)
  await self.inner(scope,receive,record)
  if scope['type']=='http':
   self.n+=1;folder=D/'browser-api';folder.mkdir(exist_ok=True);name=f"{self.n:04d}-{scope['path'].strip('/')}";raw=b''.join(chunks)
   (folder/(name+'.body')).write_bytes(raw)
   (folder/(name+'.receipt.json')).write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':scope['path'],'method':scope['method'],'status':status,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'headers':{k.decode():v.decode() for k,v in scope['headers'] if k.lower() in [b'user-agent',b'origin',b'sec-ch-ua']}},indent=2)+'\n')
app=Capture(production_app)
