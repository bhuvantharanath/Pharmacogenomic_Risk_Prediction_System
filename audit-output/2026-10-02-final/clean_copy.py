"""Verify portable identity in an isolated, enumerated candidate copy."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from run_checks import OUT, ROOT, PY, save
import compatible_bundle as bundle
import release_status

def main():
    if sys.argv[1] == 'create':
        target = Path(tempfile.mkdtemp(prefix='pgx-final-clean-'))
        paths = set(json.loads((OUT/'candidate-files.json').read_text()))
        paths.update('test-data/reference/tools/'+n for n in ('pharmcat-3.4.0-all.jar','pharmcat_positions_3.4.0.vcf.bgz','pharmcat_positions_3.4.0.vcf.bgz.csi'))
        for p in sorted(paths):
            src, dst = ROOT/p, target/p
            dst.parent.mkdir(parents=True,exist_ok=True)
            if src.is_symlink():
                assert p == 'render.yaml' and os.readlink(src) == 'infra/render.yaml'
                dst.symlink_to('infra/render.yaml')
            else:
                shutil.copyfile(src,dst)
        save('clean-copy-location.json',{'root':str(target),'files':sorted(paths),'no_git_or_environment':True})
        print(target)
    target = Path(json.loads((OUT/'clean-copy-location.json').read_text())['root'])
    label = sys.argv[1]
    identities = {'root':str(target),'application_core_sha256':bundle.application_core_hash(target),
        'release_artifact_sha256':release_status.candidate_artifact_hash(target),
        'components':{p:bundle.sha256(target/p) for p in [
            'backend/app/data/compatible_bundle.json','backend/app/data/explanations.json',
            'backend/app/data/explanation_approvals.json','backend/app/data/capabilities.json',
            'test-data/reference/tools/pharmcat-3.4.0-all.jar']}}
    for name,cmd in [('bundle',['scripts/verify_compatible_bundle.py','--json']),
        ('gate',['scripts/release_status.py','--run-required','--candidate-sha',json.loads((OUT/'candidate-identity.json').read_text())['head'],'--json'])]:
        result=subprocess.run([PY]+cmd,cwd=target,capture_output=True,text=True,timeout=1800)
        (OUT/f'clean-{label}-{name}.json').write_text(result.stdout)
        (OUT/f'clean-{label}-{name}.stderr').write_text(result.stderr)
        identities[name+'_exit_code']=result.returncode
    save('clean-'+label+'-identity.json',identities)
    print(label,identities['application_core_sha256'],identities['bundle_exit_code'],identities['gate_exit_code'])

if __name__=='__main__':main()
