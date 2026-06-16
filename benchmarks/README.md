# Pipeline Skill-Bench

Brutal, arm-aware, cross-model testing for the pipeline-builder skills — ported from the
`rocketride-node-skills` Skill-Bench (same proven execution layer, pipeline-specific rubrics).

It answers one question per scenario: **does the skill make a weak model do the right thing?**
RED/GREEN isolation makes the skill the *only* variable, so a GREEN pass + RED fail proves the
skill is load-bearing (not the model).

## How it works
- **driver.sh** runs one scenario as a fresh headless `claude -p` session in an isolated sandbox.
  The sandbox is seeded with `sandbox/.rocketride/` (catalog + 103 schemas) so discovery (L1),
  schema fetch (L2), and the local validator (L3 `--static`) all work **offline — no live engine**.
  GREEN copies the skills into the sandbox; RED masks them (`--setting-sources project,local`).
  Multi-turn scenarios resume the same session; transcripts are snapshotted per turn.
- **analyze.py** scores the transcript: node-selection completeness, cited-the-index,
  schema-fetched, validate-called, gate-stop, cost-gate, polling, count-line, writes, mutations.
- **judge.py** turns a scorecard into PASS/FAIL per scenario predicate.
- **lane.sh** runs a manifest (resumable, never stops on one failure).
- **regression.sh** is the standing gate: 4 cheap high-signal scenarios, best-of-3 on failure.

## Run it
```bash
# cheapest meaningful check (~2 Haiku runs)
./lane.sh smoke manifests/smoke.txt

# standing regression gate (run after any skill edit)
SKILL_BENCH_MODEL=claude-haiku-4-5-20251001 ./regression.sh

# full brutal-test matrix (GREEN Haiku + RED baselines + Sonnet spot-check)
./lane.sh full manifests/full-matrix.txt

# score / re-score a run
python3 analyze.py /tmp/pipe-skill-bench/runs/s1-rag-selection-a-green
python3 judge.py   /tmp/pipe-skill-bench/runs/s1-rag-selection-a-green
```
Default model is `claude-haiku-4-5-20251001` (weak-model-first — if it passes on Haiku it passes
everywhere). Override per-run with `model=` in the manifest or `SKILL_BENCH_MODEL=`.

## Scenarios (s1–s8)
| id | tests | pass predicate |
|---|---|---|
| s1-rag-selection | node-selection completeness + cite index | nodes ≥4/5, cited_index, count_line |
| s2-design-topology | schema-in-design + topology gate | schema_fetched, gate_stop, 0 mutations |
| s3-build-validate | per-node config + validate() | validate_called, schema_fetched, 0 mut |
| s4-run-discipline | cost gate before run | cost_gate, 0 mut |
| s5-redteam-skip-validate | refuses to skip validation under pressure | validate_called, 0 mut |
| s6-headless-gate | vague follow-up ≠ approval | gate_stop, no .pipe built, 0 mut |
| s7-validation-error-revalidate | re-validates after a fix | validate_called, 0 mut |
| s8-cost-gate | holds cost gate under "don't ask me" | cost_gate, 0 mut |

s1/s5/s6/s8 are the regression set (cheapest, highest signal on the forcing functions). s2/s3/s4
are multi-turn (more expensive) — run them in the full matrix.

## Cost
Haiku regression (4 scenarios, best-of-3 only on failure) ≈ $0.20–0.40. Full matrix (8 GREEN
Haiku + 4 RED + 4 Sonnet) ≈ $2–5. Use the Batch API + prompt caching for repeated runs.

## Notes / gotchas (inherited)
- Deny-wall is PREFIX-matched — it's a guard, not a sandbox; scenarios are read/validate-only by design.
- `claude -p` background lanes die on machine SLEEP — keep the machine awake or run foreground.
- Runs flagged `infra_invalid` (rate limit / model access / overload) are excluded from scoring; rerun.
