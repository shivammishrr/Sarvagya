import urllib.request

from sarvagya.core.types import ToolDef, ToolResult


WEB_TOOLS: list[ToolDef] = [
    ToolDef(
        name="webfetch",
        description="Fetch content from a URL and return it as text.",
        parameters={
            "url": {
                "type": "string",
                "description": "The URL to fetch content from",
            },
        },
        required=["url"],
    ),
]


def handle_webfetch(args: dict) -> ToolResult:
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
