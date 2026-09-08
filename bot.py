import asyncio
import os
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

# Токен берём из переменной окружения BOT_TOKEN, либо вписываем напрямую
TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")

# Создаём роутер для обработчиков
router = Router()

# Обработчик команды /start
@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("привет")

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # Запускаем поллинг (бесконечный опрос серверов Telegram)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
