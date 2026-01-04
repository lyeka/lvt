# bg_task_agent/
> L2 | Parent: src/agents/CLAUDE.md

Background task demonstration agent with progress streaming.

## Member Files

| File | Purpose |
|------|---------|
| `bg_task_agent.py` | Agent graph: bg_task → model, exports `bg_task_agent` |
| `task.py` | Task class: state machine (new→running→complete), StreamWriter dispatch |

## Task State Machine

```
new → running → complete
         └──→ (result: success | error)
```

## Usage Pattern

```python
task = Task("task_name", writer)
task.start(data={...})          # state = new
task.write_data(data={...})     # state = running
task.finish(result="success")   # state = complete
```

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

