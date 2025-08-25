from typing import Any, Dict, Optional
import httpx
from ..config import env


class BrowserClient:
    """Simple HTTP client for the Browser Tool service.

    Reads base URL from env.BROWSER_TOOL_URL. Provides browse(url) method.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 15.0) -> None:
        self.base_url = (base_url or env.BROWSER_TOOL_URL).rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=self.timeout)

    def browse(self, url: str, max_chars: int = 2000) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/browse"
        resp = self._client.post(endpoint, json={"url": url, "max_chars": max_chars})
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BrowserClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
