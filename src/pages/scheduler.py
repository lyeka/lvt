from __future__ import annotations

import time
from pathlib import Path

import streamlit as st

try:
    from scheduler import TaskScheduler
    _IMPORT_ERROR: Exception | None = None
except ModuleNotFoundError as e:
    TaskScheduler = None  # type: ignore[assignment]
    _IMPORT_ERROR = e


CONFIG_PATH = Path("config/scheduler_config.yaml")


def _ensure_scheduler() -> TaskScheduler:
    if "_task_scheduler" not in st.session_state:
        scheduler = TaskScheduler(CONFIG_PATH)
        scheduler.start()
        st.session_state["_task_scheduler"] = scheduler
    return st.session_state["_task_scheduler"]


def main() -> None:
    st.set_page_config(page_title="Scheduler", page_icon="⏱️")
    st.title("⏱️ 定时任务调度")
    st.caption("配置文件: `config/scheduler_config.yaml`")

    if _IMPORT_ERROR is not None:
        st.error(
            "未找到 APScheduler 依赖。请安装依赖后重试。\n\n"
            "使用 uv: `uv add apscheduler && uv sync` 或更新锁文件后 `uv sync --frozen`\n\n"
            "或使用 pip: `pip install APScheduler`"
        )
        return

    scheduler = _ensure_scheduler()

    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
    with col1:
        if st.button("🔄 重新加载配置", use_container_width=True):
            try:
                scheduler.reload_config()
                st.success("配置已重新加载")
            except Exception as e:
                st.error(f"重新加载失败: {e}")

    with col2:
        if st.button("▶️ 启动/继续", use_container_width=True):
            scheduler.start()
            st.toast("Scheduler 已启动")
    with col3:
        if st.button("⏸️ 暂停", use_container_width=True):
            scheduler.pause()
            st.toast("Scheduler 已暂停")
    with col4:
        if st.button("🔁 刷新", use_container_width=True):
            time.sleep(0.1)
            st.rerun()

    st.divider()

    tasks = scheduler.get_tasks()
    if not tasks:
        st.info("没有启用中的定时任务。请在配置文件中添加并启用任务。")
        return

    for t in tasks:
        with st.container(border=True):
            header = f"**{t['name']}** — {t['description']}"
            st.markdown(header)
            info_cols = st.columns([1, 1, 1, 1, 1, 1])
            info_cols[0].markdown(f"- 状态: `{t['last_status']}`")
            info_cols[1].markdown(f"- 启用: `{t['enabled']}`")
            info_cols[2].markdown(f"- Cron: `{t['cron']}`")
            info_cols[3].markdown(f"- Agent: `{t['agent']}`")
            info_cols[4].markdown(f"- Model: `{t['model']}`")
            next_run = t["next_run_time"].strftime("%Y-%m-%d %H:%M:%S") if t["next_run_time"] else "—"
            info_cols[5].markdown(f"- 下次执行: `{next_run}`")

            ts_cols = st.columns([1, 1, 2])
            started = t["last_started_at"].strftime("%Y-%m-%d %H:%M:%S") if t["last_started_at"] else "—"
            finished = t["last_finished_at"].strftime("%Y-%m-%d %H:%M:%S") if t["last_finished_at"] else "—"
            ts_cols[0].markdown(f"- 上次开始: `{started}`")
            ts_cols[1].markdown(f"- 上次结束: `{finished}`")

            # Controls
            cc1, cc2 = st.columns([1, 3])
            if cc1.button("⚡ 手动执行", key=f"manual-{t['name']}"):
                try:
                    scheduler.trigger_task(t["name"])
                    st.success("已手动触发执行")
                except Exception as e:
                    st.error(f"手动执行失败: {e}")

            with cc2.expander("执行结果预览", expanded=False):
                if t["last_error"]:
                    st.error(t["last_error"])
                else:
                    st.write(t["result_preview"] or "暂无结果")


if __name__ == "__main__":
    main()
