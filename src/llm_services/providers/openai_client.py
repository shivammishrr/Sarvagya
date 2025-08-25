from __future__ import annotations
from typing import List, Any
from openai import OpenAI
from ..base import BaseLLM
from ..types import ChatMessage, LLMConfig, LLMResponse
from ...config import env


class OpenAIClient(BaseLLM):
    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or env.MODEL_NAME
        self.client = OpenAI(api_key=api_key or env.OPENAI_API_KEY)

    def chat(self, messages: List[ChatMessage], config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or {}
        # Map our chat messages to Responses API input format
        # Each message becomes {role, content: [{type: "text", text: ...}]}
        input_msgs = [
            {
                "role": m["role"],
                "content": [
                    {"type": "text", "text": m["content"]},
                ],
            }
            for m in messages
        ]

        resp = self.client.responses.create(
            model=self.model,
            input=input_msgs,
            temperature=cfg.get("temperature", 0.2),
            max_output_tokens=cfg.get("max_tokens"),
            top_p=cfg.get("top_p"),
            stop=cfg.get("stop"),
        )

        # SDK exposes output_text for convenience when response contains text
        text = getattr(resp, "output_text", None)
        if text is None:
            # Fallback: some SDK versions use .output[0].content[0].text
            try:
                first = resp.output[0].content[0]
                text = getattr(first, "text", "")
            except Exception:
                text = ""

        usage = getattr(resp, "usage", None)
        usage_dict: Any = {}
        if usage is not None:
            usage_dict = usage.model_dump() if hasattr(usage, "model_dump") else getattr(usage, "__dict__", {})

        raw_obj: Any = resp.model_dump() if hasattr(resp, "model_dump") else resp
        return LLMResponse(text=text or "", model=self.model, provider="openai", usage=usage_dict, raw=raw_obj)
