import logging
from functools import lru_cache

import requests

from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas import MessageCreate, MessageRead, UserRead
from src.core.config import settings
from src.db.models import Message, Ticket, User
from src.db.sqlalchemy import get_async_session
from src.core.connections import TempConnection


class MessageService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
            self, message_data: MessageCreate, auth_user_id: int
    ) -> MessageRead:
        async with self.session.begin():
            ticket = await self.session.get(Ticket, message_data.ticket_id)
            if not ticket:
                raise HTTPException(
                    status_code=404,
                    detail=f'Тикета с id={message_data.ticket_id} нет.'
                )
            if ticket.user_id != auth_user_id or ticket.status_id != 2:
                # это что бы все подряд не писали в тикет и в дальнейшем можно
                # нужно будет логи добавить что бы видеть кто кому писал.
                msg = (
                        'Что бы отправить сообщение в рамках этого тикета, '
                        'необходимо поставить себя исполнителем.'
                        'И Установить статус в работе!'
                )
                conn = TempConnection.connections.get(ticket.id, None)
                if conn:
                    await TempConnection.connections[ticket.id].send_text(msg)
                raise HTTPException(
                    status_code=403,
                    detail=msg
                )
            new_message = Message(
                ticket_id=message_data.ticket_id,
                user_id=auth_user_id,
                content=message_data.content

            )
            user = await self.session.get(User, auth_user_id)
            self.session.add(new_message)
            await self.session.flush()
            msg = MessageRead(
                id=new_message.id,
                user_id=UserRead(
                    id=user.id,
                    username=user.username
                ),
                ticket_id=new_message.ticket_id,
                content=new_message.content,
                created_at=new_message.created_at

            )
            await self.send_msg(new_message.content, ticket.telegram_user_id)
            await self.session.commit()
        return msg

    async def send_msg(self, msg: str, chat_id: str) -> None:
        data = {
            'chat_id': chat_id,
            'text': msg
        }
        TELEGRAM_API_URL = (
            f'https://api.telegram.org/bot'
            f'{settings.BOT_API_KEY}/sendMessage'
        )
        response = requests.post(TELEGRAM_API_URL, data=data)
        if response.status_code == 200:
            logging.info("Сообщение успешно отправлено")
        else:
            logging.error(
                "Ошибка при отправке сообщения:", response.text
            )


@lru_cache()
def get_message_service(
    session: AsyncSession = Depends(get_async_session),
) -> MessageService:
    return MessageService(session)
