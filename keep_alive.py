import threading
from flask import Flask
from my_telegram_bot import start_bot  # припустимо, твоя функція запуску бота

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

threading.Thread(target=start_bot).start()

app.run(host="0.0.0.0", port=3000)
