# Prompt 6: constrained-image recertification preflight

**Outcome: INCONCLUSIVE for the final image.** No image was built or run, so there is no fresh container peak, OOM observation, exit status, scientific output, or graceful shutdown receipt for the Prompt 5 candidate. The 496.46 MiB Linux/arm64 peak belongs solely to the earlier image and workload. Native Linux/amd64 remains unmeasured.

## Candidate and intended configuration

Starting and final Git status are saved separately. HEAD is `1dc7557da49f38e831b382545044b00a481507b6` on `main`; the dirty tree is authoritative. All 437 Prompt 5 inventory files match their expected SHA-256 and byte counts both in the working tree and in the reconstructed context. The context contains 47,834,680 regular-file bytes, exactly the listed files and no cache, log, secret or actual environment file. The original Prompt 5 release copy had 18 verification-created Python cache files; they were excluded from this new context without changing the candidate. Build context and candidate inventories are saved as JSON.

The Dockerfile pins `pgkb/pharmcat:3.4.0`, checks the JAR SHA-256 `9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741` during build, and launches one Uvicorn worker. The declared 512 MiB setting is `JAVA_TOOL_OPTIONS=-Xmx208m -XX:MaxMetaspaceSize=68m`, `MAX_CONCURRENT_PHARMCAT=1`, `PHARMCAT_QUEUE_TIMEOUT_SECONDS=90`, ordinary PharmCAT timeout 120 s, strict caller and static explanations. The intended Docker limits are 536,870,912 bytes memory and 536,870,912 bytes total memory plus swap. Current scientific core is `38451a563c6f6cfb52257626d41700eeff3a5621ebe91b3358f878b375a6a691`; compatible manifest SHA-256 is `963a039ba16690d1c6ed772268ebb5c1512275beeb5fa117a6bef1c03aae7600`, embedded data version `2026-07-13-11-40`.

## Runtime side-effect boundary

`colima list` (exit 0) shows the existing default aarch64 profile stopped. `docker --context colima version --format '{{json .Server}}'` (exit 1) and the same Docker Desktop command (exit 1) confirm both daemons unavailable. The prior final verification records that starting the default Colima VM auto-started unrelated containers under saved restart policies. I therefore did not start that VM or reconfigure those containers. An isolated Colima profile is the practical local alternative, but it would need to obtain the pinned PharmCAT base, historically about 6 GB unpacked. The Universal instructions explicitly withhold implicit authority to install large dependencies. I requested authorization for the isolated profile and large local pull; the dependent build and workload are pending that answer.

`runtime-preflight.json` contains the exact command vectors, exit codes, stdout and stderr for `colima list`, `docker context ls` (exit 0), both Docker daemon checks (exit 1), `uname -m` (exit 0), and `df -h .` (exit 0). `candidate-preflight.json` contains every working-tree comparison, `build-context-inventory.json` the exact context, and `final-preflight-verification.json` confirms no candidate byte changed and no file was staged. The Git start/final status and staged-diff receipts are in this directory.

## Remaining work after authorization

Build from `build-context` with the actual `infra/Dockerfile`; inspect image architecture, ID and in-image JAR, data and application bytes while it remains accessible. Then run the single image under explicit memory and no-additional-swap limits through startup, health, coverage, incomplete/complete synthetic and real controls, sequential/concurrent/burst/mixed workloads, timeout/cancellation, rate-limit recovery, and owned cleanup. Capture cgroup peak/events, process RSS and count, latencies, results, container stop/exit, and native architecture limitations. No result from those stages is claimed in this preflight.

Only new audit receipts and a clean build context were created. No production source, test, deployment configuration, hosted service, VM, Docker image, or container was changed. No commit, stage, push, merge, tag, release or deployment occurred.
