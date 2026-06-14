import json

from anthropic import Anthropic

from sarvagya.core.types import LLMResponse, Message, ToolCall, ToolDef


class AnthropicAdapter:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = Anthropic(api_key=api_key)

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        system = None
        result: list[dict] = []
        for m in messages:
            if m.role == "system":
                system = m.content
                continue
            if m.role == "assistant" and m.tool_calls:
                blocks = []
                if m.content:
                    blocks.append({"type": "text", "text": m.content})
                for tc in m.tool_calls:
                    blocks.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": json.loads(tc.arguments) if isinstance(tc.arguments, str) else tc.arguments,
                    })
                result.append({"role": "assistant", "content": blocks})
            elif m.role == "tool":
                result.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.tool_call_id,
                        "content": m.content,
                    }],
                })
            else:
                result.append({"role": m.role, "content": m.content})
        return system, result

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
        self, messages: list[Message], tools: list[ToolDef] | None = None
    ) -> LLMResponse:
        system, msgs = self._convert_messages(messages)
        params = {"model": self.model, "messages": msgs, "max_tokens": 4096}
        if system:
            params["system"] = system
        if tools:
            params["tools"] = self._convert_tools(tools)
        resp = self._client.messages.create(**params)

        content = ""
        tcalls = None
        for b in resp.content:
            if b.type == "text":
                content += b.text
            elif b.type == "tool_use":
                if tcalls is None:
                    tcalls = []
                tcalls.append(ToolCall(id=b.id, name=b.name, arguments=dict(b.input)))
        return LLMResponse(content=content, tool_calls=tcalls, stop_reason=resp.stop_reason or "stop")
