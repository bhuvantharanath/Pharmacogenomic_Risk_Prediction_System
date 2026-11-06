#!/usr/bin/env bash
# B10 after deploy: live criteria L1-L5 of audit/phase9/B10.log ("Push and live check").
#
#   audit/phase9/partb/b10_live_after.sh <expected-sha>
#
# S1-S6 (six uploads) against the local B10 run, /ready, codeine on NA12273 without and with a supplied CYP2D6 call
# (two uploads), then the web bundle. Every step's exit code is printed.
set -uo pipefail
sha="$1"
repo="$(cd "$(dirname "$0")/../../.." && pwd)"
py="$repo/backend/.venv/bin/python"
out="$repo/audit/phase9/partb/B10"
base=https://pharmaguard-api-baml.onrender.com
"$py" "$repo/audit/phase9/live/measure_warm.py" --base "$base" --out "$out/live-after-s1s6" --phase scenarios
echo "scenarios rc=$?"
"$py" "$repo/audit/phase9/live/verify_postdeploy.py" "$sha" \
  "$out/live-after-s1s6/s1-s6" "$out/s1-s6/s1-s6" > "$out/postdeploy_verification.json"
echo "verify rc=$?"
"$py" "$repo/audit/phase9/partb/b5_live_checks.py" s1s6 \
  "$out/live-after-s1s6/s1-s6" "$out/s1-s6/s1-s6" > "$out/live_s1s6_fields.json"
echo "s1s6 fields rc=$?"
curl -sS -A "curl/8.7.1 (phase9-audit)" "$base/ready" > "$out/live_ready_after_s1s6.json"
echo "ready rc=$?"
"$py" "$repo/audit/phase9/partb/b10_live_checks.py" codeine "$out/live_codeine.json"
echo "codeine rc=$?"
"$py" "$repo/audit/phase9/partb/b10_live_checks.py" bundle "$sha" "$out/live_bundle.json"
echo "bundle rc=$?"
