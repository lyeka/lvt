"""
[INPUT]: 依赖 langchain_core.messages 的 BaseMessage
         依赖 langgraph.types 的 StreamWriter
         依赖 agents.utils 的 CustomData
         依赖 schema.task_data 的 TaskData
[OUTPUT]: 对外提供 Task 类
          状态机: new → running → complete
          方法: start(), write_data(), finish()
[POS]: bg_task_agent/ 的任务抽象，封装后台任务的状态管理和消息发送
       被 bg_task_agent.py 和 trade_agent.py 使用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from typing import Literal
from uuid import uuid4

from langchain_core.messages import BaseMessage
from langgraph.types import StreamWriter

from agents.utils import CustomData
from schema.task_data import TaskData


class Task:
    def __init__(self, task_name: str, writer: StreamWriter | None = None) -> None:
        self.name = task_name
        self.id = str(uuid4())
        self.state: Literal["new", "running", "complete"] = "new"
        self.result: Literal["success", "error"] | None = None
        self.writer = writer

    def _generate_and_dispatch_message(self, writer: StreamWriter | None, data: dict):
        writer = writer or self.writer
        task_data = TaskData(name=self.name, run_id=self.id, state=self.state, data=data)
        if self.result:
            task_data.result = self.result
        task_custom_data = CustomData(
            type=self.name,
            data=task_data.model_dump(),
        )
        if writer:
            task_custom_data.dispatch(writer)
        return task_custom_data.to_langchain()

    def start(self, writer: StreamWriter | None = None, data: dict = {}) -> BaseMessage:
        self.state = "new"
        task_message = self._generate_and_dispatch_message(writer, data)
        return task_message

    def write_data(self, writer: StreamWriter | None = None, data: dict = {}) -> BaseMessage:
        if self.state == "complete":
            raise ValueError("Only incomplete tasks can output data.")
        self.state = "running"
        task_message = self._generate_and_dispatch_message(writer, data)
        return task_message

    def finish(
        self,
        result: Literal["success", "error"],
        writer: StreamWriter | None = None,
        data: dict = {},
    ) -> BaseMessage:
        self.state = "complete"
        self.result = result
        task_message = self._generate_and_dispatch_message(writer, data)
        return task_message
