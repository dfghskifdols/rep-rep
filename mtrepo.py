import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import aiohttp

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен твоего бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации

# Устанавливаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Обработчик команды /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply("Привет! Я готов принимать репорты.")

# Обработчик для команды /report
async def report(update: Update, context: CallbackContext):
    try:
        # Получаем текст отчета
        report_text = update.message.text

        # Если сообщение является репортом на конкретное сообщение, добавляем ссылку на это сообщение
        if update.message.reply_to_message:
            reported_message = update.message.reply_to_message
            message_link = f"https://t.me/{update.message.chat.username}/{reported_message.message_id}"  # Формируем ссылку на сообщение
            report_text += f"\n\nСсылка на сообщение: <a href='{message_link}'>Перейти к сообщению</a>"

        # Отправляем репорт в группу администрации с использованием HTML-форматирования
        await context.bot.send_message(ADMIN_CHAT_ID, report_text, parse_mode="HTML")

        # Подтверждаем пользователю, что репорт отправлен
        await update.message.reply("Спасибо! Репорт успешно отправлен!")

    except Exception as e:
        # Логируем и информируем пользователя о возможной ошибке
        await update.message.reply(f"Произошла ошибка при отправке репорта: {e}. Попробуйте позже.")

async def main():
    # Создаем приложение и передаем токен бота
    app = Application.builder().token(API_TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, report))  # Обрабатываем все текстовые сообщения, не являющиеся командами

    # Запуск бота
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
