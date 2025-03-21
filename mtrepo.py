import asyncio
import nest_asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
from flask import Flask
from threading import Thread

# Применяем nest_asyncio для работы с асинхронными задачами
nest_asyncio.apply()

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен твоего бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации

# Настроим логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем экземпляры бота и приложения
bot = Bot(API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

# Flask-сервер для поддержки активности на Render
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
        # Получаем текст отчета
        report_text = update.message.text

        # Если сообщение является репортом на конкретное сообщение, добавляем ссылку на это сообщение
        if update.message.reply_to_message:
            reported_message = update.message.reply_to_message
            message_link = f"https://t.me/{update.message.chat.username}/{reported_message.message_id}"  # Формируем ссылку на сообщение
            report_text += f"\n\nСсылка на сообщение: <a href='{message_link}'>Перейти к сообщению</a>"

        # Отправляем репорт в группу администрации с использованием HTML-форматирования
        await bot.send_message(ADMIN_CHAT_ID, report_text, parse_mode='HTML')

        # Подтверждаем пользователю, что репорт отправлен
        await update.message.reply_text("Спасибо! Репорт успешно отправлен!")

    except Exception as e:
        # Логируем и информируем пользователя о возможной ошибке
        await update.message.reply_text(f"Произошла ошибка при отправке репорта: {e}. Попробуйте позже.")

# Основная функция для запуска
async def main():
    # Регистрация хэндлеров
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", handle_report))

    # Убедимся, что вебхуки отключены
    await bot.delete_webhook()

    # Запуск бота с использованием polling
    await app.run_polling()

# Запуск бота и Flask-сервера
if __name__ == '__main__':
    Thread(target=lambda: flask_app.run(host='0.0.0.0', port=8080, threaded=True)).start()
    asyncio.run(main())
