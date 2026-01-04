"""
[INPUT]: 依赖 langchain_core 的 HumanMessage, RunnableConfig
         依赖 agents 的 get_agent
         依赖 core 的 settings
         依赖 schema.models 的 AllModelEnum
[OUTPUT]: 对外提供 AgentExecutor 类 (execute, aexecute)
          ExecutionRecord 数据类 (任务执行状态)
[POS]: scheduler/ 的执行器，负责实际调用 agent 并记录执行结果
       被 scheduler.scheduler.TaskScheduler 使用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from agents import get_agent
from core import settings
from enum import StrEnum
from schema.models import AllModelEnum


@dataclass
class ExecutionRecord:
    started_at: datetime | None = None
    finished_at: datetime | None = None
    status: str = "idle"  # idle | running | success | error
    error: str | None = None
    result_preview: str | None = None


class AgentExecutor:
    """Executes configured agents with provided prompt/model.

    Integrates with the existing agent system. Keeps a lightweight execution record
    to be displayed by the UI.
    """

    def __init__(self) -> None:
        # In-memory tracking of last execution per task
        self.records: dict[str, ExecutionRecord] = {}

    def get_record(self, task_name: str) -> ExecutionRecord:
        return self.records.setdefault(task_name, ExecutionRecord())

    def _resolve_model(self, name: AllModelEnum | str | None) -> AllModelEnum:
        """Coerce string model name to AllModelEnum, defaulting to settings.DEFAULT_MODEL.

        - If `name` is already a StrEnum and in AVAILABLE_MODELS, use it
        - If `name` is a string, match by `.value` within AVAILABLE_MODELS
        - Otherwise, return DEFAULT_MODEL
        """
        if isinstance(name, StrEnum):
            # type: ignore[unreachable]
            if name in settings.AVAILABLE_MODELS:
                return name  # type: ignore[return-value]
        if isinstance(name, str):
            for m in settings.AVAILABLE_MODELS:
                if getattr(m, "value", None) == name:
                    return m
        # Fallback
        if settings.DEFAULT_MODEL is None:
            raise ValueError("DEFAULT_MODEL is not configured")
        return settings.DEFAULT_MODEL

    async def aexecute(self, *, task_name: str, agent_id: str, prompt: str,
                       model_name: AllModelEnum | str | None,
                       parameters: dict[str, Any] | None = None) -> None:
        rec = self.get_record(task_name)
        rec.started_at = datetime.utcnow()
        rec.finished_at = None
        rec.status = "running"
        rec.error = None
        rec.result_preview = None

        try:
            agent = get_agent(agent_id)

            # Build a fresh run/thread context for this execution
            model_enum = self._resolve_model(model_name)

            config = RunnableConfig(
                configurable={
                    "thread_id": str(uuid4()),
                    "user_id": "scheduler",
                    "model": model_enum,
                }
            )

            # Pass the prompt as a human message
            events = await agent.ainvoke(
                input={"messages": [HumanMessage(content=prompt)]},
                config=config,
                stream_mode=["updates", "values"],
            )

            # Extract final result (same pattern as service.invoke)
            response_type, response = events[-1]
            content = None
            if response_type == "values":
                try:
                    msgs = response["messages"]
                    content = msgs[-1].content if msgs else None
                except Exception:
                    content = None
            elif response_type == "updates" and "__interrupt__" in response:
                interrupts = response["__interrupt__"] or []
                content = interrupts[0].value if interrupts else None

            # Update record
            rec.status = "success"
            rec.result_preview = (content or "").strip()[:2000]
        except Exception as e:
            rec.status = "error"
            rec.error = str(e)
        finally:
            rec.finished_at = datetime.utcnow()

    def execute(self, *, task_name: str, agent_id: str, prompt: str,
                model_name: AllModelEnum | str | None,
                parameters: dict[str, Any] | None = None) -> None:
        """Synchronous wrapper for APScheduler."""
        # Run each job in its own event loop
        asyncio.run(
            self.aexecute(
                task_name=task_name,
                agent_id=agent_id,
                prompt=prompt,
                model_name=model_name,
                parameters=parameters or {},
            )
        )
