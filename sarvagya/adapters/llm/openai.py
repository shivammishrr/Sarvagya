from collections.abc import Iterator

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from sarvagya.core.types import LLMChunk, LLMResponse, Message, ToolCall, ToolDef


class OpenAIAdapter:
    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        args = {"api_key": api_key, "model": model}
        if base_url:
            args["base_url"] = base_url
        self.model = model
        self.args = {k: v for k, v in args.items() if k != "model"}
        self._client = OpenAI(**self.args)

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        result: list[dict] = []
        for m in messages:
            d: dict = {"role": m.role, "content": m.content}
            if m.tool_call_id:
                d["tool_call_id"] = m.tool_call_id
            if m.name:
                d["name"] = m.name
            result.append(d)
        return result

    def _convert_tools(self, tools: list[ToolDef]) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": {
                        "type": "object",
                        "properties": t.parameters,
                        "required": t.required,
                        "additionalProperties": False,
                    },
                },
            }
            for t in tools
        ]

    def complete(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
    ) -> LLMResponse:
        params: dict = {
            "model": self.model,
            "messages": self._convert_messages(messages),
        }
        if tools:
            params["tools"] = self._convert_tools(tools)

        resp = self._client.chat.completions.create(**params)
        choice = resp.choices[0]

        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=tc.function.arguments,
                )
                for tc in choice.message.tool_calls
            ]

        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason or "stop",
        )

    def stream(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
    ) -> Iterator[LLMChunk]:
        params: dict = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "stream": True,
        }
        if tools:
            params["tools"] = self._convert_tools(tools)

        stream = self._client.chat.completions.create(**params)
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue
            yield LLMChunk(
                content=delta.content or "",
                finish_reason=chunk.choices[0].finish_reason,
            )
