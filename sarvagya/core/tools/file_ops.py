import os
from pathlib import Path

from sarvagya.core.types import ToolDef, ToolResult


FILE_TOOLS: list[ToolDef] = [
    ToolDef(
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
    ),
    ToolDef(
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
    ),
    ToolDef(
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
    ),
]


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
    start = offset if offset > 0 else 1
    output = "".join(f"{start + i}: {line}" for i, line in enumerate(lines))
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
                success=False, output="", error="old_string not found in content"
            )
        new_content = content.replace(old_string, new_string)
    else:
        idx = content.find(old_string)
        if idx == -1:
            return ToolResult(
                success=False, output="", error="old_string not found in content"
            )
        if content.count(old_string) > 1:
            return ToolResult(
                success=False, output="",
                error="Found multiple matches. Use replace_all or more context.",
            )
        new_content = content[:idx] + new_string + content[idx + len(old_string):]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return ToolResult(success=True, output=f"Edited {file_path}")


HANDLERS = {
    "read": _read,
    "write": _write,
    "edit": _edit,
}
