"""
[INPUT]: 依赖 langchain_core.messages 的 ChatMessage
         依赖 langgraph.types 的 StreamWriter
         依赖 pydantic 的 BaseModel
[OUTPUT]: 对外提供 CustomData 类
          to_langchain() - 转换为 LangChain 消息
          dispatch() - 通过 StreamWriter 发送
[POS]: agents/ 的工具类，用于在 agent 执行期间发送自定义数据消息
       被 bg_task_agent/task.py 使用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from typing import Any

from langchain_core.messages import ChatMessage
from langgraph.types import StreamWriter
from pydantic import BaseModel, Field


class CustomData(BaseModel):
    "Custom data being sent by an agent"

    data: dict[str, Any] = Field(description="The custom data")

    def to_langchain(self) -> ChatMessage:
        return ChatMessage(content=[self.data], role="custom")

    def dispatch(self, writer: StreamWriter) -> None:
        writer(self.to_langchain())
