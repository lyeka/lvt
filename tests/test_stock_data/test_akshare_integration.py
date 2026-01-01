"""Integration tests for AkShareClient with real API calls.

这些测试调用真实的 AkShare 免费接口。
可能因网络问题失败，已标记为可跳过。

运行方式: pytest tests/test_stock_data/test_akshare_integration.py -v -s
"""

import pytest

from stock_data.ak_share import AkShareClient, AkShareError

# 标记为可选测试（网络问题可能导致失败）
pytestmark = pytest.mark.skipif(
    False,  # 默认运行，如需跳过改为 True
    reason="AkShare 接口可能因网络问题失败，可手动跳过"
)


class TestAkShareClientIntegration:
    """集成测试：AkShare 免费接口。"""

    def test_industry_boards(self):
        """测试获取行业板块列表。"""
        client = AkShareClient()
        result = client.industry_boards()

        assert result.total > 0
        assert isinstance(result.items, list)
        assert len(result.items) == result.total

        if result.items:
            first_item = result.items[0]
            assert first_item.board_code is not None
            assert first_item.board_name is not None
            print(f"\n获取到 {result.total} 个行业板块")
            print(f"示例: {first_item.board_code} - {first_item.board_name}")

    def test_industry_constituents(self):
        """测试获取行业成分股。"""
        client = AkShareClient()
        
        # 先获取一个板块代码
        boards = client.industry_boards()
        if not boards.items:
            pytest.skip("无法获取板块列表")
        
        symbol = boards.items[0].board_code
        result = client.industry_constituents(symbol=symbol)

        assert result.symbol == symbol
        assert result.total >= 0
        assert isinstance(result.items, list)

        if result.items:
            first_item = result.items[0]
            assert first_item.stock_code is not None
            assert first_item.stock_name is not None
            print(f"\n板块 {symbol} 共有 {result.total} 只成分股")
            print(f"示例: {first_item.stock_code} - {first_item.stock_name}")

    def test_sector_fund_flow_rank_today(self):
        """测试获取今日板块资金流排名。"""
        client = AkShareClient()
        result = client.sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")

        assert result.indicator == "今日"
        assert result.sector_type == "行业资金流"
        assert result.total > 0
        assert isinstance(result.items, list)

        if result.items:
            first_item = result.items[0]
            assert first_item.sector_name is not None
            assert first_item.rank > 0
            print(f"\n今日行业资金流 TOP {result.total}")
            print(f"第1名: {first_item.sector_name}")

    def test_sector_fund_flow_rank_5day(self):
        """测试获取5日板块资金流排名。"""
        client = AkShareClient()
        result = client.sector_fund_flow_rank(indicator="5日", sector_type="概念资金流")

        assert result.indicator == "5日"
        assert result.sector_type == "概念资金流"
        assert result.total > 0

        print(f"\n5日概念资金流 TOP {result.total}")
        if result.items:
            print(f"第1名: {result.items[0].sector_name}")

    def test_client_reuse(self):
        """测试复用同一个 client 实例。"""
        client = AkShareClient()

        # 连续调用多个接口
        boards = client.industry_boards()
        assert boards.total > 0

        if boards.items:
            constituents = client.industry_constituents(symbol=boards.items[0].board_code)
            assert constituents.total >= 0

        fund_flow = client.sector_fund_flow_rank()
        assert fund_flow.total > 0

        print(f"\n客户端复用测试通过")
        print(f"  板块数: {boards.total}")
        print(f"  成分股数: {constituents.total if boards.items else 0}")
        print(f"  资金流排名数: {fund_flow.total}")

    def test_invalid_symbol_raises_error(self):
        """测试无效板块代码会报错。"""
        client = AkShareClient()

        with pytest.raises(AkShareError, match="获取行业成分股失败"):
            client.industry_constituents(symbol="INVALID_CODE_12345")

