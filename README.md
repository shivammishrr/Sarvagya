# Sarvagya

Autonomous AI agent. **One API key, one model name. Works with any provider.**

## Quick Start

```bash
pip install -e ".[all]"

# Set credentials
set API_KEY=sk-your-key
set MODEL=gpt-4o

# Run
sarvagya "List all Python files in this project"
```

## Provider Agnostic

Bring your own model. Sarvagya auto-detects the provider from the model name:

```bash
# OpenAI / Groq / any OpenAI-compatible
set API_KEY=sk-...   set MODEL=gpt-4o
sarvagya "explain this codebase"

# Anthropic Claude
set API_KEY=sk-ant-...   set MODEL=claude-sonnet-4-20250514
sarvagya "explain this codebase"

# Gemini (OpenAI-compatible endpoint)
set API_KEY=...   set MODEL=gemini-2.0-flash   set OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
sarvagya "explain this codebase"

# Groq
set API_KEY=gsk_...   set MODEL=llama-3.3-70b-versatile   set OPENAI_BASE_URL=https://api.groq.com/openai/v1
sarvagya "explain this codebase"
```

Or pass `--model` and `--api-key` directly:

```bash
sarvagya "task" --model gpt-4o --api-key sk-...
sarvagya "task" --model claude-sonnet-4-20250514 --api-key sk-ant-...
```

## How Provider Detection Works

- Model name contains **"claude"** or **"anthropic"** → uses `AnthropicAdapter` (Anthropic SDK)
- Everything else → uses `OpenAIAdapter` (OpenAI SDK, compatible with any provider)
- Custom `base_url` can be set via `OPENAI_BASE_URL` env var

## Architecture

**[View interactive architecture diagram →](docs/architecture.html)**

```
sarvagya/
├── core/          Domain types, loop, context, tools (zero external deps)
├── ports/         Interfaces (Protocols)
├── adapters/      Provider implementations (one file per provider)
├── prompts/       Agent identity & rules (markdown)
└── main.py        Composition root
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Design

- **Hexagonal Architecture**: `core/` has zero external dependencies
- **Ports & Adapters**: Swap providers by changing model name, not code
- **One action per iteration**: Simple, observable, debuggable
- **Minimal**: ~1000 lines. Every function ≤30 lines.
- **Prompts as markdown**: Editable without touching code

## Stats

| Metric | Value |
|--------|-------|
| Python files | 17 |
| Total lines | ~1000 |
| External deps | 3 (optional) |
| Tools | 8 |
| Adapters | 5 |
| Protocols | 4 |

## License

MIT
