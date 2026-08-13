# Deployment notes

Verified platform facts, the deploy steps, and the things that will bite you.
Everything dated was checked against vendor documentation on **2026-07-23**.

---

## THE DECISION, AND THE NAMES (Phase 8, 2026-08-13)

**Backend: Render. Frontend: Cloudflare Pages.** Chosen on measurement, not
preference — see `reports/memory_measurement.md` and
`reports/container_parity.md`.

| | name | URL |
| --- | --- | --- |
| Backend | `pharmaguard-api` | `https://pharmaguard-api.onrender.com` |
| Frontend | `pharmaguard-web` | `https://pharmaguard-web.pages.dev` |

### Fix the names first — it breaks a circular dependency

The backend needs `CORS_ALLOWED_ORIGINS` set to the frontend's origin. The
frontend needs `API_BASE_URL` baked in at compile time pointing at the backend.
Deploy either one first and it is configured wrong.

There is no ordering that solves this, because it is not an ordering problem.
Both hosts derive the URL **deterministically from a name you choose**:
Render serves `<service>.onrender.com`, Pages serves `<project>.pages.dev`. So
pick both names up front, write both URLs down, and configure both services
before either exists. Neither has to be deployed for the other to be correct.

The corollary: **renaming either service silently breaks the pair.** The
frontend's URL is compiled into the bundle, so a renamed backend keeps serving a
client that points at the old hostname until someone rebuilds.

### The configuration that was measured, not guessed

| variable | value | why |
| --- | --- | --- |
| `JAVA_TOOL_OPTIONS` | `-Xmx256m -XX:MaxMetaspaceSize=80m` | The JVM's default max heap comes from HOST RAM — 727 MB measured on a 16 GB laptop, instant death on a 512 MB instance. PharmCAT OOMs at 160m, survives from 176m; 256m keeps 80 MB of margin and measured *lower* in-container than 192m (252.8 vs 289.2 MiB) because a bigger heap means less GC pressure. |
| `MAX_CONCURRENT_PHARMCAT` | `1` | Each in-flight `/analyze` spawns its own JVM. Same image, same hard 512 MB limit, 3 concurrent requests: at `1`, 252.8 MiB and survives; at `3`, **OOMKilled=true** and two requests lost. |
| `PHARMCAT_QUEUE_TIMEOUT_SECONDS` | `25` | Bounded wait. An unbounded one is indistinguishable from a hang at the client. Analyses take ~2.6 s in-container. |
| `CORS_ALLOWED_ORIGINS` | `https://pharmaguard-web.pages.dev` | Empty + hosting markers = refuses to start, on purpose. |
| `EXPLANATION_MODE` | `static` | No outbound call, no API key. |
| `STRICT_PHARMCAT` | `1` | A failed deploy is cheaper than a silently broken one. |

**No API key of any kind is set, and none is needed.** The deployed path calls no
LLM; `requirements-llm.txt` is not installed in the image.

### Measured facts worth keeping

| | |
| --- | --- |
| Image size | **6.01 GB** uncompressed (base `pgkb/pharmcat:3.4.0` is 5.96 GB; our layers ~45 MB) |
| Container peak, 3 concurrent, 512 MB limit | **252.8 MiB (49%)** |
| Idle | 40.2 MiB |
| Container cold start (image local) | **1.19 s** to healthy `/health` |
| Analysis latency in-container | ~2.6 s |
| In-container suite | 747 passed, 3 failed, 5 skipped — all 3 are the absent spaCy model, excluded from the production image by design |

### Two traps this cost us

**The jar the container ran was not the jar the tests validated.**
`find_jar()` globs `pharmcat-*-all.jar`; the base image ships
`/pharmcat/pharmcat.jar`. Resolution fell through to the `pharmcat_pipeline`
wrapper, which runs a VCF preprocessor the test suite never exercises. Both
paths return 200, so nothing caught it. Fixed with an explicit
`ENV PHARMCAT_JAR` plus a build-time `sha256sum -c`.

**Dio's `validateStatus` was `< 500`,** so every 503 threw before its body was
read and reached the user as "Network error talking to …". Both of the
backend's most user-visible states are 503s.

### Free-tier limits, and the keepalive

Render free gives **750 instance-hours** against a month of ~730 hours. A
keepalive pinging every 10 minutes holds the container resident essentially all
month, which leaves almost no margin — a second service, or overlapping
re-deploys, tips it over. Bandwidth overages are billable even on free accounts.

`.github/workflows/keepalive.yml` therefore ships with its `schedule:` block
**commented out** and `workflow_dispatch` only. Uncomment it for the submission
window or a recording; comment it back afterwards.

### Redeploying

```bash
# Backend: Render rebuilds on push to the tracked branch. To force one:
#   Render dashboard -> pharmaguard-api -> Manual Deploy -> Deploy latest commit

# Frontend: rebuild with the URL compiled in, then upload.
cd app
flutter build web --release --base-href "/" \
  --dart-define=API_BASE_URL=https://pharmaguard-api.onrender.com
grep -rqF "https://pharmaguard-api.onrender.com" build/web/ || echo "DEFINE DID NOT APPLY"
npx wrangler pages deploy build/web --project-name=pharmaguard-web
```

The `grep` is not paranoia: a `--dart-define` that silently failed to apply
produces a bundle that looks healthy until someone clicks Analyze.

### The Blueprint

`infra/render.yaml`, symlinked to `render.yaml` at the repo root because that is
where Render's Blueprint scanner looks. Every value above lives there with the
measurement that produced it, so recreating the service does not mean
rediscovering them.

---

## ⚠️ Read this first: Hugging Face Docker Spaces are no longer free

The Phase 1–3 plan assumed a free HF Docker Space. **That is no longer true.**
From [HF's Spaces overview](https://huggingface.co/docs/hub/spaces-overview):

> Static Spaces are free for everyone. **Gradio and Docker Spaces run on compute
> and require a paid plan to create: PRO for personal accounts**, Team or
> Enterprise for organizations.

So a Docker Space needs **HF PRO ($9/month)**. The free exception is 2 Gradio
Spaces on ZeroGPU, which does not help us — PharmaGuard is a FastAPI service
wrapping a Java process, not a Gradio app.

The Space config in `infra/hf-space/README.md` is correct and ready if you have
or want PRO. If you need genuinely free hosting, use one of the alternatives
below. **The same image works on all of them** — the container reads `$PORT`
with a 7860 fallback, so nothing needs rebuilding per host.

### Backend hosting options compared

| Option | Free? | RAM | Cold start | Catch |
| --- | --- | --- | --- | --- |
| **HF Spaces (Docker)** | ❌ needs PRO | 16 GB, 2 vCPU | ~1 min | The documented plan; no longer free |
| **Google Cloud Run** | ✅ genuinely | configurable (set 2 GB) | ~10-30 s | Needs a billing account (card on file) even though usage is free |
| **Render** | ✅ no card | 512 MB | ~1 min | 512 MB is tight for a JVM; 750 instance-hrs/month |
| **Fly.io** | ⚠️ trial credit only | configurable | fast | No longer a standing free tier |

**Recommendation: Cloud Run.** Its always-free tier is 2 M requests, 180 k
vCPU-seconds and 360 k GiB-seconds per month — far beyond a demo — and you can
give the container the ~2 GB it wants for a JVM. The cost is that Google
requires a billing account on file. If you will not add a card, use Render and
set `JAVA_TOOL_OPTIONS=-Xmx320m` to fit the JVM into 512 MB; expect PharmCAT to
be slow and to occasionally OOM on larger VCFs.

---

## 1. Backend → Hugging Face Spaces (if you have PRO)

### Free-tier / CPU Basic limits (verified)

- **2 vCPU, 16 GB RAM, 50 GB ephemeral disk** (CPU Basic)
- **Sleeps when idle**; the first request after a nap pays the container start
- **Filesystem is ephemeral** — data written at runtime is lost on restart.
  Fine for us: we retain nothing by design.
- Outbound network is restricted to ports **80, 443 and 8080**
- Container runs as **UID 1000** — see the permissions section below

### Steps

```bash
# 1. Create the Space (web UI): SDK = Docker, visibility = public.
#    https://huggingface.co/new-space

# 2. Clone it and copy the app in.
git clone https://huggingface.co/spaces/YOURNAME/pharmaguard hf-space
cd hf-space

cp -r ../pharmaguard/backend    ./backend
cp -r ../pharmaguard/rag-corpus ./rag-corpus
cp    ../pharmaguard/infra/Dockerfile      ./Dockerfile
cp    ../pharmaguard/infra/hf-space/README.md ./README.md   # the YAML front matter

# 3. Push. HF builds on push.
git add -A && git commit -m "Deploy PharmaGuard API" && git push
```

> The Dockerfile lives at `infra/Dockerfile` here but must be at the **root** of
> the Space repo, and it expects the repo root as its build context — which is
> exactly what the layout above gives it.

### Space configuration (Settings → Variables)

None are required. Set these to lock things down:

| Variable | Value |
| --- | --- |
| `CORS_ALLOWED_ORIGINS` | `https://pharmaguard.pages.dev` |
| `CORS_ALLOW_PAGES_PREVIEWS` | `pharmaguard` *(optional, for preview branches)* |
| `RATE_LIMIT_REQUESTS` | `10` |

**Do not set `GEMINI_API_KEY`.** The deployed path is `EXPLANATION_MODE=static`,
which makes no API call. The app logs a warning if it finds a key it does not
need, and **refuses to start** if it finds a `.env` file inside the image.

### The permissions gotcha

HF's [Docker Spaces guide](https://huggingface.co/docs/hub/spaces-sdks-docker)
is explicit:

> The container runs with user ID 1000. To avoid permission issues you should
> create a user and set its `WORKDIR` before any `COPY` or download.

Our Dockerfile does this, with one deviation worth knowing: it creates/reuses
uid 1000 **by number**, not by name, because the `pgkb/pharmcat` base image
already ships its own `pharmcat` user whose uid we do not control.

It also sets `TMPDIR=/home/user/app/tmp` rather than relying on `/tmp`, because
PharmCAT writes working files per request and a platform that mounts `/tmp`
read-only would otherwise fail at first analysis rather than at startup.

HF also warns that a recursive `chown` duplicates every affected file into a new
layer. We use `COPY --chown=1000:1000` throughout for that reason.

### Build timeout

The `pgkb/pharmcat` base is ~2 GB, and a cold build can exceed the default
30-minute startup budget. The Space README sets:

```yaml
startup_duration_timeout: 1h
```

---

## 2. Backend → Google Cloud Run (recommended free option)

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT

# Build and push (Cloud Build does the work; no local Docker needed).
gcloud builds submit --tag gcr.io/YOUR_PROJECT/pharmaguard-api

gcloud run deploy pharmaguard-api \
  --image gcr.io/YOUR_PROJECT/pharmaguard-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 2 \
  --set-env-vars "EXPLANATION_MODE=static,CORS_ALLOWED_ORIGINS=https://pharmaguard.pages.dev"
```

- `--min-instances 0` keeps it in the free tier and means it scales to zero,
  so cold starts happen. That is what the client's waking UI is for.
- `--max-instances 2` is a spend guard: without it a traffic spike (or a bot)
  could scale out past the free allowance.
- **2 GiB** because PharmCAT starts a JVM per request. 512 MiB will OOM.
- The container honours Cloud Run's injected `$PORT`; no rebuild needed.

---

## 3. Frontend → Cloudflare Pages

Cloudflare Pages has a genuinely free tier: unlimited requests and bandwidth,
500 builds/month.

### Automated (GitHub Actions)

`.github/workflows/deploy-web.yml` runs on pushes to `main` that touch `app/`.

> **Action choice, verified 2026-07-23:** it uses
> `cloudflare/wrangler-action@v3` with a `pages deploy` command.
> Cloudflare's older `pages-action` is **deprecated** (final release v1.5.0) and
> their docs now point at wrangler-action. Do not "fix" this backwards.

Repository secrets:

| Secret | Where to get it |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | My Profile → API Tokens → Create → *Account · Cloudflare Pages · Edit* |
| `CLOUDFLARE_ACCOUNT_ID` | Workers & Pages → right sidebar |
| `API_BASE_URL` | Your backend URL, e.g. `https://YOURNAME-pharmaguard.hf.space` |

Create the Pages project once before the first run:

```bash
npx wrangler pages project create pharmaguard --production-branch main
```

### Manual fallback

If the Action is fiddly, this is the whole deploy:

```bash
cd app
flutter build web --release --base-href "/" \
  --dart-define=API_BASE_URL=https://YOURNAME-pharmaguard.hf.space

npx wrangler pages deploy build/web --project-name=pharmaguard
```

Or drag `app/build/web` onto the Pages dashboard's upload area.

### base-href

Cloudflare Pages serves the project at the domain **root**
(`pharmaguard.pages.dev/`), so `--base-href "/"` is correct — and it is the
default. Flutter bakes the value into `index.html` at build time, so if you ever
serve under a subpath you must rebuild, not just move files:

```bash
flutter build web --release --base-href "/pharmaguard/"   # verified: writes <base href="/pharmaguard/">
```

Both variants were built and the emitted `<base href>` checked.

---

## 4. Android APK

### Generate a keystore (once)

```bash
keytool -genkey -v -keystore ~/pharmaguard-release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias pharmaguard
```

> 🔐 **The keystore and `key.properties` must never be committed.** Both are
> gitignored (`app/android/.gitignore`). Losing the keystore means you can never
> ship an update to an already-installed app; leaking it lets someone else
> publish as you. Back it up somewhere private and durable — **not this repo**.

Then create `app/android/key.properties` (gitignored):

```properties
storePassword=<your store password>
keyPassword=<your key password>
keyAlias=pharmaguard
storeFile=/absolute/path/to/pharmaguard-release.jks
```

### Build

```bash
# Gradle 8.14 does not support JDK 25 — it fails with a bare "25.0.1" as the
# entire error message, which is baffling the first time. Use JDK 17.
export JAVA_HOME=/opt/homebrew/opt/openjdk@17

cd app
flutter build apk --release \
  --dart-define=API_BASE_URL=https://YOURNAME-pharmaguard.hf.space
```

Output: `app/build/app/outputs/flutter-apk/app-release.apk` (**~51 MB**, verified).

### Verified APK properties

| Property | Value |
| --- | --- |
| `package` | `com.pharmaguard.app` |
| `versionName` | `1.0.0` (`versionCode` 1) |
| label | PharmaGuard |
| permissions | `INTERNET`, `ACCESS_NETWORK_STATE` — nothing else |
| cleartext HTTP | disabled, except loopback (see `network_security_config.xml`) |
| backups | disabled |

Confirm the backend URL really made it into the binary — a `--dart-define` that
silently failed produces an APK that looks fine and points at localhost:

```bash
unzip -oq app-release.apk -d /tmp/apk && grep -ra "hf.space" /tmp/apk/lib/ | head
```

Release builds are AOT-compiled, so the string is in `lib/*/libapp.so`, **not**
in `kernel_blob.bin` — searching the wrong file will wrongly suggest failure.

### Signing without a keystore

If `android/key.properties` is absent, the release build falls back to the debug
key and logs that it did. The APK still installs and runs; it is simply not a
distributable release. That keeps `flutter build apk --release` working on a
fresh clone instead of failing on a missing optional file.

`.github/workflows/build-apk.yml` follows the same rule: it signs properly when
the four `ANDROID_*` secrets exist, and otherwise builds a debug-signed APK and
labels it as such in the release notes.

### Distribution

GitHub Releases, sideloaded. **Play Store is out of scope** — it needs the
one-time $25 Google Play Developer registration, and this is an unfunded
academic project.

---

## 5. iOS

The iOS target is configured (bundle name `PharmaGuard`, Podfile and workspace
present, `flutter analyze` clean), but **the simulator build was NOT verified
here** — this machine has Xcode 26.6 with **no iOS simulator runtimes installed**:

```
$ xcrun simctl list runtimes
== Runtimes ==
              (empty)

$ flutter build ios --simulator
Unable to find a destination matching the provided destination specifier
  error: iOS 26.5 is not installed. Please download and install the platform
         from Xcode > Settings > Components.
```

**Fix (needs you — it is a multi-GB download and may prompt for your password):**

```
Xcode → Settings → Components → install an iOS Simulator runtime
```

Then:

```bash
cd app
open -a Simulator
flutter run -d iphone
```

Nothing in the Dart or plugin configuration is implicated — the failure is
purely the missing platform component. Verify once the runtime is installed.

**App Store distribution is deliberately out of scope.** It requires the Apple
Developer Program at **$99/year**, and even installing on a physical device
needs a signing identity (a free personal team works, but the build expires
after 7 days). Neither fits a free-tier project. The Android APK is the
installable artifact; iOS is demonstrated in the Simulator.

---

## 6. Cold starts

The single largest demo risk. Three mitigations, in order of importance:

1. **Honest UI (`app/lib/api/backend_status.dart`).** The client pings
   `/health` on load and shows *"Waking up the analysis server — the server
   sleeps when idle to stay on the free tier. The first request after a nap can
   take up to a minute"* with a progress bar and attempt counter. Retries with
   front-loaded backoff for 90 seconds before declaring failure. A bare spinner
   would look identical to a hang.

2. **`/health` is trivial.** No PharmCAT, no disk, no subprocess — so the
   wake-up ping is cheap and a still-booting container does not report itself
   unhealthy. Use `/ready` when you actually need to know if an analysis would
   work; it checks PharmCAT, the corpus, the explanation store and the label
   mapping, and returns 503 with a per-dependency breakdown.

3. **`.github/workflows/keepalive.yml`.** Pings `/health` every 10 minutes.
   **Turn it off outside demo periods** — on Render it would eat the
   750 instance-hours/month, and it warms a container nobody is watching. Note
   that GitHub disables scheduled workflows after 60 days of repo inactivity and
   does not guarantee cron punctuality, so treat it as best-effort.

---

## 7. Security posture

| Control | Implementation |
| --- | --- |
| CORS | Explicit allowlist from `CORS_ALLOWED_ORIGINS`. **No wildcard.** Localhost always allowed for dev |
| Rate limit | 10 analyses / 5 min / client IP, in-memory, returns 429 + `Retry-After` |
| Headers | `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`, `Permissions-Policy` |
| Secrets | None required. Startup **fails** on a `.env` in the image; warns on an unused key |
| Data retention | None. Temp dir deleted in a `finally`; asserted by test |

Phases 1–3 allowed any `*.pages.dev` origin by regex. On localhost that is
harmless; on a public URL it lets an attacker deploy a Pages site and call this
API from a visitor's browser. Phase 4 names origins explicitly, and
`test_deployment.py` asserts that `https://attacker-site.pages.dev` is rejected.

### Rate limiter honesty

It is in-memory and keyed on `X-Forwarded-For`, which is caller-controlled. That
is abuse *dampening*, not a security boundary — it stops a casual scraper
burning the free-tier budget. It resets on container restart, which on a
scale-to-zero host is often. Real protection needs a shared store and a trusted
proxy; both are out of scope here, and pretending otherwise would be worse than
saying so.

---

## 8. Verified locally

Confirmed on this machine, against a real PharmCAT and a real browser:

- ✅ `/health` responds in **0.8 ms**, with no PharmCAT dependency
- ✅ `/ready` returns per-dependency JSON; 503 when PharmCAT is absent
- ✅ Security headers present on success **and** error responses
- ✅ CORS: `pharmaguard.pages.dev` allowed, `attacker-site.pages.dev` and
  `evil.example.com` rejected — checked at the raw header level
- ✅ Rate limit: requests 1-3 → 200, 4-5 → 429 with `Retry-After`
- ✅ Temp dirs empty after a request, **and** after a simulated PharmCAT crash
- ✅ Cold-start UI: waking state → automatic recovery to ready, no reload
- ✅ Browser POST from `http://127.0.0.1:5000` through the allowlist → 200
- ✅ Release APK builds (51.4 MB), correct package/permissions, URL in all
  three ABIs
- ✅ Web build for both `/` and `/pharmaguard/` base-hrefs

**Not verified** (needs your accounts, or Docker):

- ❌ The Docker image has never been **built** — Docker is not installed here.
  The Dockerfile is written against verified HF/Cloud Run requirements but is
  unexercised. Build it once before relying on it.
- ❌ No HF Space, Cloudflare Pages project, or Cloud Run service exists. Every
  deploy step above is written from vendor docs, not from a completed deploy.
- ❌ The GitHub Actions workflows have never run — no git repo, no remote.
- ❌ The APK has not been installed on a physical device.
