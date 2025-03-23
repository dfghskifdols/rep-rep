import asyncio
import nest_asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging

nest_asyncio.apply()

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации
USER_CHAT_ID = 5283100992  # Ваш ID для отправки сообщений в ЛС

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

async def send_welcome_message():
    await bot.send_message(chat_id=USER_CHAT_ID, text="Доброе утро, мой господин!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши /report в ответ на сообщение, чтобы отправить репорт.")

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Репорт можно отправить только ответом на сообщение!")
        return
    
    message_id = update.message.reply_to_message.message_id
    user_id = update.message.from_user.id

    keyboard = [[
        InlineKeyboardButton("✅ Да", callback_data=f"confirm_report_{user_id}_{message_id}"),
        InlineKeyboardButton("❌ Нет", callback_data=f"cancel_report_{user_id}_{message_id}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Вы уверены, что хотите отправить репорт?", reply_markup=reply_markup)

async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    logger.info(f"Callback data: {data}")

    if len(data) != 4 or data[0] not in ["confirm", "cancel"]:
        logger.error(f"Ошибка: неверный формат callback-данных: {data}")
        await query.message.edit_text("❌ Ошибка: неверные данные для обработки репорта!")
        return
    
    action, _, user_id_str, message_id_str = data

    try:
        user_id = int(user_id_str)
        message_id = int(message_id_str)
    except ValueError:
        logger.error(f"Ошибка преобразования данных: {data}")  
        await query.message.edit_text("❌ Ошибка: неверные данные для обработки репорта!")
        return

    if query.from_user.id != user_id:
        await query.message.edit_text("❌ Вы не можете подтвердить или отменить этот репорт!")
        return

    try:
        if action == "confirm_report":
            chat = query.message.chat
            reported_message = await bot.forward_message(ADMIN_CHAT_ID, chat.id, message_id)
            
            report_text = (
                f"⚠️ <b>Новый репорт!</b>\n\n"
                f"🔗 <a href='https://t.me/c/{abs(chat.id)}/{reported_message.message_id}'>Перейти к сообщению</a>"
            )

            await bot.send_message(
                ADMIN_CHAT_ID, report_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

            await query.message.edit_text("✅ Репорт успешно отправлен!")
        elif action == "cancel_report":
            await query.message.edit_text("❌ Репорт отменен.")
    except Exception as e:
        logger.error(f"Ошибка при обработке репорта: {e}")
        await query.message.edit_text(f"❌ Ошибка при обработке репорта: {e}. Попробуйте позже.")

async def main():
    await send_welcome_message()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CallbackQueryHandler(handle_report, pattern="^(confirm_report|cancel_report)_\d+_\d+$"))

    print("Бот запущен!")
    await app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
