from functools import lru_cache

from fastapi import Depends, HTTPException

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas import SchedulerCreate, SchedulerDelete, SchedulerRead
from src.db.models import Scheduler
from src.db.sqlalchemy import get_async_session


class SchedulerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
            self, scheduler_data: SchedulerCreate, auth_user_id: int
    ) -> SchedulerRead:
        async with self.session.begin():
            new_scheduler = Scheduler(
                user_id=auth_user_id,
                telegram_user_id=scheduler_data.telegram_user_id
            )
            try:
                self.session.add(new_scheduler)
                await self.session.flush()
            except IntegrityError:
                raise HTTPException(
                    status_code=400,
                    detail="Правила уже создано."
                )
            scheduler = SchedulerRead(
                id=new_scheduler.id,
                user_id=new_scheduler.user_id,
                telegram_user_id=new_scheduler.telegram_user_id
            )
            await self.session.commit()
        return scheduler

    async def delete(
            self, scheduler_data: SchedulerDelete
    ) -> SchedulerRead:
        async with self.session.begin():
            scheduler = (await self.session.execute(
                select(
                    Scheduler
                ).where(
                    (Scheduler.telegram_user_id ==
                     scheduler_data.telegram_user_id)
                )
            )).scalar()
            if scheduler:
                await self.session.delete(scheduler)
                await self.session.commit()
                return
            raise HTTPException(
                status_code=404,
                detail="Правила для данного telegram_user_id нет."
            )


@lru_cache()
def get_scheduler_service(
    session: AsyncSession = Depends(get_async_session),
) -> SchedulerService:
    return SchedulerService(session)
