import datetime

from sqlalchemy import (
    TIMESTAMP, ForeignKey, Integer, String, text, Column, Integer, String, Date
)
from sqlalchemy.orm import DeclarativeBase, relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True)
    password = Column(String(128))

    tickets = relationship('Ticket', back_populates='user', uselist=True, cascade='all, delete')
    files = relationship('File', back_populates='user', uselist=True, cascade='all, delete')
    messages = relationship('Message', back_populates='user', uselist=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Status(Base):
    __tablename__ = 'status'

    id = Column(Integer, primary_key=True)
    name = Column(String(128))

    tickets = relationship('Ticket', back_populates='status', uselist=True)

    def __repr__(self):
        return f'<Status {self.name}>'


class Ticket(Base):
    __tablename__ = "ticket"

    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(Integer)
    user_id = Column(Integer, ForeignKey('user.id'))
    status_id = Column(Integer, ForeignKey('status.id'))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("TIMEZONE('utc', now())"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("TIMEZONE('utc', now())"),
                        onupdate=datetime.datetime.utcnow)

    user = relationship('User', back_populates='tickets', uselist=False)
    messages = relationship('Message', back_populates='ticket', uselist=True)
    status = relationship('Status', back_populates='tickets', uselist=False)
    files = relationship('File', back_populates='ticket', uselist=True)


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("ticket.id"))
    user_id = Column(Integer, ForeignKey('user.id'))
    content = Column(String(1024))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("TIMEZONE('utc', now())"))

    ticket = relationship('Ticket', back_populates='messages', uselist=False, cascade='all, delete')
    user = relationship('User', back_populates='messages', uselist=False)


class File(Base):
    __tablename__ = 'file'
    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    ticket_id = Column(Integer, ForeignKey('ticket.id'))
    created_by = Column(Integer, ForeignKey('user.id'))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("TIMEZONE('utc', now())"))

    user = relationship('User', back_populates='files', uselist=False)
    ticket = relationship('Ticket', back_populates='files', uselist=False)

    def __repr__(self):
        return f'<File {self.name}>'


class Scheduler(Base):
    __tablename__ = 'scheduler'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    telegram_user_id = Column(Integer, unique=True)
