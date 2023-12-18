import requests
from aiogram import F, Router, types
from aiogram.filters import Command
from app.db.models import File, Message, Scheduler, Ticket
from app.db.sqlalchemy import async_session_factory
from sqlalchemy import and_, or_, select

FILE_PATH: str = '/fox_test/file_storage'

router = Router()


@router.message(F.text, Command('start'))
async def start(message: types.Message):
    help_text = (
        'Просто напишите в чат, что произошло, чтобы оставить свой запрос'
    )
    await message.answer(help_text)


@router.message(F.text)
async def get_msg(message: types.Message):
    async with async_session_factory() as session:
        ticket = await get_or_create_ticket(session, message.chat.id)
        new_message = Message(
            ticket_id=ticket.id,
            user_id=None,
            content=message.text
        )
        session.add(new_message)
        await session.flush()
        await notify_api_service(
            {
                "ticket_id": ticket.id,
                "msg_id": new_message.id,
                "content": new_message.content
            }
        )


@router.message()
async def get_file(message: types.Message):
    if message.content_type == 'document':
        file_id = message.document.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        file_name = message.document.file_name
        async with async_session_factory() as session:
            ticket = await get_or_create_ticket(session, message.chat.id)
            file_extension = file_name.split('.')[-1]
            new_file = File(
                name=file_name,
                ticket_id=ticket.id
            )
            new_file.created_by = None
            session.add(new_file)
            await session.flush()
            file_id = new_file.id
            path_to_save = f'{FILE_PATH}/{file_id}.{file_extension}'
            await message.bot.download_file(file_path, path_to_save)
            new_message = Message(
                ticket_id=ticket.id,
                user_id=None,
                content=f"Пользователь прикрепил файл: file_id={file_id}"
            )
            await session.flush()
            await notify_api_service(
                {
                    "ticket_id": ticket.id,
                    "msg_id": new_message.id,
                    "content": new_message.content
                }
            )


async def get_or_create_ticket(session, telegram_user_id):
    ticket = (
        await session.execute(
            select(Ticket)
            .where(
                and_(
                    Ticket.telegram_user_id == telegram_user_id,
                    or_(Ticket.status_id == 1, Ticket.status_id == 2)
                )
            )
        )
    ).scalar()
    if not ticket:
        scheduler = (
            await session.execute(
                select(Scheduler)
                .where(Scheduler.telegram_user_id == telegram_user_id)
            )
        ).scalar()
        new_ticket = Ticket(
            telegram_user_id=telegram_user_id,
            status_id=1,
            user_id=scheduler.user_id if scheduler else None
        )
        session.add(new_ticket)
        await session.flush()
        return new_ticket
    return ticket


async def notify_api_service(message_data):
    api_url = "http://backend:8000/api/v1/message/notify"
    requests.post(api_url, json=message_data)
