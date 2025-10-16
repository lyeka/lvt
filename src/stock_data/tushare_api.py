#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tushare A股日线行情封装
======================

按照 east.py 的风格，提供简洁稳定的 TuShare SDK 调用封装。

依赖:
- tushare (pip install tushare)

环境变量:
- TUSHARE_TOKEN: TuShare Pro API Token
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv, find_dotenv


env_path = find_dotenv()
load_dotenv(env_path)



@dataclass
class TushareConfig:
    token: Optional[str] = None
    # 预留可扩展配置


class TushareAPI:
    """TuShare SDK 简洁封装。"""

    def __init__(self, config: Optional[TushareConfig] = None) -> None:
        self.config = config or TushareConfig()
        self.logger = self._setup_logger()
        self._pro = None

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _ensure_client(self) -> Any:
        """确保已初始化 TuShare Pro 客户端。"""
        if self._pro is not None:
            return self._pro

        try:
            import tushare as ts  # type: ignore
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "未安装 tushare，请先执行: pip install tushare"
            ) from e

        token = self.config.token or os.getenv("TUSHARE_TOKEN")
        if not token:
            raise EnvironmentError(
                "未找到 TUSHARE_TOKEN，请在环境变量或 .env 中配置 TuShare Pro Token"
            )

        ts.set_token(token)
        self._pro = ts.pro_api()
        return self._pro

    # ----------------------------------------------------------------------------
    # 对外方法
    # ----------------------------------------------------------------------------
    def get_daily_by_date(
        self, trade_date: str, ts_code: str
    ) -> Dict[str, Any]:
        """
        获取指定交易日的 A 股日线行情。

        Args:
            trade_date: 交易日，格式 YYYYMMDD，如 "20241008"
            limit: 每次返回数量，TuShare 默认支持 limit/offset 分页
            offset: 偏移量

        Returns:
            字典，包含 trade_date、total、items(list[dict]) 三部分
        """
        pro = self._ensure_client()

        # TuShare daily 接口：
        # https://tushare.pro/document/2?doc_id=27
        # 参数：ts_code, trade_date,
        self.logger.info(
            "获取日线行情: trade_date=%s, ts_code=%s", trade_date, ts_code
        )

        try:
            df = pro.daily(trade_date=trade_date, ts_code=ts_code)
        except Exception as e:  # noqa: BLE001
            self.logger.error("TuShare 请求失败: %s", e)
            raise

        # DataFrame -> List[Dict]
        try:
            items: List[Dict[str, Any]] = df.to_dict("records") if df is not None else []
            total = len(items)
        except Exception as e:  # noqa: BLE001
            self.logger.error("数据解析失败: %s", e)
            raise

        return {
            "trade_date": trade_date,
            "total": total,
            "items": items,
        }


# ----------------------------------------------------------------------------
# 便捷函数
# ----------------------------------------------------------------------------


def get_a_daily(
    trade_date: str, ts_code: str
) -> Dict[str, Any]:
    """便捷函数：获取某个交易日的 A 股日线行情。"""
    api = TushareAPI()
    return api.get_daily_by_date(trade_date=trade_date, ts_code=ts_code)


def get_a_daily_structured(
    trade_date: str | None = None, ts_code: str | None = None
) -> "TushareDailyResult":
    """
    获取结构化的 A 股日线行情（Pydantic 模型）。

    Args:
        trade_date: 交易日 YYYYMMDD，可为空（遵循 TuShare daily 行为）
        ts_code: TS 代码，如 000001.SZ，可为空

    Returns:
        TushareDailyResult: 结构化的日线数据
    """
    # 延迟导入以支持直接运行此文件 (__main__) 时的路径问题
    try:
        from schema.tushare import TushareDailyItem, TushareDailyResult  # type: ignore
    except ModuleNotFoundError:
        import os as _os
        import sys as _sys

        _sys.path.append(_os.path.dirname(_os.path.dirname(__file__)))  # add src/
        from schema.tushare import TushareDailyItem, TushareDailyResult  # type: ignore

    api = TushareAPI()
    pro = api._ensure_client()

    try:
        df = pro.daily(trade_date=trade_date, ts_code=ts_code)
    except Exception as e:  # noqa: BLE001
        api.logger.error("TuShare 请求失败: %s", e)
        raise

    try:
        records: List[Dict[str, Any]] = df.to_dict("records") if df is not None else []
    except Exception as e:  # noqa: BLE001
        api.logger.error("数据解析失败: %s", e)
        raise

    items = [TushareDailyItem(**rec) for rec in records]
    # items = calculate_ma(items)
    return TushareDailyResult(trade_date=trade_date, ts_code=ts_code, total=len(items), items=items)

# def calculate_ma(daily_items: list[TushareDailyItem]) -> list[TushareDailyItem]:
#     """为同一 `ts_code` 的时间序列计算 MA 指标，并回填到 items 中。

#     注意：当入参为某个交易日的全市场快照（只有单天、包含多个 ts_code）时，
#     因缺少时间序列上下文，不计算均线（将保持为 None）。
#     """
#     if not daily_items:
#         return daily_items

#     # 延迟导入，避免在无需要的路径上引入依赖。
#     import pandas as pd  # type: ignore

#     # 以 ts_code 分组，各自按 trade_date 升序计算滚动均值。
#     from collections import defaultdict

#     groups: dict[str, list[tuple[int, TushareDailyItem]]] = defaultdict(list)
#     for idx, it in enumerate(daily_items):
#         # 没有 ts_code 的记录无法建立时间序列上下文，直接跳过
#         if not it.ts_code:
#             continue
#         groups[it.ts_code].append((idx, it))

#     for _, pairs in groups.items():
#         # 构建 DataFrame 并按日期升序排列，保证 rolling 的时间顺序正确
#         df = pd.DataFrame(
#             {
#                 "idx": [p[0] for p in pairs],
#                 "trade_date": [p[1].trade_date for p in pairs],
#                 "close": [p[1].close for p in pairs],
#             }
#         )
#         # 将字符串日期按 YYYYMMDD 的字典序升序排列即可满足时间顺序
#         df = df.sort_values("trade_date", ascending=True)

#         # 计算滚动均线；使用默认 min_periods=window，前期不足周期得到 NaN
#         close_series = pd.to_numeric(df["close"], errors="coerce")
#         df["ma5"] = close_series.rolling(window=5).mean()
#         df["ma10"] = close_series.rolling(window=10).mean()
#         df["ma20"] = close_series.rolling(window=20).mean()
#         df["ma60"] = close_series.rolling(window=60).mean()

#         # 回填到对应的 BaseModel 实例；NaN 转为 None
#         for _, row in df.iterrows():
#             item = daily_items[int(row["idx"])]
#             item.ma5 = None if pd.isna(row["ma5"]) else float(row["ma5"])  # type: ignore[assignment]
#             item.ma10 = None if pd.isna(row["ma10"]) else float(row["ma10"])  # type: ignore[assignment]
#             item.ma20 = None if pd.isna(row["ma20"]) else float(row["ma20"])  # type: ignore[assignment]
#             item.ma60 = None if pd.isna(row["ma60"]) else float(row["ma60"])  # type: ignore[assignment]

#     return daily_items



if __name__ == "__main__":
    # 示例：使用结构化返回打印前5条
    import sys

    logging.basicConfig(level=logging.INFO)

    # 示例参数（可按需改为从命令行读取）
    td = None  # 或者设置为 datetime.now().strftime("%Y%m%d")
    code = "000969.SZ"

    def fmt(v: Any, nd: int = 2) -> str:
        if v is None:
            return "-"
        if isinstance(v, (int, float)):
            return f"{float(v):.{nd}f}"
        return str(v)

    try:
        res = get_a_daily_structured(trade_date=td, ts_code=code)
        print(
            f"trade_date={res.trade_date or '-'} ts_code={res.ts_code or '-'} total={res.total}\n示例前5条:"
        )
        for i, it in enumerate(res.items[:10], 1):
            print(
                # it
                f"{i:2d}. {it.ts_code} {it.trade_date} 收盘:{fmt(it.close)} 涨跌幅:{fmt(it.pct_chg)}% 成交量:{fmt(it.vol)} 5日:{fmt(it.ma5)} 10日:{fmt(it.ma10)} 20日:{fmt(it.ma20)} 60日:{fmt(it.ma60)}"
            )
    except Exception as e:  # noqa: BLE001
        print(f"执行失败: {e}")
