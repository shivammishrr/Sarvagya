from __future__ import annotations
from typing import List, Literal, TypedDict, Any, Optional

Role = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    role: Role
    content: str


class LLMResponse(TypedDict, total=False):
    text: str
    model: str
    provider: str
    usage: dict[str, Any]
    raw: Any  # provider raw response


class LLMConfig(TypedDict, total=False):
    model: str
    temperature: float
    max_tokens: int
    top_p: float
    stop: Optional[List[str]]
