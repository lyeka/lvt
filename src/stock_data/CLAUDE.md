# stock_data/
> L2 | Parent: src/CLAUDE.md

Financial data APIs for Chinese A-share markets.

## Member Files

| File | Purpose |
|------|---------|
| `east.py` | EastMoney API: MA60 breakthrough scans, `get_ma60_stocks_structured()` |
| `tushare_api.py` | TuShare Pro client: daily bars, chip distribution |
| `ak_share.py` | AKShare client: alternative data source |
| `tx.py` | Tencent historical data |
| `indicators.py` | Technical indicator calculations |
| `common.py` | Shared utilities |
| `__init__.py` | Re-exports: EastMoneyAPI, TushareClient |
| `README.md` | API documentation |
| `INDICATORS_README.md` | Technical indicators documentation |

## Primary Data Sources

| Source | Use Case | Auth |
|--------|----------|------|
| EastMoney | Real-time scans, stock selection | None |
| TuShare | Daily OHLCV, chip distribution | `TUSHARE_TOKEN` env |
| AKShare | Supplementary data | None |
| Tencent | Historical prices | None |

## Key Functions

```python
# EastMoney
get_ma60_stocks_structured() → StockScanResult  # MA60 breakthrough stocks

# TuShare
TushareClient().daily(ts_code="000001.SZ") → TushareDailyResult
TushareClient().cyq_perf(ts_code) → TushareCyqPerfResult  # Chip distribution
```

---

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

