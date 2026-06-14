from sarvagya.core.types import ToolDef, ToolResult


BASH_TOOL = ToolDef(
    name="bash",
    description="Execute a shell command. Prefer Read/Write/Edit/Glob/Grep for file operations.",
    parameters={
        "command": {
            "type": "string",
            "description": "The shell command to execute",
        },
        "timeout": {
            "type": "number",
            "description": "Timeout in ms (default 120000, max 600000)",
            "default": 120000,
        },
        "description": {
            "type": "string",
            "description": "Clear description of what this command does (5-10 words)",
        },
    },
    required=["command", "description"],
)


def make_handler(sandbox, workdir: str):
    def handler(args: dict) -> ToolResult:
        result = sandbox.execute(
            command=args["command"],
            timeout=args.get("timeout", 120000),
            workdir=workdir,
        )
        return ToolResult(
            success=result.success,
            output=result.output,
            error=result.error,
        )

    return handler
