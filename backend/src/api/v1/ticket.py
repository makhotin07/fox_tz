import jwt
from fastapi import (APIRouter, Depends, HTTPException, Query, Request,
                     WebSocket, WebSocketDisconnect)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from src.api.v1.schemas import (MessageCreate, TickeDetail, TicketRead,
                                TicketUpdate)
from src.core.config import settings
from src.core.connections import TempConnection
from src.service.message import MessageService, get_message_service
from src.service.ticket import TicketService, get_ticket_service
from src.service.user import auth_check

from .paginator import pagination

router = APIRouter()


@router.get(
        '/',
        description='Вывод списка тасков',
    )
@auth_check
async def get_list(
    request: Request,
    sort: str = '-created_at',
    filter_status: int = Query(
        None,
        alias='filter[status]',
        description=(
            'status_id по которому будет производиться фильтрация проектов'
            )
    ),
    filter_user: int = Query(
        None,
        alias='filter[user]',
        description=(
            'user_id по которому будет производиться фильтрация проектов'
            )
    ),
    page_parameters: dict = Depends(pagination),
    ticket_service: TicketService = Depends(get_ticket_service)
) -> JSONResponse:
    tickets, total_projects = await ticket_service.get_pagination(
        sort=sort,
        filter_status=filter_status,
        filter_user=filter_user,
        page_size=page_parameters['page_size'],
        page_number=page_parameters['page_number'],
    )
    headers = {"total_tickets": str(total_projects)}
    content = jsonable_encoder(tickets)
    return JSONResponse(content=content, headers=headers)


@router.get(
        '/{ticket_id}',
        description='Вывод детальной информации по тикету'
    )
@auth_check
async def detail(
    request: Request,
    ticket_id: int,
    ticket_service: TicketService = Depends(get_ticket_service)
) -> TickeDetail:
    ticket = await ticket_service.get_by_id(ticket_id)
    return ticket


@router.patch(
        '/{ticket_id}',
        description='Обновление тикета по его id'
    )
@auth_check
async def update(
    request: Request,
    ticket_data: TicketUpdate,
    ticket_id: int,
    ticket_service: TicketService = Depends(get_ticket_service)
) -> TicketRead:
    await ticket_service.update(ticket_id, ticket_data)
    ticket = await ticket_service.get_by_id(ticket_id)
    return ticket


@router.websocket(
        "/ws/{ticket_id}"
    )
async def websocket_endpoint(
    websocket: WebSocket,
    ticket_id: int,
    message_service: MessageService = Depends(get_message_service)
):
    await websocket.accept()
    # Сохраняем соединение
    await websocket.send_text("Создано соединение")
    TempConnection.connections[ticket_id] = websocket
    user_id = None
    try:
        while True:
            data = await websocket.receive_text()
            # Так как у нас не передать заголовок при создании соединения, а у
            # нас на нем авторизация,то
            # фронт будет передавать в сокет токен, а мы уже обработаем это.
            if data.startswith('Authorization: '):
                access_token = data.split(": ")[1]
                if not access_token:
                    raise HTTPException(
                        status_code=401,
                        detail='Требуется аутентификация'
                    )
                try:
                    data = jwt.decode(
                        access_token,
                        settings.SECRET,
                        algorithms='HS256'
                    )
                except ExpiredSignatureError:
                    raise HTTPException(
                        status_code=403,
                        detail='токен истек'
                    )
                except InvalidTokenError as e:
                    raise HTTPException(
                        status_code=401,
                        detail=f'токен недействителен, {str(e)}'
                    )
                except Exception as e:
                    # Генерируем общее исключение для других ошибок
                    raise HTTPException(
                        status_code=500,
                        detail=f'ошибка при проверке токена: {str(e)}'
                    )
                user_id = int(data['user_id'])
                data = None
                await websocket.send_text("Авторизация пройдена")
            if user_id and data is not None:
                await message_service.create(
                    MessageCreate(
                        ticket_id=ticket_id,
                        content=data,
                    ),
                    user_id
                )
    except WebSocketDisconnect:
        del TempConnection.connections[ticket_id]
