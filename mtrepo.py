import os
from flask import Flask, request
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
import logging

# Логирование
logging.basicConfig(level=logging.INFO)

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации
WEBHOOK_URL = 'https://yourdomain.com/{}/'.format(API_TOKEN)  # URL для Webhook (замените на ваш)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Flask приложение
app = Flask(__name__)

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


# Асинхронная функция для обработки Webhook
@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get('message'):
        chat_id = data['message']['chat']['id']
        text = data['message']['text']

        # Простой ответ на команду "hello"
        if text.lower() == "hello":
            send_message(chat_id, "Hello!")
    return '', 200


# Функция отправки сообщений через Telegram API
def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'
    data = {
        'chat_id': chat_id,
        'text': text
    }
    requests.post(url, data=data)


# Устанавливаем Webhook для бота
def set_webhook():
    url = f'https://api.telegram.org/bot{API_TOKEN}/setWebhook?url={WEBHOOK_URL}'
    requests.get(url)


# Запуск Flask сервера и Webhook
if __name__ == '__main__':
    set_webhook()  # Устанавливаем Webhook при старте сервера
    app.run(host='0.0.0.0', port=5000)  # Запускаем сервер Flask
