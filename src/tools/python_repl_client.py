from typing import Any, Dict, Optional
import httpx
from ..config import env


class PythonReplClient:
    """Simple HTTP client for the Python REPL service.

    Reads base URL from env.PYTHON_REPL_URL. Provides exec(code) method.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 15.0) -> None:
        self.base_url = (base_url or env.PYTHON_REPL_URL).rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=self.timeout)

    def exec(self, code: str) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/exec"
        resp = self._client.post(endpoint, json={"code": code})
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PythonReplClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
