from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class TaskParameters(BaseModel):
    """Arbitrary parameters for a scheduled task."""

    model_config = {
        "extra": "allow",
    }


class TaskConfig(BaseModel):
    name: str = Field(..., description="Unique task name")
    description: str = Field("", description="Task description")
    enabled: bool = Field(True, description="Whether the task is enabled")
    cron: str = Field(..., description="Cron expression (5 fields)")
    agent: str = Field(..., description="Registered agent key, e.g. trading-agent")
    prompt: str = Field(..., description="Input message for the agent, e.g. /e_v1")
    model: str = Field(..., description="Model name to use")
    parameters: TaskParameters | dict[str, Any] | None = Field(
        default_factory=dict, description="Additional parameters passed to the executor"
    )

    @field_validator("cron")
    @classmethod
    def _validate_cron(cls, v: str) -> str:
        # Basic sanity: 5 fields when using from_crontab
        if len(v.split()) != 5:
            raise ValueError("Cron expression must have 5 fields (min hour dom mon dow)")
        return v


class SchedulerSection(BaseModel):
    tasks: list[TaskConfig] = Field(default_factory=list)


class SchedulerConfig(BaseModel):
    scheduler: SchedulerSection = Field(default_factory=SchedulerSection)


def load_scheduler_config(path: str | Path) -> SchedulerConfig:
    """Load and validate scheduler config from YAML."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Scheduler config not found: {p}")
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return SchedulerConfig.model_validate(data)
    except ValidationError:
        # Re-raise with clearer context
        raise

