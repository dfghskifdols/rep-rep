import os
from flask import Flask, request
import requests

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации
WEBHOOK_URL = 'https://yourdomain.com/{}/'.format(API_TOKEN)  # URL для Webhook (замените на ваш)

# Flask приложение
app = Flask(__name__)

# Функция отправки сообщений через Telegram API
def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'
    data = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, data=data)
    return response


# Хэндлер для команды /report
@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()

    if data.get('message'):
        chat_id = data['message']['chat']['id']
        text = data['message']['text']

        # Проверка команды /report
        if text.lower().startswith('/report'):
            report_text = text[len('/report '):]  # Извлекаем текст репорта
            send_message(ADMIN_CHAT_ID, report_text)  # Отправляем репорт в группу
            send_message(chat_id, "Репорт успешно отправлен!")  # Подтверждаем отправку репорта

        # Если это просто сообщение, отвечаем на него
        elif text.lower() == "hello":
            send_message(chat_id, "Hello!")

    return '', 200


# Устанавливаем Webhook для бота
def set_webhook():
    url = f'https://api.telegram.org/bot{API_TOKEN}/setWebhook?url={WEBHOOK_URL}'
    response = requests.get(url)
    return response


# Запуск Flask сервера и Webhook
if __name__ == '__main__':
    set_webhook()  # Устанавливаем Webhook при старте сервера
    app.run(host='0.0.0.0', port=5000)  # Запускаем сервер Flask
