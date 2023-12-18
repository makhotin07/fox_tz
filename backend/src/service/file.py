import logging
from functools import lru_cache
from typing import List, Tuple
import requests

from fastapi import Depends, HTTPException, Request, UploadFile
from starlette.responses import FileResponse

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.v1.schemas import FileDetail, ReadFile
from src.api.v1.schemas import UploadFile as ShemaUploadFile
from src.api.v1.schemas import UserRead
from src.core.config import settings
from src.db.models import File, Ticket, User
from src.db.sqlalchemy import get_async_session


class FileService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upload(
            self, request: Request,
            files: list[UploadFile],
            auth_user_id: int,
            ticket_id: int
    ):
        async with self.session.begin():
            user = await self.session.get(User, auth_user_id)

            user_shema = UserRead(
                id=user.id,
                username=user.username
            )
            ticket = await self.session.get(Ticket, ticket_id)
            if ticket:
                file_schemas = []
                for file in files:
                    file_extension = file.filename.split('.')[-1]
                    new_file = File(
                        name=file.filename,
                        ticket_id=ticket_id
                    )
                    new_file.created_by = user.id
                    self.session.add(new_file)
                    await self.session.flush()
                    file_id = new_file.id
                    content = file.file.read()
                    with open(
                        f'{settings.FILE_PATH}/{file_id}.{file_extension}',
                        'wb'
                    ) as f:
                        f.write(content)
                    await self.send_file(
                        file_id,
                        file_extension,
                        file.filename,
                        ticket.telegram_user_id
                    )
                    file_shema = ReadFile(
                        id=file_id,
                        name=file.filename
                    )
                    file_schemas.append(file_shema)
                await self.session.commit()
            else:
                raise HTTPException(
                    status_code=404,
                    detail='Несуществующий ticket_id'
                )

        return ShemaUploadFile(created_by=user_shema, files=file_schemas)

    async def download(self, request: Request, file_id: int):
        async with self.session.begin():
            file = await self.session.get(File, file_id)
            if not file:
                raise HTTPException(
                    status_code=404,
                    detail=f'file_id={file_id} не существует'
                )
            return FileResponse(
                f'{settings.FILE_PATH}/{file.id}.{file.name.split(".")[-1]}',
                media_type='application/octet-stream',
                filename=file.name
            )

    async def send_file(
            self,
            file_id: int,
            file_extension: str,
            file_name: str,
            telegram_user_id: int
    ):
        url = (
            f'https://api.telegram.org/bot{settings.BOT_API_KEY}/sendDocument'
        )
        with open(
            f'{settings.FILE_PATH}/{file_id}.{file_extension}', 'rb'
        ) as file:
            # Подготавливаем данные для отправки
            files = {'document': (file_name, file)}
            data = {'chat_id': telegram_user_id}

            # Отправляем запрос
            response = requests.post(url, data=data, files=files)

        # Обрабатываем результат
        if response.status_code == 200:
            logging.info('Файл успешно отправлен')
        else:
            logging.error(
                f'Ошибка при отправке файла. Код: {response.status_code}, '
                f'Текст: {response.text}'
            )

    async def get_file_pagination(
        self,
        sort: str,
        page_size: int,
        filter_ticket: int,
        page_number: int
    ) -> Tuple[List[FileDetail], int]:
        async with self.session.begin():
            offset = (page_number - 1) * page_size
            sort_by = getattr(File, sort.replace('-', ''), File.created_at)
            query = select(
                    File
                ).options(
                    selectinload(File.user)
                )
            total_query = select(func.count('*')).select_from(File)
            if filter_ticket:
                query = query.where(
                    File.ticket_id == filter_ticket
                )
                total_query = total_query.where(
                    File.ticket_id == filter_ticket
                )
            query = query.offset(
                    offset
                ).limit(
                    page_size
                ).order_by(
                    desc(sort_by) if sort.startswith('-') else sort_by
                )
            files = (await self.session.scalars(query)).all()
            total_files = (await self.session.execute(total_query)).scalar()
            files_result = []
            for file in files:
                files_result.append(FileDetail(
                    id=file.id,
                    name=file.name,
                    created_by=UserRead(
                        id=file.user.id,
                        username=file.user.username,
                    ) if file.user else None,
                    created_at=file.created_at
                ))
            return files_result, total_files


@lru_cache()
def get_file_service(
    session: AsyncSession = Depends(get_async_session),
) -> FileService:
    return FileService(session)
