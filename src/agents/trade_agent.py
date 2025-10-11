import random
from enum import Enum
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import Command

from agents.trade_prompts import TRADE_PROMPTS
from core import get_model, settings
from schema.stock import StockItem
from schema.tushare import TushareDailyItem
from stock_data.east import get_ma60_stocks_structured
from stock_data.tushare_api import get_a_daily_structured


class StockSelectionStrategy(Enum):
    """
    股票池选择策略
    """
    EASTV1 = "e_v1"
    EASTV2 = "e_v2"




class AgentState(MessagesState):
    stock_selection_strategy: StockSelectionStrategy
    stock_dict: dict[str, StockItem]
    stock_daily_items: dict[str, list[TushareDailyItem]] 
    stock_analysis_results: dict[str, str]





def stock_pool_node(state: AgentState, config: RunnableConfig) -> Command[Literal["process_stock_items_node", "__end__"]]: 
    latest_message = state["messages"][-1]
    strategy_code = latest_message.content.split("/")[1]
    # 判断 strategy_code 是否在 StockSelectionStrategy 中
    try:
        strategy = StockSelectionStrategy(strategy_code)
    except ValueError:
        return Command(
            goto=END,
        )
  
    strategy = StockSelectionStrategy(strategy_code)
    stock_dict = {}
    if strategy == StockSelectionStrategy.EASTV1:
        result = get_ma60_stocks_structured()
        stock_dict = {stock_item.code+"."+stock_item.market: stock_item for stock_item in result.items[:3]} # 测试用，只取三个
    # elif strategy == StockSelectionStrategy.EASTV2:
    
    return {
      "stock_selection_strategy": strategy,
      "stock_dict": stock_dict,
    }


def process_stock_items_node(state: AgentState, config: RunnableConfig) -> Command[Literal["judge_via_llm_node", "__end__"]]:

    stock_dict = state["stock_dict"]
    stock_daily_items = state.get("stock_daily_items", {})
    

    for stock_code in stock_dict.keys():
        result = get_a_daily_structured(ts_code=stock_code)
        stock_daily_items[stock_code] = result.items

    return { 
      "stock_daily_items": stock_daily_items,
    }




async def judge_via_llm_node(state: AgentState, config: RunnableConfig):

    stock_dict = state["stock_dict"]
    if not stock_dict:
        return Command(
            goto=END,
            update={"messages": [AIMessage(content="No stock daily items")]}
        )

    # for stock_item in stock_daily_items.keys():
    #     prompt = build_single_stock_llm_judge_prompt(state, stock_item)
    #     model = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))
    #     response = await model.ainvoke([HumanMessage(content=prompt)])
    stock_analysis_results = {}
    messages = []
    for stock_code in stock_dict.keys():
      prompt = build_single_stock_llm_judge_prompt(state, stock_code)
      model = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))
      response = await model.ainvoke([HumanMessage(content=prompt)])
      messages.append(AIMessage(content=response.content))
      stock_analysis_results[stock_code] = response.content

    
    # target_stock_code = list(stock_dict.keys())[random.randint(0, len(stock_dict.keys())-1)]
    # prompt = build_single_stock_llm_judge_prompt(state, target_stock_code)
    # model = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))
    # response = await model.ainvoke([HumanMessage(content=prompt)])

        
    return {
      "messages": messages,
      "stock_analysis_results": stock_analysis_results
    }
    

def build_single_stock_llm_judge_prompt(state: AgentState, stock_code: str) -> str:
    basic_info = state["stock_dict"][stock_code]
    daily_items = state["stock_daily_items"][stock_code][:60]

    prompt = TRADE_PROMPTS["single_stock_llm_judge"].format(basic_info=basic_info, daily_items=daily_items)
    return prompt


agent = StateGraph(AgentState)
agent.add_node("stock_pool_node", stock_pool_node)
agent.add_node("process_stock_items_node", process_stock_items_node)
agent.add_node("judge_via_llm_node", judge_via_llm_node)

agent.add_edge(START, "stock_pool_node")
agent.add_edge("stock_pool_node", "process_stock_items_node")
agent.add_edge("process_stock_items_node", "judge_via_llm_node")
agent.add_edge("judge_via_llm_node", END)

trading_agent = agent.compile()


