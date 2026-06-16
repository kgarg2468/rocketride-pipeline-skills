---
title: Overview
slug: /nodes
sidebar_position: 0
---

Nodes are the building blocks of a RocketRide pipeline. A [pipeline](/concepts/pipelines)
is a directed graph, and each node is one component that does one job: call a model,
embed text, query a vector store, parse a document, or run a tool. You wire nodes
together and the [engine](/concepts/runtime-engine) runs them.

This page explains how a node is structured on disk and how the runtime loads and
executes it, then catalogs every node that ships with the toolchain, grouped by type.

## Anatomy of a node

Each built-in node is a directory under `nodes/src/nodes/<name>/`. A node is its
service manifest plus an implementation and its documentation:

```
nodes/src/nodes/llm_openai/
  services.json     # the manifest: identity, class type, capabilities, config schema
  IGlobal.py        # node-level lifecycle: config validation, dependency loading
  IInstance.py      # per-instance behaviour: what the node does each invocation
  *_client.py       # provider/client implementation detail
  requirements.txt  # Python dependencies, installed on demand
  <name>.svg        # canvas icon
  README.md         # co-located documentation (rendered as this node's page)
```

The **`services.json`** manifest is the contract the engine reads. Its key fields:

| Field | Purpose |
| --- | --- |
| `title` | Display name on the canvas and in this catalog. |
| `protocol` | The node's URL scheme, e.g. `llm_openai://`. |
| `classType` | The kind of work the node does (`llm`, `store`, `tool`, …). Governs how it wires into the graph. |
| `capabilities` | Flags that change engine behaviour, e.g. `invoke`. |
| `register` | How the engine registers the node: `filter` (transforms data in the graph) or `endpoint` (an edge connector). |
| `node` / `path` | The runtime (`python`) and module (`nodes.llm_openai`) the engine instantiates. |
| `prefix` | Prefix swapped when converting between URLs and module paths. |
| `description` | Prose shown in the editor. |
| `config` | The configuration schema: the fields a pipeline author fills in. |

A node's public contract is its `classType`, config schema, and the input/output
lanes it supports. The [pipeline JSON reference](/pipeline-reference) documents how a
node is referenced from a `.pipe` file (`id`, `provider`, `config`, `input`).

## How the runtime runs a node

1. **Discovery & registration.** On startup the engine scans every `services*.json`
   and registers a factory keyed by `protocol`/`prefix`. The `register` value decides
   whether the node is a `filter` in the graph or an `endpoint` connector at its edge.
2. **Instantiation.** When a pipeline references a provider, the engine instantiates
   the implementation named by `node` and `path`. `IGlobal` runs once per node
   definition (it validates `config` and loads `requirements.txt` on demand);
   `IInstance` carries the per-invocation behaviour.
3. **Wiring.** The `classType` determines how the node connects. Data nodes exchange
   data through **lanes**; `agent`, `tool`, `llm`, and `memory` nodes participate in
   **control** connections (see [Agents & tools](/concepts/agents-tools-skills)).
4. **Execution.** The engine drives the graph from sources to targets, passing each
   node's output along its lanes. `capabilities` flags toggle engine features such as
   `invoke`. See the [execution model](/concepts/execution-model) for how data flows.

Because behaviour lives in `provider` + `config`, swapping which model or store a
pipeline uses is a config edit, not a code change.

## Node types

109 nodes across 20 types. Every node declares a
class type in its manifest; the catalog below is grouped by it.

### Sources

Bring data into a pipeline: webhooks, chat, file and database readers, and cloud connectors.

| Node | Description |
| --- | --- |
| [Chat](/nodes/webhook/chat) | A user interface component that provides a web-based chat experience. |
| [Drag & Drop](/nodes/webhook/dropper) | A user interface component that provides a web-based dropper experience. |
| [Telegram Bot](/nodes/telegram) | A Telegram Bot source node that receives messages from users via the Telegram Bot API. |
| [Webhook](/nodes/webhook) | A user interface component that provides a web-based chat experience. |
| [Webhook](/nodes/webhook/webhook) | A source component that listens for incoming HTTP requests and accepts uploaded documents or data from external systems or processes. |

### LLMs

Call large language models for generation, chat, summarization, and reasoning across many providers.

| Node | Description |
| --- | --- |
| [Amazon Bedrock](/nodes/llm_bedrock) | A component that connects to Amazon Bedrock, providing access to a range of foundation models from leading AI providers through a unified AWS interface. |
| [Anthropic](/nodes/llm_anthropic) | A component that integrates with Anthropic's Claude models for natural language understanding and generation. |
| [Baidu Qianfan](/nodes/llm_baidu_qianfan) | A component that connects to Baidu Qianfan ERNIE large language models through Qianfan's OpenAI-compatible chat-completions API. |
| [Deepseek](/nodes/llm_deepseek) | A component that connects to DeepSeek’s large language models for advanced natural language processing. |
| [Gemini](/nodes/llm_gemini) | A component that connects to Gemini models for advanced natural language processing. |
| [GMI Cloud](/nodes/llm_gmi_cloud) | A component that connects to GMI Cloud's large language models for advanced natural language processing. |
| [Kimi (Moonshot)](/nodes/llm_kimi) | A component that connects to Moonshot AI's Kimi large language models for advanced natural language processing. |
| [MiniMax](/nodes/llm_minimax) | A component that connects to MiniMax's large language models for advanced natural language processing. |
| [Mistral AI](/nodes/llm_mistral) | A component that connects to Mistral AI's advanced language models for natural language processing. |
| [Ollama](/nodes/llm_ollama) | A component that integrates with locally-hosted language models through Ollama. |
| [OpenAI](/nodes/llm_openai) | A component that connects to OpenAI's latest GPT models for advanced natural language processing. |
| [OpenAI-Compatible API](/nodes/llm_openai_api) | A component that connects to any OpenAI-compatible API endpoint for language model inference. |
| [Perplexity](/nodes/llm_perplexity) | A component that connects to Perplexity AI's Sonar models for advanced natural language processing with real-time web search capabilities. |
| [Qwen](/nodes/llm_qwen) | A component that connects to Alibaba Cloud's Qwen large language models via the DashScope API. |
| [xAI](/nodes/llm_xai) | A component that integrates with xAI's Grok language models for intelligent text generation and analysis. |

### Vision & Image

Analyze and transform images: vision models, OCR, thumbnails, cleanup, and accessibility descriptions.

| Node | Description |
| --- | --- |
| [Accessibility Describe](/nodes/accessibility_describe) | An accessibility-focused image analysis node that generates scene descriptions optimized for blind and visually impaired users. |
| [Cleanup](/nodes/image_cleanup) | A component that processes an image, cleans it up for OCR tasks by converting togray scale, removing noise, deskewing, and enhancing contrast. |
| [Gemini Vision](/nodes/llm_vision_gemini) | A component that connects to Google Gemini's vision-capable models for image analysis, OCR, visual understanding, and scene description. |
| [Mistral Vision](/nodes/llm_vision_mistral) | A component that connects to Mistral AI's vision-capable models for image analysis, OCR, and visual understanding tasks. |
| [OCR](/nodes/ocr) | A component that extracts machine-readable text from images and scanned documents using optical character recognition. |
| [Ollama Vision](/nodes/llm_vision_ollama) | A component that connects to locally-hosted open-source vision models through Ollama for image analysis, description, and visual understanding tasks. |
| [OpenAI Vision](/nodes/llm_vision_openai) | A component that connects to OpenAI's vision-capable models for image analysis, OCR, visual understanding, and scene description. |
| [Thumbnail](/nodes/thumbnail) | A processing component that creates thumbnails from input images. |

### Audio

Work with audio: transcription, text-to-speech, and playback.

| Node | Description |
| --- | --- |
| [Player](/nodes/audio_player) | The Audio Player component plays audio through the system’s default audiooutput device, including the audio track from video content. |
| [Text To Speech](/nodes/audio_tts) | Converts incoming text into speech using Kokoro-82M (local KPipeline or --modelserver KokoroLoader).Output is sent on the audio lane as WAV bytes.See README for spaCy en_core_web_sm (misaki) and troubleshooting. |
| [Transcribe](/nodes/audio_transcribe) | The Audio transcribe component recieves audio or video and transcribes into text. |

### Video

Process video: frame extraction, embeddings, and video understanding.

| Node | Description |
| --- | --- |
| [Frame Grabber](/nodes/frame_grabber) | A component that extracts frames from video files and outputs them as image data. |
| [TwelveLabs](/nodes/twelvelabs) | Sends a video to TwelveLabs along with instructions and returns the generated text response. |

### Text

Operate on text: summarization, extraction, named-entity recognition, and anonymization.

| Node | Description |
| --- | --- |
| [Anomaly Detector](/nodes/anomaly_detector) | A pipeline monitoring component that detects anomalies in numeric output values using statistical methods. |
| [Anonymize](/nodes/anonymize) | A filter component that identifies and masks sensitive information in text data. |
| [Data Extractor](/nodes/extract_data) | A component that processes unstructured or semi-structured text and extracts structured data in a tabular format. |
| [Dictionary](/nodes/dictionary) | A processing component that analyzes documents to extract a dictionary of key terms and phrases. |
| [Named Entity Recognition](/nodes/ner) | A text processing component that identifies and extracts named entities from text using state-of-the-art transformer models. |
| [Prompt](/nodes/prompt) | A transformation component that takes multiple inputs and merges them into a single question with a configurable prompt. |
| [Question](/nodes/question) | A transformation component that takes input text and encapsulates it as a Question object without modification. |
| [Summarization: LLM](/nodes/summarization) | A processing component that analyzes document content to extract concise summaries, key points, and named entities. |

### Embeddings

Turn text, images, or video into vectors for semantic search and retrieval.

| Node | Description |
| --- | --- |
| [Image](/nodes/embedding_image) | A processing component that generates vector embeddings from image content using advanced computer vision models. |
| [OpenAI (Embedding)](/nodes/embedding_openai) | A component that transforms text into numerical vector representations using advanced embedding models. |
| [Transformer](/nodes/embedding_transformer) | A component that transforms text into numerical vector representations using advanced embedding models. |
| [Video](/nodes/embedding_video) | A processing component that generates vector embeddings from video content by extracting frames at configurable intervals and encoding them using vision models such as CLIP. |

### Rerank

Reorder retrieved results by relevance to a query.

| Node | Description |
| --- | --- |
| [Cohere Rerank](/nodes/rerank_cohere) | A reranking component powered by Cohere's Rerank API that improves search quality by reordering retrieved documents based on their relevance to a given query. |

### Search

Query external search providers and the web.

| Node | Description |
| --- | --- |
| [Exa Search](/nodes/search_exa) | A direct Exa web search node.Accepts user questions and returns Exa's raw search JSON as the answer. |

### Vector Stores

Store and query embeddings for retrieval: Qdrant, Pinecone, Milvus, Chroma, and more.

| Node | Description |
| --- | --- |
| [Astra DB](/nodes/astra_db) | A vector database component for Astra DB, enabling efficient storage and retrieval of vector embeddings. |
| [Chroma](/nodes/chroma) | A vector database component for Chroma, enabling efficient storage and retrieval of vector embeddings. |
| [Elasticsearch](/nodes/index_search/elasticsearch) | A vector database component for Elasticsearch, enabling efficient storage and retrieval of vector embeddings. |
| [Index Search](/nodes/index_search) | A vector database component for Elasticsearch, enabling efficient storage and retrieval of vector embeddings. |
| [Milvus](/nodes/milvus) | A vector database component for Milvus, enabling efficient storage, indexing, and retrieval of vector embeddings. |
| [MongoDB Atlas](/nodes/atlas) | A vector database component for MongoDB Atlas, enabling efficient storage and retrieval of vector embeddings using MongoDB's native vector search capabilities. |
| [OpenSearch](/nodes/index_search/opensearch) | An OpenSearch node that supports classic BM25 search and vector search for ingestion and retrieval workflows. |
| [Pinecone](/nodes/pinecone) | A component that connects to the Pinecone vector database for storing and retrieving high-dimensional embeddings. |
| [PostgreSQL (pgvector)](/nodes/vectordb_postgres) | A component that enhances PostgreSQL with vector similarity search capabilities through the pgvector extension. |
| [Qdrant](/nodes/qdrant) | A vector database component for Qdrant, enabling efficient storage and retrieval of vector embeddings. |
| [Weaviate](/nodes/weaviate) | A component that stores vector embeddings in a Weaviate instance for semantic search and retrieval. |

### Databases

Read from and write to relational and graph databases.

| Node | Description |
| --- | --- |
| [Aparavi AQL](/nodes/aparavi_aql) | Queries the Aparavi data governance platform using AQL (Aparavi Query Language). |
| [ClickHouse](/nodes/db_clickhouse) | A ClickHouse component that answers natural-language questions by translating them into SQL and executing them against the database, returning rows as a table, text, or structured answers. |
| [MySQL](/nodes/db_mysql) | A processing component that takes structured table data and inserts it into a MySQL database. |
| [Neo4J](/nodes/db_neo4j) | A processing component that connects to a Neo4J graph database. |
| [PostgreSQL](/nodes/db_postgres) | A processing component that takes structured table data and inserts it into a PostgreSQL database. |

### Memory

Persist and recall conversational or working state across runs.

| Node | Description |
| --- | --- |
| [Memory (Internal)](/nodes/memory_internal) | Run-scoped keyed memory store exposed as agent tools.Provides put, get, peek, list, and clear operations so agents canpersist intermediate results across planning waves without bloatingthe LLM context window. |
| [Persistent Memory](/nodes/memory_persistent) | A persistent cross-session memory node that retains data across pipelineinvocations. |

### Agents

Autonomous nodes that plan and call tools to accomplish a goal.

| Node | Description |
| --- | --- |
| [CrewAI Agent](/nodes/agent_crewai) | Standalone single-agent CrewAI node.Can be invoked as a tool (`<nodeId>.run_agent`) by other agents.For multi-agent delegation, use a CrewAI Manager + CrewAI Subagent nodes. |
| [CrewAI Agent](/nodes/agent_crewai/crewai_agent) | Standalone single-agent CrewAI node.Can be invoked as a tool (`<nodeId>.run_agent`) by other agents.For multi-agent delegation, use a CrewAI Manager + CrewAI Subagent nodes. |
| [CrewAI Manager](/nodes/agent_crewai/crewai_manager) | Multi-agent manager using CrewAI hierarchical process.Fans out to connected CrewAI Subagent nodes, assembles a Crew, and synthesizes their outputs.Can be invoked as a tool (`<nodeId>.run_agent`) for nested orchestration. |
| [CrewAI Subagent](/nodes/agent_crewai/crewai_subagent) | Managed CrewAI sub-agent. |
| [Deep Agent](/nodes/agent_deepagent) | Single-agent execution using Deep Agents.Adds strategic planning, persistent state, and long-context management on top of LangChain.Connect Deep Agent Subagent nodes via the deepagent invoke channel for hierarchical delegation.Can be invoked as a tool (`<nodeId>.run_agent`) by other agents. |
| [Deep Agent](/nodes/agent_deepagent/deepagent_agent) | Single-agent execution using Deep Agents.Adds strategic planning, persistent state, and long-context management on top of LangChain.Connect Deep Agent Subagent nodes via the deepagent invoke channel for hierarchical delegation.Can be invoked as a tool (`<nodeId>.run_agent`) by other agents. |
| [DeepAgent Subagent](/nodes/agent_deepagent/deepagent_subagent) | Managed Deep Agent subagent. |
| [LangChain](/nodes/agent_langchain) | Single-agent execution using LangChain.Can be invoked as a tool (`<nodeId>.run_agent`) for hierarchical agent orchestration. |
| [LlamaIndex](/nodes/agent_llamaindex) | Single-agent execution using LlamaIndex's ReAct loop.Can be invoked as a tool (`<nodeId>.run_agent`) for hierarchical agent orchestration. |
| [RocketRide Wave](/nodes/agent_rocketride) | Wave-planning agent built natively on the RocketRide architecture.Plans each step as a wave of parallel tool calls, uses keyed memory to stay token-efficient,and requests tool schemas on demand instead of loading them all upfront.Can be invoked as a tool (`<nodeId>.run_agent`) for hierarchical agent orchestration. |

### Tools

Capabilities an agent or pipeline can invoke: HTTP, shell, code execution, and external APIs.

| Node | Description |
| --- | --- |
| [Apify](/nodes/tool_apify) | Exposes Apify Actors as agent tools.Provides run_actor (run an Actor and return its dataset) and get_dataset_items. |
| [Bland AI](/nodes/tool_bland_ai) | Make and manage AI-powered phone calls via Bland AI.The agent can initiate outbound calls, retrieve call transcripts, and analyze completed calls.Requires a Bland AI API key from https://www.bland.ai |
| [Chart (Chart.js)](/nodes/tool_chartjs) | Generates Chart.js v4 chart configurations from data using the pipeline LLM.The agent provides raw data and an optional chart type or description.Returns a ```chartjs fenced code block ready for rendering in the chat UI. |
| [Daytona](/nodes/tool_daytona) | Gives agents an isolated Daytona cloud sandbox for running code and shell commands.Provides run_code, run_command, upload_file and download_file on one shared ephemeral sandbox. |
| [DeepL](/nodes/tool_deepl) | Exposes DeepL translation and AI rephrasing as agent tools.Translates text into a target language or rewrites it in a chosen style or tone via the DeepL API, returning the result plus the detected source language. |
| [Exa Search](/nodes/tool_exa_search) | Exposes Exa semantic web search as an agent tool.Performs real-time web searches via the Exa API and returns structured results with titles, URLs, text content, relevance scores, and dates. |
| [FalkorDB](/nodes/tool_falkordb) | Lets agents query a FalkorDB graph database with Cypher.Provides query (read-only by default, server-enforced), list_graphs and get_schema. |
| [File System](/nodes/tool_filesystem) | File system tool for agents. |
| [Firecrawl](/nodes/tool_firecrawl) | Exposes Firecrawl web-scraping operations as agent tools.Provides scrape_url (single page) and map_url (site structure discovery). |
| [Git](/nodes/tool_git) | Exposes local Git repository operations as agent tools. |
| [GitHub](/nodes/tool_github) | Exposes GitHub repository operations as agent tools.Covers files, issues, pull requests, reviews, releases, workflows, orgs, users,code search, and commit history. |
| [HTTP Request](/nodes/tool_http_request) | Makes HTTP requests to any API endpoint, like curl for agents.The agent provides the full request (method, URL, headers, body, auth).The node enforces security guardrails: only whitelisted URLs and enabled HTTP methods are permitted. |
| [MCP Client](/nodes/tool_mcp_client) | Connects to the Butterbase MCP server and exposes its backend tools for agent tool-calling.Butterbase is an AI-optimized Backend-as-a-Service (managed database, authentication, object storage, serverless functions, RAG). |
| [Pipeline Tool](/nodes/tool_pipe) | Exposes an inline pipeline as an agent tool.Connect this node's output lanes to any pipeline nodes on the same canvas.When an agent calls the tool, the input is routed to every connected output lane.End each connected branch with a response node to return results. |
| [Python](/nodes/tool_python) | Executes Python code in a restricted in-process sandbox via exec().Only whitelisted modules can be imported. |
| [Tavily](/nodes/tool_tavily) | Exposes Tavily real-time web search as an agent tool.Performs live web searches via the Tavily API and returns structured results with titles, URLs, content snippets, and relevance scores. |
| [v0 by Vercel](/nodes/tool_v0) | A component that connects to Vercel's v0 API to generate React + Tailwind CSS UI components from natural-language prompts. |
| [xTrace Memory](/nodes/tool_xtrace_memory) | Long-term, shared agent memory exposed as tools, backed by xTrace Memory Manager.Exposes two agent tools: 'remember' stores conversation turns and 'recall' returns the relevant, ready-to-inject context. |

### Preprocessors

Prepare and chunk data before embedding or model calls.

| Node | Description |
| --- | --- |
| [Code](/nodes/preprocessor_code) | A specialized component designed to parse and tokenize source code. |
| [General Text](/nodes/preprocessor_langchain) | A preprocessing component that segments large bodies of text into intelligently sized chunks for downstream processing. |
| [LLM](/nodes/preprocessor_llm) | A processing component that analyzes document content to extract concise summaries, key points, and named entities and to divide a document for storage into a vector database. |

### Data

Extract, shape, and route structured data within the pipeline.

| Node | Description |
| --- | --- |
| [LlamaParse](/nodes/llamaparse) | A document parsing component that uses LlamaParse to extract text and structured data from various document formats including PDFs, images, Word documents, Excel spreadsheets, and other formats. |
| [Reducto](/nodes/reducto) | A parsing component that uses Reducto to extract text and structured data from various document formats including PDFs, images, and other document types. |

### Guardrails

Validate and constrain inputs and outputs for safety and policy.

| Node | Description |
| --- | --- |
| [Guardrails](/nodes/guardrails) | A comprehensive input/output guardrails filter for AI safety. |

### Outputs

Send results out of the pipeline: responses, files, and external systems.

| Node | Description |
| --- | --- |
| [Local Text Output](/nodes/local_text_output) | A target component that writes data to the file system. |
| [Text Output](/nodes/text_output) | A target component that writes data to the file system. |

### Infrastructure

Plumbing that supports execution rather than transforming data.

| Node | Description |
| --- | --- |
| [Remote Processing](/nodes/remote) | A transport component that forwards data to a remote machine or processing node. |
| [Response](/nodes/response) | A component that returns processed answers back to the requesting client. |

### Other

Nodes that do not fall into a single category above.

| Node | Description |
| --- | --- |
| [Core](/nodes/core) | A combined configuration that bundles a preprocessor, embedding model, vector store, and LLM into a single selectable unit. |
| [Fingerprinter](/nodes/core/hash) | A processing component that generates a unique fingerprint (hash) of a document's content. |
| [IBM Watson](/nodes/llm_ibm_watson) |  |
| [Parse/Process/Embed](/nodes/autopipe) | This component combines document parsing, text preprocessing, and embedding generation in a single node.It provides an end-to-end solution for converting raw documents into vector representationssuitable for semantic search and analysis. |
| [Parser](/nodes/core/parser) | A document parsing component that extracts rich content from a wide variety of document types. |
| [Vectorizer](/nodes/vectorizer) | An internal filter that chunks incoming text, computes embeddings via the configured embedding component, and writes the resulting documents to the vector store. |
