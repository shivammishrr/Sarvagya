from __future__ import annotations
from typing import List
from openai import AzureOpenAI
from ..base import BaseLLM
from ..types import ChatMessage, LLMConfig, LLMResponse
from ...config import env


class AzureOpenAIClient(BaseLLM):
    """Azure OpenAI chat client.

    Uses deployment name as model (env.AZURE_OPENAI_DEPLOYMENT) and endpoint like
    https://<resource>.openai.azure.com/ with API key env.AZURE_OPENAI_API_KEY.
    """

    def __init__(
        self,
        model: str | None = None,
        endpoint: str | None = None,
        api_key: str | None = None,
        api_version: str | None = None,
    ) -> None:
        self.model = model or env.AZURE_OPENAI_DEPLOYMENT or env.MODEL_NAME
        self.client = AzureOpenAI(
            api_key=(api_key or env.AZURE_OPENAI_API_KEY),
            api_version=api_version or "2024-06-01",
            azure_endpoint=(endpoint or env.AZURE_OPENAI_ENDPOINT),
        )

    def chat(self, messages: List[ChatMessage], config: LLMConfig | None = None) -> LLMResponse:
        cfg = config or {}
        resp = self.client.chat.completions.create(
            model=self.model,  # deployment name
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            temperature=cfg.get("temperature", 0.2),
            max_tokens=cfg.get("max_tokens"),
            top_p=cfg.get("top_p"),
            stop=cfg.get("stop"),
        )
        choice = resp.choices[0]
        text = choice.message.content or ""
        usage = getattr(resp, "usage", None)
        return LLMResponse(
            text=text,
            model=self.model,
            provider="azure",
            usage=usage.model_dump() if hasattr(usage, "model_dump") else (usage or {}),
            raw=resp.model_dump() if hasattr(resp, "model_dump") else resp,  # type: ignore[arg-type]
        )
