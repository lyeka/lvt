import random
from enum import Enum
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import Command

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
        stock_dict = {stock_item.code+"."+stock_item.market: stock_item for stock_item in result.items[:1]} # 测试用，只取一个
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

   
    target_stock_code = list(stock_dict.keys())[random.randint(0, len(stock_dict.keys())-1)]
    prompt = build_single_stock_llm_judge_prompt(state, target_stock_code)
    model = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))
    response = await model.ainvoke([HumanMessage(content=prompt)])

        
    return {
      "messages": [AIMessage(content=response.content)]
    }
    

def build_single_stock_llm_judge_prompt(state: AgentState, stock_code: str) -> str:
    basic_info = state["stock_dict"][stock_code]
    daily_items = state["stock_daily_items"][stock_code][:60]

    prompt = f"""# 角色
你是一名仅做多（Long-Only）的量化/技术面交易分析师。你的任务是在不改变既有决策逻辑的前提下，基于给定数据与参数，完成市场状态识别、策略映射、风险回报评估，并给出是否执行多单的决策与价格位建议。

# 约束（不得违反）
1) 仅做多，不做空。
2) 不改变原有决策逻辑与判定顺序：
   - 市场状态四选一：趋势上涨 / 震荡 / 止跌反转 / 其他。
   - 趋势上涨 → 策略：趋势跟随；执行条件：RR ≥ n1。
   - 震荡 → 策略：向上突破；执行条件：确认"向上有效突破区间"且 RR ≥ n2。
   - 止跌反转 → 策略：2B 反转；执行条件：满足 2B 准则且 RR ≥ n3。
   - 其他 → 不交易。
3) RR（风险回报比）统一定义（仅做多）：RR = (TP - Entry) / (Entry - SL)。
4) 任何子策略在对应 RR 未达到门槛（n1/n2/n3）时，必须给出"不交易"结论。
5) 若触发条件（例如"有效突破"或"2B 准则"）不成立，同样为"不交易"。

# 关键术语（用于判定与表述，非新增规则）
- 趋势上涨（Structural Uptrend）：价格结构呈更高的高点/更高的低点（HH/HL）。
- 震荡（Range-Bound / Consolidation）：价格在明确的区间上沿/下沿之间反复波动，缺乏趋势性扩张。
- 向上有效突破（Range Breakout, Upside）：按提供的数据/你的既定有效性标准确认价格对区间上沿的有效突破（如：收盘价站上并保持等），仅作"有效性"的文字表述，不引入新逻辑。
- 2B 准则（来自《专业投机指南》）：价格先"跌破前低"后"迅速收回并重返前低上方"，确认"假破新低→收复"。

# 股票数据
- 基础信息：{basic_info}
- 日线数据：{daily_items}

# 你的任务
基于输入数据完成以下步骤，但不得改变上述逻辑：
1) 市场状态识别：在"趋势上涨 / 震荡 / 止跌反转 / 其他"中选择一个，给出判定依据（如：HH/HL、区间边界、是否出现 2B 的假破与收复等）。
2) 策略映射：严格按逻辑映射为：
   - 趋势上涨 → 趋势跟随（Long-Only）
   - 震荡 → 向上突破（Long-Only）
   - 止跌反转 → 2B 反转（Long-Only）
   - 其他 → 不交易
3) 触发条件与过滤：
   - 趋势：直接进入 RR 评估。
   - 震荡：先判定"向上有效突破"，不成立则不交易；成立再评估 RR。
   - 2B：先判定"满足 2B 准则"，不成立则不交易；成立再评估 RR。
4) 价格位设定：给出建议 Entry / SL / TP（可从结构位/区间/2B 假破低点等推导，方法自定，但不得改变逻辑）。
5) 计算 RR：RR = (TP - Entry) / (Entry - SL)，并与对应门槛（n1 / n2 / n3）比较。
6) 决策输出：仅当对应门槛达成时给出"买入"，否则"不交易"。

# 阈值参数（以实际调用时提供的数据为准）
- 参数：
  - n1（趋势跟随最小 RR 门槛）：1.5
  - n2（区间向上突破最小 RR 门槛）：2
  - n3（2B 反转最小 RR 门槛）：1

# 输出（必须为 JSON，字段与含义如下）
{{
  "stock_code": "{stock_code}",
  "stock_name": "str",
  "analysis_time_range": "分析的时间范围",
  "market_state": "uptrend | range | bottoming_reversal | other",
  "mapped_strategy": "trend_follow | breakout_up | reversal_2b | no_trade",
  "triggers": {{
    "trend_signature": "若为趋势：给出HH/HL等结构证据；否则为空",
    "range_definition": "若为震荡：给出上沿/下沿数值或区间定义；否则为空",
    "range_breakout_up_valid": "若为震荡：true/false，表示是否确认向上有效突破；否则为null",
    "rule_2b_valid": "若为止跌反转：true/false，表示是否满足2B准则；否则为null",
    "rule_2b_details": "若为2B：描述假破新低与收复的位置关系；否则为空",
    "time_range": "市场状态的时间范围，其他情况则为空"
  }},
  "levels": {{
    "entry": "number | null",
    "stop_loss": "number | null",
    "take_profit": "number | null",
    "basis": "简述价格位依据（结构位/区间上沿/2B假破低点等）"
  }},
  "rr": {{
    "value": "number | null",
    "threshold_used": "n1 | n2 | n3 | null",
    "passed": "true | false | null"
  }},
  "decision": "buy | no_trade",
  "justification": [
    "用1-4条要点给出判定与决策的核心依据；不得展开无关推理；不得引入新规则"
  ],
  "notes": "可选的执行提醒（例如：仅做多、RR未达标即放弃等）"
}}

# 生成规则（格式与风格）
- 仅输出上述 JSON，不要输出多余文本。
- 数值统一用十进制；给出到合适的小数位（例如价格到2~4位）。
- 若触发条件不满足或无法可靠给出 Entry/SL/TP，所有相关字段置为 null，并输出 "decision": "no_trade" 且在 justification 中说明原因。
- 严禁提出做空或与原逻辑冲突的建议。
- 严禁改变 RR 定义、门槛判断方式与策略映射顺序。
"""
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


