import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, ChatTypeFilter
from aiogram.types import Message
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
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

async def safe_send_message(message: Message, text: str, retries: int = 3):
    for attempt in range(retries):
        try:
            await message.answer(text)
            return True
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except TelegramNetworkError:
            if attempt == retries - 1:
                logging.error(f"Не удалось отправить сообщение после {retries} попыток")
            else:
                await asyncio.sleep(1 * (attempt + 1))
        except Exception as e:
            logging.error(f"Ошибка отправки: {e}")
            return False
    return False

# Работает только в личных сообщениях
@router.message(CommandStart(), ChatTypeFilter(chat_type="private"))
async def cmd_start(message: Message):
    await safe_send_message(message, "Пахан Ткаченко жирный индус")

# Команды только в личных сообщениях
@router.message(F.text.startswith('.automessage'), ChatTypeFilter(chat_type="private"))
async def set_auto_message(message: Message):
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await safe_send_message(message, "Использование: .automessage (текст)")
        return
    
    auto_text = parts[1]
    user_id = message.from_user.id
    auto_responses[user_id] = auto_text
    await safe_send_message(message, f"✅ Автоответ установлен: {auto_text}")

@router.message(F.text.startswith('.stopautomessage'), ChatTypeFilter(chat_type="private"))
async def stop_auto_message(message: Message):
    user_id = message.from_user.id
    if user_id in auto_responses:
        del auto_responses[user_id]
        await safe_send_message(message, "✅ Автоответ удален")
    else:
        await safe_send_message(message, "❌ Автоответ не установлен")

# Автоответ только в личных сообщениях
@router.message(F.text, ChatTypeFilter(chat_type="private"))
async def handle_private_messages(message: Message):
    if not message.text.startswith('.'):
        user_id = message.from_user.id
        if user_id in auto_responses:
            await safe_send_message(message, auto_responses[user_id])

# Игнорируем все сообщения из групп
@router.message(ChatTypeFilter(chat_type=["group", "supergroup"]))
async def ignore_groups(message: Message):
    pass

async def on_startup(bot: Bot) -> None:
    for attempt in range(5):
        try:
            await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")
            logging.info(f"Вебхук успешно установлен на адрес: {WEBHOOK_URL}{WEBHOOK_PATH}")
            break
        except TelegramNetworkError:
            if attempt == 4:
                logging.error("Не удалось установить вебхук после 5 попыток")
            else:
                await asyncio.sleep(2 * (attempt + 1))

async def on_shutdown(bot: Bot) -> None:
    try:
        await bot.delete_webhook()
    except:
        pass
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
