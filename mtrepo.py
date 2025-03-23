import asyncio
import nest_asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging
import random

nest_asyncio.apply()

API_TOKEN = '7705193251:AAEuxkW63TtCcXwizvAYUuoI7jH1570NgNU'  # Токен бота
ADMIN_CHAT_ID = -1002651165474  # ID группы с администраторами, из которой будет выбран случайный админ
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
        logger.info("Попытка взаимодействия с чужим репортом!")
        # Отправляем всплывающее сообщение и НЕ изменяем оригинальное сообщение
        await query.answer(text="❌ Нельзя жмякать чужие репорты!", show_alert=True)
        return

    try:
        if action == "confirm":
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
            message_text = reported_message.text if reported_message.text else "(медиа-файл)"
            reported_user_mention = f"<b>{reported_user.full_name}</b> (@{reported_user.username})"

            # Текст репорта
            report_text = (
                f"⚠️ <b>Новый репорт!</b>\n\n"
                f"👤 Пользователь: {reported_user_mention}\n"
                f"💬 Сообщение:\n<blockquote>{message_text}</blockquote>\n"
                f"{link_text}"
            )

            # Получаем список администраторов из другого чата
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

# Функция для обработки текстовых сообщений
async def handle_message(update: Update, context):
    message = update.message.text
    if "Пинг" in message:
        await update.message.reply_text("А нахуя он тебе")

    if "Неко" in message:
        # Получаем администраторов из другого чата
        admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
        
        # Проверяем, что администраторы существуют
        if admins:
            # Выбираем случайного администратора
            random_admin = random.choice(admins)
            random_username = random_admin.user.username if random_admin.user.username else "unknown_user"
            
            # Отправляем первое сообщение
            sent_message = await update.message.reply_text("вычисления кошко-девочки по айпи💻")
            
            # Задержка 5 секунд, чтобы изменить сообщение
            await asyncio.sleep(5)
            
            # Обновляем сообщение с использованием случайного администратора
            await sent_message.edit_text(f"Кошко-девочка вычислена! Она находится у @{random_username}")
        else:
            await update.message.reply_text("❌ Не удалось получить администраторов для вычислений!")

# Основная функция
async def main():
    # Отправка "Доброе утро" после запуска бота
    await send_welcome_message()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CallbackQueryHandler(handle_report, pattern="^(confirm|cancel)_\d+_\d+$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    await app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
