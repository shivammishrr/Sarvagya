# Deep Analysis of AI Agent System Prompts & Architectures

## How They Write Prompts, Design Tools, Call Tools, and Architect Their Agents

---

# Part 1: Prompt Engineering Patterns

## 1.1 Identity Section Design

Every production agent system begins with a crisp, one-line identity statement. This is universal across ALL systems analyzed.

### Identity Statement Patterns

| System | Identity | Pattern |
|--------|----------|---------|
| **Claude Code** | "You are Claude Code, Anthropic's official CLI for Claude." | Product + Company + Role |
| **Codex (GPT-5.5)** | "You are Codex, a coding agent based on GPT-5." | Name + Type + Model |
| **Devin** | "You are Devin, a software engineer using a real computer operating system." | Name + Role + Environment |
| **Manus** | "You are Manus, an AI agent created by the Manus team." | Name + Creator |
| **OpenCode** | "I am opencode, an interactive CLI agent specializing in software engineering tasks." | Name + Type + Specialty |
| **Cursor** | "You are an AI coding assistant, powered by {model_name}." | Generic + Model |
| **v0** | "You are v0, Vercel's highly skilled AI-powered assistant that always follows best practices." | Name + Company + Skill |
| **Replit** | "You are an AI programming assistant called Replit Assistant." | Generic + Name |

**Key observation**: None of these use long philosophical descriptions. They state name, what they are, and optionally who made them. The identity is always the FIRST sentence.

### Capabilities Section (Manus Pattern)

Manus uses a numbered list of 6 capabilities at the very top:
```
You excel at the following tasks:
1. Information gathering, fact-checking, and documentation
2. Data processing, analysis, and visualization
3. Writing multi-chapter articles and in-depth research reports
4. Creating websites, applications, and tools
5. Using programming to solve various problems beyond development
6. Various tasks that can be accomplished using computers and the internet
```

**Key insight**: This sets the agent's self-image and scope. It prevents the agent from saying "I can't do that" for in-scope tasks and prevents it from trying out-of-scope tasks. Claude Code doesn't need this because its scope is obvious (software engineering), but Manus needs it because its scope is broad.

### System Capability Block (Manus Pattern)

After identity, Manus adds explicit system capabilities in a structured block:
```
<system_capability>
- Communicate with users through message tools
- Access a Linux sandbox environment with internet connection
- Use shell, text editor, browser, and other software
- Write and run code in Python and various programming languages
- Independently install required software packages and dependencies via shell
- Deploy websites or applications and provide public access
...
</system_capability>
```

**Key insight**: This tells the agent WHAT it can do at a high level, separate from tools. Tools define HOW, capabilities define WHAT. This helps the agent plan at a higher level of abstraction.

## 1.2 Behavior Rules: Common Patterns Across All Systems

All 8 systems analyzed share a CORE SET of rules that appear in every prompt:

### Universal Rules

| Rule | Present In |
|------|-----------|
| Prefer dedicated tools over shell commands for file ops | Claude Code, Codex, Cursor, Devin, OpenCode, v0, Manus |
| Read before edit | ALL |
| No emojis (unless user asks) | Claude Code, Codex, Cursor, OpenCode |
| Be concise, short responses | Claude Code, Codex, Cursor, OpenCode, v0 |
| Parallelize independent tool calls | Claude Code, Codex, Cursor, Devin, OpenCode |
| Reference code as file:line_number | Claude Code, Cursor, OpenCode |
| Don't add comments unless non-obvious | Claude Code, Codex, Devin, OpenCode |
| Never expose secrets | ALL |
| Prefer edit over create for existing files | Claude Code, Codex, OpenCode, v0 |
| Don't add features beyond what was asked | Claude Code, OpenCode |
| Security best practices (no injection, etc.) | Claude Code, Devin, OpenCode, v0 |

### Unique Rules by System

| System | Unique Rule |
|--------|-------------|
| **Claude Code** | "__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__" marker for prompt caching |
| **Claude Code** | Surface adjacent bugs you spot, be a collaborator not executor |
| **Codex** | "Assume they want you to make the change, don't stop at a plan" |
| **Codex** | Never talk about goblins, gremlins, raccoons (specific anti-hallucination) |
| **Devin** | Report environment issues instead of trying to fix them |
| **Devin** | Never modify tests unless explicitly asked |
| **Manus** | One tool call per iteration (strictly enforced) |
| **Manus** | Save intermediate results to files, don't output them |
| **Manus** | Information priority: datasource API > web search > model knowledge |
| **v0** | Always use Supabase as default database |
| **v0** | Never use localStorage for persistence |
| **Cursor** | "Never use tools like Shell or code comments as means to communicate" |
| **OpenCode** | "Construct the full absolute path for the file_path argument" |
| **Replit** | "You MUST focus on the user's request" |

## 1.3 Prompt Assembly Architecture (from Claude Code)

Claude Code has the most sophisticated prompt assembly system. Here is the exact architecture:

```
getSystemPrompt()  (in prompts.ts)
    │
    │   STATIC PREFIX (globally cached, identical across sessions)
    │   ├── getSimpleIntroSection()          ── Identity + Cyber Risk
    │   ├── getSimpleSystemSection()         ── Permission modes, hooks, reminders
    │   ├── getSimpleDoingTasksSection()     ── Code style, security, error handling
    │   ├── getActionsSection()              ── Reversibility, blast radius
    │   ├── getUsingYourToolsSection()       ── Tool preferences, parallel calls
    │   ├── getSimpleToneAndStyleSection()   ── No emojis, concise references
    │   ├── getOutputEfficiencySection()     ── Inverted pyramid communication
    │   │
    │   │   __SYSTEM_PROMPT_DYNAMIC_BOUNDARY__   ← CRITICAL CACHING BOUNDARY
    │   │
    │   DYNAMIC SUFFIX (session-specific, regenerated each session)
    │   ├── getSessionSpecificGuidanceSection()  ── Agent tools, skills, verification
    │   ├── loadMemoryPrompt()                   ── MEMORY.md content
    │   ├── getAntModelOverrideSection()         ── Internal model overrides
    │   ├── computeSimpleEnvInfo()               ── CWD, OS, git state, model info
    │   ├── getLanguageSection()                 ── Language preferences
    │   ├── getOutputStyleSection()              ── Custom output styles
    │   ├── getMcpInstructionsSection()          ── MCP server instructions
    │   ├── getScratchpadInstructions()          ── Temp file directory
    │   ├── getFunctionResultClearingSection()   ── Context window management
    │   └── SUMMARIZE_TOOL_RESULTS_SECTION       ── Persist important information
```

### The Caching Boundary Pattern

The `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` marker is CRITICAL. In Anthropic's API:

- **Above the boundary**: `cache_control: { "type": "ephemeral" }` with `scope: "global"`
- **Below the boundary**: Session-specific, NOT cached globally

This means:
- The identity, behavior rules, tool usage guidance, tone/style, and output efficiency sections are cached ONCE and reused across ALL sessions
- Only the environment info, memory, MCP instructions, and scratchpad path change per session
- **50-80% cost savings** on API calls

### Section Builder Pattern

Each `get*Section()` function returns a string. They are simple concatenation builders, not template engines. Example from Claude Code:

```typescript
function getSimpleIntroSection(cyberRiskInstruction: string): string {
  return `You are Claude Code, Anthropic's official CLI for Claude.\n\nIMPORTANT: ${cyberRiskInstruction}\n\nIMPORTANT: You must NEVER generate or guess URLs...`
}
```

**Key insight**: Each section is a function that takes optional parameters (feature flags, config) and returns a string. This makes sections testable, composable, and feature-flagged.

## 1.4 Compression / Context Management Patterns

### Claude Code Pattern
```
"Old tool results will be automatically cleared from context to free up space."
"Write down any important information you might need later in your response, 
 as the original tool result may be cleared later."
```

The agent is explicitly told that tool results will be pruned (keep N most recent) and is instructed to persist important info in its response text.

### Codex Pattern
```
"When you run out of context, the tool automatically compacts the conversation. 
 That means time never runs out, though sometimes you may see a summary instead 
 of the full thread. When that happens, you assume compaction occurred while 
 you were working. Do not restart from scratch."
```

Codex tells the agent compaction happens transparently and the agent should continue naturally from the summary.

### OpenCode Pattern (most sophisticated)
Uses a **hidden compaction sub-agent** that:
1. Selects entries to keep (most recent N tokens)
2. Builds a structured summary prompt with template sections: Goal, Constraints & Preferences, Progress, Key Decisions, Next Steps, Critical Context, Relevant Files
3. Calls a separate LLM to summarize the "head" (old entries)
4. Stores compaction as `SessionMessage.Compaction` type messages
5. On history load, uses `latestCompaction` to filter what's included in context

**Key insight**: The summary template has explicit sections that mirror how an engineer thinks about a project. This structure ensures the summary is actually useful for continuing work.

### OpenHands Pattern (EventStream + Condenser)
- `CondensationRequest` event signals the system to run the condenser
- `Condensation` event records which events were forgotten and an optional summary
- `RollingCondenser` family: keeps a rolling window, summarizes old events with LLM
- `PipelineCondenser`: chains multiple condensers for different strategies
- View is lazily constructed from events; condensation is applied during view construction
- `ManipulationIndices` enforce structural properties (role alternation, tool call pairing)

### Manus Pattern
Manus doesn't use compression in the same way. Instead:
- Uses **filesystem as context** (todo.md, progress.md, notes.md on disk)
- References files by path, reads content on demand
- The event stream may be "truncated or partially omitted" by the system
- Agent is told to "save intermediate results to files"

## 1.5 Ephemeral Guidance Pattern (from Replit / Decision-Time Guidance)

**This is a key innovation** from Replit's blog (decision-time guidance).

The pattern:
1. A small, fast classifier LLM runs EVERY iteration
2. It analyzes the last error + tool result
3. Injects 1-2 sentences of micro-instructions for THIS TURN ONLY
4. The guidance does NOT persist in context
5. Does NOT break the KV cache (frozen system prompt)

This enables:
- Hundreds of situational hints without prompt bloat
- Dynamic error recovery ("that npm command failed, try --legacy-peer-deps")
- Context-specific advice without bloating the system prompt
- The classifier can use a much cheaper/faster model than the main agent

**Not found in any other system's leaked prompts**, but described in Replit's engineering blog. This is likely a competitive advantage.

---

# Part 2: Agent Architecture Patterns

## 2.1 The Simple Loop (Manus)

```
while budget_remaining:
    1. Analyze Events (understand user needs + latest state)
    2. Select ONE tool call
    3. Wait for Execution (sandbox executes, observation added to event stream)
    4. Iterate (repeat until task completion)
    5. Submit Results (message user with deliverables)
    6. Enter Standby (idle, wait for new tasks)
```

**Properties**:
- Exactly ONE tool call per iteration
- Event stream is the single source of truth (messages, actions, observations, plans, knowledge, datasource)
- Modules (Planner, Knowledge, Datasource) inject events into the stream
- Agent reads the stream to understand state, not function calls
- Filesystem is used for persistence (todo.md for progress, files for results)

## 2.2 The Think→Act Pattern (OpenManus)

```
BaseAgent.run(request)
    Loop while steps < max_steps AND state != FINISHED:
        ReActAgent.step()
            ToolCallAgent.think()
                - Append next_step_prompt as user message
                - Call LLM with tool definitions
                - Parse response: extract tool_calls
                - Return whether action is needed
            ToolCallAgent.act()
                - For each tool_call:
                    execute_tool(command)
                        - Validate tool exists in tool_map
                        - Parse JSON args
                        - tool(**args)
                        - Handle special tools (terminate → FINISHED)
                    Add tool result as message
        Check is_stuck() → handle_stuck_state()
    Cleanup
```

**Inheritance chain**: `BaseAgent → ReActAgent → ToolCallAgent → Manus`

Each layer adds:
- **BaseAgent**: State machine (IDLE/RUNNING/FINISHED/ERROR), memory, run loop, stuck detection
- **ReActAgent**: think/act separation, step() orchestrates the two
- **ToolCallAgent**: LLM tool calling, tool execution, special tool handling
- **Manus**: Tool composition (PythonExecute, BrowserUseTool, StrReplaceEditor, etc.), MCP integration, browser context awareness

**Key insight**: The inheritance chain is clean but CRITICAL. Each layer adds ONE responsibility. The separation of think/act allows intercepting/modifying the thought process at each layer.

## 2.3 The EventStream Architecture (OpenHands)

```
Event (ABC) ──── Frozen, UUID id, ISO timestamp, source
    ├── LLMConvertibleEvent (ABC) ── Can be converted to LLM Message
    │    ├── ActionEvent (tool calls)
    │    ├── MessageEvent (user/assistant messages)
    │    ├── ObservationEvent (tool results)
    │    ├── SystemPromptEvent
    │    ├── AgentErrorEvent
    │    ├── StreamingDeltaEvent
    │    ├── CondensationSummaryEvent
    │    └── 15+ types...
    ├── Condensation (forgotten events + summary)
    ├── CondensationRequest (signal to run condenser)
    ├── ConversationStateUpdateEvent
    ├── PauseEvent / InterruptEvent
    └── TokenEvent
```

**Flow**:
```
send_message()
    → MessageEvent appended to EventLog
    → agent.execute(state)
        → agent.execute_turn()
            → view = state.view (lazily built from events)
            → LLM responds with tool calls
            → ActionEvent(s) appended to EventLog
            → security_analyzer.security_risk(action)
            → if safe: execute tool → ObservationEvent appended
            → if risky: WAITING_FOR_CONFIRMATION
```

**Critical insight**: EVERYTHING is an event. The append-only event log serves as:
- Source of truth for ALL state
- Persistence mechanism (file-per-event on disk)
- LLM context (via lazy View construction)
- Replay source for debugging
- Audit trail for security

**Security architecture**: Multi-layer:
1. Action-level risk prediction (LLM self-assesses)
2. Security analyzer (runtime analysis, e.g., bash AST parsing)
3. Confirmation policies (AlwaysConfirm / NeverConfirm / ConfirmRisky)
4. Hook system (pre/post tool execution)
5. Encryption for persisted secrets

## 2.4 The Effect-ts Layered Architecture (OpenCode)

```
SessionRunner.run(sessionID)
    → runTurn(sessionID, promotion) in bounded loop (MAX_STEPS=25)
        → loadSession() → selectAgent() → resolveModel()
        → loadHistory() → materializeTools() → buildLLMRequest()
        → llm.stream(request) → persistEvents → executeLocalTools
        → checkContinuation → return needsContinuation
```

**Tool definition (Effect-TS pattern)**:
```typescript
Tool.make({
    description: "...",
    input: Schema,     // Effect Schema → JSON Schema
    output: Schema,    // Effect Schema → JSON Schema
    execute: (input, context) => Effect<Type<Output>, ToolFailure>,
})
```

**Key architectural patterns**:
1. **Effect-TS everywhere**: Services as `Context.TaggedService`, dependencies via `Layer` composition
2. **Event sourcing**: All state changes are events (published + persisted)
3. **CQRS**: Write path (EventV2.publish) separated from read path (SessionStore reads projected tables)
4. **Permission as tool filtering**: If a tool's action is denied for all resources, it's removed from the tool definitions sent to the LLM (not hidden with logit masking)
5. **Location-scoped vs global services**: Multiple concurrent sessions in different directories
6. **Tool persistence**: Tool output stored with truncation (2000 lines / 50KB, spill-to-file)

## 2.5 The Multi-Surface Architecture (Claude Code)

Claude Code uses a **coordinator mode** for multi-worker orchestration:

```
Coordinator (you) ←→ Workers (spawned via Agent tool)
    │                        │
    │── spawn research ─────→│ (parallel, read-only)
    │←─── findings ──────────│
    │                        │
    │── synthesize ────      │
    │── spawn implementation →│ (focused, write)
    │←─── changes ──────────│
    │                        │
    │── spawn verification ─→│ (fresh eyes, adversarial)
    │←─── verdict ──────────│
```

**Key insight about worker prompt writing**:
```
// ANTI-PATTERN (bad):
Agent({ prompt: "Based on your findings, fix the auth bug" })

// GOOD:
Agent({ prompt: "Fix the null pointer in src/auth/validate.ts:42. The user field
  on Session (src/auth/types.ts:15) is undefined when sessions expire but the token
  remains cached. Add a null check before user.id access — if null, return 401 with
  'Session expired'. Commit and report the hash." })
```

The coordinator MUST synthesize findings into specific, actionable prompts. Workers cannot see the coordinator's conversation. Every prompt must be self-contained.

**Sub-agent lifecycle**: Spawn → work → notify coordinator via `<task-notification>` → coordinator reads result → spawn fresh OR continue via SendMessage

## 2.6 The Proactive / Autonomous Mode (Claude Code)

Feature-flagged mode (`PROACTIVE` or `KAIROS` flags):

```
You are running autonomously. You will receive <tick> prompts that keep you alive.
    
Pacing:
- Use Sleep tool to control wait time between actions
- Prompt cache expires after 5 minutes of inactivity  
- Sleep longer for slow processes, shorter for active iteration

Bias toward action:
- Read files, search code, run tests WITHOUT asking
- Make code changes, commit at good stopping points
- If unsure between two approaches, pick one and go

Terminal focus:
- Unfocused (user away) → autonomous action, commit, push
- Focused (user watching) → collaborative, ask before large changes
```

**Anti-narration rule**: "Never respond with only a status message like 'still waiting' or 'nothing to do' — that wastes a turn and burns tokens for no reason. If you have nothing useful to do, call Sleep immediately."

## 2.7 The Plan Mode (Codex)

Codex has a formal 3-phase planning system:

```
PHASE 1 — Ground in the environment
    - Explore files, configs, schemas before asking questions
    - Resolve discoverable facts through exploration, not asking

PHASE 2 — Intent chat
    - Goal + success criteria, audience, in/out of scope, constraints
    - Bias toward questions over guessing

PHASE 3 — Implementation chat
    - Approach, interfaces, data flow, edge cases, testing
    - Decision complete: implementer needs NO decisions

Finalization:
    <proposed_plan> block with:
    - Title, Summary, Key Changes, Test Plan, Assumptions
    - Behavior-level descriptions over file-by-file inventories
    - Compact: 3-5 sections, not file lists
```

---

# Part 3: Tool Definition & Calling Patterns

## 3.1 JSON Schema Tool Definition (Universal)

ALL production systems use OpenAI-compatible function calling format:

```json
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "What this tool does — this is CRITICAL, the LLM reads this to decide when to call",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "What this param does, when to use it, edge cases"
                }
            },
            "required": ["param1"],
            "additionalProperties": false
        }
    }
}
```

### Universal Patterns in Tool Definitions

| Pattern | Present In |
|---------|-----------|
| `additionalProperties: false` | Claude Code, Codex, Cursor, Manus, v0 |
| `$schema` reference | Claude Code, Codex |
| `default` values specified | Claude Code, Codex, v0 |
| `enum` constraining string params | Claude Code, Manus, v0, Replit |
| `description` on EVERY field | ALL |
| Active voice in descriptions | ALL |
| Examples in descriptions for complex tools | Claude Code, Devin, v0 |

## 3.2 OpenManus Tool Definition Pattern

```python
class MyTool(BaseTool):
    name: str = "my_tool"
    description: str = "What this tool does"
    parameters: dict = {
        "type": "object",
        "properties": { ... },
        "required": [...],
    }

    async def execute(self, **kwargs) -> Any:
        # Implementation
        return result

# Automatic conversion to OpenAI format:
tool.to_param()  # → {"type": "function", "function": {"name": ..., ...}}
```

**ToolCollection**: Registry that wraps multiple tools:
```python
class ToolCollection:
    def to_params(self) -> List[Dict]:
        return [tool.to_param() for tool in self.tools]

    async def execute(self, *, name: str, tool_input: Dict) -> ToolResult:
        tool = self.tool_map.get(name)
        return await tool(**tool_input)  # calls execute(**kwargs)
```

The `ToolCollection` is used in TWO places:
1. **think()** → `to_params()` is passed to LLM as `tools` parameter
2. **act()** → `execute(name, args)` dispatches to the correct tool

## 3.3 OpenHands Tool Definition Pattern

```python
ToolDefinition (ABC, Pydantic model):
    - name (auto-derived from class name)
    - action_type (input schema, Action subclass)
    - observation_type (output schema, Observation subclass) 
    - executor (callable: action → Observation)
    - resources (parallel execution locking)
    - to_openai_tool() → OpenAI format
    - to_mcp_tool() → MCP format
```

**Registration**:
```python
register_tool(name, factory)      # global registry
resolve_tool(tool_spec, state)    # factory → ToolDefinition instances
```

**Key features**:
- Security risk field can be added to action schema (`add_security_risk_prediction`)
- Tools auto-add `summary` field for LLM transparency
- Executor is a Protocol, not inheritance (composition over inheritance)
- `create()` classmethod enables parameterized tool instances

## 3.4 OpenCode Tool Definition Pattern (Effect-TS)

```typescript
Tool.make({
    description: "...",
    input: Schema,       // Effect Schema → JSON Schema
    output: Schema,      // Effect Schema → JSON Schema
    execute: (input, context) => Effect<Type<Output>, ToolFailure>,
})

Tool.definition(name, tool)  // → ToolDefinition (wire format for LLM)
Tool.settle(tool, call, context)  // → decode input → execute → encode output
Tool.withPermission(tool, permissionName)  // → decorate with permission
```

**Registration via `ToolCollection`**:
```typescript
const toolCollection = ToolCollection.make()
toolCollection.add(bashTool)
toolCollection.add(readTool)
// ... 
toolCollection.definitions  // → ToolDefinition[] for LLM
```

**Key difference from Python systems**: 
- Schema is Effect-TS `Schema`, not plain dict
- Input/output are validated at runtime by Schema.decode
- Dependencies are injected via Effect's dependency system
- Permission is a DECORATOR on the tool, not in the registry

## 3.5 Replit Tool Definition Pattern (Proposed Actions)

Replit uses a UNIQUE pattern. Instead of function-calling, it uses XML-like tags:

```xml
<proposed_file_replace_substring 
    file_path="src/index.js" 
    change_summary="Fix typo in greeting">
    <old_str>Hello Worldd</old_str>
    <new_str>Hello World</new_str>
</proposed_file_replace_substring>

<proposed_shell_command 
    working_directory="/home/user/project"
    is_dangerous="false">
    npm install
</proposed_shell_command>
```

**Key insight**: This is NOT function calling. This is structured XML in the response text. The IDE parses these tags from the response and renders them as interactive UI elements (diff view, command button). This pattern is specific to Replit's IDE integration where the agent proposes changes and the user approves/edits before execution.

## 3.6 Claude Code Tool Prompt Pattern

Each tool in Claude Code has its OWN prompt file (`src/tools/*/prompt.ts`). These prompts are LONG and contain:
- Description of what the tool does and when to use it
- Instructions (numbered, detailed)
- Examples of good and bad usage
- Critical warnings about misuse
- Git-specific instructions for bash tool
- Schema in JSON format at the end

**Example: Bash tool prompt** (abbreviated):
```
"Executes a given bash command and returns its output.
 The working directory persists between commands, but shell state does not.
 
 IMPORTANT: Avoid using this tool to run find, grep, cat, head, tail, sed, 
 awk, or echo commands — use dedicated tools instead.
 
 Instructions:
 - If your command will create new directories or files, first run ls to verify parent.
 - Always quote file paths with spaces.
 - Try to maintain your current working directory by using absolute paths.
 - You may specify an optional timeout in milliseconds (up to 600000ms / 10 minutes).
 - When issuing multiple commands: if independent, parallel; if dependent, && chain.
 - For git commands: prefer new commit over amend; never skip hooks.
```

**Key insight**: Each tool's prompt acts as both documentation AND instruction. The LLM reads these when deciding which tool to use. The more detailed the tool prompt, the better the LLM's tool selection.

The tool prompts are NOT part of the schema — they are injected separately in the system prompt section.

## 3.7 Manus Tool Definition (tools.json)

Manus uses the standard OpenAI function-calling format. Notable features:

**Shell tool** requires `id` + `exec_dir` + `command`:
```json
{
    "name": "shell_exec",
    "description": "Execute commands in a specified shell session.",
    "parameters": {
        "properties": {
            "id": {"type": "string", "description": "Unique identifier of the target shell session"},
            "exec_dir": {"type": "string", "description": "Working directory for command execution"},
            "command": {"type": "string", "description": "Shell command to execute"}
        },
        "required": ["id", "exec_dir", "command"]
    }
}
```

**Multiple shell sessions**: Manus supports multiple named shell sessions (`shell_exec` vs `shell_view` vs `shell_wait`), unlike most systems that have one bash tool.

**Communication tools**: `message_notify_user` (non-blocking) and `message_ask_user` (blocking, waits for reply). These are separate from the main output channel.

**Idle tool**: `idle` is a special tool that signals "all tasks complete, entering standby." This is a UNIQUE pattern — most systems just stop calling tools.

**No edit tool**: Manus doesn't have an inline edit tool. It uses `file_str_replace` which is the same thing but named differently.

## 3.8 Tool Description Writing Patterns

### Detail Level by Tool Category

| Category | Description Detail | Example |
|----------|-------------------|---------|
| **File ops** | Medium | "Read file content. Use for checking file contents, analyzing logs, or reading configuration files." |
| **Shell** | Medium | "Execute commands in a specified shell session. Use for running code, installing packages, or managing files." |
| **Browser** | Detailed | Multiple lines with usage scenarios, limitations, and interaction patterns |
| **Web search** | Medium | "Search web pages using search engine. Use for obtaining latest information or finding references." |
| **Communication** | Detailed | Two tiers: notify (non-blocking) vs ask (blocking, user must reply) |
| **Deployment** | Detailed | Port exposure, static/nextjs deployment, testing access |
| **Idle** | Minimal | "A special tool to indicate you have completed all tasks." |

### Description Formula

Every production tool description follows:
1. **What the tool does** (1 sentence)
2. **When to use it** (1 sentence, starts with "Use for...")
3. **Optional: When NOT to use it** (for ambiguous tools)
4. **Optional: Warnings** (for destructive tools)

---

# Part 4: Tool Calling Patterns

## 4.1 The One-Action-Per-Iteration Pattern (Manus)

Manus is the STRICTEST: exactly ONE tool call per iteration. The agent loop explicitly states:
```
"Choose only one tool call per iteration, patiently repeat above steps until task completion"
```

This prevents runaway chains where the agent calls 5 tools in one turn. Each action is atomic and observable.

## 4.2 The Parallel Tool Calling Pattern (Claude Code, Codex, Cursor)

Most systems allow MULTIPLE parallel tool calls:
```
"You can call multiple tools in a single response. If you intend to call multiple 
tools and there are no dependencies between them, make all independent tool calls 
in parallel."
```

**Claude Code**: Explicitly instructs parallel calls for independent work. The coordinator prompt says "Parallelism is your superpower."

**Codex**: "You parallelize tool calls whenever you can, especially file reads such as cat, rg, sed, ls, git show, nl, and wc. You use multi_tool_use.parallel for that parallelism."

**Cursor**: "If independent and can run in parallel, make multiple Shell tool calls in a single message."

**OpenCode**: "Execute multiple independent tool calls in parallel when feasible."

## 4.3 The Sequential + Parallel Hybrid (All Systems)

The universal rule across ALL systems:
```
"Call independent tools in parallel; call dependent tools sequentially"
```

The LLM is trusted to determine which calls are independent. No system enforces this mechanically.

## 4.4 Permission-Based Tool Execution

### Manus Pattern
Tools are always available in the schema, but execution may fail if the action is unauthorized. The agent is told to verify tool names and arguments on failure and try alternatives.

### Claude Code Pattern
```
"Tools are executed in a user-selected permission mode. When you attempt to call 
a tool that is not automatically allowed, the user will be prompted to approve 
or deny. If the user denies a tool call, do not re-attempt the exact same call."
```

### OpenCode Pattern (most sophisticated)
Permission is implemented as **tool filtering**:
```typescript
function whollyDisabled(action, rules) {
    const rule = rules.findLast(rule => Wildcard.match(action, rule.action))
    return rule?.resource === "*" && rule?.effect === "deny"
}
```

If a tool is denied for all resources (`resource: "*"`), it is **completely removed from the tool definitions** sent to the LLM. The LLM never even sees it.

Permission levels: `allow | deny | ask`
- `allow`: Tool is available without confirmation
- `deny`: Tool is removed from schema entirely 
- `ask`: User is prompted each time

**Key insight**: Removing denied tools from the schema is BETTER than logit masking because it preserves the KV cache (all tool descriptions are in the cacheable prefix) and doesn't confuse the model with tools it cannot use.

### OpenHands Pattern
Multi-layer security:
1. LLM self-assesses risk level per tool call
2. Security analyzer (bash AST) checks for dangerous patterns
3. Confirmation policies (AlwaysConfirm / NeverConfirm / ConfirmRisky)
4. Hook system for custom validation

## 4.5 Tool Result Formatting

### Manus
Results are added to the event stream. Agent reads from stream. No special formatting.

### OpenManus
Result is formatted as a string and added to memory as `Message(role="tool")`:
```python
observation = await available_tools.execute(name=name, tool_input=args)
# Result is already a formatted string or ToolResult
```

### OpenCode
Tool output is stored with truncation (2000 lines max, 50KB max). Overflow spills to a file. Results include `{ title, metadata, output, attachments }`.

### Claude Code
Results are injected into conversation as tool results. The system automatically clears old results as context limits approach. Agent told to persist important info.

---

# Part 5: Detailed Architecture Comparisons

## 5.1 Agent Loop Comparison

| Aspect | Manus | Claude Code | Codex | OpenManus | OpenHands | OpenCode |
|--------|-------|-------------|-------|-----------|-----------|----------|
| **Loop type** | Simple iterative | Think→Tool→Observe | Think→Tool→Observe | Think→Act | Event→Process→Emit | Run→Turn→Continue |
| **Actions/turn** | Exactly 1 | Multiple (parallel) | Multiple (parallel) | 1 per think/act | Multiple (parallel) | Multiple (parallel) |
| **Budget** | ~50 turns | 50 per subagent | Unlimited | 10-30 steps | Configurable | 25 steps/run |
| **State machine** | Event stream state | Implicit | Implicit | IDLE/RUNNING/FINISHED/ERROR | 8 states | Implicit |
| **Compaction** | Filesystem only | Auto-trim tool results | Auto-compaction | None | CondensationEvents | Sub-agent summary |
| **Stuck detection** | None explicit | None explicit | None explicit | Duplicate content check | Execution status | Doom loop (planned) |

## 5.2 Memory / Context Comparison

| Aspect | Manus | Claude Code | Codex | OpenManus | OpenHands | OpenCode |
|--------|-------|-------------|-------|-----------|-----------|----------|
| **Primary memory** | Filesystem | Filesystem (MEMORY.md) | Filesystem (.codex/memories) | In-memory (Message list) | EventLog (disk) | SQLite + Drizzle |
| **Index** | todo.md | MEMORY.md | MEMORY.md | None | Event index | SessionMessageTable |
| **Persistence** | Sandbox filesystem | ~/.claude/projects/ | ~/.codex/memories/ | None (in-memory) | File-per-event (disk) | SQLite database |
| **Mem format** | Files | Markdown + frontmatter | Markdown + frontmatter | Pydantic Message[] | JSON events | JSON in SQLite |
| **Linking** | None | [[name]] syntax | Rollout summaries | None | Event IDs | parentID hierarchy |

## 5.3 Sub-Agent Comparison

| Aspect | Manus | Claude Code | Codex | OpenManus | OpenHands | OpenCode |
|--------|-------|-------------|-------|-----------|-----------|----------|
| **Mechanism** | Event stream | Agent tool | Agent tool | Flow abstraction | DelegateTool | Task tool |
| **Parallelism** | Yes (Wide Research) | Yes (coordinator) | Yes | Yes (Flow) | Yes (ThreadPool) | Yes (background jobs) |
| **Types** | Same agent, different goal | Specialized types | Same agent | Same agent, different tools | Agent definition files | Agent definitions |
| **Context isolation** | Separate event stream | Separate session | Separate session | Separate agent instance | Separate LocalConversation | Separate session (parentID) |
| **Result passing** | Event stream merge | task-notification | Tool output | Flow collects | DelegateObservation | Synthetic message injection |

## 5.4 Tool Registry Comparison

| Aspect | Manus | Claude Code | Codex | OpenManus | OpenHands | OpenCode |
|--------|-------|-------------|-------|-----------|-----------|----------|
| **Definition** | JSON in tools.json | Schema in prompt files | OpenAI function calling | Python BaseTool | Pydantic ToolDefinition | Effect-TS Tool.make |
| **Registry** | Hardcoded list | Tool registry (code) | Tool registry | ToolCollection | register_tool() | ToolCollection |
| **Schema format** | OpenAI | JSON Schema | OpenAI | OpenAI | OpenAI + MCP | OpenAI |
| **Filtering** | None | Feature flags | None | ToolChoice enum | Permission analyzer | Permission rules |
| **MCP support** | No | Yes | No | Yes | Yes | Yes |

## 5.5 Prompt Features Comparison

| Feature | Claude Code | Codex | Manus | OpenManus | OpenCode | v0 | Devin | Cursor |
|---------|-------------|-------|-------|-----------|----------|----|-------|--------|
| Identity statement | ✓ | ✓ | ✓ | Limited | ✓ | ✓ | ✓ | ✓ |
| Capabilities list | ✗ | ✗ | ✓ (numbered) | ✗ | ✗ | ✗ | ✗ | ✗ |
| Behavior rules | ✓ (extensive) | ✓ | ✓ (extensive, XML) | Minimal | ✓ | ✓ | ✓ | ✓ |
| Tool usage guidance | ✓ (detailed) | ✓ | ✗ | Minimal | ✓ | ✓ | ✗ | ✓ |
| Tone/style | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ |
| Output efficiency | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Compression instruction | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Memory system | ✓ | ✓ | ✓ | ✗ | ✓ (filesystem) | ✓ (memories) | ✗ | ✗ |
| Dynamic sections | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Caching boundary | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Error handling rules | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ |
| Security rules | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ | ✗ |
| Environment info | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| Plan format | Internal | <proposed_plan> | todo.md | PlanningTool | No formal plan | No formal plan | Planning mode | No formal plan |
| Interaction modes | Normal/Proactive/Coordinator | Normal/Plan | Normal | Normal | Normal | Normal | Planning/Standard | Normal/Plan/Debug/Ask |

---

# Part 6: Synthesis — What This Means for Sarvagya

## Key Design Principles Extracted

1. **Identity first**: Always start with "You are {name}, {role}."
2. **Section builder pattern**: Compose the prompt from independent section functions, not a monolithic template
3. **Caching boundary**: Separate static (global cache) from dynamic (session-specific) content
4. **One action per iteration** (Manus strictness): Simpler, more observable, easier to debug
5. **Filesystem as context** (Manus/Claude Code): Keep context small by writing results to files, referencing by path
6. **Tool descriptions are critical**: The LLM reads tool descriptions to decide when to call them. Invest in writing good descriptions with usage scenarios
7. **Parallel independent calls**: Trust the LLM to parallelize, but guide it with clear rules
8. **Hardware-enforced safety**: Remove denied tools from schema entirely (OpenCode pattern) rather than logit masking
9. **Sub-agents are clones with different prompts**: Don't specialize agent code, specialize the prompt (Manus pattern)
10. **Structured memory**: MEMORY.md index + topic files with frontmatter (Claude Code), linked via [[name]] syntax
11. **Compaction via sub-agent**: Use a separate LLM call to summarize old context into a structured format (OpenCode)
12. **Ephemeral guidance**: Use a fast classifier for per-iteration micro-instructions (Replit pattern)

## Anti-Patterns to Avoid

1. **DAG orchestration**: None of the production systems use DAGs. The LLM decides next action.
2. **Monolithic system prompt**: Claude Code's section builder pattern shows how to keep it modular
3. **Asking the user when exploration suffices**: Codex's plan mode explicitly says "explore first, ask second"
4. **Tool description as an afterthought**: The description is the most important part of a tool — it determines when the LLM calls it
5. **Nested sub-agents by default**: OpenCode explicitly denies `task` permission to sub-agents to prevent recursive spawning
6. **Mutating the system prompt mid-session**: This destroys the KV cache. Keep it frozen.

## Phased Implementation Recommendation

### Phase 1: Core Loop (DONE)
- Think→tool→observe loop with minimal toolset
- Filesystem memory (MEMORY.md + topic files)
- Local sandbox

### Phase 2: Prompt Architecture
- Section builder pattern for prompt assembly
- Static/dynamic boundary with caching marker
- Tool-specific prompt descriptions (separate from schema)
- Output efficiency instructions

### Phase 3: Tool System
- Schema-first tool definitions (Effect-TS or Pydantic pattern)
- Permission as tool filtering
- Tool descriptions with usage scenarios, not just what
- Parallel independent calls

### Phase 4: Memory & Context
- Structured memory index with [[name]] linking
- Compaction via sub-agent summarization
- Progress persistence (todo.md + progress.md)

### Phase 5: Sub-Agent Factory
- Clone pattern with prompt specialization
- Background job injection (OpenCode pattern)
- Event-based result passing

### Phase 6: Guidance Classifier
- Fast classifier LLM per iteration
- Ephemeral instruction injection
- Error pattern analysis
