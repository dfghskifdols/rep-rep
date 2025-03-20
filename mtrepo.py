import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from flask import Flask
from threading import Thread

# Токен бота и ID чата для репортов
API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен твоего бота
ADMIN_CHAT_ID = '-1002651165474'  # ID группы администрации

# Настройка бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Создаем приложение Flask
app = Flask(__name__)

# Основная страница для Flask, чтобы приложение не засыпало
@app.route('/')
def index():
    return "Bot is running!"

# Хэндлер для команды /report
@dp.message_handler(commands=['report'])
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

# Запуск aiogram в отдельном потоке
def start_polling():
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)

# Запуск Flask-сервера
def start_flask():
    app.run(host='0.0.0.0', port=5000)

# Запуск приложения
if __name__ == "__main__":
    # Запуск aiogram в фоне (в отдельном потоке)
    thread = Thread(target=start_polling)
    thread.start()
    
    # Запуск Flask-сервера
    start_flask()

