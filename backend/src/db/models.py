import datetime
from typing import Annotated, Optional

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

created_at = Annotated[datetime.datetime, mapped_column(
    TIMESTAMP(timezone=True),
    server_default=text("TIMEZONE('utc', now())")
)]
updated_at = Annotated[datetime.datetime, mapped_column(
    TIMESTAMP(timezone=True),
    server_default=text("TIMEZONE('utc', now())"),
    onupdate=datetime.datetime.utcnow
)]

timestamp = Annotated[datetime.date, mapped_column(
    TIMESTAMP(timezone=True),
    server_default=text("TIMEZONE('utc', now())"),
)]


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password: Mapped[str] = mapped_column(String(128))

    tickets: Mapped[list['Ticket']] = relationship(
        back_populates='user', uselist=True, cascade='all, delete'
    )

    files: Mapped[list['File']] = relationship(
        back_populates='user', uselist=True, cascade='all, delete'
    )

    messages: Mapped[list['Message']] = relationship(
        back_populates='user', uselist=True, cascade='all, delete'
    )

    def __repr__(self):
        return f'<User {self.username}>'


class Status(Base):
    __tablename__ = 'status'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))

    tickets: Mapped[list['Ticket']] = relationship(
        back_populates='status', uselist=True
    )

    def __repr__(self):
        return f'<Status {self.name}>'


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int]
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))
    status_id: Mapped[int] = mapped_column(ForeignKey('status.id'))
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    user: Mapped['User'] = relationship(
        back_populates='tickets', uselist=False
    )

    messages: Mapped[list['Message']] = relationship(
        back_populates='ticket', uselist=True
    )
    status: Mapped['Status'] = relationship(
        back_populates='tickets', uselist=False
    )
    files: Mapped[list['File']] = relationship(
        back_populates='ticket', uselist=True
    )


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("ticket.id"))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))
    # в телеграмме ограничение на пост с медиа и файлами 1024 символа
    content: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[created_at]

    ticket: Mapped['Ticket'] = relationship(
        back_populates='messages', uselist=False, cascade='all, delete'
    )

    user: Mapped['User'] = relationship(
        back_populates='messages', uselist=False
    )


class File(Base):
    __tablename__ = 'file'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    ticket_id: Mapped[int] = mapped_column(ForeignKey('ticket.id'))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))
    created_at: Mapped[created_at]

    user: Mapped['User'] = relationship(
        back_populates='files', uselist=False
    )

    ticket: Mapped['Ticket'] = relationship(
        back_populates='files', uselist=False
    )

    def __repr__(self):
        return f'<File {self.name}>'


class Scheduler(Base):
    __tablename__ = 'scheduler'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))
    telegram_user_id: Mapped[int] = mapped_column(Integer, unique=True)
