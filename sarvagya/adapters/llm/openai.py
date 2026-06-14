import json

from openai import OpenAI

from sarvagya.core.types import LLMResponse, Message, ToolCall, ToolDef


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
            if m.tool_calls:
                d["tool_calls"] = [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.name, "arguments": tc.arguments if isinstance(tc.arguments, str) else json.dumps(tc.arguments)}}
                    for tc in m.tool_calls
                ]
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
        self, messages: list[Message], tools: list[ToolDef] | None = None
    ) -> LLMResponse:
        params = {"model": self.model, "messages": self._convert_messages(messages)}
        if tools:
            params["tools"] = self._convert_tools(tools)
        choice = self._client.chat.completions.create(**params).choices[0]
        tcalls = None
        if choice.message.tool_calls:
            tcalls = [ToolCall(id=t.id, name=t.function.name, arguments=t.function.arguments) for t in choice.message.tool_calls]
        return LLMResponse(content=choice.message.content or "", tool_calls=tcalls, stop_reason=choice.finish_reason or "stop")

