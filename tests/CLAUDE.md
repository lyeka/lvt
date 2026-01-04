# tests/
> L2 | Parent: /CLAUDE.md

Test suite mirroring src/ structure.

## Directory Structure

| Directory | Tests For |
|-----------|-----------|
| `agents/` | Agent loading, lazy agents, GitHub MCP |
| `service/` | API endpoints, streaming, auth, lifespan |
| `client/` | AgentClient functionality |
| `core/` | Settings, LLM factory |
| `app/` | Streamlit app tests |
| `integration/` | Docker E2E tests |
| `test_stock_data/` | Financial data API tests |

## Key Files

| File | Purpose |
|------|---------|
| `conftest.py` | Shared fixtures, env isolation |
| `integration/test_docker_e2e.py` | Full stack tests (requires Docker) |

## Test Commands

```bash
pytest -q                           # Unit tests
pytest --cov=src                    # With coverage
pytest -m docker --run-docker       # Integration tests
pytest -k "test_settings"           # Pattern matching
```

## Markers

- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.docker` - Requires running Docker stack

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

