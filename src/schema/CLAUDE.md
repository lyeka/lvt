# schema/
> L2 | Parent: src/CLAUDE.md

Pydantic data models shared across all modules.

## Member Files

| File | Purpose |
|------|---------|
| `schema.py` | API contracts: UserInput, StreamInput, ChatMessage, Feedback, ChatHistory |
| `models.py` | LLM provider enums: OpenAIModelName, AnthropicModelName, etc. → AllModelEnum |
| `stock.py` | Stock data types: StockItem, StockScanResult |
| `tushare.py` | TuShare API response types: TushareDailyItem, TushareCyqPerfItem |
| `akshare.py` | AKShare API response types |
| `indicators.py` | Technical indicator types |
| `task_data.py` | TaskData for background task progress streaming |
| `__init__.py` | Re-exports core API types |

## Key Types

```python
# API Layer
UserInput        # Basic agent invocation request
StreamInput      # Streaming request with stream_tokens flag
ChatMessage      # Unified message format (human/ai/tool/custom)

# LLM Configuration
AllModelEnum     # Union of all provider model enums
Provider         # LLM provider enum

# Stock Data
StockItem        # Single stock with metrics (price, PE, ROE, etc.)
StockScanResult  # Scan result with pagination
TushareDailyItem # Daily OHLCV bar data
```

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

