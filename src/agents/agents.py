"""
[INPUT]: 依赖 langgraph 的 CompiledStateGraph/Pregel 类型
         依赖 agents.trade_agent 的 trading_agent
         依赖 agents.bg_task_agent 的 bg_task_agent
         依赖 agents.lazy_agent 的 LazyLoadingAgent
         依赖 schema 的 AgentInfo
[OUTPUT]: 对外提供 DEFAULT_AGENT, agents, get_agent(), get_all_agent_info(), load_agent()
          类型别名 AgentGraph, AgentGraphLike
[POS]: agents/ 的核心注册中心，所有 agent 在此注册，service 通过此模块获取 agent 实例
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from dataclasses import dataclass

from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel import Pregel

from agents.bg_task_agent.bg_task_agent import bg_task_agent
from agents.github_mcp_agent.github_mcp_agent import github_mcp_agent
from agents.lazy_agent import LazyLoadingAgent
from agents.trade_agent import trading_agent
from schema import AgentInfo

DEFAULT_AGENT = "trading-agent"

# Type alias to handle LangGraph's different agent patterns
# - @entrypoint functions return Pregel
# - StateGraph().compile() returns CompiledStateGraph
AgentGraph = CompiledStateGraph | Pregel  # What get_agent() returns (always loaded)
AgentGraphLike = CompiledStateGraph | Pregel | LazyLoadingAgent  # What can be stored in registry


@dataclass
class Agent:
    description: str
    graph_like: AgentGraphLike


agents: dict[str, Agent] = {
    "trading-agent": Agent(description="A trading agent.", graph_like=trading_agent),
    "bg-task-agent": Agent(description="A background task agent.", graph_like=bg_task_agent),
}


async def load_agent(agent_id: str) -> None:
    """Load lazy agents if needed."""
    graph_like = agents[agent_id].graph_like
    if isinstance(graph_like, LazyLoadingAgent):
        await graph_like.load()


def get_agent(agent_id: str) -> AgentGraph:
    """Get an agent graph, loading lazy agents if needed."""
    agent_graph = agents[agent_id].graph_like

    # If it's a lazy loading agent, ensure it's loaded and return its graph
    if isinstance(agent_graph, LazyLoadingAgent):
        if not agent_graph._loaded:
            raise RuntimeError(f"Agent {agent_id} not loaded. Call load() first.")
        return agent_graph.get_graph()

    # Otherwise return the graph directly
    return agent_graph


def get_all_agent_info() -> list[AgentInfo]:
    return [
        AgentInfo(key=agent_id, description=agent.description) for agent_id, agent in agents.items()
    ]
