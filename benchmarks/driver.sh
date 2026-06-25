#!/usr/bin/env bash
# Pipeline Skill-Bench driver: arm-aware, multi-turn, isolated sandbox, transcript snapshot.
# Usage: driver.sh <scenario.json> <seed-label> [--null-baseline]
#
# Unlike the node-skills driver (which needs a rocketride-server worktree), pipeline building
# only needs the node catalog. Each run gets a fresh sandbox seeded with a .rocketride/ dir
# (catalog + schemas) so discovery (Layer 1), schema fetch (Layer 2), and the local validator
# (Layer 3 --static) all work OFFLINE — no live engine required. Behaviour (cite/fetch/validate/
# gate) is observable from the transcript regardless of engine.
#
# GREEN copies the pipeline skills into the sandbox as project skills; RED doesn't. Both arms run
# --setting-sources project,local so ~/.claude is masked — the only delta is the skills.
set -euo pipefail

SCENARIO_FILE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
SEED="${2:-a}"
MODE=green
case "${3:-}" in --null-baseline|red) MODE=red;; esac

BENCH=/tmp/pipe-skill-bench
BENCH_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$(dirname "$BENCH_SRC")/skills"
FIXTURES="$BENCH_SRC/sandbox/.rocketride"
MODEL="${SKILL_BENCH_MODEL:-claude-haiku-4-5-20251001}"   # weak-model-first
TURN_BUDGET="${SKILL_BENCH_TURN_BUDGET:-6}"

ID=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['id'])" "$SCENARIO_FILE")
NTURNS=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(len(d.get('turns') or [d['prompt']]))" "$SCENARIO_FILE")
# reset_turns: turn indices that start a FRESH claude session (no --resume) in the SAME sandbox —
# simulates a context reset / compaction, where only on-disk state (GATE_STATE.md) carries over.
RESET_TURNS=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(' '.join(str(x) for x in (d.get('reset_turns') or [])))" "$SCENARIO_FILE")

[ -d "$FIXTURES" ] || { echo "FATAL: catalog fixtures missing at $FIXTURES (run from a checkout)" >&2; exit 1; }

RUN="$BENCH/runs/$ID-$SEED-$MODE"
rm -rf "$RUN"
mkdir -p "$RUN/.claude" "$RUN/.bench"
cp "$BENCH_SRC/sandbox/settings.json" "$RUN/.claude/settings.json"
cp "$BENCH_SRC/sandbox/log_tool.py" "$RUN/.bench/log_tool.py"
cp "$SCENARIO_FILE" "$RUN/.bench/scenario.json"
cp -R "$FIXTURES" "$RUN/.rocketride"     # offline catalog + schemas for discovery/validation
echo "$MODE" > "$RUN/.bench/arm"
echo "$MODEL" > "$RUN/.bench/model"

if [ "$MODE" = green ]; then
  mkdir -p "$RUN/.claude/skills"
  for d in "$SKILLS_SRC"/rocketride-*/; do
    cp -R "$d" "$RUN/.claude/skills/$(basename "$d")"
  done
fi

echo "[pipe-bench] $ID seed=$SEED arm=$MODE turns=$NTURNS model=$MODEL"
cd "$RUN"

snapshot_transcript() {  # $1 = session_id, $2 = turn index
  [ -z "$1" ] && return 0
  local src
  src=$(ls -t "$HOME/.claude/projects"/*/"$1.jsonl" 2>/dev/null | head -1)
  [ -n "$src" ] && cp "$src" "$RUN/.bench/transcript-$2.jsonl" 2>/dev/null || true
}

SESSION_ID=""
FINAL_RC=0
for i in $(seq 1 "$NTURNS"); do
  MSG=$(python3 -c "
import json, sys
d = json.load(open('.bench/scenario.json'))
print((d.get('turns') or [d['prompt']])[int(sys.argv[1]) - 1])" "$i")
  EXPECT=$(python3 -c "
import json, sys
d = json.load(open('.bench/scenario.json'))
e = d.get('expect') or []
i = int(sys.argv[1]) - 1
print(e[i] if i < len(e) else '')" "$i")
  RESUME_OPT=""
  if [ -n "$SESSION_ID" ]; then
    case " $RESET_TURNS " in
      *" $i "*) echo "[pipe-bench] turn $i: FRESH session — no --resume (gate-state / compaction test)";;
      *) RESUME_OPT="--resume $SESSION_ID";;
    esac
  fi
  echo "[pipe-bench] turn $i/$NTURNS: ${MSG:0:70}"
  set +e
  # shellcheck disable=SC2086
  claude -p "$MSG" $RESUME_OPT \
    --output-format json \
    --permission-mode acceptEdits \
    --max-turns 250 \
    --max-budget-usd "$TURN_BUDGET" \
    --setting-sources project,local \
    --strict-mcp-config \
    --model "$MODEL" \
    --add-dir "$RUN" \
    > ".bench/result-$i.json" 2> ".bench/stderr-$i.log"
  RC=$?
  set -e
  [ -s ".bench/result-$i.json" ] && cp ".bench/result-$i.json" .bench/result.json
  if [ "$RC" -ne 0 ] || [ ! -s ".bench/result-$i.json" ]; then
    echo "[pipe-bench] turn $i FAILED rc=$RC"; tail -3 ".bench/stderr-$i.log" 2>/dev/null || true
    FINAL_RC=$RC; [ "$FINAL_RC" -eq 0 ] && FINAL_RC=1; break
  fi
  read -r SESSION_ID SUBTYPE COST <<< "$(python3 -c "
import json
r = json.load(open('.bench/result-$i.json'))
print(r.get('session_id') or '-', r.get('subtype') or '-', r.get('total_cost_usd') or 0)")"
  snapshot_transcript "$SESSION_ID" "$i"
  printf '%s\t%s\t%s\t%s\n' "$i" "$SUBTYPE" "$SESSION_ID" "$COST" >> .bench/turns.tsv
  if [ "$SUBTYPE" != "success" ] || [ "$SESSION_ID" = "-" ]; then
    echo "[pipe-bench] turn $i subtype=$SUBTYPE — stopping"; FINAL_RC=3; break
  fi
  if [ -n "$EXPECT" ]; then
    if ! python3 -c "
import json, re, sys
r = json.load(open('.bench/result-$i.json'))
sys.exit(0 if re.search(sys.argv[1], r.get('result') or '', re.I) else 1)" "$EXPECT"; then
      echo "[pipe-bench] turn $i: expected marker /$EXPECT/ missing — early stop"; FINAL_RC=2; break
    fi
  fi
done

echo "[pipe-bench] done rc=$FINAL_RC run=$RUN"
exit $FINAL_RC
