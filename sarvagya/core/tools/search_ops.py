import os
import re

from sarvagya.core.types import ToolDef, ToolResult


SEARCH_TOOLS: list[ToolDef] = [
    ToolDef(
        name="glob",
        description="Find files matching a glob pattern.",
        parameters={
            "pattern": {"type": "string", "description": "The glob pattern to match (e.g. **/*.py)"},
            "path": {"type": "string", "description": "Directory to search in", "default": None},
        },
        required=["pattern"],
    ),
    ToolDef(
        name="grep",
        description="Search file contents using a regex pattern.",
        parameters={
            "pattern": {"type": "string", "description": "The regex pattern to search for"},
            "path": {"type": "string", "description": "Directory to search in", "default": None},
            "include": {"type": "string", "description": "File extension filter (e.g. *.py)", "default": None},
        },
        required=["pattern"],
    ),
]


def handle_glob(args: dict, workdir: str) -> ToolResult:
    import glob as gm
    pattern = args["pattern"]
    search_path = args.get("path") or workdir
    matches = gm.glob(os.path.join(search_path, pattern), recursive=True)
    return ToolResult(success=True, output="\n".join(matches) if matches else "No matches found")


def handle_grep(args: dict, workdir: str) -> ToolResult:
    pattern = args["pattern"]
    search_path = args.get("path") or workdir
    include = args.get("include")
    results: list[str] = []
    for root, dirs, files in os.walk(search_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            if include and not file.endswith(include):
                continue
            fp = os.path.join(root, file)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if re.search(pattern, line):
                            results.append(f"{fp}:{i}: {line.rstrip()}")
            except (UnicodeDecodeError, PermissionError, OSError):
                continue
    return ToolResult(success=True, output="\n".join(results) if results else "No matches found")
