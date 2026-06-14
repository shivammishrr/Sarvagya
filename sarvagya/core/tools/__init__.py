from sarvagya.core.tool_registry import ToolRegistry
from sarvagya.core.tools.bash import BASH_TOOL, make_handler as bash_handler
from sarvagya.core.tools.file_ops import FILE_TOOLS, HANDLERS as file_handlers
from sarvagya.core.tools.search_ops import SEARCH_TOOLS, make_handler as search_handler
from sarvagya.core.tools.web import WEB_TOOLS, make_handler as web_handler


def init_tools(registry: ToolRegistry, workdir: str, sandbox) -> None:
    handlers = {
        "bash": bash_handler(sandbox, workdir),
        **file_handlers,
        "glob": search_handler("glob", workdir),
        "grep": search_handler("grep", workdir),
        "webfetch": web_handler("webfetch"),
    }

    for tool in [BASH_TOOL] + FILE_TOOLS + SEARCH_TOOLS + WEB_TOOLS:
        registry.register(tool, handlers[tool.name])
