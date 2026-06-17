# Optimization Test Method

How we test the changes in `../OPTIMIZATION_ROADMAP.md` **before** shipping them. The rule:
**weak-model reliability must hold; efficiency should improve.** A latency/token win that regresses
compliance is rejected.

## The loop: ablate-then-measure
1. **Baseline** the relevant scenarios on Haiku: `./baseline.sh before <scenarios...>`
2. **Make one change** to the skills/tools.
3. **Re-measure**: `./baseline.sh after <scenarios...>`
4. **Diff**: `python3 compare.py baselines/before baselines/after`
   - Exit 0 = no reliability regression → keep the change.
   - Exit 1 = a GOOD_TRUE signal flipped False, a GOOD_FALSE flipped True, nodes dropped, or
     mutations appeared → **roll back**.
5. **Gate**: `SKILL_BENCH_MODEL=claude-haiku-4-5-20251001 ./regression.sh` must stay GREEN
   (s1,s5,s6,s8,s9). Run after every change.

RED/GREEN arms (the `red` flag in a manifest) prove the skill — not the model — is doing the work:
if RED passes too, the skill isn't load-bearing for that behavior.

## What each run records (`analyze.py` scorecard)
- **Reliability:** `cited_index`, `schema_fetched`, `validate_called`, `gate_stop`, `cost_gate`,
  `count_line`, `llms_full_fetched`, `eager_fetch` (new), `info_cheap_path` (new), `nodes_score`,
  `mutation_attempts`, `pipe_written`.
- **Efficiency:** `cost_usd`, `num_turns`, `tool_call_count`. (`compare.py` diffs these.)

## Per-change test mapping
| Roadmap change | Test here | Scenario / mechanism |
|---|---|---|
| Tool-description tuning | ✅ | RED/GREEN ablation; `compare.py` on s1/s5/s9 (compliance must not drop) |
| Structured error taxonomy | ✅ | tool-unit (invoke tool with engine down) + a fallback-routing scenario |
| FF#17 lazy schema fetch | ✅ | **s10-eager-fetch** (`eager_fetch` must stay False) |
| T2 freshness note | ✅ (after impl) | **s12** (pending): backdate `_meta`, confirm a NON-blocking note + the build proceeds |
| Error-table / any dedup | ✅ | **A/B**: `baseline.sh before …` (distributed) vs `after …` (consolidated) on s6; `compare.py` |
| T3 triage | ✅ | **s11-info-query** + look-alike BUILD requests ×10; require `<2%` misroute, `info_cheap_path` True for info |
| T1 cache correctness | ✅ (after impl) | tool-unit + **s13** (pending): stale-cache scenario |
| T1 reconnect latency | ❌ | needs a **live engine** (bench runs offline; no handshake to save) |
| Prompt-cache savings | ❌ | **MCP-server / request-construction** layer, not the skill bench |

## New scenarios added now
- **s10-eager-fetch** — tempts bulk schema loading; pass = not `eager_fetch`, nodes ≥4, 0 mutations.
- **s11-info-query** — pure question; pass today = no build/mutation; tracked metric `info_cheap_path`
  becomes the Tier-3 triage gate (and pair with build look-alikes for the `<2%` misclassification test).

## Pending scenarios (add with their feature)
- **s12-freshness-warning** — needs `_meta` on the index (T2) + a backdate step in the driver.
- **s13-cache-freshness** — needs the write-through cache (T1): design at T0, "engine changes a
  field", configure later; cached path must catch the drift (TTL) or re-fetch, never silently wire stale.

## Honest limits
The bench runs **offline** (bundled catalog/schema, no live engine), so it measures *reliability,
tool-unit correctness, and token/turn counts* — not real reconnect latency or prompt-cache savings.
Those two land at the live-engine / MCP-server layer and are validated there.
