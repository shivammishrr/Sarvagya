from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str
    content: str
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any]
    required: list[str]


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall] | None = None
    stop_reason: str = "stop"


@dataclass
class LLMChunk:
    content: str = ""
    tool_call_builder: ToolCall | None = None
    finish_reason: str | None = None


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None


@dataclass
class SandboxResult:
    success: bool
    output: str
    error: str | None = None


@dataclass
class MemoryEntry:
    key: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    success: bool
    output: str
    iterations: int = 0
    error: str | None = None
