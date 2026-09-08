import os
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# --- Конфигурация из переменных окружения Render ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://onrender.com
WEBHOOK_PATH = "/webhook"               # Путь для вебхука
WEBAPP_HOST = "0.0.0.0"                 # Слушаем все интерфейсы
WEBAPP_PORT = int(os.getenv("PORT", 8443))  # Порт, который мы указали (8443)

# Проверка, что вы не забыли указать переменные на Render
if not BOT_TOKEN or not WEBHOOK_URL:
    raise ValueError("ОШИБКА: Задайте BOT_TOKEN и WEBHOOK_URL в панели Environment на Render!")

# Инициализация бота и диспетчера
router = Router()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Обработчик команды /start ---
@router.message(CommandStart())
async def cmd_start(message: Message):
    # Бот просто пишет "Привет!" в ответ на старт
    await message.answer("Пахан Ткаченко жирный индус")

# --- Функции запуска и остановки вебхука ---
async def on_startup(bot: Bot) -> None:
    # Регистрируем вебхук в самом Telegram
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")
    logging.info(f"Вебхук успешно установлен на адрес: {WEBHOOK_URL}{WEBHOOK_PATH}")

async def on_shutdown(bot: Bot) -> None:
    # Удаляем вебхук при выключении сервера
    await bot.delete_webhook()
    await bot.session.close()

def main():
    # Включаем наш обработчик команд
    dp.include_router(router)

    # Привязываем функции к событиям старта и остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Настраиваем веб-сервер aiohttp
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    # Запускаем сервер
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == "__main__":
    # Включаем логирование, чтобы видеть ошибки в панели Render
    logging.basicConfig(level=logging.INFO)
    main()
