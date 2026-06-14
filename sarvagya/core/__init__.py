import os

from sarvagya.adapters.llm.openai import OpenAIAdapter
from sarvagya.adapters.memory.filesystem import FileMemory
from sarvagya.adapters.sandbox.local import LocalSandbox
from sarvagya.adapters.search.tavily import TavilySearch
from sarvagya.core.loop import AgentLoop
from sarvagya.core.tool_registry import ToolRegistry
from sarvagya.core.tools import init_tools
from sarvagya.core.types import AgentResult, ToolDef, ToolResult


def _make_llm(model: str, api_key: str | None):
    api_key = api_key or os.environ.get("API_KEY") or ""
    model_lower = model.lower()
    if "claude" in model_lower or "anthropic" in model_lower:
        from sarvagya.adapters.llm.anthropic import AnthropicAdapter
        return AnthropicAdapter(api_key=api_key, model=model)
    return OpenAIAdapter(api_key=api_key, model=model)


def _register_websearch(registry: ToolRegistry):
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    if not tavily_key:
        return
    tavily = TavilySearch(api_key=tavily_key)

    registry.register(
        ToolDef(
            name="websearch",
            description="Search the web using Tavily. Returns relevant results with titles, URLs and content snippets.",
            parameters={"query": {"type": "string", "description": "The search query"}},
            required=["query"],
        ),
        handler=lambda args: ToolResult(success=True, output=tavily.search(args["query"])),
    )


def run(task: str, workdir: str | None = None,
        model: str | None = None, api_key: str | None = None,
        max_iterations: int = 50) -> AgentResult:
    sandbox = LocalSandbox(workdir=workdir)
    memory = FileMemory(base_path=os.path.join(sandbox.workdir, "memory"))
    memory.init_dir("")

    registry = ToolRegistry()
    init_tools(registry, sandbox.workdir, sandbox)
    _register_websearch(registry)

    if not model:
        model = os.environ.get("MODEL", "")
    if not model:
        return AgentResult(success=False, output="", error="No model specified. Set MODEL env var or pass --model")
    if not api_key:
        return AgentResult(success=False, output="", error="No API key specified. Set API_KEY env var or pass --api-key")

    llm = _make_llm(model, api_key)
    loop = AgentLoop(llm=llm, sandbox=sandbox, memory=memory,
                     tools=registry, workdir=sandbox.workdir)
    return loop.run(task=task, max_iterations=max_iterations)
