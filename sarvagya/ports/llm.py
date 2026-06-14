from typing import Protocol

from sarvagya.core.types import LLMResponse, Message, ToolDef


class LLMProvider(Protocol):
    def complete(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
    ) -> LLMResponse:
        ...
