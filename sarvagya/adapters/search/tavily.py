from tavily import TavilyClient


class TavilySearch:
    def __init__(self, api_key: str):
        self._client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int = 5) -> str:
        resp = self._client.search(query=query, max_results=max_results)
        lines: list[str] = []
        for r in resp.get("results", []):
            title = r.get("title", "")
            url = r.get("url", "")
            content = r.get("content", "")
            lines.append(f"## {title}")
            lines.append(f"URL: {url}")
            lines.append(f"{content}\n")
        return "\n".join(lines) if lines else "No results found."
