import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
# Use OpenAI dynamic alias as sane default; per-provider overrides in registry
MODEL_NAME = os.getenv("MODEL_NAME", "chatgpt-4o-latest")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
BROWSER_TOOL_URL = os.getenv("BROWSER_TOOL_URL", "http://localhost:8081")
PYTHON_REPL_URL = os.getenv("PYTHON_REPL_URL", "http://localhost:8082")

# LLM Provider selection and API keys
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai|anthropic|gemini|mistral|groq

# Provider-specific keys/config
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")  # for Gemini
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
