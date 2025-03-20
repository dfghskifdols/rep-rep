import time
import threading
import requests  # Нужно для отправки репортов
from flask import Flask, request

TOKEN = "7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU"
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации
app = Flask(__name__)

# Функция для поддержания активности процесса
def keep_alive():
    while True:
        time.sleep(600)  # Засыпаем на 10 минут

# Запускаем фоновый поток, чтобы бот не вырубался
thread = threading.Thread(target=keep_alive, daemon=True)
thread.start()

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.json

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text.startswith("/report"):
            reply = message.get("reply_to_message")
            report_text = text

            if reply:
                message_id = reply["message_id"]
                chat_username = message["chat"].get("username", "c")
                message_link = f"https://t.me/{chat_username}/{message_id}"
                report_text += f"\n\nСсылка на сообщение: {message_link}"

            # Отправляем сообщение админам
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
                "chat_id": ADMIN_CHAT_ID,
                "text": report_text,
                "parse_mode": "HTML"
            })

            # Подтверждение пользователю
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
                "chat_id": chat_id,
                "text": "Репорт успешно отправлен!"
            })

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

if __name__ == '__main__':
    set_webhook()  # Устанавливаем вебхук

    # Запуск Flask приложения
    run_simple('0.0.0.0', 3001, app)
