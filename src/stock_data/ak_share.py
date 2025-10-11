from __future__ import annotations

import akshare as ak
import pandas as pd


class AkShareStockData:
    """
    封装对 akshare 行业板块相关接口的简单调用。

    - `get_industry_boards`: 获取行业板块列表
    - `get_industry_constituents`: 获取指定行业板块的成分股
    """

    @classmethod
    def get_industry_boards(cls) -> pd.DataFrame:
        """获取东方财富行业板块列表。"""
        return ak.stock_board_industry_name_em()

    @classmethod
    def get_industry_constituents(cls, symbol: str) -> pd.DataFrame:
        """获取指定行业板块的成分股。

        参数
        - symbol: 行业板块代码，例如 "BK0457"
        """
        return ak.stock_board_industry_cons_em(symbol=symbol)

    @classmethod
    def stock_sector_fund_flow_rank(cls, indicator: str,sector_type: str) -> pd.DataFrame:
        """
        args:
            indicator: 默认="今日"; choice of {"今日", "5日", "10日"}
            sector_type: 默认="行业资金流"; choice of {"行业资金流", "概念资金流", "地域资金流"}

        """
        return ak.stock_sector_fund_flow_rank(indicator=indicator,sector_type=sector_type)


if __name__ == "__main__":
    # 示例：打印前 5 条行业板块与指定板块成分股情况
    industry_boards = AkShareStockData.get_industry_boards()
    print(len(industry_boards))

    # cons = AkShareStockData.get_industry_constituents(symbol="BK0457")
    # print(len(cons))
    # print(cons[:5])

    # fund_flow = AkShareStockData.stock_sector_fund_flow_rank(indicator="今日",sector_type="行业资金流")
    # print(fund_flow[:5])

