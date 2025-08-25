from __future__ import annotations
from typing import List
from .types import ChatMessage, LLMConfig, LLMResponse
from .registry import get_llm


def chat(messages: List[ChatMessage], config: LLMConfig | None = None) -> LLMResponse:
    """Provider-agnostic chat completion.

    Selects an LLM client via environment (see src/config/env.py LLM_PROVIDER, MODEL_NAME)
    and returns a normalized LLMResponse.
    """
    client = get_llm()
    return client.chat(messages, config)
