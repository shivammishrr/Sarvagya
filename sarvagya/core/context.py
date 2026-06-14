import json
from pathlib import Path

from sarvagya.core.types import Message, ToolDef

_PROMPT_CACHE: str | None = None


def _load_system_prompt() -> str:
    global _PROMPT_CACHE
    if _PROMPT_CACHE is not None:
        return _PROMPT_CACHE
    p = Path(__file__).parent.parent / "prompts" / "system.md"
    _PROMPT_CACHE = p.read_text(encoding="utf-8") if p.exists() else ""
    return _PROMPT_CACHE


def build_context(
    messages: list[Message], tool_defs: list[ToolDef], workdir: str,
    iteration: int = 1, max_iterations: int = 50, memory_index: str = "",
) -> list[dict]:
    system = _load_system_prompt()
    system += f"\n\n## Session\n- Working directory: {workdir}\n- Iteration: {iteration}/{max_iterations}\n"
    if memory_index:
        system += f"\n{memory_index}\n"
    if tool_defs:
        system += "\n## Available Tools\n"
        for t in tool_defs:
            system += f"- **{t.name}**: {t.description}\n  `{json.dumps(t.parameters, indent=2)}`\n"

    result = [{"role": "system", "content": system}]
    for m in messages:
        d = {"role": m.role, "content": m.content}
        if m.tool_call_id:
            d["tool_call_id"] = m.tool_call_id
        if m.name:
            d["name"] = m.name
        if m.tool_calls:
            d["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.name, "arguments": tc.arguments if isinstance(tc.arguments, str) else json.dumps(tc.arguments)}}
                for tc in m.tool_calls
            ]
        result.append(d)
    return result


def truncate_messages(messages: list[Message], max_turns: int = 20) -> list[Message]:
    return messages if len(messages) <= max_turns else messages[-max_turns:]
