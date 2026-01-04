# pages/
> L2 | Parent: src/CLAUDE.md

Streamlit UI pages for the trading analysis platform.

## Member Files

| File | Purpose |
|------|---------|
| `trade_analyse.py` | Main trading analysis interface with chat |
| `chart.py` | Stock chart visualization |
| `report.py` | Analysis report viewer |
| `scheduler.py` | Task scheduler management UI |
| `search.py` | Stock search functionality |

## Page Registration

Streamlit auto-discovers pages from this directory. Each file becomes a page in the sidebar navigation.

## Common Patterns

- All pages use `AgentClient` for backend communication
- Session state for conversation persistence
- Async message streaming with progress indicators
- TaskData rendering for background task status

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

