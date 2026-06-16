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
| `rocketride-building-pipelines` | **Orchestrator.** Owns gate discipline + the 15 forcing functions; routes the lifecycle. |
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

## Tools

- `tools/generate-index.py` — (re)build the Layer-1 node index from the live engine / catalog.
- `skills/rocketride-configuring-pipelines/tools/fetch-node-schema.py` — one node's schema (L2).
- `skills/rocketride-configuring-pipelines/tools/validate-pipeline.py` — `client.validate()`, or
  `--static` for an engine-free pre-flight lint.

## Testing

`benchmarks/` ports the Skill-Bench harness (RED/GREEN arms, per-run isolation, cross-model). See
`benchmarks/README.md`. `ARCHITECTURE.md` documents the design + the adversarial debate behind it.
