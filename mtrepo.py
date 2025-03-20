import logging
import requests
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import asyncio

TOKEN = "7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU"
ADMIN_CHAT_ID = -1002651165474
bot = Bot(token=TOKEN)

logging.basicConfig(level=logging.INFO)

async def report(update: Update, context: CallbackContext):
    message = update.message
    report_text = message.text
    
    if message.reply_to_message:
        reported_message = message.reply_to_message
        chat = message.chat
        message_link = f"https://t.me/{chat.username}/{reported_message.message_id}"
        report_text += f"\n\nСсылка на сообщение: [Перейти к сообщению]({message_link})"

    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=report_text, parse_mode="Markdown")
    await message.reply_text("Репорт успешно отправлен!")

async def keep_alive():
    while True:
        try:
            requests.get("https://rep-rep-1.onrender.com")
        except Exception as e:
            logging.error(f"Ошибка keep_alive: {e}")
        await asyncio.sleep(300)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("report", report))
    
    loop = asyncio.get_event_loop()
    loop.create_task(keep_alive())
    
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
