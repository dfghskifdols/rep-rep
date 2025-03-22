import asyncio
import nest_asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
from flask import Flask

# Применяем nest_asyncio для работы с асинхронными задачами
nest_asyncio.apply()

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации

# Настроим логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём экземпляры бота и приложения
bot = Bot(API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

# Flask-сервер для поддержки активности
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running"

# Хэндлер для команды /start
async def start(update: Update, context):
    await update.message.reply_text("Привет! Напиши /report чтобы отправить репорт.")

# Хэндлер для команды /report
async def handle_report(update: Update, context):
    try:
        report_text = update.message.text

        # Если сообщение является репортом на конкретное сообщение, добавляем ссылку
        if update.message.reply_to_message:
            reported_message = update.message.reply_to_message
            chat = update.message.chat
            message_link = f"https://t.me/{chat.username}/{reported_message.message_id}"  
            report_text += f"\n\nСсылка на сообщение: <a href='{message_link}'>Перейти к сообщению</a>"

        # Отправляем репорт в группу администрации
        await bot.send_message(ADMIN_CHAT_ID, report_text, parse_mode='HTML')

        # Подтверждаем пользователю отправку репорта
        await update.message.reply_text("Спасибо! Репорт успешно отправлен!")

    except Exception as e:
        await update.message.reply_text(f"Ошибка при отправке репорта: {e}. Попробуйте позже.")

# Основная функция
async def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", handle_report))

    # Удаляем вебхук перед запуском polling
    await bot.delete_webhook(drop_pending_updates=True)

    print("Бот запущен!")
    await app.run_polling()

if __name__ == '__main__':
    from threading import Thread
    Thread(target=lambda: flask_app.run(host='0.0.0.0', port=8080)).start()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
