# .context/

Working/runtime context for the skills. Not source — runtime files here are gitignored.

## GATE_STATE.md (runtime, gitignored)

The orchestrator writes per-session gate state here so gates survive across turns and context
resets (forcing function 3 / GATE_PROTOCOL §2). Format — one line per gate:

```
GATE A | presented turn 3 | status: AWAITING
GATE A | presented turn 3 | status: APPROVED "yes, those 5 nodes"
GATE C.5 | presented turn 7 | status: AWAITING
```

Rules:
- A gate is APPROVED only when a human answers it explicitly. Record their words.
- A dismissed / unanswered gate stays AWAITING — re-present it unchanged; never auto-approve.
- A vague follow-up ("go ahead") does not approve a specific AWAITING gate.
- If this file can't be written (no FS access), restate the open gate at the top of every turn
  until it's answered. Never advance past an AWAITING gate.
