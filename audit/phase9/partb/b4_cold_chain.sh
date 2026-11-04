#!/usr/bin/env bash
# Runs AC6's two cold starts back to back, starting only after the post-deploy
# measurement has sent its last request (so the idle window is real).
set -uo pipefail
repo="$(cd "$(dirname "$0")/../../.." && pwd)"
after="$repo/audit/phase9/partb/B4.live-after.stdout"
until grep -q "^rc=" "$after" 2>/dev/null; do sleep 10; done
out="$repo/audit/phase9/partb/B4/cold"
"$repo/audit/phase9/partb/b4_cold.sh" cold1 20 "$out"
"$repo/audit/phase9/partb/b4_cold.sh" cold2 20 "$out"
echo "chain done"
