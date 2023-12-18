import os
from logging import config as logging_config

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from .logger import LOGGING

logging_config.dictConfig(LOGGING)
load_dotenv()


class Settings(BaseSettings):
    # настройки проекта
    PROJECT_NAME: str = 'test_fox'
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # fastapi-users
    SECRET: str = os.getenv('SECRET')

    # Бот
    BOT_API_KEY: str = os.getenv('BOT_TOKEN')

    # тут мы храним временные файлы
    FILE_PATH: str = '/fox_test/file_storage'

    # настройки ДБ
    DB_USER: str = os.getenv('POSTGRES_USER')
    DB_PASS: str = os.getenv('POSTGRES_PASSWORD')
    DB_HOST: str = os.getenv('POSTGRES_HOST')
    DB_PORT: str = os.getenv('POSTGRES_PORT')
    DB_NAME: str = os.getenv('POSTGRES_DB')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'allow'


settings = Settings()
