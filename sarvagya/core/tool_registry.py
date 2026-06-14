import json

from sarvagya.core.types import ToolDef, ToolResult


class ToolRegistry:
    def __init__(self):
        self._tools: list[ToolDef] = []
        self._handlers: dict[str, callable] = {}

    def register(self, tool: ToolDef, handler: callable):
        self._tools.append(tool)
        self._handlers[tool.name] = handler

    def schemas(self) -> list[dict]:
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
            for t in self._tools
        ]

    def tool_defs(self) -> list[ToolDef]:
        return list(self._tools)

    def execute(self, name: str, args: dict | str) -> ToolResult:
        handler = self._handlers.get(name)
        if not handler:
            return ToolResult(success=False, output="", error=f"Unknown tool: {name}")
        if isinstance(args, str):
            args = json.loads(args)
        try:
            return handler(args)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
