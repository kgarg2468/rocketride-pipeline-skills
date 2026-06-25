# rocketride-pipeline-skills

Agent-facing [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) that
teach an AI agent to **build, run, and validate RocketRide pipelines** — reliably, even on a
weak/cheap model. They ship into Claude Desktop, Cursor, and other skill-aware clients (via the
RocketRide MCP connector), so a non-technical user's agent can turn a plain-language request
("a chatbot that answers from my PDFs") into a valid, running pipeline.

> Private. This is the **pipeline-builder** skill set (end-user / agent facing). It is distinct
> from `rocketride-node-skills` (developer-facing, for *authoring* RocketRide nodes). It reuses
> that repo's proven structure and Skill-Bench test harness.

## Install

```bash
./install.sh           # symlinks each skill in skills/ into ~/.claude/skills and ~/.agents/skills
git pull               # updates installed skills in place (they're symlinks)
```

## The skills

| Skill | Role |
|---|---|
| `rocketride-building-pipelines` | **Orchestrator.** Owns gate discipline + the forcing functions (canonical set in `GATE_PROTOCOL.md`); routes the lifecycle. |
| `rocketride-designing-pipelines` | Phase 1 — discover nodes + wire the DAG (Gates A, B). |
| `rocketride-configuring-pipelines` | Phase 2 — configure nodes + validate (Gates C, C.5). |
| `rocketride-running-pipelines` | Phase 3 — submit, poll, report the result (Gate D). |
| `rocketride-debugging-pipelines` | Diagnose a failed run and route the fix. |

Start at `rocketride-building-pipelines` — it reads the others as required sub-skills.

## How it works (the short version)

Reliability comes from **process + tools as the judge**, not model intelligence:
- **Three-layer progressive disclosure:** L1 thin node index (select + wire) → L2 per-node schema
  (configure) → L3 `validate()` (the compiler). Each step uses the live MCP tool if present, else a
  bundled SDK shim, else an offline file — so the skills work **today**.
- **Forcing functions:** cite-every-node from the index, fetch-schema-before-config, the 9-point
  anti-pattern checklist as a gate, mandatory `validate()` + re-validation loop, a cost-approval
  gate before any paid run, and the "Waiting = STOP" gate discipline. See
  `skills/rocketride-building-pipelines/GATE_PROTOCOL.md`.
- **Deep docs on demand (token-economical):** a resident doc-map
  (`.rocketride/docs/ROCKETRIDE_DOC_MAP.md` — the `docs.rocketride.org` `llms.txt`, ~156 pages,
  ~2K tokens) + `fetch-doc.py` pull the **one** relevant page when needed (live-first, offline
  fallback to a bundled fresh snapshot). The ~257K-token `llms-full.txt` is **never** fetched. A
  deep lookup costs ≈ the map + one ~3K page instead of guessing or ingesting the whole manual.

## Tools

- `tools/generate-index.py` — (re)build the Layer-1 node index from the live engine / catalog.
- `skills/rocketride-configuring-pipelines/tools/fetch-node-schema.py` — one node's schema (L2).
- `skills/rocketride-configuring-pipelines/tools/validate-pipeline.py` — `client.validate()`, or
  `--static` for an engine-free pre-flight lint.
- `skills/rocketride-building-pipelines/tools/fetch-doc.py` — fetch ONE doc page by topic (resolves
  from the doc-map; refuses `llms-full.txt`; offline-falls-back to the bundled `pages/` / schema).

## Docs & freshness

The agent's RocketRide knowledge has tiers: bundled condensed refs + node `schema/` (fast path),
the resident **doc-map** + on-demand single-page fetch from `docs.rocketride.org` (depth, fresh),
and a bundled `.rocketride/docs/pages/` snapshot of the non-node docs (offline fallback, pulled from
the April-2026 docs). Refresh the map/pages by re-running the fetch in `tools/` against the live site.

**Limitation (pre-skill-load actions).** A skill loads *after* the agent's first action, so a user
explicitly ordering "read all the docs / fetch `llms-full.txt`" at turn start can't be blocked by
the skill alone. `fetch-doc.py` refuses the monolith and caps response size, and the production MCP
connector should carry the same guardrail in its system prompt / tool surface (no fetch-everything
tool). The skill reliably governs *in-flow* research (fetch one page / use the index, never the
monolith) — which is what the s9 regression scenario tests.

**The node catalog is engine-authoritative.** `LAYER1_NODE_INDEX.json` /
`.rocketride/services-catalog.json` are a 104-node snapshot. The live docs list ~26 nodes not in it
— genuinely new (`tool_deepl`, `anomaly_detector`, `tool_apify`, `llm_kimi`, `vectorizer`, …) plus
renames/groupings (docs use a single `response` node where the snapshot has `response_*`;
`llm_vision_*` where the snapshot has `image_vision_*`). For authoritative select/wire, **regenerate
from a live engine**: `python3 tools/generate-index.py` (uses `get_services()`), with `validate()`
as the drift backstop. The bundled examples use snapshot names (`response_answers`) for
self-consistency with the bundled catalog/validator.

## Testing

`benchmarks/` ports the Skill-Bench harness (RED/GREEN arms, per-run isolation, cross-model). See
`benchmarks/README.md`. `ARCHITECTURE.md` documents the design + the adversarial debate behind it.
