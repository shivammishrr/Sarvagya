from sarvagya.core.tool_registry import ToolRegistry
from sarvagya.core.tools.bash import BASH_TOOL, make_handler as bash_handler
from sarvagya.core.tools.file_ops import FILE_TOOLS, HANDLERS as file_handlers
from sarvagya.core.tools.search_ops import SEARCH_TOOLS, handle_glob, handle_grep
from sarvagya.core.tools.web import WEB_TOOLS, handle_webfetch


def init_tools(registry: ToolRegistry, workdir: str, sandbox) -> None:
    handlers = {
        "bash": bash_handler(sandbox, workdir),
        **file_handlers,
        "glob": lambda args, _wd=workdir: handle_glob(args, _wd),
        "grep": lambda args, _wd=workdir: handle_grep(args, _wd),
        "webfetch": handle_webfetch,
    }

    for tool in [BASH_TOOL] + FILE_TOOLS + SEARCH_TOOLS + WEB_TOOLS:
        registry.register(tool, handlers[tool.name])
