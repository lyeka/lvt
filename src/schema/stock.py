"""
[INPUT]: 依赖 pydantic 的 BaseModel, Field
[OUTPUT]: 对外提供 StockItem (单只股票数据)
          StockScanResult (扫描结果集，含分页)
[POS]: schema/ 的股票数据模型，定义 EastMoney 扫描结果的结构化类型
       被 stock_data.east 和 agents.trade_agent 使用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class StockItem(BaseModel):
    """Structured stock item returned from EastMoney scans."""

    code: str = Field(description="Security code, e.g. 600519")
    market: str = Field(description="Market short name, e.g. SH, SZ")
    name: str = Field(description="Security short name")

    price: float | None = Field(
        default=None, description="Latest price"
    )
    ma60: float | None = Field(
        default=None, description="60-day moving average"
    )
    change_pct: float | None = Field(
        default=None, description="Change percent for the day"
    )
    market_cap_billion: float | None = Field(
        default=None, description="Total market cap in billions (CNY)"
    )
    pe_dynamic: float | None = Field(default=None, description="Dynamic P/E")
    pe_ttm: float | None = Field(default=None, description="TTM P/E")
    pb: float | None = Field(default=None, description="Price-to-book ratio")
    roe: float | None = Field(default=None, description="Weighted ROE (%)")
    turnover_rate: float | None = Field(
        default=None, description="Turnover rate (%)"
    )
    qrr: float | None = Field(default=None, description="Volume ratio (量比)")
    popularity_rank_change: int | None = Field(
        default=None, description="Popularity rank change"
    )
    guba_top_rank: int | None = Field(
        default=None, description="Guba popularity rank"
    )


class StockScanResult(BaseModel):
    """Structured result for a stock scan (e.g., MA60 breakthrough)."""

    as_of_date: str = Field(description="Date used for dynamic indicators, YYYY-MM-DD")
    total: int = Field(description="Total number of matched items")
    page_no: int = Field(description="Page number queried")
    page_size: int = Field(description="Page size requested")
    items: list[StockItem] = Field(description="List of matched stocks")
