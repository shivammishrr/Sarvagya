from collections.abc import Iterator

from anthropic import Anthropic

from sarvagya.core.types import LLMChunk, LLMResponse, Message, ToolCall, ToolDef


class AnthropicAdapter:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = Anthropic(api_key=api_key)

    def _split_system(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        system = None
        converted: list[dict] = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                d: dict = {"role": m.role, "content": m.content}
                if m.tool_call_id:
                    d["tool_call_id"] = m.tool_call_id
                converted.append(d)
        return system, converted

    def _convert_tools(self, tools: list[ToolDef]) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": {
                    "type": "object",
                    "properties": t.parameters,
                    "required": t.required,
                },
            }
            for t in tools
        ]

    def complete(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
    ) -> LLMResponse:
        system, msgs = self._split_system(messages)
        params: dict = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": 4096,
        }
        if system:
            params["system"] = system
        if tools:
            params["tools"] = self._convert_tools(tools)

        resp = self._client.messages.create(**params)

        tool_calls = None
        content = ""
        for block in resp.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tc = ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=dict(block.input),
                )
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(tc)

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=resp.stop_reason or "stop",
        )

    def stream(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
    ) -> Iterator[LLMChunk]:
        system, msgs = self._split_system(messages)
        params: dict = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": 4096,
            "stream": True,
        }
        if system:
            params["system"] = system
        if tools:
            params["tools"] = self._convert_tools(tools)

        with self._client.messages.create(**params) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        yield LLMChunk(content=delta.text)
                elif event.type == "message_delta":
                    if event.delta.stop_reason:
                        yield LLMChunk(finish_reason=event.delta.stop_reason)
