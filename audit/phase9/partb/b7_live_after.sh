#!/usr/bin/env bash
# B7 after deploy: live criteria L2-L5 of audit/phase9/B7.log ("Push and live check").
#
#   audit/phase9/partb/b7_live_after.sh <expected-sha>
#
# S1-S6 (six uploads), then the CORS checks and the bundle, which upload nothing.
# Every step's exit code is printed.
set -uo pipefail
sha="$1"
repo="$(cd "$(dirname "$0")/../../.." && pwd)"
py="$repo/backend/.venv/bin/python"
out="$repo/audit/phase9/partb/B7"
base=https://pharmaguard-api-baml.onrender.com
"$py" "$repo/audit/phase9/live/measure_warm.py" --base "$base" --out "$out/live-after-s1s6" --phase scenarios
echo "scenarios rc=$?"
"$py" "$repo/audit/phase9/live/verify_postdeploy.py" "$sha" \
  "$out/live-after-s1s6/s1-s6" "$out/s1-s6/s1-s6" > "$out/postdeploy_verification.json"
echo "verify rc=$?"
"$py" "$repo/audit/phase9/partb/b5_live_checks.py" s1s6 \
  "$out/live-after-s1s6/s1-s6" "$out/s1-s6/s1-s6" > "$out/live_s1s6_fields.json"
echo "s1s6 fields rc=$?"
"$py" "$repo/audit/phase9/partb/b7_live_checks.py" cors "$sha" "$out/live_cors.json"
echo "cors rc=$?"
"$py" "$repo/audit/phase9/partb/b7_live_checks.py" bundle "$sha" "$out/live_bundle.json"
echo "bundle rc=$?"
