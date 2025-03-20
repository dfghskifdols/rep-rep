import os
import logging
import requests
import threading
import time
from flask import Flask, request

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен твоего бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации
WEBHOOK_HOST = 'https://yourdomain.com'  # Замените на ваш домен с поддержкой HTTPS
WEBHOOK_PATH = '/webhook/'  # Путь для Webhook
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Функция для отправки сообщений через Telegram API
def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'
    params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    response = requests.get(url, params=params)
    return response

# Хэндлер для команд
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = request.get_json()

    if 'message' in update:
        message = update['message']
        if message.get('text') == '/report':
            send_message(ADMIN_CHAT_ID, "Поступил новый репорт от пользователя.")
            send_message(message['chat']['id'], "Репорт успешно отправлен!")
        else:
            send_message(message['chat']['id'], "Команда не распознана.")
    
    return 'OK'

# Функция для анти-сна
def keep_alive():
    while True:
        try:
            # Отправляем запрос к Telegram API (пинг) для поддержания активности
            url = f'https://api.telegram.org/bot{API_TOKEN}/getMe'
            response = requests.get(url)
            if response.status_code == 200:
                print("Bot is still alive!")
            else:
                print("Error: Unable to ping bot!")
        except Exception as e:
            print(f"Error during keep alive: {e}")
        time.sleep(60)  # Пауза 60 секунд (1 минута)

if __name__ == '__main__':
    # Устанавливаем Webhook
    url = f'https://api.telegram.org/bot{API_TOKEN}/setWebhook'
    params = {'url': WEBHOOK_URL}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        print("Webhook установлен!")
    else:
        print("Ошибка установки Webhook:", response.text)

    # Запуск фоновой задачи анти-сна
    threading.Thread(target=keep_alive, daemon=True).start()

    # Запуск Flask-сервера
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
