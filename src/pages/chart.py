#!/usr/bin/env python3

"""
TuShare 股票 K线图表页面 (PyEcharts版本)
=========================================

基于 TuShare API 和 PyEcharts 的 A股日K数据可视化工具
参考官方示例: https://gallery.pyecharts.org/#/Candlestick/kline_datazoom_slider_position
"""

import os
import re
import sys
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from pyecharts import options as opts
from pyecharts.charts import Bar, Grid, Kline, Line
from streamlit_echarts import st_pyecharts

# 导入 TuShare API
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from schema.tushare import TushareDailyResult
from stock_data.tushare_api import get_a_daily_structured

# 页面配置
st.set_page_config(
    page_title="stock detail",
    page_icon="📈",
    layout="wide",
)

# st.title("📈 A股K线图表")
st.markdown("## Stock Detail")

# 侧边栏配置
with st.sidebar:
    st.header("📊 Display Options")
    
    # 股票代码输入
    stock_code = st.text_input(
        "Stock Code",
        value="000001.SZ",
        help="请输入TuShare格式的股票代码，如: 000001.SZ (深市) 或 600519.SH (沪市)",
        placeholder="例如: 000001.SZ"
    )
    
    # 时间范围选择
    time_range = st.selectbox(
        "Time Range",
        options=["最近30天", "最近60天", "最近90天", "最近180天", "最近1年"],
        index=2,  # 默认选择90天
        help="选择要显示的历史数据时间范围"
    )
    
    # 图表选项
    st.subheader("Show Options")
    show_volume = st.checkbox("Show Volume", value=True)
    show_ma = st.checkbox("Show Moving Average", value=True)
    
    if show_ma:
        ma_periods = st.multiselect(
            "Moving Average Period",
            options=[5, 10, 20, 30, 60],
            default=[60],
            help="选择要显示的移动平均线周期"
        )

def validate_stock_code(code: str) -> bool:
    """验证股票代码格式"""
    if not code:
        return False
    
    # TuShare 格式: 6位数字.SH/SZ
    pattern = r'^\d{6}\.(SH|SZ)$'
    return bool(re.match(pattern, code.upper()))

def get_date_range(time_range: str) -> tuple[str, str]:
    """根据时间范围获取开始和结束日期"""
    end_date = datetime.now()
    
    if time_range == "最近30天":
        start_date = end_date - timedelta(days=45)  # 多取一些数据以防节假日
    elif time_range == "最近60天":
        start_date = end_date - timedelta(days=90)
    elif time_range == "最近90天":
        start_date = end_date - timedelta(days=120)
    elif time_range == "最近180天":
        start_date = end_date - timedelta(days=240)
    elif time_range == "最近1年":
        start_date = end_date - timedelta(days=400)
    else:
        start_date = end_date - timedelta(days=90)
    
    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")

@st.cache_data(ttl=300)  # 缓存5分钟
def fetch_stock_data(stock_code: str, start_date: str, end_date: str) -> TushareDailyResult | None:
    """获取股票数据并缓存"""
    try:
        # 调用 TuShare API 获取数据
        result = get_a_daily_structured(trade_date=None, ts_code=stock_code)
        return result
    except Exception as e:
        st.error(f"数据获取失败: {str(e)}")
        return None

def calculate_moving_average(df: pd.DataFrame, periods: list[int]) -> pd.DataFrame:
    """计算移动平均线"""
    df_ma = df.copy()
    for period in periods:
        df_ma[f'MA{period}'] = df_ma['close'].rolling(window=period).mean()
    return df_ma

def create_kline_chart(df: pd.DataFrame, stock_code: str, show_volume: bool = True, ma_periods: list[int] = None):
    """创建PyEcharts K线图 - 参考官方示例"""
    
    # 准备数据
    dates = df['trade_date'].dt.strftime('%Y-%m-%d').tolist()
    
    # K线数据格式: [开盘价, 收盘价, 最低价, 最高价]
    kline_data = []
    for _, row in df.iterrows():
        kline_data.append([
            float(row['open']) if pd.notna(row['open']) else 0,
            float(row['close']) if pd.notna(row['close']) else 0,
            float(row['low']) if pd.notna(row['low']) else 0,
            float(row['high']) if pd.notna(row['high']) else 0,
        ])
    
    # 创建K线图 - 参考官方示例
    kline = (
        Kline(init_opts=opts.InitOpts(width="100%", height="400px"))
        .add_xaxis(xaxis_data=dates)
        .add_yaxis(
            series_name="",
            y_axis=kline_data,
            itemstyle_opts=opts.ItemStyleOpts(
                color="#ec0000",      # 阳线颜色
                color0="#00da3c",    # 阴线颜色
                border_color="#8A0000",
                border_color0="#008F28",
            ),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title=f"{stock_code} Kline Chart",
                pos_left="0"
            ),
            legend_opts=opts.LegendOpts(
                is_show=True, pos_top=10, pos_left="center"
            ),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                is_scale=True,
                boundary_gap=False,
                axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
                min_="dataMin",
                max_="dataMax",
            ),
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, 
                    areastyle_opts=opts.AreaStyleOpts(opacity=1)
                ),
            ),
            datazoom_opts=[
                opts.DataZoomOpts(
                    is_show=False,
                    type_="inside",
                    xaxis_index=[0, 1],
                    range_start=0,
                    range_end=100,
                ),
                opts.DataZoomOpts(
                    is_show=True,
                    xaxis_index=[0, 1],
                    type_="slider",
                    pos_top="85%",
                    range_start=0,
                    range_end=100,
                ),
            ],
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                axis_pointer_type="cross",
                background_color="rgba(245, 245, 245, 0.8)",
                border_width=1,
                border_color="#ccc",
                textstyle_opts=opts.TextStyleOpts(color="#000"),
            ),
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": "all"}],
                label=opts.LabelOpts(background_color="#777"),
            ),
        )
    )
    
    # 添加移动平均线
    if ma_periods:
        line = Line()
        line.add_xaxis(xaxis_data=dates)
        
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57"]
        for i, period in enumerate(ma_periods):
            if f'MA{period}' in df.columns:
                ma_data = [float(x) if pd.notna(x) else None for x in df[f'MA{period}']]
                line.add_yaxis(
                    series_name=f"MA{period}",
                    y_axis=ma_data,
                    is_symbol_show=False,
                    is_smooth=True,
                    is_hover_animation=False,
                    linestyle_opts=opts.LineStyleOpts(width=1, color=colors[i % len(colors)]),
                    label_opts=opts.LabelOpts(is_show=False),
                )
        
        # 合并K线图和均线
        kline = kline.overlap(line)
    
    # 如果显示成交量，创建网格布局
    if show_volume:
        volume_data = [float(row['vol']) if pd.notna(row['vol']) else 0 for _, row in df.iterrows()]
        
        volume_bar = (
            Bar(init_opts=opts.InitOpts(width="100%", height="150px"))
            .add_xaxis(xaxis_data=dates)
            .add_yaxis(
                series_name="Volume",
                y_axis=volume_data,
                xaxis_index=1,
                yaxis_index=1,
                label_opts=opts.LabelOpts(is_show=False),
                itemstyle_opts=opts.ItemStyleOpts(
                    color="#7fbe9e"
                ),
            )
            .set_global_opts(
                legend_opts=opts.LegendOpts(
                    is_show=True, pos_bottom=10, pos_left="center"
                ),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    grid_index=1,
                    axislabel_opts=opts.LabelOpts(is_show=False),
                ),
                yaxis_opts=opts.AxisOpts(
                    grid_index=1,
                    split_number=3,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                    axislabel_opts=opts.LabelOpts(is_show=True),
                ),
            )
        )
        
        # 创建网格布局
        grid = (
            Grid(init_opts=opts.InitOpts(width="100%", height="600px"))
            .add(
                kline,
                grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="50%"),
            )
            .add(
                volume_bar,
                grid_opts=opts.GridOpts(
                    pos_left="10%", pos_right="8%", pos_top="70%", height="16%"
                ),
            )
        )
        
        return grid
    else:
        return kline

# 主要内容区域
if not validate_stock_code(stock_code):
    st.error("❌ 请输入有效的股票代码格式，如: 000001.SZ 或 600519.SH")
    st.stop()

# 显示当前配置
# col1, col2, col3 = st.columns(3)
# with col1:
#     st.metric("股票代码", stock_code)
# with col2:
#     st.metric("时间范围", time_range)
# with col3:
#     st.metric("数据源", "TuShare Pro")

# 获取数据
with st.spinner("正在获取股票数据..."):
    start_date, end_date = get_date_range(time_range)
    stock_data = fetch_stock_data(stock_code, start_date, end_date)

if stock_data is None or not stock_data.items:
    st.error("❌ 未能获取到股票数据，请检查股票代码是否正确或稍后重试")
    st.stop()

# 转换数据格式
df_data = []
for item in stock_data.items:
    df_data.append({
        'trade_date': item.trade_date,
        'open': item.open,
        'high': item.high,
        'low': item.low,
        'close': item.close,
        'vol': item.vol,
        'amount': item.amount,
        'pct_chg': item.pct_chg
    })

df = pd.DataFrame(df_data)

# 数据预处理
df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
df = df.sort_values('trade_date').reset_index(drop=True)

# 过滤时间范围
days_map = {
    "最近30天": 30,
    "最近60天": 60,
    "最近90天": 90,
    "最近180天": 180,
    "最近1年": 365
}
recent_days = days_map.get(time_range, 60)
df = df.tail(recent_days)

if df.empty:
    st.error("❌ 所选时间范围内没有数据")
    st.stop()

# 计算移动平均线
if show_ma and 'ma_periods' in locals():
    df = calculate_moving_average(df, ma_periods)

# # 显示基本信息
# st.subheader("📊 股票基本信息")
# latest_data = df.iloc[-1]
# prev_data = df.iloc[-2] if len(df) > 1 else latest_data

# col1, col2, col3, col4 = st.columns(4)
# with col1:
#     price_change = latest_data['close'] - prev_data['close']
#     st.metric(
#         "最新价格", 
#         f"¥{latest_data['close']:.2f}",
#         delta=f"{price_change:.2f}"
#     )
# with col2:
#     st.metric(
#         "涨跌幅", 
#         f"{latest_data['pct_chg']:.2f}%",
#         delta=None
#     )
# with col3:
#     st.metric(
#         "成交量", 
#         f"{latest_data['vol']:.0f}手" if latest_data['vol'] else "N/A"
#     )
# with col4:
#     st.metric(
#         "成交额", 
#         f"{latest_data['amount']:.2f}万" if latest_data['amount'] else "N/A"
#     )

# 创建并显示图表
# st.text("📈")

try:
    chart = create_kline_chart(
        df, 
        stock_code, 
        show_volume, 
        ma_periods if show_ma and 'ma_periods' in locals() else None
    )
    
    # 使用 streamlit-echarts 的 st_pyecharts 直接渲染 PyEcharts 图表
    st_pyecharts(
        chart,
        height="600px",
        key="kline_chart",
    )
    
except Exception as e:
    st.error(f"图表渲染失败: {str(e)}")
    st.write("详细错误信息:", str(e))
    
    # 简化版本的图表作为备选
    st.write("尝试使用简化版本...")
    chart_data = df.set_index('trade_date')[['open', 'high', 'low', 'close']]
    st.line_chart(chart_data)

# 显示数据表格
if st.checkbox("显示原始数据"):
    st.subheader("📋 历史数据")
    display_df = df[['trade_date', 'open', 'high', 'low', 'close', 'vol', 'pct_chg']].copy()
    display_df['trade_date'] = display_df['trade_date'].dt.strftime('%Y-%m-%d')
    display_df.columns = ['日期', '开盘', '最高', '最低', '收盘', '成交量', '涨跌幅(%)']
    st.dataframe(display_df, use_container_width=True)

# 页脚信息
# st.markdown("---")
