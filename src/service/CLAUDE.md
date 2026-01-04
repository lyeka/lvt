# service/
> L2 | Parent: src/CLAUDE.md

FastAPI REST API backend for agent execution.

## Member Files

| File | Purpose |
|------|---------|
| `service.py` | FastAPI app, endpoints: `/info`, `/invoke`, `/stream`, `/history`, `/feedback`, `/health` |
| `utils.py` | Message conversion: `langchain_to_chat_message()`, `remove_tool_calls()` |
| `__init__.py` | Re-exports `app` for uvicorn import |

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/info` | GET | List agents, models, defaults |
| `/{agent_id}/invoke` | POST | Invoke agent, return final message |
| `/{agent_id}/stream` | POST | SSE stream with tokens + messages |
| `/history` | POST | Get chat history by thread_id |
| `/feedback` | POST | Record feedback to LangSmith |
| `/health` | GET | Health check (includes Langfuse status) |

## Lifespan Management

`lifespan()` async context:
1. Initialize database checkpointer (SQLite/Postgres/Mongo)
2. Initialize memory store
3. Load all agents (including async/lazy agents)
4. Attach checkpointer + store to each agent

## Authentication

Bearer token via `AUTH_SECRET` env var. Optional - if not set, no auth required.

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

