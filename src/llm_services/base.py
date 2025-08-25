from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from .types import ChatMessage, LLMConfig, LLMResponse


class BaseLLM(ABC):
    """Abstract base for provider-agnostic chat completion.

    Implementations should translate messages/config to provider SDK calls
    and normalize the response to `LLMResponse`.
    """

    @abstractmethod
    def chat(self, messages: List[ChatMessage], config: LLMConfig | None = None) -> LLMResponse:
        raise NotImplementedError
