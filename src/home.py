import streamlit as st
from pyecharts import options as opts
from pyecharts.charts import Liquid
from streamlit_echarts import st_pyecharts

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

st.write("# Welcome to TVL! 👋")

st.sidebar.success("Select a demo above.")


st.markdown(
    """
    ### 支持执行下面功能
    - trade analysis：选股器 -> LLM 分析 -> 交易决策
    - chart：单股K线图 -> LLM 分析 -> 交易决策
    - Sector Analysis：板块分析 -> LLM 分析 -> 交易决策
    - Report： 报告归档
"""
)

def create_liquid_chart():
    c = (
        Liquid()
        .add("lq", [0.6, 0.7])
        .set_global_opts()
    )
    return c

try:
    chart = create_liquid_chart()
    st_pyecharts(chart, height="400px", key="liquid_chart")
except Exception as e:
    st.error(f"Liquid chart rendering failed: {e}")
