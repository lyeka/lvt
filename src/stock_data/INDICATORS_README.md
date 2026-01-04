# 技术指标计算模块

## 概述

`indicators.py` 模块提供基于日线数据的技术指标计算功能，支持多种常用指标的自动计算。

## 功能特性

### 支持的指标

1. **量能指标**
   - `avg_vol_20`: 20日平均成交量（不足20天时使用现有数据均值）
   - `vol_ratio_20`: 量能倍数（当日成交量 / 均量）

2. **均线指标**
   - `ma20`: 20日移动平均线
   - `ma60`: 60日移动平均线
   - 不足窗口时置 `None`

3. **波动率指标**
   - `atr14`: 14日平均真实波幅（ATR）
   - 支持两种计算方法：
     - `sma`: 简单移动平均（默认）
     - `wilder`: Wilder 指数平滑

4. **关键位指标**
   - `prev_high_20`: 前20日最高价（不含当日）
   - `prev_low_20`: 前20日最低价（不含当日）

### 核心特性

- ✅ **自动排序**: 自动检测并按 `trade_date` 升序排序
- ✅ **灵活配置**: 支持自定义窗口参数
- ✅ **类型安全**: 完整的类型提示和 Pydantic 模型
- ✅ **边界处理**: 智能处理数据不足和缺失值情况
- ✅ **数据源无关**: 可用于任何符合格式的日线数据

## 快速开始

### 基础用法

```python
from stock_data.tushare_api import TushareClient
from stock_data.indicators import calculate_indicators

# 1. 获取原始日线数据
client = TushareClient()
result = client.daily(ts_code="000001.SZ")

# 2. 计算技术指标
enhanced = calculate_indicators(result.items)

# 3. 使用增强数据
latest = enhanced[-1]
print(f"收盘价: {latest.close}")
print(f"MA20: {latest.ma20}")
print(f"ATR14: {latest.atr14}")
print(f"量能倍数: {latest.vol_ratio_20}x")
```

### 自定义参数

```python
enhanced = calculate_indicators(
    items,
    ma_windows=[5, 10, 20, 60],  # 自定义均线窗口
    vol_window=30,                # 30日均量
    atr_window=20,                # 20日 ATR
    atr_method="wilder",          # 使用 Wilder 平滑
    prev_hl_window=30,            # 前30日高低点
)
```

### 实战示例：识别放量突破

```python
# 找出放量突破前高的交易日
for item in enhanced[-20:]:  # 最近20天
    if (item.vol_ratio_20 and item.vol_ratio_20 > 2.0 and  # 放量2倍以上
        item.prev_high_20 and item.close and 
        item.close > item.prev_high_20):  # 突破前20日高点
        
        print(f"{item.trade_date}: 放量突破！")
        print(f"  收盘: {item.close:.2f}")
        print(f"  量能倍数: {item.vol_ratio_20:.2f}x")
        print(f"  前高: {item.prev_high_20:.2f}")
```

## 数据模型

### 输入：TushareDailyItem

```python
class TushareDailyItem(BaseModel):
    ts_code: str          # 股票代码
    trade_date: str       # 交易日期 YYYYMMDD
    open: float | None    # 开盘价
    high: float | None    # 最高价
    low: float | None     # 最低价
    close: float | None   # 收盘价
    vol: float | None     # 成交量（手）
    amount: float | None  # 成交额（千元）
    # ... 其他字段
```

### 输出：EnhancedDailyItem

继承 `TushareDailyItem`，额外包含：

```python
class EnhancedDailyItem(TushareDailyItem):
    avg_vol_20: float | None     # 20日均量
    vol_ratio_20: float | None   # 量能倍数
    ma20: float | None           # 20日均线
    ma60: float | None           # 60日均线
    atr14: float | None          # 14日ATR
    prev_high_20: float | None   # 前20日最高
    prev_low_20: float | None    # 前20日最低
```

## 计算逻辑说明

### 1. 均量（avg_vol_20）

**策略**: 不足窗口时使用现有数据的均值（partial fill）

```python
# 第1天：使用自身
avg_vol_20[0] = vol[0]

# 第10天：使用前10天的均值
avg_vol_20[9] = mean(vol[0:10])

# 第20天及以后：使用完整窗口
avg_vol_20[19] = mean(vol[0:20])
```

### 2. 均线（MA）

**策略**: 不足窗口时置 `None`

```python
# 前19天：None
ma20[0:19] = None

# 第20天开始：完整窗口
ma20[19] = mean(close[0:20])
```

### 3. ATR（平均真实波幅）

**True Range 计算**:
```python
TR[t] = max(
    high[t] - low[t],
    abs(high[t] - close[t-1]),
    abs(low[t] - close[t-1])
)
```

**SMA 方法** (默认):
```python
ATR14[t] = mean(TR[t-13:t+1])  # 简单移动平均
```

**Wilder 方法**:
```python
# 第14天：SMA 初始化
ATR14[13] = mean(TR[0:14])

# 之后：指数平滑
ATR14[t] = (ATR14[t-1] * 13 + TR[t]) / 14
```

### 4. 前N日高低点

**策略**: 不含当日，第一天置 `None`

```python
# 第1天：无前值
prev_high_20[0] = None

# 第2天：取前1天
prev_high_20[1] = high[0]

# 第21天：取前20天
prev_high_20[20] = max(high[0:20])
```

## 异常处理

### 输入验证

```python
from stock_data.indicators import IndicatorsError

try:
    enhanced = calculate_indicators([])
except IndicatorsError as e:
    print(f"计算失败: {e}")  # "输入数据为空"
```

### 缺失值处理

- 自动跳过 `None` 值
- 窗口内数据不足时根据策略处理
- 不会抛出异常，返回 `None`

## 性能考虑

- **时间复杂度**: O(n × w)，其中 n 是数据量，w 是最大窗口
- **空间复杂度**: O(n)
- **建议**: 单次计算数千条数据无压力，百万级数据考虑分批

## 测试

运行单元测试：

```bash
pytest tests/test_stock_data/test_indicators.py -v
```

测试覆盖：
- ✅ 基础指标计算
- ✅ 自动排序功能
- ✅ 边界条件处理
- ✅ 两种 ATR 方法
- ✅ 自定义参数
- ✅ 缺失值处理

## 扩展建议

如果需要添加新指标：

1. 在 `EnhancedDailyItem` 中添加字段
2. 在 `calculate_indicators()` 中添加计算逻辑
3. 创建独立的 `_calculate_xxx()` 辅助函数
4. 添加对应的单元测试

## 常见问题

### Q: 为什么我的 MA20 是 None？

A: 数据不足20天。均线需要完整窗口才计算。

### Q: 如何获取其他窗口的均线（如 MA5）？

A: 使用 `ma_windows` 参数，但注意 `EnhancedDailyItem` 只有 `ma20` 和 `ma60` 字段。如需其他窗口，需要扩展模型。

### Q: ATR 的两种方法有什么区别？

A: 
- `sma`: 简单移动平均，每个窗口独立计算，适合快速响应
- `wilder`: 指数平滑，更平滑但有滞后，Wilder 原始方法

### Q: 可以用于其他数据源吗？

A: 可以！只要数据符合 `TushareDailyItem` 格式即可。支持 AKShare、East Money 等。

## 相关文件

- `src/schema/indicators.py` - 数据模型定义
- `src/stock_data/indicators.py` - 核心计算逻辑
- `tests/test_stock_data/test_indicators.py` - 单元测试
- `examples/indicators_example.py` - 使用示例

## 许可

与项目主许可协议一致。



