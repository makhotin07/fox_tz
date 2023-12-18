from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import settings as s


DATABASE_URL = f'postgresql+asyncpg://{s.DB_USER}:{s.DB_PASS}@{s.DB_HOST}:{s.DB_PORT}/{s.DB_NAME}'

async_engine = create_async_engine(DATABASE_URL, echo=True)

async_session_factory = async_sessionmaker(async_engine)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
