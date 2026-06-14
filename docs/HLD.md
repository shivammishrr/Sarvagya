# HLD — High Level Design

Sarvagya: a framework-agnostic **agent harness**. The harness is everything that is
not the model — the loop, the tool layer, the context window, the sandbox, the
permission surface. A raw model is not an agent; the harness turns it into one.

Design philosophy: **hexagonal (Ports & Adapters)**, **one action per iteration**
(Manus atomicity), and **the smallest set of high-signal tokens per turn**
(Anthropic context engineering — *Write / Select / Compress / Isolate*).

---

## 1. Layered architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CLI  (main.py)        — argparse, env, composition root      │
├─────────────────────────────────────────────────────────────┤
│  ADAPTERS  (adapters/*) — the ONLY layer that imports SDKs   │
│    llm/{openai,anthropic} · sandbox/local · memory/filesystem│
│    search/tavily                                              │
├─────────────────────────────────────────────────────────────┤
│  PORTS  (ports/*) — Protocols, zero implementations           │
│    LLMProvider · Sandbox · Memory · WebSearch                 │
├─────────────────────────────────────────────────────────────┤
│  CORE / DOMAIN  (core/*) — ZERO external imports              │
│    AgentLoop · ContextBuilder · ToolRegistry · Tools · Types  │
└─────────────────────────────────────────────────────────────┘
        │                                  │
        ▼                                  ▼
   External Services               External Storage
   LLM APIs (OpenAI/               Local filesystem
   Anthropic/Groq/Gemini)          (sandbox + memory)
```

**Layer rule (enforced):** dependency direction is always downward. `core/` imports
only stdlib + its own modules. `ports/` declares Protocols only. `adapters/` is the
sole import site for `openai`, `anthropic`, `tavily`. Provider swap = model-name
heuristic in the composition root, no code change.

## 2. The agent loop (the heart of the harness)

One action per iteration. Think → call one tool → observe → repeat. Atomic, observable,
debuggable — the property every production harness (Manus, Claude Code, Codex) shares.

```
run(task)
  └─ messages = [Message(user, task)]            # root task pinned, never truncated
     for i in range(max_iterations):
       ctx = build_context(messages, tools, env)  # SELECT: system + window + memory
       resp = llm.complete(ctx)                   # LLM call
       if resp.tool_calls:                        # ACT
            append assistant(tool_calls)
            for tc: append tool(execute(tc))      # one tool, result capped
            continue                              # → next iteration
       if resp.content:                           # DONE
            return AgentResult(success, content)
     return AgentResult(error="max iterations")
```

Why one-action-per-turn and not parallel: each action is an observable, interruptible
unit; the agent sees the result of one action before committing to the next. (Manus
strictness; see ANALYSIS.md §2.1.) Parallelism is a future rung, added only when a
profiler says the latency hurts.

## 3. Context engineering — Write / Select / Compress / Isolate

This is where the 2026 harness literature concentrates, and where Sarvagya invests.

| Strategy | Sarvagya mechanism | Detail |
|----------|--------------------|--------|
| **Write** | `memory_save` / `memory_load` tools → `Memory` port → markdown + YAML frontmatter | Agent persists findings to named notes before they leave context. Claude Code `MEMORY.md` / Manus-filesystem pattern. |
| **Select** | `build_context` assembles: frozen system prompt + env + memory index + paired message window | Only the high-signal slice of history reaches the model. Tool *guidance* (one line each) in prompt; raw schemas go via the API `tools` param, never duplicated into the prompt. |
| **Compress** | Tool-result cap (10k), webfetch HTML→text + cap, sandbox output cap, pair-aware sliding window | Truncation preserves `tool`↔`tool_calls` pairing and **pins the root user task** so the agent never forgets what it was asked. |
| **Isolate** | (future) sub-agent factory — clone with a focused prompt, separate message list | Not built this pass; the loop is single-context by design. The seam (`AgentLoop` is instantiable) leaves the door open. |

## 4. Tool subsystem

Tools are `ToolDef` (name, description, JSON-schema parameters, required) + a handler
`dict -> ToolResult`. The registry is the single point of registration, schema
generation (OpenAI/Anthropic wire format), and dispatch. Adding a tool is one
`registry.register(ToolDef(...), handler)` — no decorator, no metaclass, no plugin
loader. Lazy by construction.

Built-ins: `bash`, `read`, `write`, `edit`, `glob`, `grep`, `webfetch`, `websearch`
(conditional on `TAVILY_API_KEY`), and — new — `memory_save`, `memory_load`.

## 5. Provider model

Provider detected from the model name (`claude*`/`anthropic*` → Anthropic adapter;
everything else → OpenAI adapter, with `OPENAI_BASE_URL` for Groq/Gemini/etc.).
A single `API_KEY` env var. Adding a provider = one new file in `adapters/llm/`
implementing `LLMProvider`. Zero core changes.

## 6. Non-functional goals

| Goal | Approach |
|------|----------|
| **Provider-agnostic** | Ports; SDK coupling confined to adapters |
| **Tiny core** | ~1000 lines, every function ≤ 30 lines |
| **Zero required deps** | `dependencies = []`; `openai`/`anthropic`/`tavily` optional extras |
| **Observable** | One-action loop + `AgentResult{iterations}` + memory files on disk |
| **Testable** | Domain logic depends only on Protocols; fakes injected in tests |
| **Safe defaults** | Output caps everywhere context is built; sandbox is local subprocess |

## 7. Out of scope (explicit YAGNI)

DAG orchestrator · event sourcing · plugin marketplace / MCP server · async loop ·
streaming · vector/embedding memory · web UI. Each is a deliberate non-decision
documented in `docs/REVIEW.md §3`.
