#!/usr/bin/env python3
"""
技术指标计算模块
================

提供基于日线数据的技术指标计算功能，包括：
- 量能指标（均量、量能倍数）
- 均线（MA20, MA60）
- 波动率指标（ATR14）
- 关键位（前N日高低点）

Example:
    >>> from stock_data.tushare_api import TushareClient
    >>> from stock_data.indicators import calculate_indicators
    >>>
    >>> client = TushareClient()
    >>> result = client.daily(ts_code="000001.SZ")
    >>> enhanced = calculate_indicators(result.items)
    >>> print(enhanced[0].ma20, enhanced[0].atr14)
"""

from __future__ import annotations

import logging
from typing import Literal

from schema.indicators import EnhancedDailyItem
from schema.tushare import TushareDailyItem

__all__ = ["calculate_indicators", "IndicatorsError"]

logger = logging.getLogger(__name__)


class IndicatorsError(Exception):
    """技术指标计算异常。"""


def calculate_indicators(
    items: list[TushareDailyItem],
    *,
    ma_windows: list[int] | None = None,
    vol_window: int = 20,
    atr_window: int = 14,
    atr_method: Literal["sma", "wilder"] = "sma",
    prev_hl_window: int = 20,
) -> list[EnhancedDailyItem]:
    """
    计算技术指标并返回增强的日线数据。

    自动按 trade_date 升序排序数据（旧→新）。

    Args:
        items: 原始日线数据列表。
        ma_windows: 均线窗口列表，默认 [20, 60]。
        vol_window: 均量窗口，默认 20。
        atr_window: ATR 窗口，默认 14。
        atr_method: ATR 计算方法，'sma' 或 'wilder'，默认 'sma'。
        prev_hl_window: 前N日高低点窗口，默认 20。

    Returns:
        增强后的日线数据列表（按时间升序）。

    Raises:
        IndicatorsError: 数据为空或计算失败。

    Example:
        >>> enhanced = calculate_indicators(
        ...     items,
        ...     ma_windows=[20, 60],
        ...     atr_method="wilder"
        ... )
    """
    if not items:
        raise IndicatorsError("输入数据为空")

    if ma_windows is None:
        ma_windows = [20, 60]

    # 1. 排序：按 trade_date 升序（旧→新）
    sorted_items = sorted(items, key=lambda x: x.trade_date)
    logger.info(
        "开始计算技术指标: 数据量=%d, 日期范围=%s~%s",
        len(sorted_items),
        sorted_items[0].trade_date,
        sorted_items[-1].trade_date,
    )

    # 2. 提取基础数据
    closes = [item.close for item in sorted_items]
    highs = [item.high for item in sorted_items]
    lows = [item.low for item in sorted_items]
    vols = [item.vol for item in sorted_items]

    # 3. 计算各项指标
    avg_vols = _calculate_avg_vol(vols, vol_window)
    vol_ratios = _calculate_vol_ratio(vols, avg_vols)
    mas = {window: _calculate_ma(closes, window) for window in ma_windows}
    atrs = _calculate_atr(highs, lows, closes, atr_window, method=atr_method)
    prev_highs = _calculate_prev_high_low(highs, prev_hl_window, is_high=True)
    prev_lows = _calculate_prev_high_low(lows, prev_hl_window, is_high=False)

    # 4. 组装增强数据
    enhanced_items = []
    for i, item in enumerate(sorted_items):
        # 动态获取 MA 值（如果窗口存在）
        ma20_value = mas.get(20, [None] * len(sorted_items))[i] if 20 in mas else None
        ma60_value = mas.get(60, [None] * len(sorted_items))[i] if 60 in mas else None

        enhanced = EnhancedDailyItem(
            **item.model_dump(),
            avg_vol_20=avg_vols[i],
            vol_ratio_20=vol_ratios[i],
            ma20=ma20_value,
            ma60=ma60_value,
            atr14=atrs[i],
            prev_high_20=prev_highs[i],
            prev_low_20=prev_lows[i],
        )
        enhanced_items.append(enhanced)

    logger.info("技术指标计算完成")
    return enhanced_items


def _calculate_avg_vol(vols: list[float | None], window: int) -> list[float | None]:
    """
    计算均量。

    策略：不足窗口时使用现有数据的均值（partial）。

    Args:
        vols: 成交量列表。
        window: 窗口大小。

    Returns:
        均量列表。
    """
    result = []
    for i in range(len(vols)):
        # 取 [max(0, i-window+1), i+1] 范围的数据
        start = max(0, i - window + 1)
        window_vols = [v for v in vols[start : i + 1] if v is not None]

        if window_vols:
            result.append(sum(window_vols) / len(window_vols))
        else:
            result.append(None)

    return result


def _calculate_vol_ratio(
    vols: list[float | None], avg_vols: list[float | None]
) -> list[float | None]:
    """
    计算量能倍数。

    Args:
        vols: 成交量列表。
        avg_vols: 均量列表。

    Returns:
        量能倍数列表。
    """
    result = []
    for vol, avg_vol in zip(vols, avg_vols):
        if vol is not None and avg_vol is not None and avg_vol > 0:
            result.append(vol / avg_vol)
        else:
            result.append(None)
    return result


def _calculate_ma(prices: list[float | None], window: int) -> list[float | None]:
    """
    计算移动平均线。

    策略：不足窗口时置 null。

    Args:
        prices: 价格列表（通常是收盘价）。
        window: 窗口大小。

    Returns:
        均线列表。
    """
    result = []
    for i in range(len(prices)):
        if i < window - 1:
            # 数据不足窗口
            result.append(None)
        else:
            window_prices = [p for p in prices[i - window + 1 : i + 1] if p is not None]
            if len(window_prices) == window:
                result.append(sum(window_prices) / window)
            else:
                # 窗口内有缺失值
                result.append(None)

    return result


def _calculate_atr(
    highs: list[float | None],
    lows: list[float | None],
    closes: list[float | None],
    window: int,
    method: Literal["sma", "wilder"] = "sma",
) -> list[float | None]:
    """
    计算平均真实波幅（ATR）。

    Args:
        highs: 最高价列表。
        lows: 最低价列表。
        closes: 收盘价列表。
        window: 窗口大小。
        method: 计算方法，'sma' 或 'wilder'。

    Returns:
        ATR 列表。
    """
    # 1. 计算 TR (True Range)
    trs = []
    for i in range(len(highs)):
        high = highs[i]
        low = lows[i]
        close = closes[i]
        prev_close = closes[i - 1] if i > 0 else None

        if high is None or low is None or close is None:
            trs.append(None)
            continue

        if prev_close is None:
            # 第一天：TR = high - low
            tr = high - low
        else:
            # TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))

        trs.append(tr)

    # 2. 计算 ATR
    if method == "sma":
        return _calculate_atr_sma(trs, window)
    elif method == "wilder":
        return _calculate_atr_wilder(trs, window)
    else:
        raise IndicatorsError(f"不支持的 ATR 方法: {method}")


def _calculate_atr_sma(trs: list[float | None], window: int) -> list[float | None]:
    """
    使用简单移动平均计算 ATR。

    策略：不足窗口时置 null。
    """
    result = []
    for i in range(len(trs)):
        if i < window - 1:
            result.append(None)
        else:
            window_trs = [tr for tr in trs[i - window + 1 : i + 1] if tr is not None]
            if len(window_trs) == window:
                result.append(sum(window_trs) / window)
            else:
                result.append(None)

    return result


def _calculate_atr_wilder(trs: list[float | None], window: int) -> list[float | None]:
    """
    使用 Wilder 指数平滑计算 ATR。

    公式：ATR[t] = (ATR[t-1] * (window-1) + TR[t]) / window

    策略：前 window 天使用 SMA 初始化，之后使用 Wilder 平滑。
    """
    result = []
    atr_prev = None

    for i in range(len(trs)):
        if i < window - 1:
            # 数据不足
            result.append(None)
        elif i == window - 1:
            # 第 window 天：使用 SMA 初始化
            window_trs = [tr for tr in trs[: i + 1] if tr is not None]
            if len(window_trs) == window:
                atr_prev = sum(window_trs) / window
                result.append(atr_prev)
            else:
                result.append(None)
        else:
            # 之后：使用 Wilder 平滑
            tr = trs[i]
            if tr is not None and atr_prev is not None:
                atr_prev = (atr_prev * (window - 1) + tr) / window
                result.append(atr_prev)
            else:
                result.append(None)
                atr_prev = None  # 重置

    return result


def _calculate_prev_high_low(
    prices: list[float | None], window: int, is_high: bool
) -> list[float | None]:
    """
    计算前N日最高价或最低价（不含当日）。

    Args:
        prices: 价格列表（高价或低价）。
        window: 窗口大小。
        is_high: True 表示计算最高价，False 表示最低价。

    Returns:
        前N日高低点列表。
    """
    result = []
    for i in range(len(prices)):
        if i == 0:
            # 第一天无前值
            result.append(None)
        else:
            # 取 [max(0, i-window), i) 范围的数据（不含当日）
            start = max(0, i - window)
            window_prices = [p for p in prices[start:i] if p is not None]

            if window_prices:
                result.append(max(window_prices) if is_high else min(window_prices))
            else:
                result.append(None)

    return result
