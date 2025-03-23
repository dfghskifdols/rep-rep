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

# Функция отправки сообщения "Доброе утро, мой господин!"
async def send_welcome_message():
    await bot.send_message(chat_id=USER_CHAT_ID, text="Доброе утро, мой господин!")

# Функция старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши /report в ответ на сообщение, чтобы отправить репорт.")

# Функция репорта
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Репорт можно отправить только ответом на сообщение!")
        return
    
    # Сохраняем ID оригинального сообщения и ID пользователя, который отправил репорт
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
    logger.info(f"Callback data: {data}")  # Логируем данные для отладки

    # Проверка на правильность формата данных
    if len(data) < 3:  # Если данных меньше, чем нужно
        await query.message.edit_text("❌ Ошибка: неправильный формат данных!")
        return

    action = data[0]
    try:
        user_id = int(data[1])  # Преобразуем второй элемент в int (user_id)
        message_id = int(data[2])  # Преобразуем третий элемент в int (message_id)
    except ValueError:
        logger.error(f"Ошибка преобразования данных: {data}")  # Логируем ошибку преобразования
        await query.message.edit_text("❌ Ошибка: неверные данные для обработки репорта!")
        return

    logger.info(f"action: {action}, user_id: {user_id}, message_id: {message_id}")

    # Проверка, что запрос пришел от пользователя, который отправил репорт
    if query.from_user.id != user_id:
        await query.message.edit_text("❌ Вы не можете подтвердить или отменить этот репорт!")
        return

    try:
        if action == "confirm":
            # Получаем сообщение с помощью bot.get_message
            original_message = await bot.get_message(chat_id=query.message.chat.id, message_id=message_id)
            reported_message = original_message.reply_to_message
            reported_user = reported_message.from_user

            # Формируем ссылку на сообщение (если возможно)
            if query.message.chat.username:
                message_link = f"https://t.me/{query.message.chat.username}/{reported_message.message_id}"
                link_text = f"<a href='{message_link}'>Перейти к сообщению</a>"
            else:
                link_text = "Сообщение отправлено в приватном чате, ссылка недоступна."

            # Цитируем текст сообщения
            message_text = reported_message.text if reported_message.text else "(медиа-файл)"
            reported_user_mention = f"<b>{reported_user.full_name}</b> (@{reported_user.username})"

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

            # Отправляем репорт
            await bot.send_message(
                ADMIN_CHAT_ID, report_text,
                parse_mode=ParseMode.HTML,
                protect_content=True,
                disable_web_page_preview=True
            )

            await query.message.edit_text("✅ Репорт успешно отправлен!")
        elif action == "cancel":
            await query.message.edit_text("❌ Репорт отменен.")
    except Exception as e:
        # Логирование ошибки
        logger.error(f"Ошибка при обработке репорта: {e}")
        await query.message.edit_text(f"❌ Ошибка при обработке репорта: {e}. Попробуйте позже.")

# Основная функция
async def main():
    # Отправка "Доброе утро" после запуска бота
    await send_welcome_message()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CallbackQueryHandler(handle_report, pattern="^(confirm|cancel)_\d+_\d+$"))

    print("Бот запущен!")
    await app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
