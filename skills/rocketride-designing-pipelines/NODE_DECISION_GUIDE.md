# Node Decision Guide — which node for which use case

> Loaded once in Phase 1a (like `AGENT_PATTERN_CHEATSHEET.md`). **The default is the first row.**
> If no constraint below fires and the request doesn't pin a choice, take row 1, **state it as an
> assumption** ("assumed `chroma` — request didn't specify"), and proceed. Only the nodes listed here
> exist — never name a node that isn't in `LAYER1_NODE_INDEX.json`.

## Constraint override — check FIRST (a fired constraint *forces* the node; no question needed)

| If the request says / implies | Forced choice |
|---|---|
| offline / air-gapped / "no external services" | store `chroma` or `postgres` · embed `embedding_transformer` · llm `llm_ollama` — **never** a managed cloud node (`pinecone`/`llm_openai`/`llm_anthropic`) |
| already on Postgres / "use my Postgres" | vector store `postgres` (pgvector) — don't add a separate store |
| privacy / on-prem / "can't send data out" | `llm_ollama` + `embedding_transformer` + `chroma`/`postgres` |
| "managed / serverless / no ops" | store `pinecone` |

## Vector store (`store`) — DEFAULT ◀ `chroma`

| Option | Choose if |
|---|---|
| ◀ `chroma` | local / dev / prototype, < ~1M vectors — simplest to wire |
| `postgres` (pgvector) | already using Postgres; ≤ ~10M vectors; want one datastore |
| `qdrant` | self-hosted, scale + cost control, heavy filtered search |
| `pinecone` | fully managed, zero-ops |
| `weaviate` | hybrid (keyword + vector) / multimodal |
| `milvus` | very large (100M–B) / GPU |
| `astra_db` · `mongodb+srv` · `elasticsearch` · `opensearch` | reuse that existing infra |

## LLM (`llm`) — DEFAULT ◀ `llm_anthropic`

| Option | Choose if |
|---|---|
| ◀ `llm_anthropic` | instruction-following / agentic / long-doc / answer nodes — strong default |
| `llm_openai` | general-purpose, broad ecosystem |
| `llm_gemini` | largest context / multimodal / cheapest high-volume tier |
| ◀ `llm_ollama` | offline / private — **the offline default** |
| `llm_deepseek` · `llm_qwen` · `llm_mistral` | cost-optimized open-weight at volume |
| `llm_perplexity` | answers that need the live web |
| `llm_bedrock` | must run in AWS |

> Cost is a **pattern, not a number**: cheaper tier for high-volume/simple nodes, premium tier for
> reasoning/answer nodes. Never hardcode dollar amounts (they go stale).

## Embedding (`embedding`) — DEFAULT ◀ `embedding_openai`

| Option | Choose if |
|---|---|
| ◀ `embedding_openai` | general — cheap small variant / higher-quality large variant |
| ◀ `embedding_transformer` | offline / private / cost-binding (local miniLM-class) — **the offline default** |
| `embedding_image` · `embedding_video` | multimodal corpus |

> **Hard rule:** use the **same** embedding node for ingest and query, and its dimensions must match
> the store. Mismatched dims → retrieval returns nothing (a silent, validates-but-runs-wrong bug).

## Agent (`agent`) — DEFAULT ◀ `agent_rocketride`

| Option | Choose if |
|---|---|
| ◀ `agent_rocketride` | one agent with tools/memory — native, cheapest to wire (exactly 1 llm + 1 memory) |
| `agent_deepagent` | orchestrator + sub-agents / deep multi-step (control-plane) |
| `agent_crewai` (+ `agent_crewai_manager`) | role-specialized crew of agents |
| `agent_langchain` | only when LangChain compatibility is required |

> **Single-agent-first:** ~80% of tasks need one agent. A multi-agent crew "sounds more capable" but
> is usually the wrong, costlier choice — pick it only when the task genuinely has distinct roles.

---

*Anti-fabrication: every node named above exists in `LAYER1_NODE_INDEX.json`. Cohere / BGE lead public
embedding leaderboards but have **no embedding node** here (only `rerank_cohere` exists) — so they are
not recommendable; never invent a node to match a benchmark.*
