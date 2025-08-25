from typing import Any, Dict, Optional
import httpx
from ..config import env


class TavilyClient:
    """Minimal client for Tavily search API.

    Docs: https://docs.tavily.com/ (subject to change)
    Expects TAVILY_API_KEY in environment.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: float = 15.0) -> None:
        self.api_key = (api_key or env.TAVILY_API_KEY).strip()
        self.timeout = timeout
        self.base_url = "https://api.tavily.com"  # default public endpoint
        self._client = httpx.Client(timeout=self.timeout)

    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("TAVILY_API_KEY is not set")
        url = f"{self.base_url}/search"
        payload = {"query": query, "max_results": max_results}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        resp = self._client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TavilyClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
