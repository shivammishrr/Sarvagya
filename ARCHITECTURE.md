# Sarvagya Architecture

Autonomous AI agent with hexagonal architecture. Zero coupling to LLM providers, ~1000 lines total.

## Interactive Architecture Diagram

Open **[docs/architecture.html](docs/architecture.html)** in a browser for a full interactive visualization.

## Provider Detection

Provider is auto-detected from the model name — no config needed:

| Model pattern | Adapter | SDK |
|--------------|---------|-----|
| `claude-*` / `anthropic-*` | `AnthropicAdapter` | `anthropic` |
| Everything else | `OpenAIAdapter` | `openai` |

Set `OPENAI_BASE_URL` env var for non-default OpenAI-compatible endpoints (Groq, Gemini, etc.).

## Quick Reference

```
sarvagya/
├── main.py              CLI entry → core.run()
├── prompts/system.md    Agent identity & rules
├── core/                Zero external dependencies
│   ├── types.py         8 dataclasses (ToolCall, Message, LLMResponse, ...)
│   ├── loop.py          AgentLoop (run → _step → _call_llm → _handle_response)
│   ├── context.py       Prompt assembly + message truncation
│   ├── tool_registry.py Register / schema / dispatch
│   └── tools/           bash, file_ops, search_ops, web
├── ports/               Pure Protocols (no implementations)
└── adapters/            SDK implementations (one file per provider)
    ├── llm/             OpenAIAdapter, AnthropicAdapter
    ├── sandbox/         LocalSandbox (subprocess)
    ├── memory/          FileMemory (markdown + YAML frontmatter)
    └── search/          TavilySearch (conditional)
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Hexagonal (Ports & Adapters) | Zero coupling to LLM providers |
| Core deps | Zero external | `core/` imports only stdlib + local |
| Provider detection | Model name heuristic | Swap providers by changing `--model`, not code |
| Sandbox | Local subprocess | Replace with E2B cloud sandbox as optional adapter |
| Memory | Filesystem markdown | No DB needed. Proven pattern from LangManus. |
| Agent loop | Sync, one action per iteration | Simple, observable, debuggable |
| Tool result truncation | 10,000 chars | Prevents context overflow |
| Message window | Last 20 turns | Sliding window context management |

## Agent Loop Flow

```
run(task)
  → append user message
  → for _ in range(max_iterations=50):
      → build_context(system + session + tools + messages)
      → LLM.complete() → LLMResponse
      → if tool_calls:
          → append assistant message (with tool_calls)
          → for each call: ToolRegistry.execute(name, args)
          → append tool result (truncated to 10k chars)
          → continue loop
      → if content:
          → return AgentResult(success=True, output=content)
  → return AgentResult(success=False, error="max iterations")
```

## Layer Rules

1. **`core/` imports ZERO external packages.** Only stdlib + local modules.
2. **`ports/` defines only Protocols.** No implementations, no third-party imports.
3. **`adapters/` is the ONLY layer that imports SDKs.** One file per provider.
4. **`main.py` / `core/__init__.py`** is the only composition root.
5. Every function ≤30 lines (enforced by AST check).

## Tools

| Tool | Handler | Parameters | Required |
|------|---------|------------|----------|
| bash | `sandbox.execute()` | command, timeout, description | command, description |
| read | `_read()` | file_path, offset, limit | file_path |
| write | `_write()` | file_path, content | file_path, content |
| edit | `_edit()` | file_path, old_string, new_string, replace_all | file_path, old_string, new_string |
| glob | `handle_glob()` | pattern, path | pattern |
| grep | `handle_grep()` | pattern, path, include | pattern |
| webfetch | `handle_webfetch()` | url | url |
| websearch | `tavily.search()` | query | query |
