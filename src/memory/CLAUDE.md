# memory/
> L2 | Parent: src/CLAUDE.md

Database backends for LangGraph checkpointing and long-term memory.

## Member Files

| File | Purpose |
|------|---------|
| `__init__.py` | Factory functions: `initialize_database()`, `initialize_store()` |
| `sqlite.py` | SQLite checkpointer + InMemoryStore wrapper |
| `postgres.py` | PostgreSQL checkpointer + store with connection pooling |
| `mongodb.py` | MongoDB checkpointer |

## Backend Selection

Controlled by `DATABASE_TYPE` env var:
- `sqlite` (default): File-based, no setup required
- `postgres`: Production-ready, requires connection config
- `mongo`: Alternative NoSQL backend

## Architecture

```
Checkpointer (short-term memory)
  └── Thread-scoped conversation history
  └── State snapshots for resumption

Store (long-term memory)
  └── Cross-conversation knowledge
  └── User preferences
```

## Connection Pooling (Postgres)

Uses `psycopg_pool.AsyncConnectionPool` with:
- `autocommit=True` (LangGraph requirement)
- `row_factory=dict_row` (LangGraph requirement)
- Configurable min/max pool size

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

