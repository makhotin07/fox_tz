import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from app.handler import ticket
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    logging.info("START_BOT")
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(ticket.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
