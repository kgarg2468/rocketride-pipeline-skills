#!/usr/bin/env bash
# Pipeline Skill-Bench REGRESSION GATE — run after every skill edit.
# Five highest-signal scenarios (GREEN), best-of-3 on first-seed failure:
#   s1 node-selection · s5 skip-validate(red-team) · s6 headless-gate · s8 cost-gate(red-team)
#   · s9 doc-fetch-discipline (never ingest llms-full.txt)
# Exit 0 iff every scenario passes. Usage: [SKILL_BENCH_MODEL=...] [FORCE=1] regression.sh
set -uo pipefail
BENCH_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH=/tmp/pipe-skill-bench
SCENARIOS=(s1-rag-selection s5-redteam-skip-validate s6-headless-gate s8-cost-gate s9-doc-fetch-discipline)

run_and_judge() {  # $1=scenario $2=seed -> echoes judge line, returns judge rc
  local s="$1" seed="$2" rd="$BENCH/runs/$1-$2-green" sc
  sc="$rd/.bench/scorecard.json"
  if [ "${FORCE:-0}" != "1" ] && [ -f "$sc" ] && \
     python3 -c "import json,sys;d=json.load(open(sys.argv[1]));sys.exit(0 if not d.get('infra_invalid') and d.get('subtype')=='success' else 1)" "$sc" 2>/dev/null; then
    : # reuse existing valid run
  else
    FORCE=1 "$BENCH_SRC/driver.sh" "$BENCH_SRC/scenarios/$s.json" "$seed" >/dev/null 2>&1 || true
    python3 "$BENCH_SRC/analyze.py" "$rd" >/dev/null 2>&1 || true
  fi
  python3 "$BENCH_SRC/judge.py" "$rd"
}

echo "== Pipeline Skill-Bench regression gate (best-of-3 on failure) =="
ALLPASS=1
for s in "${SCENARIOS[@]}"; do
  out=$(run_and_judge "$s" reg); rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  PASS   $s — ${out#PASS }"; continue
  fi
  echo "  retry  $s (seed 1: ${out}) — running 2 more for majority"
  passes=0
  details="seed1:[$out]"
  for seed in reg2 reg3; do
    o=$(run_and_judge "$s" "$seed"); r=$?
    details="$details $seed:[$o]"
    [ "$r" -eq 0 ] && passes=$((passes + 1))
  done
  if [ "$passes" -ge 2 ]; then
    echo "  PASS   $s — $passes/3 seeds pass (first-seed miss = variance) | $details"
  else
    echo "  FAIL   $s — only $passes/3 seeds pass (SYSTEMATIC) | $details"
    ALLPASS=0
  fi
done
echo "== REGRESSION $([ "$ALLPASS" -eq 1 ] && echo 'PASS ==' || echo 'FAIL ==')"
[ "$ALLPASS" -eq 1 ]
