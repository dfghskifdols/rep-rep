import os
import requests
from flask import Flask, request
from werkzeug.serving import run_simple

# Конфигурация бота
API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен вашего бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации
WEBHOOK_HOST = 'https://rep-rep-1.onrender.com'  # Ваш публичный URL для вебхука
WEBHOOK_PATH = f'/{API_TOKEN}'  # Путь для вашего вебхука
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'  # Полный URL вебхука

# Инициализация Flask
app = Flask(__name__)

# Функция для отправки сообщений в Telegram
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    response = requests.post(url, data=payload)
    return response

# Хэндлер для команды /report
def handle_report(message):
    try:
        # Получаем текст отчета
        report_text = message.get('text', '')

        # Проверяем, является ли сообщение ответом на другое
        if 'reply_to_message' in message:
            reported_message = message['reply_to_message']
            chat_username = message['chat'].get('username', '')  # Получаем имя чата (если оно есть)
            if chat_username:
                # Формируем ссылку на сообщение
                message_link = f"https://t.me/{chat_username}/{reported_message['message_id']}"
                report_text += f"\n\nСсылка на сообщение: <a href='{message_link}'>Перейти к сообщению</a>"

        # Отправляем репорт в группу администрации с использованием HTML-форматирования
        send_message(ADMIN_CHAT_ID, report_text)

    except Exception as e:
        print(f"Произошла ошибка при отправке репорта: {e}")

# Обработка входящих запросов от Telegram
@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.json
        print(f"Received update: {data}")
        
        # Обрабатываем входящее сообщение
        if 'message' in data:
            message = data['message']
            if message.get('text') == '/report':
                handle_report(message)
        
        return 'OK'

# Устанавливаем вебхук с Telegram
def set_webhook():
    url = f"https://api.telegram.org/bot{API_TOKEN}/setWebhook"
    payload = {'url': WEBHOOK_URL}
    response = requests.post(url, data=payload)
    print(f"Webhook set: {response.text}")

# Запуск веб-сервера
if __name__ == '__main__':
    set_webhook()  # Устанавливаем вебхук

    # Запуск Flask приложения
    run_simple('0.0.0.0', 3001, app)
