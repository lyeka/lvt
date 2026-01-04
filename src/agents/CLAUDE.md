# agents/
> L2 | Parent: src/CLAUDE.md

AI Agent orchestration layer using LangGraph state machines.

## Member Files

| File | Purpose |
|------|---------|
| `agents.py` | Agent registry, `get_agent()`, `get_all_agent_info()`, `DEFAULT_AGENT` |
| `trade_agent.py` | Core trading analysis agent: stock pool → process → LLM analysis → compare |
| `trade_prompts.py` | Prompt templates for trading analysis (single stock, compare stocks) |
| `tools.py` | LangChain tools: Calculator, ChromaDB search |
| `utils.py` | CustomData class for streaming custom messages |
| `lazy_agent.py` | LazyLoadingAgent ABC for async agent initialization |
| `__init__.py` | Re-exports: DEFAULT_AGENT, get_agent, get_all_agent_info, load_agent, AgentGraph |

## Submodules

| Directory | Purpose |
|-----------|---------|
| `bg_task_agent/` | Background task demonstration agent with progress streaming |
| `github_mcp_agent/` | GitHub MCP integration agent (lazy-loaded) |

## Key Types

```python
AgentGraph = CompiledStateGraph | Pregel  # Loaded agent graph
AgentGraphLike = AgentGraph | LazyLoadingAgent  # Registry storage type
```

## Agent Registration

Add new agents by:
1. Create agent file in `agents/` or subdirectory
2. Register in `agents.py` → `agents: dict[str, Agent]`
3. Agent auto-appears in `/info` endpoint

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

