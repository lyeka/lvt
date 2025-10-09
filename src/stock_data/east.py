#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
东方财富选股API封装
===================

实现MA60突破策略等选股功能的优雅封装

Author: Linus Torvalds Style Implementation
Date: 2025-10-06
"""

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================================================================
# 核心数据结构定义
# ============================================================================


@dataclass
class StockFilter:
    """股票筛选条件数据结构"""

    exclude_kcb: bool = True  # 排除科创板
    exclude_cyb: bool = True  # 排除创业板
    exclude_bjs: bool = True  # 排除北交所
    exclude_st: bool = True  # 排除ST股
    ma60_breakthrough: bool = True  # MA60向上突破
    pe_min: float = 0  # 市盈率最小值
    pe_max: float = 500  # 市盈率最大值
    market_cap_min: float = 50  # 总市值最小值(亿)
    popularity_rising: bool = True  # 人气排名上升
    popularity_rank_max: int = 1000  # 股吧人气排名上限
    roe_min: float = 0  # ROE最小值


@dataclass
class RequestConfig:
    """请求配置参数"""

    page_size: int = 50
    page_no: int = 1
    calc_avg_chg: bool = True
    share_to_guba: bool = False
    dynamic_type: str = "COMMON"
    all_code: bool = True
    own_select_all: bool = False
    client: str = "web"
    biz: str = "web_ai_select_stocks"


# ============================================================================
# 东方财富API客户端
# ============================================================================


class EastMoneyAPI:
    """
    东方财富选股API客户端

    设计哲学：
    - 简洁的接口，复杂的内部实现
    - 优雅的错误处理，不让异常泄漏
    - 可配置的参数，避免硬编码魔法数字
    """

    BASE_URL = "https://np-tjxg-g.eastmoney.com"
    SEARCH_ENDPOINT = "/api/smart-tag/stock/v3/pw/search-code"

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        初始化API客户端

        Args:
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.session = self._create_session(max_retries)
        self.logger = self._setup_logger()

    def _create_session(self, max_retries: int) -> requests.Session:
        """创建带重试机制的会话"""
        session = requests.Session()

        # 配置重试策略 - Linus风格：简单有效
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 设置通用请求头
        session.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh,en;q=0.9,zh-CN;q=0.8,en-GB;q=0.7",
                "Origin": "https://xuangu.eastmoney.com",
                "Referer": "https://xuangu.eastmoney.com/",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            }
        )

        return session

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
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

    def _generate_request_id(self) -> str:
        """生成请求ID - 简单有效的UUID方案"""
        return str(uuid.uuid4()).replace("-", "") + str(int(time.time() * 1000))

    def _generate_fingerprint(self, data: str) -> str:
        """生成指纹 - MD5哈希，简单可靠"""
        return hashlib.md5(data.encode("utf-8")).hexdigest()

    def _build_keyword_string(self, filter_config: StockFilter) -> str:
        """
        构建关键词筛选字符串

        这里体现了Linus的"好品味"：
        - 用数据驱动，而不是一堆if/else
        - 条件映射表，消除特殊情况
        """
        conditions = []

        # 排除条件映射表
        exclusions = [
            (filter_config.exclude_kcb, "不要科创板"),
            (filter_config.exclude_cyb, "不要创业板"),
            (filter_config.exclude_bjs, "不要北交所"),
            (filter_config.exclude_st, "不要ST股及不要退市股"),
        ]

        # 包含条件映射表
        inclusions = [
            (filter_config.ma60_breakthrough, "向上突破60日线"),
            (True, f"市盈率(TTM){filter_config.pe_min}-{filter_config.pe_max}"),
            (True, f"总市值>{filter_config.market_cap_min}亿"),
            (filter_config.popularity_rising, "人气排名上升"),
            (True, f"股吧人气排名前{filter_config.popularity_rank_max}名"),
            (filter_config.roe_min >= 0, f"净资产收益率ROE(加权)>{filter_config.roe_min}%"),
        ]

        # 合并所有条件 - 无分支，数据驱动
        all_conditions = exclusions + inclusions
        conditions = [desc for enabled, desc in all_conditions if enabled]

        return ";".join(conditions) + ";"

    def _build_dx_info(self, filter_config: StockFilter) -> List[Dict]:
        """构建动态信息参数"""
        dx_info = []

        if filter_config.popularity_rising:
            dx_info.append(
                {
                    "paramInfos": [
                        {
                            "optionSonName": "",
                            "lowValue": "",
                            "highValue": "",
                            "optionName": "上升",
                        }
                    ],
                    "isCustom": False,
                    "index": 7,
                    "id": 78,
                    "name": "人气排名上升",
                }
            )

        dx_info.append(
            {
                "paramInfos": [
                    {
                        "optionSonName": "",
                        "lowValue": "",
                        "highValue": "",
                        "optionName": f"前{filter_config.popularity_rank_max}名",
                    }
                ],
                "isCustom": False,
                "index": 8,
                "id": 77,
                "name": f"股吧人气排名前{filter_config.popularity_rank_max}名",
            }
        )

        return dx_info

    def _build_request_payload(
        self, filter_config: StockFilter, request_config: RequestConfig
    ) -> Dict[str, Any]:
        """构建完整的请求载荷"""
        keyword = self._build_keyword_string(filter_config)
        request_id = self._generate_request_id()
        timestamp = str(int(time.time() * 1000000))
        fingerprint = self._generate_fingerprint(keyword + timestamp)

        payload = {
            "keyWord": keyword,
            "dxInfo": self._build_dx_info(filter_config),
            "pageSize": request_config.page_size,
            "pageNo": request_config.page_no,
            "fingerprint": fingerprint,
            "matchWord": "",
            "timestamp": timestamp,
            "shareToGuba": request_config.share_to_guba,
            "calcAvgChg": request_config.calc_avg_chg,
            "requestId": request_id,
            "dynamicType": request_config.dynamic_type,
            "allCode": request_config.all_code,
            "ownSelectAll": request_config.own_select_all,
            "client": request_config.client,
            "biz": request_config.biz,
            "gids": [],
            "xcId": "xc0cf09a73053300c648",  # 固定值，从原始请求中提取
        }

        return payload

    def search_stocks(
        self,
        filter_config: Optional[StockFilter] = None,
        request_config: Optional[RequestConfig] = None,
    ) -> Dict[str, Any]:
        """
        执行股票搜索

        Args:
            filter_config: 筛选条件配置
            request_config: 请求参数配置

        Returns:
            API响应数据字典

        Raises:
            requests.RequestException: 网络请求异常
            ValueError: 响应数据解析异常
        """
        # 使用默认配置 - Linus风格：合理的默认值
        if filter_config is None:
            filter_config = StockFilter()
        if request_config is None:
            request_config = RequestConfig()

        try:
            # 构建请求
            url = urljoin(self.BASE_URL, self.SEARCH_ENDPOINT)
            payload = self._build_request_payload(filter_config, request_config)

            self.logger.info(
                f"发起选股请求: 页码={request_config.page_no}, 页大小={request_config.page_size}"
            )
            self.logger.debug(f"筛选条件: {payload['keyWord']}")

            # 发送请求
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            # 解析响应
            data = response.json()

            self.logger.info(f"请求成功: 状态码={response.status_code}")
            return data

        except requests.RequestException as e:
            self.logger.error(f"网络请求失败: {e}")
            raise
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"响应数据解析失败: {e}")
            raise ValueError(f"无效的API响应数据: {e}")

    def get_ma60_breakthrough_stocks(
        self, page_no: int = 1, page_size: int = 50
    ) -> Dict[str, Any]:
        """
        获取MA60突破策略股票

        这是对外的简洁接口 - Linus哲学：让复杂的事情变简单

        Args:
            page_no: 页码
            page_size: 每页数量

        Returns:
            符合MA60突破策略的股票数据
        """
        filter_config = StockFilter()  # 使用默认的MA60突破配置
        request_config = RequestConfig(page_no=page_no, page_size=page_size)

        return self.search_stocks(filter_config, request_config)


# ============================================================================
# 便捷函数接口
# ============================================================================


def get_ma60_stocks(page_no: int = 1, page_size: int = 50) -> Dict[str, Any]:
    """
    便捷函数：获取MA60突破股票

    最简洁的使用方式 - 一行代码解决问题
    """
    api = EastMoneyAPI()
    return api.get_ma60_breakthrough_stocks(page_no, page_size)


def _to_float(val: Any) -> Optional[float]:
    """Best-effort float conversion from numbers or numeric-like strings.

    Returns None if conversion is not possible.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if not isinstance(val, str):
        return None
    s = val.strip()
    if not s or s in {"-", "N/A", "nan", "NaN"}:
        return None
    # Keep digits, minus and dot; drop units like "亿" etc.
    import re

    cleaned = "".join(re.findall(r"[-0-9.]", s))
    if cleaned in {"", "-", ".", "-.", "-.", ".."}:
        return None
    try:
        return float(cleaned)
    except Exception:
        return None


def _to_int(val: Any) -> Optional[int]:
    f = _to_float(val)
    return int(f) if f is not None else None


def _split_first_number(pipe_value: Any) -> Optional[float]:
    """Extract number before '|' if present, else parse directly."""
    if isinstance(pipe_value, str) and "|" in pipe_value:
        head = pipe_value.split("|", 1)[0]
        return _to_float(head)
    return _to_float(pipe_value)


def get_ma60_stocks_structured(
    page_no: int = 1, page_size: int = 50
) -> "StockScanResult":
    """
    获取结构化的 MA60 突破选股结果（Pydantic 模型）。

    功能等同于 `get_ma60_stocks`，但返回 `StockScanResult`，其中包含
    标准化字段与类型，便于上层消费与序列化。
    """
    # 延迟导入以支持直接运行此文件 (__main__) 时的路径问题
    try:
        from schema.stock import StockItem, StockScanResult  # type: ignore
    except ModuleNotFoundError:
        import os
        import sys

        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from schema.stock import StockItem, StockScanResult  # type: ignore

    api = EastMoneyAPI()
    raw = api.get_ma60_breakthrough_stocks(page_no, page_size)

    today = datetime.now().strftime("%Y-%m-%d")
    k_ma60 = f"60日JX{{{today}}}"
    k_pe_ttm = f"PETTM{{{today}}}"
    k_roe = f"ROE_WEIGHT{{{today}}}"
    k_rank_change = f"RANK_CHANGE{{{today}}}"
    k_guba_top = f"GUBA_TOP{{{today}}}"

    data = raw.get("data") or {}
    result = data.get("result") or {}
    items = result.get("dataList") or []
    meta_total = (result.get("meta") or {}).get("total")
    total = int(meta_total) if isinstance(meta_total, (int, float)) else int(len(items))

    structured_items: List[StockItem] = []
    for it in items:
        code = it.get("SECURITY_CODE", "")
        market = it.get("MARKET_SHORT_NAME", "")
        name = it.get("SECURITY_SHORT_NAME", "")

        price = _to_float(it.get("NEWEST_PRICE"))
        ma60 = _to_float(it.get(k_ma60))
        chg = _to_float(it.get("CHG"))

        # Market cap often comes with units (e.g., "1234亿"). Convert to billions.
        # We already strip non-numeric, assume the number is billions.
        market_cap_billion = _to_float(it.get("TOAL_MARKET_VALUE<140>"))

        pe_dynamic = _to_float(it.get("PE_DYNAMIC"))
        pe_ttm = _to_float(it.get(k_pe_ttm))
        pb = _to_float(it.get("PB"))
        roe = _split_first_number(it.get(k_roe))

        turnover_rate = _to_float(it.get("TURNOVER_RATE"))
        qrr = _to_float(it.get("QRR"))
        popularity_rank_change = _to_int(it.get(k_rank_change))
        guba_top_rank = _to_int(it.get(k_guba_top))

        structured_items.append(
            StockItem(
                code=code,
                market=market,
                name=name,
                price=price,
                ma60=ma60,
                change_pct=chg,
                market_cap_billion=market_cap_billion,
                pe_dynamic=pe_dynamic,
                pe_ttm=pe_ttm,
                pb=pb,
                roe=roe,
                turnover_rate=turnover_rate,
                qrr=qrr,
                popularity_rank_change=popularity_rank_change,
                guba_top_rank=guba_top_rank,
            )
        )

    return StockScanResult(
        as_of_date=today,
        total=total,
        page_no=page_no,
        page_size=page_size,
        items=structured_items,
    )


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == "__main__":
    # 简单的测试代码
    logging.basicConfig(level=logging.INFO)

    try:
        print("正在获取MA60突破策略股票（结构化）...")
        result = get_ma60_stocks_structured(page_no=1, page_size=10)

        print("请求成功!\n")
        print(
            f"日期: {result.as_of_date} | 总数: {result.total} | 页码: {result.page_no} | 页大小: {result.page_size}"
        )
        print("=" * 60)

        def fmt(v: Any, nd: int = 2) -> str:
            if v is None:
                return "-"
            if isinstance(v, (int, float)):
                return f"{float(v):.{nd}f}"
            return str(v)

        for i, it in enumerate(result.items, 1):
            print(
                f"{i:2d}. {it.code}.{it.market} - {it.name:8s} | "
                f"价格:{fmt(it.price):>8s} | 涨幅:{fmt(it.change_pct):>6s}% | 市值:{fmt(it.market_cap_billion):>8s}亿 | "
                f"MA60:{fmt(it.ma60):>8s} | PE_DYNAMIC:{fmt(it.pe_dynamic):>8s} | PE_TTM:{fmt(it.pe_ttm):>8s} | PB:{fmt(it.pb):>6s} | "
                f"ROE:{fmt(it.roe):>6s}% | 换手率:{fmt(it.turnover_rate):>6s}% | 量比:{fmt(it.qrr):>6s} | "
                f"人气排名变化:{it.popularity_rank_change if it.popularity_rank_change is not None else '-':>4} | "
                f"股吧人气排名:{it.guba_top_rank if it.guba_top_rank is not None else '-':>6}"
            )

    except Exception as e:
        print(f"执行失败: {e}")
