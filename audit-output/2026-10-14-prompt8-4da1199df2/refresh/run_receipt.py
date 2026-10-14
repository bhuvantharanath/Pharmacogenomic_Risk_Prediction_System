"""Run one refresh stage and preserve argv, cwd, timestamps, output and exit code.
Usage: run_receipt.py <name> <argv...>   (cwd = repository root)"""
import datetime
import json
import subprocess
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
R = D.parents[2]
name, *argv = sys.argv[1:]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
p = subprocess.run(argv, cwd=R, capture_output=True)
(D / (name + '.stdout')).write_bytes(p.stdout)
(D / (name + '.stderr')).write_bytes(p.stderr)
ledger = D / 'commands.json'
rows = json.loads(ledger.read_text()) if ledger.exists() else []
rows.append(dict(name=name, argv=argv, cwd=str(R), started_at=started,
                 ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 exit_code=p.returncode, stdout=name + '.stdout', stderr=name + '.stderr'))
ledger.write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps({'name': name, 'exit_code': p.returncode}))
print(p.stdout.decode(errors='replace')[-4000:])
print(p.stderr.decode(errors='replace')[-2000:])
sys.exit(p.returncode)
