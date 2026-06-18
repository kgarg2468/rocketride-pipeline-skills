# Pipeline Anti-Patterns & Checklist

The real, observed mistakes when building RocketRide pipelines (condensed from the RocketRide
"Common Mistakes" reference). Treat the checklist at the bottom as a **gate**, not a reading.

## The 9-point Pipeline Checklist (run per node / per pipeline, state yes/no)
1. **`.pipe` extension** — the pipeline file ends in `.pipe`, not `.json`. (RocketRide only loads
   `.pipe`.)
2. **`components` first; meta last** *(editor convention)* — keep `components` as the first key;
   `project_id`, `viewport`, `version` at the bottom. The schema marks key order optional, but the
   visual editor is happiest this way. (`--static` flags this as a warning, not an error.)
3. **`project_id`, if present, is a literal GUID** *(optional, editor convention)* — never a
   variable (`"${ROCKETRIDE_PROJECT_ID}"` is read before env substitution). The current schema marks
   `project_id` optional; include a literal GUID when authoring for the editor.
4. **`source` matches a real component id** (if you include the optional `source` field).
5. **All component ids unique.**
6. **Every non-source node has an `input` array** — `[{lane, from}]`. Sources have none.
7. **Lane types match across every edge** — output lane type of `from` = input lane type here, or
   a converter sits between them.
8. **Acyclic, no orphans** — no loops; every node reachable from the source.
9. **Secrets via `${ENV_VAR}` substitution** — never literal API keys. The engine expands any
   `${VAR}` from the environment at startup (e.g. `${OPENAI_API_KEY}`); a `ROCKETRIDE_` prefix is
   **not** required (older docs claimed it was — that's outdated).

## Configuration anti-patterns
- **Empty source config.** Source nodes need the full block, not `{}`:
  `{ "hideForm": true, "mode": "Source", "parameters": {}, "type": "<provider>" }` (use the
  provider name as `type`: `"webhook"`, `"chat"`, `"dropper"`, …). `memory_internal` needs
  `{ "type": "memory_internal" }`.
- **Missing required LLM config.** LLM nodes need a profile + apikey:
  `{ "profile": "openai-5", "openai-5": { "apikey": "${ROCKETRIDE_OPENAI_KEY}" }, "parameters": {} }`.
  Read the schema's `Pipe.schema.dependencies.profile.oneOf` for the available profiles.
- **Guessing field names.** Fetch the schema; e.g. LLM token limit is `modelTotalTokens`, not
  `max_tokens`. Profile keys are provider-specific.
- **Ignoring conditional constraints.** Schema prose like "if `batch_size` set, `max_batch_wait_ms`
  required" is binding — required fields are not the whole story.

## Wiring anti-patterns
- **Mismatched lane types.** Insert a converter (`tags → parse → text`, `text → preprocessor →
  documents`, `documents → embedding → documents`, `questions → llm → answers`).
- **Store without embedding.** Vector stores need embedded input; embed first, same model for
  ingest + query.
- **Agent control plane backwards.** The `control` array lives on the controlled node
  (`{classType, from: <agent>}`), not on the agent. (See PIPELINE_RULES_SUMMARY.)
- **Wrong source for use case.** `chat` source → conversational (`client.chat()`); `webhook`/
  `dropper` → data/files (`client.send()` / `client.send_files()`). Don't add a `question` node
  after a `chat` source — `chat` already emits `questions`.
- **One response node per agent.** In multi-agent pipelines use a single `response_answers` with
  one `input` entry per agent, not one response node each.

## Response-key anti-pattern
- **Customizing `laneName`** changes the response JSON key and breaks client code. Defaults:
  `answers`→`answers`, `text`→`text`, `documents`→`documents`, `questions`→`questions`. When in
  doubt, don't customize — use the lane-specific node (`response_answers`, `response_text`, …).

## Common build-time errors (TL;DR — full catalog elsewhere)
The complete error catalog (build-time **and** runtime, with owning phase) is the **single source of
truth** in `../rocketride-debugging-pipelines/ERROR_TABLE.md`. The three you'll most likely hit while
configuring:
| Error | Likely cause | Fix |
|---|---|---|
| `Component not found` | bad/misspelled `provider` | check the node index (cite it) |
| `Lane not supported` | wrong lane type on an edge | match lanes / add a converter |
| `project_id must be a GUID` | variable in `project_id` | use a literal GUID |

> Note: the "Common Mistakes" doc also numbers SDK/runtime mistakes (event-loop blocking,
> `use_existing`, resource cleanup, `ROCKETRIDE_` prefix). Those belong to running the pipeline —
> see `rocketride-running-pipelines`. The items above are the build-time ones.
