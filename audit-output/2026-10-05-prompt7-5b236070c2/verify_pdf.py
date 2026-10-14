import json,hashlib,re
from pathlib import Path
import pdfplumber
D=Path(__file__).resolve().parent
api=json.loads((D/'browser-api/0020-analyze.body').read_text())
with pdfplumber.open(D/'native-NA12878-print.pdf') as pdf:
 pages=[p.extract_text(layout=False) or '' for p in pdf.pages]
(D/'native-print-extracted.txt').write_text('\n\f\n'.join(pages))
def norm(s):return re.sub(r'\s+',' ',str(s)).strip()
text=norm(' '.join(pages)); checks=[]
def check(label,value):
 checks.append({'field':label,'expected':value,'present':norm(value) in text})
check('patient_id',api['patient_id']);check('timestamp',api['timestamp'])
for a in api['analyses']:
 pre=a['drug'];check(pre+'.drug',pre);check(pre+'.risk_label',a['risk_assessment']['risk_label'])
 for k in ['primary_gene','diplotype','phenotype']:check(pre+'.'+k,a['pharmacogenomic_profile'][k])
 for k in ['action','cpic_recommendation','cpic_evidence_level','source']:check(pre+'.'+k,a['clinical_recommendation'][k])
 check(pre+'.summary',a['llm_generated_explanation']['summary'])
q=api['quality_metrics']
for k,v in q['guideline_provenance'].items():
 if isinstance(v,str) and v:check('provenance.'+k,v)
warnings=q.get('pipeline_warnings',q.get('warnings',[]))
result={'pdf_sha256':hashlib.sha256((D/'native-NA12878-print.pdf').read_bytes()).hexdigest(),'api_sha256':hashlib.sha256((D/'browser-api/0020-analyze.body').read_bytes()).hexdigest(),'pages':len(pages),'checks':checks,'missing':[c for c in checks if not c['present']], 'repeated_research_header':[('RESEARCH AND EDUCATIONAL USE ONLY' in p) for p in pages], 'visual_inspection':{'pages':[1,2,3,4,5],'clipping_or_truncation_observed':False,'method':'85 dpi pdftoppm renders inspected individually'},'pipeline_warning_count':len(warnings),'pipeline_warnings_present_verbatim':[norm(w) in text for w in warnings], 'scope':'Actual Chrome UI print route and native Save as PDF; summary fields only. Current summary_document.dart does not render mechanism, variant rationale, patient-friendly expansion, detected variants or raw pipeline-warning list. JSON exports retain them. Omissions disclosed, not normalized into full-response parity.'}
(D/'native-print-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
