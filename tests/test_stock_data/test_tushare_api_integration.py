"""Integration tests for TushareClient with real API calls.

这些测试需要真实的 TUSHARE_TOKEN。
会自动从 .env 文件读取，也可以手动设置环境变量。

运行方式: pytest tests/test_stock_data/test_tushare_api_integration.py -v -s
"""

import os

import pytest
from dotenv import find_dotenv, load_dotenv

from stock_data.tushare_api import TushareClient, TushareError

# 加载 .env 文件
load_dotenv(find_dotenv())

# 检查是否有真实 token
pytestmark = pytest.mark.skipif(
    not os.getenv("TUSHARE_TOKEN"),
    reason="需要设置 TUSHARE_TOKEN（在 .env 文件或环境变量中）才能运行集成测试"
)


class TestTushareClientIntegration:
    """集成测试：使用真实 API。"""

    def test_daily_with_specific_stock(self):
        """测试获取特定股票的日线数据。"""
        client = TushareClient()
        result = client.daily(ts_code="000001.SZ")

        # 验证返回结构
        assert result.ts_code == "000001.SZ"
        assert result.total >= 0
        assert isinstance(result.items, list)

        # 如果有数据，验证字段
        if result.items:
            first_item = result.items[0]
            assert first_item.ts_code == "000001.SZ"
            assert first_item.trade_date is not None
            assert isinstance(first_item.close, int | float | type(None))
            print(f"\n获取到 {result.total} 条数据")
            print(f"最新一条: {first_item.trade_date} 收盘价 {first_item.close}")

    def test_daily_with_specific_date(self):
        """测试获取特定日期的市场数据。"""
        client = TushareClient()
        # 使用一个历史交易日
        result = client.daily(trade_date="20241231")

        assert result.trade_date == "20241231"
        assert result.total >= 0
        assert isinstance(result.items, list)

        if result.items:
            print(f"\n20241231 共有 {result.total} 只股票交易")
            print(f"示例: {result.items[0].ts_code} 收盘 {result.items[0].close}")

    def test_daily_with_stock_and_date(self):
        """测试获取特定股票特定日期的数据。"""
        client = TushareClient()
        result = client.daily(ts_code="000001.SZ", trade_date="20241231")

        assert result.ts_code == "000001.SZ"
        assert result.trade_date == "20241231"

        # 这个查询应该最多返回 1 条记录
        assert result.total <= 1

        if result.items:
            item = result.items[0]
            assert item.ts_code == "000001.SZ"
            assert item.trade_date == "20241231"
            print(f"\n000001.SZ 在 20241231 的收盘价: {item.close}")

    def test_daily_no_data_returns_empty(self):
        """测试无数据时返回空列表。"""
        client = TushareClient()
        # 使用一个不存在的股票代码
        result = client.daily(ts_code="999999.SZ")

        assert result.total == 0
        assert result.items == []

    def test_client_reuse(self):
        """测试复用同一个 client 实例。"""
        client = TushareClient()

        # 连续请求多只股票
        stocks = ["000001.SZ", "000002.SZ", "600000.SH"]
        results = []

        for stock in stocks:
            result = client.daily(ts_code=stock)
            results.append(result)

        # 验证都有返回
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.ts_code == stocks[i]
            print(f"\n{stocks[i]}: {result.total} 条数据")

    def test_invalid_token_raises_error(self, monkeypatch):
        """测试无效 token 会报错。"""
        monkeypatch.setenv("TUSHARE_TOKEN", "invalid_token_12345")

        with pytest.raises(TushareError, match="获取日线失败"):
            client = TushareClient()
            client.daily(ts_code="000001.SZ")


class TestCyqPerfIntegration:
    """集成测试：筹码分布 API。
    
    注意：cyq_perf 接口有频率限制（每分钟5次），测试间需要延迟。
    """

    def test_cyq_perf_with_all_params(self):
        """测试指定所有参数获取筹码分布。"""
        client = TushareClient()
        result = client.cyq_perf(
            ts_code="600000.SH", start_date="20241201", end_date="20241231"
        )

        assert result.ts_code == "600000.SH"
        assert result.start_date == "20241201"
        assert result.end_date == "20241231"
        assert result.total >= 0
        assert isinstance(result.items, list)

        if result.items:
            first_item = result.items[0]
            assert first_item.ts_code == "600000.SH"
            assert first_item.trade_date is not None
            assert isinstance(first_item.his_low, float)
            assert isinstance(first_item.his_high, float)
            assert isinstance(first_item.winner_rate, float)
            print(f"\n获取到 {result.total} 条筹码数据")
            print(
                f"最新: {first_item.trade_date} 胜率 {first_item.winner_rate}% "
                f"加权成本 {first_item.weight_avg}"
            )

    def test_cyq_perf_with_default_dates(self):
        """测试使用默认日期（最近60天）。"""
        client = TushareClient()
        result = client.cyq_perf(ts_code="600000.SH")

        assert result.ts_code == "600000.SH"
        assert result.start_date is not None
        assert result.end_date is not None
        assert result.total >= 0

        print(f"\n默认查询: {result.start_date} 到 {result.end_date}")
        print(f"返回 {result.total} 条数据")

    def test_cyq_perf_multiple_stocks(self):
        """测试查询多只股票的筹码分布。"""
        import time

        client = TushareClient()
        stocks = ["600000.SH", "000001.SZ", "600519.SH"]
        results = []

        for stock in stocks:
            result = client.cyq_perf(ts_code=stock, start_date="20241201", end_date="20241231")
            results.append(result)
            time.sleep(13)  # API 限制：每分钟5次，间隔至少12秒

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.ts_code == stocks[i]
            print(f"\n{stocks[i]}: {result.total} 条筹码数据")
            if result.items:
                print(f"  最新胜率: {result.items[0].winner_rate}%")

    def test_cyq_perf_data_fields(self):
        """测试返回数据的所有字段。"""
        client = TushareClient()
        result = client.cyq_perf(ts_code="600000.SH", start_date="20241231", end_date="20241231")

        if result.items:
            item = result.items[0]
            # 验证所有字段都存在
            assert hasattr(item, "ts_code")
            assert hasattr(item, "trade_date")
            assert hasattr(item, "his_low")
            assert hasattr(item, "his_high")
            assert hasattr(item, "cost_5pct")
            assert hasattr(item, "cost_15pct")
            assert hasattr(item, "cost_50pct")
            assert hasattr(item, "cost_85pct")
            assert hasattr(item, "cost_95pct")
            assert hasattr(item, "weight_avg")
            assert hasattr(item, "winner_rate")

            print(f"\n筹码分布详情 ({item.trade_date}):")
            print(f"  历史区间: {item.his_low} - {item.his_high}")
            print(f"  5%-95%成本: {item.cost_5pct} - {item.cost_95pct}")
            print(f"  中位成本: {item.cost_50pct}")
            print(f"  加权成本: {item.weight_avg}")
            print(f"  胜率: {item.winner_rate}%")

