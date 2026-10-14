"""Real PharmCAT task cancellation inside the constrained image."""
import asyncio
import json
import os
from pathlib import Path
from app.pharmcat_runner import run_pharmcat

def children():
    result=[]
    for p in Path('/proc').glob('[0-9]*/comm'):
        try:
            if p.read_text().strip()=='java':result.append(int(p.parent.name))
        except (FileNotFoundError,ProcessLookupError):pass
    return result
async def main():
    before=list(Path('/tmp').glob('pharmaguard_pharmcat_*'))
    task=asyncio.create_task(run_pharmcat(Path('/tmp/final-input.vcf').read_text()))
    seen=[]
    for _ in range(200):
        seen=children()
        if seen:break
        await asyncio.sleep(.01)
    assert seen,'No live JVM observed: cancellation not tested'
    task.cancel()
    cancelled=False
    try:await task
    except asyncio.CancelledError:cancelled=True
    await asyncio.sleep(.3)
    after=children()
    temporary=list(Path('/tmp').glob('pharmaguard_pharmcat_*'))
    print(json.dumps({'cancelled':cancelled,'observed_java_pids':seen,'java_after':after,
        'temp_before':[str(p) for p in before],'temp_after':[str(p) for p in temporary]}))
    assert cancelled and not after and temporary==before
asyncio.run(main())
