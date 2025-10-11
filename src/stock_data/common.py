from stock_data.tx import TxFinanceAPI

STOCK_DICT = {}

def format_stock_code(code: str) -> str:
    """
    将股票代码从 'sh600519' 或 'sz000001' 等形式
    转换为 '600519.SH' 或 '000001.SZ' 格式。
    """
    if not code or len(code) < 3:
        raise ValueError("股票代码格式不正确")

    prefix = code[:2].lower()
    num = code[2:]

    suffix_map = {
        "sh": "SH",
        "sz": "SZ",
        "bj": "BJ",  # 北交所
    }

    suffix = suffix_map.get(prefix, prefix.upper())
    return f"{num}.{suffix}"

df = TxFinanceAPI.get_board_rank_all_list()
for index, row in df.iterrows():
    stock_code = format_stock_code(row["code"]) # sh600519
    stock_name = row["name"]
    STOCK_DICT[stock_code] = stock_name

