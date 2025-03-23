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

# Создаем приложение бота
app = Application.builder().token(API_TOKEN).build()

# Функция отправки сообщения "Доброе утро, мой господин!"
async def send_welcome_message():
    await app.bot.send_message(chat_id=USER_CHAT_ID, text="Доброе утро, мой господин!")

# Функция старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши /report в ответ на сообщение, чтобы отправить репорт.")

# Функция репорта
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Репорт можно отправить только ответом на сообщение!")
        return

    message_id = update.message.message_id
    user_id = update.message.from_user.id

    keyboard = [[
        InlineKeyboardButton("✅ Да", callback_data=f"confirm_{user_id}_{message_id}"),
        InlineKeyboardButton("❌ Нет", callback_data=f"cancel_{user_id}_{message_id}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Вы уверены, что хотите отправить репорт?", reply_markup=reply_markup)

# Функция обработки репорта
async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    logger.info(f"Callback data: {data}")

    if len(data) < 3:
        await query.message.edit_text("❌ Ошибка: неправильный формат данных!")
        return

    action = data[0]
    try:
        user_id = int(data[1])
        message_id = int(data[2])
    except ValueError:
        logger.error(f"Ошибка преобразования данных: {data}")
        await query.message.edit_text("❌ Ошибка: неверные данные для обработки репорта!")
        return

    logger.info(f"action: {action}, user_id: {user_id}, message_id: {message_id}")

    if query.from_user.id != user_id:
        await query.message.edit_text("❌ Вы не можете подтвердить или отменить этот репорт!")
        return

    try:
        if action == "confirm":
            chat = query.message.chat
            reported_message = await context.bot.forward_message(
                chat_id=USER_CHAT_ID, from_chat_id=chat.id, message_id=message_id
            )
            reported_user = reported_message.from_user

            message_text = reported_message.text if reported_message.text else "(медиа-файл)"
            reported_user_mention = f"<b>{reported_user.full_name}</b> (@{reported_user.username})"

            report_text = (
                f"⚠️ <b>Новый репорт!</b>\n\n"
                f"👤 Пользователь: {reported_user_mention}\n"
                f"💬 Сообщение:\n<blockquote>{message_text}</blockquote>\n"
            )

            await context.bot.send_message(
                ADMIN_CHAT_ID, report_text,
                parse_mode=ParseMode.HTML,
                protect_content=True,
                disable_web_page_preview=True
            )

            await query.message.edit_text("✅ Репорт успешно отправлен!")
        elif action == "cancel":
            await query.message.edit_text("❌ Репорт отменен.")
    except Exception as e:
        logger.error(f"Ошибка при обработке репорта: {e}")
        await query.message.edit_text(f"❌ Ошибка при обработке репорта: {e}. Попробуйте позже.")

# Основная функция
async def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CallbackQueryHandler(handle_report, pattern="^(confirm|cancel)_\d+_\d+$"))

    await send_welcome_message()
    logger.info("Бот запущен!")
    await app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
