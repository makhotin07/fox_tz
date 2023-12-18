import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer  # для тестов
from src.api.v1.paginator import pagination
from src.db.models import File as FileModel
from src.service.file import FileService, get_file_service
from src.service.user import auth_check

from .schemas import UploadFile as ShemaUploadFile

router = APIRouter()

security = HTTPBearer()  # для тестов


@router.post(
        '/add_to_ticket/{ticket_id}', description='Загрузить файлы'
    )
@auth_check
async def upload(
    request: Request,
    ticket_id: int,
    files: Annotated[
        list[UploadFile], File(description='Загрузка нескольких файлов')
    ],
    file_service: FileService = Depends(get_file_service)
) -> ShemaUploadFile:
    auth_user_id = int(request.headers.get('auth_user_id'))
    files = await file_service.upload(request, files, auth_user_id, ticket_id)
    return files


@router.get('/{file_id}', description='Скачать файл')
@auth_check
async def download(
    request: Request,
    file_id: int,
    file_service: FileService = Depends(get_file_service)
) -> ShemaUploadFile:
    file = await file_service.download(request, file_id)
    return file


@router.get('/', description='Получить файлы')
@auth_check
async def get_files(
    request: Request,
    sort: str = '-created_at',
    filter_ticket: int = Query(
        None,
        alias='filter[ticket_id]',
        description=(
            'ticket_id по которому будет производиться фильтрация файлов'
        )
    ),
    page_parameters: dict = Depends(pagination),
    file_service: FileService = Depends(get_file_service)
) -> JSONResponse:
    files, total_files = await file_service.get_file_pagination(
        sort=sort,
        filter_ticket=filter_ticket,
        page_size=page_parameters['page_size'],
        page_number=page_parameters['page_number'],
    )
    headers = {"total_files": str(total_files)}
    content = jsonable_encoder(files)
    return JSONResponse(content=content, headers=headers)
