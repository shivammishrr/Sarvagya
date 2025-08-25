from __future__ import annotations
from typing import List
from google import genai
from google.genai import types as genai_types
from ..base import BaseLLM
from ..types import ChatMessage, LLMConfig, LLMResponse
from ...config import env


class GeminiClient(BaseLLM):
    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or "gemini-2.5-flash"
        self.client = genai.Client(api_key=(api_key or env.GOOGLE_API_KEY))

    def chat(self, messages: List[ChatMessage], config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or {}
        # Concatenate system content into a single system preface
        sys_parts = [m["content"] for m in messages if m["role"] == "system"]
        system_text = "\n\n".join(sys_parts) if sys_parts else None

        contents: list[genai_types.Part | str | dict] = []
        if system_text:
            contents.append({"role": "user", "parts": system_text})
        for m in messages:
            if m["role"] == "system":
                continue
            contents.append({"role": m["role"], "parts": m["content"]})

        resp = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=genai_types.GenerateContentConfig(
                temperature=cfg.get("temperature", 0.2),
                max_output_tokens=cfg.get("max_tokens"),
                top_p=cfg.get("top_p"),
                stop_sequences=cfg.get("stop"),
            ),
        )
        text = getattr(resp, "text", "") or ""
        return LLMResponse(text=text, model=self.model, provider="gemini", raw=resp)
