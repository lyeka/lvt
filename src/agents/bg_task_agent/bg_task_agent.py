"""
[INPUT]: 依赖 langchain_core 的 LLM 和消息类型
         依赖 langgraph 的 StateGraph, StreamWriter
         依赖 agents.bg_task_agent.task 的 Task
         依赖 core 的 get_model, settings
[OUTPUT]: 对外提供 bg_task_agent (CompiledStateGraph)
          AgentState, wrap_model(), acall_model(), bg_task()
[POS]: bg_task_agent/ 的核心 agent，演示后台任务进度流式输出
       在 agents.agents 中注册
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
import asyncio

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda, RunnableSerializable
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.types import StreamWriter

from agents.bg_task_agent.task import Task
from core import get_model, settings


class AgentState(MessagesState, total=False):
    """`total=False` is PEP589 specs.

    documentation: https://typing.readthedocs.io/en/latest/spec/typeddict.html#totality
    """


def wrap_model(model: BaseChatModel) -> RunnableSerializable[AgentState, AIMessage]:
    preprocessor = RunnableLambda(
        lambda state: state["messages"],
        name="StateModifier",
    )
    return preprocessor | model  # type: ignore[return-value]


async def acall_model(state: AgentState, config: RunnableConfig) -> AgentState:
    m = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))
    model_runnable = wrap_model(m)
    response = await model_runnable.ainvoke(state, config)

    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


async def bg_task(state: AgentState, writer: StreamWriter) -> AgentState:
    task1 = Task("Simple task 1...", writer)
    task2 = Task("Simple task 2...", writer)

    task1.start()
    await asyncio.sleep(2)
    task2.start()
    await asyncio.sleep(2)
    task1.write_data(data={"status": "Still running..."})
    await asyncio.sleep(2)
    task2.finish(result="error", data={"output": 42})
    await asyncio.sleep(2)
    task1.finish(result="success", data={"output": 42})
    return {"messages": []}


# Define the graph
agent = StateGraph(AgentState)
agent.add_node("model", acall_model)
agent.add_node("bg_task", bg_task)
agent.set_entry_point("bg_task")

agent.add_edge("bg_task", "model")
agent.add_edge("model", END)

bg_task_agent = agent.compile()
