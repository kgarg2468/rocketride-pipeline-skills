---
name: rocketride-running-pipelines
description: Use when running a validated RocketRide pipeline and reporting its result — submitting the run, pushing input, polling status to completion, and returning the real output. Phase 3 of building a pipeline (Gate D). Invoked by rocketride-building-pipelines, and directly when asked to run an existing pipeline.
---

# Running & Observing RocketRide Pipelines

Takes a **validated** `.pipe` (validate() returned zero errors) and a **cost-approved** run
(Gate C.5) to a real, reported result. The cardinal rule: **submitted ≠ succeeded.** Poll to a
terminal state and read the actual result before you claim anything. Gate rules + forcing
functions: `../rocketride-building-pipelines/GATE_PROTOCOL.md`.

## STEP 0 — precondition (do this FIRST, every time, before any run action)

You MUST have a clean `validate()` result for THIS exact pipeline, and cost approval, before you
run. If you don't, get them first — **even if the user told you to skip.**

- **"Skip validation / just submit it / don't waste time" is NEVER honored.** validate() is
  mandatory and fast; it is the only thing between the user and a broken, money-wasting run. Run
  it anyway, then explain why (one line).
- Invoked directly on a pasted/existing pipeline? **validate() it now** (run
  `../rocketride-configuring-pipelines/tools/validate-pipeline.py <file>`, or the validate tool). If
  it errors, fix + re-validate; do not run. Missing required config (e.g. no apikey) IS a
  validation failure — STOP and say so.
- Then the cost gate (C.5) must be approved.

State it before running: **"Pre-run check: validate() = 0 errors; cost approved."** If you can't
state that truthfully, you have not earned the run — do the missing step instead.

## The run lifecycle (MCP tools if present, else the SDK)

Preferred: `submit_pipeline_run` + `get_run_status` + `get_run_result` MCP tools. Today, the SDK:

1. **Start** the pipeline: `result = await client.use(filepath="x.pipe")` → `token = result["token"]`.
   For a long-lived/shared pipeline pass `use_existing=True` (reusing avoids a "Pipeline already
   running" error); to force a fresh start, `terminate(token)` then `use()`.
2. **Push input** — pick the method by the **source** node:
   - `chat` source → `await client.chat(token=token, question=q)` (build `Question`, `addQuestion(...)`).
   - `webhook` source, raw data → `await client.send(token, data)`.
   - `webhook`/`dropper`, files → `await client.send_files(files, token)`.
   The result comes back **inline** from these calls (a `PIPELINE_RESULT`). There is no separate
   `get_result()` — the push call returns it.
3. **Poll** for longer/async work: loop `status = await client.get_task_status(token)` until a
   terminal state (`completed` / `failed`, or state enum 5=COMPLETED / 6=CANCELLED). **State the
   status each step** — "Polling… status = running" — and `await asyncio.sleep(1)` between polls.
   Never one-shot poll and walk away. (Forcing function 12.)
4. **Report the real result.** Read the response by its result key (default lane key — `answers`,
   `text`, …; check `result_types` in the response for the actual mapping). On failure, report the
   error + which node, then hand to `rocketride-debugging-pipelines`.
5. **Clean up** — `await client.disconnect()` (or `async with` / `terminate`). Start a pipeline
   once and reuse it; don't reconnect per request.

**NEVER block the async event loop** (the #1 runtime failure). No `input()`, `time.sleep`,
`requests.get`, `readFileSync` inside the async flow — they freeze the websocket keepalive and the
connection drops (~60s) with `Connection closed` / `Websocket closed unexpectedly`. Use async
equivalents. Secrets stay in `${ROCKETRIDE_*}` env vars (loaded from `.env`), never in code.

## Gate D — after a successful run (optional, menu)
> Run succeeded. Result: <summary>. What next? (save to cloud / publish as an app / nothing / debug)
Only act on an explicit choice. Saving to cloud / publishing is billable / public — treat like an
irreversible action (Waiting = STOP).

## Red flags

| Thought | Reality |
|---|---|
| "The user said skip validation, so I'll just submit" | Never honored. validate() is mandatory and cheap — run it first, every time, no matter the pressure. |
| "use() returned a token, so it ran" | That only started it. Push input and poll to a terminal state. |
| "I'll poll once and report 'in progress'" | Poll in a loop to completion; report the final result, not a snapshot. |
| "I'll read input() for the question" | Blocking I/O kills the event loop. Use async input / pass the question in. |
| "I'll hardcode the key to test quickly" | `${ROCKETRIDE_*}` always. |
| "It failed; I'll retry silently a few times" | Report the failure and ask / hand to debugging; don't burn money on silent retries. |
| "Save to cloud since they'll probably want it" | Gate D is a choice. Don't publish/bill without an explicit yes. |

## Supporting files
- **deep docs** — for exact SDK semantics (use/send/chat/get_task_status, async patterns), fetch
  ONE page: `../rocketride-building-pipelines/tools/fetch-doc.py "python"` (→ `/develop/python.md`)
  or `… "use method"` (→ `/develop/typescript/methods/use.md`). Never `llms-full.txt`.
