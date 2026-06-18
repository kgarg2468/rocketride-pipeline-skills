# Prompt Caching — Host Integration Guide

**Prompt caching is controlled by the host app, not by this repo.** `cache_control` is a
request-level parameter the host (Claude Code / Claude Desktop / Cursor / your API caller) sets when
it assembles the `system` / `tools` / `messages` for the model. Skill files are passive Markdown and
an MCP server has no cache field in its wire format — neither can set or force caching. This repo's
job is to make caching **easy and safe** for the host, and to **measure** it.

## What this repo guarantees (cache-friendliness)
- **Byte-deterministic resident context.** The node index is generated with `sort_keys=True`
  (`tools/generate-index.py`), so re-runs produce identical bytes — a host's cached prefix isn't
  silently invalidated, and version-control diffs stay clean.
- **No timestamps inside the resident index.** The freshness stamp lives in a *separate* sibling
  (`LAYER1_NODE_INDEX.meta.json`), so it never changes the index bytes that get cached.
- **Static skill text.** SKILL.md, GATE_PROTOCOL.md, the doc-map, and reference files don't change
  mid-session, so the host can cache them across turns.

## What the host should do
The agent re-sends a stable block of background context every turn — the node index (~3.7K tokens),
`GATE_PROTOCOL.md`, the doc-map, and the SKILL text. To cache it:
1. Assemble that stable content **once**, early in the system prompt (before the volatile
   conversation), so it forms a stable prefix.
2. Put a cache breakpoint on the **last stable system block**: `cache_control: {type: "ephemeral"}`.
   (Render order is `tools` → `system` → `messages`; the breakpoint caches everything before it.)
3. Keep the skill version stable within a session (editing a SKILL.md changes the bytes → the cached
   prefix is rewritten on the next turn; that's expected and automatic).
4. Read back `response.usage.cache_read_input_tokens` to confirm hits.

**Claude Code already does this.** In the Skill-Bench (which drives `claude -p`), a multi-turn run
shows e.g. `cache_read_input_tokens ≈ 226K` vs `input_tokens ≈ 70` on later turns — ~90% of input
served from cache. Hosts that *don't* auto-cache (some custom `.mcpb` / Cursor / direct-API
integrations) get the win only if they add the breakpoint as above.

## How to measure it
`benchmarks/analyze.py` records `cache_read`, `cache_creation`, and `cache_hit_ratio` per run (from
`result.json`'s `usage` block). A healthy multi-turn run shows a high `cache_hit_ratio` (input mostly
served from cache). If it's near zero, the host isn't caching the skill context — apply the breakpoint.

## Why we can't just "turn it on" here
- MCP tools/resources/prompts carry no caching metadata in the protocol.
- Skill Markdown can't set request parameters.
- So the only in-repo levers are (1) keep the context byte-stable (done), (2) keep timestamps out of
  the resident block (done), (3) measure (done), (4) document the host knob (this file).
