import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.filters import Command
from aiogram import F
import aiohttp

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен твоего бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Хэндлер для команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот!")

# Хэндлер для команды /report
@dp.message(Command("report"))
async def handle_report(message: types.Message):
    try:
        # Получаем текст отчета
        report_text = message.text

        # Если сообщение является репортом на конкретное сообщение, добавляем ссылку на это сообщение
        if message.reply_to_message:
            reported_message = message.reply_to_message
            message_link = f"https://t.me/{message.chat.username}/{reported_message.message_id}"  # Формируем ссылку на сообщение
            report_text += f"\n\nСсылка на сообщение: <a href='{message_link}'>Перейти к сообщению</a>"

        # Отправляем репорт в группу администрации с использованием HTML-форматирования
        await bot.send_message(ADMIN_CHAT_ID, report_text, parse_mode=ParseMode.HTML)

        # Подтверждаем пользователю, что репорт отправлен
        await message.reply("Репорт успешно отправлен!")

    except Exception as e:
        # Логируем и информируем пользователя о возможной ошибке
        await message.reply(f"Произошла ошибка при отправке репорта: {e}. Попробуйте позже.")

# Асинхронная функция для поддержания активности бота
async def keep_alive():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://www.google.com/') as resp:
                    if resp.status == 200:
                        print("Bot is still alive!")
        except Exception as e:
            print(f"Error keeping bot alive: {e}")
        await asyncio.sleep(300)  # Пауза между запросами в 5 минут (300 секунд)

if __name__ == '__main__':
    # Запуск бота в отдельном потоке
    loop = asyncio.get_event_loop()
    loop.create_task(keep_alive())  # Запускаем задачу keep_alive
    dp.run_polling(bot)
    
