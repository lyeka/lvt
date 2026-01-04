#!/usr/bin/env python3
"""
技术指标计算示例
================

演示如何使用 indicators 模块计算技术指标。
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from stock_data.indicators import calculate_indicators
from stock_data.tushare_api import TushareClient


def example_basic():
    """基础示例：获取日线数据并计算指标。"""
    print("=" * 60)
    print("示例 1: 基础用法")
    print("=" * 60)

    # 1. 获取原始数据
    client = TushareClient()
    result = client.daily(ts_code="000001.SZ")

    print(f"获取到 {result.total} 条日线数据")
    print(f"日期范围: {result.items[-1].trade_date} ~ {result.items[0].trade_date}")

    # 2. 计算技术指标
    enhanced = calculate_indicators(result.items)

    # 3. 查看最新数据
    latest = enhanced[-1]  # 最新一天
    print(f"\n最新数据 ({latest.trade_date}):")
    print(f"  收盘价: {latest.close}")
    print(f"  成交量: {latest.vol} 手")
    print(f"  20日均量: {latest.avg_vol_20:.2f} 手" if latest.avg_vol_20 else "  20日均量: N/A")
    print(
        f"  量能倍数: {latest.vol_ratio_20:.2f}x" if latest.vol_ratio_20 else "  量能倍数: N/A"
    )
    print(f"  MA20: {latest.ma20:.2f}" if latest.ma20 else "  MA20: N/A")
    print(f"  MA60: {latest.ma60:.2f}" if latest.ma60 else "  MA60: N/A")
    print(f"  ATR14: {latest.atr14:.2f}" if latest.atr14 else "  ATR14: N/A")
    print(
        f"  前20日最高: {latest.prev_high_20:.2f}" if latest.prev_high_20 else "  前20日最高: N/A"
    )
    print(
        f"  前20日最低: {latest.prev_low_20:.2f}" if latest.prev_low_20 else "  前20日最低: N/A"
    )


def example_custom_params():
    """自定义参数示例。"""
    print("\n" + "=" * 60)
    print("示例 2: 自定义参数")
    print("=" * 60)

    client = TushareClient()
    result = client.daily(ts_code="600519.SH")

    # 使用 Wilder 方法计算 ATR，自定义均线窗口
    enhanced = calculate_indicators(
        result.items,
        ma_windows=[5, 10, 20, 60],  # 多个均线
        vol_window=30,  # 30日均量
        atr_window=20,  # 20日 ATR
        atr_method="wilder",  # Wilder 平滑
        prev_hl_window=30,  # 前30日高低点
    )

    latest = enhanced[-1]
    print(f"\n{latest.ts_code} 最新数据 ({latest.trade_date}):")
    print(f"  收盘价: {latest.close}")
    print(f"  MA20: {latest.ma20:.2f}" if latest.ma20 else "  MA20: N/A")
    print(f"  MA60: {latest.ma60:.2f}" if latest.ma60 else "  MA60: N/A")
    print(f"  ATR(Wilder): {latest.atr14:.2f}" if latest.atr14 else "  ATR: N/A")


def example_analysis():
    """分析示例：识别突破和放量。"""
    print("\n" + "=" * 60)
    print("示例 3: 简单分析")
    print("=" * 60)

    client = TushareClient()
    result = client.daily(ts_code="000001.SZ")
    enhanced = calculate_indicators(result.items)

    # 找出最近10天的放量突破
    print("\n最近10天的放量日（量能倍数 > 2）:")
    for item in enhanced[-10:]:
        if item.vol_ratio_20 and item.vol_ratio_20 > 2.0:
            breakthrough = ""
            if item.prev_high_20 and item.close and item.close > item.prev_high_20:
                breakthrough = " [突破前20日高点]"

            print(
                f"  {item.trade_date}: 量能倍数 {item.vol_ratio_20:.2f}x, "
                f"收盘 {item.close:.2f}{breakthrough}"
            )


if __name__ == "__main__":
    try:
        example_basic()
        example_custom_params()
        example_analysis()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()



