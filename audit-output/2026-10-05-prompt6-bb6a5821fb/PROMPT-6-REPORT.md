# Prompt 6: final-image memory recertification

**PASS for the measured local Linux/arm64 image and declared 512 MiB configuration. INCONCLUSIVE for native Linux/amd64 and the actual hosting platform.** This is operational evidence for a bounded research demo, not clinical validation or deployment authorization. The earlier `PREFLIGHT.md` is the preserved pre-start snapshot; this report supersedes its pending-runtime status.

## Candidate, context, and image

Prompt 5's dirty-tree candidate remained authoritative. All 437 inventory entries matched in both the working tree and the newly constructed build context before the build and again afterward. The context had exactly 437 files and 47,834,680 regular-file bytes; 18 verification-created Python caches in Prompt 5's older release copy were excluded. No secret, actual env file, log, or unrelated data entered the context. Start/final Git status and exact tracked diffs are saved; the tracked diff is byte-identical and staging stayed empty.

The actual `infra/Dockerfile` built successfully from that context on an isolated Colima Linux/aarch64 profile. The default Colima profile stayed stopped; the isolated profile started with no containers and ended stopped with no containers. Docker base `pgkb/pharmcat:3.4.0` resolved to manifest digest `sha256:bc498d55c33094002bd7e14221a6b3fcd7243a587675369bc1a5ecf6ac0e5319`. Final image ID is `sha256:82abce68aaafd51da8ed41eba52a2e1d5e0909a6a0f06005c8aeb5b6e7016d90`, `linux/arm64`. The build's JAR checksum/version step passed. While the image's main container was still running, all 50 copied backend/corpus/requirements files matched exact candidate SHA-256 and size; the in-image JAR, positions and index matched the compatible manifest. JAR SHA-256 is `9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741`; data version is `2026-07-13-11-40`. Candidate scientific core is `38451a563c6f6cfb52257626d41700eeff3a5621ebe91b3358f878b375a6a691`; checked compatible manifest SHA-256 is `963a039ba16690d1c6ed772268ebb5c1512275beeb5fa117a6bef1c03aae7600`.

## Runtime configuration and measured workload

All five owned containers used that exact image ID, one Uvicorn worker, `MAX_CONCURRENT_PHARMCAT=1`, `JAVA_TOOL_OPTIONS=-Xmx208m -XX:MaxMetaspaceSize=68m`, 90-second queue timeout, static explanation mode, and strict PharmCAT. The ordinary caller timeout was 120 seconds. Each container had Docker memory and total memory-plus-swap limits of **536,870,912 bytes**; in-container cgroup files confirmed `memory.max=536870912` and `memory.swap.max=0` (no additional swap). Only the separate timeout test container set `PHARMCAT_TIMEOUT_SECONDS=0.15`; it was labeled test-only and used the same image and memory bound. Local development CORS mode served only loopback-mapped ports; no hosted service was contacted.

| Stage | Actual results | Cgroup peak | Margin to 512 MiB | Peak sampled JVMs |
|---|---|---:|---:|---:|
| Main health, coverage, real incomplete, synthetic normal/actionable, both F4 cases, sequential repeats | 10 HTTP 200 including health/ready; all scientific checks passed | 507,760,640 B (484.24 MiB) | 27.76 MiB | 1 |
| Three concurrent large real analyses | 3 HTTP 200, all Unknown | 515,387,392 B (491.51 MiB) | 20.49 MiB | 1 |
| Ten concurrent large real analyses | 6 HTTP 200 Unknown; 4 bounded HTTP 503 `SERVER_BUSY` at about 90 s | **521,707,520 B (497.54 MiB)** | **15,163,392 B (14.46 MiB)** | 1 |
| One real analysis plus nine coverage previews | 10 HTTP 200 | 512,688,128 B (488.94 MiB) | 23.06 MiB | 1 |
| Real F4 request with test-only 0.15 s timeout | Controlled HTTP 503 `PHARMCAT_UNAVAILABLE` | 98,566,144 B (94.00 MiB) | 418.00 MiB | 0 sampled |

Every stage's `memory.events` counters (`low`, `high`, `max`, `oom`, `oom_kill`, `oom_group_kill`) were zero. Docker marked all five containers `OOMKilled=false`. The largest sampled JVM RSS was **312,660 KiB** and largest sampled Python RSS **196,328 KiB**. These are peaks of separate processes at potentially different times and **must not be added** to estimate the cgroup peak. The narrowest observed margin was 14.46 MiB; it is not a guarantee for different inputs, hosts, or architecture.

The 2,475,022-byte public real input was incomplete: coverage returned zero genes passing and no answerable drugs, and analyses returned Unknown. The complete synthetic normal fixture produced a CYP2C19 NM label of `No PGx-guided adjustment identified`; the complete `*2/*2` PM fixture produced `Ineffective`. Frozen read-backed F4 NA18526 (`*1/*1`, NM) and NA12878 (`*1/*2`, IM) matched Prompt 5's exact risk, profile and recommendation fields; only run-variant metadata was outside that scientific comparison. The inputs and their SHA-256 are in `container-summary.json`. Successful burst analyses were also checked for Unknown; the four busy responses were recorded as admission failures, not successful analyses.

The main container's 11th upload returned HTTP 429 `RATE_LIMITED` with `Retry-After: 210`; a new request after the actual five-minute rate window returned 200. The 429 was not counted as a successful analysis. A real JVM was observed during direct cancellation (`PID 881` inside the container); after cancellation no JVM or analysis temp tree remained. The timeout route likewise left no JVM or owned temp/log tree. Post-workload process lists showed only `tini` and `uvicorn`. Logs showed normal Uvicorn shutdown for every owned container. `docker stop --timeout 15` returned zero for each, and each final container state was `exited`, exit code 143 from expected SIGTERM, not OOM. All five owned containers were removed before stopping the isolated VM; final `docker ps -a` was empty and both Colima profiles were stopped.

## Warnings, limitations, and release boundary

The local Docker daemon warned that `--memory-swappiness 0` was unsupported; the actual cgroup `memory.swap.max=0` independently confirmed zero additional swap. The build emitted Docker's legacy-builder deprecation warning; the first owned stop used deprecated `--time` syntax and subsequent stops used `--timeout`. The isolated VM's first boot fetched Ubuntu package metadata slowly. None changed the measured cgroup settings or application bytes. Native Linux/amd64 and Render memory behavior remain **INCONCLUSIVE**; this arm64 measurement cannot certify them. The existing human explanation/author review gate remains incomplete, so this operational PASS does not mean release-ready.

`container-summary.json` is the machine-readable result. The full response bodies, cgroup before/after samples, process RSS samples, container logs, inspect outputs, Docker build output, in-image hashes, rate-limit responses, cancellation receipt, Git snapshots and exit codes are retained in this uniquely named audit directory. Exact commands and exit codes are in `commands.json` and the table appended below.

## Changed files and actions

Only this audit-output directory was added within the repository in Prompt 6 (including the isolated test harness, context, responses and receipts). The new `pgx-p6-20261005` Colima profile and its local image cache remain on disk but are stopped; the pre-existing default profile was not started or changed. There was no production source, test, UI, biological definition, Dockerfile, manifest, hosting, or release-policy edit. Before and after semantics of the candidate are identical; all 437 intended bytes and the tracked Git diff are unchanged. No commit, stage, push, merge, tag, release, deployment, redeployment, remote configuration change, or reviewer contact occurred.

## Exact executed command ledger

These 58 commands ran from the repository root. Exit code 0 means the command completed; expected HTTP 429 and 503 responses are preserved inside response receipts and are not reclassified as successful analyses. Initial read-only runtime checks before authorization are in `runtime-preflight.json`.

| Receipt | Command | Exit |
|---|---|---:|
| `colima-start` | `colima --profile pgx-p6-20261005 start --arch aarch64 --cpus 4 --memory 8 --disk 40 --runtime docker --activate=false --ssh-config=false --mount none` | 0 |
| `docker-build` | `docker --context colima-pgx-p6-20261005 build --platform linux/arm64 -f audit-output/2026-10-05-prompt6-bb6a5821fb/build-context/infra/Dockerfile -t pgx-p6-candidate:20261005 audit-output/2026-10-05-prompt6-bb6a5821fb/build-context` | 0 |
| `image-inspect` | `docker --context colima-pgx-p6-20261005 image inspect pgx-p6-candidate:20261005` | 0 |
| `container-main-start` | `docker --context colima-pgx-p6-20261005 run --detach --name pgx-p6-main-20261005 --restart no --memory 512m --memory-swap 512m --memory-swappiness 0 --publish 127.0.0.1:8768:7860 --env 'JAVA_TOOL_OPTIONS=-Xmx208m -XX:MaxMetaspaceSize=68m' --env MAX_CONCURRENT_PHARMCAT=1 --env PHARMCAT_QUEUE_TIMEOUT_SECONDS=90 --env PHARMCAT_TIMEOUT_SECONDS=120 --env EXPLANATION_MODE=static --env STRICT_PHARMCAT=1 --env PHARMAGUARD_ENV=development pgx-p6-candidate:20261005` | 0 |
| `verify-in-image` | `python3 audit-output/2026-10-05-prompt6-bb6a5821fb/verify_image.py` | 0 |
| `workload-main` | `backend/.venv/bin/python audit-output/2026-10-05-prompt6-bb6a5821fb/workload.py main pgx-p6-main-20261005 8768` | 0 |
| `rate-exhaust` | `backend/.venv/bin/python audit-output/2026-10-05-prompt6-bb6a5821fb/rate_probe.py exhaust` | 0 |
| `container-triple-start` | `docker --context colima-pgx-p6-20261005 run --detach --name pgx-p6-triple-20261005 --restart no --memory 512m --memory-swap 512m --publish 127.0.0.1:8769:7860 --env 'JAVA_TOOL_OPTIONS=-Xmx208m -XX:MaxMetaspaceSize=68m' --env MAX_CONCURRENT_PHARMCAT=1 --env PHARMCAT_QUEUE_TIMEOUT_SECONDS=90 --env PHARMCAT_TIMEOUT_SECONDS=120 --env EXPLANATION_MODE=static --env STRICT_PHARMCAT=1 --env PHARMAGUARD_ENV=development pgx-p6-candidate:20261005` | 0 |
| `triple-ready` | `curl --retry 10 --retry-delay 1 --fail --silent --show-error http://127.0.0.1:8769/ready` | 0 |
| `workload-triple` | `backend/.venv/bin/python audit-output/2026-10-05-prompt6-bb6a5821fb/workload.py triple pgx-p6-triple-20261005 8769` | 0 |
| `triple-post-processes` | `docker --context colima-pgx-p6-20261005 top pgx-p6-triple-20261005 -eo pid,ppid,comm,rss` | 0 |
| `triple-post-temp` | `docker --context colima-pgx-p6-20261005 exec pgx-p6-triple-20261005 sh -c 'find /tmp /home/user/app/tmp -maxdepth 3 \( -name "pharmaguard_pharmcat_*" -o -name "*.log" \) -print'` | 0 |
| `triple-stop` | `docker --context colima-pgx-p6-20261005 stop --time 15 pgx-p6-triple-20261005` | 0 |
| `triple-final-inspect` | `docker --context colima-pgx-p6-20261005 inspect pgx-p6-triple-20261005` | 0 |
| `triple-logs` | `docker --context colima-pgx-p6-20261005 logs pgx-p6-triple-20261005` | 0 |
| `triple-remove` | `docker --context colima-pgx-p6-20261005 rm pgx-p6-triple-20261005` | 0 |
| `container-burst-start` | `docker --context colima-pgx-p6-20261005 run --detach --name pgx-p6-burst-20261005 --restart no --memory 512m --memory-swap 512m --publish 127.0.0.1:8770:7860 --env 'JAVA_TOOL_OPTIONS=-Xmx208m -XX:MaxMetaspaceSize=68m' --env MAX_CONCURRENT_PHARMCAT=1 --env PHARMCAT_QUEUE_TIMEOUT_SECONDS=90 --env PHARMCAT_TIMEOUT_SECONDS=120 --env EXPLANATION_MODE=static --env STRICT_PHARMCAT=1 --env PHARMAGUARD_ENV=development pgx-p6-candidate:20261005` | 0 |
| `burst-ready` | `curl --retry 10 --retry-delay 1 --fail --silent --show-error http://127.0.0.1:8770/ready` | 0 |
| `workload-burst` | `backend/.venv/bin/python audit-output/2026-10-05-prompt6-bb6a5821fb/workload.py burst pgx-p6-burst-20261005 8770` | 0 |
| `rate-recovery` | `backend/.venv/bin/python audit-output/2026-10-05-prompt6-bb6a5821fb/rate_probe.py recovery` | 0 |
| `burst-post-processes` | `docker --context colima-pgx-p6-20261005 top pgx-p6-burst-20261005 -eo pid,ppid,comm,rss` | 0 |
| `burst-post-temp` | `docker --context colima-pgx-p6-20261005 exec pgx-p6-burst-20261005 sh -c 'find /tmp /home/user/app/tmp -maxdepth 3 \( -name "pharmaguard_pharmcat_*" -o -name "*.log" \) -print'` | 0 |
| `burst-stop` | `docker --context colima-pgx-p6-20261005 stop --timeout 15 pgx-p6-burst-20261005` | 0 |
| `burst-final-inspect` | `docker --context colima-pgx-p6-20261005 inspect pgx-p6-burst-20261005` | 0 |
| `burst-logs` | `docker --context colima-pgx-p6-20261005 logs pgx-p6-burst-20261005` | 0 |
| `burst-remove` | `docker --context colima-pgx-p6-20261005 rm pgx-p6-burst-20261005` | 0 |
| `container-mixed-start` | `docker --context colima-pgx-p6-20261005 run --detach --name pgx-p6-mixed-20261005 --restart no --memory 512m --memory-swap 512m --publish 127.0.0.1:8771:7860 --env 'JAVA_TOOL_OPTIONS=-Xmx208m -XX:MaxMetaspaceSize=68m' --env MAX_CONCURRENT_PHARMCAT=1 --env PHARMCAT_QUEUE_TIMEOUT_SECONDS=90 --env PHARMCAT_TIMEOUT_SECONDS=120 --env EXPLANATION_MODE=static --env STRICT_PHARMCAT=1 --env PHARMAGUARD_ENV=development pgx-p6-candidate:20261005` | 0 |
| `mixed-ready` | `curl --retry 10 --retry-delay 1 --fail --silent --show-error http://127.0.0.1:8771/ready` | 0 |
| `workload-mixed` | `backend/.venv/bin/python audit-output/2026-10-05-prompt6-bb6a5821fb/workload.py mixed pgx-p6-mixed-20261005 8771` | 0 |
| `cancellation-input-copy` | `docker --context colima-pgx-p6-20261005 cp test-data/normal_metabolizer_control.vcf pgx-p6-mixed-20261005:/tmp/p6-cancel-input.vcf` | 0 |
| `cancellation` | `backend/.venv/bin/python audit-output/2026-10-05-prompt6-bb6a5821fb/run_cancel.py` | 0 |
| `cancellation-input-remove` | `docker --context colima-pgx-p6-20261005 exec --user root pgx-p6-mixed-20261005 rm /tmp/p6-cancel-input.vcf` | 0 |
| `mixed-post-cgroup` | `docker --context colima-pgx-p6-20261005 exec pgx-p6-mixed-20261005 sh -c 'cat /sys/fs/cgroup/memory.current; cat /sys/fs/cgroup/memory.peak; cat /sys/fs/cgroup/memory.events'` | 0 |
| `mixed-post-processes` | `docker --context colima-pgx-p6-20261005 top pgx-p6-mixed-20261005 -eo pid,ppid,comm,rss` | 0 |
| `mixed-post-temp` | `docker --context colima-pgx-p6-20261005 exec pgx-p6-mixed-20261005 sh -c 'find /tmp /home/user/app/tmp -maxdepth 3 \( -name "pharmaguard_pharmcat_*" -o -name "*.log" -o -name "p6-cancel-input.vcf" \) -print'` | 0 |
| `mixed-stop` | `docker --context colima-pgx-p6-20261005 stop --timeout 15 pgx-p6-mixed-20261005` | 0 |
| `mixed-final-inspect` | `docker --context colima-pgx-p6-20261005 inspect pgx-p6-mixed-20261005` | 0 |
| `mixed-logs` | `docker --context colima-pgx-p6-20261005 logs pgx-p6-mixed-20261005` | 0 |
| `mixed-remove` | `docker --context colima-pgx-p6-20261005 rm pgx-p6-mixed-20261005` | 0 |
| `container-timeout-start` | `docker --context colima-pgx-p6-20261005 run --detach --name pgx-p6-timeout-20261005 --restart no --memory 512m --memory-swap 512m --publish 127.0.0.1:8772:7860 --env 'JAVA_TOOL_OPTIONS=-Xmx208m -XX:MaxMetaspaceSize=68m' --env MAX_CONCURRENT_PHARMCAT=1 --env PHARMCAT_QUEUE_TIMEOUT_SECONDS=90 --env PHARMCAT_TIMEOUT_SECONDS=0.15 --env EXPLANATION_MODE=static --env STRICT_PHARMCAT=1 --env PHARMAGUARD_ENV=development pgx-p6-candidate:20261005` | 0 |
| `timeout-ready` | `curl --retry 10 --retry-delay 1 --fail --silent --show-error http://127.0.0.1:8772/ready` | 0 |
| `workload-timeout` | `backend/.venv/bin/python audit-output/2026-10-05-prompt6-bb6a5821fb/workload.py timeout pgx-p6-timeout-20261005 8772` | 0 |
| `timeout-post-processes` | `docker --context colima-pgx-p6-20261005 top pgx-p6-timeout-20261005 -eo pid,ppid,comm,rss` | 0 |
| `timeout-post-temp` | `docker --context colima-pgx-p6-20261005 exec pgx-p6-timeout-20261005 sh -c 'find /tmp /home/user/app/tmp -maxdepth 3 \( -name "pharmaguard_pharmcat_*" -o -name "*.log" \) -print'` | 0 |
| `timeout-stop` | `docker --context colima-pgx-p6-20261005 stop --timeout 15 pgx-p6-timeout-20261005` | 0 |
| `timeout-final-inspect` | `docker --context colima-pgx-p6-20261005 inspect pgx-p6-timeout-20261005` | 0 |
| `timeout-logs` | `docker --context colima-pgx-p6-20261005 logs pgx-p6-timeout-20261005` | 0 |
| `timeout-remove` | `docker --context colima-pgx-p6-20261005 rm pgx-p6-timeout-20261005` | 0 |
| `main-final-cgroup` | `docker --context colima-pgx-p6-20261005 exec pgx-p6-main-20261005 sh -c 'cat /sys/fs/cgroup/memory.current; cat /sys/fs/cgroup/memory.peak; cat /sys/fs/cgroup/memory.events; cat /sys/fs/cgroup/memory.swap.max'` | 0 |
| `main-post-processes` | `docker --context colima-pgx-p6-20261005 top pgx-p6-main-20261005 -eo pid,ppid,comm,rss` | 0 |
| `main-post-temp` | `docker --context colima-pgx-p6-20261005 exec pgx-p6-main-20261005 sh -c 'find /tmp /home/user/app/tmp -maxdepth 3 \( -name "pharmaguard_pharmcat_*" -o -name "*.log" \) -print'` | 0 |
| `main-stop` | `docker --context colima-pgx-p6-20261005 stop --timeout 15 pgx-p6-main-20261005` | 0 |
| `main-final-inspect` | `docker --context colima-pgx-p6-20261005 inspect pgx-p6-main-20261005` | 0 |
| `main-logs` | `docker --context colima-pgx-p6-20261005 logs pgx-p6-main-20261005` | 0 |
| `main-remove` | `docker --context colima-pgx-p6-20261005 rm pgx-p6-main-20261005` | 0 |
| `owned-container-cleanup` | `docker --context colima-pgx-p6-20261005 ps -a --format '{{.ID}} {{.Names}} {{.Status}}'` | 0 |
| `colima-stop` | `colima --profile pgx-p6-20261005 stop` | 0 |
| `colima-final-state` | `colima list` | 0 |
