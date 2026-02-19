"""
Database Connection and Session Management
PostgreSQL with async SQLAlchemy
"""

import structlog
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Global engine and session factory
_engine = None
_session_factory = None


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def init_db() -> None:
    """Initialize database connection and create tables."""
    global _engine, _session_factory
    
    # Convert postgres:// to postgresql+asyncpg://
    db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    _engine = create_async_engine(
        db_url,
        echo=settings.DEBUG,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
    )
    
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized", url=db_url.split("@")[1] if "@" in db_url else "")


async def close_db() -> None:
    """Close database connection."""
    global _engine
    if _engine:
        await _engine.dispose()
        logger.info("Database connection closed")


async def get_session() -> AsyncSession:
    """
    Get database session.
    
    Usage:
        async with get_session() as session:
            result = await session.execute(...)
    """
    global _session_factory
    if not _session_factory:
        raise RuntimeError("Database not initialized")
    
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_health() -> bool:
    """Check database connection health."""
    global _engine
    if not _engine:
        return False
    
    try:
        async with _engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False
