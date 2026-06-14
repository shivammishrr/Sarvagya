import json
from pathlib import Path

from sarvagya.core.types import Message, ToolDef


_PROMPT_CACHE: str | None = None


def _load_system_prompt() -> str:
    global _PROMPT_CACHE
    if _PROMPT_CACHE is not None:
        return _PROMPT_CACHE
    prompt_path = Path(__file__).parent.parent / "prompts" / "system.md"
    if prompt_path.exists():
        _PROMPT_CACHE = prompt_path.read_text(encoding="utf-8")
    else:
        _PROMPT_CACHE = ""
    return _PROMPT_CACHE


def build_context(
    messages: list[Message],
    tool_defs: list[ToolDef],
    workdir: str,
    iteration: int = 1,
    max_iterations: int = 50,
    memory_index: str = "",
) -> list[dict]:
    system = _load_system_prompt()
    system += (
        f"\n\n## Session\n"
        f"- Working directory: {workdir}\n"
        f"- Iteration: {iteration}/{max_iterations}\n"
    )
    if memory_index:
        system += f"\n{memory_index}\n"

    if tool_defs:
        system += "\n## Available Tools\n"
        for t in tool_defs:
            params = json.dumps(t.parameters, indent=2)
            system += f"- **{t.name}**: {t.description}\n  `{params}`\n"

    result: list[dict] = [{"role": "system", "content": system}]
    for m in messages:
        d: dict = {"role": m.role, "content": m.content}
        if m.tool_call_id:
            d["tool_call_id"] = m.tool_call_id
        if m.name:
            d["name"] = m.name
        result.append(d)
    return result


def truncate_messages(messages: list[Message], max_turns: int = 20) -> list[Message]:
    if len(messages) <= max_turns:
        return messages
    return messages[-max_turns:]
