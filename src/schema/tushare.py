from __future__ import annotations

from pydantic import BaseModel, Field


class TushareDailyItem(BaseModel):
    """Structured item for TuShare daily bar data."""

    ts_code: str = Field(description="TS code, e.g., 000001.SZ")
    trade_date: str = Field(description="Trade date in YYYYMMDD format")

    open: float | None = Field(default=None, description="Open price")
    high: float | None = Field(default=None, description="High price")
    low: float | None = Field(default=None, description="Low price")
    close: float | None = Field(default=None, description="Close price")
    pre_close: float | None = Field(default=None, description="Previous close")
    change: float | None = Field(default=None, description="Change amount")
    pct_chg: float | None = Field(default=None, description="Change percent")
    vol: float | None = Field(default=None, description="Volume (hands)")
    amount: float | None = Field(default=None, description="Amount (thousand CNY)")
    # ma5: float | None = Field(default=None, description="5-day moving average")
    # ma10: float | None = Field(default=None, description="10-day moving average")
    # ma20: float | None = Field(default=None, description="20-day moving average")
    # ma60: float | None = Field(default=None, description="60-day moving average")


class TushareDailyResult(BaseModel):
    trade_date: str | None = Field(default=None, description="Requested trade date")
    ts_code: str | None = Field(default=None, description="Requested TS code")
    total: int = Field(description="Total number of returned items")
    items: list[TushareDailyItem] = Field(description="Daily bar records")


class TushareCyqPerfItem(BaseModel):
    """筹码分布及胜率数据项。"""

    ts_code: str = Field(description="TS code, e.g., 600000.SH")
    trade_date: str = Field(description="Trade date in YYYYMMDD format")
    his_low: float = Field(description="Historical lowest price")
    his_high: float = Field(description="Historical highest price")
    cost_5pct: float = Field(description="5% cost price")
    cost_15pct: float = Field(description="15% cost price")
    cost_50pct: float = Field(description="50% cost price (median)")
    cost_85pct: float = Field(description="85% cost price")
    cost_95pct: float = Field(description="95% cost price")
    weight_avg: float = Field(description="Weighted average cost")
    winner_rate: float = Field(description="Winner rate (%)")


class TushareCyqPerfResult(BaseModel):
    """筹码分布及胜率查询结果。"""

    ts_code: str = Field(description="Requested TS code")
    start_date: str = Field(description="Requested start date")
    end_date: str = Field(description="Requested end date")
    total: int = Field(description="Total number of returned items")
    items: list[TushareCyqPerfItem] = Field(description="CYQ performance records")

