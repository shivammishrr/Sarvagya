from __future__ import annotations
from typing import List
from groq import Groq
from ..base import BaseLLM
from ..types import ChatMessage, LLMConfig, LLMResponse
from ...config import env


class GroqClient(BaseLLM):
    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or "llama-3.1-70b-versatile"
        self.client = Groq(api_key=(api_key or env.GROQ_API_KEY))

    def chat(self, messages: List[ChatMessage], config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or {}
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            temperature=cfg.get("temperature", 0.2),
            max_tokens=cfg.get("max_tokens"),
            top_p=cfg.get("top_p"),
            stop=cfg.get("stop"),
        )
        choice = resp.choices[0]
        text = choice.message.content or ""
        usage = getattr(resp, "usage", {})
        return LLMResponse(text=text, model=self.model, provider="groq", usage=usage, raw=resp)
