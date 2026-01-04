# TVL (Trading Vision Lab) - AI Agent System for A-Share Trading Analysis
Python 3.11+ | FastAPI + Streamlit + LangGraph | PostgreSQL/SQLite/MongoDB

> L1 Project Constitution | GEB Protocol Enabled

## Directory Structure

```
src/                    # Source code root (9 modules)
├── agents/             # AI Agent orchestration: LangGraph state machines, tools, prompts
├── service/            # FastAPI REST API: endpoints, streaming, auth
├── client/             # HTTP client for service communication
├── core/               # Configuration: settings, LLM factory
├── schema/             # Pydantic data models: API contracts, stock data types
├── memory/             # Database backends: SQLite, PostgreSQL, MongoDB checkpointers
├── stock_data/         # Financial data APIs: TuShare, EastMoney, AKShare, Tencent
├── scheduler/          # APScheduler task automation: cron-based agent execution
├── pages/              # Streamlit UI pages: trading analysis, charts, reports
├── streamlit_app.py    # Frontend entry point (port 8501)
├── run_service.py      # Backend entry point (port 8080)
└── run_client.py       # Client usage examples

tests/                  # Test suite mirroring src/ structure
config/                 # Runtime configuration (scheduler_config.yaml)
docker/                 # Container definitions (Dockerfile.app, Dockerfile.service)
report/                 # Generated analysis reports (markdown, organized by date)
docs/                   # Feature documentation
```

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies, Ruff linting, pytest config |
| `compose.yaml` | Docker services: postgres, agent_service, streamlit_app |
| `.env` / `.env.example` | Environment variables (LLM keys, DB config) |
| `config/scheduler_config.yaml` | Cron task definitions |
| `langgraph.json` | LangGraph agent configuration |

## Entry Points

| Command | Description |
|---------|-------------|
| `python src/run_service.py` | Start FastAPI backend on port 8080 |
| `streamlit run src/streamlit_app.py` | Start Streamlit frontend on port 8501 |
| `docker compose watch` | Development mode with hot reload |
| `pytest -q` | Run unit tests |
| `pytest -m docker --run-docker` | Run integration tests |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Streamlit Frontend (:8501)                 │
│  pages/trade_analyse.py | pages/chart.py | pages/scheduler.py  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP/SSE
┌────────────────────────────────▼────────────────────────────────┐
│                      FastAPI Service (:8080)                    │
│         /invoke | /stream | /history | /feedback | /info       │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                      LangGraph Agents                           │
│   trading_agent (core) | bg_task_agent | github_mcp_agent       │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                      Data Layer                                 │
│   stock_data/* (TuShare/EastMoney) | memory/* (DB checkpoints)  │
└─────────────────────────────────────────────────────────────────┘
```

## LLM Provider Support

OpenAI | Anthropic | Google/VertexAI | DeepSeek | Groq | AWS Bedrock | Ollama | Azure OpenAI | OpenRouter

## Development Commands

```bash
# Environment
uv sync --frozen && source .venv/bin/activate

# Code Quality
ruff check . --fix && ruff format .
pre-commit run -a

# Testing
pytest --cov=src --cov-report=term-missing
```

---

[PROTOCOL]: 变更时更新此头部，然后检查各模块 CLAUDE.md
