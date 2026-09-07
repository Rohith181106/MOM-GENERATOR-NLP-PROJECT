import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

logger = logging.getLogger('mom_backend.database')

# Determine database engine with automatic fallback
DB_URL = settings.POSTGRES_URL
engine = None

try:
    # Test if PostgreSQL is available or if we should use SQLite
    import asyncpg
    # Create postgres engine
    engine = create_async_engine(settings.POSTGRES_URL, echo=False, pool_pre_ping=True)
except Exception:
    logger.warning("PostgreSQL asyncpg driver not loaded or connection unviable; falling back to SQLite.")
    engine = create_async_engine(settings.SQLITE_URL, echo=False)

if engine is None:
    engine = create_async_engine(settings.SQLITE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    global engine, AsyncSessionLocal
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.warning(f"PostgreSQL connection failed ({e}). Switching engine to local SQLite storage.")
        engine = create_async_engine(settings.SQLITE_URL, echo=False)
        AsyncSessionLocal = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("SQLite database tables verified/created successfully.")
