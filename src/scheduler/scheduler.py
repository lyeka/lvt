from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import SchedulerConfig, TaskConfig, load_scheduler_config
from .executor import AgentExecutor, ExecutionRecord

logger = logging.getLogger(__name__)


@dataclass
class TaskRuntime:
    config: TaskConfig
    job_id: str


class TaskScheduler:
    """Manage cron-based execution of agents loaded in the app.

    - Loads tasks from YAML config
    - Dynamically adds/removes/updates jobs
    - Exposes runtime status for UI
    """

    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)
        self._scheduler = BackgroundScheduler()
        self._executor = AgentExecutor()
        self._tasks: dict[str, TaskRuntime] = {}
        self._config_mtime: float | None = None
        self._lock = threading.RLock()

        self._scheduler.start(paused=True)
        self.reload_config()

    def _load_config(self) -> SchedulerConfig:
        cfg = load_scheduler_config(self.config_path)
        return cfg

    def _add_or_update_job(self, task: TaskConfig) -> None:
        job_id = f"task::{task.name}"
        trigger = CronTrigger.from_crontab(task.cron)

        # If job exists, remove it to ensure updates take effect cleanly
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)

        self._scheduler.add_job(
            func=self._executor.execute,
            trigger=trigger,
            id=job_id,
            kwargs={
                "task_name": task.name,
                "agent_id": task.agent,
                "prompt": task.prompt,
                "model_name": task.model,
                "parameters": task.parameters if isinstance(task.parameters, dict) else {},
            },
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
            replace_existing=True,
        )
        self._tasks[task.name] = TaskRuntime(config=task, job_id=job_id)

    def _remove_job(self, task_name: str) -> None:
        runtime = self._tasks.get(task_name)
        if runtime and self._scheduler.get_job(runtime.job_id):
            self._scheduler.remove_job(runtime.job_id)
        self._tasks.pop(task_name, None)

    def load_config(self) -> None:
        """Initial load; only adds enabled tasks."""
        cfg = self._load_config()
        with self._lock:
            for task in cfg.scheduler.tasks:
                if task.enabled:
                    self._add_or_update_job(task)
        self._config_mtime = self.config_path.stat().st_mtime

    def reload_config(self) -> None:
        """Hot-reload configuration, updating jobs dynamically."""
        cfg = self._load_config()
        with self._lock:
            new_enabled = {t.name: t for t in cfg.scheduler.tasks if t.enabled}
            existing = set(self._tasks.keys())

            # Remove disabled or deleted
            for name in list(existing - set(new_enabled.keys())):
                self._remove_job(name)

            # Add/update enabled
            for task in new_enabled.values():
                self._add_or_update_job(task)

            self._config_mtime = self.config_path.stat().st_mtime

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
        else:
            self._scheduler.resume()

    def pause(self) -> None:
        self._scheduler.pause()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    def trigger_task(self, task_name: str) -> None:
        """Manually trigger a task by name."""
        with self._lock:
            runtime = self._tasks.get(task_name)
            if not runtime:
                raise ValueError(f"Task not found or not enabled: {task_name}")
            # Run synchronously in this thread
            self._executor.execute(
                task_name=runtime.config.name,
                agent_id=runtime.config.agent,
                prompt=runtime.config.prompt,
                model_name=runtime.config.model,
                parameters=runtime.config.parameters if isinstance(runtime.config.parameters, dict) else {},
            )

    def get_tasks(self) -> list[dict[str, Any]]:
        """Return a list of task info for UI display."""
        with self._lock:
            result: list[dict[str, Any]] = []
            for name, runtime in self._tasks.items():
                job = self._scheduler.get_job(runtime.job_id)
                next_run = job.next_run_time if job else None
                rec: ExecutionRecord = self._executor.get_record(name)
                result.append(
                    {
                        "name": name,
                        "description": runtime.config.description,
                        "enabled": runtime.config.enabled,
                        "cron": runtime.config.cron,
                        "agent": runtime.config.agent,
                        "model": runtime.config.model,
                        "next_run_time": next_run,
                        "last_status": rec.status,
                        "last_started_at": rec.started_at,
                        "last_finished_at": rec.finished_at,
                        "last_error": rec.error,
                        "result_preview": rec.result_preview,
                    }
                )
            return result

