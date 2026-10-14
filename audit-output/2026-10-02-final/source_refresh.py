"""Fetch public primary version records; no clinical review is implied."""
import concurrent.futures
import datetime
import hashlib
import json
import urllib.request
from pathlib import Path
OUT=Path(__file__).resolve().parent
sources={
 'pharmcat-latest':'https://api.github.com/repos/PharmGKB/PharmCAT/releases/latest',
 'pharmvar-version':'https://www.pharmvar.org/get-version',
 'pharmvar-2':'https://www.pharmvar.org/api/haplotypes/3110?projection=FullHaplotypeInfo',
 'pharmvar-2-history':'https://www.pharmvar.org/get-haplotype-history?id=3110',
 'pharmvar-2-variants':'https://www.pharmvar.org/api/haplotypes/search/findAllVariantsForHap?id=3110',
}
def fetch(item):
    name,url=item
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'PharmaGuard-local-scientific-verification','Accept':'application/json'})
        with urllib.request.urlopen(request,timeout=30) as response: raw=response.read();status=response.status
        (OUT/(name+'.json')).write_bytes(raw)
        return {'name':name,'url':url,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'sha256':hashlib.sha256(raw).hexdigest()}
    except Exception as e:return {'name':name,'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:receipts=list(pool.map(fetch,sources.items()))
(OUT/'source-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
print(json.dumps(receipts,indent=2))
