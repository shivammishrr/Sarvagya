from __future__ import annotations
from typing import List
from mistralai import Mistral
from ..base import BaseLLM
from ..types import ChatMessage, LLMConfig, LLMResponse
from ...config import env


class MistralClient(BaseLLM):
    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or "mistral-large-latest"
        key = (api_key or env.MISTRAL_API_KEY).strip()
        self.client = Mistral(api_key=key)

    def chat(self, messages: List[ChatMessage], config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or {}
        resp = self.client.chat.complete(
            model=self.model,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            temperature=cfg.get("temperature", 0.2),
            max_tokens=cfg.get("max_tokens"),
            top_p=cfg.get("top_p"),
            stop=cfg.get("stop"),
        )
        text = resp.choices[0].message.content or ""
        usage = getattr(resp, "usage", {})
        return LLMResponse(text=text, model=self.model, provider="mistral", usage=usage, raw=resp)
