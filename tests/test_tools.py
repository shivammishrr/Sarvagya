import os
from src.tools.browser_client import BrowserClient
from src.tools.python_repl_client import PythonReplClient


def test_browser_client_base_url(monkeypatch):
    monkeypatch.setenv("BROWSER_TOOL_URL", "http://localhost:18081/")
    c = BrowserClient()
    assert c.base_url == "http://localhost:18081"
    c.close()


def test_python_repl_client_base_url(monkeypatch):
    monkeypatch.setenv("PYTHON_REPL_URL", "http://localhost:18082/")
    c = PythonReplClient()
    assert c.base_url == "http://localhost:18082"
    c.close()
