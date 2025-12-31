#!/usr/bin/env python3
"""
Tushare A股数据客户端
====================

依赖: tushare (pip install tushare)
环境变量: TUSHARE_TOKEN
"""

from __future__ import annotations

import logging
import os

import tushare as ts

from schema.tushare import TushareDailyItem, TushareDailyResult

__all__ = ["TushareClient", "TushareError"]

logger = logging.getLogger(__name__)


class TushareError(Exception):
    """Tushare API 异常基类。"""


class TushareClient:
    """
    TuShare Pro API 客户端。

    Example:
        >>> client = TushareClient()
        >>> result = client.daily(ts_code="000001.SZ")
        >>> print(result.items[0].close)
    """

    def __init__(
        self,
        token: str | None = None,
        timeout: int = 30,
    ) -> None:
        """
        初始化客户端。

        Args:
            token: TuShare Pro Token。默认从环境变量 TUSHARE_TOKEN 读取。
            timeout: API 请求超时时间（秒）。
        """
        self._token = token or os.getenv("TUSHARE_TOKEN")
        if not self._token:
            raise TushareError("未找到 Token，请传入 token 参数或设置环境变量 TUSHARE_TOKEN")

        self._pro = ts.pro_api(token=self._token, timeout=timeout)
        self._timeout = timeout

    def daily(
        self,
        ts_code: str | None = None,
        trade_date: str | None = None,
    ) -> TushareDailyResult:
        """
        获取 A 股日线行情。

        Args:
            ts_code: TS 代码，如 "000001.SZ"。
            trade_date: 交易日，格式 YYYYMMDD。

        Returns:
            结构化的日线行情数据。
        """
        logger.info("获取日线: ts_code=%s, trade_date=%s", ts_code, trade_date)
        try:
            df = self._pro.daily(ts_code=ts_code, trade_date=trade_date)
        except Exception as e:
            raise TushareError(f"获取日线失败: {e}") from e

        records = df.to_dict("records") if df is not None else []
        items = [TushareDailyItem(**rec) for rec in records]
        return TushareDailyResult(
            ts_code=ts_code,
            trade_date=trade_date,
            total=len(items),
            items=items,
        )
