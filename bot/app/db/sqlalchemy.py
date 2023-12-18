import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from typing import AsyncGenerator

# Загрузка переменных окружения из файла .env
load_dotenv()

# Формирование строки подключения к базе данных
DATABASE_URL = (
    f'postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}'
    f'@{os.getenv("POSTGRES_HOST")}:{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
)

# Создание асинхронного движка для работы с базой данных
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Создание фабрики асинхронных сессий
async_session_factory = async_sessionmaker(async_engine)


# Функция для получения асинхронной сессии
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
