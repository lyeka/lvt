import streamlit as st
from streamlit_searchbox import st_searchbox

from agents.trade_agent import StockSelectionStrategy


def search_stock_strategy(searchterm: str) -> list:
    """
    搜索股票选择策略
    当用户输入以 '/' 开头时，返回匹配的策略选项
    """
    if not searchterm.startswith('/'):
        return []
    
    # 移除开头的 '/'
    search_query = searchterm[1:].lower()
    
    # 获取所有策略选项
    strategies = []
    for strategy in StockSelectionStrategy:
        # 创建显示选项，包含策略值和描述
        display_name = f"/{strategy.value}"
        description = get_strategy_description(strategy)
        full_display = f"{display_name} - {description}"
        
        # 如果搜索词为空或匹配策略值，则包含此选项
        if not search_query or search_query in strategy.value.lower():
            strategies.append(full_display)
    
    return strategies


def get_strategy_description(strategy: StockSelectionStrategy) -> str:
    """获取策略描述"""
    descriptions = {
        StockSelectionStrategy.EASTV1: "东方财富MA60策略V1",
        StockSelectionStrategy.EASTV2: "东方财富MA60策略V2",
    }
    return descriptions.get(strategy, "未知策略")


# 页面标题
st.title("股票策略搜索")
st.write("输入 `/` 开始搜索股票选择策略")

# 搜索框
selected_value = st_searchbox(
    search_stock_strategy,
    placeholder="输入 / 搜索策略...",
    key="strategy_search",
    default_options=[],
)

# 显示选择结果
if selected_value:
    st.write(f"选择的策略: {selected_value}")
    
    # 提取策略值
    if selected_value.startswith('/'):
        strategy_value = selected_value.split(' - ')[0][1:]  # 移除 '/' 并获取策略值
        try:
            strategy = StockSelectionStrategy(strategy_value)
            st.success(f"已选择策略: {strategy.name} ({strategy.value})")
            
            # 这里可以添加更多策略相关的信息展示
            with st.expander("策略详情"):
                st.write(f"**策略名称**: {strategy.name}")
                st.write(f"**策略值**: {strategy.value}")
                st.write(f"**策略描述**: {get_strategy_description(strategy)}")
                
        except ValueError:
            st.error("无效的策略选择")
else:
    st.info("请输入 `/` 开始搜索可用的股票选择策略")