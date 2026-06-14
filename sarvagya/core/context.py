import json
import os

from sarvagya.core.types import Message, ToolDef


def build_system_prompt() -> str:
    return """You are Sarvagya, an autonomous AI agent operating in a sandboxed environment.
You complete tasks by: thinking → calling a tool → observing the result → repeating.

RULES:
- One action per iteration. Call ONE tool, observe, then decide next.
- Never call multiple tools in a single turn.
- Prefer dedicated tools (Read/Write/Edit/Glob/Grep) over bash for file operations.
- Read before edit. Never edit code you haven't read.
- Reference code as file:line_number when discussing.
- Be concise. No emojis. Short responses.
- Write important findings to notes.md before they leave context.
- When stuck, try 3 different approaches before giving up.
- Never expose secrets or API keys in your output.
- Framework-agnostic: you interact through tools, not direct SDKs."""


def build_dynamic_section(
    workdir: str,
    memory_index: str = "",
    iteration: int = 1,
    max_iterations: int = 50,
) -> str:
    lines = [
        f"Working directory: {workdir}",
        f"Iteration: {iteration}/{max_iterations}",
        "",
    ]
    if memory_index:
        lines.append(f"Memory index:\n{memory_index}")
    return "\n".join(lines)


def build_tool_section(tools: list[ToolDef]) -> str:
    lines: list[str] = []
    for t in tools:
        params_str = json.dumps(t.parameters, indent=2)
        lines.append(f"- {t.name}: {t.description}")
        lines.append(f"  Parameters: {params_str}")
    return "\n".join(lines)


def format_messages(
    messages: list[Message],
    system_prompt: str,
    dynamic_section: str,
    tool_section: str,
    schemas: list[dict],
) -> list[dict]:
    system = f"{system_prompt}\n\n{dynamic_section}\n\nAVAILABLE TOOLS:\n{tool_section}"

    result: list[dict] = [{"role": "system", "content": system}]
    for m in messages:
        d: dict = {"role": m.role, "content": m.content}
        if m.tool_call_id:
            d["tool_call_id"] = m.tool_call_id
        if m.name:
            d["name"] = m.name
        result.append(d)
    return result


def truncate_messages(
    messages: list[Message], max_turns: int = 20
) -> list[Message]:
    if len(messages) <= max_turns:
        return messages
    return messages[-max_turns:]
