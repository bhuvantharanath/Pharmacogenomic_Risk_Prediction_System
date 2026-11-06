#!/usr/bin/env bash
# B9 after deploy: live criteria L1-L5 of audit/phase9/B9.log ("Push and live check").
#
#   audit/phase9/partb/b9_live_after.sh <expected-sha>
#
# S1-S6 (six uploads) against the local B9 run, /ready, the web bundle, then the live responses exported and
# validated. Every step's exit code is printed.
set -uo pipefail
sha="$1"
repo="$(cd "$(dirname "$0")/../../.." && pwd)"
py="$repo/backend/.venv/bin/python"
out="$repo/audit/phase9/partb/B9"
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
"$py" "$repo/audit/phase9/partb/b9_live_checks.py" bundle "$sha" "$out/live_bundle.json"
echo "bundle rc=$?"
"$py" "$repo/audit/phase9/partb/b9_live_checks.py" exports "$out/live-after-s1s6/s1-s6" "$out/live_exports_validation.json"
echo "exports rc=$?"
