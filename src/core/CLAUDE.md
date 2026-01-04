# core/
> L2 | Parent: src/CLAUDE.md

Application configuration and LLM factory.

## Member Files

| File | Purpose |
|------|---------|
| `settings.py` | Pydantic Settings: env vars, provider detection, model availability |
| `llm.py` | LLM factory: `get_model(name) → ModelT`, provider-specific instantiation |
| `__init__.py` | Re-exports: `settings`, `get_model` |

## Settings Overview

```python
settings.HOST / settings.PORT      # Server binding
settings.DATABASE_TYPE             # sqlite | postgres | mongo
settings.DEFAULT_MODEL             # Auto-detected from available providers
settings.AVAILABLE_MODELS          # Set of configured model enums
```

## LLM Factory

`get_model()` returns cached model instances based on provider:

| Provider | Model Class | Config |
|----------|-------------|--------|
| OpenAI | ChatOpenAI | `OPENAI_API_KEY` |
| Anthropic | ChatAnthropic | `ANTHROPIC_API_KEY` |
| Google | ChatGoogleGenerativeAI | `GOOGLE_API_KEY` |
| DeepSeek | ChatOpenAI (custom base) | `DEEPSEEK_API_KEY` |
| Ollama | ChatOllama | `OLLAMA_MODEL`, `OLLAMA_BASE_URL` |
| Azure | AzureChatOpenAI | `AZURE_OPENAI_*` |

## Auto-Detection

On startup, `model_post_init()` scans for configured API keys and:
1. Populates `AVAILABLE_MODELS` with corresponding enums
2. Sets `DEFAULT_MODEL` to first available provider

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

