from datetime import datetime, timedelta
from functools import lru_cache, wraps
from typing import Optional

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from fastapi import Depends, HTTPException, Request

from passlib.hash import pbkdf2_sha256

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas import UserCreate, UserLogin, UserRead
from src.core.config import settings
from src.db.models import User
from src.db.sqlalchemy import async_session_factory, get_async_session


class UserManager:
    """
    Класс для управления пользователями, авторизации и аутентификации.
    Attributes:
        session (AsyncSession): Сессия SQLAlchemy для выполнения асинхронных
            операций с базой данных.
        redis (Redis): Соединение с сервером Redis для управления сессиями.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
            self, user: UserCreate
    ) -> UserRead:
        """
        Создает нового пользователя.
        Args:
            user (UserCreate): Данные нового пользователя.
        Raises:
            HTTPException: Если имя пользователя и/или адрес электронной почты
            уже используются.
        """
        async with self.session.begin():
            existing_records = (await self.session.execute(
                select(
                    User.username
                ).where(
                    (User.username == user.username)
                )
            )).all()
            if existing_records:
                username_exist = any(
                    record.username == user.username
                    for record in existing_records
                )
                if username_exist:
                    raise HTTPException(
                        status_code=409,
                        detail='Имя пользователя уже используется.'
                    )
        user.password = pbkdf2_sha256.hash(user.password)
        try:
            new_user = User(**user.model_dump())
            self.session.add(new_user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'{e}')
        else:
            await self.session.flush()
            new_id = new_user.id
            await self.session.commit()
            return UserRead(id=new_id, username=user.username)

    async def login(
            self,
            user: UserLogin
    ) -> dict:
        async with self.session.begin():
            user_exist = (await self.session.execute(
                select(
                    User
                ).where(
                    (User.username == user.username)
                )
            )).scalar()
            if user_exist:
                # проверяем пароль по хешу из БД
                if pbkdf2_sha256.verify(
                    user.password, hash=user_exist.password
                ):
                    access = await self.create_access_token(user_exist.id)
                    user = UserRead(
                        id=user_exist.id,
                        username=user_exist.username
                    )
                    return access, user
            raise HTTPException(
                status_code=401,
                detail='Неправильный логин или пароль'
            )

    async def logout(self):
        pass

    async def is_valid_token(
            self, token: str, secret: Optional[str] = None
    ) -> bool:
        """
        Проверяет, действителен ли токен.
        Args:
            token (str): Токен для проверки.
            secret (str, optional): Секретный ключ для декодирования токена
            (по умолчанию - из настроек).
        Returns:
            bool: True, если токен действителен, в противном случае - False.
        """
        try:
            _ = jwt.decode(
                token,
                secret if secret else settings.SECRET,
                algorithms=['HS256']
            )
            # Если декодирование прошло успешно, токен действителен
            return True
        except ExpiredSignatureError:
            # Генерируем исключение HTTPException для случая истекшего токена
            raise HTTPException(status_code=403, detail='токен истек')
        except InvalidTokenError as e:
            # Генерируем исключение HTTPException для случая недействительного
            # токена
            raise HTTPException(
                status_code=401, detail=f'токен недействителен, {str(e)}'
            )

    async def create_access_token(self, user_id: int):
        """
        Создает и возвращает токен доступа для пользователя.
        Args:
            user_id (int): Идентификатор пользователя.
        Returns:
            str: Токен доступа.
        """
        secret_key = settings.SECRET
        start_time = datetime.utcnow()
        expiration_time = start_time + timedelta(minutes=30)
        payload = {
            'user_id': user_id,
            'exp': expiration_time
        }
        access_token = jwt.encode(payload, secret_key, algorithm='HS256')
        return access_token

    async def get_current_user(self, request: Request) -> UserRead:
        """
        Возвращает информацию о текущем пользователе на основе токена доступа
        в заголовке запроса.
        Args:
            request (Request): Объект запроса.
        Returns:
            UserRead: Объект с информацией о текущем пользователе.
        """
        access_token = request.headers.get('Authorization')[7:]
        data = jwt.decode(access_token, settings.SECRET, algorithms='HS256')
        return int(data['user_id'])


def auth_check(func):
    """
    Декоратор для проверки аутентификации пользователя.
    Args:
        func (Callable): Функция, требующая проверки аутентификации.
    Returns:
        Callable: Декорированная функция, которая выполняет проверку
        аутентификации перед выполнением функции.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request')
        if request is None:
            raise HTTPException(
                status_code=400,
                detail='Отсутствует объект запроса (request)'
            )
        user_manager = kwargs.get('user_manager', get_user_manager(
            session=async_session_factory())
        )
        authorization_header = request.headers.get('Authorization')
        if not authorization_header:
            raise HTTPException(
                status_code=401,
                detail='Требуется аутентификация'
            )
        access_token = authorization_header[7:]
        if await user_manager.is_valid_token(access_token, settings.SECRET):
            user_id = await user_manager.get_current_user(request)
            request.headers.__dict__["_list"].append(
                ("auth_user_id".encode(), str(user_id).encode())
            )
            return await func(*args, **kwargs)
        else:
            raise HTTPException(
                status_code=401,
                detail='Недействительный токен'
            )
    return wrapper


@lru_cache()
def get_user_manager(
    session: AsyncSession = Depends(get_async_session)
) -> UserManager:
    return UserManager(session)
