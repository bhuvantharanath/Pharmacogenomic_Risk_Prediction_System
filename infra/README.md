# Infrastructure

## Hosting plan (free tier only)

The two halves deploy to two different free services. The **backend** goes to a
[Hugging Face Space](https://huggingface.co/spaces) using the Docker SDK: push
this repo with `infra/Dockerfile` as the Space's Dockerfile, and HF builds the
image and serves it on port 7860 at `https://<user>-<space>.hf.space` — no card
required, and the Space is big enough for a JRE plus the PharmCAT JAR in Phase 2
(it sleeps when idle, so expect a cold start of a few tens of seconds on the
first request after a nap). The **Flutter web build** goes to
[Cloudflare Pages](https://pages.dev): run `flutter build web --release
--dart-define=PHARMAGUARD_API_BASE_URL=https://<user>-<space>.hf.space` and
upload `app/build/web` (or point Pages at the repo with that as the build output
directory). The backend's CORS policy already allows `*.pages.dev`, including
per-branch preview deployments, so no backend change is needed to go live.
Android/iOS builds come from the same `app/` codebase and need no hosting at all.

## Files

| File | Purpose |
| --- | --- |
| `Dockerfile` | Backend image, port 7860, HF Spaces conventions. Build from the **repo root**: `docker build -f infra/Dockerfile -t pharmaguard-api .` |

## Deploy notes

- **Build context is the repo root**, because the Dockerfile copies from
  `backend/`. Building from inside `infra/` will fail.
- **Port 7860** is a Hugging Face convention, not a preference. Locally the app
  runs on 8000; only the container uses 7860.
- **No secrets are needed in Phase 1.** The stub backend makes no outbound
  network calls. When Phase 3 adds an LLM, set `GEMINI_API_KEY` as a Space
  *secret* (Settings → Variables and secrets), never as a build arg and never in
  the image.
- **Check the deployed API before pointing the app at it:**
  `curl https://<user>-<space>.hf.space/health` should return `{"status":"ok"}`.
