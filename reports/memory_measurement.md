# Peak memory — the measurement that chooses the host

Phase 8 §1. Measured **2026-08-13** on the development Mac (Apple Silicon,
macOS 25.6). Every number below is peak **resident** memory across the whole
process tree — uvicorn plus the JVM PharmCAT spawns per request — because that
sum is what a container memory limit counts.

Harness: `scripts/measure_peak_memory.py`. It starts the real app, polls
`/health`, then samples `ps` at 20 Hz across the process tree while a real VCF
goes through `POST /analyze`.

## The caveat that matters

**These are native measurements, not containerised ones.** No container runtime
was installed on this host when they were taken (`docker`, `podman`, `colima`,
`nerdctl`, `lima`, `orbstack` — all absent), so the brief's `docker stats` step
could not be run as written. colima was installed afterwards; the container
figures are in `reports/container_parity.md`. Resident memory of the same processes is the same quantity either way;
what is *not* captured is the container's own overhead and the base image's
page cache. Treat these as a **lower bound** on container RSS.

Two consequences of that gap are called out at the end and remain unverified:
image size and container cold-start.

## Single request

Demo VCF `demo_dpyd_indeterminate.vcf` (199 KB), 3 runs per configuration; the
range across runs is given where it varied.

| `JAVA_TOOL_OPTIONS` | peak RSS | java | python | status |
| --- | ---: | ---: | ---: | --- |
| *(unset — JVM default heap)* | **781.2 MB** | 726.9 | 54.3 | 200 |
| `-Xmx320m -XX:MaxMetaspaceSize=96m` | 470.8–477.6 MB | 416.1 | 54.7 | 200 |
| `-Xmx256m -XX:MaxMetaspaceSize=80m` | 399.0–401.7 MB | 347.0 | 54.6 | 200 |
| `-Xmx224m -XX:MaxMetaspaceSize=72m` | 370.1–376.7 MB | 321.9 | 54.8 | 200 |
| **`-Xmx192m -XX:MaxMetaspaceSize=64m`** | **327.8–333.3 MB** | 275.8 | 54.8 | 200 |
| `-Xmx160m … -XX:+UseSerialGC` | 274.5 MB | 220.1 | 54.4 | **503** |

Unset is the number to notice: the JVM sizes its default max heap from *host*
RAM, so on a 16 GB laptop it helps itself to ~727 MB. A container-aware JVM
would pick ~1/4 of the cgroup limit instead, but relying on that is relying on
an inference; `-Xmx` states it.

## The OOM floor is 176 MB

The 503 above changed four flags at once, so it proved nothing on its own.
Isolated by invoking the jar directly, plain GC, one variable:

| `-Xmx` | 199 KB VCF | 5 MB VCF |
| --- | --- | --- |
| 160m | **OOM** | **OOM** |
| 176m | ok | ok |
| 184m | ok | ok |
| 192m | ok | ok |

```
Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
    at org.pharmgkb.pharmcat.phenotype.Phenotyper.write(Phenotyper.java:172)
    at org.pharmgkb.pharmcat.Pipeline.call(Pipeline.java:352)
```

It dies serialising the phenotype JSON, not parsing the VCF — which is why file
size barely moves it. A 5 MB upload padded to 140 159 data rows did **not**
raise the floor: PharmCAT filters to its own positions first.

So `-Xmx192m` sits **16 MB** above the cliff, and `-Xmx224m` sits 48 MB above it.

## Worst-case single request: a 5 MB upload

`MAX_UPLOAD_BYTES` is 5 MB. Python holds the upload while the JVM runs, so the
worst case is ~70 MB above the demo figure.

| config | peak RSS | headroom under 512 MB |
| --- | ---: | ---: |
| `-Xmx192m` | 401.4–404.6 MB | ~107 MB |
| `-Xmx224m` | 435.7–439.8 MB | ~72 MB |
| `-Xmx256m` | 468.2–471.9 MB | ~40 MB |

## Concurrency is the finding

`app/pharmcat_runner.py:358` spawns PharmCAT with
`asyncio.create_subprocess_exec` and **nothing serialises the calls**. One
uvicorn worker does not mean one JVM: it means one *event loop*, and every
in-flight request gets its own JVM. Peak scales with requests in flight.

At `-Xmx192m`, the tightest configuration that does not OOM, demo VCF:

| in flight | peak RSS | fits 512 MB? |
| ---: | ---: | --- |
| 1 | 321.6 MB | yes |
| **2** | **593.8–636.3 MB** | **no** |
| 3 | 910.2 MB | no |

All requests returned 200 — on a 16 GB laptop. On a 512 MB instance the second
concurrent analysis does not return 503; the kernel OOM-kills the container and
every in-flight request dies with it.

The rate limiter does not help: `security.limiter` is 10 requests per 300 s
**per client key**, which bounds a single client's rate and says nothing about
how many distinct clients are mid-analysis at once. Two browsers, or one
demo audience, is enough.

## With the gate: measured again, 2026-08-13

`MAX_CONCURRENT_PHARMCAT=1`, `-Xmx192m -XX:MaxMetaspaceSize=64m`, same harness.
Peak stops tracking concurrency, which was the whole objective:

| in flight | before | after | wall clock |
| ---: | ---: | ---: | ---: |
| 1 | 321.6 MB | 336.3 MB | 1.53 s |
| 2 | 593.8 MB | **338.1 MB** | 2.72 s |
| 3 | 910.2 MB | **338.0 MB** | 4.10 s |
| 5 | — | **347.4 MB** | 6.79 s |

Every request returned 200. Wall time grows linearly because the analyses now
queue, which is the trade being made: latency under contention in exchange for
not being OOM-killed.

**Headroom against 512 MB: ~165 MB (32%) at 5 concurrent demo-sized uploads.**

### The residual, stated plainly

The gate bounds the JVM. It does **not** bound the uploads, because only the
subprocess is serialised — coverage checks, mapping and response assembly stay
concurrent by design. Python therefore holds one 5 MB upload per in-flight
request:

| concurrent 5 MB uploads | peak | fits 512 MB? |
| ---: | ---: | --- |
| 1 | 386.9 MB | yes |
| 3 | 416.6 MB | yes |
| 6 | 455.7 MB | yes |
| **10** | **521.9 MB** | **no** |

At 10, one request also shed cleanly as 503 SERVER_BUSY when the 25 s queue
bound expired — the intended behaviour, and evidence the bound works.

So the safe envelope is roughly **eight simultaneous maximum-size uploads**.
Reaching it needs eight distinct clients uploading 5 MB files within the same
few seconds; the per-client rate limit (10 per 300 s) does not prevent it,
because it is keyed per client. For a demo this is comfortable. It is recorded
rather than fixed because bounding uploads too was not asked for, and would
trade a real cost — refusing a legitimate second visitor at the door — against
a scenario that needs eight coordinated ones.

## What this means for the host

* **Serial traffic fits Render.** 322 MB typical, ~405 MB for a maximal upload,
  against 512 MB.
* **Concurrent traffic does not.** Two overlapping analyses exceed the limit at
  every heap setting that works at all.

Bounding PharmCAT to one concurrent invocation fixes it. That is an application
behaviour change, which Phase 8 excluded by default; it was put to the project
owner with these measurements and **approved**, scoped to the subprocess only.
Implemented in `pharmcat_runner._exec`; the result is the "with the gate"
section above. **Render is therefore the host.**

## Not measured here

Native uvicorn startup to first healthy `/health` was **0.26–0.54 s**, which
excludes image pull, container create and JVM warm-up. It is not comparable to a
platform cold start and should not be quoted as one.

Image size, container cold start and the in-container test run are Phase 8 §2 —
see `reports/container_parity.md`.
