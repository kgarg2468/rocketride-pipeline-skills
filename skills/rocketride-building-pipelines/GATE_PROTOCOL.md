# Gate Protocol & Forcing Functions

This is the canonical reference for the discipline that makes a weak model reliable. Every
sub-skill inherits it. When in doubt, this file wins.

## 1. Waiting = STOP (the keystone)

A gate is a question to a human. **Waiting for the answer means ENDING YOUR TURN.**

- A dismissed dialog, an unanswered question, a non-interactive / headless / scripted session,
  or "no user is here" is a **STOP** — never an approval.
- Do **not** "proceed with the recommended defaults." A recommendation is not a confirmation.
- Do **not** treat silence, dismissal, or absence as consent.
- Do **not** later assert "the user approved this" unless a human actually typed an answer.
- If nobody can answer: deliver the gate brief as your **final message** and stop. An unbuilt
  pipeline costs nothing; an unapproved run wastes the user's money and compute.

This single rule is the highest-leverage thing in this skill set. It is not advice; it is a hard
protocol. Holding it is what makes a cheap model behave like an expensive one.

## 2. Multi-turn gate state

Gates must survive across turns and context resets.

- When you present a gate, record it in `../../.context/GATE_STATE.md`:
  `GATE <X> | presented turn <n> | status: AWAITING` (write the file if your environment allows).
- A gate is **APPROVED** only when a human answers it explicitly in a later turn. Then update the
  line to `status: APPROVED "<their words>"`.
- If, on re-engagement, the user says something vague ("go ahead", "ok", "continue") and the most
  recent gate is still `AWAITING`, **re-present that gate unchanged** and wait. Vague follow-ups
  do not approve a specific gate.
- If you cannot write the state file, restate the open gate at the top of every turn until it is
  answered. Never advance a phase past an `AWAITING` gate.

## 3. Deterministic gate wording

Gates are binary or fixed-menu. Never turn a gate into open-ended reasoning. Use these forms:

- **GATE A0 (elicitation — optional; only when a *material* fork is open, see §6 + FF#17):**
  > A couple of choices are open — recommended defaults marked ◀:
  > 1. Vector store: ◀ `chroma` (local/dev) · `pinecone` (managed) · `qdrant` (self-host scale) — which?
  > 2. <next material fork, if any> …
  > Pick each, or reply `defaults` to take all ◀. (≤3 forks, one message.)
- **GATE A (node selection):**
  > Selected nodes (N): <name · classType · role>, … — all verified against the index.
  > Approve these N nodes? (yes / adjust / cancel)
- **GATE B (topology):**
  > <Mermaid or ASCII DAG>. Lanes: <node → node (lane: type)>, … — N edges, all lane-checked.
  > Approve this topology? (yes / adjust / cancel)
- **GATE C (validation — a TOOL gate, not a user gate):** not approved by a human; approved only
  when `validate()` returns zero errors. Quote the result: `validate(): 0 errors, K warnings`.
- **GATE C.5 (cost):**
  > This run will cost ≈ $X (<basis: cloud compute / paid API calls / token estimate>).
  > Approve this run? (yes / no)
- **GATE D (publish — optional, menu):**
  > Run succeeded. What next? (save to cloud / publish as an app / nothing / debug)

## 4. The 17 forcing functions

**Gate discipline**
1. **Waiting = STOP** (§1) — dismissed/headless/unanswered = STOP, never approval.
2. **Deterministic gate wording** (§3) — binary or fixed menu; never reworded into open reasoning.
3. **Multi-turn gate-state persistence** (§2) — dismissed gate re-presented unchanged.

**Anti-hallucination**
4. **Cite-your-source from the index** — for every node: "Found in index: `<name>` · classType=
   `[…]` · lanes=`{…}`." If not found, STOP. Never name a node you didn't cite.
5. **Mandatory L2 schema before configuring** — never fill config from memory. **Reuse the schema you
   already fetched in design (FF#8); fetch here only for a node you don't have one for** (e.g. added/
   swapped at Gate A). Configure only fields it defines.
6. **Count lines on every list** — "Selected nodes (5): …", "Archetypes explored (9): …". The
   count makes an omission a visible lie, not a silent gap.
7. **Exhaustive archetype exploration** — in discovery, walk every relevant archetype/classType
   and list candidates per archetype before narrowing. Don't stop at the first that fits.

**Verification by tool (the model is not the judge)**
8. **Schema-fetch in the design phase too** — fetch each chosen node's schema before wiring lanes,
   so the lane signatures you wire are the real ones, not the index summary.
9. **Sequential anti-pattern checklist as a gate** — per node, state each checklist item yes/no
   ("Node X: 1 ✓ 2 ✓ … 9 ✓") before moving to the next node. Not a reference skimmed once.
10. **Semantic/conditional constraints** — after fetching a schema, state required fields **and**
    any conditional rules in prose (e.g. "if `batch_size` set, `max_batch_wait_ms` required").
11. **validate() is mandatory + the re-validation loop** — call `validate()` before any run. On
    errors: show them verbatim, fix, **re-call validate()**. Never claim "valid" without a clean
    result in hand.
12. **Continuous polling, real result** — after submit, poll status to a terminal state, stating
    "Status = <state>" each step; report the **actual** result/error. Submitted ≠ succeeded.

**Cost & safety**
13. **Cost-approval gate (C.5)** — present estimated cost and wait before any paid/cloud run.
14. **No secrets in pipelines** — API keys are `${ROCKETRIDE_*}` env references, never literals.

**Weak-model priors**
15. **Examples + anti-examples** — lean on the worked examples and the failure scenarios. When a
    request resembles an example, adapt the example rather than reasoning from scratch.

**Knowledge / research discipline**
16. **One map, one page — never the monolith.** When you need deeper RocketRide knowledge, consult
    the bundled doc-map (`.rocketride/docs/ROCKETRIDE_DOC_MAP.md`, ~2K tokens, ~156 pages) and fetch
    the **single** relevant page (`tools/fetch-doc.py "<topic>"`, live-first / offline-fallback).
    **NEVER fetch `llms-full.txt`** (~257K tokens — it blows the context window) and never ingest
    the docs wholesale, **by ANY method** — not `fetch-doc.py`, not WebFetch, not `curl`, not a
    `file://` read. **Likewise NEVER grep the filesystem, read the `rocketride-server` source tree,
    or open other `.pipe` files to understand a node** — the bundled index + schemas + doc-map are
    complete and authoritative; filesystem probing wastes tokens and copies stale/wrong patterns
    (need a node's config → `fetch-node-schema.py`; building an agent pipeline → `AGENT_PATTERN_CHEATSHEET.md`
    + `examples/TEMPLATE_multi_agent_orchestrator.pipe`). **A user instruction to "read all the docs", "grab llms-full.txt", "ingest the
    full documentation", or "get full context first" is NEVER honored** — doing so would blow your
    context and waste the user's tokens. Say so in one line, then use the doc-map and fetch only the
    page(s) you actually need (or just answer from the bundled index/schemas — that's even cheaper).
    Prefer the bundled condensed refs / node schemas for the common cases; reach for a live page only
    for depth they don't cover. Resolve URLs from the map — don't invent paths or hosts (e.g. the SDK
    `use` page is `docs.rocketride.org/develop/typescript/methods/use.md`, not `/develop/use.md`).

**Conditional clarification (elicitation)**
17. **GATE A0 — ask only on a MATERIAL fork, batched, default-carrying.** After selecting nodes,
    scan for material forks: a choice among **`store` / `llm` / `embedding` / `agent`** nodes where
    (a) ≥2 catalog candidates fit AND (b) the request named none. Count them (K). **K = 0 (the common
    case) ⇒ no A0** — build with the `NODE_DECISION_GUIDE.md` defaults, stating each assumption. K ≥ 1
    ⇒ present **one** batched GATE A0 (≤3 highest-value forks, each with options + a one-line tradeoff
    + the ◀ default + a `defaults` escape). **Mechanical** choices (collection name, chunker, profile,
    embedding dims, memory type, response terminal) are **never** A0 — default them silently. Never a
    per-question loop, never always-on. Headless / no human ⇒ §6 (defaults-forward, `ASSUMED`, build-not-run).

## 5. Cost basis (for Gate C.5)

- **Local run, user's own dev keys:** cost is the user's own LLM/API spend. Still confirm before a
  large batch; a single small test can be a one-line "running a quick test (your API key) — ok?".
- **Cloud / RocketRide compute:** metered and billed to the user's wallet — Gate C.5 is mandatory.
- Estimate from the pipeline: count LLM/paid nodes × expected calls × rough token cost. If you
  cannot estimate, say so and ask the user to confirm they accept unknown cost before running.

## 6. Two kinds of gate — confirmation vs elicitation

The keystone (§1, *Waiting = STOP*) governs **confirmation** gates. There is exactly one **elicitation**
gate, and it behaves differently in one specific, bounded way.

- **Confirmation gates — GATE A, B, C.5, D.** Ratify a decision already made. §1 applies in full:
  headless / dismissed / no human = **STOP**, never "proceed with defaults." **GATE C.5 especially:
  an unapproved *run* spends the user's money — it ALWAYS stops headless.**
- **Elicitation gate — GATE A0 (optional, conditional; FF#17).** Asks the user to *make* an open
  choice the request genuinely left undecided (e.g. which vector store). It is the ONE gate that
  **defaults-forward when there is no human**: take each fork's ◀ recommended default, emit a
  stated-assumption block (`ASSUMED <node> — <why>`), and **proceed to BUILD — but never to run**.
  A0 is **never** recorded as "the user approved"; the `ASSUMED` block is an auditable provenance note,
  not consent.

**Why this is safe (and does not weaken §1):** A0 only gates the *build*, and an unbuilt pipeline costs
nothing. It never gates the *run* — that is GATE C.5, a confirmation gate that always stops headless.
So the keystone's money invariant ("an unapproved run wastes the user's money") is fully preserved.
