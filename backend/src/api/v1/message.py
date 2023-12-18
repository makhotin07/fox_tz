from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from src.api.v1.schemas import MessageCreate, MessageRead
from src.core.connections import TempConnection
from src.service.message import MessageService, get_message_service
from src.service.user import auth_check

router = APIRouter()


@router.post(
        '/',
        description='Создание сообщение в тикет сотрудником'
    )
@auth_check
async def send(
    request: Request,
    message_data: MessageCreate,
    message_service: MessageService = Depends(get_message_service),
) -> MessageRead:
    auth_user_id = int(request.headers.get('auth_user_id'))
    msg = await message_service.create(message_data, auth_user_id)
    return msg


@router.post('/notify', description='Межсервисное взаимодействие =)')
async def notify(
    message_data: dict
) -> JSONResponse:
    if message_data['ticket_id'] in TempConnection.connections:
        await TempConnection.connections[
            message_data['ticket_id']
        ].send_text(message_data['content'])
    return JSONResponse(content={"status": "Notification received"})
