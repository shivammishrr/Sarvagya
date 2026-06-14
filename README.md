# Sarvagya

Autonomous AI agent. Takes a task, uses an LLM to decide actions, executes them, returns results. ~1000 lines.

```bash
pip install -e ".[all]"
set API_KEY=sk-...   set MODEL=gpt-4o
sarvagya "List all Python files in this project"
```

---

## Architecture

```mermaid
flowchart LR
    subgraph User[" "]
        U(["You"]):::user
    end

    subgraph System["Sarvagya"]
        CLI["CLI"]:::component
        CORE["Agent Core<br/>think → tool → observe"]:::core
        LLM["LLM<br/>decides next action"]:::llm
        SBOX["Sandbox<br/>shell commands"]:::tool
        MEM["Memory<br/>markdown files"]:::tool
        SEARCH["Web Search<br/>optional"]:::tool
    end

    subgraph External[" "]
        EXT_LLM["OpenAI / Groq /<br/>Gemini / Claude"]:::external
        EXT_FS["Filesystem"]:::external
        EXT_WEB["Tavily API"]:::external
    end

    U -->|"task"| CLI
    CLI --> CORE
    CORE <-->|"asks"| LLM
    LLM --> EXT_LLM
    CORE -->|"runs"| SBOX
    CORE -->|"stores"| MEM
    CORE -.->|"optional"| SEARCH
    SBOX --> EXT_FS
    MEM --> EXT_FS
    SEARCH --> EXT_WEB
    CORE -->|"final answer"| U

    classDef user fill:#1a3a2a,stroke:#3fb950,stroke-width:2px,color:#e6edf3
    classDef component fill:#1a3a5f,stroke:#58a6ff,stroke-width:2px,color:#e6edf3
    classDef core fill:#1a1525,stroke:#bc8cff,stroke-width:2px,color:#e6edf3
    classDef llm fill:#2a1a3a,stroke:#d29922,stroke-width:2px,color:#e6edf3
    classDef tool fill:#1c2333,stroke:#39d2c0,stroke-width:2px,color:#e6edf3
    classDef external fill:#1a150d,stroke:#8b949e,stroke-width:2px,color:#8b949e
```

**What it is:** An autonomous AI agent. You give it a task, it asks an LLM what to do, runs the tool, observes the result, asks again, repeats until it has a final answer.

**How it works:** `You → CLI → Core ↔ LLM → runs Sandbox/Memory/Search → loops back → final answer`

**Components:** CLI (accepts task), Agent Core (orchestrates), LLM (decides), Sandbox (executes commands), Memory (stores notes), Web Search (optional)

**Externals:** LLM APIs (OpenAI, Groq, Gemini, Claude), Filesystem, Tavily (optional)

**Tech:** Python 3.13 · OpenAI SDK · Anthropic SDK · hexagonal pattern · markdown files

## Implementation Details

### Agent Loop

```mermaid
flowchart TD
    START(["run(task)"]) --> APPEND["append user message"]
    APPEND --> STEP{"_step()"}
    STEP --> BUILD["build_context()"]
    BUILD --> LLM_CALL["LLM.complete()"]
    LLM_CALL --> CHECK{"response"}
    CHECK -->|"exception"| FAIL["return error"]
    CHECK -->|"tool_calls"| EXEC["for each:<br/>ToolRegistry.execute()"]
    CHECK -->|"content"| SUCCESS["return final answer"]
    EXEC --> STEP
    FAIL --> DONE
    SUCCESS --> DONE
```

### File Structure

```
sarvagya/
├── main.py                    CLI entry point
├── prompts/
│   └── system.md              System prompt (markdown)
├── core/
│   ├── __init__.py            Wiring + _make_llm() + run()
│   ├── types.py               ToolCall, Message, ToolDef, etc.
│   ├── loop.py                AgentLoop class
│   ├── context.py             build_context(), truncate_messages()
│   ├── tool_registry.py       ToolRegistry class
│   └── tools/
│       ├── __init__.py        init_tools()
│       ├── bash.py            make_handler() → sandbox.execute()
│       ├── file_ops.py        _read(), _write(), _edit()
│       ├── search_ops.py      handle_glob(), handle_grep()
│       └── web.py             handle_webfetch()
├── ports/
│   ├── llm.py                 LLMProvider protocol
│   ├── sandbox.py             Sandbox protocol
│   ├── memory.py              Memory protocol
│   └── search.py              WebSearch protocol
└── adapters/
    ├── llm/
    │   ├── openai.py          OpenAIAdapter
    │   └── anthropic.py       AnthropicAdapter
    ├── sandbox/
    │   └── local.py           LocalSandbox
    ├── memory/
    │   └── filesystem.py      FileMemory
    └── search/
        └── tavily.py          TavilySearch
```

### Data Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant CR as core/__init__
    participant Agent as AgentLoop
    participant LLM
    participant Tools as ToolRegistry
    participant Sbox as Sandbox

    User->>CLI: sarvagya "task"
    CLI->>CR: run(task)
    CR->>CR: create dependencies
    CR->>Agent: AgentLoop(...).run(task)
    Agent->>Agent: append user message
    loop iteration (max 50)
        Agent->>Agent: build_context()
        Agent->>LLM: complete(messages, tools)
        LLM-->>Agent: response
        alt has tool_calls
            Agent->>Tools: execute(name, args)
            Tools->>Sbox: run command
            Sbox-->>Tools: result
            Tools-->>Agent: ToolResult
            Agent->>Agent: append result
        else has content
            Agent-->>CR: final answer
            CR-->>CLI: output
            CLI-->>User: result
        end
    end
    Agent-->>CR: max iterations error
```

### Domain Types

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

### Tools Reference

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

`websearch` only available if `TAVILY_API_KEY` is set.

## Design Decisions

| Decision | Choice | Why |
|---|---|---|
| Architecture | Hexagonal (Ports & Adapters) | Zero coupling to any LLM provider |
| Core deps | **Zero external** | `core/` imports only stdlib |
| Provider detection | Model name heuristic | Swap by changing `--model` |
| Provider auth | Single `API_KEY` | One env var for any provider |
| Sandbox | Local subprocess | Replaceable with cloud sandbox |
| Memory | Filesystem markdown | No database needed |
| Agent loop | Sync, one tool per iteration | Simple, observable |
| Prompts | Markdown files | Editable without code changes |
| Functions | ≤30 lines | Enforced by AST check |

## Auth

```bash
set API_KEY=sk-...   set MODEL=gpt-4o
set OPENAI_BASE_URL=https://api.groq.com/openai/v1   # if needed

# or inline
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
