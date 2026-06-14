import os

from sarvagya.core.types import AgentResult
from sarvagya.adapters.llm.openai import OpenAIAdapter
from sarvagya.adapters.memory.filesystem import FileMemory
from sarvagya.adapters.sandbox.local import LocalSandbox
from sarvagya.adapters.search.tavily import TavilySearch
from sarvagya.core.loop import AgentLoop
from sarvagya.core.tool_registry import ToolRegistry
from sarvagya.core.tools import init_tools
from sarvagya.core.types import ToolResult


def _make_llm(provider: str, model: str | None, api_key: str | None):
    api_key = api_key or os.environ.get("LLM_API_KEY") or ""
    models = {
        "openai": "meta-llama/llama-4-scout-17b-16e-instruct",
        "anthropic": "claude-sonnet-4-20250514",
    }
    model = model or models.get(provider, models["openai"])

    if provider == "anthropic":
        from sarvagya.adapters.llm.anthropic import AnthropicAdapter

        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        return AnthropicAdapter(api_key=key, model=model)

    groq_key = os.environ.get("GROQ_API_KEY", "")
    base_url = None
    if groq_key and not api_key:
        api_key = groq_key
        base_url = "https://api.groq.com/openai/v1"
    return OpenAIAdapter(api_key=api_key, model=model, base_url=base_url)


def _register_websearch(registry: ToolRegistry):
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    if not tavily_key:
        return
    tavily = TavilySearch(api_key=tavily_key)
    from sarvagya.core.types import ToolDef

    registry.register(
        ToolDef(
            name="websearch",
            description="Search the web using Tavily. Returns relevant results with titles, URLs and content snippets.",
            parameters={
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
            },
            required=["query"],
        ),
        handler=lambda args: ToolResult(
            success=True,
            output=tavily.search(args["query"]),
        ),
    )


def run(task: str, workdir: str | None = None, provider: str = "openai",
        model: str | None = None, api_key: str | None = None,
        max_iterations: int = 50) -> AgentResult:
    sandbox = LocalSandbox(workdir=workdir)
    memory = FileMemory(base_path=os.path.join(sandbox.workdir, "memory"))
    memory.init_dir("")

    registry = ToolRegistry()
    init_tools(registry, sandbox.workdir, sandbox)
    _register_websearch(registry)

    llm = _make_llm(provider, model, api_key)
    loop = AgentLoop(llm=llm, sandbox=sandbox, memory=memory,
                     tools=registry, workdir=sandbox.workdir)
    return loop.run(task=task, max_iterations=max_iterations)
