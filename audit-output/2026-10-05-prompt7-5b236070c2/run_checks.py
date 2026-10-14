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

