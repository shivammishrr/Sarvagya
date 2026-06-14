# Architecture Review — Sarvagya

Review of the existing `main` implementation against current (2026) harness-engineering
philosophy, then a self-review that decides exactly what changes and what does not.

References used to grade the design (framework-agnostic; we study *how production
agents are harnessed*, not bind to any SDK):

- **Harness engineering** — OpenAI "Harness engineering: leveraging Codex in an
  agent-first world"; Jonathan Fulton, "Inside the agent harness: how Codex and
  Claude Code actually work"; Addy Osmani, "Agent Harness Engineering".
  **Core idea:** the harness is *everything that isn't the model* — the loop, the
  tool layer, the context window, the sandbox, the permission model, observability.
  A raw model is not an agent.
- **Context engineering** — Anthropic, "Effective context engineering for AI
  agents"; LangChain, "Context engineering for agents" (the **Write / Select /
  Compress / Isolate** framework). **Core idea:** keeping the *smallest set of
  high-signal tokens* in context each turn.
- **Production agent internals** — Claude Code, Codex, OpenCode, OpenHands, Manus
  (the systems that actually ship). Synthesised in `ANALYSIS.md`.

---

## 1. What the current design gets right

| # | Property | Evidence |
|---|----------|----------|
| 1 | **Hexagonal layering** — `core/` imports zero external packages; only `adapters/` touches SDKs | `grep` of `core/` shows stdlib + local imports only |
| 2 | **Ports as Protocols** — provider swap is a model-name heuristic, no code change | `ports/llm.py` is a `Protocol`; `_make_llm` branches on `claude/anthropic` |
| 3 | **One-action-per-iteration loop** — Manus-style atomicity, observable, debuggable | `loop.py:_handle_response` executes tool calls then returns `None` to re-loop |
| 4 | **Tool result truncation** — first line of defence against context overflow | `MAX_OUTPUT_LEN = 10_000` in `loop.py` |
| 5 | **Sliding-window context** — last 20 turns | `context.py:truncate_messages` |
| 6 | **Markdown system prompt** — editable without code | `prompts/system.md` |
| 7 | **Function-size discipline** — every function ≤ 30 lines (claimed) | enforced by AST check (per ARCHITECTURE.md) |

These map cleanly onto the harness-engineering checklist (loop, tool layer, sandbox,
context management). The bones are good. **Do not rewrite the bones.**

---

## 2. Real defects and gaps (evidence-based)

### BUG-1 — Memory port is dead code (Write/Select strategy broken)
`FileMemory` is constructed and `init_dir("")` is called, and `_get_memory_index()`
reads it into the system prompt — but **no tool exists to let the agent *write* to
memory**. The system prompt even tells the agent: *"Write important findings to
notes.md before they leave context"* — yet there is no `memory_save` / `notes` tool.

This is the "Write" half of the context-engineering framework, unimplemented. The
agent literally cannot obey its own prompt. **Must fix.**

### BUG-2 — `context.py` duplicates the OpenAI message format and does it by hand
`build_context()` hand-builds the OpenAI `tool_calls` wire shape
(`{"id", "type":"function", "function":{...}}`) into the *system message content*
**and** `OpenAIAdapter._convert_messages` builds the same shape again for the real
API. Two sources of truth, drift risk, and the tool schemas are stringified into the
system prompt as JSON for no benefit (the LLM gets the real `tools` array separately).

### BUG-3 — Tool schemas leak into the system prompt
`build_context` appends `## Available Tools` with `json.dumps(t.parameters)` into the
system prompt, *in addition to* passing `tools` to the API. Claude Code / Codex
inject tool *guidance* (when to use) into the prompt, not the raw JSON schema — the
schema is already in the API call. This is prompt bloat for zero signal.

### BUG-4 — `truncate_messages` is naive and corrupts tool-call pairing
It keeps the **last 20 messages by count**. Tool-result messages must be paired with
their preceding assistant `tool_calls` message; a blind slice can orphan a `tool`
message from its `tool_call_id`, which OpenAI/Anthropic **reject** with a 400.
Count-based truncation also silently drops the original user task as the window
slides. The harness-engineering literature (Anthropic, OpenHands) is unanimous:
truncation must preserve message-pair integrity and pin the root task.

### BUG-5 — `_call_llm` round-trips `list[dict]` → `Message` for nothing
`AgentLoop._step` calls `build_context` which returns `list[dict]`, then `_call_llm`
converts those dicts *back* into `Message` dataclasses to call `llm.complete`. The
adapters then convert `Message` *back* to dicts. Three conversions, one logical step.
The `Message` dataclass exists precisely so the loop stays in its own types.

### BUG-6 — `webfetch`/`grep`/`glob` open the world
- `webfetch` follows any URL with a 30s timeout and returns raw bytes (HTML, binary…)
  into context — no size cap, no HTML→text.
- `grep` walks the whole tree including `node_modules`/`.git` on a huge repo →
  catastrophic output. Needs path scoping and the same 10k cap.

### BUG-7 — No tests
`git ls-files` shows zero test files. For a harness, where the loop logic is the
entire value, this is the highest-risk gap. The `ToolRegistry`, `truncate_messages`,
`_handle_response` control flow, and the memory adapter all have logic that silently
breaks (see BUG-4).

### BUG-8 — `subprocess.run(..., shell=True)` on Windows
`LocalSandbox.execute` uses `shell=True` with an arbitrary command string. On the
agent's own machine that is the contract (it's a *local* sandbox), but the timeout is
`timeout / 1000` ms→s and there is no output-size guard, so a `cat huge.log` fills
context. Minor, but the truncation belongs at the source.

### BUG-9 — `read` tool `limit=None` echoed into the JSON schema
`file_ops.py` sets `"default": None` and `limit` is `int`. JSON Schema with
`"default": null` on an integer field is invalid per OpenAI's strict mode. Will break
when `strict=True` tool calling is used.

---

## 3. What is intentionally NOT changing (YAGNI)

Applying the lazy-senior-dev ladder to every "could add":

- **No DAG/orchestrator.** None of the production harnesses use one; the loop decides
  the next action. (ANALYSIS.md anti-pattern #1.)
- **No event sourcing.** OpenHands' append-only EventLog is beautiful and we are not
  building it: a `list[Message]` is enough at this scale.
- **No plugin marketplace / MCP server.** Out of scope; adding a second tool is one
  `registry.register(...)` call.
- **No async.** The loop is sync and one-tool-per-turn; async adds complexity the
  harness does not need yet.
- **No streaming.** Adds a whole second code path through every adapter for marginal
  benefit in a CLI that returns a final answer.
- **No vector memory / embeddings.** Filesystem markdown + frontmatter is the proven
  pattern (Claude Code `MEMORY.md`, Codex `.codex/memories`, Manus files). Search is
  O(n) over a handful of notes — fine.
- **No new dependencies.** The fix uses stdlib only.

---

## 4. Change set (what this branch actually does)

Driven entirely by §2. Smallest diff that closes the real gaps:

| Change | Fixes | Files |
|--------|-------|-------|
| Add `memory_save` + `memory_load` tools wired to the existing `Memory` port | BUG-1 | `core/tools/memory_ops.py`, `core/tools/__init__.py` |
| Drop tool-schema injection from the system prompt; keep one-line guidance only | BUG-2, BUG-3 | `core/context.py` |
| Pair-aware, root-task-preserving truncation | BUG-4 | `core/context.py` |
| Loop stays in `Message`; `build_context` returns `list[Message]` + system `str` | BUG-5 | `core/loop.py`, `core/context.py`, ports |
| Cap `webfetch`/`grep`/`glob` output; HTML→text for webfetch | BUG-6 | `core/tools/web.py`, `core/tools/search_ops.py` |
| Add a real test suite (registry, context pairing, loop control flow, memory, sandbox) | BUG-7 | `tests/` |
| Sandbox output cap + Windows-safe command handling | BUG-8 | `adapters/sandbox/local.py` |
| Fix `read` schema (`limit` has no `null` default) | BUG-9 | `core/tools/file_ops.py` |

**Line budget:** stay near the current ~1000. The additions (memory tools, pair-aware
truncation, tests) are offset by deleting the duplicated message-conversion and the
schema-in-prompt bloat.

---

## 5. Self-review (the lazy-senior check)

> Would I delete any of the above before merging? Run each change against the ladder.

- **memory tools** — does it need to exist? **Yes**, the agent's own prompt demands it
  and it is the missing "Write" strategy. Not speculative. Keep.
- **pair-aware truncation** — stdlib does this? No. Native? No. Is it one line? No.
  Minimum code that works: ~15 lines. Keep, and it is tested (BUG-4 is a live crash).
- **HTML→text in webfetch** — stdlib `html.parser` does it in ~20 lines, no dep. This
  is rung 2 of the ladder. Keep.
- **drop schema-from-prompt** — this is *deletion*. Deletion always wins. Keep.
- **loop stays in Message** — deletion of two conversions. Keep.
- **tests** — non-trivial logic leaves one runnable check behind. The ponytail minimum.
  Keep.

Nothing to cut. **Approved.** Proceeding to HLD/LLD.

---

## 6. Verdict

The architecture (hexagonal, ports, one-action loop) is sound and matches production
harness practice. The defects are concentrated in **context management** (the part of
harness engineering that matters most in 2026) and **missing test coverage**. The
change set is surgical: it activates a dead port, fixes a live crash in truncation,
removes duplicated wire-format logic, and adds the safety net the loop deserves. No
rewrite, no new dependencies, no speculative abstraction.
