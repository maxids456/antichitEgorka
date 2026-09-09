import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
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

@router.message(CommandStart())
async def cmd_start(message: Message):
    try:
        await message.answer("Пахан Ткачонко жирный индус")
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")

@router.message(F.text.startswith('.spam'))
async def spam_handler(message: Message):
    if message.chat.type != "private":
        return
    
    parts = message.text.split(maxsplit=2)
    
    if len(parts) < 3:
        await message.answer("Использование: .spam (количество) (текст)")
        return
    
    try:
        count = int(parts[1])
    except ValueError:
        await message.answer("Количество должно быть числом")
        return
    
    spam_text = parts[2]
    
    if count > 20:
        await message.answer("Максимум 20 сообщений за раз")
        return
    
    if count < 1:
        await message.answer("Количество должно быть больше 0")
        return
    
    await message.answer(f"Начинаю спам: {count} сообщений")
    
    for i in range(count):
        try:
            await message.answer(spam_text)
            await asyncio.sleep(0.1)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except Exception as e:
            logging.error(f"Ошибка отправки спама: {e}")
            break

async def set_webhook_with_retry(bot: Bot, url: str, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            await bot.set_webhook(url)
            logging.info(f"Вебхук установлен: {url}")
            return True
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except TelegramNetworkError as e:
            logging.warning(f"Попытка {attempt + 1} не удалась: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logging.error(f"Неожиданная ошибка: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    return False

async def on_startup(bot: Bot) -> None:
    webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    success = await set_webhook_with_retry(bot, webhook_url)
    if not success:
        logging.error("Не удалось установить вебхук после всех попыток")

async def on_shutdown(bot: Bot) -> None:
    try:
        await bot.delete_webhook()
    except Exception as e:
        logging.error(f"Ошибка при удалении вебхука: {e}")
    finally:
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
