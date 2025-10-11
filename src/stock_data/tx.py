from __future__ import annotations

from typing import Any, Optional

import httpx
import pandas as pd


class TxFinanceAPI:
    """
    腾讯自选股/行情接口封装。

    将如下 curl 封装为类方法：
    curl -L 'https://proxy.finance.qq.com/cgi/cgi-bin/rank/hs/getBoardRankList?_appver=11.17.&board_code=aStock&sort_type=price&direct=down&offset=5400&count=200' \
      -H 'Accept: */*' \
      -H 'Accept-Language: zh,en;q=0.9,zh-CN;q=0.8,en-GB;q=0.7' \
      -H 'Origin: https://stockapp.finance.qq.com' \
      -H 'Referer: https://stockapp.finance.qq.com/' \
      -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
    """

    BASE_URL = (
        "https://proxy.finance.qq.com/cgi/cgi-bin/rank/hs/getBoardRankList"
    )

    @classmethod
    def get_board_rank_all_list(cls) -> pd.DataFrame:
        """
        """
        df_list: list[pd.DataFrame] = []
        offset = 0
        while True:
            df = cls.get_board_rank_list(offset=offset, count=200)
            df_list.append(df)
            offset += 200
            if len(df) == 0:
                break
        return pd.concat(df_list)

    @classmethod
    def get_board_rank_list(
        cls,
        *,
        board_code: str = "aStock",
        sort_type: str = "priceRatio",
        direct: str = "down",
        offset: int = 0,
        count: int = 200,
        appver: str = "11.17.",
        headers: Optional[dict[str, str]] = None,
        cookies: Optional[dict[str, str]] = None,
        timeout: float = 10.0,
        coerce_numeric: bool = True,
    ) -> pd.DataFrame:
        """
        获取板块排名列表（与给定 curl 等价），返回 pd.DataFrame。

        参数
        - board_code: 板块代码，例如 aStock
        - sort_type: 排序字段，例如 price
        - direct: 排序方向 up/down
        - offset: 偏移量（分页）
        - count: 返回条目数
        - appver: App 版本号参数 `_appver`
        - headers: 额外或覆盖的请求头
        - cookies: 可选的 cookie 字典
        - timeout: 超时时间（秒）
        - coerce_numeric: 尝试将数字形态的字段转换为数值类型
        返回
        - `rank_list` 对应的表数据 DataFrame
        抛出
        - httpx.HTTPError: 网络或 HTTP 层错误
        - ValueError: 响应异常或非 JSON 时抛出
        """

        params = {
            "_appver": appver,
            "board_code": board_code,
            "sort_type": sort_type,
            "direct": direct,
            "offset": str(offset),
            "count": str(count),
        }

        default_headers: dict[str, str] = {
            "Accept": "*/*",
            "Accept-Language": "zh,en;q=0.9,zh-CN;q=0.8,en-GB;q=0.7",
            "Origin": "https://stockapp.finance.qq.com",
            "Referer": "https://stockapp.finance.qq.com/",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/141.0.0.0 Safari/537.36"
            ),
        }
        if headers:
            default_headers.update(headers)

        with httpx.Client(
            timeout=timeout,
            headers=default_headers,
            cookies=cookies,
            follow_redirects=True,
        ) as client:
            resp = client.get(cls.BASE_URL, params=params)
            resp.raise_for_status()
            try:
                payload: dict[str, Any] = resp.json()
            except ValueError as exc:  # 非 JSON 响应
                raise ValueError(
                    f"Unexpected non-JSON response: {resp.text[:200]}"
                ) from exc

        # 基本结构校验与提取
        if payload.get("code") not in (None, 0):
            raise ValueError(f"API error: code={payload.get('code')} msg={payload.get('msg')}")

        data = payload.get("data") or {}
        rank_list = data.get("rank_list") or []
        df = pd.DataFrame(rank_list)

        if coerce_numeric and not df.empty:
            for col in df.columns:
                if df[col].dtype == object:
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except (ValueError, TypeError):
                        pass

        return df


if __name__ == "__main__":
    # 简单示例：打印 DataFrame 头部
    # df = TxFinanceAPI.get_board_rank_list()
    # print(df[:3])
    total = TxFinanceAPI.get_board_rank_all_list()
    print(len(total))
   
