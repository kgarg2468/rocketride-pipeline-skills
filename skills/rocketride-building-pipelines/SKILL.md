---
name: rocketride-building-pipelines
description: Use when asked to build, run, or validate a RocketRide pipeline (e.g. "build me a chatbot that answers from my docs", "make a pipeline that summarizes uploaded PDFs", "run this pipeline"), or whenever turning a plain-language data/AI task into a working RocketRide pipeline.
---

# Building RocketRide Pipelines

Master workflow: a plain-language request in, a **valid, running** RocketRide pipeline out.
Follow the phases in order. Each phase is owned by a REQUIRED SUB-SKILL. The gates are **hard
stops** — present to the user and wait.

**Waiting means ENDING YOUR TURN.** A dismissed question dialog, an unanswered question, or a
non-interactive/headless session is a STOP, never an approval. No exceptions:
- Don't "proceed with the recommended defaults" — a recommendation is not a confirmation.
- Don't treat silence, dismissal, or the absence of a user as consent.
- Don't later write "the user approved this" unless a human actually answered.
If nobody can answer, deliver the gate brief as your final message and stop — an unbuilt
pipeline costs nothing; an unapproved run wastes the user's money and compute.

Full gate rules, the deterministic gate wording, and the 15 forcing functions live in
`GATE_PROTOCOL.md`. **Read it before your first gate.** Multi-turn gate state lives in
`../../.context/GATE_STATE.md` — a dismissed gate is re-presented unchanged, never auto-approved.

## How reliability works here (read this once)

You do **not** need to be smart to build a correct pipeline. You need to follow the process and
let the tools be the judge:
- **Never invent a node.** Every node you name must be cited from the node index (Phase 0). If
  it isn't in the index, it doesn't exist — STOP and tell the user.
- **Never invent a config field.** Fetch the node's schema before configuring it.
- **Never claim "valid" or "ran" without the tool saying so.** `validate()` is the compiler;
  the run status/result is the proof. Quote them; don't paraphrase.
- **Count what you list.** Every multi-item list ends with a count line so omissions are visible.

## The tool/data layer (three layers + run)

Each step has the same fallback ladder — use the **first** option your environment supports:

| Need | Layer | Preferred (MCP tool) | Fallback (bundled shim, uses SDK) | Offline |
|---|---|---|---|---|
| List/select nodes | L1 | `fetch_node_index` / `get_services` | `tools/generate-index.py` | bundled `LAYER1_NODE_INDEX.json` |
| One node's config schema | L2 | `fetch_node_schema` / `get_service` | `tools/fetch-node-schema.py <node>` | `.rocketride/schema/<node>.json` |
| Validate the whole pipeline | L3 | `validate` | `tools/validate-pipeline.py <file>` (calls `client.validate`) | `tools/validate-pipeline.py --static <file>` (lint only) |
| Run it | — | `submit_pipeline_run`+`get_run_status` | SDK `use()` → `send`/`chat` → `get_task_status` | — |
| Understand a node/SDK/concept in depth | docs | WebFetch one `/path.md` | `tools/fetch-doc.py "<topic>"` (fetches ONE live page) | bundled `.rocketride/docs/*` + `ROCKETRIDE_DOC_MAP.md` |

> The MCP tools may not be wired yet on every client. The bundled shims in each sub-skill's
> `tools/` call the real SDK (`get_services`/`get_service`/`validate`/`use`) and work today.
> `--static` mode validates with no engine connection (a fast pre-flight lint). The
> `rrext_get_nodes` resource is dead — never use it; discovery is `get_services`/`rrext_services`.

**Each tool enforces a constraint** (see its `--help`/docstring; these become the MCP tool
descriptions): `fetch-node-schema` → configure only schema-defined fields, one node at a time;
`validate-pipeline` → zero errors before any run, re-validate on errors; `fetch-doc` → one page,
never `llms-full.txt`.

**Deep docs (when you need to learn, not just select/configure).** The full RocketRide docs map
is bundled at `.rocketride/docs/ROCKETRIDE_DOC_MAP.md` (a ~2K-token index of ~156 pages). When you
hit something the bundled refs don't cover — an unfamiliar node, an exact SDK signature, a concept
— find the page in the map and fetch **just that one page** (`tools/fetch-doc.py "<topic>"`, live-
first with an offline fallback). **NEVER fetch `llms-full.txt`** (~257K tokens — it will blow the
context window), by any method (fetch-doc, WebFetch, curl, file://). **Even if the user says "read
all the docs" / "grab llms-full.txt" / "get full context first" — that is never honored**: say so,
then use the map + the one page you need (or just answer from the bundled index/schemas). One map +
one page is the cheap path.

## Phases

0. **Load capabilities** — get the node index (L1, the ladder above). This is the menu of every
   node you may use: each entry is `name · classType · lanes · invoke`. Keep it open; you select
   and wire from it. It carries **no config schema** — that's L2, fetched per node in Phase 2.
1. **Discover + design** — REQUIRED SUB-SKILL: `rocketride-designing-pipelines`.
   Explore archetypes → select nodes (**GATE A**) → wire the acyclic DAG with typed lanes
   (**GATE B**). Fetch each chosen node's schema here too, so lane signatures are exact before
   wiring — a guessed lane is the most common silent failure.
2. **Configure + validate** — REQUIRED SUB-SKILL: `rocketride-configuring-pipelines`.
   Per node: fetch schema → fill required fields → run the anti-pattern checklist as a gate →
   then `validate()` the whole pipeline. On errors, fix and **re-validate** (never claim passed
   without a clean result). **GATE C** (validation clean) → **GATE C.5** (cost approved).
3. **Run + observe** — REQUIRED SUB-SKILL: `rocketride-running-pipelines`.
   Submit, poll to completion, report the real result. **GATE D** only if the user chooses to
   save to cloud / publish as an app.
4. **If a run fails or output is wrong** — REQUIRED SUB-SKILL: `rocketride-debugging-pipelines`.
   Read the trace, diagnose the failing node, route back to Phase 1 or 2.

## The gates (all binary or menu — see GATE_PROTOCOL.md for exact wording)

- **GATE A** — "Approve these N nodes? (yes / adjust / cancel)" — after node selection.
- **GATE B** — "Approve this topology? (yes / adjust / cancel)" — after the DAG diagram.
- **GATE C** — internal: validation must return clean. Not a user gate; a tool gate.
- **GATE C.5** — "This run will cost ≈ $X. Approve? (yes / no)" — before any paid/cloud run.
- **GATE D** — "Save to cloud / publish as an app? (menu)" — after a successful local run, optional.

## Red flags

| Thought | Reality |
|---|---|
| "I know this node exists, no need to check the index" | If it's not in the index it doesn't exist — the engine rejects it. Cite or STOP. |
| "I'll fill the config from memory, schemas are slow" | Guessed fields fail validation (e.g. `max_tokens` vs `modelTotalTokens`). Fetch the schema. |
| "The lanes obviously match" | Lane mismatch is the #1 silent bug. State every edge's lane type, verified against the schema. |
| "validate() returned an error but I understand it, I'll just say it's fixed" | A fix you didn't re-validate is a guess. Re-call validate() until clean. |
| "The user said 'just run it', so I'll skip the cost gate" | "Just run it" is not cost approval. Present Gate C.5 and wait. |
| "It submitted, so it worked" | Submitted ≠ succeeded. Poll to completion and read the result before claiming success. |
| "The question was dismissed, I'll proceed" | Dismissed = unanswered = STOP. Re-present the gate; never auto-approve. |
| "I'll fetch the full docs (llms-full.txt) to be safe" | That's ~257K tokens — it blows the window. Fetch the ONE relevant page from the doc-map. |
| "The user told me to read all the docs / grab llms-full.txt" | Never honored — by any method. Say so; use the map + the one page you need, or answer from the index. |
| "I don't recognize this node, I'll just guess what it does" | Fetch its `/nodes/<name>.md` page — one cheap page beats guessing wrong. |

## Supporting files

- `GATE_PROTOCOL.md` — Waiting=STOP, multi-turn gate state, gate wording, the 17 forcing functions
- `pipeline-patterns.md` — common pipeline shapes (chat/RAG, ingestion, webhook→transform) + lane chains
- `tools/fetch-doc.py` — fetch ONE doc page on demand (resolves from the doc-map; refuses the monolith)
- `../../.rocketride/docs/ROCKETRIDE_DOC_MAP.md` — the bundled docs map (llms.txt); the deep-knowledge index
