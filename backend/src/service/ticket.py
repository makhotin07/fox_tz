from functools import lru_cache
from typing import List

from fastapi import Depends, HTTPException

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.v1.schemas import (MessageReadShort, StatusRead, TickeDetail,
                                TicketRead, TicketUpdate, UserRead)
from src.db.models import Ticket, User
from src.db.sqlalchemy import get_async_session


class TicketService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pagination(
        self,
        sort: str,
        filter_status: int,
        filter_user: int,
        page_size: int,
        page_number: int
    ) -> List[TicketRead]:
        offset = (page_number - 1) * page_size
        sort_by = getattr(Ticket, sort.replace('-', ''), Ticket.id)
        async with self.session.begin():
            total_query = select(func.count('*')).select_from(Ticket)
            query = select(
                    Ticket
                ).options(
                    selectinload(
                        Ticket.messages
                    ),
                    selectinload(
                        Ticket.status
                    ),
                    selectinload(
                        Ticket.user
                    )
                )
            if filter_status:
                query = query.where(
                    Ticket.status_id == filter_status
                )
                total_query = total_query.where(
                    Ticket.status_id == filter_status
                )
            if filter_user:
                query = query.where(
                    Ticket.user_id == filter_user
                )
                total_query = total_query.where(
                    Ticket.user_id == filter_user
                )

            query = query.order_by(
                desc(sort_by) if sort.startswith('-') else sort_by
            ).offset(
                offset
            ).limit(
                page_size
            )
            tickets = (await self.session.scalars(query)).all()
            ticket_list = [TicketRead(
                    id=x.id,
                    user_id=UserRead(
                        id=x.user.id,
                        username=x.user.username
                    ) if x.user_id is not None else None,
                    status=StatusRead(
                        id=x.status.id,
                        name=x.status.name
                    ),
                    created_at=x.created_at,
                    updated_at=x.updated_at
                ) for x in tickets]
            total_ticket = (await self.session.execute(total_query)).scalar()
        return ticket_list, total_ticket

    async def get_by_id(self, ticket_id: str) -> TickeDetail:
        async with self.session.begin():
            ticket = await self.session.get(
                Ticket,
                ticket_id,
                options=(
                    selectinload(Ticket.messages),
                    selectinload(Ticket.status),
                    selectinload(Ticket.user),
                )
            )
            if not ticket:
                raise HTTPException(
                    status_code=404, detail='Ticket с таким id не существует'
                )
            ticket_return = TickeDetail(
                id=ticket.id,
                telegram_user_id=ticket.telegram_user_id,
                status=StatusRead(
                    id=ticket.status.id,
                    name=ticket.status.name
                ),
                created_at=ticket.created_at,
                updated_at=ticket.updated_at,
                user_id=UserRead(
                    id=ticket.user.id,
                    username=ticket.user.username
                ) if ticket.user_id is not None else None,
                messages=[MessageReadShort(
                    id=x.id,
                    user_id=x.user_id,
                    content=x.content,
                    created_at=x.created_at
                ) for x in ticket.messages]
            )
            return ticket_return

    async def update(self, ticket_id: int, ticket_data: TicketUpdate) -> int:
        if ticket_data:
            async with self.session.begin():
                ticket = await self.session.get(
                    Ticket,
                    ticket_id,
                    options=(
                        selectinload(Ticket.messages),
                    )
                )
                if not ticket:
                    raise HTTPException(
                        status_code=404,
                        detail="Несуществующий тикет"
                    )
                if ticket_data.status_id:
                    ticket.status_id = ticket_data.status_id
                if ticket_data.user_id:
                    user = await self.session.get(User, ticket_data.user_id)
                    if user:
                        ticket.user_id = ticket_data.user_id
                    else:
                        raise HTTPException(
                            status_code=404,
                            detail=(
                                f'Пользователь с id={ticket_data.user_id} не '
                                'существует.'
                            )
                        )
                await self.session.commit()
                return
        raise HTTPException(status_code=400, detail='Пустой запрос')


@lru_cache()
def get_ticket_service(
    session: AsyncSession = Depends(get_async_session),
) -> TicketService:
    return TicketService(session)
