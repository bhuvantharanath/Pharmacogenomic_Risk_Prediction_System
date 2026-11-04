#!/usr/bin/env bash
# B4 after deploy: warm latency (AC7), then S1-S6 against the local HEAD run.
#
#   audit/phase9/partb/b4_live_after.sh <expected-sha>
#
# Same tool and phase as the pre-deploy baseline (measure_warm.py --phase
# latency, then --phase scenarios). measure_warm.py waits out the rate-limit
# window between phases, so the two runs never share a bucket.
set -uo pipefail
sha="$1"
repo="$(cd "$(dirname "$0")/../../.." && pwd)"
py="$repo/backend/.venv/bin/python"
out="$repo/audit/phase9/partb/B4"
base=https://pharmaguard-api-baml.onrender.com
"$py" "$repo/audit/phase9/live/measure_warm.py" --base "$base" --out "$out/live-after" --phase latency
echo "latency rc=$?"
"$py" "$repo/audit/phase9/live/measure_warm.py" --base "$base" --out "$out/live-after-s1s6" --phase scenarios
echo "scenarios rc=$?"
"$py" "$repo/audit/phase9/live/verify_postdeploy.py" "$sha" \
  "$out/live-after-s1s6/s1-s6" "$repo/audit/phase9/partb/B3/s1-s6/s1-s6" > "$out/postdeploy_verification.json"
echo "verify rc=$?"
