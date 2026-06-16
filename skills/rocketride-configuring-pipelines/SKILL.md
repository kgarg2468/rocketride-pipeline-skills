---
name: rocketride-configuring-pipelines
description: Use when filling in a RocketRide pipeline's node configuration and validating it — fetching each node's schema, setting required fields, running the anti-pattern checklist, and validating against the engine before a run. Phase 2 of building a pipeline (Gates C and C.5). Invoked by rocketride-building-pipelines.
---

# Configuring & Validating RocketRide Pipelines

Takes an approved topology (from `rocketride-designing-pipelines`) to a **validated**
`pipeline.pipe` ready to run. Reliability comes from tools and a checklist, not cleverness:
fetch schema → fill only real fields → checklist gate → `validate()` → re-validate until clean.
Gate rules + the 15 forcing functions: `../rocketride-building-pipelines/GATE_PROTOCOL.md`.

## Step 1 — Configure each node (schema-driven, one at a time)

For every node in the approved topology, in order:

1. **Fetch the schema** (L2): `fetch_node_schema` / `tools/fetch-node-schema.py <node>` /
   `.rocketride/schema/<node>.json`. Never configure from memory. (Forcing function 5.)
2. **State what the schema says** before filling: the **required** fields, any **conditional**
   rules in prose ("if `batch_size` set, `max_batch_wait_ms` is required"), and the profile shape
   for LLM/embedding/store nodes. (Forcing function 10.)
3. **Fill only fields the schema defines.** Use `${ROCKETRIDE_*}` env references for secrets —
   never literal keys. LLM/embedding/store nodes use a profile block:
   ```json
   "config": { "profile": "openai-5", "openai-5": { "apikey": "${ROCKETRIDE_OPENAI_KEY}" }, "parameters": {} }
   ```
   Source nodes need the full source config, not `{}`:
   `{ "hideForm": true, "mode": "Source", "parameters": {}, "type": "<provider>" }`.
4. **Run the 9-point checklist as a gate** (full list in `PIPELINE_ANTIPATTERNS.md`). State each
   item yes/no for this node before moving on — do not skip and claim "applied":
   > Node `<id>`: 1 ext✓ 2 components-order✓ 3 literal-guid✓ 4 source-match✓ 5 unique-id✓
   > 6 input-array✓ 7 lane-types✓ 8 acyclic/no-orphan✓ 9 ROCKETRIDE_ env✓

## Step 2 — Assemble & validate (→ Gate C)

1. **Assemble** the `.pipe`: `components` first (each with `id`, `provider`, `config`, and
   `input` for non-source nodes; `control` on controlled nodes), then a **literal-GUID**
   `project_id`, `viewport`, `version: 1`. File extension **`.pipe`**.
2. **validate()** the whole pipeline (L3): `validate` tool / `tools/validate-pipeline.py <file>`
   (calls `client.validate()` → `{errors, warnings}`) / `--static` lint if no engine.
3. **The re-validation loop** (Forcing function 11): if `errors` is non-empty, show them
   **verbatim**, fix the offending node (loop back to Step 1 for that node — don't restart
   design), then **call validate() again**. Repeat until `errors == []`. Never write "validation
   passed" without a clean result in hand. Address warnings or explain why each is acceptable.
4. **Gate C** is a tool gate, not a user gate — it is "passed" only when validate() returns zero
   errors. Quote it: `validate(): 0 errors, K warnings`.

## Step 3 — Cost approval (→ Gate C.5)

Before handing off to run, estimate cost and gate it (GATE_PROTOCOL §5):
- Count paid/LLM nodes × expected calls × rough token cost; note if it runs on cloud compute
  (billed to the wallet) vs the user's own dev keys locally.
- **Gate C.5:**
  > This run will cost ≈ $X (<basis>). Approve this run? (yes / no)
  STOP and wait. "Just run it" earlier is not cost approval. A tiny local test on the user's own
  key can be a one-line confirm; cloud/large runs always gate.

Hand the validated `.pipe` to `rocketride-running-pipelines`.

## Red flags

| Thought | Reality |
|---|---|
| "I'll set apikey/model from what I remember" | Fetch the schema; field names differ per provider (`modelTotalTokens`, profile keys). |
| "Required fields only; prose constraints are optional" | Conditional rules ("if X then Y") are required too — state and satisfy them. |
| "I'll run the checklist once at the end" | Per node, as a gate, stated yes/no. A checklist skimmed once is a checklist skipped. |
| "validate() erred but I fixed it in the text" | A fix you didn't re-validate is a guess. Re-call validate() until errors == []. |
| "Zero errors but warnings — ship it" | Read each warning; fix or justify. Warnings are often the real bug. |
| "Hardcode the key just for the test" | Never. `${ROCKETRIDE_*}` always; literal keys leak and break substitution. |
| "Skip the cost gate, it's a small run" | Present Gate C.5 regardless; let the user decide. |

## Supporting files

- `PIPELINE_ANTIPATTERNS.md` — the real common mistakes, the 9-point checklist, the error table
- `tools/fetch-node-schema.py` — `get_service(name)` (live) or read `.rocketride/schema/<name>.json`
- `tools/validate-pipeline.py` — `client.validate(pipeline)`; `--static` = local lint, no engine
