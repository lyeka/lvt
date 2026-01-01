#!/usr/bin/env python3
"""
AkShare 数据客户端
==================

依赖: akshare (pip install akshare)
"""

from __future__ import annotations

import logging

import akshare as ak

from schema.akshare import (
    IndustryBoardItem,
    IndustryBoardsResult,
    IndustryConstituentItem,
    IndustryConstituentsResult,
    SectorFundFlowItem,
    SectorFundFlowResult,
)

__all__ = ["AkShareClient", "AkShareError"]

logger = logging.getLogger(__name__)


class AkShareError(Exception):
    """AkShare API 异常基类。"""


class AkShareClient:
    """
    AkShare API 客户端。

    Example:
        >>> client = AkShareClient()
        >>> result = client.industry_boards()
        >>> print(f"共 {result.total} 个行业板块")
    """

    def industry_boards(self) -> IndustryBoardsResult:
        """
        获取东方财富行业板块列表。

        Returns:
            行业板块列表数据。
        """
        logger.info("获取行业板块列表")
        try:
            df = ak.stock_board_industry_name_em()
        except Exception as e:
            raise AkShareError(f"获取行业板块列表失败: {e}") from e

        # 根据实际返回字段映射
        items = []
        for _, row in df.iterrows():
            # akshare 返回的字段可能是中文，需要映射
            items.append(
                IndustryBoardItem(
                    board_code=str(row.get("板块代码", row.iloc[0])),
                    board_name=str(row.get("板块名称", row.iloc[1])),
                )
            )

        return IndustryBoardsResult(total=len(items), items=items)

    def industry_constituents(self, symbol: str) -> IndustryConstituentsResult:
        """
        获取指定行业板块的成分股。

        Args:
            symbol: 板块代码，如 "BK0457"。

        Returns:
            行业成分股数据。
        """
        logger.info("获取行业成分股: symbol=%s", symbol)
        try:
            df = ak.stock_board_industry_cons_em(symbol=symbol)
        except Exception as e:
            raise AkShareError(f"获取行业成分股失败: {e}") from e

        items = []
        for _, row in df.iterrows():
            items.append(
                IndustryConstituentItem(
                    stock_code=str(row.get("代码", row.iloc[0])),
                    stock_name=str(row.get("名称", row.iloc[1])),
                )
            )

        return IndustryConstituentsResult(symbol=symbol, total=len(items), items=items)

    def sector_fund_flow_rank(
        self, indicator: str = "今日", sector_type: str = "行业资金流"
    ) -> SectorFundFlowResult:
        """
        获取板块资金流排名。

        Args:
            indicator: 指标周期，可选 "今日"、"5日"、"10日"。
            sector_type: 板块类型，可选 "行业资金流"、"概念资金流"、"地域资金流"。

        Returns:
            板块资金流排名数据。
        """
        logger.info("获取板块资金流: indicator=%s, sector_type=%s", indicator, sector_type)
        try:
            df = ak.stock_sector_fund_flow_rank(indicator=indicator, sector_type=sector_type)
        except Exception as e:
            raise AkShareError(f"获取板块资金流失败: {e}") from e

        items = []
        for idx, row in df.iterrows():
            items.append(
                SectorFundFlowItem(
                    sector_name=str(row.get("名称", row.iloc[0])),
                    rank=int(idx) + 1,  # 使用索引作为排名
                )
            )

        return SectorFundFlowResult(
            indicator=indicator, sector_type=sector_type, total=len(items), items=items
        )
