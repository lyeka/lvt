# client/
> L2 | Parent: src/CLAUDE.md

HTTP client for agent service communication.

## Member Files

| File | Purpose |
|------|---------|
| `client.py` | AgentClient: sync/async invoke, stream, history, feedback |
| `__init__.py` | Re-exports: AgentClient, AgentClientError |

## AgentClient API

```python
client = AgentClient(base_url="http://localhost:8080")

# Synchronous
response = client.invoke(message="Hello", model="gpt-4o-mini")

# Streaming (generator)
for msg in client.stream(message="Hello"):
    if isinstance(msg, str):
        print(msg, end="")  # Token
    else:
        print(msg.content)  # ChatMessage

# Async
response = await client.ainvoke(message="Hello")
async for msg in client.astream(message="Hello"):
    ...
```

## Features

- Auto-fetches `/info` on init for agent/model discovery
- Bearer token auth via `AUTH_SECRET` env var
- Thread/user ID support for conversation persistence
- SSE parsing for streaming responses

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

