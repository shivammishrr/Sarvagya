from __future__ import annotations
from typing import List, Any
import anthropic
from ..base import BaseLLM
from ..types import ChatMessage, LLMConfig, LLMResponse
from ...config import env


class AnthropicClient(BaseLLM):
    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or "claude-3-7-sonnet-latest"
        key = (api_key or env.ANTHROPIC_API_KEY).strip()
        self.client = anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()

    def chat(self, messages: List[ChatMessage], config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or {}
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        system = "\n\n".join(system_parts) if system_parts else None
        # Anthropic expects list of messages without system role
        msgs = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]

        resp = self.client.messages.create(
            model=self.model,
            system=system,
            max_tokens=cfg.get("max_tokens", 1024),
            temperature=cfg.get("temperature", 0.2),
            messages=msgs,
        )
        # content is a list of blocks; pick text blocks
        text = "".join([b.text for b in resp.content if getattr(b, "type", "") == "text"])  # type: ignore[attr-defined]
        usage = getattr(resp, "usage", {})
        return LLMResponse(
            text=text,
            model=self.model,
            provider="anthropic",
            usage=usage if isinstance(usage, dict) else getattr(usage, "__dict__", {}),
            raw=resp,
        )
