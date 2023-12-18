import datetime
from typing import List, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import validator
from src.core import json
from src.core.validators.pydantic import PydanticValidator


class BaseModel(PydanticBaseModel):
    class Config:
        json_loads = json.loads
        json_dumps = json.dumps


class UserRead(BaseModel):
    id: int
    username: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserReadWithToken(BaseModel):
    access_token: str
    user: UserRead


class UserCreate(BaseModel):
    username: str
    password: str

    @validator('password')
    def validate_password(cls, v):
        return PydanticValidator.validate_password(v)

    @validator('username')
    def validate_username(cls, v):
        return PydanticValidator.validate_username(v)


class MessageCreate(BaseModel):
    ticket_id: int
    content: str


class MessageReadShort(BaseModel):
    id: int
    user_id: Optional[int]
    content: str
    created_at: datetime.datetime


class MessageRead(MessageReadShort):
    ticket_id: int
    user_id: Optional[UserRead]


class StatusRead(BaseModel):
    id: int
    name: str


class TicketRead(BaseModel):
    id: int
    user_id: Optional[UserRead]
    status: StatusRead
    created_at: datetime.datetime
    updated_at: datetime.datetime


class TickeDetail(TicketRead):
    telegram_user_id: int
    messages: List[MessageReadShort]


class TicketUpdate(BaseModel):
    user_id: Optional[int] = None
    status_id: Optional[int] = None


class SchedulerCreate(BaseModel):
    telegram_user_id: int


class SchedulerRead(SchedulerCreate):
    id: int
    user_id: int


class SchedulerDelete(SchedulerCreate):
    pass


class ReadFile(BaseModel):
    id: int
    name: str


class FileDetail(ReadFile):
    created_at: datetime.datetime
    created_by: Optional[UserRead]


class UploadFile(BaseModel):
    files: List[ReadFile]
    created_by: Optional[UserRead]
