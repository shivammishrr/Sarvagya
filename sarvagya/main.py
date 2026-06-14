import argparse
import os

from sarvagya.adapters.llm.openai import OpenAIAdapter
from sarvagya.adapters.memory.filesystem import FileMemory
from sarvagya.adapters.sandbox.local import LocalSandbox
from sarvagya.adapters.search.tavily import TavilySearch
from sarvagya.core.loop import AgentLoop
from sarvagya.core.tools import ToolRegistry, init_tools
from sarvagya.core.types import ToolResult


def main():
    parser = argparse.ArgumentParser(description="Sarvagya - Autonomous AI Agent")
    parser.add_argument("task", nargs="?", help="Task prompt for the agent")
    parser.add_argument(
        "--workdir",
        default=os.getcwd(),
        help="Working directory for the agent",
    )
    parser.add_argument(
        "--provider",
        default="openai",
        choices=["openai", "anthropic"],
        help="LLM provider to use",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (default: provider-specific)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key for the LLM provider",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=50,
        help="Maximum iterations for the agent loop",
    )

    args = parser.parse_args()

    task = args.task or os.environ.get("SARVAGYA_TASK")
    if not task:
        parser.print_help()
        print("\nError: task prompt is required")
        return

    api_key = args.api_key or os.environ.get("LLM_API_KEY") or ""
    groq_api_key = os.environ.get("GROQ_API_KEY", "")
    tavily_api_key = os.environ.get("TAVILY_API_KEY", "")

    sandbox = LocalSandbox(workdir=args.workdir)
    memory = FileMemory(base_path=os.path.join(sandbox.workdir, "memory"))
    memory.init_dir("")

    registry = ToolRegistry()
    init_tools(registry, sandbox.workdir, sandbox)

    if tavily_api_key:
        tavily = TavilySearch(api_key=tavily_api_key)
        registry.register(
            name="websearch",
            description="Search the web using Tavily. Returns relevant results with titles, URLs and content snippets.",
            parameters={
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
            },
            required=["query"],
            handler=lambda args: ToolResult(
                success=True,
                output=tavily.search(args["query"]),
            ),
        )

    models = {
        "openai": "meta-llama/llama-4-scout-17b-16e-instruct",
        "anthropic": "claude-sonnet-4-20250514",
    }
    model = args.model or models.get(args.provider, models["openai"])

    if args.provider == "anthropic":
        from sarvagya.adapters.llm.anthropic import AnthropicAdapter

        if "sk-ant" not in api_key:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        llm = AnthropicAdapter(api_key=api_key, model=model)
    else:
        base_url = None
        if groq_api_key and not api_key:
            api_key = groq_api_key
            base_url = "https://api.groq.com/openai/v1"
        llm = OpenAIAdapter(
            api_key=api_key,
            model=model,
            base_url=base_url,
        )

    loop = AgentLoop(
        llm=llm,
        sandbox=sandbox,
        memory=memory,
        tools=registry,
        workdir=sandbox.workdir,
    )

    result = loop.run(task=task, max_iterations=args.max_iterations)
    if result.error:
        print(f"Error: {result.error}")
    if result.output:
        print(result.output)


if __name__ == "__main__":
    main()
