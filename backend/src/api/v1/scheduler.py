from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from src.api.v1.schemas import SchedulerCreate, SchedulerDelete, SchedulerRead
from src.service.scheduler import SchedulerService, get_scheduler_service
from src.service.user import auth_check

router = APIRouter()


@router.post(
        '/',
        description=('Автоматически устанавливать на тикеты пользователя '
                     'сотрудника')
    )
@auth_check
async def create(
    request: Request,
    scheduler_data: SchedulerCreate,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> SchedulerRead:
    auth_user_id = int(request.headers.get('auth_user_id'))
    scheduler = await scheduler_service.create(scheduler_data, auth_user_id)
    return scheduler


@router.delete(
        '/',
        description='Убрать автоопределение сотрудника на тикеты пользователя'
    )
@auth_check
async def delete(
    request: Request,
    scheduler_data: SchedulerDelete,
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
) -> JSONResponse:
    await scheduler_service.delete(scheduler_data)
    return JSONResponse(status_code=200, content='Правило успешно удалено.')
