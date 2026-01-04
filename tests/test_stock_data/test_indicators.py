"""技术指标计算模块测试。"""

from __future__ import annotations

import pytest

from schema.tushare import TushareDailyItem
from stock_data.indicators import IndicatorsError, calculate_indicators


@pytest.fixture
def sample_daily_data() -> list[TushareDailyItem]:
    """创建测试用的日线数据（30天）。"""
    items = []
    base_price = 10.0

    for i in range(30):
        date = f"202401{i + 1:02d}"
        # 模拟价格波动
        close = base_price + (i % 5) * 0.5
        high = close + 0.3
        low = close - 0.3
        vol = 10000.0 + (i % 3) * 5000.0

        item = TushareDailyItem(
            ts_code="000001.SZ",
            trade_date=date,
            open=close - 0.1,
            high=high,
            low=low,
            close=close,
            pre_close=close - 0.2,
            change=0.2,
            pct_chg=2.0,
            vol=vol,
            amount=vol * close / 10,  # 千元
        )
        items.append(item)

    return items


def test_calculate_indicators_basic(sample_daily_data):
    """测试基础指标计算。"""
    enhanced = calculate_indicators(sample_daily_data)

    assert len(enhanced) == 30
    assert enhanced[0].ts_code == "000001.SZ"

    # 检查最后一天的数据
    latest = enhanced[-1]
    assert latest.avg_vol_20 is not None
    assert latest.vol_ratio_20 is not None
    assert latest.ma20 is not None
    assert latest.ma60 is None  # 只有30天数据
    assert latest.atr14 is not None
    assert latest.prev_high_20 is not None
    assert latest.prev_low_20 is not None


def test_calculate_indicators_sorting(sample_daily_data):
    """测试自动排序功能。"""
    # 倒序输入
    reversed_data = list(reversed(sample_daily_data))
    enhanced = calculate_indicators(reversed_data)

    # 应该按日期升序输出
    assert enhanced[0].trade_date < enhanced[-1].trade_date
    for i in range(len(enhanced) - 1):
        assert enhanced[i].trade_date < enhanced[i + 1].trade_date


def test_calculate_indicators_empty():
    """测试空数据输入。"""
    with pytest.raises(IndicatorsError, match="输入数据为空"):
        calculate_indicators([])


def test_avg_vol_partial_fill(sample_daily_data):
    """测试均量的 partial fill 策略。"""
    # 只取前10天
    enhanced = calculate_indicators(sample_daily_data[:10])

    # 第1天应该有均量（使用自身）
    assert enhanced[0].avg_vol_20 is not None
    assert enhanced[0].avg_vol_20 == enhanced[0].vol

    # 第10天应该有均量（使用前10天的均值）
    assert enhanced[9].avg_vol_20 is not None


def test_ma_null_when_insufficient(sample_daily_data):
    """测试均线在数据不足时置 null。"""
    # 只取前15天
    enhanced = calculate_indicators(sample_daily_data[:15])

    # MA20 应该全部为 null（不足20天）
    for item in enhanced:
        assert item.ma20 is None

    # MA60 也应该全部为 null
    for item in enhanced:
        assert item.ma60 is None


def test_ma_calculation(sample_daily_data):
    """测试均线计算正确性。"""
    enhanced = calculate_indicators(sample_daily_data)

    # 第20天应该有 MA20
    assert enhanced[19].ma20 is not None

    # 手动计算验证
    closes = [item.close for item in sample_daily_data[:20]]
    expected_ma20 = sum(closes) / 20
    assert abs(enhanced[19].ma20 - expected_ma20) < 0.001


def test_atr_sma_method(sample_daily_data):
    """测试 ATR SMA 方法。"""
    enhanced = calculate_indicators(sample_daily_data, atr_method="sma")

    # 前13天应该没有 ATR
    for i in range(13):
        assert enhanced[i].atr14 is None

    # 第14天开始应该有 ATR
    assert enhanced[13].atr14 is not None
    assert enhanced[13].atr14 > 0


def test_atr_wilder_method(sample_daily_data):
    """测试 ATR Wilder 方法。"""
    enhanced = calculate_indicators(sample_daily_data, atr_method="wilder")

    # 前13天应该没有 ATR
    for i in range(13):
        assert enhanced[i].atr14 is None

    # 第14天开始应该有 ATR
    assert enhanced[13].atr14 is not None
    assert enhanced[13].atr14 > 0

    # Wilder 方法应该更平滑（后续值变化较小）
    atr_changes = []
    for i in range(14, len(enhanced) - 1):
        if enhanced[i].atr14 and enhanced[i + 1].atr14:
            change = abs(enhanced[i + 1].atr14 - enhanced[i].atr14)
            atr_changes.append(change)

    # 平均变化应该较小
    avg_change = sum(atr_changes) / len(atr_changes) if atr_changes else 0
    assert avg_change < 0.5  # 根据测试数据调整阈值


def test_prev_high_low(sample_daily_data):
    """测试前N日高低点计算。"""
    enhanced = calculate_indicators(sample_daily_data, prev_hl_window=5)

    # 第1天应该没有前值
    assert enhanced[0].prev_high_20 is None
    assert enhanced[0].prev_low_20 is None

    # 第2天开始应该有前值
    assert enhanced[1].prev_high_20 is not None
    assert enhanced[1].prev_low_20 is not None

    # 验证第6天的前5日高低点
    highs = [item.high for item in sample_daily_data[:5]]
    lows = [item.low for item in sample_daily_data[:5]]
    assert enhanced[5].prev_high_20 == max(highs)
    assert enhanced[5].prev_low_20 == min(lows)


def test_vol_ratio_calculation(sample_daily_data):
    """测试量能倍数计算。"""
    enhanced = calculate_indicators(sample_daily_data)

    # 所有有成交量的日期都应该有量能倍数
    for item in enhanced:
        if item.vol and item.avg_vol_20:
            assert item.vol_ratio_20 is not None
            assert item.vol_ratio_20 == item.vol / item.avg_vol_20


def test_custom_windows(sample_daily_data):
    """测试自定义窗口参数。"""
    enhanced = calculate_indicators(
        sample_daily_data,
        ma_windows=[5, 10],
        vol_window=10,
        atr_window=7,
        prev_hl_window=10,
    )

    # 自定义窗口不包含 20 和 60，所以 ma20 和 ma60 应该为 None
    latest = enhanced[-1]
    assert latest.ma20 is None  # 未计算 20 日均线
    assert latest.ma60 is None  # 未计算 60 日均线
    assert latest.atr14 is not None  # 实际是 7 日 ATR（字段名固定）
    assert latest.avg_vol_20 is not None  # 实际是 10 日均量（字段名固定）


def test_handle_none_values():
    """测试处理 None 值的情况。"""
    items = [
        TushareDailyItem(
            ts_code="000001.SZ",
            trade_date="20240101",
            open=10.0,
            high=None,  # 缺失值
            low=9.8,
            close=10.0,
            vol=10000.0,
        ),
        TushareDailyItem(
            ts_code="000001.SZ",
            trade_date="20240102",
            open=10.1,
            high=10.5,
            low=10.0,
            close=10.2,
            vol=12000.0,
        ),
    ]

    enhanced = calculate_indicators(items)

    # 应该能正常处理，不抛出异常
    assert len(enhanced) == 2
    assert enhanced[0].atr14 is None  # 因为有缺失值
