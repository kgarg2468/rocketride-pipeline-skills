# Agent-pattern cheat-sheet — orchestrator + sub-agents (read ONCE)

For any "one orchestrator that delegates to specialist sub-agents, then returns one answer"
pipeline. Everything you need is here — do **NOT** re-open the full node index or grep the source.
Adapt `examples/TEMPLATE_multi_agent_orchestrator.pipe`; this sheet explains its wiring.

## The nodes
| role | provider | key config | input lane | control (on THIS node) |
|---|---|---|---|---|
| Source (pasted text) | `chat` | `hideForm:true, mode:"Source", type:"chat"` | — (it's the source) | — |
| Orchestrator | `agent_deepagent` | `instructions:[...], max_waves:10` | `questions` (from source) | — (it's the invoker) |
| Sub-agent | `agent_deepagent_subagent` | `name, description, instructions:[...]` | **none** — reached only by delegation | `[{classType:"deepagent", from:"<orchestrator id>"}]` |
| LLM (one per agent) | `llm_openai` | `profile:"gpt-4-1"` (or `gpt-4-1-mini`); `"<profile>":{apikey:"${ROCKETRIDE_OPENAI_KEY}"}` | — | `[{classType:"llm", from:"<the agent it powers>"}]` |
| Terminal | `response_answers` | `laneName:"answers"` | `answers` (from orchestrator) | — |

## The wiring rules (the #1 source of validate-fix cycles)
- **Control goes on the CONTROLLED node, pointing back to its invoker** — never on the agent itself.
  - each sub-agent → `control:[{classType:"deepagent", from:"<orchestrator>"}]`
  - each LLM → `control:[{classType:"llm", from:"<the agent that uses it>"}]`
- **Sub-agents have NO `input` lane** (`lanes:{}`); they're reached only via the orchestrator's
  delegation. Don't wire a data lane into a sub-agent.
- **Every agent needs its own `llm`** wired via control (orchestrator + each sub-agent → one llm each).
- **One source** (`chat`) → orchestrator's `questions`. **One terminal** (`response_answers`) ←
  orchestrator's `answers`. Not one response per agent.
- Keys are `${ROCKETRIDE_*}` env refs, never literals. `project_id` is a literal GUID.

## Shape (8 nodes for orchestrator + 2 sub-agents)
```
chat ──questions──▶ agent_deepagent (orchestrator) ──answers──▶ response_answers
                      ├─ llm_openai                  (control: llm ← orchestrator)
                      ├─ agent_deepagent_subagent #1 (control: deepagent ← orchestrator)
                      │    └─ llm_openai              (control: llm ← sub-agent #1)
                      └─ agent_deepagent_subagent #2 (control: deepagent ← orchestrator)
                           └─ llm_openai              (control: llm ← sub-agent #2)
```
Add or remove sub-agents (each with its own llm) as the task needs. Copy the template, fill the
`instructions`/`name`/`description` + a literal GUID, and validate once. That's the whole pattern.
