# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **TVL** (Trading Vision Lab), an AI agent system for stock trading analysis focused on Chinese A-share markets. The system combines FastAPI backend services with Streamlit frontend interfaces, using LangGraph for agent orchestration.

## Architecture

### Core Components
1. **FastAPI Service** (`src/service/`) - REST API backend on port 8080
   - Agent execution endpoints
   - Chat history management
   - Task scheduling API
   - Entry point: `src/run_service.py`

2. **Streamlit Frontend** (`src/streamlit_app.py`, `src/pages/`) - Web UI on port 8501
   - Trading analysis interface (`pages/trade_analyse.py`)
   - Chart visualization (`pages/chart.py`)
   - Report generation (`pages/report.py`)
   - Task scheduler interface (`pages/scheduler.py`)

3. **Agent System** (`src/agents/`) - AI agent orchestration using LangGraph
   - `trade_agent.py` - Main trading analysis agent
   - `agents.py` - Agent registry and management
   - `bg_task_agent/` - Background task agent
   - `github_mcp_agent/` - GitHub integration agent

4. **Data Layer** (`src/memory/`, `src/stock_data/`)
   - Multiple database backends: SQLite, PostgreSQL, MongoDB
   - Financial data APIs: TuShare, East Money, AKShare, Tencent

5. **Scheduler System** (`src/scheduler/`) - Automated task execution
   - Cron-based scheduling via APScheduler
   - Configuration in `config/scheduler_config.yaml`

### Key Directories
- `src/core/` - Settings and LLM configuration
- `src/schema/` - Pydantic data models
- `src/client/` - API client for service communication
- `config/` - Configuration files
- `data/` - Data storage
- `report/` - Generated analysis reports (markdown)
- `privatecredentials/` - Development credentials (mounted in Docker)

## Development Commands

### Environment Setup
```bash
# Install dependencies with uv (preferred)
uv sync --frozen
source .venv/bin/activate

# Or install minimal client dependencies only
uv sync --frozen --only-group client
```

### Running Services
```bash
# Run FastAPI backend (http://0.0.0.0:8080)
python src/run_service.py

# Run Streamlit frontend (http://localhost:8501)
streamlit run src/streamlit_app.py

# Docker development with hot reload (recommended)
docker compose watch
```

### Testing
```bash
# Unit tests
pytest -q

# Coverage report
pytest --cov=src --cov-report=term-missing

# Docker integration tests (requires docker compose watch running)
pytest -m docker --run-docker
```

### Code Quality
```bash
# Lint and format with Ruff
ruff check . --fix
ruff format .

# Run pre-commit hooks
pre-commit run -a
```

## Docker Configuration

The system uses Docker Compose with three services:
1. **postgres** - PostgreSQL database (port 5432)
2. **agent_service** - FastAPI backend (port 8080)
3. **streamlit_app** - Streamlit frontend (port 8501)

Hot reload is configured for development:
- Agent service watches: `src/agents/`, `src/schema/`, `src/service/`, `src/core/`, `src/memory/`
- Streamlit app watches: `src/client/`, `src/schema/`, `src/streamlit_app.py`

## Key Configuration Files

- `pyproject.toml` - Python dependencies and tool configuration
- `compose.yaml` - Docker Compose setup
- `.env.example` - Environment variable template (copy to `.env`)
- `config/scheduler_config.yaml` - Task scheduler configuration
- `langgraph.json` - LangGraph configuration

## Agent Development

To add a new agent:
1. Place agent code in `src/agents/`
2. Register agent in `src/agents/agents.py` to appear in `/info` endpoint
3. Agent should follow the existing pattern using LangGraph state machines

## Financial Data Sources

The system integrates multiple Chinese financial data sources:
- **TuShare** (`src/stock_data/tushare_api.py`) - Professional financial data
- **East Money** (`src/stock_data/east.py`) - Real-time market data
- **AKShare** (`src/stock_data/ak_share.py`) - Alternative data source
- **Tencent** (`src/stock_data/tx.py`) - Historical data

## Report Generation

Analysis reports are automatically generated in markdown format and saved to `/report/` directory. The system supports:
- Stock selection strategy analysis
- Individual stock analysis
- Sector/industry analysis
- Daily market reports
- Portfolio analysis

## Security Notes

- Never commit real secrets to repository
- Development credentials should be placed in `privatecredentials/` (mounted by Docker)
- Copy `.env.example` to `.env` and configure locally
- API keys for LLM providers (OpenAI, Anthropic, Google, etc.) are required in `.env`

## LLM Configuration

The system supports multiple LLM providers configured via environment variables:
- OpenAI: `OPENAI_API_KEY`, `OPENAI_BASE_URL`
- Anthropic: `ANTHROPIC_API_KEY`
- Google: `GOOGLE_API_KEY`
- DeepSeek: `DEEPSEEK_API_KEY`
- Local models via Ollama: `OLLAMA_BASE_URL`

Configuration is managed in `src/core/llm_config.py`.