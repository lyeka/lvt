# src/
> L2 | Parent: /CLAUDE.md

Source code root. All runtime logic lives here.

## Module Map

| Directory | Purpose |
|-----------|---------|
| `agents/` | LangGraph agent definitions, tools, prompts |
| `service/` | FastAPI REST API backend |
| `client/` | HTTP client for agent service |
| `core/` | Settings, LLM factory |
| `schema/` | Pydantic data models |
| `memory/` | Database checkpointers (SQLite/Postgres/Mongo) |
| `stock_data/` | Financial data APIs |
| `scheduler/` | APScheduler cron automation |
| `pages/` | Streamlit UI pages |

## Entry Points

| File | Purpose |
|------|---------|
| `run_service.py` | FastAPI server startup (port 8080) |
| `streamlit_app.py` | Streamlit app entry (port 8501) |
| `run_client.py` | Client usage examples |
| `run_agent.py` | Direct agent execution |
| `home.py` | Streamlit home page helper |

## Import Conventions

- Relative imports within modules: `from .submodule import X`
- Cross-module imports: `from agents import get_agent`
- Schema is shared: `from schema import ChatMessage, UserInput`

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

