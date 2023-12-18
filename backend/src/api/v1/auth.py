from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from src.api.v1.schemas import (UserCreate, UserLogin, UserRead,
                                UserReadWithToken)
from src.service.user import UserManager, get_user_manager

router = APIRouter()


@router.post('/registration')
async def registration(
    user: UserCreate,
    user_manager: UserManager = Depends(get_user_manager)
) -> UserRead:
    user = await user_manager.create(user)
    return user


@router.post('/login')
async def login(
    user: UserLogin,
    user_manager: UserManager = Depends(get_user_manager)
) -> JSONResponse:
    access, user_data = await user_manager.login(user)
    user_data = UserReadWithToken(access_token=access, user=user_data)
    return JSONResponse(content=user_data.model_dump())


# @router.post('/logout')
# async def logout(
#     user_manager: UserManager = Depends(get_user_manager)
# ) -> JSONResponse:
#     pass
#     так как у нас простая аутентификация по аксес токену,
#     который выдается на опр. время, то можно просто организовать удаление
#     токена из памяти приложения на фронте :)
