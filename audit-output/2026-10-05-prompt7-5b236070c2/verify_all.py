from run_checks import *
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
commands=[
 ('backend',[PY,'-m','pytest','backend/tests','-q','-ra','--junitxml='+str(OUT/'backend.xml')],ROOT),
 ('bundle',[PY,'scripts/verify_compatible_bundle.py','--json'],ROOT),
 ('provenance',[PY,'scripts/verify_provenance.py','--no-report'],ROOT),
 ('mapping',[PY,'scripts/validate_label_mapping.py'],ROOT),
 ('adjudication',[PY,'scripts/adjudication_status.py','--json'],ROOT),
 ('review',[PY,'scripts/review_status.py','--json'],ROOT),
 ('flutter-analyzer',['flutter','analyze','--no-pub'],ROOT/'app'),
 ('flutter-tests',['flutter','test','--no-pub','--reporter','json'],ROOT/'app'),
 ('web-build',['flutter','build','web','--release','--no-pub','--output='+str(OUT/'web-build'),'--dart-define=API_BASE_URL=http://127.0.0.1:8000'],ROOT/'app'),
 ('release-gate',[PY,'scripts/release_status.py','--run-required','--candidate-sha',head,'--json'],ROOT)]
for args in commands:run(*args)
