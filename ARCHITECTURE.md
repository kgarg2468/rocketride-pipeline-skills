# Architecture

## Goal
Make an AI agent reliably good at building RocketRide pipelines — so good that even a weak/cheap
model (Haiku-class) performs like a strong one. Reliability must come from the **skill + tool
design**, not from model intelligence.

## Decisions (settled by an adversarial agent-team debate: 4 forks → synthesis → red-team → finalize)

1. **One orchestrator + 4 lifecycle sub-skills** (not 1 monolith, not 8 fine-grained). Coarse
   enough that a weak model doesn't get lost routing; each skill <~150 lines (re-readable fast).
   Mirrors the proven `rocketride-node-skills` structure.
2. **Verification by tools (autonomous) + approval gates only at costly/irreversible boundaries**
   (cost before a run; publish before marketplace). Not a gate at every step (gate fatigue), not
   no gates (wallet burn). All gates inherit the "Waiting = STOP" discipline that drove node-skills
   gate blast-through from 32–45% → 0/24 across three models.
3. **Reliability from rich-prose discipline + graceful tool degradation.** Every L-step has a
   ladder: MCP tool → bundled SDK shim → offline file/lint. The skills work today and absorb the
   MCP tools when they land, with no rewrite.
4. **Reuse the Skill-Bench harness, replace the rubrics.** The execution layer (lane.sh, driver.sh,
   analyze.py, regression.sh) is domain-agnostic; only scenarios + scoring dimensions change.

The red-team pass initially failed the design and produced 12 must-fixes; all are folded in — most
notably the **cost-approval gate (C.5)**, **multi-turn gate-state persistence**, the **mandatory
re-validation loop**, **schema-fetch in the design phase** (catch lane mismatches before wiring),
and **negative/failure examples**.

## The three-layer + run model (maps to what the SDK actually exposes)

| Layer | Purpose | SDK ground truth (`mixins/services.py` etc.) |
|---|---|---|
| L1 index | select + wire | `get_services()` → DAP `rrext_services`; cached as `.rocketride/services-catalog.json` |
| L2 schema | configure | `get_service(name)` → one `SERVICE_DEFINITION` (incl. `Pipe.schema`) |
| L3 validate | the compiler | `validate(pipeline)` → `{errors, warnings}` (native `validatePipeline`, real structural check) |
| run | execute | `use()` → `send`/`chat`/`send_files` (inline result) → `get_task_status` poll |

> These SDK methods exist today; they were just missing from the stale agent-facing API doc. The
> `rrext_get_nodes` MCP resource is dead (no server handler) — discovery is `rrext_services`. The
> obvious Tier-1 MCP work is to expose `rrext_services` + `rrext_validate` (+ async run) as tools.

## The forcing functions
Canonical numbered list in `skills/rocketride-building-pipelines/GATE_PROTOCOL.md` (the single
source of truth for both the set and its count). Grouped: gate discipline (Waiting=STOP,
deterministic wording, multi-turn persistence); anti-hallucination (cite-from-index,
schema-before-config, count-lines, exhaustive archetypes); verification-by-tool (schema-in-design,
checklist-as-gate, conditional constraints, validate+re-validate loop, real polling); cost & safety
(cost gate, no literal secrets); weak-model priors (examples + anti-examples); knowledge discipline
(one-map-one-page docs, lazy per-node schema fetch).

## Why a weak model still wins
Tools are the judge (the engine validates, not the model); checklists-as-grammar (Haiku is ~95%
reliable on yes/no checklists, ~30% on "does this look valid?"); count-lines make omissions a
visible lie; bounded per-phase context; few-shot + negative examples; one hard STOP rule that is
model-independent.

## Status
Skills + reference + examples + shims complete and self-validated (the local validator passes all
3 worked examples and catches planted errors). Skill-Bench port + cross-model brutal-test pass in
`benchmarks/`. Packaging for Claude `.mcpb` / Cursor and ChatGPT/goose translations are deferred.
