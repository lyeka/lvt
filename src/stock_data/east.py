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


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == "__main__":
    # 简单的测试代码
    logging.basicConfig(level=logging.INFO)

    try:
        print("正在获取MA60突破策略股票...")
        result = get_ma60_stocks(page_no=1, page_size=10)

        print("请求成功!")
        print(f"返回数据键: {list(result.keys())}")
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"今天日期: {today}")
        print(f"ROE_WEIGHT{{{today}}}")

        # 如果有股票数据，显示前几只
        if "data" in result and result["data"]:
            data = result["data"]
            if (
                isinstance(data, dict)
                and "result" in data
                and "dataList" in data["result"]
            ):
                stocks = data["result"]["dataList"]
                total = data["result"].get("meta", {}).get("total", len(stocks))
                print(f"\n找到 {total} 只符合MA60突破策略的股票:")
                print("=" * 60)
                for i, stock in enumerate(stocks[:], 1):  # 显示所有返回的股票
                    code = stock.get("SECURITY_CODE", "N/A")
                    market_shot_name = stock.get("MARKET_SHORT_NAME", "N/A")
                    name = stock.get("SECURITY_SHORT_NAME", "N/A")
                    price = stock.get("NEWEST_PRICE", "N/A")
                    ma60 = stock.get(f"60日JX{{{today}}}", "N/A")
                    chg = stock.get("CHG", "N/A")
                    market_cap = stock.get("TOAL_MARKET_VALUE<140>", "N/A")
                    pe_dynamic = stock.get("PE_DYNAMIC", "N/A")
                    pe_ttm = stock.get(f"PETTM{{{today}}}", "N/A")
                    pb = stock.get("PB", "N/A")
                    # roe_date = stock.get(f"ROE_WEIGHT{{{today}}}&&DATE", "N/A")
                    roe = stock.get(f"ROE_WEIGHT{{{today}}}", "N/A").split("|")[0]
                    turnover_rate = stock.get("TURNOVER_RATE", "N/A")
                    qrr = stock.get("QRR", "N/A") # 量比
                    rrank_change = stock.get(f"RANK_CHANGE{{{today}}}", "N/A") # 人气排名变化
                    guba_top = stock.get(f"GUBA_TOP{{{today}}}", "N/A") # 股吧人气排名
                    print(
                        f"{i:2d}. {code}.{market_shot_name} - {name:8s} | 价格:{price:>8s} | 涨幅:{chg:>6s}% | 市值:{market_cap:>10s} | MA60:{ma60:>8s} | PE_DYNAMIC:{pe_dynamic:>8s} | PE_TTM:{pe_ttm:>8s} | PB:{pb:>8s} | ROE:{roe:>8s} | 换手率:{turnover_rate:>8s} | 量比:{qrr:>8s} | 人气排名变化:{rrank_change:>8s} | 股吧人气排名:{guba_top:>8s}"
                    )
            else:
                print(f"\n数据结构: {type(data)}")
                if isinstance(data, dict):
                    print(f"数据键: {list(data.keys())}")
                else:
                    print(f"数据内容: {data}")

    except Exception as e:
        print(f"执行失败: {e}")
