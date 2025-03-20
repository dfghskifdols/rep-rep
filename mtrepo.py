import threading
import time
import requests
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен твоего бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации

bot = Bot(token=API_TOKEN)

def keep_alive():
    while True:
        try:
            requests.get('https://api.telegram.org')  # Пинг сервера Telegram
        except Exception as e:
            print(f"Ошибка в keep_alive: {e}")
        time.sleep(300)  # Повторяем каждые 5 минут

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Привет! Отправьте /report в ответ на сообщение, чтобы отправить жалобу.')

def report(update: Update, context: CallbackContext):
    message = update.message
    if message.reply_to_message:
        reported_message = message.reply_to_message
        report_text = f"Поступил репорт от @{message.from_user.username} на сообщение: \n"
        report_text += f"{reported_message.text}"
        bot.send_message(ADMIN_CHAT_ID, report_text, parse_mode='HTML')
        message.reply_text("Репорт отправлен!")
    else:
        message.reply_text("Вы должны ответить на сообщение, чтобы отправить репорт.")

def main():
    updater = Updater(API_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("report", report))
    
    # Запускаем поток для keep_alive
    threading.Thread(target=keep_alive, daemon=True).start()
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
