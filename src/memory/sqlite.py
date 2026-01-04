"""
[INPUT]: 依赖 langgraph.checkpoint.sqlite 的 AsyncSqliteSaver
         依赖 langgraph.store.memory 的 InMemoryStore
         依赖 core.settings 的 settings
[OUTPUT]: 对外提供 get_sqlite_saver() → AsyncContextManager[AsyncSqliteSaver]
          get_sqlite_store() → AsyncContextManager[InMemoryStore]
          AsyncInMemoryStore 包装类
[POS]: memory/ 的 SQLite 后端实现，默认开发环境使用
       被 memory/__init__.py 调用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.memory import InMemoryStore

from core.settings import settings


def get_sqlite_saver() -> AbstractAsyncContextManager[AsyncSqliteSaver]:
    """Initialize and return a SQLite saver instance."""
    return AsyncSqliteSaver.from_conn_string(settings.SQLITE_DB_PATH)


class AsyncInMemoryStore:
    """Wrapper for InMemoryStore that provides an async context manager interface."""

    def __init__(self):
        self.store = InMemoryStore()

    async def __aenter__(self):
        return self.store

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # No cleanup needed for InMemoryStore
        pass

    async def setup(self):
        # No-op method for compatibility with PostgresStore
        pass


@asynccontextmanager
async def get_sqlite_store():
    """Initialize and return a store instance for long-term memory.

    Note: SQLite-specific store isn't available in LangGraph,
    so we use InMemoryStore wrapped in an async context manager for compatibility.
    """
    store_manager = AsyncInMemoryStore()
    yield await store_manager.__aenter__()
