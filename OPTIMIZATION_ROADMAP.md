# RocketRide Pipeline-Skills — Optimization Roadmap

> Research output. No skill behavior changes are made by this document. It records what to
> optimize, in what order, with what guardrails, and **how each change is tested**. Produced from
> a 12-agent audit (5 internal lenses verified against the repo + 4 external-research streams +
> red-team) over an external efficiency analysis.

## Prime directive (the over-axis)
**Weak-model (Haiku-class) reliability and gate discipline come first.** Any change that saves
tokens/latency but reduces weak-model compliance is **net-negative** and is rejected. Empirical
basis: in the sibling node-skills repo, *repeating* the "Waiting = STOP" rule + rationalization
table drove gate blast-through from 32–45% → 0/24 across three models. **Redundancy here is a
forcing function, not waste.**

## What the audit confirmed about the current state
The skill set already exemplifies most documented best practices: coarse-grain orchestrator +
4 sub-skills, "Waiting = STOP" as a hard protocol, tool-as-judge (`validate()`), three-layer
progressive disclosure, count-lines, few-shot + anti-examples, multi-turn gate-state. So the
optimization space is **runtime efficiency + a few additive wins**, not structural change — and the
largest risk is "optimizing" reliability away via deduplication.

---

## Verdict on the handed analysis (tier by tier)

| Tier | Verdict | Correction / note |
|---|---|---|
| **T1 — schema reconnect + Phase1/Phase2 double-fetch** | **CONFIRMED, high-value** | Real (~10 reconnects for a 5-node build). Safe **only with T2** (else cached schemas drift). |
| **T2 — freshness `_meta` stamping** | **CONFIRMED — prerequisite, not a peer** | Must ship **before** T1. Phrase the staleness signal as *informational*, or Haiku treats "stale" as a hard stop. |
| **T3 — activation cheap-path triage** | **CONFIRMED risk; gate it** | Misclassifying a build as a "question" silently skips all gates. Ship only behind a `<2%` misclassification test + recovery path. |
| **T4 — context dedup** | **MOSTLY REJECT** | Repetition is load-bearing; counts were overstated (≈3–6× for Waiting=STOP, not 8×); savings ≈0.5% of tokens. **Only the error-table merge is safe**, and only A/B-tested. |

Factual fix from the audit: `elasticsearch.json` is **~100 KB (~25K tokens)** — the largest schema,
bigger than the analysis implied → **result-size bounding matters more, not less.**

---

## New optimizations the analysis missed (ranked by impact-to-risk)
1. **Prompt caching the stable context** — mark the L1 index + `GATE_PROTOCOL.md` + doc-map as
   `cache_control` blocks. **~90% token savings on repeat reads, zero reliability risk.** (Lands at
   the MCP-server / request-construction layer — see test caveats.)
2. **Tool-description tuning** — put constraints in the *tool descriptions* (the weak model's first
   signal), e.g. fetch-doc "never llms-full", fetch-node-schema "only use fields in the schema".
   External evidence: **+20–30% compliance, zero token cost.**
3. **Structured error taxonomy** — tools return `{code, retriable, fallback}` JSON instead of prose
   stderr, so a weak model routes to the fallback instead of retrying blindly.
4. **Forcing function #17 — schema fetch is lazy per-node, never eager** — blocks "fetch all 104
   schemas" (~80 KB) blowups during design.
5. **Checklist-as-tool** — make the 9-point anti-pattern check a programmatic tool (`--checklist`),
   pushing validation fully off the model.
6. **Interleave the failure examples** into the flow (not all-at-end) + carry a phase-handoff
   summary (`.context/DESIGN_STATE.md`) so phases don't re-derive context.
7. **Result-size bounding on schema fetch** (the elasticsearch outlier) with a truncation signal —
   never silently drop required fields.

---

## The 3 critical tensions → safe resolutions
1. **Caching ↔ freshness** → ship **T2 first**; T1 cache carries a TTL checked against the `_meta`
   stamp; deploy together or not at all.
2. **Dedup ↔ weak-model redundancy** → **reject** Red-flags and "never-llms-full" consolidation;
   the redundancy is what makes a weak model comply. Only the (reference-not-gate) error table may
   merge, A/B-tested.
3. **Triage ↔ gate discipline** → tight keyword whitelist, default-to-full-lifecycle, a recovery
   path if the user corrects a misroute, and a `<2%` misclassification gate before shipping.

---

## Sequenced roadmap
**Do-first (low-risk, high-value, testable here):**
1. Tool-description tuning · 2. Structured error taxonomy · 3. FF#17 lazy-fetch guard ·
4. T2 freshness `_meta` stamping (+ non-blocking staleness note).

**Then (depends on the above):**
5. T1 write-through schema cache with TTL (gated on T2) · 6. Result-size bounding · 7. Phase-handoff
summary + interleaved negatives.

**At the MCP-server layer (validated there, not in the skill bench):**
8. Prompt caching the stable context.

**Conditional:** 9. T3 triage — only if the misclassification test passes (`<2%`).
**Polish (A/B-tested):** 10. Error-table merge · checklist-as-tool.

**NEVER (rejected):** Red-flags dedup · "never-llms-full" dedup · T1 caching without T2 ·
removing multi-turn gate-state · aggressive schema truncation that can drop required fields ·
optimizing tokens at the expense of compliance.

---

## How each change is tested (summary; full detail in `benchmarks/OPTIMIZATION_TESTS.md`)
Method: **ablate-then-measure** — baseline → change one thing → re-run the same scenarios GREEN on
Haiku → keep only if reliability holds *and* efficiency improves. RED/GREEN arms prove the skill
(not the model) is doing the work. Each run records pass/fail predicates + `cost_usd`/`duration_s`/
`num_turns`/`tool_call_count` (`analyze.py`).

| Change | Testable here? | How |
|---|---|---|
| Tool-description tuning | ✅ | RED/GREEN ablation on Haiku; compliance delta |
| Structured errors | ✅ | tool-unit (force failure) + a fallback scenario |
| FF#17 lazy fetch | ✅ | `s10-eager-fetch` scenario; `eager_fetch` signal |
| T2 freshness note | ✅ | backdate `_meta`; confirm non-blocking + proceeds (`s12`, pending) |
| Error-table / any dedup | ✅ | **A/B** consolidated vs distributed on `s6` |
| T3 triage | ✅ | `s11-info-query` + paired build look-alikes ×10; `<2%` gate |
| T1 cache *correctness* | ✅ | tool-unit + stale-cache scenario (`s13`, pending) |
| T1 reconnect *latency* | ❌ | **needs a live engine** (bench runs offline) |
| Prompt-cache savings | ❌ | **MCP-server / request layer**, not the skill bench |

Regression gate after **every** change: `regression.sh` (s1,s5,s6,s8,s9) GREEN on Haiku; rollback
on any drop.

## Status
Roadmap only. Test scaffolding added under `benchmarks/` (see `OPTIMIZATION_TESTS.md`). No skill
behavior changed yet. Do-first batch implementation pending approval.
