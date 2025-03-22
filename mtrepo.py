import asyncio
import nest_asyncio
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler
import logging
from flask import Flask
from threading import Thread
import urllib.parse

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
            # Экранируем ссылку и добавляем ее в текст отчета
            message_link_escaped = urllib.parse.quote(message_link)
            report_text += f"\n\nСсылка на сообщение: <a href='{message_link_escaped}'>Перейти к сообщению</a>"

        # Получаем всех администраторов группы
        admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)

        # Добавляем администраторов в список для пинга
        mention_users = []
        for admin in admins:
            if admin.user.username:
                mention_users.append(f"@{admin.user.username}")  # Пингуем только тех, у кого есть username

        # Разделяем администраторов на две части
        mid = len(mention_users) // 2
        first_half = mention_users[:mid]
        second_half = mention_users[mid:]

        # Отправляем сообщение с репортом в HTML-формате
        message = f"Внимание! Новый репорт: \n\n{report_text}"
        await bot.send_message(ADMIN_CHAT_ID, message, parse_mode=ParseMode.HTML)

        # Отправляем пинг первой половины администраторов
        if first_half:
            message_ping_first_half = f"Пинг первой половины администраторов: \n\n{' '.join(first_half)}"
            await bot.send_message(ADMIN_CHAT_ID, message_ping_first_half, parse_mode=ParseMode.MARKDOWN)
        elif not first_half:  # Если первой половины нет, отправим второй пинг
            logger.info("Первая половина администраторов пуста.")

        # Отправляем пинг второй половины администраторов
        if second_half:
            message_ping_second_half = f"Пинг второй половины администраторов: \n\n{' '.join(second_half)}"
            await bot.send_message(ADMIN_CHAT_ID, message_ping_second_half, parse_mode=ParseMode.MARKDOWN)
        elif not second_half:  # Если второй половины нет, выводим информацию в лог
            logger.info("Вторая половина администраторов пуста.")

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
    # Запуск Flask-сервера в отдельном потоке
    Thread(target=lambda: flask_app.run(host='0.0.0.0', port=8080)).start()

    # Запуск основного цикла бота
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
