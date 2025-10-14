import asyncio
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import Command, StreamWriter

from agents.bg_task_agent.task import Task
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

def get_stock_selection_strategy_description(strategy_code: str) -> StockSelectionStrategy:
    if strategy_code == StockSelectionStrategy.EASTV1:
        return "不要科创板;不要创业板;不要北交所;不要ST股及不要退市股;向上突破60日线;市盈率(TTM)0-500;总市值>50亿;人气排名上升;股吧人气排名前1000名;净资产收益率ROE(加权)>0%;"
    elif strategy_code == StockSelectionStrategy.EASTV2:
        return "不要科创板;不要创业板;不要北交所;不要ST股及不要退市股;向上突破60日线;市盈率(TTM)0-500;总市值>50亿;人气排名上升;股吧人气排名前1000名;净资产收益率ROE(加权)>0%;"
    else:
        raise ValueError(f"Invalid stock selection strategy: {strategy_code}")




class AgentState(MessagesState):
    stock_selection_strategy: StockSelectionStrategy
    stock_dict: dict[str, StockItem]
    stock_daily_items: dict[str, list[TushareDailyItem]] 
    stock_analysis_results: dict[str, str]


def write_analysis_report(stock_code: str, stock_name: str, analysis_content: str, prompt: str | None = None) -> None:
    """
    将股票分析报告写入文件
    
    Args:
        stock_code: 股票代码 (如 000001.SZ)
        stock_name: 股票名称
        analysis_content: 分析内容
    """
    try:
        # 获取项目根目录
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        
        # 生成当前日期 (YYYYMMDD格式)
        today = datetime.now().strftime("%Y%m%d")
        
        # 创建报告目录
        report_dir = project_root / "report" / today
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件路径
        report_file = report_dir / f"{stock_code}.md"
        
        # 生成报告内容
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_content = f"""# {stock_name} ({stock_code}) 分析报告
| analysis_time | stock_code | stock_name |
|------|-----|-----|
| {timestamp} | {stock_code} | {stock_name} |
---

{analysis_content}

---
<details >
<summary>📘 分析 prompt</summary>

```markdown
{prompt if prompt else "None"}
```
</details>

---
*本报告由 AI 自动生成，仅供参考，不构成投资建议*
"""
        
        # 写入文件 (覆盖模式)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
    except Exception as e:
        # 静默处理文件写入错误，不影响主流程
        print(f"写入分析报告失败 {stock_code}: {str(e)}")





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
        stock_dict = {stock_item.code+"."+stock_item.market: stock_item for stock_item in result.items[:]}
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




async def judge_via_llm_node(state: AgentState, config: RunnableConfig, writer: StreamWriter):
    """使用后台任务并发分析多只股票"""
    stock_dict = state["stock_dict"]
    if not stock_dict:
        return Command(
            goto=END,
            update={"messages": [AIMessage(content="No stock daily items")]}
        )

    # 创建并发任务列表
    tasks = []
    for stock_code in stock_dict.keys():
        task = analyze_single_stock(state, stock_code, config, writer)
        tasks.append(task)
    
    # 并发执行所有股票分析任务
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    stock_analysis_results = {}
    messages = []
    successful_analyses = 0
    failed_analyses = 0
    
    for result in results:
        if isinstance(result, Exception):
            failed_analyses += 1
            messages.append(AIMessage(content=f"股票分析出现异常: {str(result)}"))
        else:
            stock_code, analysis_content = result
            stock_analysis_results[stock_code] = analysis_content
            # messages.append(AIMessage(content=analysis_content))
            if "分析失败" in analysis_content:
                failed_analyses += 1
            else:
                successful_analyses += 1
    
    # 添加总结消息
    summary_msg = f"股票分析完成: 成功 {successful_analyses} 只，失败 {failed_analyses} 只"
    messages.append(AIMessage(content=summary_msg))
        
    return {
        "messages": messages,
        "stock_analysis_results": stock_analysis_results
    }
    

async def analyze_single_stock(
    state: AgentState, 
    stock_code: str, 
    config: RunnableConfig, 
    writer: StreamWriter | None = None
) -> tuple[str, str]:
    """分析单只股票的异步任务函数"""
    stock_info = state["stock_dict"][stock_code]
    task = Task(f"analyze {stock_code}", writer)
    
    try:
        # 启动任务
        start_time = time.time()
        task.start(data={"stock_code": stock_code, "stock_name": stock_info.name})
        
     
        prompt = build_single_stock_llm_judge_prompt(state, stock_code)
        
        # 调用LLM进行分析
        # task.write_data(data={"status": "正在进行AI分析..."})
        model = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))
        hidden_config = config.copy() if config else {}
        hidden_config["tags"] = hidden_config.get("tags", []) + ["skip_stream"]
        response = await model.ainvoke([HumanMessage(content=prompt)], hidden_config)

        # 写入分析报告文件
        task.write_data(data={"status": "正在写入分析报告..."})
        write_analysis_report(stock_code, stock_info.name, response.content, prompt)
        
        # 完成任务
        # result_summary = response.content[:100] + "..." if len(response.content) > 100 else response.content
        end_time = time.time()
        task.finish(
            result="success", 
            data={
                "stock_code": stock_code,
                "analysis_cost_time": round(end_time - start_time, 2),
                # "analysis_summary": result_summary,
                # "full_analysis": response.content
            }
        )
        
        
        
        return stock_code, response.content
        
    except Exception as e:
        # 任务失败
        task.finish(
            result="error", 
            data={
                "stock_code": stock_code,
                "error": str(e)
            }
        )
        return stock_code, f"分析失败: {str(e)}"


def build_single_stock_llm_judge_prompt(state: AgentState, stock_code: str) -> str:
    basic_info = state["stock_dict"][stock_code]
    daily_items = state["stock_daily_items"][stock_code][:60]
    stock_selection_strategy_description = get_stock_selection_strategy_description(state["stock_selection_strategy"])
    prompt = TRADE_PROMPTS["single_stock_llm_judge_v2"].format(stock_selection_strategy=stock_selection_strategy_description, basic_info=basic_info, daily_items=daily_items)
    return prompt

async def compare_stock_analysis_results_node(state: AgentState, config: RunnableConfig, writer: StreamWriter) -> Command[Literal["__end__"]]:
    stock_analysis_results = state["stock_analysis_results"]
    prompt = await build_compare_stock_analysis_results_prompt(state, stock_analysis_results)
    model = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))
    response = await model.ainvoke([HumanMessage(content=prompt)])
    return {
        "messages": [AIMessage(content=response.content)]
    }

async def build_compare_stock_analysis_results_prompt(state: AgentState, stock_analysis_results: dict[str, str]) -> str:
    prompt = TRADE_PROMPTS["compare_stock_analysis_results"].format(stock_analysis_results=stock_analysis_results)
    return prompt


agent = StateGraph(AgentState)
agent.add_node("stock_pool_node", stock_pool_node)
agent.add_node("process_stock_items_node", process_stock_items_node)
agent.add_node("judge_via_llm_node", judge_via_llm_node)
agent.add_node("compare_stock_analysis_results_node", compare_stock_analysis_results_node)

agent.add_edge(START, "stock_pool_node")
agent.add_edge("stock_pool_node", "process_stock_items_node")
agent.add_edge("process_stock_items_node", "judge_via_llm_node")
agent.add_edge("judge_via_llm_node", "compare_stock_analysis_results_node")
agent.add_edge("compare_stock_analysis_results_node", END)

trading_agent = agent.compile()


