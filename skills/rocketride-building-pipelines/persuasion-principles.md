# Persuasion Principles for the Gate Protocol

**Load this when:** authoring or editing a forcing function — to pick the lever that makes a weak
model actually comply, and to understand *why* the existing rules are worded the way they are.

## Why this exists

LLMs are *parahuman*: trained on human text, they respond to the same compliance levers humans do.
Meincke et al. (2025, N≈28,000 conversations) found persuasion technique more than doubled
compliance (33% → 72%). Our moat is built on this: the forcing functions don't make the model
smarter — they make a cheap model **comply under pressure**. Get the lever right and Haiku holds
the gate; get it wrong and it rationalizes past it. This is design, not manipulation — every lever
here serves the user's genuine interest (no wasted spend, no hallucinated pipelines).

## The levers we use (and the two we don't)

| Lever | What it is | How we use it |
|---|---|---|
| **Authority** | Deference to a definitive source | Imperative, non-negotiable wording: "YOU MUST", "NEVER", "No exceptions". The index / schema / `validate()` is *the* source of truth — the model defers to the tool, not its own guess. |
| **Commitment** | Consistency with a prior public statement | Force an explicit act: state a count line, cite the index entry, write `GATE_STATE.md`, answer the checklist yes/no per node. Having said it, the model stays consistent. |
| **Social Proof** | Conformity to the norm / named failure mode | "X without Y = failure. Every time." "Submitted ≠ succeeded." "A fix you didn't re-validate is a guess." Plus the real number: blast-through 32–45% → 0/24. |
| **Scarcity** | Urgency from a hard ordering | "BEFORE any run." "Immediately after selecting the node." Time-bounds defeat "I'll do it later." |

**Avoid Liking** — flattery / agreeableness breeds sycophancy and undercuts the honest "STOP, this
isn't approved." **Avoid Reciprocity** — guilt-based compliance feels manipulative and is weaker
than the four above. Discipline skills use Authority + Commitment + Social Proof + Scarcity.

## The psychology, briefly

- **Bright-line rules kill rationalization.** "NEVER, no exceptions" removes the "is this an
  exception?" decision the model would otherwise lose under pressure.
- **Implementation intentions automate behavior.** "When you present a gate, write `GATE_STATE.md`"
  (trigger → action) beats "track gates carefully."
- **Close every loophole explicitly.** State the rule, then forbid the specific workarounds the
  baseline run showed the model reaching for (see the red-flag tables and rationalization rows).

## The ethics test

Would the user endorse this technique if they understood it fully? Every lever here passes: it
exists to stop predictable, expensive failures (unapproved runs, hallucinated nodes, leaked keys).

---

## Appendix B — forcing function → lever map

Each forcing function (`GATE_PROTOCOL.md` §4) is built on a specific lever. When you edit one,
preserve its lever; when you add one, choose deliberately.

| FF | Forcing function | Primary lever(s) |
|---|---|---|
| 1 | Waiting = STOP | **Authority** (hard protocol) + **Social Proof** (32–45% → 0/24) |
| 2 | Deterministic gate wording | **Commitment** (forced binary/menu choice) + Authority |
| 3 | Multi-turn gate-state persistence | **Commitment** (written, re-presented unchanged) |
| 4 | Cite-your-source from the index | **Authority** (index is truth) + **Commitment** (must state the citation) |
| 5 | Mandatory L2 schema fetch before config | **Authority** (schema is truth) + **Scarcity** (before configuring) |
| 6 | Count lines on every list | **Commitment** (public count) + **Social Proof** (omission = visible lie) |
| 7 | Exhaustive archetype exploration | **Social Proof** (the norm is: walk every archetype) |
| 8 | Schema-fetch in the design phase too | **Scarcity** (before wiring) + Authority |
| 9 | Sequential checklist as a gate | **Commitment** (state each item yes/no) + Scarcity (per node) |
| 10 | Semantic / conditional constraints | **Authority** (schema rules) + Commitment (state them) |
| 11 | validate() + the re-validation loop | **Authority** (tool is the judge) + **Social Proof** ("a fix you didn't re-validate is a guess") |
| 12 | Continuous polling, real result | **Social Proof** ("submitted ≠ succeeded") + Commitment (state Status= each step) |
| 13 | Cost-approval gate (C.5) | **Authority** + **Scarcity** (before any paid run) |
| 14 | No secrets in pipelines | **Authority** ("never literals; `${ROCKETRIDE_*}` always") |
| 15 | Examples + anti-examples | **Social Proof** (adapt the worked example, not raw reasoning) |
| 16 | One map, one page — never the monolith | **Authority** ("NEVER fetch llms-full.txt, by any method") + Scarcity |
| 17 | Lazy schema fetch — never eager/bulk | **Authority** + **Scarcity** (only when about to wire THAT node) |

## Research

- Cialdini, R. B. (2021). *Influence: The Psychology of Persuasion (New & Expanded).* — the seven principles.
- Meincke, Shapiro, Duckworth, Mollick, Mollick & Cialdini (2025). *Call Me A Jerk: Persuading AI to
  Comply.* — N≈28,000 LLM conversations; compliance 33% → 72%; Authority, Commitment, Scarcity strongest.
