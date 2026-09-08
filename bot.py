import os
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8443))

if not BOT_TOKEN or not WEBHOOK_URL:
    raise ValueError("ОШИБКА: Задайте BOT_TOKEN и WEBHOOK_URL в панели Environment на Render!")

router = Router()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

auto_responses = {}

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Пахан Ткаченко жирный индус")

@router.message(F.text.startswith('.automessage'))
async def set_auto_message(message: Message):
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.answer("Использование: .automessage (СООБЩЕНИЕ)")
        return
    
    auto_text = parts[1]
    
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        auto_responses[target_user_id] = auto_text
        await message.answer(f"Автоответ для пользователя {target_user_id} установлен: {auto_text}")
    else:
        auto_responses['all'] = auto_text
        await message.answer(f"Автоответ для всех установлен: {auto_text}")

@router.message(F.text.startswith('.stopautomessage'))
async def stop_auto_message(message: Message):
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        if target_user_id in auto_responses:
            del auto_responses[target_user_id]
            await message.answer(f"Автоответ для пользователя {target_user_id} удален")
        else:
            await message.answer("Для этого пользователя нет автоответа")
    else:
        if 'all' in auto_responses:
            del auto_responses['all']
            await message.answer("Автоответ для всех удален")
        else:
            await message.answer("Нет установленных автоответов")

@router.message()
async def handle_messages(message: Message):
    if message.text and not message.text.startswith('.'):
        if message.from_user.id in auto_responses:
            await message.answer(auto_responses[message.from_user.id])
        elif 'all' in auto_responses:
            await message.answer(auto_responses['all'])

async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")
    logging.info(f"Вебхук успешно установлен на адрес: {WEBHOOK_URL}{WEBHOOK_PATH}")

async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    await bot.session.close()

def main():
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
