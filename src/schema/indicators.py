"""技术指标增强数据模型。"""

from __future__ import annotations

from pydantic import Field

from schema.tushare import TushareDailyItem


class EnhancedDailyItem(TushareDailyItem):
    """
    增强的日线数据，包含派生技术指标。

    继承自 TushareDailyItem，添加以下派生字段：
    - 量能指标：avg_vol_20, vol_ratio_20
    - 均线：ma20, ma60
    - 波动率：atr14
    - 关键位：prev_high_20, prev_low_20
    """

    # 量能指标
    avg_vol_20: float | None = Field(
        default=None,
        description="20日平均成交量（手）。不足20天时使用现有数据的均值。",
    )
    vol_ratio_20: float | None = Field(
        default=None,
        description="量能倍数，当日成交量 / 20日平均成交量。",
    )

    # 均线
    ma20: float | None = Field(
        default=None,
        description="20日均线（收盘价）。不足20天时为 null。",
    )
    ma60: float | None = Field(
        default=None,
        description="60日均线（收盘价）。不足60天时为 null。",
    )

    # 波动率指标
    atr14: float | None = Field(
        default=None,
        description="14日平均真实波幅（ATR）。不足14天时为 null。",
    )

    # 关键位
    prev_high_20: float | None = Field(
        default=None,
        description="前20日最高价（不含当日）。首日为 null。",
    )
    prev_low_20: float | None = Field(
        default=None,
        description="前20日最低价（不含当日）。首日为 null。",
    )


