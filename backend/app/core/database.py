import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Determine database URL - use SQLite for local dev if no PostgreSQL available
_database_url = settings.DATABASE_URL
if _database_url.startswith("postgresql"):
    # For local dev without PostgreSQL, fall back to SQLite
    if not os.environ.get("DATABASE_URL"):
        try:
            import asyncpg

            # Quick check if PostgreSQL is reachable
            import asyncio

            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                asyncpg.connect(
                    _database_url.replace("postgresql+asyncpg://", "postgresql://")
                )
            )
            loop.close()
        except Exception:
            _database_url = "sqlite+aiosqlite:///./blacksentinel_pulse.db"

engine = create_async_engine(
    _database_url,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    **({"pool_size": 20, "max_overflow": 10} if "sqlite" not in _database_url else {}),
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class Neo4jDriver:
    """Neo4j async driver singleton."""

    _driver = None

    @classmethod
    async def get_driver(cls):
        try:
            from neo4j import AsyncGraphDatabase

            if cls._driver is None:
                cls._driver = AsyncGraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                )
            return cls._driver
        except Exception:
            return None

    @classmethod
    async def close(cls):
        if cls._driver:
            await cls._driver.close()
            cls._driver = None


async def get_db() -> AsyncSession:
    """Dependency for getting async database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_neo4j():
    """Dependency for getting Neo4j sessions."""
    driver = await Neo4jDriver.get_driver()
    if driver is None:
        yield None
        return
    async with driver.session() as session:
        yield session


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
