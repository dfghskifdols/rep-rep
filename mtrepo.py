import asyncio
import nest_asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging
import random

nest_asyncio.apply()

API_TOKEN = 'YOUR_BOT_TOKEN'  # Токен бота
ADMIN_CHAT_ID = -1002651165474  # ID группы администрации
USER_CHAT_ID = 5283100992  # Ваш ID для отправки сообщений в ЛС

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

# Храним уже подтверждённые репорты
confirmed_reports = set()

# Возможные ответы на "РаФа"
rafa_responses = [
    "Hymanoid ненавидит меня, за то что я его не всегда пингую", "Blue_Nexus иногда стает ебланом", "Кирич невнимательный", 
    "IDC... я не придумал что он делает", "РаФа - сокращенно Рандом Факт", "Freeze похуист по жизни", "Humanoid постоянно ноет что у него нету твинка",
    "Blue_Nexus держат в рабсте", "Кирич любит аниме-тянок... но в жизни девушек он не любит", "еще жду",
    "Freeze - успех успешный", "Humanoid фанат пнг блю лок ждет 3 сезон сделанный в Microsoft Excel", "Blue_Nexus абажает чат гпт",
    "Изначально Кирич создавал канал про свою жизнь", "еще жду", "Freeze - антипацифист☮️"
]

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
    
    message_id = update.message.reply_to_message.message_id
    user_id = update.message.from_user.id
    report_key = f"{user_id}_{message_id}"

    if report_key in confirmed_reports:
        await update.message.reply_text("⚠️ Этот репорт уже был подтверждён!")
        return

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
    if len(data) < 3:
        await query.message.edit_text("❌ Ошибка: неправильный формат данных!")
        return

    action = data[0]
    try:
        user_id = int(data[1])
        message_id = int(data[2])
    except ValueError:
        await query.message.edit_text("❌ Ошибка: неверные данные для обработки репорта!")
        return

    if query.from_user.id != user_id:
        await query.answer(text="❌ Нельзя жмякать чужие репорты!", show_alert=True)
        return

    report_key = f"{user_id}_{message_id}"
    if report_key in confirmed_reports:
        await query.answer(text="⚠️ Этот репорт уже был обработан!", show_alert=True)
        return

    if action == "confirm":
        reported_message = query.message.reply_to_message
        reported_user = reported_message.from_user

        if query.message.chat.username:
            message_link = f"https://t.me/{query.message.chat.username}/{reported_message.message_id}"
            link_text = f"<a href='{message_link}'>Перейти к сообщению</a>"
        else:
            link_text = "Сообщение отправлено в приватном чате, ссылка недоступна."

        message_text = reported_message.text if reported_message.text else "(медиа-файл)"
        reported_user_mention = f"<b>{reported_user.full_name}</b> (@{reported_user.username})"

        report_text = (
            f"⚠️ <b>Новый репорт!</b>\n\n"
            f"👤 Пользователь: {reported_user_mention}\n"
            f"💬 Сообщение:\n<blockquote>{message_text}</blockquote>\n"
            f"{link_text}"
        )

        await query.message.edit_text("⏳Отправка...")

        # Получаем администраторов
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
            await asyncio.sleep(4)
            await bot.send_message(ADMIN_CHAT_ID, "Первая часть админов: " + " ".join(admin_mentions[:half]))
            await asyncio.sleep(4)
            await bot.send_message(ADMIN_CHAT_ID, "Вторая часть админов: " + " ".join(admin_mentions[half:]))

        # Задаем вопрос о пинге
        keyboard = [
            [InlineKeyboardButton("✅ Да", callback_data=f"ping_{user_id}_{message_id}_yes")],
            [InlineKeyboardButton("❌ Нет", callback_data=f"ping_{user_id}_{message_id}_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text("Пинговать администраторов?", reply_markup=reply_markup)

        confirmed_reports.add(report_key)
        await query.message.edit_text("✅ Репорт успешно отправлен!")
    elif action == "cancel":
        await query.message.edit_text("❌ Репорт отменен.")

# Функция обработки пинга администраторов
async def handle_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    
    if len(data) < 3:
        await query.message.edit_text("❌ Ошибка: неправильный формат данных!")
        return

    action = data[0]  # Действие: ping

    if len(data) == 4:
        ping_answer = data[3]
        
        if ping_answer == "yes":
            await query.message.edit_text("⏳ Отправка пинга администраторам...")

            # Получаем администраторов
            admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
            admin_mentions = [f"@{admin.user.username}" for admin in admins if admin.user.username]

            # Отправляем пинг
            await bot.send_message(ADMIN_CHAT_ID, "Пинг от пользователя", parse_mode=ParseMode.HTML)

            if admin_mentions:
                half = len(admin_mentions) // 2
                await asyncio.sleep(4)
                await bot.send_message(ADMIN_CHAT_ID, "Первая часть админов: " + " ".join(admin_mentions[:half]))
                await asyncio.sleep(4)
                await bot.send_message(ADMIN_CHAT_ID, "Вторая часть админов: " + " ".join(admin_mentions[half:]))

            await query.message.edit_text("✅ Пинг отправлен!")
        elif ping_answer == "no":
            await query.message.edit_text("❌ Пинг не был отправлен.")
        else:
            await query.message.edit_text("❌ Ошибка: неверный ответ на вопрос о пинге.")
    else:
        await query.message.edit_text("❌ Ошибка: неправильный формат данных для пинга.")

# Функция обработки сообщений
async def handle_message(update: Update, context):
    message = update.message.text.lower()
    
    if "неко" in message:
        admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
        if admins:
            random_admin = random.choice(admins)
            random_username = random_admin.user.username if random_admin.user.username else "unknown_user"
            sent_message = await update.message.reply_text("вычисления кошко-девочки по айпи💻")
            await asyncio.sleep(5)
            await sent_message.edit_text(f"Кошко-девочка вычислена! Она находится у @{random_username}")
        else:
            await update.message.reply_text("❌ Не удалось получить администраторов для вычислений!")
    
    elif "пинг" in message:
        await update.message.reply_text("А нахуя он тебе?")
    
    elif "рафа" in message:
        response = random.choice(rafa_responses)
        await update.message.reply_text(response)

# Основная функция
async def main():
    await send_welcome_message()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CallbackQueryHandler(handle_report, pattern="^(confirm|cancel)_\d+_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_ping, pattern="^ping_\d+_\d+_(yes|no)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    await app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
