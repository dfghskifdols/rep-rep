import asyncio
import nest_asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging
import random

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
    
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    report_key = f"report_{user_id}_{message_id}"

    # Проверяем, не отправлен ли уже репорт
    if context.bot_data.get(report_key, False):
        await update.message.reply_text("⚠️ Вы уже отправили репорт на это сообщение!")
        return

    # Сохраняем, что репорт еще не был подтвержден
    context.bot_data[report_key] = False

    keyboard = [[
        InlineKeyboardButton("✅ Да", callback_data=f"confirm_{user_id}_{message_id}"),
        InlineKeyboardButton("❌ Нет", callback_data=f"cancel_{user_id}_{message_id}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Вы уверены, что хотите отправить репорт?", reply_markup=reply_markup)

async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    if len(data) < 3:
        await query.message.edit_text("❌ Ошибка: неправильный формат данных!")
        return

    action, user_id, message_id = data[0], int(data[1]), int(data[2])
    report_key = f"report_{user_id}_{message_id}"

    # Проверяем, не отправлен ли уже репорт
    if context.bot_data.get(report_key, False):
        await query.answer(text="❌ Репорт уже отправлен!", show_alert=True)
        return

    # Если репорт еще не подтвержден, помечаем его в процессе обработки
    context.bot_data[report_key] = True

    # Блокируем повторные нажатия, изменяя текст кнопок
    keyboard_disabled = [[InlineKeyboardButton("⏳ Обработка...", callback_data="ignore")]]
    await query.message.edit_text("⏳ Обработка репорта...", reply_markup=InlineKeyboardMarkup(keyboard_disabled))

    if query.from_user.id != user_id:
        await query.answer(text="❌ Нельзя жмякать чужие репорты!", show_alert=True)
        return

    try:
        if action == "confirm":
            reported_message = query.message.reply_to_message
            reported_user = reported_message.from_user

            if query.message.chat.username:
                message_link = f"https://t.me/{query.message.chat.username}/{reported_message.message_id}"
                link_text = f"<a href='{message_link}'>Перейти к сообщению</a>"
            else:
                link_text = "Сообщение в приватном чате, ссылка недоступна."

            message_text = reported_message.text if reported_message.text else "(медиа-файл)"
            reported_user_mention = f"<b>{reported_user.full_name}</b> (@{reported_user.username})"

            report_text = (
                f"⚠️ <b>Новый репорт!</b>\n\n"
                f"👤 Пользователь: {reported_user_mention}\n"
                f"💬 Сообщение:\n<blockquote>{message_text}</blockquote>\n"
                f"{link_text}"
            )

            admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
            admin_mentions = [f"@{admin.user.username}" for admin in admins if admin.user.username]

            await bot.send_message(
                ADMIN_CHAT_ID, report_text,
                parse_mode=ParseMode.HTML,
                protect_content=True,
                disable_web_page_preview=True
            )

            if admin_mentions:
                half = len(admin_mentions) // 2
                await asyncio.sleep(5)
                await bot.send_message(ADMIN_CHAT_ID, "Первая часть админов: " + " ".join(admin_mentions[:half]))
                await asyncio.sleep(5)
                await bot.send_message(ADMIN_CHAT_ID, "Вторая часть админов: " + " ".join(admin_mentions[half:]))

            await query.message.edit_text("✅ Репорт успешно отправлен!", reply_markup=None)

        elif action == "cancel":
            await query.message.edit_text("❌ Репорт отменен.", reply_markup=None)

    except Exception as e:
        logger.error(f"Ошибка при обработке репорта: {e}")
        await query.message.edit_text(f"❌ Ошибка: {e}. Попробуйте позже.")

async def handle_message(update: Update, context):
    message = update.message.text
    if "Неко" in message:
        admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
        if admins:
            random_admin = random.choice(admins)
            random_username = random_admin.user.username if random_admin.user.username else "unknown_user"
            sent_message = await update.message.reply_text("вычисления кошко-девочки по айпи💻")
            await asyncio.sleep(5)
            await sent_message.edit_text(f"Кошко-девочка вычислена! Она находится у @{random_username}")
        else:
            await update.message.reply_text("❌ Не удалось получить администраторов для вычислений!")
    elif "Пинг" in message:
        await update.message.reply_text("А нахуя он тебе?")

async def main():
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
