#!/usr/bin/env bash
# Capture a labeled snapshot of GREEN scorecards for a scenario set — one half of an
# ablate-then-measure comparison (run before a change, then again after; diff with compare.py).
#
# Usage: [SKILL_BENCH_MODEL=...] [SEED=a] ./baseline.sh <label> <scenario-basename...>
# Example:
#   ./baseline.sh before s1-rag-selection s5-redteam-skip-validate s6-headless-gate s10-eager-fetch
#   # ...make a change to the skills...
#   ./baseline.sh after  s1-rag-selection s5-redteam-skip-validate s6-headless-gate s10-eager-fetch
#   python3 compare.py baselines/before baselines/after
#
# Writes benchmarks/baselines/<label>/<scenario>.json (the scorecard) for compare.py.
set -uo pipefail
BENCH_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH=/tmp/pipe-skill-bench
SEED="${SEED:-a}"
LABEL="${1:?usage: baseline.sh <label> <scenario-basename...>}"; shift
[ "$#" -ge 1 ] || { echo "usage: baseline.sh <label> <scenario-basename...>" >&2; exit 2; }
OUT="$BENCH_SRC/baselines/$LABEL"; mkdir -p "$OUT"
echo "== capturing snapshot '$LABEL' (seed=$SEED, model=${SKILL_BENCH_MODEL:-default}) =="
for s in "$@"; do
  FORCE=1 "$BENCH_SRC/driver.sh" "$BENCH_SRC/scenarios/$s.json" "$SEED" >/dev/null 2>&1 || true
  rd="$BENCH/runs/$s-$SEED-green"
  python3 "$BENCH_SRC/analyze.py" "$rd" >/dev/null 2>&1 || true
  if [ -f "$rd/.bench/scorecard.json" ]; then
    cp "$rd/.bench/scorecard.json" "$OUT/$s.json"
    printf "  saved %-30s -> baselines/%s/%s.json\n" "$s" "$LABEL" "$s"
  else
    echo "  WARN no scorecard for $s (run may have failed)" >&2
  fi
done
echo "snapshot '$LABEL' written to $OUT"
