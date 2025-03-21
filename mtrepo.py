import asyncio
import nest_asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler
import logging
from flask import Flask
from threading import Thread

# Применяем nest_asyncio
nest_asyncio.apply()

API_TOKEN = 'ТВОЙ_ТОКЕН'
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем бота и приложение
bot = Bot(API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

# Flask для поддержания активности на Render
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running"

# Команда /start
async def start(update: Update, context):
    await update.message.reply_text("Привет! Напиши /report чтобы отправить репорт.")

# Команда /report
async def handle_report(update: Update, context):
    try:
        report_text = update.message.text
        if update.message.reply_to_message:
            reported_message = update.message.reply_to_message
            message_link = f"https://t.me/{update.message.chat.username}/{reported_message.message_id}"
            report_text += f"\n\nСсылка на сообщение: <a href='{message_link}'>Перейти к сообщению</a>"
        
        await bot.send_message(ADMIN_CHAT_ID, report_text, parse_mode='HTML')
        await update.message.reply_text("Спасибо! Репорт успешно отправлен!")

    except Exception as e:
        await update.message.reply_text(f"Ошибка при отправке репорта: {e}")

# Основная функция
async def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", handle_report))

    # Убедимся, что старый polling отключен перед запуском нового
    await bot.delete_webhook(drop_pending_updates=True)

    await app.run_polling()

# Запуск Flask и бота
if __name__ == '__main__':
    Thread(target=lambda: flask_app.run(host='0.0.0.0', port=8080, threaded=True)).start()
    asyncio.run(main())
