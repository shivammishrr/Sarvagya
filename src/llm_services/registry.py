from __future__ import annotations
from .base import BaseLLM
from .providers.openai_client import OpenAIClient
from .providers.anthropic_client import AnthropicClient
from .providers.gemini_client import GeminiClient
from .providers.mistral_client import MistralClient
from .providers.groq_client import GroqClient
from ..config import env


def get_llm() -> BaseLLM:
    provider = (env.LLM_PROVIDER or "openai").lower()
    model = env.MODEL_NAME

    if provider == "openai":
        # default MODEL_NAME now chatgpt-4o-latest
        return OpenAIClient(model=model)
    if provider == "anthropic":
        return AnthropicClient(model=model or "claude-3-7-sonnet-latest")
    if provider == "gemini":
        return GeminiClient(model=model or "gemini-2.5-flash")
    if provider == "mistral":
        return MistralClient(model=model or "mistral-large-latest")
    if provider == "groq":
        return GroqClient(model=model or "llama-3.3-70b-versatile")

    # Fallback
    return OpenAIClient(model=model)
