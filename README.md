# Sarvagya

Autonomous AI agent with hexagonal architecture. Zero coupling to LLM providers. ~1000 lines.

```bash
pip install -e ".[all]"
set API_KEY=sk-...   set MODEL=gpt-4o
sarvagya "List all Python files in this project"
```

---

## Architecture

Sarvagya uses **hexagonal architecture (Ports & Adapters)**. The domain layer (`core/`) imports **zero external packages**. All SDK coupling lives in `adapters/`. Providers are swapped by changing the model name — no config, no code changes.

```mermaid
flowchart TB
    subgraph CLI["Composition Root"]
        main_py["main.py"]
        core_init["core/__init__.py<br/>wires everything"]
    end

    subgraph Core["Domain Layer (core/) — zero external deps"]
        types["types.py<br/>8 dataclasses"]
        loop["loop.py<br/>AgentLoop"]
        context["context.py<br/>prompt builder"]
        registry["tool_registry.py<br/>register + dispatch"]
        tools_pkg["tools/<br/>bash, file_ops, search, web"]
    end

    subgraph Ports["Ports Layer (ports/) — Protocols only"]
        port_llm["LLMProvider"]
        port_sbox["Sandbox"]
        port_mem["Memory"]
        port_srch["WebSearch"]
    end

    subgraph Adapters["Adapters Layer (adapters/) — SDKs live here"]
        adapt_llm["llm/<br/>OpenAIAdapter · AnthropicAdapter"]
        adapt_sbox["sandbox/<br/>LocalSandbox"]
        adapt_mem["memory/<br/>FileMemory"]
        adapt_srch["search/<br/>TavilySearch"]
    end

    subgraph External["External"]
        direction LR
        API["OpenAI / Groq / Gemini / etc"]
        CLAUDE["Anthropic Claude"]
        FS["Filesystem"]
    end

    main_py --> core_init
    core_init --> loop & registry & tools_pkg
    core_init --> adapt_llm & adapt_sbox & adapt_mem & adapt_srch
    loop --> port_llm & port_sbox & port_mem
    loop --> context & registry
    tools_pkg --> registry

    port_llm -.-> adapt_llm
    port_sbox -.-> adapt_sbox
    port_mem -.-> adapt_mem
    port_srch -.-> adapt_srch

    adapt_llm --> API & CLAUDE
    adapt_sbox --> FS
    adapt_mem --> FS
```

## Agent Loop

One action per iteration — think, call one tool, observe, repeat.

```mermaid
flowchart TD
    START(["run(task)"]) --> APPEND["append user message"]
    APPEND --> STEP{"_step()"}

    STEP --> BUILD["build_context()<br/>system + session + tools + messages"]
    BUILD --> LLM_CALL["_call_llm()<br/>LLMProvider.complete()"]
    LLM_CALL --> CHECK{"response"}

    CHECK -->|"exception"| FAIL["return AgentResult(error)"]
    CHECK -->|"tool_calls"| EXEC["_handle_response()"]
    CHECK -->|"content"| SUCCESS["return AgentResult(output)"]

    EXEC --> ASM["append assistant message<br/>with tool_calls"]
    ASM --> DISPATCH["for each call:<br/>ToolRegistry.execute(name, args)"]
    DISPATCH --> RESULT["append tool result<br/>(truncated 10k chars)"]
    RESULT --> STEP

    FAIL --> DONE
    SUCCESS --> DONE
```

## File Structure

```
sarvagya/
├── main.py                    CLI entry + DI container (36 lines)
├── prompts/
│   └── system.md              Agent identity & rules (markdown)
├── core/                      Domain — zero external dependencies
│   ├── __init__.py            Composition root (60 lines)
│   ├── types.py               8 dataclasses (62 lines)
│   ├── loop.py                AgentLoop — think/tool/observe (76 lines)
│   ├── context.py             System prompt + message assembly (49 lines)
│   ├── tool_registry.py       Register, schema, dispatch (45 lines)
│   └── tools/
│       ├── __init__.py        init_tools() (18 lines)
│       ├── bash.py            Shell execution (39 lines)
│       ├── file_ops.py        Read/write/edit (93 lines)
│       ├── search_ops.py      Glob/grep (56 lines)
│       └── web.py             Web fetch (31 lines)
├── ports/                     Protocols — pure Python, no deps
│   ├── llm.py                 LLMProvider (12 lines)
│   ├── sandbox.py             Sandbox (19 lines)
│   ├── memory.py              Memory (19 lines)
│   └── search.py              WebSearch (6 lines)
└── adapters/                  SDK implementations — one file per provider
    ├── llm/
    │   ├── openai.py          OpenAI / Groq / Gemini (63 lines)
    │   └── anthropic.py       Anthropic Claude (79 lines)
    ├── sandbox/
    │   └── local.py           Subprocess sandbox (47 lines)
    ├── memory/
    │   └── filesystem.py      Markdown with YAML frontmatter (64 lines)
    └── search/
        └── tavily.py          Tavily web search (18 lines)
```

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as main.py
    participant CR as core/__init__
    participant Agent as AgentLoop
    participant LLM as LLMProvider
    participant Tools as ToolRegistry
    participant Sbox as Sandbox

    User->>CLI: sarvagya "task"
    CLI->>CR: run(task, model, api_key)
    CR->>CR: create Sandbox, Memory, Registry, LLM
    CR->>Agent: AgentLoop(...).run(task)

    Agent->>Agent: append user message
    loop iteration (max 50)
        Agent->>Agent: build_context()
        Agent->>LLM: complete(messages, tools)
        LLM-->>Agent: LLMResponse

        alt has tool_calls
        Agent->>Tools: execute(name, args)
        Tools->>Sbox: bash / read / etc
        Sbox-->>Tools: result
        Tools-->>Agent: ToolResult
        Agent->>Agent: append to messages, continue
        Agent-->>CR: AgentResult(output)
            CR-->>CLI: result
            CLI-->>User: output
        end
    end
    Agent-->>CR: AgentResult(error="max iterations")
```

## Provider Detection

Provider is inferred from the model name — no config flags needed:

```mermaid
flowchart LR
    MODEL["model name"] --> DETECT{"contains<br/>claude / anthropic?"}
    DETECT -->|yes| AA["AnthropicAdapter<br/>(anthropic SDK)"]
    DETECT -->|no| OA["OpenAIAdapter<br/>(openai SDK)"]

    API["API_KEY"] --> AA & OA
    OBASE["OPENAI_BASE_URL<br/>(optional)"] -.->|"read natively by SDK"| OA
```

| Model pattern | Adapter | SDK |
|---|---|---|
| `claude-*`, `anthropic-*` | AnthropicAdapter | `anthropic` |
| Everything else (`gpt-4o`, `gemini-*`, `llama-*`, etc.) | OpenAIAdapter | `openai` |

Set `OPENAI_BASE_URL` env var for non-default endpoints (Groq, Gemini, Together, etc.).

## Domain Types

All types are `@dataclass` classes in `core/types.py` (62 lines).

```mermaid
classDiagram
    class ToolCall {
        +id: str
        +name: str
        +arguments: dict | str
    }
    class Message {
        +role: str
        +content: str
        +tool_call_id: str | None
        +name: str | None
        +tool_calls: list~ToolCall~ | None
    }
    class ToolDef {
        +name: str
        +description: str
        +parameters: dict
        +required: list~str~
    }
    class LLMResponse {
        +content: str
        +tool_calls: list~ToolCall~ | None
        +stop_reason: str
    }
    class ToolResult {
        +success: bool
        +output: str
        +error: str | None
    }
    class SandboxResult {
        +success: bool
        +output: str
        +error: str | None
    }
    class MemoryEntry {
        +key: str
        +content: str
        +metadata: dict
    }
    class AgentResult {
        +success: bool
        +output: str
        +iterations: int
        +error: str | None
    }
    LLMResponse --> ToolCall
    Message --> ToolCall
```

## Tools Reference

| Tool | Handler | Parameters | Required |
|------|---------|------------|----------|
| **bash** | `sandbox.execute()` | command, timeout, description | command, description |
| **read** | `_read()` | file_path, offset, limit | file_path |
| **write** | `_write()` | file_path, content | file_path, content |
| **edit** | `_edit()` | file_path, old_string, new_string, replace_all | file_path, old_string, new_string |
| **glob** | `handle_glob()` | pattern, path | pattern |
| **grep** | `handle_grep()` | pattern, path, include | pattern |
| **webfetch** | `handle_webfetch()` | url | url |
| **websearch** | `tavily.search()` | query | query |

`websearch` is only available if `TAVILY_API_KEY` is set.

## Design Decisions

| Decision | Choice | Why |
|---|---|---|
| Architecture | Hexagonal (Ports & Adapters) | Zero coupling to any LLM provider |
| Core deps | **Zero external** | `core/` imports only stdlib + local modules |
| Provider detection | Model name heuristic | Swap providers by changing `--model`, not code or config |
| Provider auth | Single `API_KEY` env var | No per-provider key management |
| Sandbox | Local subprocess | Replaceable with E2B cloud sandbox as an adapter |
| Memory | Filesystem markdown | No database needed. Proven pattern (LangManus). |
| Agent loop | Sync, one tool per iteration | Simple, observable, debuggable |
| Prompts | Markdown files | Editable without touching code |
| Every function | ≤30 lines | Enforced by AST check |

## Auth

Set a single `API_KEY` env var (or pass `--api-key`):

```bash
# OpenAI / Groq / any OpenAI-compatible
set API_KEY=sk-...   set MODEL=gpt-4o
set OPENAI_BASE_URL=https://api.groq.com/openai/v1   # if needed

# Anthropic
set API_KEY=sk-ant-...   set MODEL=claude-sonnet-4-20250514

# Or pass inline
sarvagya "task" --model gpt-4o --api-key sk-...
```

## Install

```bash
pip install -e ".[all]"         # all providers
pip install -e ".[openai]"      # OpenAI-compatible only
pip install -e ".[anthropic]"   # Anthropic only
```

## Stats

| Metric | Value |
|--------|-------|
| Python files | 17 |
| Total lines | ~1000 |
| External deps | 3 (all optional) |
| Adapters | 5 |
| Protocols | 4 |
| Tools | 8 |

## License

MIT
