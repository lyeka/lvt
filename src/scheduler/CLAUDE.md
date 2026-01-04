# scheduler/
> L2 | Parent: src/CLAUDE.md

APScheduler-based cron automation for agent execution.

## Member Files

| File | Purpose |
|------|---------|
| `scheduler.py` | TaskScheduler: job management, hot-reload, UI status exposure |
| `executor.py` | AgentExecutor: async agent invocation, execution records |
| `config.py` | Pydantic models: TaskConfig, SchedulerConfig, YAML loader |
| `__init__.py` | Re-exports |

## Configuration

Tasks defined in `config/scheduler_config.yaml`:

```yaml
scheduler:
  tasks:
    - name: daily_scan
      cron: "0 9 * * 1-5"  # 5-field cron
      agent: trading-agent
      prompt: "/e_v1"
      model: deepseek-chat
      enabled: true
```

## Architecture

```
TaskScheduler
  └── BackgroundScheduler (APScheduler)
  └── AgentExecutor
        └── get_agent() → ainvoke()
        └── ExecutionRecord (status tracking)
```

## Key Operations

```python
scheduler.reload_config()     # Hot-reload YAML
scheduler.trigger_task(name)  # Manual execution
scheduler.get_tasks()         # UI status list
scheduler.start() / pause() / shutdown()
```

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

