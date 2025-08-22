import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
BROWSER_TOOL_URL = os.getenv("BROWSER_TOOL_URL", "http://localhost:8081")
PYTHON_REPL_URL = os.getenv("PYTHON_REPL_URL", "http://localhost:8082")
