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

### Architecture Layers (Hexagonal / Ports & Adapters)

```mermaid
flowchart TB
    subgraph User["User / CLI"]
        CLI["CLI Entry"]
        CR["Composition Root"]
    end

    subgraph Core["Domain Layer — zero external deps"]
        LOOP["Agent Loop<br/>think → tool → observe"]
        TYPES["Domain Types"]
        CTX["Context Builder"]
        REG["Tool Registry"]
        TOOLS["Built-in Tools<br/>bash · file_ops · search · web"]
    end

    subgraph Ports["Port Layer — Protocols"]
        P_LLM["LLM Provider"]
        P_SBOX["Sandbox"]
        P_MEM["Memory"]
        P_SRCH["Web Search"]
    end

    subgraph Adapters["Adapter Layer — SDK implementations"]
        A_LLM["OpenAI Adapter<br/>Anthropic Adapter"]
        A_SBOX["Local Sandbox"]
        A_MEM["File Memory"]
        A_SRCH["Tavily Search"]
    end

    subgraph External["External Services"]
        EXT_LLM["LLM APIs<br/>OpenAI · Groq · Gemini · Claude"]
        EXT_FS["Filesystem"]
    end

    CLI --> CR
    CR --> LOOP & REG & TOOLS
    CR --> A_LLM & A_SBOX & A_MEM & A_SRCH

    LOOP --> P_LLM & P_SBOX & P_MEM
    LOOP --> CTX & REG
    TOOLS --> REG
    CTX --> TYPES

    P_LLM -.->|implements| A_LLM
    P_SBOX -.->|implements| A_SBOX
    P_MEM -.->|implements| A_MEM
    P_SRCH -.->|implements| A_SRCH

    A_LLM -->|HTTP| EXT_LLM
    A_SBOX -->|subprocess| EXT_FS
    A_MEM -->|read/write| EXT_FS
```

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
├── main.py                    CLI entry + DI
├── prompts/
│   └── system.md              Agent identity & rules
├── core/                      Zero external dependencies
│   ├── __init__.py            Composition root
│   ├── types.py               8 dataclasses
│   ├── loop.py                AgentLoop
│   ├── context.py             Prompt assembly
│   ├── tool_registry.py       Register + dispatch
│   └── tools/
│       ├── bash.py            Shell execution
│       ├── file_ops.py        Read/write/edit
│       ├── search_ops.py      Glob/grep
│       └── web.py             Web fetch
├── ports/                     Protocols only
│   ├── llm.py                 LLMProvider
│   ├── sandbox.py             Sandbox
│   ├── memory.py              Memory
│   └── search.py              WebSearch
└── adapters/                  SDK implementations
    ├── llm/
    │   ├── openai.py          OpenAI/Groq/Gemini
    │   └── anthropic.py       Anthropic Claude
    ├── sandbox/
    │   └── local.py           Subprocess
    ├── memory/
    │   └── filesystem.py      Markdown files
    └── search/
        └── tavily.py          Tavily search
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
