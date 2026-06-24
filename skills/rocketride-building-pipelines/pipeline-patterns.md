# Common Pipeline Patterns

A quick map of the shapes most requests reduce to. Match the request to a pattern, then adapt the
matching worked example in `rocketride-designing-pipelines/examples/`. These are starting points —
always verify node names + lanes against the live index and schemas.

**Build from a blanket request.** When a pattern fits, adapt its template — cheaper *and* more
accurate than wiring from scratch. Where a pattern leaves a node **open** (which store / llm /
embedding / agent), take the `../rocketride-designing-pipelines/NODE_DECISION_GUIDE.md` default and
**state the assumption** ("assumed `chroma` — request didn't specify"). Default *silently* on
everything mechanical (collection name, chunker profile, embedding dims, response terminal, memory
type). The exhaustive archetype walk (FF#7) still applies when no pattern fits.

A pipeline is a directed **acyclic** graph of nodes joined by **typed lanes**. Exactly one
**source** node; data flows source → … → a terminal (`response_*` for replies, a store/`db_*`
for ingestion). Lanes are typed channels — the output lane of one node must match an input lane
of the next, or you insert a converter.

## Lane cheat-sheet (input → node → output)
- `tags → parse → text, table, image, audio, video` (raw file bytes → extracted content)
- `text → preprocessor_langchain → documents` (chunk for retrieval)
- `text → question → questions` (turn raw text into askable questions; **not** after a `chat` source)
- `documents → embedding_* → documents` (add vectors; **required before any store**)
- `questions → embedding_* → questions` (vectorize a query)
- `questions → <vector store> → documents, answers, questions` (retrieve)
- `questions → llm_* → answers`
- `image → accessibility_describe / ocr → text`

## Pattern 1 — Conversational answer (chat → llm → response)
`chat → llm_openai → response_answers`. Source is `chat` (use `client.chat()`); LLM needs a
`profile` + apikey; terminal is `response_answers`. Simplest useful pipeline. See `simple-chat-rag`.

## Pattern 2 — RAG / answer-from-my-docs (chat → embed → store(search) → llm → response)
`chat → embedding_transformer → <store>(search) → llm_openai → response_answers`. The store node
(qdrant/chroma/pinecone/…) runs in **search mode** on the `questions` lane and returns context.
Use the **same embedding model** for ingestion and query. See `simple-chat-rag`.
*Defaults to state (if unspecified): store ◀`chroma`, embed ◀`embedding_openai`, llm ◀`llm_anthropic` — see `NODE_DECISION_GUIDE.md`.*

## Pattern 3 — Document ingestion (webhook → parse → preprocess → embed → store)
`webhook → parse → preprocessor_langchain → embedding_transformer → <store>(ingest)`. Terminal is
the **store** (ingest mode, `documents → []`) — ingestion pipelines need **no** response node.
Feed it with `client.send_files()`. See `document-ingestion`.

## Pattern 4 — Webhook transform / ETL (webhook → processor → response)
`webhook → <processor> → response_text`. For "take this input, do X, return result" with no
retrieval or chat. Feed with `client.send()`. Compose from the cheat-sheet with a real processor
(e.g. `summarization`, `extract_data`, `anonymize_text`); LLM-backed processors attach their llm
via the control plane.

## Pattern 5 — Agentic (chat → agent ← llm + tools + memory via control-plane)
`chat → agent_rocketride → response_answers`, with `llm_*`, `tool_*`, and `memory_*` attached to
the agent via the **control plane** (the controlled node carries `control: [{classType, from:
<agent id>}]`, NOT the agent). `agent_rocketride` requires exactly 1 llm and 1 memory; tools are
optional. Check each agent's `invoke` cardinality in the index. This is the most error-prone
shape — design it slowly, cite every invoke requirement. See the `agentic-chat` worked example.

## Pattern 6 — NL→database query (chat/webhook → db_* → response)
`db_postgres`/`db_mysql`/`db_neo4j`/etc. take `questions` and an attached `llm` (via control plane)
to craft SQL/Cypher. They appear in both `database` and `tool` classTypes — **default to the
data-flow `db_*` node** (a pipeline that queries the DB) and state the assumption; use the agent-tool
form only if the request describes an *agent/assistant that can query*.

## Pattern 7 — Summarize (source → parse → summarization → response)

`webhook → parse → summarization → response_text` (or `chat → summarization → response_text` for
pasted text). Single-shot "summarize / TL;DR these docs" — **no** retrieval, **no** store. The
`summarization` processor is LLM-backed: attach its `llm_*` via the control plane (the `llm` carries
`control: [{classType:"llm", from:"summarization_1"}]`). Feed files with `client.send_files()`.
*Defaults to state: llm ◀`llm_anthropic`. Don't grow this into RAG — summarize ≠ answer-from-docs.*

When a request doesn't fit cleanly, compose from the lane cheat-sheet: list the data you start
with, the data you want, and find the converter chain between them.
