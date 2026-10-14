# Executed command receipts

Exact argv are quoted below. Working directories, times and exit codes remain in command-index.json. Inline read/hash orchestration and CUA interaction outcomes are described in their receipts; no shell exit is invented for a browser action.

| Receipt | Exact command | Exit |
|---|---|---|
| git-status-start | `git status --porcelain=v1 -uall` | 0 |
| git-diff-start | `git diff --binary` | 0 |
| git-staged-start | `git diff --cached --binary` | 0 |
| head | `git rev-parse HEAD` | 0 |
| branch | `git branch --show-current` | 0 |
| gate-help | `backend/.venv/bin/python scripts/release_status.py --help` | 0 |
| real-acceptance | `backend/.venv/bin/python audit-output/2026-10-05-prompt7-5b236070c2/real_acceptance.py` | 0 |
| pdf-render | `pdftoppm -r 85 -png audit-output/2026-10-05-prompt7-5b236070c2/native-NA12878-print.pdf audit-output/2026-10-05-prompt7-5b236070c2/print-page` | 0 |
| pdf-extract | `/Users/bhuvant/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 audit-output/2026-10-05-prompt7-5b236070c2/verify_pdf.py` | 0 |
| glossary-report | `backend/.venv/bin/python scripts/glossary_status.py` | 0 |
| git-diff-final | `git diff --binary` | 0 |
| git-diff-stat-final | `git diff --stat` | 0 |
| git-diff-check | `git diff --check` | 0 |
| git-staged-final | `git diff --cached --binary` | 0 |
| finalize-owner-package | `python3 audit-output/2026-10-05-prompt7-5b236070c2/finalize_package.py` | 0 |
| NA12878-pharmcat.execution.json | `/opt/homebrew/opt/openjdk/bin/java -Xmx208m -XX:MaxMetaspaceSize=68m -jar '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/test-data/reference/tools/pharmcat-3.4.0-all.jar' -vcf '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-30-f4/NA12878.observed.vcf' -o '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA12878.pharmcat' -reporterJson` | 0 |
| NA18526-pharmcat.execution.json | `/opt/homebrew/opt/openjdk/bin/java -Xmx208m -XX:MaxMetaspaceSize=68m -jar '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/test-data/reference/tools/pharmcat-3.4.0-all.jar' -vcf '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-30-f4/NA18526.observed.vcf' -o '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA18526.pharmcat' -reporterJson` | 0 |
| NA18861-pharmcat.execution.json | `/opt/homebrew/opt/openjdk/bin/java -Xmx208m -XX:MaxMetaspaceSize=68m -jar '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/test-data/reference/tools/pharmcat-3.4.0-all.jar' -vcf '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-01-f7/frozen-local/NA18861.1000G2022.vcf.gz' -o '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA18861.pharmcat' -reporterJson` | 0 |
| adjudication.execution.json | `'/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/backend/.venv/bin/python' scripts/adjudication_status.py --json` | 1 |
| backend.execution.json | `'/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/backend/.venv/bin/python' -m pytest backend/tests -q -ra '--junitxml=/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/backend.xml'` | 0 |
| bundle.execution.json | `'/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/backend/.venv/bin/python' scripts/verify_compatible_bundle.py --json` | 0 |
| flutter-analyzer.execution.json | `flutter analyze --no-pub` | 0 |
| flutter-tests.execution.json | `flutter test --no-pub --reporter json` | 0 |
| isolated-content-baseline.execution.json | `'/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/backend/.venv/bin/python' '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/release-copy/scripts/release_status.py' --content-only --candidate-sha 1dc7557da49f38e831b382545044b00a481507b6 --json` | 1 |
| isolated-content-invalid.execution.json | `'/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/backend/.venv/bin/python' '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/release-copy/scripts/release_status.py' --content-only --candidate-sha 1dc7557da49f38e831b382545044b00a481507b6 --json` | 1 |
| isolated-content-restored.execution.json | `'/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/backend/.venv/bin/python' '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/release-copy/scripts/release_status.py' --content-only --candidate-sha 1dc7557da49f38e831b382545044b00a481507b6 --json` | 1 |
| mapping.execution.json | `'/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/backend/.venv/bin/python' scripts/validate_label_mapping.py` | 0 |
| provenance.execution.json | `'/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/backend/.venv/bin/python' scripts/verify_provenance.py --no-report` | 0 |
| read-replay-0.execution.json | `bcftools mpileup -q 20 -Q 20 -d 1000 --ns UNMAP,SECONDARY,QCFAIL,DUP,SUPPLEMENTARY -a FORMAT/DP,FORMAT/AD -f '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-30-f4/GRCh38.chr10.fa' -r chr10:94760900-94853914 -Ob -o '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA18526.pileup.bcf' '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-30-f4/NA18526.CYP2C19.bam'` | 0 |
| read-replay-1.execution.json | `bcftools call -m --ploidy 2 -a FORMAT/GQ -Ov -o '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA18526.calls.vcf' '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA18526.pileup.bcf'` | 0 |
| read-replay-2.execution.json | `bcftools norm -f '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-30-f4/GRCh38.chr10.fa' -Ov -o '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA18526.normalized.vcf' '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA18526.calls.vcf'` | 0 |
| read-replay-3.execution.json | `bcftools mpileup -q 20 -Q 20 -d 1000 --ns UNMAP,SECONDARY,QCFAIL,DUP,SUPPLEMENTARY -a FORMAT/DP,FORMAT/AD -f '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-30-f4/GRCh38.chr10.fa' -r chr10:94760900-94853914 -Ob -o '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA12878.pileup.bcf' '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-30-f4/NA12878.CYP2C19.bam'` | 0 |
| read-replay-4.execution.json | `bcftools call -m --ploidy 2 -a FORMAT/GQ -Ov -o '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA12878.calls.vcf' '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA12878.pileup.bcf'` | 0 |
| read-replay-5.execution.json | `bcftools norm -f '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-09-30-f4/GRCh38.chr10.fa' -Ov -o '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA12878.normalized.vcf' '/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/NA12878.calls.vcf'` | 0 |
| release-gate.execution.json | `'/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/backend/.venv/bin/python' scripts/release_status.py --run-required --candidate-sha 1dc7557da49f38e831b382545044b00a481507b6 --json` | 1 |
| review.execution.json | `'/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/backend/.venv/bin/python' scripts/review_status.py --json` | 0 |
| web-build.execution.json | `flutter build web --release --no-pub '--output=/Users/bhuvant/Projects/Pharmacogenomic Risk Prediction System/audit-output/2026-10-05-prompt7-5b236070c2/web-build' --dart-define=API_BASE_URL=http://127.0.0.1:8000` | 0 |
| Initial symlink inventory helper error; preserved receipt | `python3 audit-output/2026-10-05-prompt7-5b236070c2/assemble_owner.py` | 1 |
| Inventory-contract correction; candidate unchanged | `python3 audit-output/2026-10-05-prompt7-5b236070c2/assemble_owner.py` | 0 |
