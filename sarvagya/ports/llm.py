from collections.abc import Iterator
from typing import Protocol

from sarvagya.core.types import LLMChunk, LLMResponse, Message, ToolDef


class LLMProvider(Protocol):
    def complete(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
    ) -> LLMResponse:
        ...

    def stream(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
    ) -> Iterator[LLMChunk]:
        ...
