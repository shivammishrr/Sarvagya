# Sarvagya Architecture

Autonomous AI agent. One loop, one action per iteration, filesystem as memory, provider-agnostic.

## Hexagonal Architecture (Ports & Adapters)

```mermaid
flowchart TD
    subgraph main["main.py (Composition Root)"]
        DI[Dependency Injection]
    end

    subgraph core["core/ - Domain"]
        LOOP[AgentLoop]
        TYPES[Domain Types]
        TOOLS[ToolRegistry]
        CTX[Prompt Assembly]
    end

    subgraph ports["ports/ - Interfaces (Protocols)"]
        LLMP[LLMProvider]
        SANDP[Sandbox]
        MEMP[Memory]
    end

    subgraph adapters["adapters/ - Implementations"]
        OA[OpenAIAdapter]
        AA[AnthropicAdapter]
        LS[LocalSandbox]
        FM[FileMemory]
        TV[TavilySearch]
    end

    subgraph external["External Services"]
        GROQ[Groq API<br/>OpenAI-compatible]
        CLAUDE[Anthropic Claude]
        FS[Filesystem]
    end

    DI --> LOOP
    DI --> OA
    DI --> AA
    DI --> LS
    DI --> FM
    DI --> TV

    LOOP -- uses --> LLMP
    LOOP -- uses --> SANDP
    LOOP -- uses --> MEMP

    LLMP -.-> OA
    LLMP -.-> AA
    SANDP -.-> LS
    MEMP -.-> FM

    OA -- HTTP --> GROQ
    AA -- HTTP --> CLAUDE
    LS -- subprocess --> FS
    FM -- read/write --> FS
```

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant M as main.py
    participant L as AgentLoop
    participant P as LLMProvider
    participant T as ToolRegistry
    participant S as Sandbox

    U->>M: task prompt
    M->>L: run(task)
    loop each iteration
        L->>P: complete(messages, tools)
        P-->>L: LLMResponse (content | tool_calls)
        alt has tool_calls
            L->>T: execute(name, args)
            T->>S: run command / read file / etc
            S-->>T: result
            T-->>L: ToolResult
            L->>L: append to context
        else has content
            L-->>M: final answer
            M-->>U: response
        end
    end
```

## Provider Abstraction

```mermaid
classDiagram
    class LLMProvider {
        <<Protocol>>
        +complete(messages, tools) LLMResponse
        +stream(messages, tools) Iterator~LLMChunk~
    }

    class OpenAIAdapter {
        -client: OpenAI
        +complete(messages, tools) LLMResponse
        +stream(messages, tools) Iterator~LLMChunk~
    }

    class AnthropicAdapter {
        -client: Anthropic
        +complete(messages, tools) LLMResponse
        +stream(messages, tools) Iterator~LLMChunk~
    }

    class AgentLoop {
        -llm: LLMProvider
        -sandbox: Sandbox
        -memory: Memory
        -tools: ToolRegistry
        +run(task, max_iterations) AgentResult
    }

    LLMProvider <|.. OpenAIAdapter : implements
    LLMProvider <|.. AnthropicAdapter : implements
    AgentLoop --> LLMProvider : depends on abstraction
```

## Domain Types

```mermaid
classDiagram
    class Message {
        +role: str
        +content: str
        +tool_call_id: str | None
        +name: str | None
    }

    class ToolDef {
        +name: str
        +description: str
        +parameters: dict
        +required: list~str~
    }

    class ToolCall {
        +id: str
        +name: str
        +arguments: dict
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

    LLMResponse --> ToolCall : contains
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Hexagonal (Ports & Adapters) | Zero coupling to LLM providers |
| Language | Python 3.13+ | Latest typing, pattern matching, dataclasses |
| LLM Abstraction | Protocol with adapters | Swap OpenAI/Anthropic/Groq via config |
| Sandbox | Local subprocess + Cloud (future) | Start local, add E2B later |
| Memory | Filesystem (markdown) | Proven pattern, no DB needed |
| Package Manager | uv | Fast, modern Python packaging |
| Linting | ruff | Fast, replaces flake8 + isort |
| Typing | mypy --strict | Bug prevention at compile time |

## File Structure

```
sarvagya/
  __init__.py
  main.py                  # Composition root
  core/
    __init__.py
    types.py               # Shared domain types
    loop.py                # Agent loop (framework-agnostic)
    tools.py               # Tool registry
    context.py             # Prompt assembly
  ports/
    __init__.py
    llm.py                 # LLMProvider protocol
    sandbox.py             # Sandbox protocol
    memory.py              # Memory protocol
    search.py              # WebSearch protocol
  adapters/
    __init__.py
    llm/
      __init__.py
      openai.py            # OpenAI/Groq adapter (OpenAI-compatible)
      anthropic.py         # Anthropic adapter
    sandbox/
      __init__.py
      local.py             # Local subprocess sandbox
    memory/
      __init__.py
      filesystem.py        # Filesystem memory
    search/
      __init__.py
      tavily.py            # Tavily web search
```

## Rules

1. **`core/` imports ZERO external packages.** Only stdlib + local modules.
2. **`ports/` defines only Protocols.** No implementations, no third-party imports.
3. **`adapters/` is the ONLY layer that imports SDKs.** One file per provider.
4. **`main.py` is the ONLY composition root.** Adapters are wired to ports here.
5. **One action per iteration.** Agent calls ONE tool, observes result, repeats.
6. **Filesystem as context.** Session data lives in files, not in-memory.
