import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from sarvagya.core.types import ToolDef, ToolResult


class ToolRegistry:
    def __init__(self):
        self._tools: list[ToolDef] = []
        self._handlers: dict[str, callable] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        required: list[str],
        handler: callable,
    ):
        self._tools.append(
            ToolDef(
                name=name,
                description=description,
                parameters=parameters,
                required=required,
            )
        )
        self._handlers[name] = handler

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

    def execute(self, name: str, args: dict) -> ToolResult:
        handler = self._handlers.get(name)
        if not handler:
            return ToolResult(
                success=False, output="", error=f"Unknown tool: {name}"
            )
        try:
            return handler(args)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


def init_tools(registry: ToolRegistry, workdir: str, sandbox) -> None:
    def _bash(args: dict) -> ToolResult:
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

    def _read(args: dict) -> ToolResult:
        file_path = args["file_path"]
        if not os.path.exists(file_path):
            return ToolResult(
                success=False, output="", error=f"File not found: {file_path}"
            )
        offset = args.get("offset", 0)
        limit = args.get("limit")
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if offset > 0:
            lines = lines[offset - 1:]
        if limit:
            lines = lines[:limit]
        output = "".join(
            f"{i + offset if offset > 0 else i + 1}: {line}"
            for i, line in enumerate(lines)
        )
        return ToolResult(success=True, output=output)

    def _write(args: dict) -> ToolResult:
        file_path = args["file_path"]
        content = args["content"]
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(
            success=True,
            output=f"Written {len(content)} bytes to {file_path}",
        )

    def _edit(args: dict) -> ToolResult:
        file_path = args["file_path"]
        old_string = args["old_string"]
        new_string = args["new_string"]
        replace_all = args.get("replace_all", False)

        if not os.path.exists(file_path):
            return ToolResult(
                success=False, output="", error=f"File not found: {file_path}"
            )
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if replace_all:
            if old_string not in content:
                return ToolResult(
                    success=False,
                    output="",
                    error="old_string not found in content",
                )
            new_content = content.replace(old_string, new_string)
        else:
            idx = content.find(old_string)
            if idx == -1:
                return ToolResult(
                    success=False,
                    output="",
                    error="old_string not found in content",
                )
            if content.count(old_string) > 1:
                return ToolResult(
                    success=False,
                    output="",
                    error="Found multiple matches. Use replace_all or more context.",
                )
            new_content = (
                content[:idx]
                + new_string
                + content[idx + len(old_string):]
            )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return ToolResult(success=True, output=f"Edited {file_path}")

    def _glob(args: dict) -> ToolResult:
        import glob as glob_module

        pattern = args["pattern"]
        search_path = args.get("path") or workdir
        matches = glob_module.glob(
            os.path.join(search_path, pattern), recursive=True
        )
        output = "\n".join(matches) if matches else "No matches found"
        return ToolResult(success=True, output=output)

    def _grep(args: dict) -> ToolResult:
        pattern = args["pattern"]
        search_path = args.get("path") or workdir
        include = args.get("include")
        results: list[str] = []
        for root, dirs, files in os.walk(search_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for file in files:
                if include and not file.endswith(include):
                    continue
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                results.append(
                                    f"{filepath}:{i}: {line.rstrip()}"
                                )
                except (UnicodeDecodeError, PermissionError, OSError):
                    continue
        output = "\n".join(results) if results else "No matches found"
        return ToolResult(success=True, output=output)

    def _webfetch(args: dict) -> ToolResult:
        url = args["url"]
        req = urllib.request.Request(
            url, headers={"User-Agent": "Sarvagya/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8")
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    registry.register(
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
        handler=_bash,
    )

    registry.register(
        name="read",
        description="Read a file from the filesystem. Lines are numbered starting at 1.",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to read",
            },
            "offset": {
                "type": "integer",
                "description": "Line number to start reading from",
                "default": 0,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of lines to read",
                "default": None,
            },
        },
        required=["file_path"],
        handler=_read,
    )

    registry.register(
        name="write",
        description="Create or overwrite a file with the given content.",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file",
            },
        },
        required=["file_path", "content"],
        handler=_write,
    )

    registry.register(
        name="edit",
        description="Perform exact string replacement in a file. Read before edit.",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file",
            },
            "old_string": {
                "type": "string",
                "description": "The exact text to replace",
            },
            "new_string": {
                "type": "string",
                "description": "The replacement text",
            },
            "replace_all": {
                "type": "boolean",
                "description": "Replace all occurrences",
                "default": False,
            },
        },
        required=["file_path", "old_string", "new_string"],
        handler=_edit,
    )

    registry.register(
        name="glob",
        description="Find files matching a glob pattern.",
        parameters={
            "pattern": {
                "type": "string",
                "description": "The glob pattern to match (e.g. **/*.py)",
            },
            "path": {
                "type": "string",
                "description": "Directory to search in",
                "default": None,
            },
        },
        required=["pattern"],
        handler=_glob,
    )

    registry.register(
        name="grep",
        description="Search file contents using a regex pattern.",
        parameters={
            "pattern": {
                "type": "string",
                "description": "The regex pattern to search for",
            },
            "path": {
                "type": "string",
                "description": "Directory to search in",
                "default": None,
            },
            "include": {
                "type": "string",
                "description": "File extension filter (e.g. *.py)",
                "default": None,
            },
        },
        required=["pattern"],
        handler=_grep,
    )

    registry.register(
        name="webfetch",
        description="Fetch content from a URL and return it as text.",
        parameters={
            "url": {
                "type": "string",
                "description": "The URL to fetch content from",
            },
            "format": {
                "type": "string",
                "enum": ["text", "markdown"],
                "description": "Return format",
                "default": "markdown",
            },
        },
        required=["url"],
        handler=_webfetch,
    )
