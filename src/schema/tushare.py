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

