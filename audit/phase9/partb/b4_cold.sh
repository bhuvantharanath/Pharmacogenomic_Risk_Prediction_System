#!/usr/bin/env bash
# B4 AC6: one Render cold start, measured only after a verified shutdown.
#
#   audit/phase9/partb/b4_cold.sh <label> <idle-minutes> <outdir>
#
# Waits <idle-minutes> with no traffic from here, reads Render's log for the
# idle window (read-only API) and records whether the instance shut down, then
# probes /health once with a 300 s budget (audit/phase9/live/probe.sh, the Part A
# tool). The probe runs either way; the log decides whether it counts as cold.
set -uo pipefail
label="$1"; idle_min="$2"; out="$3"
repo="$(cd "$(dirname "$0")/../../.." && pwd)"
api="${RENDER_API_HELPER:?set RENDER_API_HELPER to the read-only render_api.py}"
mkdir -p "$out"
idle_start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "$label idle from $idle_start for ${idle_min} min" | tee -a "$out/cold.log"
sleep $(( idle_min * 60 ))
idle_end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$repo/backend/.venv/bin/python" "$api" logs "$idle_start" "$idle_end" "$out/$label.idle_logs.json"
api_rc=$?
echo "$label render log read rc=$api_rc for $idle_start..$idle_end" | tee -a "$out/cold.log"
MAX_TIME=300 "$repo/audit/phase9/live/probe.sh" \
  https://pharmaguard-api-baml.onrender.com/health "$label" "$out/$label"
echo "$label done $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$out/cold.log"
