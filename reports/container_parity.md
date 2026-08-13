# Container parity — running the suite inside the image

Phase 8 §2. Measured **2026-08-13**, colima 0.9 / Docker 29.5.2 on Apple
Silicon. Image `pharmaguard-api:phase8`, built from `infra/Dockerfile`.

Nobody had run the tests in the container before. The point of doing so is not
to re-confirm that the code works — it is to find the places where the container
is a *different environment* from the one every test result came from.

It found one, and it mattered.

## The finding: the container ran a different PharmCAT invocation

`resolve_invoker()` inside the freshly built image reported:

```
find_jar() -> None
invoker kind -> wrapper
describe     -> /pharmcat/pharmcat_pipeline
```

`find_jar()` searches for `pharmcat-*-all.jar` under a fixed list of
directories. The base image installs the jar as **`/pharmcat/pharmcat.jar`** — a
filename the glob does not match, in a directory not on the list. Resolution
therefore fell through to the `pharmcat_pipeline` wrapper.

Both paths produce results, which is precisely why this survived: `/ready` was
green, `/analyze` returned 200, and nothing anywhere said "by the way, this is
not the code path you tested". But the wrapper runs PharmCAT's **VCF
preprocessor** first, and every one of this project's validation numbers —
integration fidelity, the coverage sweep, the 294 corrected labels — was
produced by `java -jar` with no preprocessing.

**The deployed image was exercising an invocation the suite has never covered.**

### Fixed in configuration, not in code

The jar the base image ships is byte-identical to the one the repository
validated against:

```
9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741  /pharmcat/pharmcat.jar
9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741  test-data/reference/tools/pharmcat-3.4.0-all.jar
```

So the fix is to point at it — `ENV PHARMCAT_JAR=/pharmcat/pharmcat.jar` — plus
a build-time `sha256sum -c` and a `-version` grep, so the build fails if that
jar ever stops being the validated one. That is a stronger guarantee than the
brief's "fetch it at build time with a checksum": the artifact is already pinned
by the base image tag, and now the bytes are pinned too.

After the change:

```
invoker kind -> jar
describe     -> java -jar /pharmcat/pharmcat.jar
```

## The suite, inside the image

Run against the real repository layout (bind-mounted, so path-dependent tests
see what they expect) using the container's own Python, Java and PharmCAT:

```
docker run --rm -v "$PWD":/repo -w /repo/backend \
  -e CORS_ALLOWED_ORIGINS=https://pharmaguard-web.pages.dev \
  -e PHARMCAT_JAR=/pharmcat/pharmcat.jar \
  -e PHARMAGUARD_CORPUS_DIR=/repo/rag-corpus/mechanisms \
  pharmaguard-test:phase8 python3 -m pytest -q
```

**747 passed, 3 failed, 5 skipped.** All three failures share one root cause and
none affects the deployed service:

| failing test | cause |
| --- | --- |
| `test_provenance_policy … detects_a_fabricated_mechanism_entity` | spaCy model `en_core_web_sm` absent |
| `test_provenance_policy … it_does_not_gate` | same |
| `test_documented_numbers … test_counts_match_the_suite` | collects 750 not 771, because the spaCy-dependent modules skip |

`en_core_web_sm` is absent **by design**: the mechanism vocabulary check is a
build-time authoring tool, `requirements-dev.txt` is deliberately not installed
in the production image, and a test already proves the app boots with the import
blocked. The deployed service never runs this code.

One earlier failure was **my harness, not the container**: passing
`PHARMAGUARD_ENV=development` disabled the CORS guard, so
`test_guard_still_fires_on_hosting_markers_with_empty_allowlist` did not raise.
Without that variable it passes — which is itself the confirmation §2 wanted.

## Startup refuses loudly, in the container

| condition | result |
| --- | --- |
| `CORS_ALLOWED_ORIGINS=""` with `PORT` set | `Application startup failed. Exiting.` — names Render, compose and the `PHARMAGUARD_ENV=development` escape hatch |
| PharmCAT absent, `STRICT_PHARMCAT=1` | `RuntimeError: [startup] FATAL: … Fix: … or set PHARMCAT_JAR=…` |

Both messages name what to change. Neither reaches a user: they are startup
logs, which is why `_assert_single_worker` is on the operator-only list in
`scripts/glossary_lib.py`.

## Image, user, secrets

| check | result |
| --- | --- |
| user | `uid=1000 gid=1000` (`user`), non-root |
| `$TMPDIR` | `/home/user/app/tmp`, writable |
| `/etc` | not writable — good |
| `.env*` under `/home/user` | none |
| credential-shaped env vars | none, in the running container or in `Config.Env` |
| layer scan (API-key, private-key patterns) | **no matches** in our layers |

**Image size: 6.01 GB uncompressed**, of which the `pgkb/pharmcat:3.4.0` base is
**5.96 GB** — our layers add ~45 MB, and 43 MB of that is pip.

The Dockerfile said "~1.97 GB on Docker Hub". That is the **compressed** figure;
uncompressed on disk it is three times larger. Corrected in the Dockerfile,
because it is the number that matters for a host with a build-disk limit.

## Memory, under a real 512 MB limit

`--memory 512m --memory-swap 512m`, i.e. Render free with no swap to hide behind.

| state | `docker stats` | OOM-killed |
| --- | ---: | --- |
| idle | 40.2 MiB (7.8%) | no |
| 1 analysis + 3 concurrent, `MAX_CONCURRENT_PHARMCAT=1` | **286.9 MiB (56.0%)** | **no** |

Concurrent request timings — 2.58 s, 5.23 s, 7.79 s — are the queue working:
each waits for the one before it.

### The gate, proven by removing it

Same image, same 512 MB limit, same three concurrent requests, only
`MAX_CONCURRENT_PHARMCAT=3`:

```
HTTP 503 in 1.22s
HTTP 503 in 1.22s
HTTP 200 in 3.35s
OOMKilled=true
```

The container was killed by the kernel and two requests died with it. This is
the §1 finding reproduced in the real artifact on the real limit, and it is the
evidence that the semaphore is load-bearing rather than defensive.

**Container cold start: 1.19 s** from `docker run` to a healthy `/health`, with
the image already local. It excludes image pull and platform scheduling, so it
is a floor for Render's cold start, not a prediction of it.

## What is still not verified here

* **Architecture.** This image is `linux/arm64`; Render builds `linux/amd64`.
  The base image is multi-arch (both manifests present), so the same Dockerfile
  applies, but the amd64 image size and timings are unmeasured.
* **Platform cold start** on Render, which includes pulling ~6 GB.
