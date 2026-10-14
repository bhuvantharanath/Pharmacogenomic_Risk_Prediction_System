# F5 — 512 MiB container acceptance record

Recorded 2026-10-01. Local, uncommitted verification only; no deployment.

## Frozen target and inputs

- Intended plan: Render `free`, 512 MiB. Dockerfile uses pinned `pgkb/pharmcat:3.4.0`, one uvicorn worker, one PharmCAT JVM, static explanations, strict PharmCAT startup, 120-second PharmCAT timeout, and a 90-second admission/JVM queue timeout.
- Test runtime: Colima Docker on Linux/aarch64, cgroup v2 `memory.max=536870912` bytes and `memory.swap.max=0` (Docker `--memory 512m --memory-swap 512m`). This is a direct constrained Linux-container measurement, not a Render Linux/amd64 measurement.
- Real-sized incomplete input: `audit-output/2026-09-26/derived/NA18526.1000G2022.vcf.gz`, SHA-256 `adefa771bacbe2cf7d1930c5c92c90eb46722132eddc43040bb9659f19c81c77`.
- Complete synthetic control: `test-data/normal_metabolizer_control.vcf`.
- Complete observed real control: `audit-output/2026-09-30-f4/NA18526.observed.vcf`.
- Final local image: `pharmaguard-api:f5-release-candidate-v2`, image ID `sha256:b4ffd316f7a943ef1a01fcce41fa2692fc76835f4b60b90e8a783c360acc9087`, Linux/arm64, with `tini` as PID 1. Embedded `main.py` and `security.py` checksums matched the local working tree at build time.

## Reproduction and invariant

The pre-F5 image (`sha256:7ee9927fc174b1a63c6460123a6db319045f1a69169e354d81f48afef8e94058`) used `-Xmx256m -XX:MaxMetaspaceSize=80m`. A single real-sized incomplete analysis touched the 512 MiB cgroup ceiling (`memory.events max=105`); three concurrent uploads OOM-killed the container, exit 137. Reducing only the JVM to 192m/64m still OOM-killed a three-upload run: queued requests retained multiple expanded VCFs before reaching the existing one-JVM semaphore. The measured Python RSS rose to about 338 MiB in that probe.

Invariant: no more than one public upload request, whether `/analyze` or `/coverage`, may parse/decompress a VCF while the one allowed PharmCAT JVM is active. Queue waiting must be bounded before the body is consumed. A stopped/cancelled owned process must leave no running or zombie descendant and no owned temporary data.

The fix adds a process-wide, FIFO, cancellable ASGI admission gate for both upload endpoints before multipart parsing; the existing PharmCAT semaphore remains for JVM ownership. The gate returns 503 `SERVER_BUSY` after 90 seconds without reading the queued body. `tini` reaps orphaned descendants in the actual image. Genomic coverage rules, PharmCAT invocation, and clinical interpretation were not changed for F5.

The first admission candidate guarded only `/analyze`. An analysis plus one concurrent real-sized `/coverage` request both returned 200 but touched the 512 MiB ceiling (`memory.events max=28`). This finding caused the gate to be extended to `/coverage` as well. The regression was observed failing before that change and passing after it.

## JVM tuning and final workload

| Configuration | Finding |
| --- | --- |
| 192m heap / 64m metaspace | Memory stayed below limit, but the real-sized PharmCAT analysis returned `PHARMCAT_UNAVAILABLE`; rejected. |
| 224m / 72m with admission | Representative requests passed, but the ten-upload burst reached 512 MiB and `memory.events max=14`; rejected as too little headroom. |
| **208m / 68m with shared upload admission** | Final exact-source image passed the representative workload at 494.96 MiB peak, the ten-analysis burst at 496.13 MiB, and one analysis plus nine coverage previews at 454.58 MiB. `memory.events max=0`, `oom=0`, `oom_kill=0`; no container exit. |

For the final image, `/health`, `/ready`, `/coverage` on the real incomplete file, one real incomplete `/analyze`, one complete synthetic `/analyze`, one complete observed-real `/analyze`, two sequential repeats, and three simultaneous real-sized analyses all returned 200. The final three-request case sampled one JVM maximum, JVM RSS about 305 MiB and Python RSS about 191 MiB. Ten simultaneous real-sized analyses produced six 200 responses and four bounded 503 `SERVER_BUSY` responses at about 90 seconds; JVM count remained one, sampled JVM RSS about 305 MiB and Python RSS about 192 MiB. In a separate mixed run, PharmCAT was observed running before nine real-sized coverage previews were sent; all ten requests returned 200 at 454.58 MiB peak. Queue refusal did not mean genomic abstention or an application crash.

The three representative `/analyze` response bodies matched the pre-F5 image after excluding only request timestamp and processing-time fields. This includes the observed-real normal clopidogrel result, the synthetic normal results, and the incomplete-file Unknown results. No clinical labels were tuned to the workload.

An intentional 0.15-second PharmCAT timeout on the final image returned 503 `PHARMCAT_UNAVAILABLE`; inspection found only `tini` and uvicorn, no Java child or temporary files, and no OOM event. A separate cancellation probe on the final image spawned a parent and descendant, cancelled the owned task, and confirmed both PIDs disappeared and the temporary directory was empty. The previous image left a zero-RSS zombie descendant under uvicorn PID 1; the final image did not.

## Reproduce

Build the local image from the repository root with `docker build -f infra/Dockerfile -t pharmaguard-api:f5-release-candidate-v2 .`. Run it with `--memory 512m --memory-swap 512m`, the environment above, and a local port. `measure.py` accepts container name, host port, exact `JAVA_TOOL_OPTIONS`, and output ID; its final results are `measurements-v2.json`. The ten-analysis and mixed-path traces are `burst-v2-measurements.json` and `mixed-v2-measurements.json`. Build, workload, and test logs are in this directory. The measurement harness samples cgroup memory and `docker top` process RSS; the cgroup's `memory.peak` and `memory.events` are the authoritative limit/OOM counters.

## Tests and release boundary

- Admission, hostile concurrent-input, resource-ownership, and deployment targeted tests passed.
- Complete backend suite: only `test_checked_manifest_matches_declared_environment` and `test_clean_isolated_copy_passes_bundle_verification` failed. The new application/configuration bytes deliberately change the scientific application hash; the checked bundle and historical hash-migration record still describe the earlier candidate. Their failure is correct and must not be suppressed or relabelled as current validation.
- `scripts/verify_compatible_bundle.py`: FAIL. Checked core hash `204c315389f97f8de688b8ac3219bcc27f0a95c6e8c699fc50fd8b0df361725c`; current core hash `42ae5b9477c3291a287d629fdd2e28f26261094a66531084b9d06373e14886c0` at this report's final configuration. Historical benchmark identity does not bridge to the changed bytes.
- Authoritative release gate: `not-ready`, `release_ready=false`, `content_ready=false`. Generated entries approved/releasable: 0/0; 20 unapproved, deterministic-template-only mode; clinical expert review `NOT_OBTAINED`. Existing human-review blockers remain, and bundle compatibility is additionally false. No approval or historical evidence was fabricated.
- `git diff --check` passed. All changes remain local and uncommitted.

## F5 files changed locally

- `backend/app/main.py`, `backend/app/security.py`: shared pre-body upload admission for `/analyze` and `/coverage`.
- `backend/app/pharmcat_runner.py`: corrected the inner JVM-slot documentation; no F5 clinical or invocation logic change.
- `infra/Dockerfile`: minimal PID 1 reaper (`tini`).
- `infra/render.yaml`: measured 208m/68m JVM limits and admission comments.
- `infra/DEPLOY_NOTES.md`: current measured configuration and limitations.
- `backend/tests/test_analysis_memory_admission.py`, `backend/tests/test_deployment.py`: admission and process-reaper regressions.
- `audit-output/2026-09-30-f5/`: frozen plan, measurement harness, raw JSON/log evidence, and this report.

**Conclusion:** F5's local Linux/arm64 512 MiB operational workload passed with explicit queue shedding and clean timeout/cancellation. Do not infer Linux/amd64 Render parity or overall release readiness. Before any release, perform the controlled benchmark/bundle revalidation for the changed application identity and resolve the separate human-review gate; then verify the target platform. No hosting configuration was deployed. F5 test containers were stopped after recording results; their local Docker metadata and the audit files remain available.
