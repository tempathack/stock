"""Database connection and session management.

Provides:
- Async SQLAlchemy engine with connection pooling (pool_size / max_overflow
  from settings)
- ``get_async_session()`` async context-manager for request-scoped sessions
- ``get_pool_status()`` returning live pool metrics
- Legacy ``get_db_connection()`` kept for any remaining sync call-sites
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, contextmanager
from typing import Generator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

# ── Module-level singletons (initialised by init_engine) ─────────────────

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _pg_to_async_url(url: str) -> str:
    """Convert a ``postgresql://`` DSN to ``postgresql+asyncpg://``."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def init_engine(database_url: str, *, pool_size: int = 10, max_overflow: int = 20) -> None:
    """Create the async engine and session factory.

    Must be called once during application startup (e.g. in the lifespan handler).
    """
    global _engine, _session_factory  # noqa: PLW0603
    async_url = _pg_to_async_url(database_url)
    _engine = create_async_engine(
        async_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=600,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    logger.info(
        "async engine initialised",
        extra={"pool_size": pool_size, "max_overflow": max_overflow},
    )


async def dispose_engine() -> None:
    """Dispose of the engine on shutdown."""
    global _engine, _session_factory  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("async engine disposed")


def get_engine() -> AsyncEngine | None:
    """Return the current engine (or ``None`` if not initialised)."""
    return _engine


@asynccontextmanager
async def get_async_session() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async session.

    Callers must check ``get_engine() is not None`` before calling if they
    want to fall back gracefully.
    """
    if _session_factory is None:
        raise RuntimeError("Database engine not initialised — call init_engine() first")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_pool_status() -> dict | None:
    """Return connection pool metrics, or None if engine is unavailable."""
    if _engine is None:
        return None
    pool = _engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.status(),
    }


# ── Legacy synchronous helper (kept for backward compat) ─────────────────


@contextmanager
def get_db_connection(db_url: str | None) -> Generator:
    """Yield a psycopg2 connection, or None if unavailable.

    .. deprecated::
        Prefer ``get_async_session()`` in new code.
    """
    if not db_url:
        yield None
        return

    try:
        import psycopg2
    except ImportError:
        logger.warning("psycopg2 not installed — DB features disabled")
        yield None
        return

    conn = None
    try:
        conn = psycopg2.connect(db_url)
        yield conn
    except Exception:
        logger.exception("Failed to connect to database")
        yield None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
