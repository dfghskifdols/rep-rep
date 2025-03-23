import asyncio
import nest_asyncio
import html
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
from flask import Flask
from threading import Thread

nest_asyncio.apply()

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации
USER_CHAT_ID = 5283100992  # Ваш ID для отправки сообщений в ЛС

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши /report в ответ на сообщение, чтобы отправить репорт.")

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Репорт можно отправить только ответом на сообщение!")
        return
    
    # Сохраняем ID оригинального сообщения и ID пользователя, который отправил репорт
    message_id = update.message.message_id
    user_id = update.message.from_user.id

    # Сохраняем информацию о репорте в контексте (будет доступна при обработке callback)
    context.user_data['report_user_id'] = user_id
    context.user_data['report_message_id'] = message_id

    keyboard = [[
        InlineKeyboardButton("✅ Да", callback_data=f"confirm_report_{user_id}_{message_id}"),
        InlineKeyboardButton("❌ Нет", callback_data=f"cancel_report_{user_id}_{message_id}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Вы уверены, что хотите отправить репорт?", reply_markup=reply_markup)

async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    logger.info(f"Callback data: {query.data}")

    # Проверка, что данные имеют формат "action_user_id_message_id"
    try:
        data = query.data.split('_')
        action = data[0]
        user_id = int(data[1])
        message_id = int(data[2])

        # Логируем полученные данные
        logger.info(f"Parsed data - Action: {action}, User ID: {user_id}, Message ID: {message_id}")

        # Проверяем, что это тот же человек, кто отправил репорт
        if query.from_user.id != user_id:
            await query.message.edit_text("❌ Вы не можете подтвердить или отменить этот репорт!")
            return

        if action == "confirm_report":
            await confirm_report(update, context, user_id, message_id)
        elif action == "cancel_report":
            await cancel_report(update, context, user_id, message_id)
    except Exception as e:
        logger.error(f"Ошибка при обработке callback данных: {e}")
        await query.message.edit_text("❌ Ошибка при обработке вашего запроса. Попробуйте позже.")

async def confirm_report(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, message_id: int):
    query = update.callback_query
    await query.answer()

    try:
        original_message = await query.message.chat.get_message(message_id)
        reported_message = original_message.reply_to_message
        reported_user = reported_message.from_user

        # Формируем ссылку на сообщение (если возможно)
        chat = query.message.chat
        if chat.username:
            message_link = f"https://t.me/{chat.username}/{reported_message.message_id}"
            link_text = f"<a href='{message_link}'>Перейти к сообщению</a>"
        else:
            link_text = "Сообщение отправлено в приватном чате, ссылка недоступна."

        # Цитируем текст сообщения
        message_text = html.escape(reported_message.text) if reported_message.text else "(медиа-файл)"
        reported_user_mention = f"<b>{html.escape(reported_user.full_name)}</b> (@{reported_user.username})"

        # Текст репорта
        report_text = (
            f"⚠️ <b>Новый репорт!</b>\n\n"
            f"👤 Пользователь: {reported_user_mention}\n"
            f"💬 Сообщение:\n<blockquote>{message_text}</blockquote>\n"
            f"{link_text}"
        )

        # Получаем список администраторов
        admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
        admin_mentions = [f"@{admin.user.username}" for admin in admins if admin.user.username]

        # Разделяем список админов на две части
        mid = len(admin_mentions) // 2
        first_half = admin_mentions[:mid]
        second_half = admin_mentions[mid:]

        # Отправляем репорт
        await bot.send_message(
            ADMIN_CHAT_ID, report_text,
            parse_mode=ParseMode.HTML,
            protect_content=True,
            disable_web_page_preview=True
        )

        # Пингуем первую половину админов
        if first_half:
            await bot.send_message(
                ADMIN_CHAT_ID, f"👥 Пинг админов (1-я часть): {' '.join(first_half)}",
                parse_mode=ParseMode.HTML,
                protect_content=True,
                disable_web_page_preview=True
            )

        # Пингуем вторую половину админов
        if second_half:
            await bot.send_message(
                ADMIN_CHAT_ID, f"👥 Пинг админов (2-я часть): {' '.join(second_half)}",
                parse_mode=ParseMode.HTML,
                protect_content=True,
                disable_web_page_preview=True
            )

        await query.message.edit_text("✅ Репорт успешно отправлен!")
    except Exception as e:
        await query.message.edit_text(f"❌ Ошибка при отправке репорта: {e}. Попробуйте позже.")

async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, message_id: int):
    query = update.callback_query
    await query.answer()

    # Проверяем, что это тот же человек, кто отправил репорт
    if query.from_user.id != user_id:
        await query.message.edit_text("❌ Вы не можете отменить этот репорт!")
        return
    
    await query.message.edit_text("❌ Репорт отменен.")

async def notify_user_on_shutdown():
    try:
        await bot.send_message(USER_CHAT_ID, "👋 Мой господин... прощайте")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение пользователю при выключении: {e}")

async def notify_user_on_start():
    try:
        await bot.send_message(USER_CHAT_ID, "Доброе утро, мой господин!")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение пользователю при запуске: {e}")

async def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CallbackQueryHandler(handle_report))

    print("Бот запущен!")
    await notify_user_on_start()  # Отправляем сообщение при запуске
    await app.run_polling()

    await notify_user_on_shutdown()  # Отправляем сообщение перед остановкой

if __name__ == '__main__':
    Thread(target=lambda: flask_app.run(host='0.0.0.0', port=8080)).start()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
